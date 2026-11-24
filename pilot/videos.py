"""Local media and caption index. No network, decoder, model or original writes."""
import asyncio
from contextlib import contextmanager
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time

from fastapi import HTTPException
from . import collection_sort,durable,network,retrieval,store,work_queue
from . import video_inventory as inventory

ROOT=Path(os.environ.get('VIDEO_DIR','/videos'))
ACTIVE=None
PARTITION_TASK=None
STOP=threading.Event()
STOP_REASON='user'
LOCK=threading.Lock()
NOTICE='Sous-titres locaux : langue, sens et synchronisation non vérifiés. Le texte ne prouve pas que les gestes montrés ont été compris.'


SCHEMA='''CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY,path TEXT NOT NULL,revision TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS video_text USING fts5(id UNINDEXED,title,language UNINDEXED,track UNINDEXED,start_ms UNINDEXED,end_ms UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');'''
# Rebuilt layout: identifier and title once per video, each cue once; the
# search tables index a view instead of copying it. 7.70 GB became 3.42 GB with
# identical answers to 1,395 queries on the Bazzite lab (24 November 2026).
# The main table is named video_search: earlier versions, after a rollback,
# create their own empty video_text and rebuild instead of writing into it.
BUILD_SCHEMA='''CREATE TABLE media(id TEXT PRIMARY KEY,path TEXT NOT NULL,revision TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE video_doc(doc INTEGER PRIMARY KEY,id TEXT NOT NULL UNIQUE,title TEXT NOT NULL,first_cue INTEGER,last_cue INTEGER);
        CREATE TABLE video_cue(cue INTEGER PRIMARY KEY,doc INTEGER NOT NULL,language TEXT NOT NULL,track TEXT NOT NULL,start_ms INTEGER NOT NULL,end_ms INTEGER NOT NULL,text TEXT NOT NULL);
        CREATE VIEW video_rows AS SELECT c.cue AS cue,d.id AS id,d.title AS title,c.language AS language,c.track AS track,
            c.start_ms AS start_ms,c.end_ms AS end_ms,c.text AS text FROM video_cue c JOIN video_doc d ON d.doc=c.doc;
        CREATE VIRTUAL TABLE video_search USING fts5(id UNINDEXED,title,language UNINDEXED,track UNINDEXED,start_ms UNINDEXED,end_ms UNINDEXED,text,content='video_rows',content_rowid='cue',tokenize='unicode61 remove_diacritics 2');
        CREATE TABLE video_search_partitions(scope TEXT PRIMARY KEY);'''
# Bound the write-ahead log once checkpointed: without it a full inventory left
# a multi-gigabyte videos.db-wal on disk (Bazzite lab, 24 November 2026).
WAL_LIMIT=64*1024*1024


class Access:
    """Connections of this process to videos.db; a rebuilt index replaces the
    file only when none is open. Nested use in one thread never waits."""
    def __init__(self):
        self.condition=threading.Condition();self.readers=0;self.replacing=False;self.local=threading.local()

    @contextmanager
    def reading(self):
        depth=getattr(self.local,'depth',0)
        if not depth:
            with self.condition:
                self.condition.wait_for(lambda:not self.replacing)
                self.readers+=1
        self.local.depth=depth+1
        try:yield
        finally:
            self.local.depth=depth
            if not depth:
                with self.condition:self.readers-=1;self.condition.notify_all()

    @contextmanager
    def replacing_file(self,timeout=60):
        with self.condition:
            self.replacing=True
            if not self.condition.wait_for(lambda:self.readers==0,timeout):
                self.replacing=False;self.condition.notify_all()
                raise TimeoutError('video_index_busy')
        try:yield
        finally:
            with self.condition:self.replacing=False;self.condition.notify_all()


ACCESS=Access()


def database():return store.ROOT/'videos.db'


def building():return store.ROOT/'videos.db.next'


@contextmanager
def connect():
    durable.mkdir(store.ROOT)
    with ACCESS.reading():
        path=database();db=sqlite3.connect(path,timeout=10);db.row_factory=sqlite3.Row
        path.chmod(0o600)
        db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL');db.execute(f'PRAGMA journal_size_limit={WAL_LIMIT}')
        if not db.execute('SELECT 1 FROM sqlite_master LIMIT 1').fetchone():db.executescript(SCHEMA)
        try:
            with db:yield db
        finally:db.close()


def main_table(db):
    """Search table of the rebuilt layout, or of a file published before 0.114.0."""
    return 'video_search' if db.execute("SELECT 1 FROM sqlite_master WHERE name='video_search'").fetchone() else 'video_text'


@contextmanager
def build_connection():
    """A private file rebuilt from the sources: no journal is needed, an
    interrupted build is simply discarded and the published index stays."""
    path=building()
    for leftover in (path,Path(str(path)+'-journal')):
        leftover.unlink(missing_ok=True)
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row
    path.chmod(0o600)
    db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
    db.executescript(BUILD_SCHEMA)
    try:
        with db:yield db
    except BaseException:
        db.close();path.unlink(missing_ok=True);raise
    db.close()


