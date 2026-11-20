#!/usr/bin/env python3
"""Opt-in real local MP4 recognition + French translation; never run by CI.

Use only an owned synthetic media fixture and a prepared pinned Whisper cache.
Numeric success does not certify recognition, translation or synchronization.
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
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import captions,durable,engine,operations,store,transcriptions,videos
from real_assistant_check import TestTransport


async def check(args):
    base=Path(__file__).resolve().parents[1];original=httpx.AsyncClient;started=time.monotonic()
    async def guard(**kw):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json().get('models',[])
        if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        free=int((await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)).splitlines()[0])
        if free<1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False,'message':'Essai autorisé'}
    await guard()
    free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0])
    if free<8192+1536:raise RuntimeError('Initial GPU allocation unavailable.')
    if not args.media.is_file() or args.media.suffix.lower()!='.mp4':raise RuntimeError('Provide the owned synthetic MP4.')
    if args.report.exists():raise RuntimeError('Choose a new report path.')
    original_hash=hashlib.sha256(args.media.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='ss-real-audio-') as folder:
        root=Path(folder);media=root/'video';media.mkdir();shutil.copyfile(args.media,media/'fixture.mp4')
        (media/'fixture.info.json').write_text(json.dumps({'title':'Synthetic workshop speech','language':'en','duration':132}))
        mode={'id':'real-audio','name':'Real audio translation','model':args.model,'think':False}
        with patch.object(store,'ROOT',root/'state'),patch.object(videos,'ROOT',media),patch.object(transcriptions,'MODEL_ROOT',args.cache),\
             patch.dict(engine.MODES,{'real-audio':mode}),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(operations,'status',guard),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,24,6),**kw)):
            store.init();videos.STOP.clear();videos.scan();identifier=videos.listing()['videos'][0]['id']
            job=await transcriptions.create(identifier,'en','real-audio',True);await transcriptions.ACTIVE[job['id']]
            result=transcriptions.status(job['id'],True)
            translation=None
            if result['translation_job']:
                task=captions.ACTIVE.get(result['translation_job'])
                if task:await task
                translation=captions.status(result['translation_job'],full=True)
            if videos.ACTIVE:await videos.ACTIVE
            source=videos.source(identifier)
            checks={'audio_completed':result['status']=='completed','all_three_units':result['units_done']==3,
                'french_completed':bool(translation and translation['status']=='completed'),
                'french_indexed':source.get('language')=='fr','both_tracks':{t['origin'] for t in source['tracks']}=={'local_transcription','local_translation'},
                'original_unchanged':hashlib.sha256((media/'fixture.mp4').read_bytes()).hexdigest()==original_hash}
            report={'schema':1,'version':json.loads((base/'deploy/release.json').read_text())['version'],'elapsed_ms':round((time.monotonic()-started)*1000),
                'source_digest':hashlib.sha256(b''.join(p.read_bytes() for p in sorted((base/'pilot').rglob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'synthetic_audio':True,'real_recognition':True,'real_translation':True,
                'customer_validation':False,'translation_options':{'model':args.model,'context':16384,'output':4096,'gpu_layers':24,'threads':6,'think':False,'keep_alive_seconds':15},
                'transcription':result,'translation':translation,'indexed_source':source,'checks':checks,'human_semantic_review':'required_separately'}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({'elapsed_ms':report['elapsed_ms'],'checks':checks,'error':result['error'],'translation_error':translation.get('error') if translation else None}),flush=True)
            await transcriptions.stop_all();await captions.stop_all();await videos.stop()
            if not all(checks.values()):raise RuntimeError('Inspect the private report; this run has gaps.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--media',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--model',required=True);p.add_argument('--report',type=Path,required=True)
    asyncio.run(check(p.parse_args()))
