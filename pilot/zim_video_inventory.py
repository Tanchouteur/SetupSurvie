"""Inspect archive media without downloading, decoding or changing any source.

This is the host reader side. The portal will read the resulting SQLite files
without loading libzim. Existing native text indexes are not video inventories.
"""
from contextlib import contextmanager
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import shutil
import sqlite3
import time
from urllib.parse import unquote,urlsplit

from . import durable

FORMAT=1
MAX_HTML=2_000_000
MAX_VIDEOS_PER_PAGE=100
MAX_TRACKS_PER_VIDEO=100


def resolve(article,reference,base=''):
    """Resolve archive-relative URLs; remote links remain references, never files."""
    if not isinstance(reference,str) or len(reference)>4000:return {'status':'invalid_reference'}
    reference=reference.strip()
    try:parsed=urlsplit(reference)
    except ValueError:return {'status':'invalid_reference'}
    if parsed.scheme or parsed.netloc:
        return {'status':'remote_reference','url':reference} if parsed.scheme in ('http','https') or not parsed.scheme and parsed.netloc else {'status':'unsupported_reference'}
    if not parsed.path:return {'status':'invalid_reference'}
    if base:
        # A remote HTML base makes relative URLs remote too. Do not resolve a
        # network URL by filename against a coincidentally present local media.
        try:base_url=urlsplit(base)
        except ValueError:return {'status':'invalid_reference'}
        if base_url.scheme or base_url.netloc:return {'status':'remote_reference','url':reference,'base':base}
    decoded=unquote(parsed.path)
    if '\\' in decoded or any(ord(c)<32 for c in decoded):return {'status':'invalid_reference'}
    root=posixpath.dirname(article)
    if base:
        resolved=resolve(article,base)
        if resolved['status']!='internal':return resolved
        root=resolved['path'] if base.endswith('/') else posixpath.dirname(resolved['path'])
    path=posixpath.normpath(decoded.lstrip('/') if decoded.startswith('/') else posixpath.join(root,decoded))
    if path in ('','.','..') or path.startswith('../'):return {'status':'invalid_reference'}
    return {'status':'internal','path':path,'query':parsed.query[:1000],'fragment':parsed.fragment[:1000]}


class Videos(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.items=[];self.active=None;self.base='';self.errors=[];self.skip=0

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('script','style'):self.skip+=1;return
        if self.skip:return
        if tag=='base' and not self.base:self.base=attrs.get('href','')[:4000]
        if tag=='video':
            if len(self.items)>=MAX_VIDEOS_PER_PAGE:self.errors.append('video_reference_limit');self.active=None;return
            self.active={'sources':[],'tracks':[],'title':str(attrs.get('title') or attrs.get('aria-label') or '')[:400]}
            self.items.append(self.active)
            if attrs.get('src') or attrs.get('data-src'):self.active['sources'].append({'src':attrs.get('src') or attrs['data-src'],'type':''})
        elif tag=='source' and self.active is not None and (attrs.get('src') or attrs.get('data-src')):
            if len(self.active['sources'])<100:self.active['sources'].append({'src':attrs.get('src') or attrs['data-src'],'type':str(attrs.get('type') or '')[:120]})
            else:self.errors.append('media_source_limit')
        elif tag=='track' and self.active is not None and (attrs.get('src') or attrs.get('data-src')):
            if len(self.active['tracks'])>=MAX_TRACKS_PER_VIDEO:self.errors.append('subtitle_reference_limit');return
            self.active['tracks'].append({'src':attrs.get('src') or attrs['data-src'],'language_declared':str(attrs.get('srclang') or '')[:40],
                'label':str(attrs.get('label') or '')[:120],'kind':str(attrs.get('kind') or 'subtitles')[:40]})
        elif tag=='iframe' and attrs.get('src'):
            url=attrs['src']
            try:host=(urlsplit(url).hostname or '').lower()
            except ValueError:return
            if host in ('www.youtube.com','youtube.com','www.youtube-nocookie.com','youtube-nocookie.com','player.vimeo.com'):
                if len(self.items)<MAX_VIDEOS_PER_PAGE:self.items.append({'sources':[{'src':url[:4000],'type':'remote_embed'}],'tracks':[],'title':str(attrs.get('title') or '')[:400]})
                else:self.errors.append('video_reference_limit')

    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag=='video':self.active=None


@contextmanager
def connect(path,readonly=False):
    path=Path(path)
    if path.is_symlink():raise ValueError('Inventory link refused')
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro' if readonly else path,uri=readonly,timeout=10)
    db.row_factory=sqlite3.Row
    if readonly:db.execute('PRAGMA query_only=ON')
    else:db.execute('PRAGMA synchronous=FULL')
    try:
        with db:yield db
    finally:db.close()


class Paused(Exception):pass
class ArchiveChanged(Exception):pass


def fingerprint(source,archive):
    info=source.stat()
    return {'format':FORMAT,'uuid':str(archive.uuid),'bytes':info.st_size,'mtime_ns':info.st_mtime_ns}


def summary(db):
    value=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
    value.update(entries_examined=int(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0]),
        video_resources=db.execute("SELECT count(*) FROM resources WHERE category='video'").fetchone()[0],
        subtitle_resources=db.execute("SELECT count(*) FROM resources WHERE category='subtitle'").fetchone()[0],
        video_references=db.execute('SELECT count(*) FROM video_refs').fetchone()[0],
        skipped_html=db.execute('SELECT count(*) FROM issues').fetchone()[0])
    return value


