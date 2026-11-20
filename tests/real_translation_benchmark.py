#!/usr/bin/env python3
"""Opt-in 40-page translation on the authorized model host; never in CI."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(BASE),str(BASE/'scripts')]
import httpx
import control
import host_performance
from pilot import durable,engine,operations,store,translation_benchmark as bench
from real_assistant_check import TestTransport


async def check(args):
    original=httpx.AsyncClient
    async def available(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status();models=response.json().get('models',[])
        if any(row.get('name',row.get('model'))!=args.model for row in models):raise RuntimeError('Another model is in use.')
        free=int((await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)).splitlines()[0])
        if free<1536 or kwargs.get('starting') and free<args.gpu_expected_mib+1536:
            print(json.dumps({'guard':'gpu_reserve_unavailable','free_mib':free,'starting':bool(kwargs.get('starting'))}),flush=True)
            raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False,'message':'Essai autorisé sur corpus fictif'}
    await available(starting=True)
    with tempfile.TemporaryDirectory(prefix='ss-long-translation-') as folder:
        root=Path(folder);sampler=host_performance.Sampler()
        async def resources():
            def sample():
                value=sampler.sample(root);value.update(control.hardware({'data_dir':str(root)}),available=True,memory_gpu_age_ms=0);return value
            return await asyncio.to_thread(sample)
        mode={'id':'real-long-translation','name':'Essai long réel','model':args.model,'think':False}
        with patch.object(store,'ROOT',root/'state'),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.dict(engine.MODES,{'real-long-translation':mode}),\
             patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),patch.object(operations,'status',available),\
             patch.object(operations,'performance',resources),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,args.gpu_layers,6),**kw)):
            store.init();report=await bench.start('real-long-translation',json.loads((BASE/'deploy/release.json').read_text())['version'])
            task=bench.ACTIVE[report['id']]
            while not task.done():
                await asyncio.wait({task},timeout=20);value=bench.status()
                print(json.dumps({key:value.get(key) for key in ('status','pages_done','parts_done','current_page','active_elapsed_ms','sample_count')}),flush=True)
            report=bench.status(full=True)
            report['real_recipe']={'real_model':True,'fictional_document':True,'customer_hardware_validation':False,'gpu_layers':args.gpu_layers,'gpu_expected_mib':args.gpu_expected_mib,'threads':6,
                'context':16384,'output_limit':4096,'keep_alive_seconds':15,'host_bridge':'native_functions_directly_HTTP_bridge_tested_separately',
                'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((BASE/'pilot').rglob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            if report.get('fixture'):
                durable.write_bytes(args.report.with_suffix('.private-parts.json'),json.dumps(bench.work(report),ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({key:report.get(key) for key in ('status','reason','pages_done','parts_done','active_elapsed_ms','source_words_per_minute')}),flush=True)
            if report.get('status')!='completed' or report.get('pages_done')!=40:raise RuntimeError('Long translation has gaps; inspect the private report.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--gpu-layers',type=int,choices=range(1,65),default=32);p.add_argument('--gpu-expected-mib',type=int,default=8192)
    asyncio.run(check(p.parse_args()))
