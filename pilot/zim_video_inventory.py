"""Inspect archive media without downloading, decoding or changing any source.

This is the host reader side. The portal will read the resulting SQLite files
without loading libzim. Existing native text indexes are not video inventories.
"""
from contextlib import contextmanager
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import shutil
import sqlite3
import time
from urllib.parse import unquote,urlsplit

from . import durable,video_inventory

FORMAT=3
MAX_HTML=2_000_000
MAX_VIDEOS_PER_PAGE=100
MAX_TRACKS_PER_VIDEO=100
YOUTUBE_TITLES='youtube_video_titles_v1'
YOUTUBE_SUBTITLES = 'youtube_video_subtitles_v1'
EXAMINED_STATUSES={'completed','reused','partial'}


def unexamined_files(directory, report):
    """Compare revisions without opening an archive or its index."""
    revisions = {row['archive']: row.get('revision', {}) for row in report.get('results', [])
                 if row.get('status') in EXAMINED_STATUSES}
    pending = []
    for path in sorted(Path(directory).glob('*.zim')):
        try:
            info = video_inventory.regular(path)
        except (OSError, ValueError):
            continue
        saved = revisions.get(path.name, {})
        if (info.st_size, info.st_mtime_ns) != (saved.get('bytes'), saved.get('mtime_ns')):
            pending.append(path)
    return pending
LIMITED_INVENTORY_MESSAGE = 'Toutes les collections ont été parcourues. Le rapport indique les entrées non examinées.'
YOUTUBE_MEDIA=re.compile(r'videos/([A-Za-z0-9_-]{11})/video\.(?:webm|mp4)')
MEDIA_TAG = re.compile(rb'<(?:video|iframe)', re.IGNORECASE)
GENERIC_TITLE=re.compile(r'(?:vid[eé]o|videoplayback|clip|media|index|[0-9]+|[0-9a-f]{16,}|[A-Za-z0-9_-]{24,})',re.I)
TECHNICAL_TITLE=re.compile(r'://|\?[\w-]+=|\.(?:m4s|webm|mp4|ts)$',re.I)


def partial_with_all_archives(report):
    results = report.get('results')
    return (report.get('phase') == 'partial' and not report.get('unexamined')
            and isinstance(results, list) and 0 < len(results) == report.get('archives')
            and all(isinstance(row, dict) and row.get('status') in EXAMINED_STATUSES for row in results))


def readable_title(title):
    title=' '.join(title.split())
    if title and not TECHNICAL_TITLE.search(title) and not GENERIC_TITLE.fullmatch(title):
        return title[:400]
    return ''


def display_title(payload, titles):
    path=payload['path']
    if title:=titles.get(path):
        return title
    filename=path.rsplit('/',1)[-1]
    title=payload['title']
    if title not in (path,filename) and (cleaned:=readable_title(title)):
        return cleaned
    stem=posixpath.splitext(filename.split('?',1)[0])[0]
    if re.fullmatch(r'[\w. -]+',stem) and not GENERIC_TITLE.fullmatch(stem):
        cleaned=' '.join(re.sub(r'[_-]+',' ',stem).split())
        if cleaned and not GENERIC_TITLE.fullmatch(cleaned):
            return cleaned[:400]
    collection=' '.join(payload['collection'].split())[:350]
    return f'{collection} — Vidéo sans titre ({payload["inventory_id"][:8]})'


def standalone_media(path, mimetype):
    filename=path.rsplit('/',1)[-1].split('?',1)[0].lower()
    return not (filename.endswith(('.m4s','.d.ts')) or mimetype=='video/mp2t' and path=='index.ts')


def youtube_collection(archive):
    return archive.has_entry_by_path('channel.json') and archive.has_entry_by_path('home_playlists.json')


