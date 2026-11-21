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
import zlib

from . import durable,retrieval,wiki_structure
from .html_text import Text

FORMAT=2
TOKENIZE="tokenize='unicode61 remove_diacritics 2'"
# Since 0.88.0 the article text is stored once, zlib-compressed, in `docs`; the
# FTS table reads it through a view (external content). Ranking only uses the
# FTS index, so results stay identical while the file shrinks by about 40 %.
# Older indexes, with the text inside the FTS table, stay readable.
COMPRESSED_TABLE='docs'


def unz(blob):
    return zlib.decompress(blob).decode('utf-8') if blob is not None else None


def is_compressed(db):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(COMPRESSED_TABLE,)).fetchone() is not None


def _create_tables(db,tables,domains,compressed):
    extra=',domains UNINDEXED' if domains else ''
    options=''
    if compressed:
        column=',domains' if domains else ''
        db.execute(f'CREATE TABLE IF NOT EXISTS {COMPRESSED_TABLE}(id INTEGER PRIMARY KEY,path TEXT,title TEXT,ztext BLOB,language TEXT{column})')
        db.execute(f'CREATE VIEW IF NOT EXISTS docs_text AS SELECT id,path,title,unz(ztext) AS text,language{column} FROM {COMPRESSED_TABLE}')
        options=",content='docs_text',content_rowid='id'"
    for table in tables:
        db.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5(path UNINDEXED,title,text,language UNINDEXED{extra},{TOKENIZE}{options})")


def _insert(db,table,rows,compressed):
    """Rows are (path,title,text,language[,domains]), kept in insertion order."""
    for row in rows:
        marks=','.join('?'*len(row))
        if not compressed:
            db.execute(f'INSERT INTO {table} VALUES({marks})',row)
            continue
        names='path,title,text,language'+(',domains' if len(row)==5 else '')
        packed=(row[0],row[1],zlib.compress(row[2].encode('utf-8'),6),*row[3:])
        identifier=db.execute(f"INSERT INTO {COMPRESSED_TABLE}({names.replace('text','ztext')}) VALUES({marks})",packed).lastrowid
        # External content: the FTS index is fed explicitly with the same rowid.
        db.execute(f'INSERT INTO {table}(rowid,{names}) VALUES(?,{marks})',(identifier,*row))


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
    db.create_function('unz',1,unz,deterministic=True)
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
                compressed = table == 'articles' and is_compressed(db)
                # Compressed indexes filter on the plain columns of `docs`, so
                # ranking never decompresses the text of the candidates.
                column = 'd.' if compressed else ''
                category_filter = f' AND instr({column}domains, ?) > 0' if shared else ''
                lang={'fra':'fr','eng':'en'}.get(language,language)
                language_filter = f" AND (?='' OR {column}language=?)"
                parameters = (plan.fts(), lang, lang)
                if lang and retrieval.ifixit_edition(meta['book']):
                    # Old local indexes trusted the HTML hint. Read the
                    # candidates and classify them using the same rule as Kiwix.
                    db.create_function('article_language', 2, lambda hint, text: retrieval.article_language({
                        'book': meta['book'], 'language': hint, 'text': text,
                    }), deterministic=True)
                    text = 'unz(d.ztext)' if compressed else 'text'
                    language_filter = f' AND article_language({column}language, substr({text},1,4000))=?'
                    parameters = (plan.fts(), lang)
                parameters += ((json.dumps(category),) if shared else ()) + (limit,)
                shown=f"path,title,language,substr(text,1,4000) AS _text{domains_column},snippet({table},2,'','','…',45) AS excerpt"
                if compressed:
                    ids=[row[0] for row in db.execute(f"SELECT {table}.rowid FROM {table} JOIN {COMPRESSED_TABLE} d ON d.id={table}.rowid WHERE {table} MATCH ?{language_filter}{category_filter} ORDER BY bm25({table},0,3,1,0) LIMIT ?",parameters)]
                    found={row['rowid']:row for row in db.execute(f"SELECT rowid,{shown} FROM {table} WHERE {table} MATCH ? AND rowid IN ({','.join('?'*len(ids))})",(plan.fts(),*ids))} if ids else {}
                    rows=[found[identifier] for identifier in ids if identifier in found]
                else:
                    rows=db.execute(f"SELECT {shown} FROM {table} WHERE {table} MATCH ?{language_filter}{category_filter} ORDER BY bm25({table},0,3,1,0) LIMIT ?",parameters).fetchall()
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
        # A build resumed from an older release keeps the format it started with.
        started = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='articles'").fetchone()
        compressed = not legacy and (not started or is_compressed(db))
        _create_tables(db,tables,bool(categories),compressed)
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
                    for table in selected:
                        _insert(db, table, ((path, title, text[start:start+2400], language, *suffix)
                                            for start in range(0, min(len(text), 500_000), 2200)), compressed)
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


def compress(published,*,cancel=None,reserve=1_000_000_000,batch=2000):
    """Rewrite a published index in the compressed format, without the ZIM.

    The same rows are copied in the same order, so search results are unchanged.
    The old file stays published until the new one is complete and verified.
    Returns the new size, or None when there is nothing to convert."""
    published=Path(published);work=published.with_suffix('.compressing')
    before=published.stat()
    def check():
        if cancel and Path(cancel).exists():raise Paused()
        if shutil.disk_usage(published.parent).free<reserve:raise StorageReserve('Espace libre insuffisant pour compresser l’index.')
    with connect(published,True) as source:
        names={row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        if COMPRESSED_TABLE in names or 'articles' not in names:return None
    # The new file is about 60 % of the old one; keep the usual reserve on top.
    if shutil.disk_usage(published.parent).free<before.st_size*0.7+reserve:
        raise StorageReserve('Espace libre insuffisant pour compresser l’index.')
    work.unlink(missing_ok=True)
    try:
        # The source is closed before publishing: Windows refuses to replace an open file.
        with connect(published,True) as source,connect(work) as db:
            domains='domains' in {row[1] for row in source.execute('PRAGMA table_info(articles)')}
            # A crash only leaves a work file, deleted at the next attempt.
            db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
            db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
            db.executemany('INSERT INTO metadata VALUES(?,?)',source.execute('SELECT key,value FROM metadata'))
            _create_tables(db,['articles'],domains,True)
            columns='path,title,text,language'+(',domains' if domains else '')
            rows=source.execute(f'SELECT {columns} FROM articles ORDER BY rowid')
            copied=0
            while chunk:=rows.fetchmany(batch):
                check()
                _insert(db,'articles',(tuple(row) for row in chunk),True)
                copied+=len(chunk)
                db.commit()
            expected=source.execute('SELECT count(*) FROM articles').fetchone()[0]
            if copied!=expected or db.execute(f'SELECT count(*) FROM {COMPRESSED_TABLE}').fetchone()[0]!=expected:
                raise sqlite3.DatabaseError('Copie incomplète de l’index.')
            db.execute("INSERT INTO articles(articles) VALUES('optimize')")
            db.commit()
            db.execute("INSERT INTO articles(articles,rank) VALUES('integrity-check',0)")
        current=published.stat()
        if (current.st_size,current.st_mtime_ns)!=(before.st_size,before.st_mtime_ns):
            raise ArchiveChanged('Index republié pendant la compression ; nouvelle version conservée.')
        durable.sync_file(work);durable.publish(work,published)
    except BaseException:
        work.unlink(missing_ok=True)
        raise
    return published.stat().st_size
