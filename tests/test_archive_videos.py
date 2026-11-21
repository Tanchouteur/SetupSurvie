"""Actual tiny ZIM to checked tracks, shared index and documentary source."""
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock,patch
import httpx
from fastapi import HTTPException
from pilot import app as gateway,archive_videos,captions,engine,operations,store,videos,retrieval,library,zim_video_inventory
import test_zim_video_inventory as fixtures


@unittest.skipUnless(fixtures.HAS_ZIM,'Optional libzim reader required')
class ArchiveVideoIndexTests(unittest.TestCase):
    setUp_archive=fixtures.ArchiveVideoTests.setUp
    create=fixtures.ArchiveVideoTests.create

    def setUp(self):
        self.setUp_archive()
        for module,name,value in ((store,'ROOT',self.root/'pilot'),(archive_videos,'ZIMS',self.root),(videos,'ROOT',self.root/'video')):
            change=patch.object(module,name,value);change.start();self.addCleanup(change.stop)
        store.init();videos.ROOT.mkdir();videos.STOP.clear();self.report=zim_video_inventory.build(self.zim,archive_videos.directory())

    def test_archive_tracks_join_existing_search_source_and_webvtt_without_libzim_in_reader(self):
        report=videos.scan();self.assertEqual(report['phase'],'completed',report);self.assertEqual(report['videos'],2);self.assertEqual(report['tracks'],1)
        listing=videos.listing();self.assertEqual(listing['total'],2)
        video=next(item for item in listing['videos'] if item['tracks']);self.assertTrue(video['archive_video']);self.assertEqual(video['archive_article'],'zim:fixture/A/course.html')
        plan=retrieval.plan('Fictional bearing 17 mm',['fictional','17'],library.SYNONYMS)
        found,_=videos.search(plan);self.assertTrue(found);source=videos.source(found[0]['id'])
        self.assertTrue(source['transcription_available']);self.assertIn('Fictional 17 mm.',source['text']);self.assertEqual(source['position_ms'],1000)
        self.assertIn('00:00:01.000 --> 00:00:02.000',videos.webvtt(video['id'].split(':')[1],0))
        self.assertFalse(source['audio_verified']);self.assertEqual(source['human_review'],'not_performed')

    def test_local_filter_keeps_only_files_from_the_video_folder(self):
        from zim_video_fixture import create
        youtube=self.root/'youtube-fixture.zim'
        create(youtube,youtube=True,with_tracks=False)
        zim_video_inventory.build(youtube,archive_videos.directory())
        (videos.ROOT/'local.mp4').write_bytes(b'local fixture')
        (videos.ROOT/'youtube').mkdir()
        (videos.ROOT/'youtube'/'download.mp4').write_bytes(b'download fixture')
        videos.scan()

        self.assertEqual(videos.listing()['total'],8)
        local=videos.listing(origin='local')
        self.assertEqual(sorted(videos.row(item['id'])[1]['path'] for item in local['videos']),
                         ['local.mp4','youtube/download.mp4'])
        grouped=videos.listing(grouped=True,origin='local')
        self.assertEqual(grouped['total'],2)
        self.assertEqual(videos.listing(grouped=True,origin='local',query='shadow')['total'],0)
        self.assertEqual(videos.listing(grouped=True,origin='local',query='download')['total'],1)

    def test_published_archive_is_searchable_before_the_host_inventory_finishes(self):
        from zim_video_fixture import create

        async def scenario():
            directory = archive_videos.directory()
            progress = directory/'progress.json'
            host = {'schema': 1, 'job_id': 'batch', 'phase': 'running', 'archives': 3,
                    'results': [self.report]}
            progress.write_text(json.dumps(host), encoding='utf-8')
            self.assertEqual(videos.scan()['videos'], 2)
            self.assertFalse(videos.stale())
            query = retrieval.plan('measure a shadow', ['measure', 'shadow'], library.SYNONYMS)
            self.assertFalse(videos.search(query)[0])

            (directory/'aaaaaaaaaaaaaaaaaaaaaaaa.building').write_bytes(b'incomplete fixture')
            self.assertFalse(videos.stale())
            second = self.root/'youtube-fixture.zim'
            create(second, youtube=True, with_tracks=False)
            host['results'].append(zim_video_inventory.build(second, directory))
            progress.write_text(json.dumps(host), encoding='utf-8')
            self.assertTrue(videos.stale())

            with patch.object(videos, 'ACTIVE', None), patch.object(videos, 'CHECKED', 0.0):
                self.assertEqual(await videos.ensure_fresh(force=True), 'refreshing')
                report = await asyncio.wait_for(videos.ACTIVE, 5)
            self.assertEqual(report['videos'], 6)
            self.assertFalse(videos.stale())
            self.assertEqual(archive_videos.progress()['phase'], 'running')
            self.assertFalse(archive_videos.state()['reader_ready'])
            self.assertEqual(videos.listing()['total'], 6)
            found, coverage = videos.search(query)
            self.assertEqual(found[0]['title'], 'How do we measure a shadow?')
            self.assertEqual(coverage['status'], 'partial')

        asyncio.run(scenario())

    def test_youtube_subtitles_already_in_the_zim_join_search_after_reusing_the_inventory(self):
        from zim_video_fixture import create

        youtube = self.root/'youtube-with-subtitles.zim'
        create(youtube, youtube=True, youtube_tracks=True, with_tracks=False)
        with patch.object(zim_video_inventory, 'save_youtube_metadata'):
            zim_video_inventory.build(youtube, archive_videos.directory())
        videos.scan()
        query = retrieval.plan('règle graduée', ['regle', 'graduee'], library.SYNONYMS)
        self.assertFalse(videos.search(query, 'fr')[0])

        upgraded = zim_video_inventory.build(youtube, archive_videos.directory())
        self.assertEqual(upgraded['status'], 'reused')
        self.assertTrue(videos.stale())
        self.assertEqual(videos.scan()['phase'], 'completed')

        found, _ = videos.search(query, 'fr')
        self.assertEqual(len(found), 1)
        source = videos.source(found[0]['id'])
        self.assertEqual(source['title'], 'How do we measure a shadow?')
        self.assertEqual(source['position_ms'], 1000)
        self.assertIn('règle graduée fictive', source['text'])
        self.assertEqual(source['subtitle_status'], 'french_available')
        self.assertEqual(len(source['tracks']), 1)

    def test_archive_replacement_invalidates_reading_and_missing_cache_is_not_an_empty_success(self):
        videos.scan();video=next(item for item in videos.listing()['videos'] if item['tracks']);_,payload,_=videos.row(video['id'])
        cache=videos.track_file(payload['tracks'][0]);cache.unlink()
        with self.assertRaises(HTTPException):videos.source(video['id'])
        self.create(extra=True);self.assertEqual(list(archive_videos.items()),[])
        with self.assertRaises(HTTPException):videos.source(video['id'])

    def test_reused_archive_repairs_missing_track_and_index_refresh_does_not_claim_bad_cache_ready(self):
        videos.scan();video=next(item for item in videos.listing()['videos'] if item['tracks']);_,payload,_=videos.row(video['id'])
        cache=videos.track_file(payload['tracks'][0]);cache.unlink();errors=[]
        stale=next(item for item in archive_videos.items(errors) if item['tracks'])
        self.assertEqual(stale['subtitle_status'],'invalid');self.assertTrue(errors)
        self.assertEqual(zim_video_inventory.build(self.zim,archive_videos.directory())['status'],'reused')
        videos.scan();self.assertIn('Fictional 17 mm.',videos.source(video['id'])['text'])

    def test_french_preparation_of_internal_track_keeps_native_media_and_timestamps(self):
        async def scenario():
            with patch.object(videos,'ACTIVE',None),patch.object(captions,'ACTIVE',{}),patch.object(engine,'LOCK',asyncio.Semaphore(1)),\
                 patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':False})),\
                 patch.object(captions,'translate_batch',AsyncMock(return_value=([{'id':0,'text':'Texte fictif : 17 mm.'}],'fixture',{}))):
                videos.scan();video=next(item for item in videos.listing()['videos'] if item['tracks']);before=self.zim.read_bytes()
                try:
                    job=await captions.create(video['id'],0,'rapide');await asyncio.wait_for(captions.ACTIVE[job['id']],5)
                    if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,5)
                    self.assertEqual(captions.status(job['id'])['status'],'completed')
                    value=videos.source(video['id']);self.assertEqual(value['language'],'fr');self.assertIn('Texte fictif',value['text'])
                    self.assertEqual(value['subtitle_status'],'french_prepared')
                    fr=next(track for track in value['tracks'] if track['language']=='fr')
                    self.assertIn('00:00:01.000 --> 00:00:02.000',videos.webvtt(video['id'].split(':')[1],fr['id']))
                    plan=retrieval.plan('Texte fictif',['fictif'],library.SYNONYMS);found,_=videos.search(plan,'fr');self.assertTrue(found)
                    self.assertEqual(self.zim.read_bytes(),before)
                finally:await captions.stop_all();await videos.stop()
        asyncio.run(scenario())


class ArchiveVideoLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def test_legacy_report_excludes_unfinished_collections_from_examined_count(self):
        with TemporaryDirectory() as folder,patch.object(store,'ROOT',Path(folder)):
            directory=archive_videos.directory()
            directory.mkdir()
            report={'schema':1,'phase':'paused','completed':4,'archives':4,'results':[
                {'status':'reused'},{'status':'partial'},{'status':'paused'},{'status':'error'},
            ]}
            (directory/'progress.json').write_text(json.dumps(report),encoding='utf-8')
            result=archive_videos.progress()
            self.assertEqual((result['completed'],result['archives'],result['phase']),(2,4,'paused'))

    async def test_host_start_failure_and_queue_are_not_hidden_by_an_old_finished_inventory(self):
        previous={'phase':'completed','job_id':'old','reader_ready':True,'reader_updating':False}
        host={'action':'video-inventory','id':'new','phase':'starting'}
        with patch.object(archive_videos,'state',return_value=previous),patch.object(operations,'library_command',AsyncMock(return_value=host)):
            self.assertEqual((await archive_videos.status())['phase'],'preparing')
            host['phase']='error';value=await archive_videos.status();self.assertEqual(value['phase'],'error');self.assertFalse(value['reader_ready'])
            with patch.object(operations,'library_command',AsyncMock(side_effect=HTTPException(503,'offline'))):
                value=await archive_videos.status();self.assertEqual(value['phase'],'completed');self.assertIn('control_notice',value)
    async def test_previous_scan_cannot_mark_a_new_or_running_archive_inventory_ready(self):
        saved={'phase':'completed','job_id':'new','finished':20}
        reader={'phase':'completed','archive_inventory_job':'new','archive_inventory_finished':19}
        with patch.object(archive_videos,'progress',return_value=saved),patch.object(videos,'status',return_value=reader):
            self.assertFalse(archive_videos.state()['reader_ready']);reader['archive_inventory_finished']=20
            self.assertTrue(archive_videos.state()['reader_ready']);saved['phase']='running'
            self.assertFalse(archive_videos.state()['reader_ready'])
    async def test_completed_native_job_refreshes_reader_even_when_previous_scan_was_busy(self):
        previous=asyncio.create_task(asyncio.sleep(0))
        with patch.object(archive_videos,'progress',return_value={'job_id':'fixture','phase':'completed'}),\
             patch.object(videos,'ACTIVE',previous),patch.object(videos,'start',AsyncMock(side_effect=[HTTPException(409,'Busy'),{}])) as refresh:
            await archive_videos.follow('fixture');self.assertEqual(refresh.await_count,2)

    async def test_paused_inventory_does_not_restart_reader_or_inference(self):
        with patch.object(archive_videos,'progress',return_value={'job_id':'fixture','phase':'paused'}),patch.object(videos,'start',AsyncMock()) as refresh:
            await archive_videos.follow('fixture');refresh.assert_not_called()

    async def test_reader_can_see_status_but_preparation_pause_and_report_are_admin_only(self):
        headers={'Origin':'http://test'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://test') as client:
            gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'reader','role':'reader'}
            try:
                with patch.object(archive_videos,'state',return_value={'phase':'not_started'}):
                    self.assertEqual((await client.get('/api/zim-videos')).status_code,200)
                self.assertEqual((await client.get('/api/admin/zim-videos/report')).status_code,403)
                for path in ('/api/admin/zim-videos/start','/api/admin/zim-videos/pause'):
                    self.assertEqual((await client.post(path,headers=headers)).status_code,403)
                gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'family','role':'admin'}
                with patch.object(archive_videos,'start',AsyncMock(return_value={'accepted':True})) as start:
                    self.assertEqual((await client.post('/api/admin/zim-videos/start',headers=headers)).status_code,202);start.assert_awaited_once()
                with patch.object(operations,'library_command',AsyncMock(return_value={'phase':'paused'})) as pause:
                    self.assertEqual((await client.post('/api/admin/zim-videos/pause',headers=headers)).status_code,202)
                    pause.assert_awaited_once_with('video-inventory-pause',{})
            finally:gateway.app.dependency_overrides.clear()
