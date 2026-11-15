#!/usr/bin/env python3
"""Explicit R7/local-model long reading check. Never in CI; fictional PDFs only."""
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
from pilot import durable,engine,library,operations,store,summaries
from real_assistant_check import TestTransport


async def check(args):
    base=Path(__file__).resolve().parents[1];original=httpx.AsyncClient
    report={'schema':1,'kind':'real long summary','fictional_corpus':True,'customer_validation':False,
        'version':json.loads((base/'deploy/release.json').read_text())['version'],
        'source_digest':hashlib.sha256(b''.join(p.read_bytes() for p in sorted((base/'pilot').glob('*.py')))).hexdigest(),
        'model':args.model,'num_ctx':16384,'num_gpu':args.gpu_layers,'threads':6,'predict':4096,'checkpoint_states':[]}
    def save():durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
    async def available(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json()['models']
            if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        if args.gpu_layers:
            raw=await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
            free=int(raw.splitlines()[0]);ours=sum(row.get('size_vram',0) for row in loaded)//1024**2
            if free<1536 or free+ours<8192+1536:raise RuntimeError('VRAM reserve unavailable.')
        return {'online':True,'paused':False}
    await available()
    with tempfile.TemporaryDirectory(prefix='ss-summary-real-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir();records=[]
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
        for index,value in enumerate((17,59),1):
            writer=PdfWriter();name=f'notice-{index}.fr.pdf'
            for number in range(1,22):
                page=writer.add_blank_page(width=300,height=400)
                page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
                words=f'La notice {index} donne la valeur fictive {value} unites pour le capteur de serre. Ne pas extrapoler ces donnees de test.' if number==21 else 'Introduction historique fictive. Aucun chiffre de capteur dans cette page.'
                stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+words+') Tj ET').encode());page[NameObject('/Contents')]=stream
            writer.write(guides/name);records.append({'path':name,'title':f'Notice fictive de capteur {index}','language':'fr','document_date':'2026-01-01','edition':str(index)})
        (guides/'metadata.json').write_text(json.dumps(records),encoding='utf-8')
        profile={'id':'real-summary','model':args.model,'think':True,'name':'Real fixture'}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])),patch.object(operations,'status',available),\
             patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),patch.dict(engine.MODES,{'real-summary':profile}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,args.gpu_layers,6),**kw)):
            store.init();library.index_guides();started=time.monotonic()
            with patch.object(summaries,'launch'):
                item=await summaries.create('fixture','Compare les valeurs des deux notices fictives de capteurs de serre et leurs limites. Cite chaque source et sa page.', 'real-summary',source_ids=['guide:'+row['path'] for row in records])
            task=asyncio.create_task(summaries.run(item['id']))
            try:
                while not task.done():
                    await asyncio.wait({task},timeout=20)
                    state=summaries.status(item['id'],'fixture');progress={key:state[key] for key in ('status','read','total','pending','node_count')}
                    report['checkpoint_states'].append(progress);print(json.dumps(progress),flush=True);save()
                await task
                report['elapsed_ms']=round((time.monotonic()-started)*1000);report['result']=summaries.status(item['id'],'fixture')
                report['export']=summaries.export(item['id'],'fixture')
                with store.connect() as db:report['all_nodes']=[dict(row) for row in db.execute('SELECT * FROM summary_nodes WHERE summary_id=? ORDER BY id',(item['id'],))]
                save();print(json.dumps({'status':report['result']['status'],'error':report['result']['error'],'elapsed_ms':report['elapsed_ms']}),flush=True)
            finally:
                if not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
                await library.kiwix_queries.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True);parser.add_argument('--gpu-layers',type=int,choices=range(0,129),default=0);parser.add_argument('--report',type=Path,required=True)
    asyncio.run(check(parser.parse_args()))
