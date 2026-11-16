"""Durable provider acquisition and common index; fake provider/model, no Internet."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from pilot import captions,caption_acquisition as acquired,engine,operations,provider_subtitles,store,videos

ID='abcDEF_12-3'


class CaptionAcquisitionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        def mock(module,key,value):
            change=patch.object(module,key,value);change.start();self.addCleanup(change.stop)
        for module,key,value in ((store,'ROOT',root/'state'),(videos,'ROOT',root/'video'),(videos,'ACTIVE',None),(acquired,'ACTIVE',{}),(acquired,'CONTROL_LOCK',asyncio.Lock()),(captions,'ACTIVE',{}),(engine,'LOCK',asyncio.Semaphore(1))):mock(module,key,value)
        store.init();videos.ROOT.mkdir();videos.STOP.clear();(videos.ROOT/'fixture.mp4').write_bytes(b'Tiny synthetic video placeholder')
        (videos.ROOT/'fixture.info.json').write_text(json.dumps({'title':'Provider fixture','extractor':'Youtube','id':ID,'language':'en','duration':8}))
        videos.scan();self.video=videos.listing()['videos'][0]['id'];self.language='en';self.calls=[];self.gate=None;self.closed=0;self.failure=None
        test=self
        class Worker:
            async def fetch(self,command):
                test.calls.append(command)
                if test.gate:await test.gate.wait()
                if test.failure:raise ValueError(test.failure)
                rows=[{'start':1,'duration':3,'text':'Do not open the blue cover.'},{'start':3,'duration':2,'text':'Fictional rotor 17 mm.'}]
                cues,changes=provider_subtitles.checked_cues(rows)
                return {'video_id':ID,'provider':'youtube','tool_version':'fixture','track':{'language':test.language,'origin':'automatic','name':'Fixture'},
                    'raw_provider_cues':rows,'cues':cues,'timing_adjustments':changes,'available_tracks':[],'online_translation_requested':False}
            async def close(self):test.closed+=1
        mock(acquired,'FetchWorker',Worker)
        mock(operations,'status',AsyncMock(return_value={'online':True,'paused':False,'message':'Fixture'}))
        async def translate(parts,mode):
            words=['Ne pas ouvrir le capot bleu.','Rotor fictif 17 mm.']
            return [{'id':row['position'],'text':words[row['position']]} for row in parts],'fixture-model',{}
        mock(captions,'translate_batch',translate)

    async def asyncTearDown(self):
        await acquired.stop_all();await captions.stop_all();await videos.stop()

    async def finish(self,job):
        task=acquired.ACTIVE.get(job['id'])
        if task:await asyncio.wait_for(task,4)
        value=acquired.status(job['id'],True)
        if value['translation_job']:
            task=captions.ACTIVE.get(value['translation_job'])
            if task:await asyncio.wait_for(task,4)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,4)
        return value

    async def test_explicit_source_retrieval_keeps_original_rows_then_indexes_both_languages(self):
        before={p.name:p.read_bytes() for p in videos.ROOT.iterdir()};self.assertEqual(self.calls,[])
        job=await acquired.create(self.video);result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result);self.assertTrue(result['translation_job'])
        self.assertEqual(result['timing_adjustments'],1);self.assertEqual(result['provider_result']['raw_provider_cues'][0]['duration'],3)
        source=videos.source(self.video);self.assertEqual(source['language'],'fr');self.assertIn('Ne pas ouvrir',source['text'])
        self.assertEqual({track['origin'] for track in source['tracks']},{'automatic','local_translation'})
        self.assertEqual(before,{p.name:p.read_bytes() for p in videos.ROOT.iterdir()});self.assertEqual(self.closed,1)
        self.assertNotIn('provider_result',acquired.status(job['id']))
        native=Path.read_text
        def no_transcript_poll(path,*args,**kwargs):
            if path.name=='provider.json':raise AssertionError('Status poll must not read a complete transcript')
            return native(path,*args,**kwargs)
        with patch.object(Path,'read_text',no_transcript_poll):
            self.assertEqual(acquired.status(job['id'])['language'],'en')
            self.assertEqual(len(acquired.prepared_tracks(videos.row(self.video)[1])),1)

    async def test_pause_joins_provider_child_and_resume_is_explicit(self):
        self.gate=asyncio.Event();job=await acquired.create(self.video,translate_french=False)
        for _ in range(100):
            if self.calls:break
            await asyncio.sleep(.01)
        paused=await acquired.pause(job['id']);self.assertEqual(paused['status'],'paused');self.assertEqual(self.closed,1)
        self.assertEqual(videos.source(self.video)['tracks'],[])
        self.gate=None;await acquired.resume(job['id']);result=await self.finish(job)
        self.assertEqual(result['status'],'completed');self.assertEqual(len(self.calls),2)

    async def test_blocked_provider_is_not_an_empty_success_and_can_be_retried(self):
        self.failure='provider_blocked';job=await acquired.create(self.video,translate_french=False);result=await self.finish(job)
        self.assertEqual(result['status'],'error');self.assertIn('refuse',result['error']);self.assertEqual(videos.source(self.video)['tracks'],[])
        self.failure=None;self.language='fr';await acquired.resume(job['id']);result=await self.finish(job)
        self.assertEqual(result['status'],'completed');self.assertIsNone(result['translation_job'])

    async def test_no_source_reference_never_searches_by_title_or_contacts_provider(self):
        (videos.ROOT/'fixture.info.json').write_text(json.dumps({'title':'No reliable provider identity','language':'en'}));videos.scan()
        with self.assertRaises(HTTPException):await acquired.create(self.video)
        self.assertEqual(self.calls,[])
        job=await acquired.create(self.video,'https://youtu.be/'+ID,translate_french=False);result=await self.finish(job)
        self.assertEqual(result['status'],'completed');self.assertEqual(result['identity_basis'],'user_reference')

    async def test_changed_local_video_cannot_receive_a_late_provider_response(self):
        self.gate=asyncio.Event();job=await acquired.create(self.video,translate_french=False)
        for _ in range(100):
            if self.calls:break
            await asyncio.sleep(.01)
        (videos.ROOT/'fixture.mp4').write_bytes(b'Changed local edition');self.gate.set();result=await self.finish(job)
        self.assertEqual(result['status'],'error');videos.scan();self.assertEqual(videos.source(self.video)['tracks'],[])

    async def test_resume_is_serialized_and_restart_never_restarts_network(self):
        self.gate=asyncio.Event();job=await acquired.create(self.video,translate_french=False)
        await acquired.stop_all();self.assertEqual(acquired.status(job['id'])['status'],'paused')
        calls=len(self.calls);acquired.listing();await asyncio.sleep(.01);self.assertEqual(len(self.calls),calls)
        resumed=await asyncio.gather(acquired.resume(job['id']),acquired.resume(job['id']),return_exceptions=True)
        self.assertEqual(sum(isinstance(value,HTTPException) and value.status_code==409 for value in resumed),1)
        self.gate.set();result=await self.finish(job);self.assertEqual(result['status'],'completed')

    async def test_translation_pause_does_not_lose_acquired_source(self):
        with patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':True,'message':'Pause de test'})):
            result=await self.finish(await acquired.create(self.video))
        self.assertEqual(result['status'],'completed');self.assertIsNone(result['translation_job'])
        self.assertIn('traduction',result['error']);self.assertEqual(videos.source(self.video)['language'],'en')

    async def test_early_database_without_summary_keeps_completed_tracks_after_upgrade(self):
        result=await self.finish(await acquired.create(self.video,translate_french=False))
        with acquired.connect() as db:db.execute('ALTER TABLE jobs DROP COLUMN result_summary')
        reopened=(await asyncio.gather(*(asyncio.to_thread(acquired.status,result['id'],True) for _ in range(8))))[0]
        self.assertEqual(reopened['published_hash'],result['published_hash']);self.assertEqual(reopened['status'],'completed')
        self.assertEqual(len(acquired.prepared_tracks(videos.row(self.video)[1])),1)


class FetchWorkerProcessTests(unittest.IsolatedAsyncioTestCase):
    async def execute(self,script,command=None,cancel=False):
        import os
        import sys
        native=asyncio.create_subprocess_exec
        async def child(*args,**kwargs):return await native(sys.executable,'-c',script,**kwargs)
        worker=acquired.FetchWorker()
        with patch.object(asyncio,'create_subprocess_exec',child),patch.dict(os.environ,{'PROVIDER_SECRET_FIXTURE':'must-not-reach-child'}):
            task=asyncio.create_task(worker.fetch(command or {'id':ID}))
            try:
                if cancel:
                    for _ in range(100):
                        if worker.process:break
                        await asyncio.sleep(.01)
                    task.cancel()
                return await asyncio.wait_for(task,5)
            finally:
                await worker.close()
                if worker.process:
                    self.assertIsNotNone(worker.process.returncode);self.assertTrue(worker.process.stdout.at_eof())

    async def test_actual_child_receives_json_without_parent_secrets(self):
        result=await self.execute("import json,sys,os; command=json.load(sys.stdin); print(json.dumps({'ok':True,'result':{'id':command['id'],'has_secret':'PROVIDER_SECRET_FIXTURE' in os.environ}}))")
        self.assertEqual(result,{'id':ID,'has_secret':False})

    async def test_cancelled_real_child_is_terminated_and_joined(self):
        with self.assertRaises(asyncio.CancelledError):await self.execute('import sys,time; sys.stdin.read(); time.sleep(60)',cancel=True)

    async def test_oversized_child_output_is_bounded_and_child_is_joined(self):
        with self.assertRaisesRegex(ValueError,'provider_response_too_large'):await self.execute("import sys; sys.stdin.read(); sys.stdout.write('x'*25000000); sys.stdout.flush()")