def save_youtube_metadata(db, archive, check):
    """Match offline YouTube titles and declared tracks to the exact video."""
    if not youtube_collection(archive):
        return
    if db.execute('SELECT 1 FROM metadata WHERE key=?', (YOUTUBE_SUBTITLES,)).fetchone():
        return
    candidates={row[0] for row in db.execute("SELECT path FROM resources WHERE category='video'") if YOUTUBE_MEDIA.fullmatch(row[0])}
    titles={}
    conflicts=set()
    tracks = {}
    if candidates:
        entry_by_id = getattr(archive, 'get_entry_by_id', None) or archive._get_entry_by_id
        for index in range(archive.entry_count):
            if index%128==0:
                check()
            entry=entry_by_id(index)
            if entry.is_redirect or not re.fullmatch(r'videos/[^/]+\.json',entry.path):
                continue
            try:
                item=entry.get_item()
                if item.mimetype!='application/json' or item.size>MAX_HTML:
                    continue
                data=json.loads(bytes(item.content))
                if not isinstance(data,dict):
                    continue
                path=video_inventory.text_field(data,'videoPath')
                video_id = data.get('id')
                if path not in candidates or YOUTUBE_MEDIA.fullmatch(path)[1] != video_id:
                    continue
                directory = data.get('subtitlePath')
                entries = data.get('subtitleList')
                if directory == f'videos/{video_id}' and isinstance(entries, list):
                    declared = tracks.setdefault(path, {})
                    for subtitle_info in entries[:MAX_TRACKS_PER_VIDEO]:
                        if len(declared) >= MAX_TRACKS_PER_VIDEO:
                            break
                        code = subtitle_info.get('code') if isinstance(subtitle_info, dict) else None
                        if isinstance(code, str) and re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,3}', code):
                            subtitle = f'{directory}/video.{code}.vtt'
                            if db.execute('SELECT 1 FROM subtitles WHERE path=?', (subtitle,)).fetchone():
                                declared[subtitle] = code
                title=readable_title(video_inventory.text_field(data,'title') or '')
                title.encode('utf-8')
                if not title:
                    continue
                if titles.setdefault(path,title)!=title:
                    conflicts.add(path)
            except (RuntimeError,KeyError,ValueError,RecursionError):
                continue
    db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',(YOUTUBE_TITLES,json.dumps(
        {path:title for path,title in titles.items() if path not in conflicts},ensure_ascii=False)))
    db.execute('INSERT INTO metadata VALUES(?,?)', (YOUTUBE_SUBTITLES, json.dumps(tracks)))


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
        if base_url.scheme not in ('','http','https'):return {'status':'unsupported_reference'}
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


def scan_html_references(db, entry, content):
    # Both tag names are ASCII. The parser still handles every candidate
    # page, including comments, scripts, embedded links and relative paths.
    if not MEDIA_TAG.search(content):
        return
    parser = Videos()
    parser.feed(content.decode('utf-8', errors='replace'))
    parser.close()
    for position, value in enumerate(parser.items):
        for group in ('sources', 'tracks'):
            for ref in value[group]:
                ref.update(resolved=resolve(entry.path, ref['src'], parser.base))
                if len(ref['src']) > 4000:
                    ref['src'] = ''
                    parser.errors.append('reference_too_long')
        db.execute('INSERT OR REPLACE INTO video_refs VALUES(?,?,?,?)',
                   (entry.path, position, (value['title'] or entry.title)[:400], json.dumps(value, ensure_ascii=False)))
    if parser.errors:
        db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)',
                   (entry.path, ','.join(sorted(set(parser.errors)))))


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


def cache_track(root,source,path,webvtt):
    def linked(path):
        try:return video_inventory.is_link(path)
        except FileNotFoundError:return False
    folder=Path(root)/'tracks'
    if linked(folder):raise ValueError('Track cache link refused')
    durable.mkdir(folder);data=webvtt.encode()
    key=hashlib.sha256((source['archive']+json.dumps(source['revision'],sort_keys=True)+path).encode()+data).hexdigest();cache=folder/(key+'.vtt')
    if linked(cache):raise ValueError('Track cache link refused')
    if not cache.exists() or cache.read_bytes()!=data:durable.write_bytes(cache,data,private=True)
    return key,cache