def publish_built():
    """Replace videos.db by the completed build once no connection is open."""
    path=building();target=database()
    try:
        durable.sync_file(path)
        replace_index(path,target)
    except BaseException:
        path.unlink(missing_ok=True);raise


def replace_index(path,target):
    with ACCESS.replacing_file():
        if target.is_file():
            # A clean checkpoint first: an interruption below leaves either the
            # complete old index or the complete new one, never a foreign log.
            db=sqlite3.connect(target,timeout=30)
            try:
                db.execute('PRAGMA journal_mode=WAL')
                busy,_,_=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
                if busy:raise TimeoutError('video_index_busy')
            finally:db.close()
        for suffix in ('-wal','-shm'):
            Path(str(target)+suffix).unlink(missing_ok=True)
        os.replace(path,target)
        durable.sync_directory(store.ROOT)


def safe_file(relative):
    if not isinstance(relative,str) or not relative or '\\' in relative or any(p in ('','.','..') for p in relative.split('/')):
        raise HTTPException(400,'Chemin vidéo invalide.')
    path=ROOT/relative
    try:
        if any(inventory.is_link(p) for p in [ROOT,*[ROOT.joinpath(*Path(relative).parts[:n]) for n in range(1,len(Path(relative).parts)+1)]]):raise ValueError()
        if not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():raise ValueError()
        return path
    except (OSError,ValueError):raise HTTPException(404,'Ce fichier vidéo local n’est plus disponible.') from None


def identity(value):
    match=re.fullmatch(r'video:([a-f0-9]{64})(?:#t=(\d{1,10})(?:&track=\d{1,3})?)?',value)
    if not match:raise HTTPException(400,'Référence vidéo invalide.')
    return match[1],int(match[2] or 0)


def stat_revision(payload):
    values=[]
    if payload.get('provider')=='zim':
        from . import archive_videos
        revision=archive_videos.original_revision(payload)
        if not revision:return None
        values.append(['archive',revision]);entries=[(track['path'],track) for track in payload['tracks'] if track['technical_status']=='passed']
    else:entries=[(payload['path'],None),(payload['metadata']['path'],None),*[(track['path'],track) for track in payload['tracks']]]
    for relative,track in entries:
        try:
            path=track_file(track) if track is not None else safe_file(relative);info=path.stat();values.append([relative,info.st_size,info.st_mtime_ns])
        except HTTPException:
            if relative==payload['metadata']['path'] and payload['metadata']['status']=='missing':values.append([relative,None]);continue
            return None
    return hashlib.sha256(json.dumps(values,ensure_ascii=False).encode()).hexdigest()


def original_revision(payload):
    if payload.get('provider')=='zim':
        from . import archive_videos
        return archive_videos.original_revision(payload)
    return stat_revision({**payload,'tracks':[track for track in payload['tracks'] if not track.get('prepared_job') and not track.get('transcription_job') and not track.get('acquired_job')]})


def track_file(track):
    if track.get('archive_cache'):
        from . import archive_videos
        return archive_videos.track_file(track)
    if track.get('acquired_job'):
        from . import caption_acquisition
        path=caption_acquisition.track_file(track['acquired_job'])
        if not path.is_file():raise HTTPException(404,'Cette piste récupérée n’est plus disponible.')
        return path
    if track.get('transcription_job'):
        from . import transcriptions
        path=transcriptions.track_file(track['transcription_job'])
        if not path.is_file():raise HTTPException(404,'Cette transcription n’est plus disponible.')
        return path
    if track.get('prepared_job'):
        from . import captions
        path=captions.track_file(track['prepared_job'])
        if not path.is_file():raise HTTPException(404,'Cette piste préparée n’est plus disponible.')
        return path
    return safe_file(track['path'])


def row(identifier):
    key,position=identity(identifier)
    with connect() as db:value=db.execute('SELECT * FROM media WHERE id=?',(key,)).fetchone()
    if not value:raise HTTPException(404,'Vidéo introuvable. Actualisez l’index des vidéos depuis Collections.')
    payload=json.loads(value['payload'])
    if stat_revision(payload)!=value['revision']:raise HTTPException(409,'La vidéo ou ses sous-titres ont changé. Actualisez les vidéos avant de rouvrir ce résultat.')
    return dict(value),payload,position


def revision(identifier):
    try:return row(identifier)[0]['revision']
    except HTTPException:return None


