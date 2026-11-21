"""Rebuildable SQLite article indexes. Reading requires no libzim or model."""
from collections import deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import closing, contextmanager
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


def search(root,plan,language='',limit=40,source_dir=None,*,collection_match=None,archive_allowed=None,category=None,only_path=None,skip_books=(),index_paths=None):
    if not plan.groups:return Matches()
    if category is not None and category not in ('resilience','culture'):
        raise ValueError('Unknown archive index category')
    domains_column=',domains' if category else ''
    deadline=time.monotonic()+3
    def one(path):
        try:
            with connect(path.resolve(),True) as db:
                db.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
                meta=json.loads(db.execute('SELECT value FROM metadata WHERE key=?',('source',)).fetchone()[0])
                if meta['book'] in skip_books or (archive_allowed is not None and not archive_allowed(meta['book'])):return [],'excluded',None
                if plan.collection:
                    allowed=collection_match(meta,plan.collection) if collection_match else plan.collection in retrieval.normal(meta['book']+' '+meta['title']).replace(' ','')
                    if not allowed:return [],'excluded',None
                if source_dir is not None and Path(source_dir).is_dir():
                    source=Path(source_dir)/(meta['book']+'.zim')
                    if not source.is_file():return [],'outdated',None
                    stat=source.stat();_,size,mtime=meta['fingerprint'].rsplit(':',2)
                    if (stat.st_size,stat.st_mtime_ns)!=(int(size),int(mtime)):return [],'outdated',None
                shared = category is not None and db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='articles'").fetchone() is not None
                table = 'articles_' + category if category and not shared else 'articles'
                category_filter = ' AND instr(domains, ?) > 0' if shared else ''
                lang={'fra':'fr','eng':'en'}.get(language,language)
                language_filter = " AND (?='' OR language=?)"
                parameters = (plan.fts(), lang, lang)
                if lang and retrieval.ifixit_edition(meta['book']):
                    # Old local indexes trusted the HTML hint. Read the
                    # candidates and classify them using the same rule as Kiwix.
                    db.create_function('article_language', 2, lambda hint, text: retrieval.article_language({
                        'book': meta['book'], 'language': hint, 'text': text,
                    }), deterministic=True)
                    language_filter = ' AND article_language(language, substr(text,1,4000))=?'
                    parameters = (plan.fts(), lang)
                parameters += ((json.dumps(category),) if shared else ()) + (limit,)
                rows=db.execute(f"SELECT path,title,language,substr(text,1,4000) AS _text{domains_column},snippet({table},2,'','','…',45) AS excerpt FROM {table} WHERE {table} MATCH ?{language_filter}{category_filter} ORDER BY bm25({table},0,3,1,0) LIMIT ?",parameters).fetchall()
                return [{'id':'zim:'+meta['book']+'/'+r['path'],'title':r['title'],'language':r['language'],'excerpt':r['excerpt'],'_text':r['_text'],
                    'url':'/content/'+quote(meta['book']+'/'+r['path'],safe='/'),'book':meta['book'],'collection':meta['title'],'kind':'article','match':'local_index','_rank':i,**({'_indexed_domains':json.loads(r['domains'])} if category else {})} for i,r in enumerate(rows)],'searched',meta['book']
        except (OSError,sqlite3.Error,ValueError,KeyError,TypeError):return [],'failed',None
    if index_paths is not None:
        paths = list(index_paths)
    elif only_path is not None:
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
        coverage={key:sum(status==key for _,status,_ in values) for key in ('searched','failed','outdated')}
        if category is not None:
            coverage['books'] = [book for _, status, book in values if status == 'searched']
        return Matches([row for rows, _, _ in values for row in rows],coverage)


def metadata(archive,key,default=''):
    try:return archive.get_metadata(key).decode('utf-8',errors='replace')
    except (KeyError,RuntimeError):return default


def languages(value):
    return tuple(sorted(set(re.findall(r'[a-z]{2,3}',str(value).lower()))))


