"""Real queue, SQLite and media search with a simulated YouTube host and models."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from pilot import archive_videos, engine, library, operations, store, videos, work_queue, youtube_pipeline
import test_video_transcriptions as speech_fixture

ADMIN = {'id': 'famille', 'role': 'admin'}
CHILD = {'id': 'enfant', 'role': 'user'}


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        state = patch.object(store, 'ROOT', Path(temporary.name))
        state.start()
        self.addCleanup(state.stop)
        store.init()
        self.queue = work_queue.Queue()
        self.queue.initialize()

    async def test_host_preparations_use_the_same_cards_without_queue_controls(self):
        report = {'kind': 'download', 'phase': 'verifying', 'source': 'windows',
                  'total_bytes': 2000, 'verified_bytes': 1000,
                  'active': [{'title': 'Collection fictive', 'phase': 'verifying'}]}
        jobs = self.queue.snapshot(CHILD, report)['jobs']
        transfer = next(job for job in jobs if job['id'] == 'host:download')
        self.assertEqual((transfer['lane'], transfer['status']), ('network', 'running'))
        self.assertEqual(transfer['preparation']['verified_bytes'], 1000)
        self.assertFalse(transfer['movable'] or transfer['retry'])

        report = {'kind': 'video-inventory', 'phase': 'paused', 'observed_at': 123}
        with patch.object(archive_videos, 'progress', return_value={'phase': 'paused'}):
            jobs = self.queue.snapshot(ADMIN, report)['jobs']
        inventory = [job for job in jobs if job['kind'] in ('archive-video-index', 'host-video-inventory')]
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]['preparation']['observed_at'], 123)

    async def test_priority_pause_running_slot_and_error_isolation(self):
        queue = self.queue
        observed = []
        finish = asyncio.Event()

        async def execute(identifier):
            token = work_queue.CURRENT.set(identifier)
            try:
                async with queue:
                    observed.append(identifier)
                    if identifier == 'active':
                        await finish.wait()
                    elif identifier == 'bad':
                        raise RuntimeError('Fixture')
            finally:
                work_queue.CURRENT.reset(token)

        for identifier, owner in [('active', None), ('bad', 'famille'), ('child', 'enfant'), ('last', None)]:
            queue.records[identifier] = {'id': identifier, 'kind': 'translation', 'title': identifier, 'status': 'queued', 'owner': owner}
        tasks = [asyncio.create_task(execute(identifier)) for identifier in queue.records]
        await asyncio.sleep(0)
        self.assertEqual(observed, ['active'])
        queue.set_paused(True)
        with self.assertRaises(HTTPException):
            queue.move('active', 1, ADMIN)
        with self.assertRaises(HTTPException):
            queue.move('last', -1, CHILD)
        queue.move('last', -1, ADMIN)
        finish.set()
        await tasks[0]
        self.assertEqual(observed, ['active'])
        restarted = work_queue.Queue()
        restarted.initialize()
        self.assertTrue(restarted.paused)
        queue.set_paused(False)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.assertIsInstance(results[1], RuntimeError)
        self.assertEqual(observed, ['active', 'last', 'child', 'bad'])
        self.assertFalse(queue.locked())

    async def test_questions_get_next_ai_slot_with_video_work_in_parallel(self):
        queue = self.queue
        observed = []
        release_ai = asyncio.Event()
        release_background = asyncio.Event()

        async def run(identifier, gate=None):
            token = work_queue.CURRENT.set(identifier)
            kind = queue.records[identifier]['kind']
            try:
                async with queue.slots[work_queue.BACKGROUND_LANE.get(kind, 'ai')]:
                    observed.append(identifier)
                    if gate:
                        await gate.wait()
            finally:
                work_queue.CURRENT.reset(token)

        jobs = [('initial', 'translation'), ('background', 'translation'),
                ('q1', 'chat'), ('q2', 'chat'), ('q3', 'chat'), ('q4', 'chat'),
                ('download', 'youtube'), ('speech', 'speech')]
        for identifier, kind in jobs:
            queue.records[identifier] = {'id': identifier, 'kind': kind, 'owner': 'famille',
                                         'title': identifier, 'status': 'queued'}
        first = asyncio.create_task(run('initial', release_ai))
        await asyncio.sleep(0)
        tasks = [asyncio.create_task(run(identifier, release_background if identifier in ('download','speech') else None))
                 for identifier, _ in jobs[1:]]
        await asyncio.sleep(0)
        self.assertEqual(observed, ['initial', 'download', 'speech'])
        self.assertEqual(queue.order(), ['q1', 'q2', 'q3', 'background', 'q4'])
        self.assertEqual(queue.waiting_state('q1'), 'next')
        self.assertEqual(queue.waiting_state('q2'), 'waiting')
        queue.set_paused(True)
        self.assertEqual(queue.waiting_state('q1'), 'paused')
        queue.set_paused(False)
        with self.assertRaises(HTTPException):
            queue.move('background', -1, ADMIN)
        release_ai.set()
        await first
        await asyncio.wait_for(asyncio.gather(*tasks[:-2]), 2)
        self.assertEqual(observed[3:], ['q1', 'q2', 'q3', 'background', 'q4'])
        self.assertFalse(queue.locked())
        self.assertTrue(queue.slots['network'].locked())
        self.assertTrue(queue.slots['local'].locked())
        queue.set_paused(True)
        release_background.set()
        await asyncio.gather(*tasks[-2:])

    async def test_cancelled_head_releases_the_slot_to_other_jobs(self):
        queue = self.queue
        await queue.acquire()
        waiter = asyncio.create_task(queue.acquire())
        following = asyncio.create_task(queue.acquire())
        await asyncio.sleep(0)
        waiter.cancel()
        queue.release()
        await asyncio.gather(waiter, return_exceptions=True)
        await asyncio.wait_for(following, 1)
        queue.release()
        self.assertFalse(queue.locked())

    async def test_drop_moves_only_visible_waiters_in_the_same_priority_group(self):
        queue = self.queue
        queue.set_paused(True)
        for key, kind, owner in [('first', 'translation', 'famille'), ('private', 'translation', 'enfant'),
                                 ('second', 'translation', 'famille'), ('question', 'chat', 'famille'),
                                 ('last', 'translation', 'famille')]:
            queue.records[key] = {'kind': kind, 'owner': owner}
            queue.waiters.append((key, asyncio.get_running_loop().create_future()))
        with self.assertRaises(HTTPException):
            queue.move('last', None, ADMIN, target='private')
        with self.assertRaises(HTTPException):
            queue.move('last', None, ADMIN, target='question')
        queue.move('last', None, ADMIN, target='first')
        self.assertEqual([key for key, _ in queue.waiters], ['last', 'private', 'first', 'question', 'second'])
        queue.move('last', None, ADMIN, target='second', after=True)
        self.assertEqual([key for key, _ in queue.waiters], ['first', 'private', 'second', 'question', 'last'])

    async def test_both_video_inventories_remain_visible_during_track_preparation(self):
        queue = self.queue
        track = {'id': 'track', 'kind': 'youtube-track', 'title': 'Piste', 'status': 'running'}
        queue.records['track'] = track
        queue.slots['local'].active = ('track', None)
        with (patch.object(videos, 'running', return_value=object()),
              patch.object(videos, 'status', return_value={'phase': 'running', 'videos': 3}),
              patch.object(archive_videos, 'progress', return_value={'phase': 'running', 'completed': 2, 'archives': 5}),
              patch.object(work_queue, 'describe', return_value=track)):
            value = queue.snapshot(ADMIN)
        active = {job['id']: job for job in value['jobs'] if job['status'] == 'running'}
        self.assertEqual(set(active), {'track', 'video-index', 'archive-video-index'})
        self.assertEqual((active['archive-video-index']['done'], active['archive-video-index']['total']), (2, 5))
        self.assertTrue(value['lanes']['local']['running'])
        self.assertTrue(all(job['lane'] == 'local' and not job['movable'] for job in active.values()))

    async def test_failed_video_index_is_visible_without_counting_as_running(self):
        report = {'phase': 'failed', 'error': 'L’ancien index reste disponible.', 'videos': 3}
        with patch.object(videos, 'ROOT', store.ROOT), patch.object(videos, 'status', return_value=report):
            value = self.queue.snapshot(ADMIN)
        self.assertFalse(value['lanes']['local']['running'])
        index = next(job for job in value['jobs'] if job['id'] == 'video-index')
        self.assertEqual((index['lane'], index['status'], index['error']), ('local', 'failed', report['error']))

    async def test_summary_hides_other_profile_content_but_reports_activity(self):
        queue = self.queue
        queue.save({'id': 'own', 'owner': 'enfant', 'kind': 'chat', 'title': 'Question enfant', 'status': 'done'})
        queue.save({'id': 'private', 'owner': 'famille', 'kind': 'translation', 'title': 'Document privé', 'status': 'error'})
        queue.save({'id': 'shared', 'owner': None, 'kind': 'captions', 'title': 'Vidéo familiale', 'status': 'error'})
        await queue.acquire()
        try:
            value = queue.snapshot(CHILD)
            self.assertTrue(value['running'])
            self.assertEqual([job['id'] for job in value['jobs']], ['shared', 'own'])
            self.assertFalse(value['jobs'][0]['retry'])
        finally:
            queue.release()


class YoutubePipelineTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = speech_fixture.VideoTranscriptionTests.asyncSetUp
    asyncTearDown = speech_fixture.VideoTranscriptionTests.asyncTearDown

    async def test_batch_reattaches_to_host_and_indexes_english_and_translated_words(self):
        youtube_pipeline.initialize()
        queue = work_queue.Queue()
        queue.initialize()
        with patch.object(engine, 'LOCK', queue), patch.object(work_queue, 'QUEUE', queue), \
             patch.object(youtube_pipeline, 'launch'):
            batch = await youtube_pipeline.submit('https://youtu.be/aaaaaaaaaaa\nhttps://youtu.be/bbbbbbbbbbb', 480)
            identifier = batch['job']
            item = {'line': 1, 'id': 'aaaaaaaaaaa', 'path': 'rotor.mp4', 'title': 'Rotor fictif', 'status': 'downloaded'}
            failure = {'line': 2, 'id': 'bbbbbbbbbbb', 'status': 'error', 'reason': 'private', 'message': 'vidéo privée'}
            completion = {'phase': 'completed', 'action': 'youtube-download', 'youtube_list': identifier,
                          'message': 'Un téléchargement a échoué.',
                          'youtube': {'items': [item, failure], 'counts': {'downloaded': 1, 'error': 1}}}
            youtube_pipeline.update(identifier, submitted=True)
            with patch.object(operations, 'library_command', AsyncMock(return_value={'phase': 'idle'})) as host, \
                 patch.object(operations, 'youtube_result', AsyncMock(return_value=completion)):
                await youtube_pipeline.download(identifier)
                host.assert_awaited_once_with()
            self.assertEqual(youtube_pipeline.read(identifier)['status'], 'error')
            self.assertEqual(youtube_pipeline.details(identifier)['failures'], [failure])
            preparation = next(row for row in youtube_pipeline.listing() if row['kind'] == 'youtube-track')
            await asyncio.wait_for(youtube_pipeline.prepare(preparation['id']), 30)
            self.assertEqual(youtube_pipeline.read(preparation['id'])['status'], 'queued')
            await asyncio.wait_for(youtube_pipeline.prepare(preparation['id']), 30)
            self.assertEqual(youtube_pipeline.read(preparation['id'])['status'], 'completed')
            self.assertEqual({track['language'] for track in videos.source(self.video)['tracks']}, {'en', 'fr'})
            self.assertEqual(len(self.calls), 3)  # Probe and two known audio units.
            for term, language, expected in [('rotor fictif', '', 'title'),
                                               ('fictional', 'en', 'subtitle'), ('ouvrir', 'fr', 'subtitle')]:
                plan = library.retrieval.plan(term, library.search_terms(term), library.SYNONYMS)
                found, _ = videos.search(plan, language)
                self.assertTrue(any(row['id'].startswith(self.video) and row['match'] == expected for row in found), term)
            youtube_pipeline.observe(completion)
            self.assertEqual(youtube_pipeline.read(preparation['id'])['status'], 'completed')

    async def test_youtube_worker_does_not_hold_the_ai_slot(self):
        youtube_pipeline.initialize()
        queue = work_queue.Queue()
        queue.initialize()
        started, finish = asyncio.Event(), asyncio.Event()

        async def follow(*_):
            started.set()
            await finish.wait()

        with patch.object(engine, 'LOCK', queue), patch.object(work_queue, 'QUEUE', queue), \
             patch.object(operations, 'library_command', AsyncMock(return_value={'phase': 'idle'})), \
             patch.object(youtube_pipeline, 'follow', follow):
            try:
                batch = await youtube_pipeline.submit('https://youtu.be/aaaaaaaaaaa', 480)
                await asyncio.wait_for(started.wait(), 2)
                self.assertIn(batch['job'], youtube_pipeline.TASKS)
                await asyncio.wait_for(engine.LOCK.acquire(), 2)
                try:
                    value = queue.snapshot(ADMIN)
                    self.assertTrue(value['lanes']['ai']['running'])
                    self.assertTrue(value['lanes']['network']['running'])
                    download = next(job for job in value['jobs'] if job['id'] == batch['job'])
                    self.assertEqual((download['lane'], download['status']), ('network','running'))
                finally:
                    engine.LOCK.release()
            finally:
                finish.set()
                await youtube_pipeline.stop()

    async def test_backfill_only_registers_local_youtube_downloads(self):
        youtube_pipeline.initialize()
        report = {'per_video': [
            {'path':'youtube/Canal/exemple.mp4','title':'Exemple local','source':{'extractor':'Youtube'}},
            {'path':'autres/video.mp4','source':{'extractor':'Youtube'}},
            {'path':'youtube/video-sans-provenance.mp4','source':{}},
        ]}
        youtube_pipeline.register_indexed_youtube(report)
        youtube_pipeline.register_indexed_youtube(report)
        self.assertEqual([row['title'] for row in youtube_pipeline.listing()], ['Exemple local'])

    async def test_resume_does_not_start_a_report_already_completed_on_host(self):
        youtube_pipeline.initialize()
        with patch.object(youtube_pipeline, 'launch'), patch.object(engine, 'LOCK', work_queue.Queue()):
            batch = await youtube_pipeline.submit('https://youtu.be/aaaaaaaaaaa', 480)
            identifier = batch['job']
            youtube_pipeline.update(identifier, submitted=True)
            state = {'phase': 'completed', 'action': 'youtube-download', 'youtube_list': identifier, 'youtube': {}}
            with patch.object(operations, 'library_command', AsyncMock(return_value=state)) as host:
                await youtube_pipeline.download(identifier)
            host.assert_awaited_once_with()
            self.assertEqual(youtube_pipeline.read(identifier)['status'], 'completed')
