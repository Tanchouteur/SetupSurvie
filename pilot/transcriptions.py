"""Explicit resumable MP4 speech recognition. Source media stays read-only.

The CPU decoder/recognizer lives in a private child, terminated and joined on
pause. Only a complete checked WebVTT track is published to the common index.
"""
import asyncio
from contextlib import contextmanager
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

from fastapi import HTTPException
from . import work_queue
from . import captions,durable,engine,operations,store,video_inventory,videos

ACTIVE={}
UNIT_MS=60000
MODEL_ROOT=Path(os.environ.get('PILOT_SPEECH_CACHE','/webui-data/cache/whisper'))
VERSIONS=Path('/srv/versions.json') if Path('/srv/versions.json').is_file() else Path(__file__).resolve().parents[1]/'deploy/versions.json'
NOTICE='Transcription locale automatique de la parole, non relue. Les mots et horodatages sont estimés ; les images et gestes ne sont pas analysés. Vérifiez les passages techniques avec la vidéo.'


def running():return any(not task.done() for task in ACTIVE.values())


@contextmanager
def connect():
    durable.mkdir(store.ROOT);path=store.ROOT/'video-transcriptions.db'
    db=sqlite3.connect(path,timeout=10);db.row_factory=sqlite3.Row;path.chmod(0o600)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.executescript('''CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,video_id TEXT NOT NULL,source_revision TEXT NOT NULL,
        title TEXT NOT NULL,language TEXT NOT NULL,detected_language TEXT,mode TEXT NOT NULL,translate_french INTEGER NOT NULL,
        status TEXT NOT NULL,error TEXT,created REAL NOT NULL,updated REAL NOT NULL,probe TEXT,progress_ms INTEGER NOT NULL DEFAULT 0,
        published_hash TEXT,index_status TEXT,translation_job TEXT);
        CREATE INDEX IF NOT EXISTS jobs_by_video ON jobs(video_id, created DESC);
        CREATE TABLE IF NOT EXISTS units(job_id TEXT NOT NULL,start_ms INTEGER NOT NULL,end_ms INTEGER NOT NULL,result TEXT NOT NULL,
        PRIMARY KEY(job_id,start_ms));
        CREATE TABLE IF NOT EXISTS rejections(job_id TEXT NOT NULL,start_ms INTEGER NOT NULL,created REAL NOT NULL,reason TEXT NOT NULL,result TEXT NOT NULL);''')
    try:
        with db:yield db
    finally:db.close()


def get(identifier):
    with connect() as db:row=db.execute('SELECT * FROM jobs WHERE id=?',(identifier,)).fetchone()
    if not row:raise HTTPException(404,'Transcription introuvable.')
    return dict(row)


def update(identifier,state,error=None,**extra):
    if any(key not in ('probe','progress_ms','detected_language','published_hash','index_status','translation_job') for key in extra):raise ValueError('Unknown transcription field')
    with connect() as db:db.execute('UPDATE jobs SET status=?,error=?,updated=?'+''.join(','+key+'=?' for key in extra)+' WHERE id=?',
        (state,error,time.time(),*extra.values(),identifier))


def status(identifier,full=False):
    item=get(identifier)
    if item['status'] in ('queued','running') and identifier not in ACTIVE:
        update(identifier,'paused','Transcription interrompue ; reprenez-la explicitement.');item=get(identifier)
    with connect() as db:units=[json.loads(row[0]) for row in db.execute('SELECT result FROM units WHERE job_id=? ORDER BY start_ms',(identifier,))]
    probe=json.loads(item['probe']) if item['probe'] else {}
    result={key:item[key] for key in ('id','video_id','title','language','detected_language','mode','translate_french','status','error','created','updated','progress_ms','index_status','translation_job')}
    result.update(duration_ms=probe.get('duration_ms'),units_done=len(units),cues=sum(len(unit['cues']) for unit in units),
        human_review='not_performed',notice=NOTICE)
    if full:
        with connect() as db:rejected=[{**dict(row),'result':json.loads(row['result'])} for row in db.execute('SELECT start_ms,created,reason,result FROM rejections WHERE job_id=? ORDER BY created',(identifier,))]
        result.update(source_revision=item['source_revision'],published_hash=item['published_hash'],probe=probe,units=units,rejected_proposals=rejected)
    return result


