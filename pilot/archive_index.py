"""Rebuildable SQLite article indexes. Reading requires no libzim or model."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from urllib.parse import quote

from . import durable,retrieval,wiki_structure
from .html_text import Text

FORMAT=2


class Paused(Exception):pass
class StorageReserve(OSError):pass
class ArchiveChanged(OSError):pass


class ArticleText(Text):
    def __init__(self):super().__init__(prefer_main=False)


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
    try:
        if path.stat().st_size>4_000_000:raise ValueError()
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or ('results' in value and not isinstance(value['results'],list)):raise ValueError()
        return value
    except (OSError,ValueError):return {'phase':'not_prepared','archives':0,'articles':0}


def manifest(root,source_dir=None):
    try:
        path=Path(root)/'manifest.json'
        if path.stat().st_size>4_000_000:raise ValueError()
        records=json.loads(path.read_text(encoding='utf-8'))['archives']
        if not isinstance(records,dict):raise ValueError()
    except (OSError,ValueError,KeyError,TypeError):records={r['archive']:r for r in status(root).get('results',[]) if isinstance(r,dict) and r.get('archive')}
    result={}
    for name,record in records.items():
        if not isinstance(name,str) or not isinstance(record,dict):continue
        if record.get('status') not in ('ready','kiwix_index'):continue
        if source_dir is not None and Path(source_dir).is_dir():
            path=Path(source_dir)/name
            if Path(name).name!=name or not path.is_file():continue
            stat=path.stat()
            if (record.get('bytes'),record.get('mtime_ns'))!=(stat.st_size,stat.st_mtime_ns):continue
        result[name]=record
    return result


class Matches(list):
    def __init__(self,values=(),coverage=None):super().__init__(values);self.coverage=coverage or {}


def index_name(archive):
    return hashlib.sha256(archive.encode()).hexdigest()[:24]


def search(root,plan,language='',limit=40,source_dir=None,*,collection_match=None,archive_allowed=None,category=None,only_path=None,skip_books=()):
    if not plan.groups:return Matches()
    if category is not None and category not in ('resilience','culture'):
        raise ValueError('Unknown archive index category')
    table='articles' if category is None else 'articles_'+category
    domains_column=',domains' if category else ''
    deadline=time.monotonic()+3
    def one(path):
        try:
            with connect(path.resolve(),True) as db:
                db.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
                meta=json.loads(db.execute('SELECT value FROM metadata WHERE key=?',('source',)).fetchone()[0])
                if meta['book'] in skip_books or (archive_allowed is not None and not archive_allowed(meta['book'])):return [],'excluded'
                if plan.collection:
                    allowed=collection_match(meta,plan.collection) if collection_match else plan.collection in retrieval.normal(meta['book']+' '+meta['title']).replace(' ','')
                    if not allowed:return [],'excluded'
                if source_dir is not None and Path(source_dir).is_dir():
                    source=Path(source_dir)/(meta['book']+'.zim')
                    if not source.is_file():return [],'outdated'
                    stat=source.stat();_,size,mtime=meta['fingerprint'].rsplit(':',2)
                    if (stat.st_size,stat.st_mtime_ns)!=(int(size),int(mtime)):return [],'outdated'
                lang={'fra':'fr','eng':'en'}.get(language,language)
                rows=db.execute(f"SELECT path,title,language,substr(text,1,4000) AS _text{domains_column},snippet({table},2,'','','…',45) AS excerpt FROM {table} WHERE {table} MATCH ? AND (?='' OR language=?) ORDER BY bm25({table},0,3,1,0) LIMIT ?",(plan.fts(),lang,lang,limit)).fetchall()
                return [{'id':'zim:'+meta['book']+'/'+r['path'],'title':r['title'],'language':r['language'],'excerpt':r['excerpt'],'_text':r['_text'],
                    'url':'/content/'+quote(meta['book']+'/'+r['path'],safe='/'),'book':meta['book'],'collection':meta['title'],'kind':'article','match':'local_index','_rank':i,**({'_indexed_domains':json.loads(r['domains'])} if category else {})} for i,r in enumerate(rows)],'searched'
        except (OSError,sqlite3.Error,ValueError,KeyError,TypeError):return [],'failed'
    if only_path is not None:
        paths=[Path(only_path)]
    elif archive_allowed is not None and source_dir is not None and Path(source_dir).is_dir():
        paths=[Path(root)/(index_name(source.name)+'.sqlite') for source in Path(source_dir).glob('*.zim')
               if source.stem not in skip_books and archive_allowed(source.stem)]
        paths=[path for path in paths if path.is_file()]
    else:
        paths=list(Path(root).glob('*.sqlite'))
    if not paths:return Matches(coverage={'searched':0,'failed':0,'outdated':0})
    with ThreadPoolExecutor(max_workers=min(8,max(1,os.cpu_count() or 1))) as pool:
        values=list(pool.map(one,paths))
        coverage={key:sum(status==key for _,status in values) for key in ('searched','failed','outdated')}
        return Matches([row for rows,_ in values for row in rows],coverage)


def metadata(archive,key,default=''):
    try:return archive.get_metadata(key).decode('utf-8',errors='replace')
    except (KeyError,RuntimeError):return default


def languages(value):
    return tuple(sorted(set(re.findall(r'[a-z]{2,3}',str(value).lower()))))


def build_archive(source,root,*,cancel=None,force=False,reserve=1_000_000_000,
                  categories=(),corrections=None,category_signature='',progress=None):
    """One process owns one archive. Every committed cursor is resumable."""
    from libzim.reader import Archive
    source=Path(source);root=Path(root);durable.mkdir(root)
    key=index_name(source.name)
    published=root/(key+'.sqlite');building=root/(key+'.building')
    tables=['articles_'+domain for domain in categories] or ['articles']
    correction_map=corrections or {}
    def check():
        if cancel and Path(cancel).exists():raise Paused()
        if shutil.disk_usage(root).free<reserve:raise StorageReserve('Espace libre insuffisant pour poursuivre l’indexation.')
    check();stat=source.stat();archive=Archive(source)
    native_languages=languages(metadata(archive,'Language'))
    native={'has_fulltext_index':bool(archive.has_fulltext_index),'native_languages':list(native_languages),
            'kiwix_language_compatible':len(native_languages)==1}
    if archive.has_fulltext_index and native['kiwix_language_compatible'] and not force:
        return {'archive':source.name,'status':'kiwix_index','articles':0,**native,'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
    reason='forced' if force else 'missing_index' if not archive.has_fulltext_index else 'native_multilingual' if native_languages else 'native_language_missing'
    fingerprint=f'{FORMAT}:{archive.uuid}:{category_signature}:{stat.st_size}:{stat.st_mtime_ns}' if categories else f'{FORMAT}:{archive.uuid}:{stat.st_size}:{stat.st_mtime_ns}'
    book=source.stem;info={'book':book,'title':metadata(archive,'Title',book),'language':metadata(archive,'Language'),'fingerprint':fingerprint}
    if published.is_file():
        try:
            with connect(published,True) as db:
                old=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
                if old['fingerprint']==fingerprint:return {'archive':source.name,'status':'ready',**native,'index_reason':reason,'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'articles':int(db.execute("SELECT value FROM metadata WHERE key='articles'").fetchone()[0])}
        except (OSError,sqlite3.Error,ValueError,KeyError,TypeError):pass
    if building.exists():
        try:
            with connect(building) as db:old=db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()
            if not old or json.loads(old[0]).get('fingerprint')!=fingerprint:building.unlink()
        except (sqlite3.Error,ValueError):building.unlink()
    with connect(building) as db:
        db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT)')
        extra=',domains UNINDEXED' if categories else ''
        for table in tables:
            db.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5(path UNINDEXED,title,text,language UNINDEXED{extra},tokenize='unicode61 remove_diacritics 2')")
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('source',json.dumps(info)))
        cursor=db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone();cursor=int(cursor[0]) if cursor else 0
        count=db.execute("SELECT value FROM metadata WHERE key='articles'").fetchone();count=int(count[0]) if count else 0
        counts_row=db.execute("SELECT value FROM metadata WHERE key='category_counts'").fetchone()
        counts=json.loads(counts_row[0]) if counts_row else dict.fromkeys(categories,0)
        skipped=0
        if progress:progress(cursor,archive.entry_count,counts)
        entry_by_id=getattr(archive,'get_entry_by_id',None) or archive._get_entry_by_id  # libzim 4.x / 3.13.1
        for index in range(cursor,archive.entry_count):
            if not categories or index%64==0:check()
            elif cancel and Path(cancel).exists():raise Paused()
            entry=entry_by_id(index)
            if not entry.is_redirect:
                item=entry.get_item()
                if item.mimetype in ('text/html','application/xhtml+xml','text/plain') and item.size<=2_000_000:
                    raw=bytes(item.content).decode('utf-8',errors='replace')
                    parser=ArticleText();parser.feed(raw) if item.mimetype!='text/plain' else parser.parts.append(raw)
                    text=parser.text();language=parser.language or {'fra':'fr','eng':'en'}.get(info['language'],info['language'])
                    if text:
                        selected=tables
                        if categories:
                            domains=correction_map.get(entry.path)
                            if domains is None:
                                candidate={'id':'zim:'+book+'/'+entry.path,'title':entry.title,'_text':text}
                                if item.mimetype!='text/plain':
                                    candidate['_wiki_structure']=wiki_structure.extract(raw[:wiki_structure.MAX_HTML].encode('utf-8'))
                                domains=retrieval.domains(candidate)
                            selected=['articles_'+domain for domain in categories if domain in domains]
                            for domain in domains:
                                if domain in counts:counts[domain]+=1
                        suffix=(json.dumps(domains),) if categories else ()
                        values='?,?,?,?,?' if categories else '?,?,?,?'
                        for table in selected:
                            db.executemany(f'INSERT INTO {table} VALUES({values})',
                                ((entry.path,entry.title,text[start:start+2400],language,*suffix)
                                 for start in range(0,min(len(text),500_000),2200)))
                        count+=1
                else:skipped+=1
            if (index+1)%64==0:
                db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('cursor',str(index+1)))
                db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('articles',str(count)))
                if categories:db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('category_counts',json.dumps(counts)))
                db.commit()
                if progress and (index+1)%1024==0:progress(index+1,archive.entry_count,counts)
        current=source.stat()
        if current.st_size!=stat.st_size or current.st_mtime_ns!=stat.st_mtime_ns:raise ArchiveChanged('Archive modifiée pendant l’indexation ; ancien index conservé.')
        db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('cursor',str(archive.entry_count)))
        db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('articles',str(count)))
        if categories:db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('category_counts',json.dumps(counts)))
        db.commit()
        if progress:progress(archive.entry_count,archive.entry_count,counts)
        for table in tables:db.execute(f"INSERT INTO {table}({table}) VALUES('optimize')")
        db.commit()
    durable.sync_file(building);durable.publish(building,published)
    return {'archive':source.name,'status':'ready',**native,'index_reason':reason,'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'articles':count,'skipped_entries':skipped}