def public(payload,revision):
    key=payload['inventory_id'];media=payload['media'];source=payload['source']
    declared=source.get('upload_date_declared') or ''
    date=declared[:4]+'-'+declared[4:6]+'-'+declared[6:] if re.fullmatch(r'\d{8}',declared) else ''
    folder='' if payload['collection'] in ('.','') else payload['collection']
    audio_language=media.get('language_declared') or next(
        (track['language_declared'] for track in payload['tracks']
         if track.get('origin')=='local_transcription' and track.get('language_declared')), '')
    return {'id':'video:'+key,'kind':'video','title':payload['title'][:400],'collection':source.get('channel') or folder,
        'audio_transcription_supported':True,
        'archive_video':payload.get('provider')=='zim','archive_name':payload.get('archive'),'archive_article':('zim:'+payload['book']+'/'+payload['articles'][0]) if payload.get('provider')=='zim' and payload.get('articles') else None,
        'language':media.get('language_declared') or '', 'audio_language':audio_language, 'duration_seconds':media.get('duration_seconds_declared'),
        'subtitle_status':payload['subtitle_status'],'video_revision':revision,'document_date':date,'edition':'',
        'collected_at':'','archive_date':'','provenance':source.get('channel') or 'Fichier vidéo local','licence':'Droits d’usage à vérifier.',
        'url':'/api/videos/media?id='+key,'images':[],'tracks':[
            {'id':index,'preference_key':hashlib.sha256(track['path'].encode()).hexdigest(),
             'language':track['language_declared'] or '', 'origin':track['origin'],'status':track['technical_status'],
             'warnings':track['warnings'],'errors':track['errors'][:10],'translation_notice':track.get('translation_notice',''),
             'transcription_notice':track.get('transcription_notice',''),
             'acquisition_notice':track.get('acquisition_notice',''),'timing_adjustments':track.get('timing_adjustments',0),
             'source_language':track.get('source_language',''),'url':'/api/videos/track?id='+key+'&track='+str(index)}
            for index,track in enumerate(payload['tracks'])],
        'video_notice':NOTICE,'audio_verified':False,'human_review':'not_performed'}


def search_domains(payload, sorting):
    if sorting.state(collection_sort.video(payload)) == 'main' and 'search_domains' in payload:
        return payload['search_domains']
    return retrieval.domains({'title': payload['title'], '_text': payload.get('description') or ''})


def source(identifier):
    stored,payload,position=row(identifier);result=public(payload,stored['revision']);result['id']=identifier
    result['_indexed_domains'] = search_domains(payload, collection_sort.load(network.CATALOG))
    # Favor a declared French track unless a search result selects a specific track.
    candidates=[(i,t) for i,t in enumerate(payload['tracks']) if t['technical_status']=='passed']
    candidates.sort(key=lambda pair:(not (pair[1]['language_declared'] or '').startswith('fr'),pair[0]))
    requested=re.search(r'&track=(\d+)$',identifier)
    if requested:candidates=[pair for pair in candidates if pair[0]==int(requested[1])]
    track=candidates[0][1] if candidates else None
    cues=[]
    if track:
        cues=[cue for cue in track_cues(payload,track) if cue['end_ms']>position][:80]
        if track.get('translation_notice'):result['video_notice']=track['translation_notice']+' '+NOTICE
    text='\n'.join(f'[{int(c["start_ms"])//60000:02d}:{(int(c["start_ms"])//1000)%60:02d}] {c["text"]}' for c in cues)
    result.update(text=text[:100000],position_ms=position,text_truncated=bool(len(text)>100000 or cues and len(cues)>=80),preview=True,
                  transcription_available=bool(cues),language=(track['language_declared'] or '') if cues else result['language'])
    return result


def confirm_indexed_tracks(published):
    if not published:
        return
    from . import caption_acquisition, captions, transcriptions
    modules = {'acquired_job': caption_acquisition, 'prepared_job': captions,
               'transcription_job': transcriptions}
    for origin, identifiers in published.items():
        try:
            with modules[origin].connect() as db:
                db.executemany("UPDATE jobs SET index_status='requested' WHERE id=? "
                               "AND status='completed' AND index_status='pending'",
                               ((identifier,) for identifier in identifiers))
        except (OSError, sqlite3.Error):
            # The searchable index has already been committed.
            continue


def signature(archives=True):
    """Cheap fingerprint of finished local files: names, sizes and dates only.

    Nothing is opened or decoded; partial downloads are ignored so that a
    download in progress does not trigger repeated inventories. Without
    `archives`, only the local files and the collection sort count."""
    local = ROOT.is_dir() and not inventory.is_link(ROOT)
    digest=hashlib.sha256(b'archive-display-titles-and-origin-v3-compact-index-0.114')
    digest.update(json.dumps(collection_sort.load(network.CATALOG).as_json()).encode())
    count=0
    for directory,folders,files in os.walk(ROOT,followlinks=False) if local else ():
        folders.sort();base=Path(directory)
        for name in sorted(files):
            if inventory.INCOMPLETE.search(name):continue
            suffix=Path(name).suffix.lower()
            if suffix not in inventory.VIDEO_EXTENSIONS and suffix not in inventory.SUBTITLE_EXTENSIONS and not name.endswith('.info.json'):continue
            try:info=(base/name).lstat()
            except OSError:continue
            digest.update(json.dumps([str((base/name).relative_to(ROOT)),info.st_size,info.st_mtime_ns],ensure_ascii=False).encode()+b'\n');count+=1
    archived = False
    try:
        if not archives:raise LookupError()
        from . import archive_videos
        published = [[path.name, info.st_size, info.st_mtime_ns]
                     for path, info in archive_videos.published_indexes()]
        progress=archive_videos.progress()
        archived = bool(published) or progress.get('phase') in ('completed','partial')
        if archived:
            digest.update(json.dumps(['archives', published, progress.get('job_id'), progress.get('finished')]).encode())
    except Exception:pass
    return digest.hexdigest()+':'+str(count) if local or archived else None


