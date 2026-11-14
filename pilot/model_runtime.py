"""Read-only local model metadata. Never pulls, starts or loads a model."""
import asyncio
from collections import OrderedDict
import time
import re
import httpx
from . import store

CACHE=OrderedDict()


async def describe(endpoint,model,*,fresh=False):
    key=(str(store.ROOT),endpoint,model);previous=CACHE.get(key)
    if previous and not fresh and time.monotonic()-previous[0]<60:return dict(previous[1])
    result={'model':model,'available':False,'installed':False,'native_context':None,'digest':None,'version':None,'running':None,'other_models':0}
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=3) as client:
            async with asyncio.timeout(4):
                version,tags,show,ps=await asyncio.gather(client.get(endpoint+'/api/version'),client.get(endpoint+'/api/tags'),
                    client.post(endpoint+'/api/show',json={'model':model}),client.get(endpoint+'/api/ps'))
                for response in (version,tags,show,ps):response.raise_for_status()
                listed=next((m for m in tags.json().get('models',[]) if m.get('name',m.get('model'))==model),None)
                details=show.json();info=details.get('model_info',{})
                lengths=[value for name,value in info.items() if name.endswith('.context_length') and type(value) is int and 0<value<=10_000_000]
                native=info.get(str(info.get('general.architecture',''))+'.context_length')
                if type(native) is not int or native not in lengths:native=lengths[0] if len(lengths)==1 else None
                running=next((m for m in ps.json().get('models',[]) if m.get('name',m.get('model'))==model),None)
                digest=str(listed.get('digest','')).removeprefix('sha256:') if listed else ''
                release=str(version.json().get('version',''))
                result.update(available=True,installed=bool(listed) and not bool(details.get('remote_host') or details.get('remote_model')),
                    native_context=native,digest=digest if re.fullmatch('[a-fA-F0-9]{64}',digest) else None,
                    version=release if re.fullmatch(r'[0-9][a-zA-Z0-9.+-]{0,60}',release) else None,
                    running={k:running.get(k) for k in ('name','digest','size','size_vram','context_length')} if running else None,
                    other_models=sum(m.get('name',m.get('model'))!=model for m in ps.json().get('models',[])))
    except (TimeoutError,httpx.HTTPError,ValueError,TypeError,AttributeError):pass
    CACHE[key]=(time.monotonic(),result)
    while len(CACHE)>16:CACHE.popitem(last=False)
    return dict(result)
