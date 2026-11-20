#!/usr/bin/env python3
"""Opt-in model check on fictitious document/captions, no video recognition claim."""
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
from pilot import assistant_metrics,durable,engine,library,operations,store,videos
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
    with tempfile.TemporaryDirectory(prefix='ss-video-real-') as directory:
        root=Path(directory);guides=root/'guides';media=root/'video';guides.mkdir();media.mkdir()
        (guides/'rotor.fr.txt').write_text('Assemblage du rotor fictif. La notice inventée indique un espacement de 23 mm. Le support du rotor fictif doit être mis au repos avant le réglage. Données de recette, jamais des consignes pratiques.')
        (media/'rotor.info.json').write_text(json.dumps({'title':'Assemblage du rotor fictif — vidéo de recette','language':'fr','duration':12}))
        shutil.copyfile(base/'tests/fixtures/video/solid-green.webm',media/'rotor.webm')
        (media/'rotor.fr.srt').write_text('1\n00:00:08,000 --> 00:00:10,000\nDans cet assemblage du rotor fictif, le sous-titre de test mentionne une cote de 17 mm. Seules les paroles écrites sont disponibles : aucune observation des gestes ni des images.\n')
        profile={'id':'real-video','model':args.model,'think':False,'name':'Essai réel des sources vidéo'}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(videos,'ROOT',media),\
             patch.object(library,'books',AsyncMock(return_value=[])),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),\
             patch.object(engine,'POLICY',base/'deploy/assistant-system.fr.txt'),patch.dict(engine.MODES,{'real-video':profile}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':2048}),patch.object(operations,'status',guard),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(2048,32,6),**kw)):
            store.init();library.index_guides();videos.STOP.clear();videos.scan()
            question='Fais une synthèse des documents et vidéos sur le rotor fictif. Compare les cotes annoncées et dis ce que les sources permettent réellement de vérifier.'
            job,conversation=store.new_id(),store.new_id();now=time.time()
            with store.connect() as db:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,'fixture','Video check',now))
                db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user',question,now))
                db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(job,'fixture',conversation,'real-video','queued',now,now))
            await engine.run(job,'fixture',conversation,'real-video',domain='all')
            with store.connect() as db:result=dict(db.execute('SELECT status,answer,sources,error FROM jobs WHERE id=?',(job,)).fetchone())
            result['sources']=json.loads(result['sources']);metrics=assistant_metrics.read(job)
            report={'schema':1,'version':json.loads((base/'deploy/release.json').read_text())['version'],'real_model':True,'fictional_corpus':True,
                'customer_validation':False,'model':args.model,'options':{'context':16384,'output':2048,'gpu_layers':32,'threads':6,'keep_alive_seconds':15},
                'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').rglob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'question':question,'result':result,'measurements':metrics,
                'checks':{'done':result['status']=='done','guide_cited':any(r['id'].startswith('guide:') for r in result['sources']),
                    'video_cited':any(r['id'].startswith('video:') for r in result['sources']),'17_present':'17' in result['answer'],'23_present':'23' in result['answer']},
                'human_semantic_review':'required_separately','pixel_or_audio_recognition_tested':False}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({'status':result['status'],'checks':report['checks'],'sources':len(result['sources']),'elapsed_ms':metrics.get('total_ms')}),flush=True)
            await library.kiwix_queries.close()
            if not all(report['checks'].values()):raise RuntimeError('Real video source check has gaps; inspect the private report.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--report',type=Path,required=True)
    asyncio.run(check(p.parse_args()))