CHECKED=0.0
CHECK_INTERVAL=60
# Each archive published by a running ZIM video inventory changes the
# signature; a full rebuild took 25 minutes of the pilot's CPU for 17,375 videos
# and restarted in a loop on the Bazzite lab (24 November 2026). While such an
# inventory runs, its newly published archives wait until this many times the
# last rebuild duration has passed: at most a fifth of the time spent
# rebuilding. Its end still triggers a rebuild
# (archive_videos.follow and the finished date).
ARCHIVE_REFRESH_FACTOR=4
# Rebuilds shorter than this are never deferred.
ARCHIVE_DEFER_AFTER=60


def archive_inventory_running():
    try:
        from . import archive_videos
        return archive_videos.progress().get('phase')=='running'
    except Exception:return False


def stale():
    """True when the published index does not describe the current files."""
    current=status()
    if current['phase']=='running':return False
    if current['phase'] in ('not_started','interrupted'):return True
    # Backups skip the rebuildable index: a restored report alone is not enough.
    if current['phase']=='completed' and current.get('videos') and not indexed_count():return True
    if current['phase']=='paused' and current.get('stopped_by')!='user':return True
    # A completed, failed or voluntarily stopped inventory is redone only
    # when the files changed since it started.
    if current.get('signature')==signature():return False
    duration=max(0,current.get('finished',0)-current.get('started',0))
    if (current['phase']=='completed' and 'local_signature' in current and duration>=ARCHIVE_DEFER_AFTER
            and time.time()-current['finished']<ARCHIVE_REFRESH_FACTOR*duration
            and archive_inventory_running() and current['local_signature']==signature(archives=False)):
        return False
    return True


async def ensure_fresh(force=False):
    """Start a read-only inventory when the video folder changed.

    Called at startup and before video searches, at most once a minute. The
    previous index stays searchable during the refresh."""
    global CHECKED
    if work_queue.QUEUE.paused:return 'paused'
    if running() is not None:return 'refreshing'
    if not force and time.monotonic()-CHECKED<CHECK_INTERVAL:return 'checked'
    CHECKED=time.monotonic()
    try:
        if not await asyncio.to_thread(stale):
            await ensure_partitions()
            return 'fresh'
        await start();return 'refreshing'
    except HTTPException:return 'refreshing'
    except Exception:return 'unavailable'


def indexed_count():
    try:
        with connect() as db:return db.execute('SELECT count(*) FROM media').fetchone()[0]
    except sqlite3.Error:return 0


def partition_name(key):
    return 'vtext_'+hashlib.sha256(key.encode()).hexdigest()


def partition_tables(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='video_search_partitions'").fetchone():
        return None
    return {row[0]:partition_name(row[0]) for row in db.execute('SELECT scope FROM video_search_partitions')}


def rebuild_partitions():
    if not (store.ROOT/'videos.db').is_file():
        return
    with LOCK, connect() as db:
        if partition_tables(db) is not None:
            return
        db.execute('BEGIN IMMEDIATE')
        build_partitions(db)


def partitions_ready():
    path=database()
    with ACCESS.reading():
        if not path.is_file():return True
        db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)
        try:return partition_tables(db) is not None
        finally:db.close()


async def ensure_partitions():
    global PARTITION_TASK
    if partitions_running() or STOP.is_set() or work_queue.QUEUE.paused:
        return
    try:
        if await asyncio.to_thread(partitions_ready):return
    except (OSError,sqlite3.Error):
        return
    if partitions_running() or STOP.is_set() or work_queue.QUEUE.paused:
        return
    async def run():
        try:await asyncio.to_thread(rebuild_partitions)
        except (OSError,sqlite3.Error,ValueError):pass
    PARTITION_TASK=asyncio.create_task(run())


def build_partitions(db):
    if STOP.is_set():raise InterruptedError()
    previous=partition_tables(db)
    if previous is not None:
        for table in previous.values():
            db.execute(f'DROP TABLE IF EXISTS {table}')
        db.execute('DELETE FROM video_search_partitions')
    else:
        db.execute('CREATE TABLE video_search_partitions(scope TEXT PRIMARY KEY)')
    scopes={key:collection_sort.video(json.loads(payload)) for key,payload in db.execute('SELECT id,payload FROM media')}
    tables={key:partition_name(key) for key in set(scopes.values())}
    # Partitions index the rows of video_text without copying them: the text
    # stored once halves the subtitle content (2.2 GB on the Bazzite lab).
    for key,table in tables.items():
        db.execute(f"""CREATE VIRTUAL TABLE {table} USING fts5(id UNINDEXED,title,language UNINDEXED,
            track UNINDEXED,start_ms UNINDEXED,end_ms UNINDEXED,text,content='video_text',tokenize='unicode61 remove_diacritics 2')""")
        db.execute('INSERT INTO video_search_partitions VALUES(?)',(key,))
    for number,row in enumerate(db.execute('SELECT rowid,* FROM video_text')):
        if number%512==0 and STOP.is_set():raise InterruptedError()
        scope=scopes.get(row['id'])
        if scope is not None:
            db.execute(f'INSERT INTO {tables[scope]}(rowid,id,title,language,track,start_ms,end_ms,text) VALUES(?,?,?,?,?,?,?,?)',tuple(row))


