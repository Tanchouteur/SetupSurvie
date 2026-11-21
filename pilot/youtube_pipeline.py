"""Durable bridge between host YouTube downloads and portal video workers."""
import asyncio
import hashlib
import json
import logging
import time

from fastapi import HTTPException

from . import engine, operations, store, work_queue, youtube_downloads
from .youtube_list import INSTALLATION_LIST

TASKS = {}
TERMINAL_HOST = ('completed', 'error', 'interrupted', 'paused')


def initialize():
    with store.connect() as db:
        db.execute("UPDATE youtube_pipeline SET data=json_set(data,'$.status','queued') WHERE json_extract(data,'$.status') IN ('running','preparing')")

        db.execute("""UPDATE youtube_pipeline SET data=json_set(data,'$.done',json_extract(data,'$.total'))
            WHERE kind='youtube' AND json_extract(data,'$.done')>json_extract(data,'$.total')""")


def read(identifier):
    with store.connect() as db:
        row = db.execute('SELECT data FROM youtube_pipeline WHERE id=?', (identifier,)).fetchone()
    if not row:
        raise HTTPException(404, 'Travail YouTube introuvable.')
    return json.loads(row['data'])


def update(identifier, **changes):
    data = read(identifier)
    if all(data.get(key) == value for key, value in changes.items()):
        return
    data.update(changes)
    with store.connect() as db:
        db.execute('UPDATE youtube_pipeline SET data=?,updated=? WHERE id=?',
                   (json.dumps(data, ensure_ascii=False), time.time(), identifier))


def public(data):
    result = {key: data[key] for key in ('status','title','model','done','total','href','error','stage') if key in data}
    failures = [item for item in data.get('items', []) if item['status'] in ('error','refused')]
    if failures:
        result.update(failures=failures[:12], failure_count=len(failures))
    return result


def details(identifier):
    return public(read(identifier))


def insert(identifier, kind, **data):
    with store.connect() as db:
        db.execute('INSERT OR IGNORE INTO youtube_pipeline VALUES(?,?,?,?)',
                   (identifier, kind, json.dumps({'kind': kind, **data}, ensure_ascii=False), time.time()))


def enqueue(text, height, *, identifier=None):
    if len(text.encode('utf-8')) > youtube_downloads.MAX_TEXT:
        raise HTTPException(413, 'Liste trop longue : divisez-la en plusieurs fichiers.')
    summary = youtube_downloads.check(text)
    if not summary['videos'] or height not in (360, 480, 720):
        raise HTTPException(400, 'Vérifiez les adresses YouTube et la qualité choisie.')
    identifier = youtube_downloads.save(text, prune=False, identifier=identifier)
    count = len(summary['videos'])
    insert(identifier, 'youtube', title=f'{count} vidéo(s) · {height}p', status='queued',
           model='yt-dlp · Deno · FFmpeg', total=count, done=0, height=height,
           href='#/appareil/bibliotheque', items=[])
    return {'accepted': True, 'job': identifier, **summary}


async def submit(text, height):
    result = enqueue(text, height)
    launch(result['job'], download)
    return result


def enqueue_installation_list():
    path = store.ROOT / INSTALLATION_LIST
    if path.is_symlink():
        return True
    try:
        try:
            with path.open('rb') as source:
                raw = source.read(youtube_downloads.MAX_TEXT + 1)
        except FileNotFoundError:
            return False
        # The same list must retain its queue state after startup or install recovery.
        identifier = hashlib.sha256(b'SetupSurvie YouTube installation\0' + raw).hexdigest()[:32]
        enqueue(raw.decode('utf-8'), 480, identifier=identifier)
    except (HTTPException, OSError, UnicodeError):
        logging.getLogger(__name__).warning('La liste YouTube de l’installation n’a pas pu être ajoutée.')
    return True


def launch(identifier, worker):
    previous = TASKS.get(identifier)
    if previous and not previous.done():
        return
    task = asyncio.create_task(worker(identifier))
    TASKS[identifier] = task
    def finished(done):
        if TASKS.get(identifier) is done:
            TASKS.pop(identifier, None)
        if not done.cancelled() and (error := done.exception()):
            logging.getLogger(__name__).error('Un travail vidéo a été interrompu.', exc_info=error)
    task.add_done_callback(finished)


def observe(state):
    """Register finished files before the host changes jobs."""
    progress = state.get('youtube') or {}
    register_videos(item for item in progress.get('items', []) if item['status'] in ('downloaded','skipped'))


def register_videos(items):
    entries = []
    published = time.time()
    for item in items:
        path = item.get('path')
        if path:
            key = hashlib.sha256(path.encode('utf-8')).hexdigest()
            video_id = 'video:' + key
            data = {'kind':'youtube-track', 'path':path, 'video_id':video_id, 'status':'queued',
                    'title':item.get('title') or path.rsplit('/', 1)[-1],
                    'stage':'Indexation du titre', 'href':'#/bibliotheque/recherche?source=' + video_id,
                    'model':'Selon les pistes disponibles', 'published':published}
            entries.append(('youtube-track-' + key, 'youtube-track', json.dumps(data, ensure_ascii=False), published))
    if entries:
        with store.connect() as db:
            db.executemany('INSERT OR IGNORE INTO youtube_pipeline VALUES(?,?,?,?)', entries)


