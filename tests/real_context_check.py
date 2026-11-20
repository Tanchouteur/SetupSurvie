#!/usr/bin/env python3
"""Opt-in model check for long source identities; no real archive or download.

Run only on the authorized model host, outside CI. The report includes fictional
source text and the actual answer and must stay private.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import AsyncMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import assistant_metrics,durable,engine,library,operations,store
from real_assistant_check import TestTransport


async def check(args):
    base=Path(__file__).resolve().parents[1];original=httpx.AsyncClient
    async def guard(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json().get('models',[])
        if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        free=int((await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)).splitlines()[0])
        ours=sum(row.get('size_vram',0) for row in loaded)//1024**2
        if free<1536 or free+ours<8192+1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False}
    await guard()
    sources=[{'id':'zim:encyclopedie/A/'+str(i)+'-'+'path'*35,
        'title':'Suivi des capteurs de la serre fictive — '+str(i)+' titre "fr" \\ '*8,'language':'fr',
        'document_date':'2026','edition':'Édition complète '+str(i),'provenance':'Origine fictive '+('a'*100),
        'text':(f'Notice fictive {i} du suivi des capteurs de la serre : valeur inventée {i+17} unités. Données de recette sans application réelle. '*40)} for i in range(12)]
    byid={source['id']:source for source in sources}
    profile={'id':'real-context','model':args.model,'think':False,'name':'Essai réel du dossier documentaire'}
    with tempfile.TemporaryDirectory(prefix='ss-context-real-') as directory:
        with patch.object(store,'ROOT',Path(directory)/'state'),patch.object(library,'search',AsyncMock(return_value=library.SearchResults(sources,{'status':'complete','domain':'all'}))),\
             patch.object(library,'source',AsyncMock(side_effect=lambda identifier:byid[identifier])),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),\
             patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),patch.dict(engine.MODES,{'real-context':profile}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':args.context,'output_tokens':4096}),patch.object(operations,'status',guard),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,32,6),**kw)):
            store.init();job,conversation=store.new_id(),store.new_id();now=time.time()
            question='Fais une synthèse des documents sur le suivi des capteurs de la serre fictive. Compare les notices reçues et cite leurs valeurs.'
            with store.connect() as db:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,'fixture','Context check',now))
                db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user',question,now))
                db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(job,'fixture',conversation,'real-context','queued',now,now))
            await engine.run(job,'fixture',conversation,'real-context',domain='all')
            with store.connect() as db:result=dict(db.execute('SELECT status,answer,sources,error FROM jobs WHERE id=?',(job,)).fetchone())
            result['sources']=json.loads(result['sources']);metrics=assistant_metrics.read(job)
            trace=json.loads((store.ROOT/'traces'/(job+'.json')).read_text())
            packets=[row['result'] for row in trace.get('tools',[]) if row.get('tool')=='read_sources']
            read_ids={row['id'] for packet in packets for row in packet['results']}
            report={'schema':1,'version':json.loads((base/'deploy/release.json').read_text())['version'],'real_model':True,'fictional_corpus':True,
                'customer_validation':False,'model':args.model,'options':{'context':args.context,'output':4096,'gpu_layers':32,'threads':6,'keep_alive_seconds':15},
                'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').rglob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'question':question,'result':result,'measurements':metrics,'read_packets':packets,
                'rejected_proposals':trace.get('rejected_answers',[]),
                'citation_proposals':[row.get('proposals') for row in trace.get('tools',[]) if row.get('stage')=='citation_linking'],
                'checks':{'done':result['status']=='done','model_called':bool(metrics.get('model_calls')),'multiple_sources_read':len(read_ids)>=3,
                    'citations_read':bool(result['sources']) and all(row['id'] in read_ids for row in result['sources']),
                    'context_unchanged':metrics['context']==args.context,
                    'packets_fit':bool(metrics.get('reading_packets')) and all(row['encoded_bytes']<=row['maximum_bytes'] for row in metrics['reading_packets']),
                    'budget_fits':bool(metrics['budgets']) and all(row['input_estimate']+row['output']+row['template_reserve']<=row['context'] for row in metrics['budgets'])},
                'human_semantic_review':'required_separately'}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({'status':result['status'],'checks':report['checks'],'sources_read':len(read_ids),'sources_cited':len(result['sources']),'elapsed_ms':metrics.get('total_ms')}),flush=True)
            await library.kiwix_queries.close()
            if not all(report['checks'].values()):raise RuntimeError('Real context check has gaps; inspect the private report.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True)
    parser.add_argument('--context',type=int,choices=(16384,32768),default=16384);parser.add_argument('--report',type=Path,required=True)
    asyncio.run(check(parser.parse_args()))