def build_search_tables(db):
    """Index the cues of a rebuilt file: the main table, then one partition per
    collection scope, each reading the cues of its videos by rowid range."""
    if STOP.is_set():raise InterruptedError()
    db.execute("INSERT INTO video_search(video_search) VALUES('rebuild')")
    scopes={key:collection_sort.video(json.loads(payload)) for key,payload in db.execute('SELECT id,payload FROM media')}
    tables={key:partition_name(key) for key in set(scopes.values())}
    for key,table in tables.items():
        db.execute(f"""CREATE VIRTUAL TABLE {table} USING fts5(id UNINDEXED,title,language UNINDEXED,
            track UNINDEXED,start_ms UNINDEXED,end_ms UNINDEXED,text,content='video_rows',content_rowid='cue',tokenize='unicode61 remove_diacritics 2')""")
        db.execute('INSERT INTO video_search_partitions VALUES(?)',(key,))
    for key,first,last in db.execute('SELECT id,first_cue,last_cue FROM video_doc').fetchall():
        if STOP.is_set():raise InterruptedError()
        scope=scopes.get(key)
        if scope is not None and first is not None:
            db.execute(f'INSERT INTO {tables[scope]}(rowid,id,title,language,track,start_ms,end_ms,text) '
                       'SELECT cue,id,title,language,track,start_ms,end_ms,text FROM video_rows WHERE cue BETWEEN ? AND ?',(first,last))


def search(plan,language='',limit=40,sorting=None,domain='all'):
    if not ROOT.is_dir() and not (store.ROOT/'videos.db').is_file():return [],{'status':'not_available'}
    phase=status()['phase']
    if phase=='not_started' or (phase=='running' and not indexed_count()):return [],{'status':'not_indexed','indexed_videos':0}
    sorting=sorting if sorting is not None else collection_sort.Sort()
    with connect() as db:
        db.execute('BEGIN')
        def collection_matches(serialized):
            payload=json.loads(serialized)
            label=(payload.get('source') or {}).get('channel') or payload.get('collection') or ''
            return not plan.collection or plan.collection in retrieval.normal(label).replace(' ','')
        def in_scope(serialized):
            payload=json.loads(serialized)
            return sorting.permits(collection_sort.video(payload),domain) and collection_matches(serialized)
        partitions=partition_tables(db)
        restricted=bool(sorting.excluded or domain=='other' or (domain!='all' and sorting.other))
        if partitions is not None and (restricted or plan.collection):
            if plan.collection:
                matches={collection_sort.video(json.loads(row[0])) for row in db.execute('SELECT payload FROM media')
                         if collection_matches(row[0])}
            else:
                matches=set(partitions)
            tables=[table for key,table in partitions.items() if key in matches and sorting.permits(key,domain)]
            restriction=''
            if plan.collection:
                db.create_function('in_video_scope',1,in_scope,deterministic=True)
                restriction='AND id IN (SELECT id FROM media WHERE in_video_scope(payload))'
        else:
            tables=[main_table(db)]
            restriction=''
            if restricted or plan.collection:
                db.create_function('in_video_scope',1,in_scope,deterministic=True)
                restriction='AND id IN (SELECT id FROM media WHERE in_video_scope(payload))'
        rows=[]
        for table in tables:
            if plan.words:
                query=f"""SELECT id,title,language,track,start_ms,end_ms,snippet({table},6,'','', '…',45) AS excerpt,
                          text AS _text,bm25({table}) AS rank FROM {table} WHERE {table} MATCH ? {restriction}
                          AND (?='' OR language=? OR substr(language,1,2)=?) ORDER BY rank LIMIT ?"""
                args=(plan.fts(relaxed=True),language,language,language[:2],limit)
            else:
                query=f"""SELECT id,title,language,track,start_ms,end_ms,'' AS excerpt,text AS _text
                          FROM {table} WHERE track='metadata' {restriction}
                          AND (?='' OR language=? OR substr(language,1,2)=?) ORDER BY title COLLATE NOCASE,id LIMIT ?"""
                args=(language,language,language[:2],limit)
            rows.extend(db.execute(query,args))
        if plan.words:rows.sort(key=lambda row:row['rank'])
        else:rows.sort(key=lambda row:(row['title'].lower(),row['id']))
        rows=rows[:limit]
        result=[];stale_rows=0
        for candidate in rows:
            try:stored,payload,_=row('video:'+candidate['id'])
            except HTTPException:stale_rows+=1;continue
            data=public(payload,stored['revision']);start=int(candidate['start_ms'])
            data.update(id='video:'+candidate['id']+('#t='+str(start)+'&track='+candidate['track'] if candidate['track']!='metadata' else ''),
                        language=candidate['language'],excerpt=candidate['excerpt'],_text=candidate['_text'],
                        match='subtitle' if candidate['track']!='metadata' else 'title',position_ms=start,
                        transcription_origin=payload['tracks'][int(candidate['track'])]['origin'] if candidate['track']!='metadata' else 'metadata_only')
            data['_indexed_domains'] = search_domains(payload, sorting)
            result.append(data)
    from . import archive_videos
    archives=archive_videos.coverage()
    total=indexed_count()
    state='refreshing' if phase=='running' else 'partial' if stale_rows or phase!='completed' or archives['status'] in ('not_indexed','partial') else 'complete'
    return result,{'status':state,'stale_results':stale_rows,'results':len(result),'indexes_queried':len(tables),'indexed_videos':total,'partitioned':partitions is not None,'scope':'indexed_local_and_archive_video_titles_and_tracks','archives':archives}