def register_indexed_youtube(report):
    """Backfill existing downloads and imports made from the host command line."""
    register_videos(item for item in report.get('per_video', [])
                    if item['path'].startswith('youtube/')
                    and (item.get('source', {}).get('extractor') or '').lower() == 'youtube')


@work_queue.tracked('youtube')
async def download(identifier):
    try:
        while True:
            # A busy host (e.g. preparing maps) must not reserve the model slot.
            state = await operations.library_command()
            own = state.get('youtube_list') == identifier
            archived = await operations.youtube_result(identifier) if not own and read(identifier).get('submitted') else None
            if archived:
                state, own = archived, True
            if own or state.get('phase') not in youtube_downloads.ACTIVE:
                break
            update(identifier, stage='Le PC serveur prépare une autre opération.')
            await asyncio.sleep(3)
        async with work_queue.QUEUE.slots['network']:
            if read(identifier).get('retry') or not own:
                try:
                    await operations.library_command('youtube-download', {'list': identifier, 'max_height': read(identifier)['height']})
                except HTTPException as error:
                    # Another preparation can claim the controller after status.
                    if error.status_code == 409 and 'déjà en cours' in str(error.detail):
                        update(identifier, status='queued')
                        return
                    raise
                update(identifier, submitted=True, retry=False)
                state = await operations.library_command()
            update(identifier, status='running', stage='Téléchargement sur le PC serveur', error=None)
            if work_queue.QUEUE.paused:
                await pause_active_download()
            await follow(identifier, state)
    except HTTPException as error:
        update(identifier, status='error', error=str(error.detail))
    except Exception:
        update(identifier, status='error', error='Le suivi du téléchargement a été interrompu. Vous pouvez réessayer.')
        logging.getLogger(__name__).exception('Suivi YouTube interrompu')


async def follow(identifier, state):
    missing = 0
    while True:
        if state.get('youtube_list') != identifier:
            state = await operations.youtube_result(identifier) or state
        if state.get('youtube_list') == identifier:
            missing = 0
            progress = state.get('youtube') or {}
            if progress:
                counts = progress.get('counts', {})
                total = progress.get('videos', read(identifier)['total'])
                if 'done' in progress and 'total' in progress:
                    # The host also counts rejected and duplicate input lines as processed.
                    done = progress['done'] - (progress['total'] - total)
                else:
                    done = sum(counts.get(key, 0) for key in ('downloaded', 'skipped', 'error'))
                done = max(0, min(done, total))
                current = progress.get('current') or {}
                stage = f"Vidéo {current.get('index', done)} / {total}"
                if current.get('percent') is not None:
                    stage += f" · fichier en cours {current['percent']:.0f} %"
                update(identifier, done=done, items=progress.get('items', []), stage=stage)
                # Register new tracks incrementally even if the batch stops.
                observe(state)
            phase = state.get('phase')
            if phase in TERMINAL_HOST:
                errors = (progress.get('counts') or {}).get('error', 0)
                if phase == 'paused' and read(identifier).get('hold'):
                    update(identifier, status='queued', retry=True, hold=False, stage='Reprise à la prochaine activation')
                    return
                status = 'error' if errors else phase
                update(identifier, status=status, stage=state.get('message'),
                       error=state.get('message') if status in ('error', 'interrupted') else None)
                return
        else:
            missing += 1
            if missing >= 3:
                raise HTTPException(503, 'Le contrôleur a perdu le suivi de cette liste. Vérifiez la mise à jour du PC serveur et réessayez.')
        await asyncio.sleep(2)
        state = await operations.library_command()


def select_track(payload):
    tracks = [(index, track['language_declared'].lower().split('-')[0])
              for index, track in enumerate(payload['tracks'])
              if track['technical_status'] == 'passed' and track.get('language_declared')]
    original = (payload.get('media', {}).get('language_declared') or '').lower().split('-')[0]
    if original and original != 'fr' and tracks and all(lang == 'fr' for _, lang in tracks):
        return 'transcribe', None
    if any(lang == 'fr' for _, lang in tracks):
        return 'french', None
    if tracks:
        return 'translate', next((index for index, lang in tracks if lang == 'en'), tracks[0][0])
    return 'transcribe', None


