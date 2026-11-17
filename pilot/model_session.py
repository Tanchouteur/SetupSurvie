"""One selected local model, with a bounded recovery before any generated output.

The Ollama scheduler owns eviction. Never stop other applications or silently
change model/context. A retry retains the question and never replays tool work.
"""
import asyncio
import json
import re
import time

import httpx

# No idle expiry. Explicit stop/game pause and the engine scheduler still apply.
KEEP_ALIVE=-1


class Failure(RuntimeError):
    def __init__(self,kind):
        self.kind=kind
        super().__init__(kind)


def failure_kind(value):
    return 'memory_error' if re.search(r'out of memory|insufficient memory|failed to allocate',str(value),re.I) else 'model_error'


def chat_messages(messages,tools=(),placement='native'):
    """Keep trusted instructions in one initial system message.

    Some installed templates collect every system content but also retain those
    messages in their loop. A trailing system message can then suppress the
    assistant generation header. Tool data and stored history remain untouched.
    """
    systems=[message for message in messages if message.get('role')=='system']
    result=[{**systems[0],'content':'\n\n'.join(message.get('content','') for message in systems)},
            *(message for message in messages if message.get('role')!='system')] if systems else list(messages)
    if tools and placement=='last_user' and result and result[-1].get('role')!='user':
        description='Outils disponibles pour compléter un manque précis ; sinon rédige avec les résultats reçus :\n'+json.dumps(tools,ensure_ascii=False)
        if result[0].get('role')=='system':result[0]={**result[0],'content':result[0]['content']+'\n\n'+description}
        else:result.insert(0,{'role':'system','content':description})
    return result


class Session:
    def __init__(self,client,endpoint,runtime,context,measurement,notice,guard):
        self.client=client;self.endpoint=endpoint;self.runtime=runtime;self.context=context
        self.measurement=measurement;self.notice=notice;self.guard=guard;self.retried=False
        self.loaded=bool(runtime.get('running'))
        self.measurement.value['model_preparations']=[]
        self.measurement.value['model_retries']=[]

    async def recover(self,stage,reason,status=None):
        if self.retried:return False
        self.retried=True
        record={'stage':stage,'reason':reason}
        if status is not None:record['http_status']=status
        self.measurement.value['model_retries'].append(record)
        self.notice('retrying');self.measurement.phase('model_loading')
        await asyncio.sleep(.25)
        await self.guard()
        return True

    async def prepare(self):
        await self.guard()
        # A normal cold chat already loads its model. Explicitly finish a model
        # switch first so the user's question is never a load-only operation.
        allocated=(self.runtime.get('running') or {}).get('context_length')
        context_changed=type(allocated) is int and allocated>0 and allocated!=self.context
        switching=not self.loaded and bool(self.runtime.get('other_models'))
        if not self.runtime.get('available') or not (switching or context_changed):return
        self.notice('switching' if switching else 'loading');self.measurement.phase('model_loading')
        while True:
            started=time.monotonic();record={'status':'failed'}
            try:
                response=await self.client.post(self.endpoint+'/api/chat',json={
                    'model':self.runtime['model'],'messages':[],'stream':False,
                    'keep_alive':KEEP_ALIVE,'options':{'num_ctx':self.context}},timeout=httpx.Timeout(300,connect=15))
                response.raise_for_status();event=response.json()
                if event.get('error'):raise Failure(failure_kind(event['error']))
                if event.get('done') is not True or event.get('done_reason')!='load':raise Failure('invalid_model_load')
                record['status']='ready';self.loaded=True;return
            except (httpx.TransportError,httpx.HTTPStatusError,Failure) as error:
                status=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else None
                reason=error.kind if isinstance(error,Failure) else 'transport' if status is None else 'http_error'
                transient=status in (500,502,503,504) if status else not isinstance(error,Failure) or reason=='memory_error'
                if not transient or not await self.recover('loading',reason,status):raise
            finally:
                record['duration_ms']=round((time.monotonic()-started)*1000)
                self.measurement.value['model_preparations'].append(record)

    async def chat(self,payload):
        payload={**payload,'keep_alive':KEEP_ALIVE,'messages':chat_messages(payload['messages'],payload.get('tools'),self.runtime.get('tool_schema_placement'))}
        while True:
            produced=False;last={};done=False
            self.notice('loading' if self.runtime.get('available') and not self.loaded else 'preparing')
            try:
                async with self.client.stream('POST',self.endpoint+'/api/chat',json=payload,timeout=httpx.Timeout(180 if self.loaded else 300,connect=15)) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:continue
                        last=json.loads(line)
                        if last.get('error'):raise Failure(failure_kind(last['error']))
                        message=last.get('message') or {}
                        produced|=bool(message.get('content') or message.get('thinking') or message.get('tool_calls') or last.get('eval_count'))
                        done=last.get('done') is True
                        # Acknowledge-only frames are not assistant answers. Do
                        # not let one finish a user's question successfully.
                        if produced:yield last
                if not done:raise Failure('stream_interrupted')
                if produced or last.get('done_reason')=='length':
                    self.loaded=True
                    if not produced:yield last
                    return
                if not await self.recover('chat','empty_response'):
                    yield last
                    return
            except (httpx.TransportError,httpx.HTTPStatusError,Failure) as error:
                status=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else None
                reason=error.kind if isinstance(error,Failure) else 'transport' if status is None else 'http_error'
                transient=status in (500,502,503,504) if status else not isinstance(error,Failure) or reason in ('memory_error','stream_interrupted')
                if produced or not transient or not await self.recover('chat',reason,status):raise
