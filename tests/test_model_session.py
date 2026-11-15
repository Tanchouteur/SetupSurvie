"""Lifecycle recovery on simulated Ollama HTTP only; no model or GPU."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock

import httpx

from pilot import assistant_metrics,model_session


class MessageFormatTests(unittest.TestCase):
    def test_legacy_tools_remain_declared_after_a_tool_result(self):
        messages=[{'role':'system','content':'Policy'},{'role':'user','content':'Question'},{'role':'tool','content':'Untrusted source text'}]
        tools=[{'type':'function','function':{'name':'read_source'}}]
        before=json.dumps(messages)
        result=model_session.chat_messages(messages,tools,'last_user')
        self.assertIn('read_source',result[0]['content']);self.assertNotIn('Untrusted source text',result[0]['content'])
        self.assertEqual(result[-1],messages[-1]);self.assertEqual(json.dumps(messages),before)
    def test_late_instructions_do_not_hide_the_generation_header_or_mutate_tool_data(self):
        messages=[{'role':'system','content':'Initial policy'},{'role':'user','content':'Original question'},
                  {'role':'assistant','content':'','tool_calls':[{'function':{'name':'read_sources','arguments':{'ids':['a']}}}]},
                  {'role':'tool','content':'{"source":"untrusted data"}'},{'role':'system','content':'Final citation instructions'}]
        before=json.dumps(messages);result=model_session.chat_messages(messages)
        self.assertEqual(result[0]['content'],'Initial policy\n\nFinal citation instructions')
        self.assertEqual(result[-1]['role'],'tool');self.assertEqual(result[-1]['content'],messages[-2]['content'])
        self.assertEqual(len([m for m in result if m['role']=='system']),1)
        self.assertEqual(json.dumps(messages),before)


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self,responses,*,runtime=None,guard=None):
        self.requests=[];self.stages=[];self.measured=assistant_metrics.Measurement('fixture','new:local','rapide',16384)
        self.guard=guard or AsyncMock()
        def handler(request):
            self.requests.append(json.loads(request.content))
            value=responses.pop(0)
            if isinstance(value,BaseException):raise value
            if isinstance(value,httpx.AsyncByteStream):return httpx.Response(200,stream=value)
            if isinstance(value,tuple):return httpx.Response(value[0],json={'error':value[1]})
            return httpx.Response(200,content=json.dumps(value).encode()+b'\n')
        self.payload={'model':'new:local','messages':[{'role':'user','content':'Question privée conservée'}],
                      'tools':[{'function':{'name':'read_source'}}],'stream':True,'keep_alive':'5m','options':{'num_ctx':16384,'num_predict':4096}}
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            session=model_session.Session(client,'http://fixture',runtime or {'model':'new:local','available':True,'running':None,'other_models':1},16384,self.measured,self.stages.append,self.guard)
            await session.prepare()
            return [event async for event in session.chat(self.payload)]

    @staticmethod
    def ready():return {'done':True,'done_reason':'load'}

    @staticmethod
    def reply():return {'message':{'content':'Réponse fictive'},'done':True,'done_reason':'stop','eval_count':3}

    async def test_switch_loads_target_before_question_with_same_context_and_keepalive(self):
        result=await self.exercise([self.ready(),self.reply()])
        self.assertEqual(result[-1]['message']['content'],'Réponse fictive')
        self.assertEqual(self.requests[0],{'model':'new:local','messages':[],'stream':False,'keep_alive':'5m','options':{'num_ctx':16384}})
        self.assertEqual(self.requests[1],self.payload)
        self.assertIn('switching',self.stages)
        self.assertEqual(self.measured.value['model_preparations'][0]['status'],'ready')

    async def test_warm_or_unknown_runtime_does_not_reload_or_force_evict(self):
        for runtime in ({'available':True,'running':{'name':'new:local'},'other_models':1},{'available':False}):
            await self.exercise([self.reply()],runtime=runtime)
            self.assertEqual(self.requests,[self.payload]);self.assertEqual(self.measured.value['model_preparations'],[])

    async def test_changed_context_is_prepared_without_changing_requested_value(self):
        await self.exercise([self.ready(),self.reply()],runtime={'model':'new:local','available':True,'running':{'name':'new:local','context_length':8192}})
        self.assertEqual(self.requests[0]['options']['num_ctx'],16384)
        self.assertIn('loading',self.stages);self.assertNotIn('switching',self.stages)

    async def test_load_failure_recovers_once_without_sending_question_twice(self):
        await self.exercise([(503,'Server busy /private/path'),self.ready(),self.reply()])
        self.assertEqual([len(p['messages']) for p in self.requests],[0,0,1])
        report=self.measured.value
        self.assertEqual(report['model_retries'],[{'stage':'loading','reason':'http_error','http_status':503}])
        for private in ('/private/path','Question privée','Réponse fictive'):self.assertNotIn(private,json.dumps(report,ensure_ascii=False))

    async def test_empty_acknowledgement_does_not_finish_question(self):
        for reason in ('load','unload','stop'):
            await self.exercise([self.ready(),{'done':True,'done_reason':reason},self.reply()])
            self.assertEqual(self.requests[-2],self.requests[-1])
            self.assertEqual(len(self.measured.value['model_retries']),1)

    async def test_empty_response_stops_after_one_recovery(self):
        result=await self.exercise([self.ready(),self.ready(),self.ready()])
        self.assertEqual(len(self.requests),3);self.assertFalse(result[-1].get('message'))

    async def test_one_recovery_budget_shared_with_loading(self):
        result=await self.exercise([(503,'busy'),self.ready(),self.ready()])
        self.assertEqual(len(self.requests),3);self.assertEqual(len(self.measured.value['model_retries']),1)
        self.assertEqual(result,[self.ready()])

    async def test_transient_start_failure_keeps_same_model_tools_and_question(self):
        for failure in ((500,'runner stopped'),httpx.ReadTimeout('loading'),{'error':'out of memory /private/path'}):
            await self.exercise([failure,self.reply()],runtime={'available':True,'running':{'name':'new:local'}})
            self.assertEqual(self.requests,[self.payload,self.payload])

    async def test_permanent_http_error_or_invalid_load_is_not_retried(self):
        for failure in ((404,'not installed'),(400,'unsupported tools')):
            with self.assertRaises(httpx.HTTPStatusError):await self.exercise([failure])
            self.assertEqual(len(self.requests),1)
        with self.assertRaises(model_session.Failure):await self.exercise([{'done':True,'done_reason':'unload'}])
        self.assertEqual(len(self.requests),1)

    async def test_no_retry_after_thinking_tool_calls_or_output_limit(self):
        for message in ({'thinking':'Raisonnement privé'},{'tool_calls':[{'function':{'name':'calculate'}}]},{'content':'Texte déjà commencé'}):
            event={'message':message,'done':True,'done_reason':'stop'}
            result=await self.exercise([event],runtime={'available':True,'running':{'name':'new:local'}})
            self.assertEqual(result,[event]);self.assertEqual(len(self.requests),1)
        await self.exercise([{'done':True,'done_reason':'length'}],runtime={'available':True,'running':{'name':'new:local'}})
        self.assertEqual(len(self.requests),1)

    async def test_partial_disconnection_is_not_replayed(self):
        class Broken(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b'{"message":{"content":"Partial"},"done":false}\n'
                raise httpx.ReadError('broken')
        with self.assertRaises(httpx.ReadError):await self.exercise([Broken()],runtime={'available':True,'running':{'name':'new:local'}})
        self.assertEqual(len(self.requests),1)

    async def test_pause_before_load_or_retry_prevents_new_requests(self):
        with self.assertRaises(model_session.Failure):await self.exercise([],guard=AsyncMock(side_effect=model_session.Failure('engine_paused')))
        self.assertEqual(self.requests,[])
        guard=AsyncMock(side_effect=[None,model_session.Failure('engine_paused')])
        with self.assertRaises(model_session.Failure):await self.exercise([(503,'busy')],guard=guard)
        self.assertEqual(len(self.requests),1)

    async def test_cancellation_during_loading_does_not_retry(self):
        with self.assertRaises(asyncio.CancelledError):await self.exercise([asyncio.CancelledError()])
        self.assertEqual(len(self.requests),1)


if __name__=='__main__':unittest.main()
