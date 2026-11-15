#!/usr/bin/env python3
"""Opt-in real-model check through a loopback endpoint.

Never run in CI. All documents/state are fictional and temporary. Defaults to
CPU/two threads. Explicit GPU tests check the requested memory reserve.
Reports with the actual answers are private. Does not benchmark a customer's PC.
"""
import argparse
import asyncio
import json
import hashlib
from pathlib import Path
import sys
import subprocess
import tempfile
import time
from unittest.mock import AsyncMock,patch
from urllib.parse import urlparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import assistant_metrics,durable,engine,library,operations,store


class TestTransport(httpx.AsyncBaseTransport):
    def __init__(self,predict,gpu_layers=0,threads=2):
        self.inner=httpx.AsyncHTTPTransport(trust_env=False);self.predict=predict;self.gpu_layers=gpu_layers;self.threads=threads
    async def handle_async_request(self,request):
        if request.url.path=='/api/chat':
            value=json.loads(request.content)
            value['options']={**value.get('options',{}),'num_gpu':self.gpu_layers,'num_thread':self.threads}
            if 'num_predict' in value['options']:value['options']['num_predict']=min(value['options']['num_predict'],self.predict)
            value['keep_alive']='15s'
            headers=dict(request.headers);headers.pop('content-length',None)
            request=httpx.Request(request.method,request.url,headers=headers,content=json.dumps(value).encode(),extensions=request.extensions)
        return await self.inner.handle_async_request(request)
    async def aclose(self):await self.inner.aclose()


