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
    if loop not in STATES:STATES[loop]={'fulltext':asyncio.Semaphore(2),'title':asyncio.Semaphore(2),'cache':OrderedDict(),'structure_lane':asyncio.Semaphore(2),'structures':OrderedDict(),'flights':{},'retiring':set(),'pending':OrderedDict(),'writer':None}
    return STATES[loop]


async def disk_io(operation,*args):
    """Cancellation must not leave a thread using a SQLite file after teardown."""
    task=asyncio.create_task(asyncio.to_thread(operation,*args))
    try:return await asyncio.shield(task)
    except asyncio.CancelledError:
        while not task.done():
            # The caller was cancelled (or timed out): report that, even if the
            # thread later fails, so wait_for() still raises TimeoutError.
            try:await asyncio.shield(task)
            except asyncio.CancelledError:pass
            except Exception:pass
        if not task.cancelled():task.exception()
        raise


def remember_on_disk(shared,root,key,result):
    pending=shared['pending'];pending[key]=(root,key,result)
    while len(pending)>MAX_ENTRIES or sum(len(value[2][0]) for value in pending.values())>MAX_BYTES:pending.popitem(last=False)
    async def write_all():
        try:
            while pending:
                _,arguments=pending.popitem(last=False)
                try:await disk_io(search_cache.write,*arguments)
                except Exception:pass # Optional persistence never fails a search.
        finally:pending.clear()
    if shared['writer'] is None or shared['writer'].done():shared['writer']=asyncio.create_task(write_all())


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
        if generation and search_cache.budget():
            cached=await disk_io(search_cache.read,root,key)
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
                    if generation and search_cache.budget():remember_on_disk(shared,root,key,result)
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
            shared['retiring'].discard(value)
            if not value.cancelled():value.exception()
        task.add_done_callback(finished)
    task.search_waiters+=1
    try:return await asyncio.shield(task),getattr(task,'cache_source','')=='disk'
    finally:
        task.search_waiters-=1
        if task.search_waiters==0 and not task.done():
            # Stop sharing the cancelled request immediately, but retain its
            # file user until disk_io has really joined the executor thread.
            # A sibling's gather cancellation may return before this finally.
            shared['retiring'].add(task)
            if shared['flights'].get(flight_key) is task:shared['flights'].pop(flight_key,None)
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)


async def close():
    shared=STATES.pop(asyncio.get_running_loop(),None)
    if shared:
        tasks=list(set(shared['flights'].values())|shared['retiring'])
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        if shared['writer']:await asyncio.gather(shared['writer'],return_exceptions=True)
