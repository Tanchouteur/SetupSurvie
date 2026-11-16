"""Explicit subtitle acquisition, separate from offline reading and recognition.

The original MP4 is never changed. Provider rows and adjusted display intervals
remain private; only complete checked tracks are attached to the common index.
"""
import asyncio
from contextlib import contextmanager
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

from fastapi import HTTPException
from . import captions,durable,engine,provider_subtitles,store,video_inventory,videos

ACTIVE={}
CONTROL_LOCK=asyncio.Lock()
NOTICE='Sous-titres récupérés sur YouTube, non relus. Langue et origine sont déclarées par le fournisseur. Les intervalles qui se chevauchent sont ajustés pour l’affichage ; vérifiez l’alignement avec votre vidéo locale.'
REASONS={'provider_tool_unavailable':'L’outil de récupération des sous-titres manque dans cette installation.',
    'provider_blocked':'YouTube refuse cette récupération. Aucun contournement n’est lancé ; la reconnaissance audio locale reste possible.',
    'provider_captions_unavailable':'Aucune piste accessible n’a été récupérée pour cette référence. La reconnaissance audio locale reste possible.',
    'provider_unreachable':'La récupération n’a pas abouti. Vérifiez Internet ou reprenez plus tard ; les pistes déjà disponibles restent utilisables.',
    'source_reference_required':'L’adresse YouTube de cette vidéo est nécessaire. Indiquez sa référence exacte, pas une recherche par titre.',
    'invalid_video_reference':'Indiquez une adresse HTTPS YouTube ou son identifiant vidéo valide.',
    'provider_track_unavailable':'La piste choisie n’est plus proposée. Reprenez avec une autre langue ou le choix automatique.',
    'provider_response_too_large':'La réponse de la source dépasse la limite de préparation. Aucune piste partielle n’est publiée.'}


def running():return any(not task.done() for task in ACTIVE.values())


@contextmanager
def connect():
    durable.mkdir(store.ROOT);path=store.ROOT/'video-acquisition.db'
    db=sqlite3.connect(path,timeout=10);db.row_factory=sqlite3.Row;path.chmod(0o600)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.execute('''CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,video_id TEXT NOT NULL,source_revision TEXT NOT NULL,
        title TEXT NOT NULL,provider_id TEXT NOT NULL,identity_basis TEXT NOT NULL,language TEXT NOT NULL,origin TEXT NOT NULL,
        preferred_language TEXT NOT NULL,mode TEXT NOT NULL,translate_french INTEGER NOT NULL,status TEXT NOT NULL,error TEXT,
        created REAL NOT NULL,updated REAL NOT NULL,published_hash TEXT,index_status TEXT,translation_job TEXT,result_summary TEXT)''')
    if 'result_summary' not in {row[1] for row in db.execute('PRAGMA table_info(jobs)')}:
        try:db.execute('ALTER TABLE jobs ADD COLUMN result_summary TEXT')
        except sqlite3.OperationalError:
            if 'result_summary' not in {row[1] for row in db.execute('PRAGMA table_info(jobs)')}:raise
    try:
        with db:yield db
    finally:db.close()


def get(identifier):
    with connect() as db:item=db.execute('SELECT * FROM jobs WHERE id=?',(identifier,)).fetchone()
    if not item:raise HTTPException(404,'Récupération de sous-titres introuvable.')
    return dict(item)


def update(identifier,state,error=None,**extra):
    if any(key not in ('published_hash','index_status','translation_job') for key in extra):raise ValueError('Unknown acquisition field')
    with connect() as db:db.execute('UPDATE jobs SET status=?,error=?,updated=?'+''.join(','+key+'=?' for key in extra)+' WHERE id=?',
        (state,error,time.time(),*extra.values(),identifier))


def files(identifier):
    if not isinstance(identifier,str) or not re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',identifier):raise HTTPException(400,'Référence de récupération invalide.')
    folder=store.ROOT/'video-acquisition'/identifier
    if any(path.exists() and video_inventory.is_link(path) for path in (store.ROOT,folder.parent,folder)):
        raise HTTPException(409,'Lien refusé pour les sous-titres récupérés.')
    return folder


def track_file(identifier):
    path=files(identifier)/'source.vtt'
    if path.exists() and video_inventory.is_link(path):raise HTTPException(409,'Lien de piste récupérée refusé.')
    return path