def status():
    try:
        value=json.loads((store.ROOT/'videos-report.json').read_text())
        if value.get('phase')=='running' and (ACTIVE is None or ACTIVE.done()):value['phase']='interrupted'
        return value
    except (OSError,ValueError):return {'schema':1,'phase':'not_started','videos':0,'tracks':0,'errors':[]}


VIDEO_COLLECTIONS = """
WITH named_videos AS (
    SELECT id,revision,payload,
        substr(COALESCE(NULLIF(trim(json_extract(payload,'$.source.channel')),''),
                        NULLIF(NULLIF(json_extract(payload,'$.collection'),'.'),'')),1,400) AS label,
        json_extract(payload,'$.provider') AS provider
    FROM media
), grouped_videos AS (
    SELECT *, CASE WHEN label IS NULL THEN 'video:'||id
        WHEN provider='zim' THEN 'zim:'||lower(label)
        ELSE 'local:'||lower(label) END AS group_key
    FROM named_videos
)
"""


def listing_card(record):
    payload=json.loads(record['payload'])
    item=public(payload,record['revision'])
    item['available']=stat_revision(payload)==record['revision']
    return item


def listing(offset=0,limit=30,query='',grouped=False,group='',origin='all'):
    words=retrieval.normal(query).split()[:10]
    filters=[]
    parameters=[]
    if words:
        title_match="id IN (SELECT id FROM {table} WHERE {table} MATCH ? AND track='metadata')"
        filters.append(f'({title_match} OR collection_matches(label))' if grouped or group else title_match)
        parameters.append(' AND '.join('"'+word+'"' for word in words))
    if group:
        filters.append('group_key=?')
        parameters.append(group)
    if origin=='local':
        # Files placed in library/video/ (by hand or by the YouTube list tool),
        # as opposed to videos read inside Kiwix ZIM archives.
        filters.append("COALESCE(json_extract(payload,'$.provider'),'local')<>'zim'")
    restriction=' WHERE '+' AND '.join(filters) if filters else ''
    prefix=VIDEO_COLLECTIONS if grouped or group else ''
    table='grouped_videos' if prefix else 'media'
    report=status()
    if prefix:
        report={key:report[key] for key in ('phase','finished','videos','error') if key in report}
    with connect() as db:
        db.execute('BEGIN')
        restriction=restriction.replace('{table}',main_table(db))
        if prefix and words:
            def collection_matches(label):
                text=retrieval.normal(label or '')
                return all(word in text for word in words)
            db.create_function('collection_matches',1,collection_matches,deterministic=True)
        if grouped:
            groups=db.execute(prefix+f"""
                SELECT group_key,MIN(label) AS label,count(*) AS count,MIN(id) AS first_id
                FROM {table}{restriction} GROUP BY group_key
                ORDER BY label IS NULL,label COLLATE NOCASE,group_key
            """,parameters).fetchall()
            page=[]
            for row in groups[offset:offset+limit]:
                value={'id':row['group_key'],'name':row['label'],'count':row['count']}
                if row['count']==1:
                    value['video']=listing_card(db.execute('SELECT * FROM media WHERE id=?',(row['first_id'],)).fetchone())
                page.append(value)
            return {'status':report,'total':sum(row['count'] for row in groups),'group_total':len(groups),'groups':page}
        total=db.execute(prefix+'SELECT count(*) FROM '+table+restriction,parameters).fetchone()[0]
        order="json_extract(payload,'$.title') COLLATE NOCASE,id" if group else 'id'
        records=db.execute(prefix+'SELECT * FROM '+table+restriction+' ORDER BY '+order+' LIMIT ? OFFSET ?',(*parameters,limit,offset)).fetchall()
    return {'status':report,'total':total,'offset':offset,'videos':[listing_card(record) for record in records]}


