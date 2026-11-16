"""Read-only observations after a refused test; no prompt, log, start or model load."""
import asyncio
from contextlib import asynccontextmanager
import json
import math
import re
import time

import httpx
from fastapi import HTTPException
from . import durable,engine,operations,store

ACTIONS={'calibration','search_experiment','performance','translation_benchmark'}


def number(value):return type(value) in (int,float) and math.isfinite(value) and 0<=value<10**13


def controller(value):
    if not isinstance(value,dict):return {}
    result={name:value[name] for name in ('online','paused','control_available') if type(value.get(name)) is bool}
    for name,allowed in {'operation':('start','stop',None),'reason':('user_pause','user_gaming','gaming','start_failed'),
                         'control_error':('timeout','http_error','connection_error','invalid_response','not_configured')}.items():
        if value.get(name) in allowed:result[name]=value.get(name)
    for name in ('control_elapsed_ms','control_http_status'):
        if number(value.get(name)):result[name]=value[name]
    memory=value.get('memory',{})
    if isinstance(memory,dict):result['memory']={name:memory[name] for name in ('total','used','available') if number(memory.get(name))}
    gpus=value.get('gpus',[])
    result['gpus']=[{name:g[name] for name in ('total','used','utilization') if number(g.get(name))} for g in gpus[:8] if isinstance(g,dict)] if isinstance(gpus,list) else []
    last=value.get('last_engine_action',{})
    if isinstance(last,dict):
        enums={'action':('start','stop'),'stage':('transfer_guard','service_command','waiting_for_api','completed'),
               'status':('running','completed','failed'),'target':('windows','linux'),
               'error_kind':('SetupError','OSError','ValueError','TimeoutExpired','CalledProcessError','PermissionError','other_error')}
        result['last_engine_action']={name:last[name] for name,allowed in enums.items() if last.get(name) in allowed}
        for name in ('created','finished','elapsed_ms'):
            if number(last.get(name)):result['last_engine_action'][name]=last[name]
        if type(last.get('forced')) is bool:result['last_engine_action']['forced']=last['forced']
    return result


async def snapshot(model=None):
    started=time.monotonic()
    async def host():
        try:return controller(await operations.status(fresh=True))
        except Exception:return {'observation':'unavailable'}
    async def probe(client,path):
        before=time.monotonic()
        row={}
        try:
            response=await client.get(engine.OLLAMA+path);row['http_status']=response.status_code;response.raise_for_status()
            data=response.json()
            if path=='/api/version':
                version=data.get('version')
                if isinstance(version,str) and re.fullmatch(r'[0-9][a-zA-Z0-9.+-]{0,60}',version):row['version']=version
                else:raise ValueError()
            else:
                models=data.get('models')
                if not isinstance(models,list):raise ValueError()
                row['model_count']=len(models)
                if model:
                    selected=next((m for m in models if isinstance(m,dict) and m.get('name',m.get('model'))==model),None)
                    row['selected_present']=selected is not None
                    if selected:row['selected']={key:selected[key] for key in ('size','size_vram','context_length') if number(selected.get(key))}
            row['state']='responding'
        except (httpx.HTTPError,ValueError,TypeError,AttributeError) as error:
            row['state']='timeout' if isinstance(error,httpx.TimeoutException) else 'http_error' if isinstance(error,httpx.HTTPStatusError) else 'invalid_response' if not isinstance(error,httpx.HTTPError) else 'connection_error'
        row['elapsed_ms']=round((time.monotonic()-before)*1000);return row
    async with httpx.AsyncClient(trust_env=False,timeout=httpx.Timeout(3,connect=2)) as client:
        state,version,running,installed=await asyncio.gather(host(),probe(client,'/api/version'),probe(client,'/api/ps'),probe(client,'/api/tags'))
    return {'created':time.time(),'elapsed_ms':round((time.monotonic()-started)*1000),'controller':state,
            'ollama':{'version':version,'running':running,'installed':installed},
            'scope':'whole_host_memory_and_independent_local_api_observations','model_loaded_by_this_check':False}


def location():return store.ROOT/'startup-diagnostic.json'


def history():
    try:
        path=location()
        if path.stat().st_size>200_000:return []
        data=json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data,list) else []
    except (OSError,ValueError):return []


@asynccontextmanager
async def observe(action,mode,version):
    """An optional diagnostic must never replace the original refusal."""
    try:yield
    except HTTPException as error:
        if action in ACTIONS and mode in engine.MODES and error.status_code in (409,429,503):
            try:
                model=engine.MODES[mode]['model']
                row={'created':time.time(),'version':version,'action':action,'mode':mode,'model':model,
                     'context':engine.context_size(model),'http_status':error.status_code,'phase':'refused_before_start'}
                row['observed']=await snapshot(model)
                rows=[*history(),row][-20:]
                durable.write_bytes(location(),json.dumps(rows,ensure_ascii=False).encode('utf-8'),private=True)
            except Exception:pass
        raise


async def report(version,mode=None):
    selected=mode if mode in engine.MODES else None
    model=engine.MODES[selected]['model'] if selected else None
    return {'schema':1,'kind':'SetupSurvie startup diagnostic','created':time.time(),'version':version,
            'mode':selected,'model':model,'context':engine.context_size(model) if model else None,
            'refused_attempts':history(),'current':await snapshot(model),
            'limitations':['read_only_no_load_or_start','whole_host_memory','observations_after_refusal_not_the_exact_failure_instant',
                           'not_a_test_of_answer_quality','earlier_failures_without_record_remain_unknown']}
