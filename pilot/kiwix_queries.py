"""Bounded shared Kiwix request lanes and short-lived successful response cache."""
import asyncio
from collections import OrderedDict
import json
import time
import weakref
import xml.etree.ElementTree as ET
from . import search_cache

STATES=weakref.WeakKeyDictionary()
TTL=300
MAX_BYTES=8_000_000
MAX_ENTRIES=256


def state():
    loop=asyncio.get_running_loop()
    if loop not in STATES:STATES[loop]={'fulltext':asyncio.Semaphore(2),'title':asyncio.Semaphore(2),'cache':OrderedDict(),'flights':{}}
    return STATES[loop]


async def request(root,endpoint,path,kind,reader,*,generation='',timeout=None):
    shared=state();key=(str(root),endpoint,path+('\0'+generation if generation else ''));now=time.monotonic();prior=shared['cache'].get(key)
    if prior and now-prior[0]<TTL:return prior[1],True
    if prior:shared['cache'].pop(key,None)
    def validate(raw):
        if kind=='title':
            if not isinstance(json.loads(raw),list):raise ValueError('Invalid title response')
        else:
            tree=ET.fromstring(raw)
            if tree.tag!='rss' or tree.find('channel') is None:raise ValueError('Invalid search response')
    async def fetch():
        if generation:
            cached=await asyncio.to_thread(search_cache.read,root,key)
            if cached:
                try:validate(cached[0])
                except (ValueError,TypeError,ET.ParseError):cached=None
            if cached:
                task.cache_source='disk'
                shared['cache'][key]=(time.monotonic(),cached)
                trim();return cached
        async with shared[kind]:
            async with asyncio.timeout(timeout if timeout is not None else 2 if kind=='title' else 3):
                raw,content=await reader(path)
                validate(raw)
                result=(raw,content)
                if len(raw)<=1_000_000:
                    shared['cache'][key]=(time.monotonic(),result)
                    trim()
                    if generation:await asyncio.to_thread(search_cache.write,root,key,result)
                return result
    def trim():
        while len(shared['cache'])>MAX_ENTRIES or sum(len(value[1][0]) for value in shared['cache'].values())>MAX_BYTES:shared['cache'].popitem(last=False)
    flight_key=(key,timeout)
    task=shared['flights'].get(flight_key)
    if task is None:
        task=asyncio.create_task(fetch());shared['flights'][flight_key]=task
        task.search_waiters=0
        def finished(value):
            if shared['flights'].get(flight_key) is value:shared['flights'].pop(flight_key,None)
            if not value.cancelled():value.exception()
        task.add_done_callback(finished)
    task.search_waiters+=1
    try:return await asyncio.shield(task),getattr(task,'cache_source','')=='disk'
    finally:
        task.search_waiters-=1
        if task.search_waiters==0 and not task.done():
            if shared['flights'].get(flight_key) is task:shared['flights'].pop(flight_key,None)
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)


async def close():
    shared=STATES.pop(asyncio.get_running_loop(),None)
    if shared:
        tasks=list(shared['flights'].values())
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