def scan():
    with LOCK:
        report={'schema':1,'phase':'running','started':time.time(),'videos':0,'tracks':0,'errors':[],
                'stage':'Lecture des vidéos et des pistes'}
        try:report['signature']=signature();report['local_signature']=signature(archives=False)
        except Exception:report['signature']=None
        last_saved=time.monotonic()
        def save():durable.write_bytes(store.ROOT/'videos-report.json',json.dumps(report,ensure_ascii=False).encode(),private=True)
        save()
        try:
            from . import archive_videos
            archive_report=archive_videos.progress()
            archived=list(archive_videos.items(report['errors']))
            if not ROOT.is_dir() or inventory.is_link(ROOT):
                if not archived:raise ValueError('video_directory_unavailable')
                found={'videos':[],'skipped':[],'errors':[],'unexamined':[],'limitations':[]}
            else:found=inventory.inventory(ROOT,cancelled=STOP.is_set)
            found['videos'].extend(archived)
            report.pop('stage')
            report['archive_inventory_job']=archive_report.get('job_id') if archive_report['phase'] in ('completed','partial') else None
            report['archive_inventory_finished']=archive_report.get('finished')
            report['archive_inventory_phase']=archive_report['phase']
            found['limitations']=[text.replace(' et vidéos dans les ZIM','') for text in found['limitations']]
            found['limitations'].append('Collections : médias et pistes explicites des pages HTML examinées ; lecteurs JavaScript, sens et synchronisation non certifiés.')
            sorting = collection_sort.load(network.CATALOG)
            published = {}
            # Build a separate file: searches keep the published index, the
            # log stays small and the replaced file leaves no free pages.
            with build_connection() as db:
                for item in found['videos']:
                    if STOP.is_set():raise InterruptedError()
                    try:
                        from . import transcriptions
                        recognized=transcriptions.prepared_tracks(item);item['tracks'].extend(recognized)
                        if recognized:
                            item['subtitle_status']='source_transcribed'
                            item['next_action']='Lire la transcription automatique et vérifier les mots et horodatages avec l’original.'
                    except Exception:report['errors'].append({'id':item['inventory_id'],'reason':'transcriptions_unavailable'})
                    try:
                        from . import caption_acquisition
                        acquired=caption_acquisition.prepared_tracks(item);item['tracks'].extend(acquired)
                        if acquired and any(track['language_declared'].lower().startswith('fr') for track in acquired):item['subtitle_status']='french_available'
                        elif acquired and not item['subtitle_status'].startswith('french'):item['subtitle_status']='source_only'
                    except Exception:report['errors'].append({'id':item['inventory_id'],'reason':'acquired_captions_unavailable'})
                    try:
                        from . import captions
                        prepared=captions.prepared_tracks(item);item['tracks'].extend(prepared)
                        if prepared:
                            item['subtitle_status']='french_prepared'
                            item['next_action']='Lire la piste française préparée et vérifier langue, sens et synchronisation avec l’original.'
                    except Exception:report['errors'].append({'id':item['inventory_id'],'reason':'prepared_captions_unavailable'})
                    key=item['inventory_id'];version=stat_revision(item)
                    if not version:report['errors'].append({'id':key,'reason':'source_changed'});continue
                    main = sorting.state(collection_sort.video(item)) == 'main'
                    description = (item['description'] or '')[:100000]
                    subject = {'title': item['title'], '_text': description}
                    domains = set(retrieval.domains(subject)) if main else set()
                    language=item['media']['language_declared'] or ''
                    doc=db.execute('INSERT INTO video_doc(id,title) VALUES(?,?)',(key,item['title'])).lastrowid
                    first=db.execute('INSERT INTO video_cue(doc,language,track,start_ms,end_ms,text) VALUES(?,?,?,?,?,?)',(doc,language,'metadata',0,0,description)).lastrowid;last=first
                    for index,track in enumerate(item['tracks']):
                        if track['technical_status']!='passed':continue
                        parsed=inventory.inspect_subtitle(track_file(track),item['media']['duration_seconds_declared'],include_cues=True)
                        if parsed['technical_status']!='passed' or parsed['revision']!=track['revision']:raise ValueError('subtitle_changed')
                        for cue in parsed['cues']:
                            last=db.execute('INSERT INTO video_cue(doc,language,track,start_ms,end_ms,text) VALUES(?,?,?,?,?,?)',(doc,track['language_declared'] or '',str(index),cue['start_ms'],cue['end_ms'],cue['text'])).lastrowid
                        for origin in ('acquired_job', 'prepared_job', 'transcription_job'):
                            if track.get(origin):
                                published.setdefault(origin, set()).add(track[origin])
                        if main:
                            sample = []
                            length = 0
                            for cue in parsed['cues']:
                                sample.append(cue['text'])
                                length += len(cue['text']) + 1
                                if length >= 4000:
                                    break
                            domains.update(retrieval.domains({**subject, '_text': ' '.join(sample)}))
                        report['tracks']+=1
                    if main:
                        item['search_domains'] = sorted(domains)
                    db.execute('UPDATE video_doc SET first_cue=?,last_cue=? WHERE doc=?',(first,last,doc))
                    db.execute('INSERT INTO media VALUES(?,?,?,?)',(key,item['path'],version,json.dumps(item,ensure_ascii=False)))
                    report['videos']+=1
                    if time.monotonic()-last_saved>2:
                        save();last_saved=time.monotonic()
                if STOP.is_set():raise InterruptedError()
                fresh=archive_videos.progress()
                if fresh.get('job_id')!=archive_report.get('job_id') or fresh.get('finished')!=archive_report.get('finished'):report['archive_inventory_job']=None
                report['stage']='Publication des index de recherche vidéo';save()
                build_search_tables(db)
            publish_built()
            confirm_indexed_tracks(published)
            report.pop('stage')
            report.update(phase='completed',skipped=found['skipped'],inventory_errors=found['errors'],unexamined=found['unexamined'],limitations=found['limitations'],
                          per_video=[{'id':'video:'+item['inventory_id'],'path':item['path'],'title':item['title'],'subtitle_status':item['subtitle_status'],
                                      'archive':item.get('archive'),'provider':item.get('provider','local'),
                                      'media':item['media'],'source':{key:item['source'].get(key) for key in ('id','extractor','channel','upload_date_declared')},
                                      'revision':stat_revision(item),'same_source_paths':item['same_source_paths'],
                                      'tracks':[{key:track[key] for key in ('language_declared','origin','technical_status','errors','warnings')} for track in item['tracks']],
                                      'validation':item['validation'],'next_action':item['next_action']} for item in found['videos']])
        except InterruptedError:report.update(phase='paused',stopped_by=STOP_REASON)
        except Exception:report.update(phase='failed',error='L’inventaire n’a pas abouti ; l’ancien index reste conservé.')
        report.pop('stage',None)
        report['finished']=time.time();save()
        return report