def _article(entry, info, categories, corrections):
    if entry.is_redirect:
        return None, False
    item = entry.get_item()
    if item.mimetype not in ('text/html', 'application/xhtml+xml', 'text/plain') or item.size > 2_000_000:
        return None, True
    raw = bytes(item.content).decode('utf-8', errors='replace')
    parser = ArticleText()
    if item.mimetype == 'text/plain':
        parser.parts.append(raw)
    else:
        parser.feed(raw)
    text = parser.text()
    if not text:
        return None, False
    language = retrieval.article_language({'id': 'zim:' + info['book'] + '/' + entry.path,
        'book': info['book'], 'language': parser.language or info['language'], 'text': text})
    domains = corrections.get(entry.path)
    if categories and domains is None:
        candidate = {'id': 'zim:' + info['book'] + '/' + entry.path, 'title': entry.title, '_text': text}
        if wiki_structure.wikipedia(candidate) and item.mimetype != 'text/plain':
            candidate['_wiki_structure'] = wiki_structure.extract(raw[:wiki_structure.MAX_HTML].encode('utf-8'))
        domains = retrieval.application_domains(candidate)
    return (entry.path, entry.title, text[:502_400], language, domains), False


def _entry_reader(archive):
    return getattr(archive, 'get_entry_by_id', None) or archive._get_entry_by_id


def _init_category_reader(source, info, categories, corrections):
    from libzim.reader import Archive
    global _category_reader
    _category_reader = (_entry_reader(Archive(source)), info, categories, corrections)


def _read_category_batch(bounds):
    read, info, categories, corrections = _category_reader
    return [_article(read(index), info, categories, corrections) for index in range(*bounds)]


def _articles(source, archive, cursor, info, categories, corrections, workers):
    total = archive.entry_count
    if not categories or workers <= 1 or total - cursor < 512:
        read = _entry_reader(archive)
        for index in range(cursor, total):
            yield _article(read(index), info, categories, corrections)
        return
    # Keep a bounded window of batches and consume them in archive order.
    # SQLite has one writer, so the existing cursor still resumes exactly.
    batch_size = 16
    bounds = iter((start, min(start + batch_size, total)) for start in range(cursor, total, batch_size))
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_category_reader,
                             initargs=(source, info, categories, corrections)) as pool:
        pending = deque(pool.submit(_read_category_batch, batch)
                        for _, batch in zip(range(workers * 2), bounds))
        while pending:
            yield from pending.popleft().result()
            batch = next(bounds, None)
            if batch is not None:
                pending.append(pool.submit(_read_category_batch, batch))


def build_archive(source,root,*,cancel=None,force=False,reserve=1_000_000_000,
                  categories=(),corrections=None,category_signature='',progress=None,workers=1):
    """One process owns one archive. Every committed cursor is resumable."""
    from libzim.reader import Archive
    source=Path(source);root=Path(root);durable.mkdir(root)
    key=index_name(source.name)
    published=root/(key+'.sqlite');building=root/(key+'.building')
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
        legacy = categories and db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='articles_resilience'").fetchone()
        tables = ['articles_' + domain for domain in categories] if legacy else ['articles']
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
        articles = _articles(source, archive, cursor, info, categories, correction_map, workers)
        with closing(articles):
            for index, (article, skipped_entry) in enumerate(articles, cursor):
                if not categories or index % 64 == 0:
                    check()
                elif cancel and Path(cancel).exists():
                    raise Paused()
                skipped += skipped_entry
                if article:
                    path, title, text, language, domains = article
                    selected = tables
                    if categories:
                        if legacy:
                            selected = ['articles_' + domain for domain in categories if domain in domains]
                        for domain in domains:
                            if domain in counts:
                                counts[domain] += 1
                    suffix = (json.dumps(domains),) if categories else ()
                    values = '?,?,?,?,?' if categories else '?,?,?,?'
                    for table in selected:
                        db.executemany(f'INSERT INTO {table} VALUES({values})',
                            ((path, title, text[start:start+2400], language, *suffix)
                             for start in range(0, min(len(text), 500_000), 2200)))
                    count += 1
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
