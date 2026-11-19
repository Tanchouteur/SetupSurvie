"""Independent execution slots for portal work. Workers own their checkpoints."""
import asyncio
from collections import deque
from contextvars import ContextVar
from functools import wraps
import json
import logging
import sqlite3

from fastapi import HTTPException

from . import store

CURRENT = ContextVar('portal_work', default=None)
KINDS = {
    'chat': 'Question à l’assistant',
    'summary': 'Synthèse de documents',
    'translation': 'Traduction de document',
    'captions': 'Traduction de sous-titres',
    'speech': 'Transcription audio',
    'acquisition': 'Récupération de sous-titres',
    'youtube': 'Téléchargement YouTube',
    'youtube-track': 'Préparation de sous-titres YouTube',
    'calibration': 'Calibrage du modèle',
    'search-test': 'Essai de recherche avec IA',
    'performance': 'Essai de performances',
    'translation-test': 'Essai de traduction',
}


BACKGROUND_LANE = {'youtube': 'network', 'acquisition': 'network', 'speech': 'local', 'youtube-track': 'local', 'video-index': 'local'}
CHAT_BURST = 3


class Slot:
    def __init__(self, queue, *, prioritize_chat=False):
        self.queue = queue
        self.prioritize_chat = prioritize_chat
        self.waiters = []
        self.active = None
        self.chats_while_waiting = 0

    def locked(self):
        return self.active is not None

    def priority(self, key):
        record = self.queue.records.get(key, {})
        return self.prioritize_chat and record.get('priority', record.get('kind') == 'chat')

    def choose(self, tickets, chats):
        question = next((ticket for ticket in tickets if self.priority(ticket[0])), None)
        background = next((ticket for ticket in tickets if not self.priority(ticket[0])), None)
        if question and background and chats < CHAT_BURST:
            return question, chats + 1
        return background or question, 0

    def order(self):
        questions, background = deque(), deque()
        for key, future in self.waiters:
            if not future.cancelled():
                (questions if self.priority(key) else background).append(key)
        ordered = []
        chats = self.chats_while_waiting
        while questions and background:
            if chats < CHAT_BURST:
                ordered.append(questions.popleft())
                chats += 1
            else:
                ordered.append(background.popleft())
                chats = 0
        return ordered + list(questions) + list(background)

    def dispatch(self):
        if self.queue.paused or self.active is not None:
            return
        self.waiters[:] = [ticket for ticket in self.waiters if not ticket[1].cancelled()]
        if self.waiters:
            ticket, self.chats_while_waiting = self.choose(self.waiters, self.chats_while_waiting)
            self.waiters.remove(ticket)
            self.active = ticket
            ticket[1].set_result(None)

    async def acquire(self):
        ticket = (CURRENT.get(), asyncio.get_running_loop().create_future())
        self.waiters.append(ticket)
        self.dispatch()
        try:
            await ticket[1]
        except BaseException:
            if ticket in self.waiters:
                self.waiters.remove(ticket)
            if self.active is ticket:
                self.active = None
            self.dispatch()
            raise
        return True

    async def __aenter__(self):
        await self.acquire()
        return self

    def release(self):
        if self.active is None:
            raise ValueError('Work slot already released')
        self.active = None
        self.dispatch()

    async def __aexit__(self, *_):
        self.release()


