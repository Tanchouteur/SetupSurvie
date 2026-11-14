"""Context and memory trial orchestration with fake HTTP only; never loads a model."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx
from fastapi import HTTPException
from pilot import calibration,engine,model_runtime,operations,store,translations


class CalibrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.model=engine.MODES['rapide']['model'];self.digest='a'*64;self.loaded=False;self.context=0;self.native=65536
        self.pause=False;self.pressure=False;self.hang=False;self.cloud=False;self.calls=[];self.started=asyncio.Event();self.release=asyncio.Event()
        for target,name,value in [(store,'ROOT',Path(temporary.name)),(engine,'LOCK',asyncio.Semaphore(1)),(engine,'ACTIVE',{}),(translations,'ACTIVE',{}),(calibration,'ACTIVE',{}),(model_runtime,'CACHE',{})]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        store.init()
        with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',('context:'+self.model,'8192'))
        async def state(**kwargs):
            return {'online':True,'control_available':True,'paused':self.pause,'memory':{'total':32*1024**3,'available':(3 if self.pressure and self.loaded and self.context>=32768 else 20)*1024**3},
                'gpus':[{'name':'Fake GPU','total':8*1024**3,'used':5*1024**3}]}
        p=patch.object(operations,'status',AsyncMock(side_effect=state));p.start();self.addCleanup(p.stop)
        client=httpx.AsyncClient
        async def handler(request):
            self.calls.append(request.url.path)
            if request.url.path=='/api/version':return httpx.Response(200,json={'version':'0.12.0'})
            if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':self.model,'digest':self.digest}]})
            if request.url.path=='/api/show':return httpx.Response(200,json={'model_info':{'general.architecture':'fixture','fixture.context_length':self.native,'vision.context_length':128},'remote_host':'cloud.invalid' if self.cloud else ''})
            if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[{'name':self.model,'digest':self.digest,'context_length':self.context,'size':8*1024**3,'size_vram':6*1024**3}] if self.loaded else []})
            if request.url.path=='/api/generate':
                payload=json.loads(request.content);self.assertEqual(payload,{'model':self.model,'keep_alive':0,'stream':False});self.loaded=False
                return httpx.Response(200,json={'done':True,'done_reason':'unload'})
            self.assertEqual(request.url.path,'/api/chat');payload=json.loads(request.content);self.assertNotIn('tools',payload)
            self.context=payload['options']['num_ctx'];self.loaded=True;self.started.set()
            if self.hang:await self.release.wait()
            text=payload['messages'][0]['content'];tokens=int(len(text.encode('utf-8'))/4)
            event={'message':{'content':'OK'},'done':True,'done_reason':'stop','prompt_eval_count':tokens,'eval_count':1,'load_duration':1000000,'prompt_eval_duration':2000000,'eval_duration':1000000,'total_duration':4000000}
            return httpx.Response(200,content=json.dumps(event).encode()+b'\n')
        p=patch.object(httpx,'AsyncClient',side_effect=lambda **kw:client(transport=httpx.MockTransport(handler),**kw));p.start();self.addCleanup(p.stop)

    async def finish(self,max_context=32768):
        report=await calibration.start('rapide',max_context)
        await asyncio.wait_for(calibration.ACTIVE[report['id']],5)
        return calibration.status()

    async def test_cold_warm_measured_contexts_require_explicit_apply_and_can_rollback(self):
        report=await self.finish()
        self.assertEqual(report['status'],'completed',report)
        self.assertEqual([(t['context'],t['temperature'],t['status']) for t in report['trials']],[(16384,'probe','passed'),(16384,'cold','passed'),(16384,'warm','passed'),(32768,'cold','passed'),(32768,'warm','passed')])
        self.assertEqual(report['recommendation'],32768);self.assertEqual(engine.context_size(self.model),8192)
        self.assertTrue(report['model_released']);self.assertFalse(self.loaded)
        await calibration.apply(report['id']);self.assertEqual(engine.context_size(self.model),32768)
        await calibration.apply(report['id']);self.assertEqual(engine.context_size(self.model),32768)
        calibration.rollback(self.model);self.assertEqual(engine.context_size(self.model),8192)
        self.assertTrue(calibration.location().with_name(report['id']+'.json').is_file())
        self.assertNotIn('/api/pull',self.calls);self.assertNotIn('messages',json.dumps(report));self.assertNotIn('Repère',json.dumps(report))

    async def test_pressure_stops_higher_context_without_changing_saved_choice(self):
        self.pressure=True;report=await self.finish(65536)
        self.assertEqual(report['reason'],'ram_pressure');self.assertEqual(report['recommendation'],16384)
        self.assertEqual(report['trials'][-1]['context'],32768);self.assertEqual(report['trials'][-1]['failure_free']['ram_available'],3*1024**3)
        self.assertFalse(any(t['context']==65536 for t in report['trials']));self.assertFalse(self.loaded)
        self.assertEqual(engine.context_size(self.model),8192)

    async def test_pause_refuses_before_any_model_contact(self):
        self.pause=True
        with self.assertRaises(HTTPException) as caught:await calibration.start('rapide')
        self.assertEqual(caught.exception.status_code,409);self.assertEqual(self.calls,[])

    async def test_pause_during_trial_cancels_request_without_forcing_restart(self):
        self.hang=True;report=await calibration.start('rapide');await asyncio.wait_for(self.started.wait(),2);self.pause=True
        await asyncio.wait_for(calibration.ACTIVE[report['id']],4)
        self.assertEqual(calibration.status()['reason'],'paused');self.assertFalse(calibration.running())
        self.assertNotIn('/api/generate',self.calls);self.assertEqual(engine.context_size(self.model),8192)

    async def test_new_question_takes_priority_and_cancel_remains_explicit(self):
        self.hang=True;report=await calibration.start('rapide');await asyncio.wait_for(self.started.wait(),2)
        engine.ACTIVE['new-question']=object()
        await asyncio.wait_for(calibration.ACTIVE[report['id']],4)
        self.assertEqual(calibration.status()['reason'],'other_activity');self.assertNotIn('/api/generate',self.calls)
        engine.ACTIVE.clear();self.started.clear();self.loaded=False
        report=await calibration.start('rapide');await asyncio.wait_for(self.started.wait(),2);await calibration.cancel()
        self.assertEqual(calibration.status()['status'],'cancelled');self.assertFalse(calibration.running())

    async def test_native_limit_remote_model_and_changed_digest_are_enforced(self):
        self.native=20000;report=await self.finish(65536)
        self.assertEqual(report['recommendation'],16384);self.assertEqual(len(report['trials']),3)
        self.digest='b'*64
        with self.assertRaises(HTTPException):await calibration.apply(report['id'])
        self.cloud=True;self.calls.clear();report=await self.finish()
        self.assertEqual(report['reason'],'model_metadata_unavailable');self.assertNotIn('/api/chat',self.calls)

    async def test_restart_does_not_resume_or_contact_engine(self):
        calibration.save({'schema':1,'id':'a'*32,'status':'running','trials':[]})
        report=calibration.status();self.assertEqual(report['status'],'interrupted');self.assertEqual(report['reason'],'service_restarted');self.assertEqual(self.calls,[])

    async def test_immediate_cancel_does_not_look_like_a_restart(self):
        await calibration.start('rapide');await calibration.cancel()
        self.assertEqual(calibration.status()['status'],'cancelled');self.assertEqual(calibration.status()['reason'],'user_cancelled')