def listing(limit=100, *, video_id=None):
    query='SELECT id FROM jobs'
    parameters=[]
    if video_id is not None:
        query+=' WHERE video_id=?'
        parameters.append(video_id)
    query+=' ORDER BY created DESC'
    if limit is not None:
        query+=' LIMIT ?'
        parameters.append(limit)
    with connect() as db:
        identifiers=[row[0] for row in db.execute(query,parameters)]
    return [status(identifier) for identifier in identifiers]


def model_config():
    try:
        pin=json.loads(VERSIONS.read_text())['speech'];marker=MODEL_ROOT/'ready.json';folder=MODEL_ROOT/'faster-whisper-small'
        if json.loads(marker.read_text())!=pin:raise ValueError()
        for path in (MODEL_ROOT,folder,*[folder/name for name in ('model.bin','config.json','tokenizer.json')]):
            if video_inventory.is_link(path) or not path.exists():raise ValueError()
        runtime={key:importlib.metadata.version(key) for key in ('faster-whisper','av','ctranslate2')}
        return {'available':True,'model_path':str(folder),'model':pin,'runtime':runtime,'device':'cpu','compute_type':'int8',
            'threads':max(1,min(4,(os.cpu_count() or 2)//2))}
    except (OSError,ValueError,KeyError,importlib.metadata.PackageNotFoundError):
        return {'available':False,'reason':'speech_not_prepared','message':'La reconnaissance vocale n’est pas préparée. Préparez la dictée avec l’installateur, une fois avec Internet, puis réessayez.'}


def current_source(item):
    _,payload,_=videos.row(item['video_id'])
    if videos.original_revision(payload)!=item['source_revision']:raise HTTPException(409,'Cette vidéo a changé. Actualisez les vidéos puis créez une nouvelle transcription ; les anciens passages restent conservés.')
    if payload.get('provider')=='zim':
        from . import archive_videos
        return payload,{'archive':archive_videos.audio_source(payload)}
    return payload,{'path':str(videos.safe_file(payload['path']))}


def track_file(identifier):
    if not isinstance(identifier,str) or not re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',identifier):raise HTTPException(400,'Référence de transcription invalide.')
    directory=store.ROOT/'video-transcriptions'/identifier;path=directory/'source.vtt'
    if any(parent.exists() and video_inventory.is_link(parent) for parent in (store.ROOT,store.ROOT/'video-transcriptions',directory,path)):
        raise HTTPException(409,'Lien de fichier refusé pour cette transcription.')
    return path


async def available():
    state=await operations.status(fresh=True)
    if state.get('paused'):raise HTTPException(503,'L’assistant est en pause. Les passages terminés sont conservés ; reprenez la transcription après la pause.')


class Worker:
    def __init__(self):self.process=None

    async def start(self):
        env={key:os.environ[key] for key in ('PATH','LANG','LC_ALL','SYSTEMROOT','WINDIR') if key in os.environ}
        env.update(HF_HUB_OFFLINE='1',CUDA_VISIBLE_DEVICES='',PYTHONUNBUFFERED='1')
        creation=asyncio.create_task(asyncio.create_subprocess_exec(sys.executable,'-m','pilot.speech_worker',
            cwd=str(Path(__file__).resolve().parents[1]),env=env,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,limit=1_000_000))
        try:self.process=await asyncio.shield(creation)
        except asyncio.CancelledError:
            self.process=await asyncio.shield(creation);await self.close();raise

    async def close(self):
        if self.process is None:return
        if self.process.returncode is None:
            try:self.process.terminate()
            except ProcessLookupError:pass
            try:await asyncio.wait_for(self.process.wait(),5)
            except TimeoutError:self.process.kill();await self.process.wait()

    async def call(self,command):
        if self.process is None:await self.start()
        self.process.stdin.write((json.dumps(command)+'\n').encode());await self.process.stdin.drain()
        response=asyncio.create_task(self.process.stdout.readline());start=time.monotonic()
        try:
            while not response.done():
                await asyncio.wait({response},timeout=1);await available()
                if time.monotonic()-start>900:raise ValueError('La reconnaissance de ce passage dépasse quinze minutes. Il reste à reprendre ; aucun résultat partiel n’est publié.')
            line=await response
            if len(line)>900000:raise ValueError('Réponse de transcription trop longue ; le passage reste à reprendre.')
            try:value=json.loads(line)
            except ValueError:raise ValueError('L’outil audio s’est arrêté sans réponse exploitable. Les passages terminés restent conservés.') from None
            if not value.get('ok'):
                messages={
                    'archive_reader_unavailable':'Le lecteur des collections ne répond pas. Les passages terminés sont conservés ; reprenez quand Kiwix fonctionne.',
                    'archive_edition_unavailable':'Le lecteur n’utilise pas la même édition de la collection. Si elle vient de changer, arrêtez puis rouvrez SetupSurvie avant un nouvel examen.',
                    'archive_media_range_unavailable':'Le lecteur ne permet pas de lire cette vidéo par portions. Aucune copie complète ou piste partielle n’a été publiée.',
                    'archive_media_redirect_refused':'Cette référence renvoie vers un autre média ; la reconnaissance reste en attente d’une source locale vérifiée.',
                    'archive_media_response_invalid':'Le média renvoyé ne correspond pas à l’inventaire. Vérifiez la collection avant de reprendre.',
                    'archive_secondary_reference_refused':'Ce média demande d’ouvrir une autre ressource. La reconnaissance accepte ici les fichiers vidéo inclus, sans liste distante.'}
                raise ValueError(messages.get(value.get('reason'),'Le décodage audio ou la reconnaissance a échoué. Vérifiez le format du fichier et la préparation de la dictée.'))
            return value['result']
        finally:
            if not response.done():response.cancel();await asyncio.gather(response,return_exceptions=True)


def checked_unit(value,start,end):
    if not isinstance(value,dict) or not isinstance(value.get('cues'),list) or type(value.get('eof')) is not bool:raise ValueError('Réponse de transcription non exploitable.')
    if type(value.get('last_decoded_ms')) is not int or value['last_decoded_ms']<0:raise ValueError('Chronologie audio non exploitable.')
    previous=start;boundary=min(end,value['last_decoded_ms']) if value['eof'] else end
    for cue in value['cues']:
        if not isinstance(cue,dict) or any(type(cue.get(k)) is not int for k in ('start_ms','end_ms')) or not isinstance(cue.get('text'),str):raise ValueError('Segment de transcription non exploitable.')
        if not start<=cue['start_ms']<cue['end_ms']<=boundary or cue['start_ms']<previous or not cue['text'].strip() or len(cue['text'])>6000:raise ValueError('Les horodatages reconnus se chevauchent ou sortent du passage. Gardez le rapport pour vérification.')
        previous=cue['end_ms']
    return value


def publish(identifier):
    import html
    item=get(identifier);payload,_=current_source(item)
    with connect() as db:units=[json.loads(row[0]) for row in db.execute('SELECT result FROM units WHERE job_id=? ORDER BY start_ms',(identifier,))]
    cues=[cue for unit in units for cue in unit['cues']]
    if not cues:raise ValueError('Aucune parole exploitable n’a été reconnue. Aucun sous-titre vide n’est publié ; vérifiez la piste audio.')
    content='WEBVTT\n\n'+'\n\n'.join(captions.stamp(cue['start_ms'])+' --> '+captions.stamp(cue['end_ms'])+'\n'+html.escape(cue['text'],quote=False) for cue in cues)+'\n'
    path=track_file(identifier);durable.write_bytes(path,content.encode(),private=True)
    parsed=video_inventory.inspect_subtitle(path,None,include_cues=True)
    if parsed['technical_status']!='passed' or len(parsed['cues'])!=len(cues):raise ValueError('La transcription complète ne passe pas les contrôles de sous-titres. Elle reste privée et non publiée.')
    current_source(item)
    with connect() as db:
        current=db.execute('SELECT status FROM jobs WHERE id=?',(identifier,)).fetchone()[0]
        if current!='running':return False
        db.execute("UPDATE jobs SET status='completed',published_hash=?,updated=?,index_status='pending' WHERE id=?",(parsed['text_utf8_sha256'],time.time(),identifier))
    return True


@work_queue.tracked('speech')
async def run(identifier):
    worker=Worker()
    try:
        config=model_config()
        if not config['available']:raise ValueError(config['message'])
        while True:
            async with work_queue.QUEUE.slots['local']:
                await available();item=get(identifier)
                if item['status'] not in ('queued','running'):return
                _,source=await asyncio.to_thread(current_source,item)
                update(identifier,'running')
                if not item['probe'] or not json.loads(item['probe']).get('audio_present'):
                    probe=await worker.call({'action':'probe',**source})
                    await asyncio.to_thread(current_source,item)
                    probe['recognizer']={key:config[key] for key in ('model','runtime','device','compute_type','threads')}
                    update(identifier,'running',probe=json.dumps(probe));item=get(identifier)
                    if not probe.get('audio_present'):raise ValueError('Cette vidéo ne contient pas de piste audio décodable. Aucune parole n’a été inventée.')
                start=item['progress_ms'];end=start+UNIT_MS;began=time.monotonic()
                value=await worker.call({'action':'transcribe',**source,'model_path':config['model_path'],
                    'threads':config['threads'],'language':item['detected_language'] or item['language'] or None,'start_ms':start,'end_ms':end})
                try:checked_unit(value,start,end)
                except ValueError as error:
                    with connect() as db:db.execute('INSERT INTO rejections VALUES(?,?,?,?,?)',(identifier,start,time.time(),str(error),json.dumps(value,ensure_ascii=False,allow_nan=False)))
                    raise
                await asyncio.to_thread(current_source,item);await available()
                value.update(start_ms=start,end_ms=end,elapsed_ms=round((time.monotonic()-began)*1000),
                    recognizer={key:config[key] for key in ('model','runtime','device','compute_type','threads')})
                language=value.get('language') or item['detected_language']
                if language and (not isinstance(language,str) or not re.fullmatch(r'[a-z]{2,3}',language)):raise ValueError('Langue reconnue non exploitable.')
                finished=value['eof'] and value['last_decoded_ms']<=end
                with connect() as db:
                    db.execute('INSERT INTO units VALUES(?,?,?,?)',(identifier,start,end,json.dumps(value,ensure_ascii=False,allow_nan=False)))
                    db.execute('UPDATE jobs SET progress_ms=?,detected_language=?,updated=? WHERE id=?',
                        (max(start,min(end,value['last_decoded_ms'])) if finished else end,language,time.time(),identifier))
                if finished:
                    publication=asyncio.create_task(asyncio.to_thread(publish,identifier))
                    try:published=await asyncio.shield(publication)
                    except asyncio.CancelledError:
                        update(identifier,'paused','Transcription mise en pause ; passages terminés conservés.');await asyncio.shield(publication);raise
                    if not published:return
                    break
            # A waiting ordinary question gets the lock between audio units.
            await asyncio.sleep(1)
        try:await videos.refresh_after(time.time());update(identifier,'completed',index_status='requested')
        except HTTPException:update(identifier,'completed',index_status='pending')
        item=get(identifier)
        if item['translate_french'] and not (item['detected_language'] or item['language']).startswith('fr'):
            # The scan attaches the completed source before its ordinary French
            # translation is requested. A busy/failed inventory stays explicit.
            if videos.ACTIVE:await asyncio.shield(videos.ACTIVE)
            _,payload,_=videos.row(item['video_id'])
            source=next((index for index,track in enumerate(payload['tracks']) if track.get('transcription_job')==identifier),None)
            if source is not None:
                translation=await captions.create(item['video_id'],source,item['mode']);update(identifier,'completed',translation_job=translation['id'])
    except asyncio.CancelledError:
        if get(identifier)['status'] in ('queued','running'):update(identifier,'paused','Transcription mise en pause ; passages terminés conservés.')
        raise
    except HTTPException as error:
        item=get(identifier)
        if item['status']=='completed':update(identifier,'completed','Transcription terminée ; la traduction française reste à lancer depuis cette vidéo.')
        else:update(identifier,'paused' if error.status_code==503 else 'error',str(error.detail))
    except ValueError as error:
        update(identifier,'completed' if get(identifier)['status']=='completed' else 'error',str(error))
    except Exception:
        if get(identifier)['status']=='completed':update(identifier,'completed','La transcription est conservée ; la préparation française reste à lancer depuis cette vidéo.')
        else:update(identifier,'error','Transcription interrompue. Les passages terminés restent conservés ; vérifiez le fichier et la préparation de la dictée.')
    finally:await worker.close()


def launch(identifier):
    task=asyncio.create_task(run(identifier));ACTIVE[identifier]=task
    def done(task):
        if ACTIVE.get(identifier) is task:ACTIVE.pop(identifier,None)
    task.add_done_callback(done)


async def create(video_id,language='',mode='rapide',translate_french=True):
    if not isinstance(language,str) or (language and not re.fullmatch(r'[a-z]{2,3}',language)):raise HTTPException(400,'Choisissez une langue source valide ou la détection automatique.')
    if mode not in engine.MODES:raise HTTPException(400,'Mode IA inconnu.')
    await available();config=model_config()
    if not config['available']:raise HTTPException(409,config['message'])
    _,payload,_=await asyncio.to_thread(videos.row,video_id);revision=videos.original_revision(payload)
    if not revision:raise HTTPException(409,'La vidéo a changé ; actualisez les vidéos.')
    key=store.new_id();now=time.time()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        previous=db.execute('SELECT id FROM jobs WHERE video_id=? AND source_revision=? AND language=? AND translate_french=? ORDER BY created DESC LIMIT 1',
            (video_id,revision,language,int(translate_french))).fetchone()
        if not previous:
            if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=2:raise HTTPException(429,'Deux transcriptions attendent déjà. Reprenez-les ou mettez-les en pause.')
            db.execute('INSERT INTO jobs(id,video_id,source_revision,title,language,mode,translate_french,status,created,updated,index_status) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (key,video_id,revision,payload['title'],language,mode,int(translate_french),'queued',now,now,'not_published'))
    if previous:return status(previous[0])
    launch(key);return status(key)


async def pause(identifier):
    item=get(identifier)
    if item['status'] in ('queued','running'):
        update(identifier,'paused','Transcription mise en pause ; passages terminés conservés.')
        task=ACTIVE.get(identifier)
        if task:task.cancel();await asyncio.gather(task,return_exceptions=True)
    return status(identifier)


async def resume(identifier):
    item=get(identifier)
    if item['status'] in ('queued','running') and identifier not in ACTIVE:status(identifier);item=get(identifier)
    if item['status'] not in ('paused','error'):raise HTTPException(409,'Cette transcription est déjà active ou terminée.')
    await available();await asyncio.to_thread(current_source,item)
    with connect() as db:
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=2:raise HTTPException(429,'La file des transcriptions est pleine.')
    update(identifier,'queued');launch(identifier);return status(identifier)


async def stop_all():
    tasks=list(ACTIVE.values())
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)


def prepared_tracks(payload):
    revision=videos.original_revision(payload)
    with connect() as db:rows=[dict(row) for row in db.execute("SELECT * FROM jobs WHERE video_id=? AND source_revision=? AND status='completed' ORDER BY created DESC",('video:'+payload['inventory_id'],revision))]
    for item in rows:
        try:
            parsed=video_inventory.inspect_subtitle(track_file(item['id']),None)
            if parsed['technical_status']!='passed' or parsed['text_utf8_sha256']!=item['published_hash']:continue
            return [{'path':item['id']+'/source.vtt','transcription_job':item['id'],'source_revision':revision,
                'language_declared':item['detected_language'] or item['language'],'language_basis':'local_speech_recognition',
                'origin':'local_transcription','transcription_notice':NOTICE,**parsed}]
        except (OSError,HTTPException):continue
    return []
