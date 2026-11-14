"""Bounded single-flight catalogue with a dated last-good snapshot and safe diagnostics."""
import asyncio
from collections import OrderedDict
import json
from pathlib import Path
import time
import weakref
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException
from . import durable,source_metadata

CACHE=OrderedDict()
FLIGHTS=weakref.WeakKeyDictionary()
TTL=30


class Catalog(list):
    def __init__(self,values=(),available=True,*,state=None,observed=None,error='',http_status=None,elapsed_ms=None):
        super().__init__(values);self.available=available;self.state=state or ('live' if available else 'unavailable')
        self.observed=observed;self.error=error;self.http_status=http_status;self.elapsed_ms=elapsed_ms
    def info(self):
        return {'state':self.state,'collections':len(self),'age_seconds':max(0,round(time.time()-self.observed)) if self.observed else None,
                'error':self.error or None,'http_status':self.http_status,'elapsed_ms':self.elapsed_ms}


def parse(raw):
    root=ET.fromstring(raw);ns={'a':'http://www.w3.org/2005/Atom'}
    if root.tag!='{http://www.w3.org/2005/Atom}feed':raise ValueError('Invalid catalogue format')
    result=[]
    for entry in root.findall('a:entry',ns):
        link=next((l.get('href','') for l in entry.findall('a:link',ns) if l.get('type')=='text/html'),'')
        if not link.startswith('/content/') or not link.removeprefix('/content/').strip('/'):continue
        fields={c.tag.rsplit('}',1)[-1]:c.text or '' for c in entry};tags=fields.get('tags','').split(';')
        identifier=fields.get('id','').removeprefix('urn:uuid:')
        import re
        result.append({'title':fields.get('title','')[:1000],'language':fields.get('language','')[:100],'book':link.removeprefix('/content/').strip('/'),
            'search_id':identifier if re.fullmatch(r'[0-9a-fA-F-]{36}',identifier) else '',
            'fulltext':False if '_ftindex:no' in tags else True if '_ftindex:yes' in tags else None,
            'description':fields.get('summary','')[:600],
            'archive_date':source_metadata.date_value(fields.get('updated',''),timestamp=True)})
    return result


def snapshot(root,endpoint):
    key=(str(Path(root).resolve()),endpoint)
    if key in CACHE:return key,CACHE[key]
    path=Path(root)/'kiwix-catalog.json'
    try:
        if path.stat().st_size>4_000_000:raise ValueError()
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or value['schema']!=1 or value['endpoint']!=endpoint or not isinstance(value['items'],list) or not all(isinstance(i,dict) and isinstance(i.get('book'),str) and isinstance(i.get('language',''),str) and i.get('fulltext') in (True,False,None) for i in value['items']):raise ValueError()
        if not isinstance(value['observed'],(int,float)):raise ValueError()
    except (OSError,ValueError,KeyError,TypeError):value=None
    return key,value


async def load(root,endpoint,reader,*,refresh=False):
    key,previous=snapshot(root,endpoint);now=time.time()
    if previous and not refresh and now-previous.get('checked',previous['observed'])<TTL:
        return Catalog(previous['items'],state='stale' if previous.get('error') else 'cached',observed=previous['observed'],error=previous.get('error',''))
    loop=asyncio.get_running_loop();flights=FLIGHTS.setdefault(loop,{})
    async def fetch():
        started=time.monotonic();error='';status=None
        try:
            raw,_=await asyncio.wait_for(reader('/catalog/v2/entries?count=-1',maximum=8_000_000),timeout=5)
            items=parse(raw);observed=time.time()
            value={'schema':1,'endpoint':endpoint,'observed':observed,'checked':observed,'items':items}
            CACHE[key]=value
            try:durable.write_bytes(Path(root)/'kiwix-catalog.json',json.dumps(value,ensure_ascii=False).encode('utf-8'),private=True)
            except OSError:pass
            return Catalog(items,observed=observed,elapsed_ms=round((time.monotonic()-started)*1000))
        except (TimeoutError,httpx.TimeoutException):error='catalog_timeout'
        except httpx.HTTPError:error='connection_error'
        except HTTPException as exc:
            status=getattr(exc,'upstream_status',exc.status_code);error='response_too_large' if exc.status_code==413 else 'http_error'
        except (ET.ParseError,ValueError,TypeError):error='invalid_catalog'
        elapsed=round((time.monotonic()-started)*1000)
        if previous:
            CACHE[key]={**previous,'checked':time.time()-TTL+5,'error':error}
            return Catalog(previous['items'],state='stale',observed=previous['observed'],error=error,http_status=status,elapsed_ms=elapsed)
        return Catalog(available=False,error=error,http_status=status,elapsed_ms=elapsed)
    task=flights.get(key)
    if task is None or task.done():
        task=asyncio.create_task(fetch());flights[key]=task
        def clear(finished):
            if flights.get(key) is finished:flights.pop(key,None)
        task.add_done_callback(clear)
    try:return await asyncio.shield(task)
    finally:
        while len(CACHE)>16:CACHE.popitem(last=False)