def status(identifier,full=False):
    item=get(identifier)
    if item['status'] in ('queued','running') and identifier not in ACTIVE:
        update(identifier,'paused','Récupération interrompue ; reprenez-la explicitement avec Internet.');item=get(identifier)
    result={key:item[key] for key in ('id','video_id','title','status','error','created','updated','index_status','translation_job')}
    result.update(notice=NOTICE,human_review='not_performed')
    if item['result_summary']:
        try:result.update(json.loads(item['result_summary']))
        except ValueError:result['provider_report_unavailable']=True
    private=files(identifier)/'provider.json'
    if full and private.is_file() and not video_inventory.is_link(private):
        try:
            value=json.loads(private.read_text());result.update(language=value['track']['language'],origin=value['track']['origin'],cues=len(value['cues']),timing_adjustments=len(value['timing_adjustments']))
            result.update(provider_result=value)
        except (OSError,ValueError,KeyError):result['provider_report_unavailable']=True
    if full:result.update(source_revision=item['source_revision'],provider_id=item['provider_id'],identity_basis=item['identity_basis'],published_hash=item['published_hash'])
    return result


def listing(limit=100):
    with connect() as db:ids=[row[0] for row in db.execute('SELECT id FROM jobs ORDER BY created DESC'+(' LIMIT ?' if limit is not None else ''),(limit,) if limit is not None else ())]
    return [status(identifier) for identifier in ids]


def current_source(item):
    _,payload,_=videos.row(item['video_id'])
    if videos.original_revision(payload)!=item['source_revision']:raise HTTPException(409,'Cette vidéo a changé ; actualisez l’inventaire et créez une nouvelle récupération. Les anciens fichiers restent conservés.')
    return payload


class FetchWorker:
    def __init__(self):self.process=None;self.closing=None

    async def fetch(self,command):
        # No user environment, cookie, token or proxy is passed to this child.
        env={key:os.environ[key] for key in ('PATH','LANG','LC_ALL','SYSTEMROOT','WINDIR') if key in os.environ};env['PYTHONUNBUFFERED']='1'
        creation=asyncio.create_task(asyncio.create_subprocess_exec(sys.executable,'-m','pilot.caption_fetch_worker',
            cwd=str(Path(__file__).resolve().parents[1]),env=env,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL))
        try:self.process=await asyncio.shield(creation)
        except asyncio.CancelledError:
            self.process=await asyncio.shield(creation);await self.close();raise
        encoded=json.dumps(command).encode()
        try:
            async with asyncio.timeout(90):
                self.process.stdin.write(encoded);await self.process.stdin.drain();self.process.stdin.close()
                # Bound the child's output; communicate() alone could allocate an
                # unbounded buffer before checking a malicious provider payload.
                pieces=[];size=0
                while chunk:=await self.process.stdout.read(65536):
                    size+=len(chunk)
                    if size>24_000_000:raise ValueError('provider_response_too_large')
                    pieces.append(chunk)
                await self.process.wait()
                value=json.loads(b''.join(pieces))
        except TimeoutError:raise ValueError('provider_unreachable') from None
        if not value.get('ok'):raise ValueError(value.get('reason') if value.get('reason') in REASONS else 'provider_captions_unavailable')
        return value['result']

    async def close(self):
        if self.process is None:return
        if self.closing is None:self.closing=asyncio.create_task(self._close())
        try:await asyncio.shield(self.closing)
        except asyncio.CancelledError:
            await asyncio.shield(self.closing);raise

    async def _close(self):
        async def discard_output():
            while await self.process.stdout.read(65536):pass
        # wait() alone can leave the read pipe open after an oversized response,
        # especially on Python 3.12. Drain without retaining any further bytes.
        draining=asyncio.create_task(discard_output())
        if self.process.stdin and not self.process.stdin.is_closing():self.process.stdin.close()
        try:
            if self.process.returncode is None:
                try:self.process.terminate()
                except ProcessLookupError:pass
            try:await asyncio.wait_for(self.process.wait(),5)
            except TimeoutError:
                if self.process.returncode is None:
                    try:self.process.kill()
                    except ProcessLookupError:pass
                await self.process.wait()
            await draining
        finally:
            if not draining.done():draining.cancel();await asyncio.gather(draining,return_exceptions=True)


