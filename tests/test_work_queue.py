"""Real queue, SQLite and media search with a simulated YouTube host and models."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from pilot import engine, library, operations, store, videos, work_queue, youtube_pipeline
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
            queue.records[identifier] = {'id': identifier, 'kind': 'youtube', 'title': identifier, 'status': 'queued', 'owner': owner}
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
