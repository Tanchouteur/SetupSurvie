#!/usr/bin/env python3
"""Opt-in actual translation on R7, one existing hashed PDF and selected pages.

No download, no customer state, no global model change. Reports remain private.
CPU CI only imports the argument/fixture code; it never invokes this recipe.
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
from pilot import durable,engine,library,operations,store,translations
from real_assistant_check import TestTransport


async def check(args):
    source=args.source.resolve()
    if not source.is_file() or source.suffix.lower()!='.pdf' or source.stat().st_size>32_000_000:raise ValueError('An existing PDF of at most 32 MB is required.')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=args.sha256:raise ValueError('Source hash mismatch.')
    if not 1<=args.first<=args.last<=args.first+9:raise ValueError('Choose at most ten original pages.')
    base=Path(__file__).resolve().parents[1];original=httpx.AsyncClient;measures=[]
    report={'schema':1,'kind':'SetupSurvie real translation check','version':json.loads((base/'deploy/release.json').read_text())['version'],
        'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((base/'pilot').glob('*.py')))).hexdigest(),
        'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model':args.model,'customer_hardware_validation':False,
        'source':{'sha256':args.sha256,'bytes':source.stat().st_size,'title':args.title,'provenance':args.provenance},
        'pages':{'first':args.first,'last':args.last},'options':{'gpu_layers':args.gpu_layers,'threads':6,'context':16384,'think':args.think},'measurements':measures}
    def save():durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
    async def available(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json().get('models',[])
            if any(row.get('name',row.get('model'))!=args.model for row in loaded):raise RuntimeError('Another model is in use.')
        if args.gpu_layers:
            raw=await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
            free=int(raw.splitlines()[0]);ours=sum(row.get('size_vram',0) for row in loaded)//1024**2
            if free<1536 or free+ours<8192+1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False}
    await available();actual_translate=translations.translate
    if args.preload_model:
        if args.preload_model==args.model:raise ValueError('Choose a different installed model to test the switch.')
        async with original(trust_env=False,timeout=180) as client:
            loaded=(await client.get('http://127.0.0.1:11434/api/ps')).json().get('models',[])
            installed=(await client.get('http://127.0.0.1:11434/api/tags')).json().get('models',[])
            if loaded:raise RuntimeError('The switch test starts only with no model loaded.')
            if not any(row.get('name')==args.preload_model for row in installed):raise ValueError('Preload model is not already installed.')
            response=await client.post('http://127.0.0.1:11434/api/chat',json={'model':args.preload_model,'messages':[],'stream':False,'keep_alive':'15s','options':{'num_ctx':4096,'num_gpu':8,'num_thread':6}})
            response.raise_for_status()
            if response.json().get('done_reason')!='load':raise RuntimeError('Preload did not complete.')
        report['preloaded_by_recipe']=args.preload_model
        # Only the model this recipe has just loaded is admitted in addition to
        # the target. The Ollama scheduler owns eviction; no forced unload.
        previous_available=available
        async def with_owned_preload(**kwargs):
            async with original(trust_env=False,timeout=5) as client:
                response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();loaded=response.json().get('models',[])
                if any(row.get('name',row.get('model')) not in (args.model,args.preload_model) for row in loaded):raise RuntimeError('An unrelated model is in use.')
            if any(row.get('name',row.get('model'))==args.preload_model for row in loaded):
                raw=await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
                if int(raw.splitlines()[0])<8192+1536:raise RuntimeError('Target model reserve unavailable after preload.')
                return {'online':True,'paused':False}
            return await previous_available(**kwargs)
        available=with_owned_preload
    async def observed_translate(text,mode):return await actual_translate(text,mode,on_metrics=measures.append)
    with tempfile.TemporaryDirectory(prefix='ss-translation-real-') as directory:
        root=Path(directory);guides=root/'guides';guides.mkdir();shutil.copyfile(source,guides/'original.en.pdf')
        (guides/'metadata.json').write_text(json.dumps([{'path':'original.en.pdf','title':args.title,'language':'en','provenance':args.provenance,'licence':'Temporary private test; commercial redistribution not established.'}]))
        profile={'id':'real-translation','model':args.model,'think':{'true':True,'false':False}.get(args.think,args.think)}
        with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])),\
             patch.object(operations,'status',available),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.dict(engine.MODES,{'real-translation':profile}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,args.gpu_layers,6),**kw)),\
             patch.object(translations,'translate',side_effect=observed_translate),patch.object(translations,'launch'):
            store.init();library.index_guides();item=await translations.create('fixture','guide:original.en.pdf',None,'real-translation',args.first,args.last)
            if args.pause_after is not None and not 1<=args.pause_after<item['total']:raise ValueError('Pause checkpoint must leave at least one pending fragment.')
            task=asyncio.create_task(translations.run(item['id']));started=time.monotonic()
            translations.ACTIVE[item['id']]=task;checkpoint_done=False
            try:
                while not task.done():
                    await asyncio.wait({task},timeout=1 if args.pause_after and not checkpoint_done else 15);state=translations.status(item['id'],'fixture')
                    if args.pause_after and not checkpoint_done and state['done']>=args.pause_after and state['status'] in ('running','queued'):
                        checkpoint=await translations.pause(item['id'],'fixture');report['checkpoint']={'status':checkpoint['status'],'done':checkpoint['done'],'total':checkpoint['total']}
                        saved=[(row['position'],row['translated']) for row in checkpoint['parts'] if row['status']=='done']
                        store.init();await translations.resume(item['id'],'fixture');checkpoint_done=True
                        task=asyncio.create_task(translations.run(item['id']));translations.ACTIVE[item['id']]=task
                        report['checkpoint']['resume_requested']=True;report['checkpoint']['saved_parts']=saved
                    report['state']=state;report['elapsed_ms']=round((time.monotonic()-started)*1000);save()
                    print(json.dumps({'status':state['status'],'done':state['done'],'total':state['total'],'elapsed_ms':report['elapsed_ms']}),flush=True)
                await task;state=translations.status(item['id'],'fixture')
                state['parts']=[part for offset in range(0,state['total'],10) for part in translations.status(item['id'],'fixture',offset)['parts']]
                report['state']=state;report['export']=translations.export(item['id'],'fixture');report['elapsed_ms']=round((time.monotonic()-started)*1000);save()
                if checkpoint_done:
                    report['checkpoint']['completed_parts_preserved']=all(any(row['position']==position and row['translated']==text for row in state['parts']) for position,text in report['checkpoint']['saved_parts'])
                    save()
                if args.verify_reader and state['publication']['source_id']:
                    from pilot import translation_reader
                    choices=translation_reader.choices(state['source_id'])
                    pages=[translation_reader.page(state['publication']['source_id'],state['source_id'],number) for number in range(args.first,args.last+1)]
                    report['reader']={'choices':choices,'pages':pages,'all_translated_parts_match':all(
                        page.get('parts')==[row['translated'] if row['status']=='done' else '[Texte non extractible : consultez la page originale.]' for row in state['parts'] if row['page']==page['page']]
                        for page in pages)};save()
            finally:
                if not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
                translations.ACTIVE.pop(item['id'],None)
            await library.kiwix_queries.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',required=True);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--title',required=True);parser.add_argument('--provenance',default='Unknown provenance; test only.');parser.add_argument('--first',type=int,required=True);parser.add_argument('--last',type=int,required=True)
    parser.add_argument('--gpu-layers',type=int,choices=range(129),default=0);parser.add_argument('--think',choices=('true','false','low','medium','high'),default='true');parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--pause-after',type=int)
    parser.add_argument('--preload-model')
    parser.add_argument('--verify-reader',action='store_true')
    asyncio.run(check(parser.parse_args()))