def video_items(db,root,source,check=lambda:None):
    """Export complete checked tracks, never original video bytes, for the portal."""
    revision=source['revision'];archive=source['archive'];book=source['book'];seen=set();items={}
    refs=db.execute('SELECT * FROM video_refs ORDER BY article,position')
    def resource(ref,category):
        if ref['resolved']['status']!='internal':return None
        path=ref['resolved']['path'];alias=db.execute('SELECT target FROM aliases WHERE path=?',(path,)).fetchone()
        if alias:path=alias[0]
        row=db.execute('SELECT * FROM resources WHERE path=? AND category=?',(path,category)).fetchone()
        return dict(row) if row else None
    for row in refs:
        check()
        value=json.loads(row['payload']);sources=[item for ref in value['sources'] if (item:=resource(ref,'video'))]
        if not sources:continue
        path=sources[0]['path'];seen.update(item['path'] for item in sources)
        item=items.setdefault(path,{'title':row['title'] or path.rsplit('/',1)[-1],'articles':[],'tracks':[]})
        if row['article'] not in item['articles']:item['articles'].append(row['article'])
        for ref in value['tracks']:
            found=resource(ref,'subtitle')
            if found and not any(track['source_path']==found['path'] for track in item['tracks']):
                item['tracks'].append({'source_path':found['path'],'language_declared':ref.get('language_declared') or None,
                                       'language_basis':'html_track_declared'})
    for row in db.execute("SELECT path FROM resources WHERE category='video'"):
        if row[0] not in seen:items.setdefault(row[0],{'title':row[0].rsplit('/',1)[-1],'articles':[],'tracks':[]})
    embedded = db.execute('SELECT value FROM metadata WHERE key=?', (YOUTUBE_SUBTITLES,)).fetchone()
    if embedded:
        for video, declared in json.loads(embedded[0]).items():
            if video not in items:
                continue
            tracks = items[video]['tracks']
            known = {track['source_path'] for track in tracks}
            tracks.extend({'source_path': track, 'language_declared': language,
                           'language_basis': 'youtube_archive_catalogue'}
                          for track, language in declared.items() if track not in known)
    db.execute('DELETE FROM video_items')
    for path,value in items.items():
        check()
        key=hashlib.sha256(('zim:'+archive+'/'+path).encode()).hexdigest();tracks=[]
        media=db.execute('SELECT size,mimetype FROM resources WHERE path=?',(path,)).fetchone()
        for track in value['tracks']:
            row=db.execute('SELECT * FROM subtitles WHERE path=?',(track['source_path'],)).fetchone()
            report=json.loads(row['report']) if row else {'technical_status':'invalid','errors':['piste_non_examinee'],'warnings':[]}
            report.setdefault('warnings',[])
            if report['technical_status']=='passed':
                cache_key,cache=cache_track(root,source,track['source_path'],row['webvtt'])
                report=video_inventory.inspect_subtitle(cache)
                track.update(path='zim-videos/tracks/'+cache.name,archive_cache=cache_key)
            else:track['path']='unavailable:'+track['source_path']
            tracks.append({**track,'origin':'unknown',**report})
        usable=[track for track in tracks if track['technical_status']=='passed']
        state='french_available' if any((t['language_declared'] or '').lower().startswith('fr') for t in usable) else 'source_only' if usable else 'invalid' if tracks else 'missing'
        payload={'inventory_id':key,'provider':'zim','path':path,'archive':archive,'book':book,'archive_revision':revision,'articles':value['articles'],
            'title':value['title'],'description':'','collection':source['title'],'metadata':{'path':'','status':'missing'},'same_source_paths':[],
            'media':{'present':True,'format':Path(path).suffix.lower().lstrip('.'),'mimetype':media['mimetype'],'size_bytes':media['size'],'duration_seconds_declared':None,'language_declared':None},
            'source':{'id':None,'extractor':'zim','channel':source['title'],'upload_date_declared':None},'tracks':tracks,'subtitle_status':state,
            'validation':{'human_review':'not_performed'},'next_action':'Comparer les paroles et horodatages au média original.'}
        db.execute('INSERT INTO video_items VALUES(?,?)',(key,json.dumps(payload,ensure_ascii=False)))


