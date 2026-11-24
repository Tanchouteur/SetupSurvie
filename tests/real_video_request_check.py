#!/usr/bin/env python3
"""Opt-in real-model check of video requests and player links on fictitious files.

Runs only where Ollama and a GPU are available (never in CI or the CPU runner).
No download; the report keeps real answers about invented videos.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import AsyncMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import assistant_metrics,durable,engine,library,operations,store,video_requests,videos
from real_assistant_check import TestTransport

FIRE='Allumer un feu sans allumettes';WATER='Filtrer l’eau de pluie';PUMP='Réparer une pompe à main'
CASES=[
    {'id':'sujet_par_titre','question':'Cherche une vidéo sur comment faire du feux','expected':FIRE},
    {'id':'liste_generale','question':'ok bah trouve une vidéo de nimporte quoi dans la biblioteque','expected':None,'needs_link':True},
    {'id':'mot_dans_sous_titres','question':'Trouve-moi une vidéo où on parle d’un archet en bois','expected':FIRE},
    {'id':'sujet_absent','question':'Cherche une vidéo sur la soudure à l’arc','expected':None,'needs_link':False},
    {'id':'contenu_sous_titres','question':'D’après la vidéo sur le feu, quelle longueur d’archet est indiquée ? Donne aussi le lien de la vidéo.','expected':FIRE,'contains':'60'},
]


def fixtures(base,root):
    media=root/'video';media.mkdir();clip=base/'tests/fixtures/video/solid-green.webm'
    for stem,title,subtitle in [('feu',FIRE,'Pour cet exercice fictif, on prépare un archet en bois de 60 cm avant de frotter la planche.'),('eau',WATER,None),
                                ('pompe',PUMP,'La rondelle fictive de la pompe se remplace après avoir retiré le levier.')]:
        shutil.copyfile(clip,media/(stem+'.webm'))
        (media/(stem+'.info.json')).write_text(json.dumps({'title':title,'language':'fr','duration':12,'channel':'Chaîne fictive','id':stem.ljust(11,'x'),'extractor':'Youtube','description':'Vidéo de recette fictive.'},ensure_ascii=False))
        if subtitle:(media/(stem+'.fr.srt')).write_text('1\n00:00:02,000 --> 00:00:06,000\n'+subtitle+'\n')
    return media


def links(answer):return re.findall(r'\]\((/[^)\s]+)\)',answer)


def target(link):
    match=re.search(r'source=video:([a-f0-9]{64})',link)
    return match[1] if match else None


def assess(case,result,raw,titles):
    answer=result['answer'] or '';found=links(answer);keys=[target(link) for link in found];expected=next((key for key,title in titles.items() if title==case.get('expected')),None)
    checks={'done':result['status']=='done','no_invented_link':bool(all(key in titles for key in keys))}
    if case.get('expected'):
        checks['expected_link']=expected in keys;checks['no_false_absence']=not re.search(r'\baucune vid[ée]o\b',answer,re.I)
    if case.get('needs_link'):checks['some_link']=bool(found);checks['no_false_absence']=not re.search(r'\baucune vid[ée]o\b',answer,re.I)
    if case.get('needs_link') is False:checks['no_off_topic_appendix']='Vidéos trouvées dans la bibliothèque' not in answer
    if case.get('contains'):
        checks['fact_present']=case['contains'] in answer;checks['video_cited']=any(row['id'].startswith('video:') for row in result['sources'])
    return checks,{'links_written_by_model':len(links(raw)) if raw is not None else None,'links_final':len(found),'appendix_added':raw is not None and raw!=answer}


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
    with tempfile.TemporaryDirectory(prefix='ss-video-request-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir();media=fixtures(base,root)
        (guides/'feu.fr.txt').write_text('Notice fictive sur le feu. Données de recette, jamais des consignes pratiques.')
        profile={'id':'real-video','model':args.model,'think':False,'name':'Essai réel des demandes de vidéos'}
        raw={};appendix=video_requests.appendix
        def recorded(answer,suggestions):raw['value']=answer;return appendix(answer,suggestions)
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(videos,'ROOT',media),patch.object(videos,'CHECKED',0.0),\
             patch.object(library,'books',AsyncMock(return_value=[])),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),\
             patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),patch.dict(engine.MODES,{'real-video':profile}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':2048}),patch.object(operations,'status',guard),\
             patch.object(video_requests,'appendix',recorded),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(2048,args.gpu_layers,6),**kw)):
            store.init();library.index_guides();videos.STOP.clear();videos.scan()
            titles={row['id'].split(':',1)[1]:row['title'] for row in videos.listing()['videos']}
            if len(titles)!=3:raise RuntimeError('Video fixtures were not indexed.')
            cases=[]
            for case in CASES:
                raw.clear();job,conversation=store.new_id(),store.new_id();now=time.time();started=time.monotonic()
                with store.connect() as db:
                    db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,'fixture','Video request check',now))
                    db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user',case['question'],now))
                    db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(job,'fixture',conversation,'real-video','queued',now,now))
                await engine.run(job,'fixture',conversation,'real-video',domain='resilience')
                with store.connect() as db:result=dict(db.execute('SELECT status,answer,sources,error FROM jobs WHERE id=?',(job,)).fetchone())
                result['sources']=json.loads(result['sources'] or '[]');checks,detail=assess(case,result,raw.get('value'),titles)
                cases.append({**case,'result':result,'checks':checks,**detail,'elapsed_s':round(time.monotonic()-started,1),'measurements':assistant_metrics.read(job)})
                print(json.dumps({'case':case['id'],'status':result['status'],'checks':checks,**detail,'elapsed_s':cases[-1]['elapsed_s']},ensure_ascii=False),flush=True)
            await library.kiwix_queries.close()
    report={'schema':1,'version':json.loads((base/'deploy/release.json').read_text())['version'],'real_model':True,'fictional_corpus':True,'customer_validation':False,'model':args.model,
            'options':{'context':16384,'output':2048,'gpu_layers':args.gpu_layers,'threads':6,'keep_alive_seconds':15},
            'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').rglob('*.py')))).hexdigest(),'cases':cases,'human_review':'required_separately'}
    durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
    return all(all(case['checks'].values()) for case in cases)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--gpu-layers',type=int,default=99)
    raise SystemExit(0 if asyncio.run(check(parser.parse_args())) else 2)
