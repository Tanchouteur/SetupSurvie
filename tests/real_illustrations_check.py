#!/usr/bin/env python3
"""Opt-in real-model selection of original figure references, never vision/CI."""
import argparse
import asyncio
import hashlib
import json
import os
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
    original=httpx.AsyncClient;base=Path(__file__).resolve().parents[1]
    report={'schema':1,'fictional_corpus':True,'real_model':True,'vision':False,'customer_hardware_validation':False,
        'policy_digest':hashlib.sha256((base/'deploy/assistant-system.fr.txt').read_bytes()).hexdigest(),'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'version':json.loads((base/'deploy/release.json').read_text())['version'],'model':args.model,
        'source_digest':hashlib.sha256(b''.join(p.read_bytes() for p in sorted((base/'pilot').rglob('*.py')))).hexdigest(),
        'options':{'context':16384,'output':4096,'gpu_layers':args.gpu_layers,'threads':6,'reserve_mib':1536},'progress':[]}
    def save():durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
    async def available(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json()['models']
            if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        if args.gpu_layers:
            raw=await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
            free=int(raw.splitlines()[0]);ours=sum(row.get('size_vram',0) for row in loaded)//1024**2
            if free<1536 or free+ours<8192+1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False}
    await available()
    with tempfile.TemporaryDirectory(prefix='ss-figures-real-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir();zims=root/'zim';zims.mkdir();(zims/'fixture.zim').write_bytes(b'Fictional catalogue identity, not a real archive.')
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
        writer=PdfWriter()
        for number in range(1,22):
            page=writer.add_blank_page(width=300,height=400)
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
            words='Suivi des capteurs de la serre fictive. Atlas indique 17 unites. Schema fictif de capteur : ne pas extrapoler ces donnees de test.' if number==21 else 'Introduction historique fictive sans valeur de capteur.'
            drawing=' 30 50 60 40 re S 150 50 60 40 re S 90 70 m 150 70 l S' if number==21 else ''
            stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 200 Td ('+words+') Tj ET'+drawing).encode());page[NameObject('/Contents')]=stream
        writer.write(guides/'atlas.fr.pdf')
        (guides/'metadata.json').write_text(json.dumps([{'path':'atlas.fr.pdf','title':'Atlas — capteurs de serre fictifs','language':'fr','document_date':'2026-01-01','edition':'A'}]))
        html='''<html lang="fr"><title>Boreal — capteurs de serre fictifs</title><p>Suivi des capteurs de la serre fictive. Boreal indique 59 unités. Ne pas extrapoler ces données de test.</p><figure><img src="../I/schema.svg" alt="Schéma de capteur Boreal"><figcaption>Schéma du capteur fictif Boreal : valeur 59 unités. Données de test.</figcaption></figure><figure><img src="../I/logo.svg" alt="Logo de l’éditeur"><figcaption>Logo publicitaire de l’éditeur, sans information sur les capteurs.</figcaption></figure></html>'''
        async def get(path,**kw):return library.Fetched(html.encode(),'text/html','/content/fixture/A/boreal')
        profile={'id':'real-figures','model':args.model,'think':True,'name':'Real fixture'}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture','title':'Fixture','language':'fr'}])),patch.object(library,'get',get),patch.dict(os.environ,{'ZIM_DIR':str(zims)}),\
             patch.object(operations,'status',available),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),\
             patch.dict(engine.MODES,{'real-figures':profile}),patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,args.gpu_layers,6),**kw)):
            store.init();library.index_guides();now=time.time();question='Fais une synthèse des documents sur le suivi des capteurs de la serre fictive. Compare les valeurs Atlas et Boreal et montre leurs schémas originaux utiles, sans le logo.'
            with store.connect() as db:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','fixture','Figures',now));db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',('c','user',question,now))
                db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('figure-check','fixture','c','real-figures','queued',now,now))
            task=asyncio.create_task(engine.run('figure-check','fixture','c','real-figures',source_ids=['guide:atlas.fr.pdf','zim:fixture/A/boreal']))
            try:
                while not task.done():
                    await asyncio.wait({task},timeout=20);progress=engine.PROGRESS.get('figure-check',{});sample={key:progress.get(key) for key in ('stage','sources_read')};report['progress'].append(sample);print(json.dumps(sample),flush=True);save()
                await task
                with store.connect() as db:report['result']=dict(db.execute('SELECT * FROM jobs WHERE id=?',('figure-check',)).fetchone())
                report['measurements']=assistant_metrics.read('figure-check');report['elapsed_ms']=round((time.time()-now)*1000)
                report['sources']=json.loads(report['result']['sources']);report['selected_figures']=[figure for source in report['sources'] for figure in source.get('figures',[])]
                save();print(json.dumps({'status':report['result']['status'],'selected':[item['id'] for item in report['selected_figures']],'elapsed_ms':report['elapsed_ms']}),flush=True)
            finally:
                if not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
                await library.kiwix_queries.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True);parser.add_argument('--gpu-layers',type=int,choices=range(0,129),default=0);parser.add_argument('--report',type=Path,required=True)
    asyncio.run(check(parser.parse_args()))