def publish(identifier,value):
    item=get(identifier);payload=current_source(item)
    if value.get('video_id')!=item['provider_id']:raise ValueError('invalid_video_reference')
    cues,adjustments=provider_subtitles.checked_cues(value['raw_provider_cues'])
    if cues!=value.get('cues') or adjustments!=value.get('timing_adjustments'):raise ValueError('invalid_provider_cues')
    language=value.get('track',{}).get('language');origin=value.get('track',{}).get('origin')
    if not isinstance(language,str) or not provider_subtitles.LANG.fullmatch(language) or origin not in ('provided','automatic'):raise ValueError('invalid_provider_cues')
    path=track_file(identifier);private=files(identifier)/'provider.json'
    for target in (private,path):
        if target.exists() and video_inventory.is_link(target):raise HTTPException(409,'Lien refusé pour cette récupération.')
    durable.write_bytes(private,json.dumps(value,ensure_ascii=False,allow_nan=False).encode(),private=True)
    content='WEBVTT\n\n'+'\n\n'.join(captions.stamp(cue['start_ms'])+' --> '+captions.stamp(cue['end_ms'])+'\n'+html.escape(cue['text'],quote=False) for cue in cues)+'\n'
    durable.write_bytes(path,content.encode(),private=True)
    checked=video_inventory.inspect_subtitle(path,payload['media']['duration_seconds_declared'],include_cues=True)
    if checked['technical_status']!='passed' or len(checked['cues'])!=len(cues):raise ValueError('invalid_provider_cues')
    with connect() as db:
        if db.execute('SELECT status FROM jobs WHERE id=?',(identifier,)).fetchone()[0]!='running':return False
        summary=json.dumps({'language':language,'origin':origin,'cues':len(cues),'timing_adjustments':len(adjustments)})
        db.execute("UPDATE jobs SET status='completed',published_hash=?,updated=?,index_status='pending',result_summary=? WHERE id=?",(checked['text_utf8_sha256'],time.time(),summary,identifier))
    return True


async def run(identifier):
    worker=FetchWorker()
    try:
        item=get(identifier)
        if item['status'] not in ('queued','running'):return
        await asyncio.to_thread(current_source,item);update(identifier,'running')
        value=await worker.fetch({'id':item['provider_id'],'preferred':item['preferred_language'],'language':item['language'],'origin':item['origin']})
        await asyncio.to_thread(current_source,item)
        publication=asyncio.create_task(asyncio.to_thread(publish,identifier,value))
        try:published=await asyncio.shield(publication)
        except asyncio.CancelledError:
            update(identifier,'paused','Récupération mise en pause ; les pistes terminées restent conservées.');await asyncio.shield(publication);raise
        if not published:return
        try:await videos.start();update(identifier,'completed',index_status='requested')
        except HTTPException:update(identifier,'completed',index_status='pending')
        item=get(identifier)
        if item['translate_french'] and not value['track']['language'].lower().startswith('fr'):
            if videos.ACTIVE:await asyncio.shield(videos.ACTIVE)
            _,payload,_=videos.row(item['video_id'])
            source=next((index for index,track in enumerate(payload['tracks']) if track.get('acquired_job')==identifier),None)
            if source is not None:
                translation=await captions.create(item['video_id'],source,item['mode']);update(identifier,'completed',translation_job=translation['id'])
    except asyncio.CancelledError:
        if get(identifier)['status'] in ('queued','running'):update(identifier,'paused','Récupération mise en pause. Reprenez-la avec Internet ; aucun fichier source n’est modifié.')
        raise
    except (ValueError,HTTPException) as error:
        message=str(error.detail) if isinstance(error,HTTPException) else REASONS.get(str(error),'Les sous-titres reçus ne passent pas les contrôles. Aucune piste partielle n’est publiée.')
        if get(identifier)['status']=='completed':update(identifier,'completed','Piste récupérée et conservée ; la traduction française reste à lancer depuis la vidéo.')
        else:update(identifier,'error',message)
    except Exception:
        if get(identifier)['status']=='completed':update(identifier,'completed','Piste conservée ; actualisez les vidéos et lancez sa traduction si nécessaire.')
        else:update(identifier,'error',REASONS['provider_unreachable'])
    finally:await worker.close()


def launch(identifier):
    task=asyncio.create_task(run(identifier));ACTIVE[identifier]=task
    def done(task):
        if ACTIVE.get(identifier) is task:ACTIVE.pop(identifier,None)
    task.add_done_callback(done)