class Queue(Slot):
    def __init__(self):
        super().__init__(self, prioritize_chat=True)
        self.paused = False
        self.records = {}
        self.root = None
        self.slots = {'ai': self, 'network': Slot(self), 'local': Slot(self)}

    def initialize(self):
        with store.connect() as db:
            saved = db.execute("SELECT value FROM settings WHERE key='work-queue-paused'").fetchone()
        self.root = store.ROOT
        self.paused = bool(saved and saved[0] == '1')

    def set_paused(self, paused):
        with store.connect() as db:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('work-queue-paused',?)", ('1' if paused else '0',))
        self.paused = paused
        for slot in self.slots.values():
            slot.dispatch()

    def move(self, identifier, direction, profile):
        kind = self.records.get(identifier, {}).get('kind')
        slot = self.slots[BACKGROUND_LANE.get(kind, 'ai')]
        priority = slot.priority(identifier)
        visible = [(index, key) for index, (key, future) in enumerate(slot.waiters)
                   if not future.cancelled() and key in self.records
                   and slot.priority(key) == priority and can_move(self.records[key], profile)]
        position = next((i for i, (_, key) in enumerate(visible) if key == identifier), None)
        if position is None or not 0 <= position + direction < len(visible):
            raise HTTPException(409, 'La position a changé. Consultez de nouveau la file.')
        first, second = visible[position][0], visible[position + direction][0]
        slot.waiters[first], slot.waiters[second] = slot.waiters[second], slot.waiters[first]

    def save(self, record):
        if self.root is None or self.root != store.ROOT:
            return
        with store.connect() as db:
            db.execute("INSERT OR REPLACE INTO work_history VALUES(?,?,strftime('%s','now'))",
                       (record['id'], json.dumps(record, ensure_ascii=False)))
            db.execute('DELETE FROM work_history WHERE id IN (SELECT id FROM work_history ORDER BY updated DESC,rowid DESC LIMIT -1 OFFSET 300)')

    def snapshot(self, profile):
        from . import youtube_pipeline

        active = {slot.active[0] for slot in self.slots.values() if slot.active and slot.active[0] is not None}
        orders = {name: slot.order() for name, slot in self.slots.items()}
        ordered = [key for order in orders.values() for key in order]
        keys = set(ordered)
        records = self.records.copy()
        lanes = {name: {'running': slot.locked()} for name, slot in self.slots.items()}
        with store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute('SELECT data FROM work_history ORDER BY updated DESC,rowid DESC LIMIT 300')]
        video_jobs = {row['id']: row for row in youtube_pipeline.listing()}
        jobs = []
        for key in dict.fromkeys([*(key for key in records if key in active), *ordered, *records]):
            row = records.get(key)
            if row is None:
                continue
            details = youtube_pipeline.public(video_jobs[key]) if key in video_jobs else describe(row['kind'], key)
            public = {**row, **details}
            if key in active:
                public['status'] = 'running'
            elif key in keys:
                public['status'] = 'queued'
            elif public['status'] in ('queued', 'running'):
                public['status'] = 'preparing'
            if allowed(public, profile):
                jobs.append(public)
        jobs.extend({'id': row['id'], 'kind': row['kind'], 'type': row['type'], **youtube_pipeline.public(row)}
                    for row in video_jobs.values() if row['id'] not in records)
        jobs.extend(row for row in history if row['id'] not in records and row['kind'] not in ('youtube', 'youtube-track') and allowed(row, profile))
        from . import videos
        if videos.running() and not any(job['kind'] == 'youtube-track' and job['status'] == 'running' for job in jobs):
            lanes['local']['running'] = True
            report = videos.status()
            jobs.append({'id': 'video-index', 'kind': 'video-index', 'type': 'Indexation vidéo',
                         'title': 'Titres et sous-titres', 'status': 'running',
                         'stage': f"{report.get('videos', 0)} vidéo(s) traitée(s)"})
        for job in jobs:
            job['lane'] = BACKGROUND_LANE.get(job['kind'], 'ai')
            job.setdefault('priority', job['kind'] == 'chat')
            lane_order = orders[job['lane']]
            job['next'] = bool(lane_order and lane_order[0] == job['id'])
            job['movable'] = job['id'] in keys and can_move(job, profile)
            job['retry'] = job['status'] in ('paused', 'error', 'stopped', 'interrupted') and (
                job['kind'] in ('translation', 'summary') or profile['role'] == 'admin' and
                job['kind'] in ('youtube','youtube-track','captions','speech','acquisition','translation-test'))
        return {'paused': self.paused, 'running': any(lane['running'] for lane in lanes.values()), 'lanes': lanes, 'jobs': [
            {key: value for key, value in job.items() if key != 'owner'} for job in jobs
        ]}


QUEUE = Queue()


def allowed(row, profile):
    # Conversation and document titles belong to their profile.
    return row.get('owner') in (None, profile['id'])


def can_move(row, profile):
    return allowed(row, profile) and (profile['role'] == 'admin' or row.get('owner') == profile['id'])


def tracked(kind):
    def decorate(worker):
        @wraps(worker)
        async def run(*args, **kwargs):
            job = args[0] if args else kwargs.get('identifier', kwargs.get('report'))
            identifier = job if isinstance(job, str) else job.get('id') or job.get('job_id') or kind
            initial = describe(kind, identifier)
            if isinstance(job, dict):
                initial.update({key: job[key] for key in ('model', 'mode') if key in job})
            record = {'id': identifier, 'kind': kind, 'type': KINDS[kind], **initial}
            if kind == 'chat':
                # Performance trials delegate to the response engine too.
                record['priority'] = CURRENT.get() not in QUEUE.records
            QUEUE.records[identifier] = record
            persisted_elsewhere = kind in ('youtube', 'youtube-track')
            try:
                if not persisted_elsewhere:
                    QUEUE.save({**record, 'status': 'interrupted'})
            except (OSError, sqlite3.Error):
                logging.getLogger(__name__).warning('Historique de la file indisponible')
            token = CURRENT.set(identifier)
            try:
                return await worker(*args, **kwargs)
            finally:
                CURRENT.reset(token)
                try:
                    if not persisted_elsewhere:
                        final = describe(kind, identifier)
                        if final['status'] in ('queued', 'running', 'preparing'):
                            final['status'] = 'interrupted'
                        QUEUE.save({**record, **final})
                except Exception:
                    logging.getLogger(__name__).exception('Historique de la file indisponible')
                finally:
                    QUEUE.records.pop(identifier, None)
        return run
    return decorate


