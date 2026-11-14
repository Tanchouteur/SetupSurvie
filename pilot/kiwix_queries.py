"""Bounded shared Kiwix request lanes and short-lived successful response cache."""
import asyncio
from collections import OrderedDict
import json
import time
import weakref
import xml.etree.ElementTree as ET

STATES=weakref.WeakKeyDictionary()
TTL=15
MAX_BYTES=8_000_000


def state():
    loop=asyncio.get_running_loop()
    if loop not in STATES:STATES[loop]={'fulltext':asyncio.Semaphore(2),'title':asyncio.Semaphore(2),'cache':OrderedDict(),'flights':{}}
    return STATES[loop]


async def request(root,endpoint,path,kind,reader):
    shared=state();key=(str(root),endpoint,path);now=time.monotonic();prior=shared['cache'].get(key)
    if prior and now-prior[0]<TTL:return prior[1],True
    if prior:shared['cache'].pop(key,None)
    async def fetch():
        async with shared[kind]:
            async with asyncio.timeout(2 if kind=='title' else 3):
                raw,content=await reader(path)
                if kind=='title':
                    if not isinstance(json.loads(raw),list):raise ValueError('Invalid title response')
                else:
                    tree=ET.fromstring(raw)
                    if tree.tag!='rss' or tree.find('channel') is None:raise ValueError('Invalid search response')
                result=(raw,content)
                if len(raw)<=1_000_000:
                    shared['cache'][key]=(time.monotonic(),result)
                    while len(shared['cache'])>64 or sum(len(value[1][0]) for value in shared['cache'].values())>MAX_BYTES:shared['cache'].popitem(last=False)
                return result
    task=shared['flights'].get(key)
    if task is None:
        task=asyncio.create_task(fetch());shared['flights'][key]=task
        def finished(value):
            if shared['flights'].get(key) is value:shared['flights'].pop(key,None)
            if not value.cancelled():value.exception()
        task.add_done_callback(finished)
    return await asyncio.shield(task),False


async def close():
    shared=STATES.pop(asyncio.get_running_loop(),None)
    if shared:
        tasks=list(shared['flights'].values())
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