async def create(video_id,reference='',language='',origin='',mode='rapide',translate_french=True):
    async with CONTROL_LOCK:return await _create(video_id,reference,language,origin,mode,translate_french)


async def _create(video_id,reference,language,origin,mode,translate_french):
    if mode not in engine.MODES:raise HTTPException(400,'Mode IA inconnu.')
    if (language and not provider_subtitles.LANG.fullmatch(language)) or origin not in ('','provided','automatic'):raise HTTPException(400,'Choisissez une langue et une origine valides.')
    _,payload,_=await asyncio.to_thread(videos.row,video_id)
    try:provider=provider_subtitles.identity(payload,reference)
    except ValueError as error:raise HTTPException(400,REASONS.get(str(error),REASONS['invalid_video_reference'])) from None
    revision=videos.original_revision(payload)
    if not revision:raise HTTPException(409,'La vidéo a changé ; actualisez les vidéos.')
    key=store.new_id();now=time.time()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        previous=db.execute('SELECT id FROM jobs WHERE video_id=? AND source_revision=? AND provider_id=? AND language=? AND origin=? AND translate_french=? ORDER BY created DESC LIMIT 1',
            (video_id,revision,provider['id'],language,origin,int(translate_french))).fetchone()
        if not previous:
            if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=2:raise HTTPException(429,'Deux récupérations sont déjà en cours ; attendez ou mettez-les en pause.')
            db.execute('INSERT INTO jobs(id,video_id,source_revision,title,provider_id,identity_basis,language,origin,preferred_language,mode,translate_french,status,created,updated,index_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,video_id,revision,payload['title'],provider['id'],provider['basis'],language,origin,payload['media'].get('language_declared') or '',mode,int(translate_french),'queued',now,now,'not_published'))
    if previous:return status(previous[0])
    launch(key);return status(key)


async def pause(identifier):
    async with CONTROL_LOCK:return await _pause(identifier)


async def _pause(identifier):
    if get(identifier)['status'] in ('queued','running'):
        update(identifier,'paused','Récupération mise en pause ; reprenez-la explicitement avec Internet.')
        task=ACTIVE.get(identifier)
        if task:task.cancel();await asyncio.gather(task,return_exceptions=True)
    return status(identifier)


async def resume(identifier):
    async with CONTROL_LOCK:return await _resume(identifier)


async def _resume(identifier):
    item=get(identifier)
    if item['status'] in ('queued','running') and identifier not in ACTIVE:status(identifier);item=get(identifier)
    if item['status'] not in ('paused','error'):raise HTTPException(409,'Cette récupération est déjà active ou terminée.')
    await asyncio.to_thread(current_source,item)
    with connect() as db:
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=2:raise HTTPException(429,'La file des récupérations est pleine.')
    update(identifier,'queued');launch(identifier);return status(identifier)


async def stop_all():
    tasks=list(ACTIVE.values())
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)


def prepared_tracks(payload):
    revision=videos.original_revision(payload)
    with connect() as db:rows=[dict(row) for row in db.execute("SELECT * FROM jobs WHERE video_id=? AND source_revision=? AND status='completed' ORDER BY created DESC",('video:'+payload['inventory_id'],revision))]
    result=[];languages=set()
    for item in rows:
        try:
            if item['result_summary']:summary=json.loads(item['result_summary'])
            else:
                private=files(item['id'])/'provider.json'
                if video_inventory.is_link(private):continue
                value=json.loads(private.read_text());summary={**value['track'],'timing_adjustments':len(value['timing_adjustments'])}
            language=summary['language']
            if language in languages:continue
            parsed=video_inventory.inspect_subtitle(track_file(item['id']),payload['media']['duration_seconds_declared'])
            if parsed['technical_status']!='passed' or parsed['text_utf8_sha256']!=item['published_hash']:continue
            result.append({'path':item['id']+'/source.vtt','acquired_job':item['id'],'source_revision':revision,
                'language_declared':language,'language_basis':'provider_declared','origin':summary['origin'],
                'acquisition_notice':NOTICE,'timing_adjustments':summary['timing_adjustments'],'provider':'youtube',**parsed})
            languages.add(language)
        except (OSError,ValueError,KeyError,HTTPException):continue
    return result
