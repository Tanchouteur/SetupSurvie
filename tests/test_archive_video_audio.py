"""Real tiny archive identity/index, simulated ASR/translation, no model."""
import asyncio
from unittest.mock import AsyncMock,patch
import unittest
from pilot import archive_videos,captions,engine,library,operations,store,transcriptions as speech,videos,zim_video_inventory
import test_zim_video_inventory as fixtures


@unittest.skipUnless(fixtures.HAS_ZIM,'Optional libzim reader required')
class ArchiveAudioTests(unittest.IsolatedAsyncioTestCase):
    create=fixtures.ArchiveVideoTests.create

    async def asyncSetUp(self):
        fixtures.ArchiveVideoTests.setUp(self);self.calls=[];self.gate=None;self.waiting=asyncio.Event();self.audio=True;self.closed=0
        for module,name,value in ((store,'ROOT',self.root/'pilot'),(archive_videos,'ZIMS',self.root),(videos,'ROOT',self.root/'video'),
                                  (videos,'ACTIVE',None),(speech,'ACTIVE',{}),(captions,'ACTIVE',{}),(engine,'LOCK',asyncio.Semaphore(1))):
            change=patch.object(module,name,value);change.start();self.addCleanup(change.stop)
        store.init();videos.ROOT.mkdir();videos.STOP.clear();zim_video_inventory.build(self.zim,archive_videos.directory());videos.scan()
        self.video=next(item for item in videos.listing()['videos'] if not item['tracks'])['id']
        changes=[patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':False})),
            patch.object(speech,'model_config',return_value={'available':True,'model_path':'/fixture/model','model':{},'runtime':{},'device':'cpu','compute_type':'int8','threads':2})]
        test=self
        class Worker:
            async def call(self,command):
                test.calls.append(command)
                if command['action']=='probe':return {'audio_present':test.audio,'duration_ms':61000}
                start=command['start_ms']
                if start and test.gate:test.waiting.set();await test.gate.wait()
                return {'cues':[{'start_ms':start+100,'end_ms':start+800,'text':f'Fictional bearing {17+start//60000} mm. Do not open.'}],
                    'language':'en','language_probability':.99,'eof':bool(start),'last_decoded_ms':61000 if start else 62000,'raw_segments':[],
                    'media_io':{'source':'kiwix_byte_ranges','http_requests':2,'media_bytes':200}}
            async def close(self):test.closed+=1
        changes.append(patch.object(speech,'Worker',Worker))
        async def translate(parts,mode):return [{'id':row['position'],'text':f'Roulement fictif {17+row["position"]} mm. Ne pas ouvrir.'} for row in parts],'fixture',{}
        changes.append(patch.object(captions,'translate_batch',translate))
        for change in changes:change.start();self.addCleanup(change.stop)

    async def asyncTearDown(self):
        await speech.stop_all();await captions.stop_all();await videos.stop()

    async def finish(self,job):
        if task:=speech.ACTIVE.get(job['id']):await asyncio.wait_for(task,6)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,6)
        result=speech.status(job['id'],True)
        if result['translation_job']:
            if task:=captions.ACTIVE.get(result['translation_job']):await asyncio.wait_for(task,6)
            if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,6)
        return result

    async def test_archive_audio_and_french_track_join_existing_reader_search_without_extracting_media(self):
        before=self.zim.read_bytes();job=await speech.create(self.video,'en','rapide',True);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result);self.assertEqual(result['units_done'],2)
        self.assertEqual(result['units'][0]['media_io']['media_bytes'],200);self.assertTrue(result['translation_job'])
        source=videos.source(self.video);self.assertEqual(source['language'],'fr');self.assertIn('Ne pas ouvrir',source['text'])
        self.assertEqual({track['origin'] for track in source['tracks']},{'local_transcription','local_translation'})
        plan=library.retrieval.plan('roulement',library.search_terms('roulement'),library.SYNONYMS)
        self.assertTrue(videos.search(plan,'fr')[0]);self.assertEqual(self.zim.read_bytes(),before);self.assertEqual(list(videos.ROOT.iterdir()),[])
        self.assertTrue(all('archive' in command and 'path' not in command for command in self.calls));self.assertEqual(self.closed,1)

    async def test_pause_keeps_finished_unit_and_resume_does_not_repeat_it(self):
        self.gate=asyncio.Event();job=await speech.create(self.video,'en',translate_french=False);await asyncio.wait_for(self.waiting.wait(),5)
        paused=await speech.pause(job['id']);self.assertEqual(paused['units_done'],1);self.assertEqual(paused['progress_ms'],60000)
        self.assertFalse(speech.track_file(job['id']).exists());self.gate=None
        result=await self.finish(await speech.resume(job['id']));self.assertEqual(result['status'],'completed');self.assertEqual(result['units_done'],2)
        self.assertEqual(sum(command.get('start_ms')==0 for command in self.calls),1)

    async def test_replaced_archive_does_not_publish_a_track_for_the_previous_edition(self):
        self.gate=asyncio.Event();job=await speech.create(self.video,'en',translate_french=False);await asyncio.wait_for(self.waiting.wait(),5)
        self.create(extra=True);self.gate.set();result=await self.finish(job)
        self.assertEqual(result['status'],'error');self.assertEqual(result['units_done'],1);self.assertFalse(speech.track_file(job['id']).exists())

    async def test_missing_audio_is_reported_without_invoking_recognition_or_inventing_a_track(self):
        self.audio=False;result=await self.finish(await speech.create(self.video,'en',translate_french=False))
        self.assertEqual(result['status'],'error');self.assertIn('piste audio',result['error']);self.assertEqual(len(self.calls),1)
        self.assertFalse(speech.track_file(result['id']).exists())

    async def test_only_configured_reader_can_enter_the_private_descriptor(self):
        _,payload,_=videos.row(self.video);payload['endpoint']='https://external.invalid';payload['url']='https://external.invalid/media'
        with patch.object(library,'KIWIX','http://kiwix:8080'):
            source=archive_videos.audio_source(payload)
        self.assertEqual(source['endpoint'],'http://kiwix:8080');self.assertEqual(source['book'],'fixture')
        self.assertEqual(source['uuid'],payload['archive_revision']['uuid']);self.assertNotIn('url',source)