async def check(args):
    report={'schema':1,'kind':'SetupSurvie real assistant check','created':time.time(),'model':args.model,
            'inference_options':{'num_gpu':args.gpu_layers,'num_thread':args.threads,'num_predict':args.predict,'num_ctx':args.context,'think':args.think},
            'fictional_corpus':True,'real_model':True,'cases':[],'customer_hardware_validation':False}
    base=Path(__file__).resolve().parents[1]
    report['software_version']=json.loads((base/'deploy/release.json').read_text())['version']
    report['source_digest']=hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').glob('*.py')))).hexdigest()
    async def available(**kwargs):
        async with original_client(trust_env=False,timeout=5) as client:
            response=await client.get(args.endpoint+'/api/ps');response.raise_for_status()
            loaded=response.json().get('models',[])
            owned={args.model}
            if preloaded:owned.add(args.switch_from)
            if any(row.get('name',row.get('model')) not in owned for row in loaded):raise RuntimeError('Another model is in use; test stopped.')
            if args.gpu_layers:
                raw=await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
                free=int(raw.splitlines()[0]);owned=sum(row.get('size_vram',0) for row in loaded)//1024**2
                if free<args.gpu_reserve_mib or free+owned<args.gpu_expected_mib+args.gpu_reserve_mib:
                    raise RuntimeError('Insufficient free VRAM for this test and its reserve.')
        return {'online':True,'paused':False}
    original_client=httpx.AsyncClient;preloaded=False
    with tempfile.TemporaryDirectory(prefix='setupsurvie-real-cpu-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir()
        records=[]
        for index,value in enumerate((17,23,31,43,59),1):
            name=f'notice-{index}.fr.txt'
            text=('Contexte historique fictif sans consigne pratique. '*100)+f'\nSuivi des capteurs de la serre fictive : la notice {index} donne la valeur inventée {value} unités. Ce sont des données de test, pas des mesures réelles.\n'
            (guides/name).write_text(text,encoding='utf-8')
            records.append({'path':name,'title':f'Suivi des capteurs de la serre fictive — notice {index}','language':'fr','document_date':'2026-01-01','edition':str(index)})
        (guides/'metadata.json').write_text(json.dumps(records),encoding='utf-8')
        profile={'id':'real-local','name':'Essai local réel','model':args.model,'think':args.think}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])),\
             patch.object(engine,'OLLAMA',args.endpoint),patch.object(engine,'POLICY',Path(__file__).resolve().parents[1]/'deploy/assistant-system.fr.txt'),\
             patch.dict(engine.MODES,{'real-local':profile}),patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':args.context,'output_tokens':args.predict}),\
             patch.object(operations,'status',available),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original_client(transport=TestTransport(args.predict,args.gpu_layers,args.threads),**kw)):
            store.init();library.index_guides()
            if args.switch_from:
                # Only preload into an idle Ollama instance. Do not unload any
                # third-party model to make this optional test possible.
                await available()
                async with original_client(trust_env=False,timeout=300,transport=TestTransport(args.predict,args.gpu_layers,args.threads)) as client:
                    current=await client.get(args.endpoint+'/api/ps');current.raise_for_status()
                    if current.json().get('models'):raise RuntimeError('Switch check requires an idle model service.')
                    response=await client.post(args.endpoint+'/api/chat',json={'model':args.switch_from,'messages':[],
                        'stream':False,'keep_alive':'15s','options':{'num_ctx':args.context}})
                    response.raise_for_status();loaded=response.json()
                    if loaded.get('done_reason')!='load':raise RuntimeError('Switch preparation did not load the test model.')
                preloaded=True;report['switch_from']=args.switch_from
            questions=[('simple','Fais une synthèse des documents sur le suivi des capteurs de la serre fictive'),
                       ('natural','Fais une synthèse des documents sur le suivi des capteurs de la serre fictive. Compare les notices et cite leurs valeurs.')]
            for index,(name,question) in enumerate(questions,1):
                if args.case!='all' and args.case!=name:continue
                await available();identifier='live-'+str(index);conversation='conversation-'+str(index);now=time.time()
                with store.connect() as db:
                    db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,'fixture',name,now))
                    db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user',question,now))
                    db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(identifier,'fixture',conversation,'real-local','queued',now,now))
                print('Starting real model case:',name,flush=True)
                task=asyncio.create_task(engine.run(identifier,'fixture',conversation,'real-local'))
                while not task.done():
                    done,_=await asyncio.wait({task},timeout=20)
                    if done:break
                    progress=engine.PROGRESS.get(identifier,{})
                    print(json.dumps({'name':name,'progress':progress.get('stage'),'sources_read':progress.get('sources_read',0),'elapsed_seconds':round(time.time()-now)}),flush=True)
                await task
                with store.connect() as db:job=dict(db.execute('SELECT * FROM jobs WHERE id=?',(identifier,)).fetchone())
                measures=assistant_metrics.read(identifier);answer=job.get('answer') or ''
                case={'name':name,'question':question,'status':job['status'],'error':job.get('error'),'answer':answer,
                      'sources':json.loads(job.get('sources') or '[]'),'measurements':measures,
                      'expected_fictional_values_present':[value for value in (17,23,31,43,59) if str(value) in answer]}
                async with original_client(trust_env=False,timeout=5) as client:
                    response=await client.get(args.endpoint+'/api/ps');response.raise_for_status()
                    case['observed_models']=[{key:row.get(key) for key in ('name','digest','size','size_vram','context_length')} for row in response.json().get('models',[])]
                trace=store.ROOT/'traces'/(identifier+'.json')
                if trace.exists():
                    evidence=json.loads(trace.read_text());case['rejected_proposals']=evidence.get('rejected_answers',[])
                    case['citation_proposals']=[item.get('proposals') for item in evidence.get('tools',[]) if item.get('stage')=='citation_linking']
                report['cases'].append(case)
                durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
                print(json.dumps({'name':name,'status':job['status'],'sources_read':measures.get('sources_read') if measures else None,'total_ms':measures.get('total_ms') if measures else None}),flush=True)
            await library.kiwix_queries.close()
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',default='http://127.0.0.1:21434')
    parser.add_argument('--model',required=True)
    parser.add_argument('--switch-from',help='Explicitly preload another installed test model, then test the selected model switch.')
    parser.add_argument('--case',choices=('all','simple','natural'),default='all')
    parser.add_argument('--context',type=int,choices=(16384,32768),default=16384)
    parser.add_argument('--predict',type=int,choices=range(256,4097),default=1536)
    parser.add_argument('--think',choices=('false','true','low','medium','high'),default='false')
    parser.add_argument('--gpu-layers',type=int,choices=range(-1,129),default=0)
    parser.add_argument('--threads',type=int,choices=range(1,9),default=2)
    parser.add_argument('--gpu-expected-mib',type=int,default=8192)
    parser.add_argument('--gpu-reserve-mib',type=int,default=1536)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();args.endpoint=args.endpoint.rstrip('/')
    args.think={'false':False,'true':True}.get(args.think,args.think)
    parsed=urlparse(args.endpoint)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password:parser.error('Use an explicit local endpoint or private SSH tunnel.')
    if args.gpu_expected_mib<512 or args.gpu_reserve_mib<512:parser.error('Keep an explicit VRAM estimate and reserve of at least 512 MiB.')
    asyncio.run(check(args))


if __name__=='__main__':main()