@work_queue.tracked('youtube-track')
async def prepare(identifier):
    from . import captions, transcriptions, videos

    data = read(identifier)
    video_id = data['video_id']
    try:
        async with work_queue.QUEUE.slots['local']:
            # The preparation's own turn only chooses or schedules the next
            # stage. Its child takes a separate turn for actual inference.
            update(identifier, stage='Actualisation de l’index des vidéos')
            await videos.refresh_after(data['published'])
            _, payload, _ = await asyncio.to_thread(videos.row, video_id)
            action, track = select_track(payload)
            if action == 'french':
                update(identifier, status='completed', stage='Piste française indexée', error=None)
                return
            kind, module = ('captions', captions) if action == 'translate' else ('speech', transcriptions)
            if action == 'translate':
                child = await captions.create(video_id, track, 'rapide')
            else:
                child = await transcriptions.create(video_id, '', 'rapide', False)
            if data.get('retry') and child['status'] in ('error', 'paused'):
                child = await module.resume(child['id'])
            update(identifier, status='preparing', stage=work_queue.KINDS[kind], child=child['id'],
                   model=engine.MODES['rapide']['model'] if kind=='captions' else 'Whisper small · CPU', error=None, retry=False)
        task = module.ACTIVE.get(child['id'])
        if task:
            await asyncio.gather(asyncio.shield(task), return_exceptions=True)
        result = module.get(child['id'])
        if result['status'] != 'completed':
            update(identifier, status='paused' if result['status']=='paused' else 'error',
                   error=result.get('error') or 'La piste n’a pas pu être préparée. Réessayez depuis la file.')
            return
        # A completed local transcription becomes the input to the next turn.
        update(identifier, stage='Publication de la piste dans l’index des vidéos')
        await videos.refresh_after(result['updated'] if result['index_status']=='pending' else 0)
        _, payload, _ = await asyncio.to_thread(videos.row, video_id)
        next_action, _ = select_track(payload)
        if next_action == 'french':
            update(identifier, status='completed', stage='Piste française indexée', error=None)
        elif kind == 'speech' and next_action == 'translate':
            update(identifier, status='queued', stage='Traduction française en attente')
        else:
            update(identifier, status='error', error='Aucune piste exploitable n’a été publiée dans l’index.')
    except HTTPException as error:
        if error.status_code == 429:
            update(identifier, status='queued', stage='En attente d’une place pour préparer la piste')
        else:
            update(identifier, status='paused' if error.status_code == 503 else 'error', error=str(error.detail))
    except Exception:
        update(identifier, status='error', error='La préparation des sous-titres a été interrompue. Vous pouvez réessayer.')
        logging.getLogger(__name__).exception('Préparation automatique des pistes interrompue')


def pending():
    with store.connect() as db:
        return [dict(row) for row in db.execute("""SELECT id,kind FROM youtube_pipeline
            WHERE json_extract(data,'$.status') IN ('queued','running','preparing') ORDER BY updated,rowid""")]


def listing():
    with store.connect() as db:
        rows = db.execute('''SELECT id,kind,data FROM youtube_pipeline
            WHERE json_extract(data,'$.status')!='completed'
            UNION ALL
            SELECT id,kind,data FROM (SELECT id,kind,data FROM youtube_pipeline
            WHERE json_extract(data,'$.status')='completed' ORDER BY updated DESC,rowid DESC LIMIT 40)''').fetchall()
    return [{'id': row['id'], 'type': work_queue.KINDS[row['kind']], **json.loads(row['data'])} for row in rows]


async def retry(identifier):
    data = read(identifier)
    if data['status'] not in ('error', 'paused', 'interrupted'):
        raise HTTPException(409, 'Seul un travail interrompu, en pause ou en erreur peut être relancé.')
    update(identifier, status='queued', error=None, retry=True)
    launch(identifier, download if data['kind']=='youtube' else prepare)


async def watch():
    """Independent of the browser; recover previous jobs and their media."""
    from . import videos

    observed_index = None
    installation_list_seen = False
    while True:
        try:
            if not installation_list_seen:
                installation_list_seen = await asyncio.to_thread(enqueue_installation_list)
            for item in pending():
                launch(item['id'], download if item['kind']=='youtube' else prepare)
            if operations.TOKEN:
                try:
                    state = await operations.library_command()
                    if state.get('action') == 'youtube-download':
                        observe(state)
                except HTTPException:
                    pass
            await videos.ensure_fresh()
            report = await asyncio.to_thread(videos.status)
            if report['phase'] == 'completed' and report.get('finished') != observed_index:
                register_indexed_youtube(report)
                observed_index = report.get('finished')
        except Exception:
            logging.getLogger(__name__).exception('Suivi automatique des vidéos indisponible')
        await asyncio.sleep(4)


async def stop():
    tasks = list(TASKS.values())
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def pause_active_download():
    active = work_queue.QUEUE.slots['network'].active
    if not active or not active[0] or active[0] not in TASKS:
        return
    identifier = active[0]
    data = read(identifier)
    if data['kind'] != 'youtube':
        return
    try:
        state = await operations.library_command()
        if state.get('youtube_list') == identifier and state.get('phase') in youtube_downloads.ACTIVE:
            update(identifier, hold=True)
            await operations.library_command('youtube-download-pause',{'list':identifier})
    except HTTPException:
        # The controller may already have finished. The next ticket stays paused.
        return
