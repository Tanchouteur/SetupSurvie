"""Real local queue/index, fake model only. No corpus, media or model download."""
import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import captions,engine,library,operations,store,videos


class CaptionPreparationTests(unittest.IsolatedAsyncioTestCase):
    # Durable publication is checked for correctness, not a four-second SLA.
    FINISH_TIMEOUT=30
    async def asyncSetUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        for module,key,value in [(store,'ROOT',self.root/'state'),(videos,'ROOT',self.root/'video'),(videos,'ACTIVE',None),
                                 (captions,'ACTIVE',{}),(engine,'LOCK',asyncio.Semaphore(1))]:
            mocked=patch.object(module,key,value);mocked.start();self.addCleanup(mocked.stop)
        videos.ROOT.mkdir();videos.STOP.clear();store.init()
        (videos.ROOT/'rotor.webm').write_bytes(b'tiny fictional file, no decoder required')
        (videos.ROOT/'rotor.info.json').write_text(json.dumps({'title':'Rotor fictif','language':'en','duration':60}))
        self.write_cues(2);videos.scan();self.video=videos.listing()['videos'][0]['id'];self.calls=[]
        self.state={'online':True,'paused':False,'message':'Prêt'}
        self.ready=patch.object(operations,'status',AsyncMock(return_value=self.state));self.ready.start();self.addCleanup(self.ready.stop)
        async def translated(parts,mode):
            self.calls.append([row['position'] for row in parts])
            return [{'id':row['position'],'text':'Le rotor fictif mesure '+str(row['position']+17)+' mm. Ne pas dépasser cette cote.'} for row in parts],'fixture-model',{'context':16384,'private':'fixture'}
        self.translated=translated;self.real_translate=captions.translate_batch
        mock=patch.object(captions,'translate_batch',side_effect=translated);self.mock_translate=mock.start();self.addCleanup(mock.stop)

    def write_cues(self,count):
        (videos.ROOT/'rotor.en.srt').write_text('\n\n'.join(str(i+1)+'\n00:00:'+f'{i:02d}'+',000 --> 00:00:'+f'{i:02d}'+',800\n'+f'The fictional rotor measures {i+17} mm. Do not exceed this value.' for i in range(count))+'\n')

    async def asyncTearDown(self):
        await captions.stop_all();await videos.stop()

    async def finish(self,job):
        task=captions.ACTIVE.get(job['id'])
        if task:await asyncio.wait_for(task,self.FINISH_TIMEOUT)
        if videos.ACTIVE:await asyncio.wait_for(videos.ACTIVE,self.FINISH_TIMEOUT)
        return captions.status(job['id'],full=True)

    async def test_complete_french_track_keeps_original_times_is_indexed_and_never_writes_originals(self):
        before={p.name:p.read_bytes() for p in videos.ROOT.iterdir()}
        job=await captions.create(self.video,0,'rapide');result=await self.finish(job)
        self.assertEqual(result['status'],'completed',result)
        self.assertEqual((result['done'],result['total']),(2,2));self.assertEqual(result['human_review'],'not_performed')
        self.assertEqual(before,{p.name:p.read_bytes() for p in videos.ROOT.iterdir()})
        value=videos.source(self.video);self.assertEqual(value['subtitle_status'],'french_prepared')
        self.assertEqual(value['language'],'fr');self.assertIn('17 mm',value['text']);self.assertIn('Traduction locale automatique',value['video_notice'])
        tracks=value['tracks'];fr=next(track for track in tracks if track['language']=='fr')
        self.assertEqual(fr['origin'],'local_translation');self.assertEqual(len(tracks),2)
        key,_=videos.identity(self.video);text=videos.webvtt(key,fr['id'])
        self.assertIn('00:00:00.000 --> 00:00:00.800',text);self.assertIn('00:00:01.000 --> 00:00:01.800',text)
        plan=library.retrieval.plan('rotor',library.search_terms('rotor'),library.SYNONYMS)
        found,_=videos.search(plan,'fr');self.assertTrue(found)
        self.assertTrue(all(row['transcription_origin']=='local_translation' for row in found))
        english=videos.source(self.video+'#t=0&track=0');self.assertEqual(english['language'],'en')
        self.assertNotIn('source_text',json.dumps(captions.listing()))

    async def test_duplicate_request_reuses_completed_preparation(self):
        first=await captions.create(self.video,0,'rapide');await self.finish(first)
        second=await captions.create(self.video,0,'rapide')
        self.assertEqual(first['id'],second['id']);self.assertEqual(len(self.calls),1)

    async def test_numbers_or_units_changed_never_publish_and_rejections_survive_resume(self):
        async def bad(parts,mode):return [{'id':row['position'],'text':'Le rotor mesure 999 cm.'} for row in parts],'bad-model',{}
        self.mock_translate.side_effect=bad
        job=await captions.create(self.video,0,'rapide');failed=await self.finish(job)
        self.assertEqual(failed['status'],'error');self.assertEqual(failed['blocked'],1)
        self.assertFalse(captions.track_file(job['id']).exists());self.assertEqual(videos.source(self.video)['language'],'en')
        self.assertTrue(failed['rejected_proposals']);self.assertIn('999',failed['parts'][0]['candidate'])
        self.mock_translate.side_effect=self.translated
        result=await self.finish(await captions.resume(job['id'],'rapide'))
        self.assertEqual(result['status'],'completed');self.assertEqual(len(result['rejected_proposals']),3)

    async def test_only_the_bad_cue_is_retried_then_batching_and_original_times_are_kept(self):
        self.write_cues(18);videos.scan()
        async def translate(parts,mode):
            rows,model,metrics=await self.translated(parts,mode)
            if len(parts)>1 and parts[0]['position']==0:rows[1]['text']='Le rotor fictif mesure 999 cm.'
            return rows,model,metrics
        self.mock_translate.side_effect=translate
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(self.calls,[list(range(16)),[1],[16,17]])
        self.assertEqual((result['status'],result['done']),('completed',18))
        self.assertEqual(len(result['rejected_proposals']),1)
        self.assertEqual([(part['start_ms'],part['end_ms']) for part in result['parts']],
            [(1000*i,1000*i+800) for i in range(18)])

    async def test_pause_and_resume_reuses_only_completed_cues(self):
        self.write_cues(40);videos.scan();entered=asyncio.Event()
        async def delayed(parts,mode):
            if parts[0]['position']>=16:entered.set();await asyncio.Event().wait()
            return await self.translated(parts,mode)
        self.mock_translate.side_effect=delayed
        job=await captions.create(self.video,0,'rapide');await asyncio.wait_for(entered.wait(),4)
        paused=await captions.pause(job['id']);self.assertEqual(paused['status'],'paused');self.assertEqual(paused['done'],16)
        self.assertFalse(captions.track_file(job['id']).exists())
        self.mock_translate.side_effect=self.translated
        result=await self.finish(await captions.resume(job['id']))
        self.assertEqual(result['status'],'completed');self.assertEqual(result['done'],40)
        self.assertEqual(self.calls[0],list(range(16)));self.assertEqual(self.calls[1][0],16)

    async def test_changed_source_refuses_resume_and_hides_old_prepared_track(self):
        job=await captions.create(self.video,0,'rapide');await self.finish(job)
        path=videos.ROOT/'rotor.en.srt';path.write_text(path.read_text()+'\n\n3\n00:00:03,000 --> 00:00:04,000\nChanged source\n')
        with self.assertRaises(HTTPException):videos.source(self.video)
        videos.scan();self.assertFalse(any(t['origin']=='local_translation' for t in videos.source(self.video)['tracks']))
        captions.update(job['id'],'paused')
        with self.assertRaises(HTTPException):await captions.resume(job['id'])
        self.assertTrue(captions.track_file(job['id']).exists())

    async def test_restart_is_paused_without_implicit_inference(self):
        launch=patch.object(captions,'launch');launch.start();self.addCleanup(launch.stop)
        job=await captions.create(self.video,0,'rapide')
        self.assertEqual(job['status'],'paused');self.assertEqual(self.calls,[])
        launch.stop();result=await self.finish(await captions.resume(job['id']))
        self.assertEqual(result['status'],'completed')

    async def test_engine_pause_prevents_create_and_leaves_pending_work_paused(self):
        self.state.update(paused=True)
        with self.assertRaises(HTTPException):await captions.create(self.video,0,'rapide')
        self.assertEqual(captions.listing(),[]);self.assertEqual(self.calls,[])

    async def test_game_pause_between_batches_keeps_progress_without_restarting_engine(self):
        self.write_cues(40);videos.scan()
        async def paused(parts,mode):
            value=await self.translated(parts,mode);self.state['paused']=True;return value
        self.mock_translate.side_effect=paused
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'paused');self.assertEqual(result['done'],16)
        self.assertEqual(len(self.calls),1);self.assertFalse(captions.track_file(result['id']).exists())

    async def test_protocol_rejection_is_kept_and_never_mistaken_for_a_track(self):
        async def bad(parts,mode):raise captions.CandidateError('Fixture wrong ids','{"cues":[{"id":900}]}')
        self.mock_translate.side_effect=bad
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'error');self.assertEqual(result['done'],0)
        self.assertIn('900',result['rejected_proposals'][0]['candidate'])

    async def test_contradictory_refusal_gets_one_clarification_and_keeps_rejected_candidate(self):
        candidate='{"status":"refused","cues":[{"id":0,"text":"Proposition refusée"}]}'
        async def response(parts,mode,**kwargs):
            if not kwargs:raise captions.CandidateError('Inconsistent status',candidate,repairable=True,metrics={'total_ms':123})
            self.assertEqual(kwargs,{'repair':candidate})
            return await self.translated(parts,mode)
        self.mock_translate.side_effect=response
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'completed');self.assertEqual(self.mock_translate.await_count,2)
        self.assertEqual(result['rejected_proposals'][0]['candidate'],candidate)
        metrics=json.loads(result['parts'][0]['metrics'])
        self.assertEqual(metrics['format_repair_count'],1);self.assertEqual(metrics['format_repair_attempt']['total_ms'],123)

    async def test_interrupted_format_clarification_keeps_both_rejections_and_retries(self):
        attempts=[]
        async def response(parts,mode,**options):
            attempts.append([part['position'] for part in parts])
            if len(attempts)==1:
                raise captions.CandidateError('Statut contradictoire','première réponse',repairable=True)
            if options.get('repair'):
                raise captions.InterruptedBatch('Flux interrompu','réponse partielle')
            return await self.translated(parts,mode)
        self.mock_translate.side_effect=response
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(attempts,[[0,1],[0,1],[0],[1]])
        self.assertEqual((result['status'],result['done']),('completed',2))
        self.assertEqual([entry['candidate'] for entry in result['rejected_proposals']],['première réponse','réponse partielle'])

    async def test_second_contradiction_stops_without_an_unbounded_retry(self):
        self.mock_translate.side_effect=captions.CandidateError('Still inconsistent','refused data',repairable=True)
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'error');self.assertEqual(result['done'],0)
        self.assertEqual(self.mock_translate.await_count,2);self.assertEqual(len(result['rejected_proposals']),2)
        self.assertFalse(captions.track_file(result['id']).exists())

    async def test_game_pause_after_contradiction_prevents_the_clarification(self):
        async def response(parts,mode):
            self.state['paused']=True
            raise captions.CandidateError('Inconsistent','refused data',repairable=True)
        self.mock_translate.side_effect=response
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'paused');self.assertEqual(self.mock_translate.await_count,1)
        self.assertEqual(len(result['rejected_proposals']),1);self.assertFalse(captions.track_file(result['id']).exists())

    async def test_job_path_rejects_traversal_and_symlink(self):
        with self.assertRaises(HTTPException):captions.track_file('../../not-ours')
        key=store.new_id();folder=store.ROOT/'video-captions';folder.mkdir()
        try:(folder/key).symlink_to(self.root,target_is_directory=True)
        except OSError:self.skipTest('Symlink creation unavailable')
        with self.assertRaises(HTTPException):captions.track_file(key)

    async def test_pause_joins_publication_thread_and_cannot_expose_a_late_track(self):
        entered=threading.Event();release=threading.Event();original=captions.publish
        def publishing(identifier):
            entered.set()
            if not release.wait(4):raise RuntimeError('Test publication was not released')
            return original(identifier)
        with patch.object(captions,'publish',side_effect=publishing):
            job=await captions.create(self.video,0,'rapide')
            self.assertTrue(await asyncio.to_thread(entered.wait,3))
            paused=asyncio.create_task(captions.pause(job['id']))
            await asyncio.sleep(.02);self.assertFalse(paused.done())
            release.set();result=await asyncio.wait_for(paused,3)
        self.assertEqual(result['status'],'paused');videos.scan()
        self.assertFalse(any(track['origin']=='local_translation' for track in videos.source(self.video)['tracks']))
        self.assertEqual((await self.finish(await captions.resume(job['id'])))['status'],'completed')

    async def test_model_never_returns_timestamps_or_reorders_cues(self):
        original=httpx.AsyncClient;payloads=[]
        response_cues=[{'id':2,'text':'Texte français'}]
        def handler(request):
            payload=json.loads(request.content);payloads.append(payload)
            return httpx.Response(200,content=json.dumps({'message':{'content':json.dumps({'status':'translated','cues':response_cues})},'done':True,'done_reason':'stop'}).encode()+b'\n')
        with patch.object(captions.model_runtime,'describe',AsyncMock(return_value={'available':True,'installed':True,'native_context':16384,'running':None,'other_models':0})),\
             patch.object(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
            with self.assertRaises(captions.CandidateError):await self.real_translate([{'position':0,'source_text':'17 mm'}],'rapide')
            response_cues[:]=[{'id':0,'text':'Le rotor mesure 17 mm.'}]
            result,model,metrics=await self.real_translate([{'position':0,'source_text':'17 mm'}],'rapide')
        self.assertEqual(result[0]['id'],0);self.assertEqual(metrics['status'],'done');self.assertIn('writing',metrics['phases_ms'])
        self.assertIn('runtime_after',metrics);self.assertIsNotNone(metrics['first_text_ms'])
        self.assertEqual(len(payloads),2);self.assertNotIn('start_ms',payloads[0]['messages'][1]['content'])

    async def test_compact_cpu_profile_is_used_to_publish_a_french_track(self):
        compact = engine.COMPACT_CPU
        original = httpx.AsyncClient
        payloads = []

        def handler(request):
            payload = json.loads(request.content)
            payloads.append(payload)
            instruction, _, segments = payload['messages'][1]['content'].partition('\n')
            self.assertIn('Translate the following subtitles into French', instruction)
            parts = json.loads(segments)
            rows = [{'id': part['id'], 'text': f'Le rotor fictif mesure {part["id"] + 17} mm. Ne pas dépasser cette cote.'}
                    for part in parts]
            reply = {'message': {'content': json.dumps({'status': 'translated', 'cues': rows})},
                     'done': True, 'done_reason': 'stop'}
            return httpx.Response(200, content=json.dumps(reply).encode() + b'\n')

        runtime = {'available': True, 'installed': True, 'native_context': 32768, 'running': None, 'other_models': 0}
        with patch.dict(engine.MODES, {'rapide': {**engine.MODES['rapide'], **compact}}), \
                patch.object(captions, 'translate_batch', self.real_translate), \
                patch.object(captions.model_runtime, 'describe', AsyncMock(return_value=runtime)), \
                patch.object(httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)):
            result = await self.finish(await captions.create(self.video, 0, 'rapide'))
        self.assertEqual(result['status'], 'completed', result)
        self.assertTrue(any(track['language'] == 'fr' for track in videos.source(self.video)['tracks']))
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]['model'], compact['model'])
        self.assertEqual(payloads[0]['options']['num_ctx'], 8192)
        self.assertIs(payloads[0]['think'], False)

    async def test_real_protocol_clarifies_status_but_never_accepts_an_explicit_refusal(self):
        original=httpx.AsyncClient;payloads=[];refused=False
        def handler(request):
            payload=json.loads(request.content);payloads.append(payload)
            parts=json.loads(payload['messages'][1]['content'])
            rows=[{'id':p['id'],'text':f'Le rotor fictif mesure {p["id"]+17} mm. Ne pas dépasser cette cote.'} for p in parts]
            value={'status':'refused' if refused or len(payloads)==1 else 'translated','cues':[] if refused else rows}
            return httpx.Response(200,content=json.dumps({'message':{'content':json.dumps(value)},'done':True,'done_reason':'stop'}).encode()+b'\n')
        with patch.object(captions,'translate_batch',self.real_translate),\
             patch.object(captions.model_runtime,'describe',AsyncMock(return_value={'available':True,'installed':True,'native_context':16384,'running':None,'other_models':0})),\
             patch.object(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
            first=await self.finish(await captions.create(self.video,0,'rapide'))
            self.assertEqual(first['status'],'completed');self.assertEqual(len(payloads),2)
            self.assertTrue(any('annonce un refus' in m.get('content','') for m in payloads[1]['messages']))
            self.assertEqual(len(first['rejected_proposals']),1)
            self.assertIn('refused',first['rejected_proposals'][0]['candidate'])
            # A different source revision makes a separate job; an unambiguous
            # empty refusal is not retried and never receives a French track.
            self.write_cues(3);videos.scan();refused=True;payloads.clear()
            second=await self.finish(await captions.create(self.video,0,'rapide'))
            self.assertEqual(second['status'],'error');self.assertEqual(second['done'],0)
            self.assertEqual(len(payloads),1);self.assertFalse(captions.track_file(second['id']).exists())

    async def test_output_format_offers_no_refusal_and_keeps_spoken_apologies(self):
        original=httpx.AsyncClient;payloads=[]
        def handler(request):
            payload=json.loads(request.content);payloads.append(payload)
            parts=json.loads(payload['messages'][1]['content'])
            value={'cues':[{'id':p['id'],'text':f'Désolé, le rotor fictif mesure {p["id"]+17} mm. Ne pas dépasser cette cote.'} for p in parts]}
            return httpx.Response(200,content=json.dumps({'message':{'content':json.dumps(value)},'done':True,'done_reason':'stop'}).encode()+b'\n')
        with patch.object(captions,'translate_batch',self.real_translate),\
             patch.object(captions.model_runtime,'describe',AsyncMock(return_value={'available':True,'installed':True,'native_context':16384,'running':None,'other_models':0})),\
             patch.object(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
            result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(result['status'],'completed')
        self.assertNotIn('status',payloads[0]['format']['properties']);self.assertNotIn('refused',payloads[0]['messages'][0]['content'])

    async def test_missing_and_reordered_cues_retry_in_smaller_groups_then_publish(self):
        self.write_cues(6);videos.scan()
        original=httpx.AsyncClient;attempts=[]
        def handler(request):
            payload=json.loads(request.content)
            parts=json.loads(payload['messages'][1]['content'])
            attempts.append([p['id'] for p in parts])
            schema=payload['format']['properties']['cues']
            self.assertEqual((schema['minItems'],schema['maxItems']),(len(parts),len(parts)))
            rows=[{'id':p['id'],'text':f'Le rotor fictif mesure {p["id"]+17} mm. Ne pas dépasser cette cote.'} for p in parts]
            value={'cues':rows[-2::-1] if len(attempts)==1 else rows}
            return httpx.Response(200,json={'message':{'content':json.dumps(value)},'done':True,'done_reason':'stop'})
        with patch.object(captions,'translate_batch',self.real_translate),\
             patch.object(captions.model_runtime,'describe',AsyncMock(return_value={'available':True,'installed':True,'native_context':16384,'running':None,'other_models':0})),\
             patch.object(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
            result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(attempts,[list(range(6)),[0,1,2],[3,4,5]])
        self.assertEqual((result['status'],result['done']),('completed',6))
        self.assertEqual(len(result['rejected_proposals']),1)

    async def test_single_cue_retries_an_interrupted_reply_before_publishing(self):
        self.write_cues(1);videos.scan()
        original=httpx.AsyncClient
        calls=[]
        def handler(request):
            calls.append(json.loads(request.content))
            if len(calls)==1:
                interrupted={'message':{'content':'{"cues":[{"id":0,"text":"999'},'done':False}
                return httpx.Response(200,content=(json.dumps(interrupted)+'\n').encode())
            value={'cues':[{'id':0,'text':'Le rotor fictif mesure 17 mm. Ne dépassez pas cette valeur.'}]}
            return httpx.Response(200,json={'message':{'content':json.dumps(value)},'done':True,'done_reason':'stop'})
        runtime={'available':False,'native_context':None}
        with patch.object(captions,'translate_batch',self.real_translate),patch.object(
             captions.model_runtime,'describe',AsyncMock(return_value=runtime)),patch.object(
             httpx,'AsyncClient',side_effect=lambda **kw:original(transport=httpx.MockTransport(handler),**kw)
        ):
            result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(len(calls),2)
        self.assertEqual((result['status'],result['done']),('completed',1))
        self.assertIn('999',result['rejected_proposals'][0]['candidate'])
        self.assertNotIn('999',captions.track_file(result['id']).read_text())

    async def test_permanent_single_cue_interruption_stops_after_one_retry(self):
        self.write_cues(1);videos.scan()
        self.mock_translate.side_effect=captions.InterruptedBatch('Flux interrompu','Proposition partielle')
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual(self.mock_translate.await_count,2)
        self.assertEqual((result['status'],result['done']),('error',0))
        self.assertFalse(captions.track_file(result['id']).exists())

    async def test_incomplete_single_cue_stops_without_publishing(self):
        self.mock_translate.side_effect=captions.IncompleteBatch('Segment omis','{"cues":[]}')
        result=await self.finish(await captions.create(self.video,0,'rapide'))
        self.assertEqual((result['status'],result['done']),('error',0))
        self.assertEqual([len(call.args[0]) for call in self.mock_translate.await_args_list],[2,1])
        self.assertEqual(len(result['rejected_proposals']),2)
        self.assertFalse(captions.track_file(result['id']).exists())

    async def test_api_requires_family_and_report_does_not_start_inference(self):
        from pilot import app as gateway
        role={'id':'fixture','role':'reader'}
        async def user():return role
        gateway.app.dependency_overrides[gateway.user]=user;self.addCleanup(gateway.app.dependency_overrides.clear)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/admin/video-captions')).status_code,403)
            role['role']='admin';self.assertEqual((await client.get('/api/admin/video-captions')).json(),{'jobs':[]})
            self.assertEqual(self.calls,[])
            self.assertEqual((await client.post('/api/admin/video-captions',json={'id':'video:../x','track':0})).status_code,422)


if __name__=='__main__':unittest.main()