def summary(db):
    value=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
    value.update(entries_examined=int(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0]),
        video_resources=db.execute("SELECT count(*) FROM resources WHERE category='video'").fetchone()[0],
        subtitle_resources=db.execute("SELECT count(*) FROM resources WHERE category='subtitle'").fetchone()[0],
        usable_tracks=db.execute('SELECT count(*) FROM subtitles WHERE usable=1').fetchone()[0],
        video_references=db.execute('SELECT count(*) FROM video_refs').fetchone()[0],
        issues_count=db.execute('SELECT count(*) FROM issues').fetchone()[0],
        skipped_html=db.execute("SELECT count(*) FROM issues WHERE reason='html_too_large'").fetchone()[0])
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
            prior=json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
            if prior['revision']==revision:
                for row in db.execute('SELECT path,webvtt FROM subtitles WHERE usable=1'):
                    check();cache_track(root,prior,row['path'],row['webvtt'])
                reused={**summary(db),'status':'reused','file':published.name}
                needs_metadata = (youtube_collection(archive)
                                  and not db.execute('SELECT 1 FROM metadata WHERE key=?', (YOUTUBE_SUBTITLES,)).fetchone())
        if prior['revision']==revision:
            if needs_metadata:
                with connect(published) as db:
                    save_youtube_metadata(db, archive, check)
                    video_items(db, root, prior, check)
                    if fingerprint(source,archive)!=revision:raise ArchiveChanged()
            return reused
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
            CREATE TABLE IF NOT EXISTS subtitles(path TEXT PRIMARY KEY,usable INTEGER NOT NULL,report TEXT NOT NULL,webvtt TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS subtitle_cues(path TEXT NOT NULL,position INTEGER NOT NULL,start_ms INTEGER NOT NULL,end_ms INTEGER NOT NULL,text TEXT NOT NULL,PRIMARY KEY(path,position));
            CREATE TABLE IF NOT EXISTS video_items(id TEXT PRIMARY KEY,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS video_refs(article TEXT NOT NULL,position INTEGER NOT NULL,title TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(article,position));
            CREATE TABLE IF NOT EXISTS issues(path TEXT PRIMARY KEY,reason TEXT NOT NULL);''')
        try:title=archive.get_metadata('Title').decode('utf-8',errors='replace')[:400]
        except (KeyError,RuntimeError):title=source.stem
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('source',json.dumps({'archive':source.name,'book':source.stem,'title':title,'revision':revision,'entries':archive.entry_count})))
        db.execute('INSERT OR IGNORE INTO metadata VALUES(?,?)',('cursor','0'));db.commit()
        cursor=int(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0])
        entry_by_id=getattr(archive,'get_entry_by_id',None) or archive._get_entry_by_id  # libzim 4.x / 3.13.1
        for index in range(cursor,archive.entry_count):
            check()
            entry=entry_by_id(index)
            try:
                item=entry.get_item();mime=item.mimetype.lower().split(';')[0]
                if entry.is_redirect:
                    db.execute('INSERT OR REPLACE INTO aliases VALUES(?,?)',(entry.path,item.path))
                elif mime.startswith('video/') or mime in ('text/vtt','application/x-subrip') or entry.path.lower().endswith(('.vtt','.srt')):
                    db.execute('INSERT OR REPLACE INTO resources VALUES(?,?,?,?)',(entry.path,'video' if mime.startswith('video/') else 'subtitle',mime,item.size))
                    if not mime.startswith('video/'):
                        if item.size>video_inventory.MAX_SIDECAR_BYTES:
                            report={'technical_status':'invalid','errors':['fichier_annexe_trop_gros'],'cue_count':0};cues=[]
                        else:
                            try:
                                content=bytes(item.content).decode('utf-8-sig')
                                report=video_inventory.inspect_subtitle_text(content,'vtt' if mime=='text/vtt' or entry.path.lower().endswith('.vtt') else 'srt',include_cues=True)
                                cues=report.pop('cues')
                            except UnicodeError:report={'technical_status':'invalid','errors':['encodage_non_utf8'],'cue_count':0};cues=[]
                        usable=report['technical_status']=='passed'
                        def stamp(ms):return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'
                        webvtt='WEBVTT\n\n'+'\n\n'.join(stamp(c['start_ms'])+' --> '+stamp(c['end_ms'])+'\n'+html.escape(c['text'],quote=False) for c in cues)+'\n' if usable else ''
                        db.execute('INSERT OR REPLACE INTO subtitles VALUES(?,?,?,?)',(entry.path,int(usable),json.dumps(report,ensure_ascii=False),webvtt))
                        db.execute('DELETE FROM subtitle_cues WHERE path=?',(entry.path,))
                        db.executemany('INSERT INTO subtitle_cues VALUES(?,?,?,?,?)',[(entry.path,n,c['start_ms'],c['end_ms'],c['text']) for n,c in enumerate(cues)])
                elif mime in ('text/html','application/xhtml+xml'):
                    if item.size > MAX_HTML:
                        db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)', (entry.path, 'html_too_large'))
                    else:
                        scan_html_references(db, entry, bytes(item.content))
            except (RuntimeError,KeyError,ValueError):db.execute('INSERT OR REPLACE INTO issues VALUES(?,?)',(entry.path,'entry_unreadable'))
            if (index+1)%checkpoint==0:
                db.execute("UPDATE metadata SET value=? WHERE key='cursor'",(str(index+1),));db.commit()
        db.execute("UPDATE metadata SET value=? WHERE key='cursor'",(str(archive.entry_count),));db.commit()
        check()
        if fingerprint(source,archive)!=revision:raise ArchiveChanged()
        save_youtube_metadata(db, archive, check)
        video_items(db,root,json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0]),check)
        db.commit()
        check()
        if fingerprint(source,archive)!=revision:raise ArchiveChanged()
        value=summary(db)
    del archive
    durable.sync_file(building);durable.publish(building,published)
    return {**value,'status':'partial' if value['issues_count'] else 'completed','file':published.name}


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
                    if resource and group=='tracks':
                        check=db.execute('SELECT report FROM subtitles WHERE path=?',(target,)).fetchone()
                        ref['checks']=json.loads(check[0]) if check else {'technical_status':'invalid','errors':['piste_non_examinee']}
            result.append({**value,'article':row['article'],'position':row['position'],'title':row['title']})
        return {'summary':summary(db),'items':result,'total':db.execute('SELECT count(*) FROM video_refs').fetchone()[0],'offset':offset}
