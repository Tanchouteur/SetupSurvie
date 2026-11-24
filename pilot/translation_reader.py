"""Read only published French text; drafts, source snapshots and accounts stay private."""
from collections import OrderedDict
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import threading
from fastapi import HTTPException
from . import catalogue,library,publications,store

CACHE=OrderedDict();CACHE_LOCK=threading.Lock();CACHE_BYTES=0
MAX_CACHE_BYTES=64_000_000


class Pages(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.pages={};self.page=None;self.part=None;self.notice=None
    def handle_starttag(self,tag,attrs):
        attrs={k:v or '' for k,v in attrs}
        if tag=='section':
            match=re.fullmatch(r'page=([1-9]\d{0,3})',attrs.get('id',''))
            self.page=int(match[1]) if match and int(match[1])<=1200 else None
            if self.page:self.pages.setdefault(self.page,{'parts':[],'warnings':[]})
        if tag=='p' and self.page:
            if 'part' in attrs.get('class','').split():self.part=[]
            elif 'notice' in attrs.get('class','').split():self.notice=[]
    def handle_data(self,text):
        if self.part is not None:self.part.append(text)
        elif self.notice is not None:self.notice.append(text)
    def handle_endtag(self,tag):
        if tag=='p' and self.page:
            if self.part is not None:self.pages[self.page]['parts'].append(''.join(self.part));self.part=None
            if self.notice is not None:self.pages[self.page]['warnings'].append(''.join(self.notice));self.notice=None
        if tag=='section':self.page=None;self.part=None;self.notice=None


def source_key(identifier):
    key=catalogue.canonical(identifier)
    if not key.startswith(('guide:','zim:')):raise HTTPException(400,'Document original requis.')
    return key


def current_revision(identifier):
    return catalogue.revision(identifier,library.GUIDES,Path(os.environ.get('ZIM_DIR','/zim')))


def publication_path(path):
    if not isinstance(path,str) or not re.fullmatch(r'TRAD-(?:[a-f0-9]{32}|[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})\.fr\.html',path):raise HTTPException(404,'Traduction publiée introuvable.')
    target=library.GUIDES/path
    if any(p.is_symlink() for p in [target,*target.parents]) or not target.resolve().is_relative_to(library.GUIDES.resolve()):raise HTTPException(404,'Traduction publiée indisponible.')
    return target


def publication(path,expected=None):
    global CACHE_BYTES
    if expected and (not isinstance(expected,str) or not re.fullmatch(r'[a-f0-9]{64}',expected)):raise HTTPException(422,'Empreinte de traduction indisponible.')
    target=publication_path(path)
    try:
        before=target.stat()
        if not 0<before.st_size<=128_000_000:raise HTTPException(413,'Cette traduction est trop volumineuse pour ce lecteur. Ouvrez le document partagé.')
        key=(str(target),before.st_size,before.st_mtime_ns,expected)
        with CACHE_LOCK:
            if key in CACHE:CACHE.move_to_end(key);return CACHE[key][0]
        raw=target.read_bytes();after=target.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):raise HTTPException(409,'La traduction a changé pendant sa lecture. Réessayez.')
    except OSError:raise HTTPException(404,'Fichier de traduction publié indisponible.') from None
    if expected and hashlib.sha256(raw).hexdigest()!=expected:raise HTTPException(409,'La traduction publiée a été modifiée. Ouvrez le document partagé pour l’examiner.')
    try:parser=Pages();parser.feed(raw.decode('utf-8'));parser.close()
    except (ValueError,UnicodeError):raise HTTPException(422,'Le texte publié ne peut pas être lu dans ce lecteur.') from None
    if not parser.pages:raise HTTPException(422,'Le texte publié ne fournit pas de pages lisibles dans ce lecteur.')
    value=parser.pages;weight=len(raw)
    if weight<=MAX_CACHE_BYTES:
        with CACHE_LOCK:
            if key not in CACHE:
                while CACHE and (CACHE_BYTES+weight>MAX_CACHE_BYTES or len(CACHE)>=16):CACHE_BYTES-=CACHE.popitem(last=False)[1][1]
                CACHE[key]=(value,weight);CACHE_BYTES+=weight
    return value


def choices(identifier):
    original=source_key(identifier);revision=current_revision(original);result=[]
    literal=identifier.split('#page=')[0] if identifier.startswith('guide:') else identifier
    with store.connect() as db:
        rows=db.execute('SELECT published_path,title,source_meta,published_at FROM translation_publications WHERE source_id IN (?,?) AND published_at IS NOT NULL ORDER BY published_at DESC LIMIT 12',(original,literal)).fetchall()
    for row in rows:
        try:
            meta=json.loads(row['source_meta'])
            if not isinstance(meta,dict):continue
            # Opening an original must not parse twelve translated books. Text
            # and its integrity are checked only after a reader asks to open it.
            if not publication_path(row['published_path']).is_file():continue
            pages=meta.get('published_pages',[])
            pages=sorted(set(pages)) if isinstance(pages,list) and len(pages)<=1200 and all(type(page) is int and 1<=page<=1200 for page in pages) else []
            saved=meta.get('source_revision');freshness='unchanged' if revision and saved and revision==saved else 'changed' if revision and saved else 'unknown'
            result.append({'id':'guide:'+row['published_path'],'title':row['title'],'published_at':row['published_at'],'pages':pages,
                'freshness':freshness,'partial':bool(meta.get('published_missing')),'missing':meta.get('published_missing',0),'integrity_recorded':bool(meta.get('published_sha256')),
                'original_document_date':meta.get('document_date',''),'original_edition':meta.get('edition','')})
        except (HTTPException,OSError,ValueError,TypeError):continue
    return {'original_id':original,'translations':result,'notice':publications.NOTICE}


def page(identifier,original_id,number):
    original=source_key(original_id)
    if not isinstance(identifier,str) or not identifier.startswith('guide:'):raise HTTPException(400,'Traduction publiée requise.')
    path=identifier.removeprefix('guide:')
    with store.connect() as db:row=db.execute('SELECT source_id,title,source_meta FROM translation_publications WHERE published_path=? AND published_at IS NOT NULL',(path,)).fetchone()
    if not row or source_key(row['source_id'])!=original:raise HTTPException(404,'Cette traduction ne correspond pas au document demandé.')
    try:meta=json.loads(row['source_meta'])
    except (ValueError,TypeError):raise HTTPException(422,'Métadonnées de traduction indisponibles.') from None
    if not isinstance(meta,dict):raise HTTPException(422,'Métadonnées de traduction indisponibles.')
    pages=publication(path,meta.get('published_sha256'))
    completeness={'partial':bool(meta.get('published_missing')),'missing':meta.get('published_missing',0)}
    if number not in pages:return {'page':number,'available':False,'pages':sorted(pages),'notice':publications.NOTICE,**completeness}
    current=current_revision(original);saved=meta.get('source_revision')
    return {'page':number,'available':True,'pages':sorted(pages),'title':row['title'],'original_id':original,
        'freshness':'unchanged' if current and saved and current==saved else 'changed' if current and saved else 'unknown',
        'notice':publications.NOTICE,**completeness,'parts':pages[number]['parts'],'warnings':pages[number]['warnings']}