async def start():
    global ACTIVE
    if work_queue.QUEUE.paused:raise HTTPException(409,'Reprenez la file pour lancer l’inventaire vidéo.')
    if running() is not None:raise HTTPException(409,'Un inventaire vidéo est déjà en cours.')
    STOP.clear()
    # Publish running before handing work to a thread: a fast poll must not
    # mistake the preceding completed report for the newly requested inventory.
    durable.write_bytes(store.ROOT/'videos-report.json',json.dumps({'schema':1,'phase':'running','started':time.time(),'videos':0,'tracks':0,'errors':[]}).encode(),private=True)
    ACTIVE=asyncio.create_task(asyncio.to_thread(scan));return {'accepted':True}


async def refresh_after(published):
    """Wait for an index built after publication, including during another scan."""
    task=running()
    if task is not None:
        await asyncio.shield(task)
    current=status()
    if current.get('started',0)<published or current.get('phase')!='completed':
        if current.get('phase') == 'paused' and current.get('stopped_by') == 'user':
            raise HTTPException(409,'L’actualisation des vidéos est en pause.')
        if running() is None:
            await start()
        report=await asyncio.shield(running())
        if report.get('phase')!='completed':
            raise HTTPException(503,'L’index vidéo n’a pas pu être actualisé.')
    return 'indexed'


def request_stop(reason='user'):
    global STOP_REASON
    STOP_REASON=reason;STOP.set()


async def stop(reason='user'):
    request_stop(reason)
    for task in (running(),partitions_running()):
        if task is None:continue
        # Both writing tasks check STOP and finish their SQLite transaction before shutdown.
        try:await asyncio.shield(task)
        except asyncio.CancelledError:
            if not task.cancelled():raise
        except Exception:pass
    return status()


def running():
    """The inventory task of this event loop, if one is still running."""
    return running_task(ACTIVE)


def partitions_running():
    return running_task(PARTITION_TASK)


def running_task(task):
    if task is None or task.done():return None
    try:same=task.get_loop() is asyncio.get_running_loop()
    except RuntimeError:same=False
    return task if same else None


def track_cues(payload,track):
    parsed=inventory.inspect_subtitle(track_file(track),payload['media']['duration_seconds_declared'],include_cues=True)
    if parsed['technical_status']!='passed' or parsed['revision']!=track['revision']:raise HTTPException(409,'Cette piste a changé ; actualisez les vidéos.')
    return parsed['cues']


def webvtt(key,index):
    _,payload,_=row('video:'+key)
    if not 0<=index<len(payload['tracks']):raise HTTPException(404,'Piste introuvable.')
    track=payload['tracks'][index]
    if track['technical_status']!='passed':raise HTTPException(422,'Cette piste ne passe pas les contrôles techniques. Consultez son rapport.')
    def stamp(ms):return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'
    return 'WEBVTT\n\n'+'\n\n'.join(stamp(c['start_ms'])+' --> '+stamp(c['end_ms'])+'\n'+html.escape(c['text'],quote=False) for c in track_cues(payload,track))+'\n'
