#!/usr/bin/env python3
"""Opt-in checks on a separately downloaded Baofeng manual; no corpus in CI.

Run on the authorized inference machine, never in the CPU runner. The manual must
already exist and match the pinned catalogue hash. No transmission/radio control.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import assistant_metrics,durable,engine,library,operations,store
from real_assistant_check import TestTransport

CASES=[
 ('keypad','Comment verrouiller et déverrouiller le clavier du Baofeng UV-5R ? Est-ce que cela bloque aussi les boutons sur le côté ?', 'Notice française page PDF 34 : # environ deux secondes ; les trois touches latérales ne sont pas verrouillées.'),
 ('memory','Sur un Baofeng UV-5R, comment mémoriser une fréquence simplex dans un canal vide, puis retrouver ce canal ?', 'Notice française page PDF 41 : mode VFO, MEM-CH menu 27, canal vide, confirmation MENU, EXIT, puis VFO/MR pour mode MR. Aucun effacement des canaux existants.'),
 ('quarter','Quelle longueur théorique en centimètres pour un brin quart d’onde à 145 MHz ? Et quelles limites pour une vraie antenne de portatif ?', '51,69 cm théoriques, retour de courant/adaptation, antenne raccourcie distincte. Ne pas couper une antenne commerciale.'),
 ('dipole','À 433 MHz, quelle est la longueur théorique totale d’un dipôle demi-onde et celle de chaque bras, en centimètres ?', '34,62 cm au total, environ 17,31 cm par bras ; dimensions théoriques distinctes de l’ajustement réel.'),
 ('quarter-calculated','Calcule avec les documents la longueur théorique en centimètres d’un brin quart d’onde à 147,5 MHz. Distingue le résultat d’une dimension de fabrication.', 'Formule exacte 299792458/(147500000*4)*100 : environ 50,81 cm. Calcul réellement demandé à l’outil, hypothèses et unités conservées ; pas de copie de la ligne 145 MHz ni de dimension universelle.'),
 ('unspecified','Quelle longueur d’antenne dois-je utiliser pour mon talkie Baofeng ?', 'Demander fréquence/bande et type/usage ; aucune dimension universelle déduite de la seule puissance.'),
]

def scenario(path):
    data=json.loads(path.read_text(encoding='utf-8'));root=path.resolve().parent;documents=[];cases=[]
    for row in data['documents']:
        relative=Path(row['path'])
        if relative.name!=row['path'] or relative.suffix.lower() not in ('.pdf','.html','.md','.txt'):raise ValueError('A scenario document must have a simple local filename.')
        local=(root/relative).resolve()
        if not local.is_relative_to(root) or not local.is_file() or local.stat().st_size>32_000_000:raise ValueError('Scenario document unavailable or outside its directory.')
        if hashlib.sha256(local.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Scenario document hash mismatch.')
        meta={key:row[key] for key in ('path','title','language','document_date','edition','provenance','licence') if key in row}
        if any(prior['path']==meta['path'] for _,prior in documents):raise ValueError('Duplicate scenario filename.')
        documents.append((local,meta))
    for row in data['cases']:
        name=row['name'];question=row['question'];review=row['review_reference']
        if not __import__('re').fullmatch(r'[a-zA-Z0-9-]{1,60}',name) or not 1<=len(question)<=2000 or not isinstance(review,str):raise ValueError('Invalid scenario case.')
        if any(prior[0]==name for prior in cases):raise ValueError('Duplicate scenario case.')
        cases.append((name,question,review))
    if not 1<=len(documents)<=12 or not 1<=len(cases)<=32:raise ValueError('Scenario exceeds test bounds.')
    return documents,cases


async def check(args):
    base=Path(__file__).resolve().parents[1]
    external=scenario(args.scenario_file) if args.scenario_file else None
    manual=args.manual.resolve() if args.manual else None
    entry=next(row for row in json.loads((base/'deploy/content-catalog.json').read_text())['items'] if row['id']=='baofeng-uv5r-manual')
    if not external and (not manual or manual.stat().st_size!=entry['bytes'] or hashlib.sha256(manual.read_bytes()).hexdigest()!=entry['sha256']):raise ValueError('Manual does not match the verified catalogue resource.')
    original=httpx.AsyncClient
    report={'schema':1,'kind':'SetupSurvie real documentary case check','fictional_corpus':False,'customer_hardware_validation':False,'radio_hardware_control':False,
        'version':json.loads((base/'deploy/release.json').read_text())['version'],'model':args.model,
        'source_digest':hashlib.sha256(b''.join(p.read_bytes() for p in sorted((base/'pilot').glob('*.py')))).hexdigest(),
        'policy_digest':hashlib.sha256((base/'deploy/assistant-system.fr.txt').read_bytes()).hexdigest(),
        'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'manual':None if external else {key:entry[key] for key in ('id','url','sha256','bytes','edition')},
        'scenario_documents':[{**meta,'sha256':hashlib.sha256(local.read_bytes()).hexdigest()} for local,meta in external[0]] if external else [],
        'reference_digest':hashlib.sha256((base/'deploy/library-templates/antennes-radio.fr.md').read_bytes()).hexdigest(),
        'scenario_digest':hashlib.sha256(args.scenario_file.read_bytes()).hexdigest() if external else None,
        'options':{'context':16384,'output':4096,'gpu_layers':args.gpu_layers,'threads':6,'reserve_mib':1536,'think':args.think},'cases':[]}
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
    cases=external[1] if external else CASES
    if args.case and args.case not in {row[0] for row in cases}:raise ValueError('Unknown scenario case.')
    await available()
    with tempfile.TemporaryDirectory(prefix='ss-radio-real-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir()
        if external:
            metadata=[meta for _,meta in external[0]]
            for local,meta in external[0]:shutil.copyfile(local,guides/meta['path'])
        else:
            shutil.copyfile(manual,guides/'baofeng.fr.pdf')
            shutil.copyfile(base/'deploy/library-templates/antennes-radio.fr.md',guides/'antennes-radio.fr.md')
            metadata=[{'path':'baofeng.fr.pdf','title':entry['title'],'language':'fr','edition':entry['edition'],'provenance':entry['publisher']+' — '+entry['url'],'licence':entry['licence']},
                {'path':'antennes-radio.fr.md','title':'Antennes radio : fréquence, longueur et type d’antenne','language':'fr','document_date':'2026-11-15','edition':'1','provenance':'Fiche SetupSurvie ; références BIPM et ARRL indiquées dans le document.'}]
        (guides/'metadata.json').write_text(json.dumps(metadata),encoding='utf-8')
        profile={'id':'real-radio','model':args.model,'think':({'true':True,'false':False}.get(args.think,args.think)),'name':'Real radio manual check'}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])),\
             patch.object(operations,'status',available),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),\
             patch.dict(engine.MODES,{'real-radio':profile}),patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,args.gpu_layers,6),**kw)):
            store.init();library.index_guides()
            for name,question,expected in cases:
                if args.case and name!=args.case:continue
                await available();now=time.time();identifier='radio-'+name
                with store.connect() as db:
                    db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(identifier,'fixture','Radio check',now));db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(identifier,'user',question,now))
                    db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(identifier,'fixture',identifier,'real-radio','queued',now,now))
                print('Starting '+name,flush=True)
                task=asyncio.create_task(engine.run(identifier,'fixture',identifier,'real-radio'))
                try:
                    while not task.done():
                        await asyncio.wait({task},timeout=20);print(json.dumps({'case':name,'progress':engine.PROGRESS.get(identifier,{}).get('stage'),'elapsed':round(time.time()-now)}),flush=True)
                    await task
                    with store.connect() as db:result=dict(db.execute('SELECT * FROM jobs WHERE id=?',(identifier,)).fetchone())
                    result['sources']=json.loads(result['sources']);result.update(name=name,question=question,review_reference=expected,measurements=assistant_metrics.read(identifier))
                    trace=store.ROOT/'traces'/(identifier+'.json')
                    if trace.exists():result['tool_trace']=json.loads(trace.read_text()).get('tools',[])
                    report['cases'].append(result);save();print(json.dumps({'case':name,'status':result['status'],'sources':len(result['sources'])}),flush=True)
                finally:
                    if not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
            await library.kiwix_queries.close()
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True);parser.add_argument('--think',choices=('true','false','low','medium','high'),default='true');parser.add_argument('--manual',type=Path);parser.add_argument('--scenario-file',type=Path);parser.add_argument('--case');parser.add_argument('--gpu-layers',type=int,choices=range(129),default=0);parser.add_argument('--report',type=Path,required=True)
    asyncio.run(check(parser.parse_args()))