def describe(kind, identifier):
    from . import engine

    result = {'status': 'queued', 'title': KINDS[kind]}
    try:
        if kind in ('chat', 'translation', 'summary'):
            with store.connect() as db:
                if kind == 'chat':
                    row = db.execute('''SELECT j.status,j.mode,j.error,j.user_id,j.conversation_id,j.created,c.title
                        FROM jobs j JOIN conversations c ON c.id=j.conversation_id WHERE j.id=?''', (identifier,)).fetchone()
                    if row:
                        question = db.execute("SELECT content FROM messages WHERE conversation_id=? AND role='user' AND created<=? ORDER BY id DESC LIMIT 1",
                                              (row['conversation_id'], row['created'])).fetchone()
                        result['title'] = question[0][:180] if question else row['title']
                        result['href'] = '#/assistant?conversation=' + row['conversation_id']
                elif kind == 'summary':
                    row = db.execute('SELECT status,mode,error,user_id,conversation_id,question AS title FROM summary_jobs WHERE id=?', (identifier,)).fetchone()
                else:
                    row = db.execute('SELECT status,mode,error,user_id,conversation_id,title FROM translations WHERE id=?', (identifier,)).fetchone()
                    progress = db.execute("SELECT sum(status='done'),count(*) FROM translation_parts WHERE translation_id=?", (identifier,)).fetchone()
                    result.update(done=progress[0] or 0, total=progress[1])
                if row:
                    result.update(status=row['status'], mode=row['mode'], error=row['error'], owner=row['user_id'])
                    if kind == 'chat':
                        stage = engine.PROGRESS.get(identifier, {}).get('stage')
                        phase = {'preparing':'Préparation de la demande','searching':'Recherche dans la bibliothèque',
                                 'reading':'Lecture des documents','writing':'Rédaction de la réponse',
                                 'illustrating':'Recherche d’illustrations','referencing':'Vérification des références'}.get(stage)
                        if phase:
                            result['stage'] = phase
                    result.setdefault('href', '#/assistant?conversation=' + row['conversation_id'])
                    if kind != 'chat':
                        result['title'] = row['title'][:180]
                else:
                    # Deleted or unavailable private jobs never become public.
                    result['owner'] = ''
        elif kind in ('captions', 'speech', 'acquisition'):
            from . import captions, transcriptions, caption_acquisition
            module = {'captions': captions, 'speech': transcriptions, 'acquisition': caption_acquisition}[kind]
            row = module.get(identifier)
            result.update({key: row[key] for key in ('status', 'title', 'mode', 'error') if key in row})
            result['href'] = '#/bibliotheque/recherche?source=' + row['video_id']
            if kind == 'captions':
                with module.connect() as db:
                    count = db.execute("SELECT sum(status='done'),count(*) FROM parts WHERE job_id=?", (identifier,)).fetchone()
                result.update(done=count[0] or 0, total=count[1])
            elif kind == 'speech':
                probe = json.loads(row['probe']) if row['probe'] else {}
                result.update(model='Whisper small · CPU', done=row['progress_ms'], total=probe.get('duration_ms'))
            else:
                result['model'] = 'YouTube'
        elif kind in ('youtube', 'youtube-track'):
            from . import youtube_pipeline
            result.update(youtube_pipeline.details(identifier))
        else:
            from . import calibration, performance, search_experiment, translation_benchmark
            module = {'calibration': calibration, 'performance': performance, 'search-test': search_experiment,
                      'translation-test': translation_benchmark}[kind]
            data = module.status()
            result.update({key: data[key] for key in ('status', 'mode', 'model', 'error') if key in data})
        if not result.get('model') and result.get('mode') in engine.MODES:
            result['model'] = engine.MODES[result['mode']]['model']
    except (HTTPException, OSError, ValueError, sqlite3.Error):
        if kind in ('chat', 'translation', 'summary'):
            result['owner'] = ''
    return result


async def retry(identifier, profile):
    from . import caption_acquisition, captions, summaries, transcriptions, translation_benchmark, translations, youtube_pipeline

    with store.connect() as db:
        row = db.execute('SELECT data FROM work_history WHERE id=?', (identifier,)).fetchone()
    record = json.loads(row[0]) if row else None
    if profile['role'] == 'admin':
        try:
            youtube_pipeline.read(identifier)
        except HTTPException as error:
            if error.status_code != 404:
                raise
        else:
            await youtube_pipeline.retry(identifier)
            return
    if not record or not allowed(record, profile):
        raise HTTPException(404, 'Travail introuvable.')
    kind = record['kind']
    if kind in ('translation', 'summary'):
        module = translations if kind == 'translation' else summaries
        await module.resume(identifier, profile['id'])
        return
    if profile['role'] == 'admin':
        if kind == 'translation-test':
            await translation_benchmark.resume()
            return
        module = {'speech': transcriptions, 'captions': captions, 'acquisition': caption_acquisition}.get(kind)
        if module:
            await module.resume(identifier)
            return
    raise HTTPException(409, 'Ouvrez le travail d’origine pour le relancer.')