def build(source,root,*,cancel=None,checkpoint=128,reserve=1_000_000_000):
    """Caller holds an OS lease. Commit cursors and keep last complete inventory."""
    from libzim.reader import Archive
    source=Path(source);root=Path(root)
    if source.is_symlink() or not source.is_file() or root.is_symlink():raise ValueError('Archive/inventory link or missing source refused')
    if not 1<=checkpoint<=10000:raise ValueError('Invalid checkpoint size')
    durable.mkdir(root)
    def check():
        if cancel and Path(cancel).exists():raise Paused()
        if shutil.disk_usage(root).free<reserve:raise OSError('Inventory storage reserve unavailable')
    check();archive=Archive(source);revision=fingerprint(source,archive)
    key=hashlib.sha256(source.name.encode()).hexdigest()[:24];published=root/(key+'.sqlite');building=root/(key+'.building')
    if published.exists():
        with connect(published,True) as db:
            value=summary(db)
            if value['revision']==revision:return {**value,'status':'reused','file':published.name}
    if building.exists():
        with connect(building,True) as db:prior=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
        if prior['revision']!=revision:
            # Keep an interrupted older edition for diagnosis; do not mix rows.
            retired=root/(key+'.interrupted-'+str(time.time_ns())+'.sqlite');durable.publish(building,retired)
    with connect(building) as db:
        building.chmod(0o600)
        db.executescript('''CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS resources(path TEXT PRIMARY KEY,category TEXT NOT NULL,mimetype TEXT NOT NULL,size INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS aliases(path TEXT PRIMARY KEY,target TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS video_refs(article TEXT NOT NULL,position INTEGER NOT NULL,title TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(article,position));
            CREATE TABLE IF NOT EXISTS issues(path TEXT PRIMARY KEY,reason TEXT NOT NULL);''')
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('source',json.dumps({'archive':source.name,'book':source.stem,'revision':revision,'entries':archive.entry_count})))
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('cursor','0'));db.commit()
        cursor=int(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0])
        for index in range(cursor,archive.entry_count):
            check()
            entry=archive._get_entry_by_id(index)
            try:
                item=entry.get_item();mime=item.mimetype.lower().split(';')[0]
                if entry.is_redirect:
                    db.execute('INSERT OR REPLACE INTO aliases VALUES(?,?)',(entry.path,item.path))
                elif mime.startswith('video/') or mime in ('text/vtt','application/x-subrip') or entry.path.lower().endswith(('.vtt','.srt')):
                    db.execute('INSERT OR REPLACE INTO resources VALUES(?,?,?,?)',(entry.path,'video' if mime.startswith('video/') else 'subtitle',mime,item.size))
                elif mime in ('text/html','application/xhtml+xml'):
                    if item.size>MAX_HTML:db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)',(entry.path,'html_too_large'));continue
                    parser=Videos();parser.feed(bytes(item.content).decode('utf-8',errors='replace'));parser.close()
                    for position,value in enumerate(parser.items):
                        for group in ('sources','tracks'):
                            for ref in value[group]:
                                ref.update(resolved=resolve(entry.path,ref['src'],parser.base))
                                if len(ref['src'])>4000:ref['src']='';parser.errors.append('reference_too_long')
                        db.execute('INSERT OR REPLACE INTO video_refs VALUES(?,?,?,?)',(entry.path,position,(value['title'] or entry.title)[:400],json.dumps(value,ensure_ascii=False)))
                    if parser.errors:db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)',(entry.path,','.join(sorted(set(parser.errors)))))
            except (RuntimeError,KeyError,ValueError):db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)',(entry.path,'entry_unreadable'))
            if (index+1)%checkpoint==0:
                db.execute("UPDATE metadata SET value=? WHERE key='cursor'",(str(index+1),));db.commit()
        db.execute("UPDATE metadata SET value=? WHERE key='cursor'",(str(archive.entry_count),));db.commit()
        check()
        if fingerprint(source,archive)!=revision:raise ArchiveChanged()
        value=summary(db)
    del archive
    durable.sync_file(building);durable.publish(building,published)
    return {**value,'status':'partial' if value['skipped_html'] else 'completed','file':published.name}


def references(path,offset=0,limit=50):
    """Bounded records with internal existence checked, without reading media."""
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid inventory page')
    with connect(path,True) as db:
        rows=db.execute('SELECT * FROM video_refs ORDER BY article,position LIMIT ? OFFSET ?',(limit,offset)).fetchall();result=[]
        for row in rows:
            value=json.loads(row['payload'])
            for group in ('sources','tracks'):
                for ref in value[group]:
                    resolved=ref['resolved']
                    if resolved['status']!='internal':continue
                    target=resolved['path'];alias=db.execute('SELECT target FROM aliases WHERE path=?',(target,)).fetchone()
                    if alias:target=alias[0]
                    resource=db.execute('SELECT * FROM resources WHERE path=?',(target,)).fetchone()
                    expected='video' if group=='sources' else 'subtitle'
                    ref['availability']='present' if resource and resource['category']==expected else 'missing_or_unsupported'
                    if resource:ref['resource']=dict(resource)
            result.append({**value,'article':row['article'],'position':row['position'],'title':row['title']})
        return {'summary':summary(db),'items':result,'total':db.execute('SELECT count(*) FROM video_refs').fetchone()[0],'offset':offset}
