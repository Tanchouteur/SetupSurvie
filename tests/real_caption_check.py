#!/usr/bin/env python3
"""Opt-in subtitle translation on an authorized GPU host; fictional captions only."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import captions,durable,engine,operations,store,videos
from real_assistant_check import TestTransport


async def check(args):
    original=httpx.AsyncClient;base=Path(__file__).resolve().parents[1]
    async def guard(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json().get('models',[])
        if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        free=int((await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)).splitlines()[0])
        ours=sum(row.get('size_vram',0) for row in loaded)//1024**2
        if free<1536 or free+ours<8192+1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False,'message':'Test local autorisé'}
    await guard()
    sentences=['Fictional assembly for a language test, not real instructions.',
        'The imaginary rotor measures 17 mm.',
        'Do not replace the 23 mm support with the 31 mm support.',
        'Before continuing, disconnect the fictional battery.',
        'Keep the two blue parts together and the red part separate.',
        'The label says 12 V and 8 W. Never convert these values.']
    with tempfile.TemporaryDirectory(prefix='ss-real-caption-') as directory:
        root=Path(directory);media=root/'video';media.mkdir()
        (media/'rotor.webm').write_bytes((base/'tests/fixtures/video/solid-green.webm').read_bytes())
        (media/'rotor.info.json').write_text(json.dumps({'title':'Fictional subtitle test','language':'en','duration':12}))
        source='\n\n'.join(str(i+1)+'\n'+captions.stamp(i*2000).replace('.',',')+' --> '+captions.stamp(i*2000+1800).replace('.',',')+'\n'+text for i,text in enumerate(sentences))+'\n'
        (media/'rotor.en.srt').write_text(source)
        mode={'id':'real-caption','name':'Real captions','model':args.model,'think':False}
        with patch.object(store,'ROOT',root/'state'),patch.object(videos,'ROOT',media),patch.dict(engine.MODES,{'real-caption':mode}),\
             patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(operations,'status',guard),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,32,6),**kw)):
            store.init();videos.STOP.clear();videos.scan();identifier=videos.listing()['videos'][0]['id']
            job=await captions.create(identifier,0,'real-caption');await captions.ACTIVE[job['id']]
            if videos.ACTIVE:await videos.ACTIVE
            result=captions.status(job['id'],full=True);value=videos.source(identifier)
            report={'schema':1,'version':json.loads((base/'deploy/release.json').read_text())['version'],'model':args.model,
                'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').glob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fictional_captions':True,'real_model':True,
                'customer_validation':False,'options':{'context':16384,'output':4096,'gpu_layers':32,'threads':6,'keep_alive_seconds':15},
                'result':result,'indexed_source':value,'checks':{'completed':result['status']=='completed','all_cues':result['done']==len(sentences),
                    'french_indexed':value['language']=='fr','original_unchanged':(media/'rotor.en.srt').read_text()==source},
                'human_semantic_review':'required_separately','audio_transcription_tested':False,'online_acquisition_tested':False}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({'status':result['status'],'done':result['done'],'total':result['total'],'checks':report['checks'],'error':result['error']},ensure_ascii=False),flush=True)
            await captions.stop_all();await videos.stop()
            if not all(report['checks'].values()):raise RuntimeError('Subtitle check has gaps; inspect the private report.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--report',type=Path,required=True)
    asyncio.run(check(p.parse_args()))
