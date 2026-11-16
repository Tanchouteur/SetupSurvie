"""Durable audio workflow on tiny files; recognition is simulated, no model."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from pilot import captions,engine,operations,store,transcriptions as speech,videos


class VideoTranscriptionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.calls=[];self.closed=0;self.gate=None;self.entered=asyncio.Event();self.audio=True;self.empty=False
        self.first_eof=False;self.operations={'online':True,'paused':False};self.overlap=False
        def mock(module,key,value):
            change=patch.object(module,key,value);change.start();self.addCleanup(change.stop)
        for module,key,value in ((store,'ROOT',self.root/'state'),(videos,'ROOT',self.root/'video'),(videos,'ACTIVE',None),
                                  (speech,'ACTIVE',{}),(captions,'ACTIVE',{}),(engine,'LOCK',asyncio.Semaphore(1))):mock(module,key,value)
        videos.ROOT.mkdir();videos.STOP.clear();store.init()
        (videos.ROOT/'rotor.mp4').write_bytes(b'Fictional audio placeholder, no decoder in this test.')
        (videos.ROOT/'rotor.info.json').write_text(json.dumps({'title':'Rotor fictif','language':'en','duration':61}))
        videos.scan();self.video=videos.listing()['videos'][0]['id']
        mock(speech,'model_config',lambda:{'available':True,'model_path':'/fixture/model','model':{'repository':'fixture','revision':'pinned'},'runtime':{},'device':'cpu','compute_type':'int8','threads':2})
        mock(operations,'status',AsyncMock(side_effect=lambda **kw:self.operations))
        test=self
        class Worker:
            async def call(self,command):
                test.calls.append(command);test.entered.set()
                if command['action']=='probe':return {'audio_present':test.audio,'duration_ms':61000}
                if test.gate and command['start_ms']>=60000:await test.gate.wait()
                start=command['start_ms']
                cues=[] if test.empty else [{'start_ms':start+100,'end_ms':start+800,'text':'Fictional rotor '+str(start//60000+17)+' mm. Do not open.'}]
                if test.overlap:cues.append({'start_ms':start+700,'end_ms':start+900,'text':'Overlapping recognition.'})
                return {'cues':cues,
                    'language':'en','language_probability':.99,'eof':True if test.first_eof else start>0,'last_decoded_ms':61000 if start>0 or test.first_eof else 62000,
                    'warnings':[],'raw_segments':[]}
            async def close(self):test.closed+=1
        mock(speech,'Worker',Worker)
        async def translate(parts,mode):return [{'id':row['position'],'text':'Rotor fictif '+str(row['position']+17)+' mm. Ne pas ouvrir.'} for row in parts],'fixture-model',{}
        mock(captions,'translate_batch',translate)

    async def asyncTearDown(self):
        await speech.stop_all();await captions.stop_all();await videos.stop()

    async def finish(self,job):
        task=speech.ACTIVE.get(job['id'])
        if task:await asyncio.wait_for(task,5)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,5)
        return speech.status(job['id'],True)

    async def test_audio_source_and_french_track_reach_common_index_without_writing_mp4(self):
        before={p.name:p.read_bytes() for p in videos.ROOT.iterdir()}
        job=await speech.create(self.video,'en','rapide',True);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result);self.assertEqual(result['units_done'],2)
        self.assertEqual(result['progress_ms'],61000);self.assertEqual(result['cues'],2);self.assertTrue(result['translation_job'])
        task=captions.ACTIVE.get(result['translation_job'])
        if task:await asyncio.wait_for(task,5)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,5)
        source=videos.source(self.video)
        self.assertEqual({t['origin'] for t in source['tracks']},{'local_transcription','local_translation'})
        self.assertIn('Ne pas ouvrir',source['text']);self.assertEqual(source['language'],'fr')
        self.assertEqual(before,{p.name:p.read_bytes() for p in videos.ROOT.iterdir()});self.assertEqual(self.closed,1)
        self.assertEqual(result['human_review'],'not_performed')

    async def test_eof_inside_context_does_not_drop_words_after_unit_boundary(self):
        self.first_eof=True
        job=await speech.create(self.video,'en',translate_french=False);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result)
        starts=[call['start_ms'] for call in self.calls if call['action']=='transcribe']
        self.assertEqual(starts,[0,60000]);self.assertEqual(result['cues'],2)

    async def test_pause_and_resume_keep_finished_audio_units_but_publish_no_draft(self):
        self.gate=asyncio.Event();job=await speech.create(self.video,'en',translate_french=False)
        for _ in range(100):
            if any(c.get('start_ms')==60000 for c in self.calls):break
            await asyncio.sleep(.02)
        paused=await speech.pause(job['id']);self.assertEqual(paused['status'],'paused');self.assertEqual(paused['units_done'],1)
        self.assertEqual(videos.source(self.video)['tracks'],[]);self.assertEqual(self.closed,1)
        self.gate=None;await speech.resume(job['id']);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result);self.assertEqual(result['units_done'],2)
        self.assertEqual([c.get('start_ms') for c in self.calls if c['action']=='transcribe'],[0,60000,60000])

    async def test_no_audio_and_empty_recognition_do_not_publish_fake_subtitles(self):
        self.audio=False;job=await speech.create(self.video,'en',translate_french=False);result=await self.finish(job)
        self.assertEqual(result['status'],'error');self.assertIn('piste audio',result['error']);self.assertEqual(videos.source(self.video)['tracks'],[])
        self.audio=True;self.empty=True
        await speech.resume(job['id']);result=await self.finish(job)
        self.assertEqual(result['status'],'error');self.assertIn('Aucune parole',result['error']);self.assertEqual(videos.source(self.video)['tracks'],[])

    async def test_paused_engine_never_starts_worker_or_creates_job(self):
        self.operations['paused']=True
        with self.assertRaises(HTTPException) as raised:await speech.create(self.video)
        self.assertEqual(raised.exception.status_code,503);self.assertEqual(self.calls,[]);self.assertEqual(speech.listing(),[])

    async def test_rejected_recognition_stays_private_and_survives_a_successful_retry(self):
        self.overlap=True;job=await speech.create(self.video,'en',translate_french=False);result=await self.finish(job)
        self.assertEqual(result['status'],'error');self.assertEqual(result['units_done'],0)
        self.assertEqual(len(result['rejected_proposals']),1)
        self.assertEqual(len(result['rejected_proposals'][0]['result']['cues']),2)
        self.assertNotIn('rejected_proposals',speech.status(job['id']));self.assertEqual(videos.source(self.video)['tracks'],[])
        self.overlap=False;await speech.resume(job['id']);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result);self.assertEqual(len(result['rejected_proposals']),1)

    async def test_changed_original_prevents_resume(self):
        self.gate=asyncio.Event();job=await speech.create(self.video,'en',translate_french=False)
        for _ in range(100):
            if any(c.get('start_ms')==60000 for c in self.calls):break
            await asyncio.sleep(.02)
        await speech.pause(job['id']);(videos.ROOT/'rotor.mp4').write_bytes(b'Another source, old units must not be attached.')
        videos.scan()
        with self.assertRaises(HTTPException) as raised:await speech.resume(job['id'])
        self.assertEqual(raised.exception.status_code,409);self.assertEqual(speech.status(job['id'])['units_done'],1)

    async def test_completed_french_track_is_removed_if_recognized_source_is_changed(self):
        job=await speech.create(self.video,'en',translate_french=False);await self.finish(job)
        _,payload,_=videos.row(self.video);source_index=next(i for i,t in enumerate(payload['tracks']) if t.get('transcription_job'))
        translated=await captions.create(self.video,source_index,'rapide')
        task=captions.ACTIVE.get(translated['id'])
        if task:await asyncio.wait_for(task,5)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,5)
        self.assertEqual(videos.source(self.video)['language'],'fr')
        speech.track_file(job['id']).write_text('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nChanged speech.\n')
        videos.scan();self.assertEqual(videos.source(self.video)['tracks'],[])
        self.assertTrue(captions.track_file(translated['id']).exists())

    def test_worker_result_rejects_overlap_outside_unit_and_invalid_types(self):
        for cue in ({'start_ms':False,'end_ms':10,'text':'invalid'}, {'start_ms':10,'end_ms':70000,'text':'outside'}, {'start_ms':10,'end_ms':20,'text':''}):
            with self.subTest(cue=cue),self.assertRaises(ValueError):speech.checked_unit({'cues':[cue],'eof':True,'last_decoded_ms':20},0,60000)


class WorkerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_pause_terminates_only_our_child_and_waits_for_exit(self):
        import sys
        child=await asyncio.create_subprocess_exec(sys.executable,'-c','import sys,time; sys.stdin.readline(); time.sleep(30)',
            stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE)
        other=await asyncio.create_subprocess_exec(sys.executable,'-c','import time; time.sleep(30)')
        worker=speech.Worker();worker.process=child
        try:
            with patch.object(operations,'status',AsyncMock(return_value={'paused':True})):
                with self.assertRaises(HTTPException):await worker.call({'action':'probe','path':'/fixture/media.mp4'})
            await worker.close();self.assertIsNotNone(child.returncode);self.assertIsNone(other.returncode)
        finally:
            await worker.close()
            if other.returncode is None:other.terminate();await other.wait()

    async def test_cancel_during_creation_still_joins_the_created_child(self):
        import sys
        began=asyncio.Event();release=asyncio.Event();created=[];spawn=asyncio.create_subprocess_exec
        async def delayed(*args,**kwargs):
            began.set();await release.wait()
            child=await spawn(sys.executable,'-c','import time; time.sleep(30)',stdout=asyncio.subprocess.PIPE)
            created.append(child);return child
        worker=speech.Worker()
        with patch.object(asyncio,'create_subprocess_exec',delayed):
            task=asyncio.create_task(worker.start());await began.wait();task.cancel();release.set()
            with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(len(created),1);self.assertIsNotNone(created[0].returncode)

    def test_preparation_pin_and_runtime_are_checked_without_loading_or_downloading_model(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache=root/'cache';model=cache/'faster-whisper-small';model.mkdir(parents=True)
            pin={'repository':'fixture/whisper','revision':'pinned'};versions=root/'versions.json';versions.write_text(json.dumps({'speech':pin}))
            for name in ('model.bin','config.json','tokenizer.json'):(model/name).write_bytes(b'tiny fixture')
            (cache/'ready.json').write_text(json.dumps(pin))
            with patch.object(speech,'MODEL_ROOT',cache),patch.object(speech,'VERSIONS',versions),patch.object(speech.importlib.metadata,'version',return_value='fixture-version'):
                value=speech.model_config();self.assertTrue(value['available']);self.assertEqual(value['model'],pin)
                (cache/'ready.json').write_text(json.dumps({**pin,'revision':'another'}));self.assertFalse(speech.model_config()['available'])
                (cache/'ready.json').write_text(json.dumps(pin));(model/'tokenizer.json').unlink();self.assertFalse(speech.model_config()['available'])
