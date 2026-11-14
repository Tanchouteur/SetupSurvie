"""Rebuildable SQLite article indexes. Reading requires no libzim or model."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from urllib.parse import quote

from . import durable,retrieval

FORMAT=1


class Paused(Exception):pass


class ArticleText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0;self.language=''
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','nav'):self.skip+=1
        if tag=='html':self.language=dict(attrs).get('lang','').split('-')[0]
        if tag in ('p','h1','h2','h3','li','br'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','nav'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
    def text(self):return re.sub(r'[ \t]+',' ',' '.join(self.parts)).strip()


@contextmanager
def connect(path,readonly=False):
    path=Path(path).resolve()
    db=sqlite3.connect(path.as_uri()+'?mode=ro' if readonly else str(path),uri=readonly,timeout=2)
    db.row_factory=sqlite3.Row
    if readonly:db.execute('PRAGMA query_only=ON')
    try:yield db
    finally:db.close()


def status(root):
    path=Path(root)/'progress.json'
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {'phase':'not_prepared','archives':0,'articles':0}


def search(root,plan,language='',limit=40):
    if not plan.groups:return []
    deadline=time.monotonic()+3
    def one(path):
        try:
            with connect(path.resolve(),True) as db:
                db.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
                meta=json.loads(db.execute('SELECT value FROM metadata WHERE key=?',('source',)).fetchone()[0])
                if plan.collection and plan.collection not in retrieval.normal(meta['book']+' '+meta['title']).replace(' ',''):return []
                lang={'fra':'fr','eng':'en'}.get(language,language)
                rows=db.execute("SELECT path,title,language,substr(text,1,4000) AS _text,snippet(articles,2,'','','…',45) AS excerpt FROM articles WHERE articles MATCH ? AND (?='' OR language=?) ORDER BY bm25(articles,0,3,1,0) LIMIT ?",(plan.fts(),lang,lang,limit)).fetchall()
                return [{'id':'zim:'+meta['book']+'/'+r['path'],'title':r['title'],'language':r['language'],'excerpt':r['excerpt'],'_text':r['_text'],
                    'url':'/content/'+quote(meta['book']+'/'+r['path'],safe='/'),'book':meta['book'],'collection':meta['title'],'kind':'article','match':'local_index','_rank':i} for i,r in enumerate(rows)]
        except (OSError,sqlite3.Error,ValueError,KeyError,TypeError):return []
    paths=list(Path(root).glob('*.sqlite'))
    if not paths:return []
    with ThreadPoolExecutor(max_workers=min(8,max(1,os.cpu_count() or 1))) as pool:
        return [row for values in pool.map(one,paths) for row in values]


def metadata(archive,key,default=''):
    try:return archive.get_metadata(key).decode('utf-8',errors='replace')
    except (KeyError,RuntimeError):return default


def build_archive(source,root,*,cancel=None,force=False):
    """One process owns one archive. Every committed cursor is resumable."""
    from libzim.reader import Archive
    source=Path(source);root=Path(root);durable.mkdir(root)
    key=hashlib.sha256(source.name.encode()).hexdigest()[:24]
    published=root/(key+'.sqlite');building=root/(key+'.building')
    def check():
        if cancel and Path(cancel).exists():raise Paused()
        if shutil.disk_usage(root).free<1_000_000_000:raise OSError('Espace libre insuffisant pour poursuivre l’indexation.')
    check();stat=source.stat();archive=Archive(source)
    if archive.has_fulltext_index and not force:return {'archive':source.name,'status':'kiwix_index','articles':0}
    fingerprint=f'{FORMAT}:{archive.uuid}:{stat.st_size}:{stat.st_mtime_ns}'
    book=source.stem;info={'book':book,'title':metadata(archive,'Title',book),'language':metadata(archive,'Language'),'fingerprint':fingerprint}
    if published.is_file():
        try:
            with connect(published,True) as db:
                old=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
                if old['fingerprint']==fingerprint:return {'archive':source.name,'status':'ready','articles':int(db.execute("SELECT value FROM metadata WHERE key='articles'").fetchone()[0])}
        except (OSError,sqlite3.Error,ValueError,KeyError,TypeError):pass
    if building.exists():
        try:
            with connect(building) as db:old=db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()
            if not old or json.loads(old[0]).get('fingerprint')!=fingerprint:building.unlink()
        except (sqlite3.Error,ValueError):building.unlink()
    with connect(building) as db:
        db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT)')
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS articles USING fts5(path UNINDEXED,title,text,language UNINDEXED,tokenize='unicode61 remove_diacritics 2')")
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('source',json.dumps(info)))
        cursor=db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone();cursor=int(cursor[0]) if cursor else 0
        count=db.execute("SELECT value FROM metadata WHERE key='articles'").fetchone();count=int(count[0]) if count else 0
        skipped=0
        for index in range(cursor,archive.entry_count):
            check()
            # libzim 3.13.1 exposes entry enumeration under this pinned name.
            entry=archive._get_entry_by_id(index)
            if not entry.is_redirect:
                item=entry.get_item()
                if item.mimetype in ('text/html','application/xhtml+xml','text/plain') and item.size<=2_000_000:
                    raw=bytes(item.content).decode('utf-8',errors='replace')
                    parser=ArticleText();parser.feed(raw) if item.mimetype!='text/plain' else parser.parts.append(raw)
                    text=parser.text();language=parser.language or {'fra':'fr','eng':'en'}.get(info['language'],info['language'])
                    if text:
                        for start in range(0,min(len(text),500_000),2200):
                            db.execute('INSERT INTO articles VALUES(?,?,?,?)',(entry.path,entry.title,text[start:start+2400],language))
                        count+=1
                else:skipped+=1
            if (index+1)%64==0:
                db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('cursor',str(index+1)))
                db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('articles',str(count)));db.commit()
        current=source.stat()
        if current.st_size!=stat.st_size or current.st_mtime_ns!=stat.st_mtime_ns:raise OSError('Archive modifiée pendant l’indexation ; ancien index conservé.')
        db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('cursor',str(archive.entry_count)))
        db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('articles',str(count)));db.commit()
        db.execute("INSERT INTO articles(articles) VALUES('optimize')");db.commit()
    durable.sync_file(building);durable.publish(building,published)
    return {'archive':source.name,'status':'ready','articles':count,'skipped_entries':skipped}
