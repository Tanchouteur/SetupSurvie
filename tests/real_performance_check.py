#!/usr/bin/env python3
"""Opt-in real-model/counter campaign on tiny fixtures; never executed by CI.

Run only on the authorized inference host. No downloads, forced unloads, cache
clearing or service changes. This does not measure a customer's full library.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import AsyncMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import httpx
import control
import host_performance
from pilot import durable,engine,library,operations,performance,store
from real_assistant_check import TestTransport


async def check(args):
    root=Path(__file__).resolve().parents[1];original=httpx.AsyncClient
    async def available(**kwargs):
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status()
            models=response.json().get('models',[])
            if any(row.get('name',row.get('model'))!=args.model for row in models):raise RuntimeError('Another model is in use.')
        raw=await asyncio.to_thread(control.subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
        free=int(raw.splitlines()[0]);owned=sum(row.get('size_vram',0) for row in models)//1024**2
        if free<1536 or free+owned<8192+1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False}
    await available()
    with tempfile.TemporaryDirectory(prefix='ss-performance-real-') as directory:
        data=Path(directory);guides=data/'guides';guides.mkdir()
        for filename,text in [('feu.fr.txt','Techniques pour faire du feu. Document fictif de test de recherche, sans instruction pratique. Comparer les sources et leurs limites.'),
                              ('solaire.fr.txt','Panneau solaire et batterie. Document fictif de test, sans schéma ni consigne électrique.'),
                              ('histoire.fr.txt','La Révolution française. Document fictif destiné à mesurer la recherche, sans cours historique.')]:
            (guides/filename).write_text(text,encoding='utf-8')
        sampler=host_performance.Sampler()
        async def resources():
            def sample():
                value=sampler.sample(data);value.update(control.hardware({'data_dir':str(data)}),available=True,memory_gpu_age_ms=0)
                return value
            return await asyncio.to_thread(sample)
        profile={'id':'real-performance','model':args.model,'think':False,'name':'Essai réel de performances'}
        with patch.object(store,'ROOT',data/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])),\
             patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),patch.object(engine,'POLICY',root/'deploy/assistant-system.fr.txt'),\
             patch.dict(engine.MODES,{'real-performance':profile}),patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':2048}),\
             patch.object(operations,'status',available),patch.object(operations,'performance',resources),\
             patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(2048,args.gpu_layers,6),**kw)):
            store.init();library.index_guides()
            report=await performance.start('real-performance','fixture',json.loads((root/'deploy/release.json').read_text())['version'])
            task=performance.ACTIVE[report['id']]
            while not task.done():
                await asyncio.wait({task},timeout=20)
                value=performance.status();print(json.dumps({'status':value['status'],'step':value.get('current_step'),'samples':value['sample_count']}),flush=True)
            report=performance.status(full=True)
            report['real_recipe']={'real_model':True,'fictional_corpus':True,'customer_hardware_validation':False,
                'host_bridge':'native_functions_directly_HTTP_bridge_tested_separately','gpu_layers':args.gpu_layers,'threads':6,'context':16384,'output_limit':2048,
                'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((root/'pilot').glob('*.py')))).hexdigest(),
                'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
            durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
            print(json.dumps({'status':report['status'],'reason':report.get('reason'),'steps':[{k:row.get(k) for k in ('id','status','reason','elapsed_ms')} for row in report['steps']],
                              'samples':report['sample_count'],'host_samples':report['host_sample_count']}),flush=True)
            await library.kiwix_queries.close()
            if report.get('reason')!='completed':raise RuntimeError('Campaign has gaps; inspect the private report.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True);parser.add_argument('--gpu-layers',type=int,choices=range(1,65),required=True)
    parser.add_argument('--report',type=Path,required=True)
    asyncio.run(check(parser.parse_args()))
