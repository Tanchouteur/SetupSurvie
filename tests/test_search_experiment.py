"""Paired experiment with fake retrieval and fake inference, no real corpus/model."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx
from fastapi import HTTPException
from pilot import calibration,engine,library,model_runtime,operations,search_experiment as experiment,store,translations


class SearchExperimentTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_zero_free_space_sample_is_kept_as_the_minimum(self):
        report={'reserves':{},'minimum_free':{}}
        samples=iter([{'disk':10},{'disk':0},{'disk':5_000_000_000}])
        async def slow():await asyncio.sleep(3.5);return 'done'
        with patch.object(calibration,'guard',AsyncMock(side_effect=lambda _:next(samples,{'disk':7}))):
            self.assertEqual(await experiment.watched(slow(),report),'done')
        self.assertEqual(report['minimum_free']['disk'],0)

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);root=Path(temporary.name)
        self.pause=False;self.hang=False;self.invalid=False;self.bad_rank=False;self.partial=False;self.remote=False
        self.large_coverage=False;self.missing_video=False
        self.started=asyncio.Event();self.release=asyncio.Event();self.calls=[]
        reference={'version':'fixture.1','cases':[{'id':sid,'query':query,'domain':'resilience','need':'Fictional need'} for sid,query in [('tune-fire','calibration feu'),('verify-fire','production feu'),('verify-unknown','inconnue')]]}
        path=root/'reference.json';path.write_text(json.dumps(reference))
        for target,name,value in [(store,'ROOT',root/'state'),(engine,'LOCK',asyncio.Semaphore(1)),(engine,'ACTIVE',{}),(translations,'ACTIVE',{}),(calibration,'ACTIVE',{}),(experiment,'ACTIVE',{}),(experiment,'REFERENCE',path)]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        store.init()
        async def state(**kwargs):return {'online':True,'control_available':True,'paused':self.pause,'memory':{'total':32*1024**3,'available':20*1024**3},'gpus':[] if self.missing_video else [{'name':'Fake GPU','total':8*1024**3,'used':3*1024**3}]}
        p=patch.object(operations,'status',AsyncMock(side_effect=state));p.start();self.addCleanup(p.stop)
        async def runtime(*args,**kwargs):return {'available':True,'installed':not self.remote,'digest':'a'*64,'native_context':32768,'other_models':0,'running':{'size_vram':5*1024**3} if self.missing_video else None}
        p=patch.object(model_runtime,'describe',AsyncMock(side_effect=runtime));p.start();self.addCleanup(p.stop)
        self.unload=AsyncMock()
        p=patch.object(calibration,'release_model',self.unload);p.start();self.addCleanup(p.stop)
        async def find(query,**kwargs):
            self.assertEqual(kwargs['limit'],5);self.assertEqual(kwargs['domain'],'resilience')
            if 'inconnue' in query:return library.SearchResults([],{'status':'complete'})
            title='Useful fictional procedure' if query in ('allumage','fire making') else 'Incidental fictional mention'
            sid='useful' if query in ('allumage','fire making') else 'distractor'
            coverage={'status':'partial' if self.partial else 'complete'}
            if self.large_coverage:coverage['local_index']={'phase':'completed','archives':400,'articles':1000,'results':[{'archive':'fixture.zim','path':'PRIVATE-PATH-'+str(i),'detail':'x'*1000} for i in range(400)]}
            return library.SearchResults([{'id':'guide:'+sid,'title':title,'language':'en','excerpt':'Fictional extract, no real instructions.','private':'DO NOT EXPORT'}],coverage)
        p=patch.object(library,'search',AsyncMock(side_effect=find));p.start();self.addCleanup(p.stop)
        client=httpx.AsyncClient
        async def handler(request):
            self.assertEqual(request.url.path,'/api/chat');self.calls.append(request.url.path)
            payload=json.loads(request.content);self.assertNotIn('tools',payload);self.assertEqual(payload['options']['num_ctx'],8192)
            self.started.set()
            if self.hang:await self.release.wait()
            data=json.loads(payload['messages'][1]['content'])
            if 'candidates' in data:
                order=sorted(range(len(data['candidates'])),key=lambda i:not data['candidates'][i]['title'].startswith('Useful'))
                value={'order':[999] if self.bad_rank else order}
            else:value={'fr':'inconnue' if data['query']=='inconnue' else 'allumage','en':'inconnue' if data['query']=='inconnue' else 'fire making'}
            event={'message':{'content':'malformed' if self.invalid else json.dumps(value),'thinking':'PRIVATE REASONING'},'done':True,'done_reason':'stop','prompt_eval_count':100,'eval_count':10,'load_duration':1000000}
            return httpx.Response(200,content=json.dumps(event).encode()+b'\n')
        p=patch.object(httpx,'AsyncClient',side_effect=lambda **kw:client(transport=httpx.MockTransport(handler),**kw));p.start();self.addCleanup(p.stop)

    async def finish(self,suite='verification'):
        report=await experiment.start('rapide',suite,15000)
        await asyncio.wait_for(experiment.ACTIVE[report['id']],5)
        return experiment.status()

    def judge_all(self,report):
        for case in report['cases']:
            report=experiment.review(report['id'],case['id'],{r['id']:'useful' if r['id']=='guide:useful' else 'unrelated' for r in case['candidates']})
        return report

    async def test_paired_methods_need_human_judgments_and_never_enable_search(self):
        report=await self.finish('all');self.assertEqual(report['status'],'completed',report)
        self.assertEqual(report['summary']['decision'],'needs_review')
        self.assertEqual(report['cases'][1]['methods']['baseline']['ids'],['guide:distractor'])
        self.assertEqual(report['cases'][1]['methods']['rewritten']['ids'][0],'guide:useful')
        self.assertEqual(report['cases'][1]['methods']['reranked']['ids'][0],'guide:useful')
        report=self.judge_all(report)
        self.assertEqual(report['summary']['decision'],'candidate_to_confirm')
        self.assertFalse(report['summary']['enabled_by_default']);self.assertEqual(report['summary']['splits']['verification']['baseline']['hit5'],0)
        self.assertEqual(report['summary']['splits']['verification']['reranked']['hit5'],1)
        self.assertEqual(report['summary']['splits']['verification']['reranked']['no_useful_in_pool'],1)
        self.assertEqual(report['summary']['splits']['calibration']['baseline']['measured'],1)
        self.assertNotIn('PRIVATE REASONING',json.dumps(report));self.assertNotIn('DO NOT EXPORT',json.dumps(report))
        self.assertTrue(experiment.location().with_name(report['id']+'.json').is_file());self.unload.assert_awaited_once()
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM settings').fetchone()[0],0)

    async def test_invalid_model_output_and_invented_indices_keep_original_results(self):
        self.bad_rank=True;report=await self.finish()
        case=report['cases'][0];self.assertEqual(case['methods']['reranked']['error'],'invalid_output')
        self.assertEqual(case['methods']['baseline']['ids'],['guide:distractor'])
        self.assertNotIn('999',json.dumps(case['candidates']))
        self.invalid=True;report=await self.finish()
        self.assertEqual(report['cases'][0]['methods']['rewritten']['error'],'invalid_output')
        self.assertNotIn('reranked',report['cases'][0]['methods'])

    async def test_partial_coverage_and_exceeded_budget_prevent_candidate_decision(self):
        self.partial=True;report=self.judge_all(await self.finish())
        self.assertEqual(report['summary']['decision'],'needs_coverage')
        self.assertFalse(report['summary']['candidates_to_confirm'])
        report['cases'][0]['coverage_complete']=True
        report['cases'][0]['methods']['rewritten']['elapsed_ms']=15001
        report['cases'][0]['methods']['reranked']['elapsed_ms']=15001
        self.assertFalse(experiment.summarize(report)['candidates_to_confirm'])

    async def test_pause_refuses_before_any_inference_and_remote_model_is_refused(self):
        self.pause=True
        with self.assertRaises(HTTPException):await experiment.start()
        self.assertEqual(self.calls,[])
        self.pause=False;self.remote=True;report=await self.finish()
        self.assertEqual(report['reason'],'model_metadata_unavailable');self.assertEqual(self.calls,[])

    async def test_new_question_interrupts_inference_and_does_not_unload_its_model(self):
        self.hang=True;report=await experiment.start();await asyncio.wait_for(self.started.wait(),2)
        engine.ACTIVE['queued-question']=object()
        await asyncio.wait_for(experiment.ACTIVE[report['id']],4)
        self.assertEqual(experiment.status()['reason'],'other_activity');self.unload.assert_not_awaited()
        self.assertEqual(experiment.status()['cases'][0]['methods']['baseline']['ids'],['guide:distractor'])

    async def test_explicit_cancel_restart_and_mutual_exclusion(self):
        self.hang=True;report=await experiment.start();await asyncio.wait_for(self.started.wait(),2)
        with self.assertRaises(HTTPException):await calibration.start('rapide')
        with self.assertRaises(HTTPException):await experiment.start()
        await experiment.cancel();self.assertEqual(experiment.status()['status'],'cancelled')
        saved=experiment.status();saved['status']='running';experiment.save(saved)
        self.assertEqual(experiment.status()['reason'],'service_restarted');self.assertFalse(experiment.running())
        self.assertNotIn('/api/pull',self.calls)

    async def test_review_rejects_unknown_candidate_and_wrong_run(self):
        report=await self.finish()
        with self.assertRaises(HTTPException):experiment.review(report['id'],'verify-fire',{'invented':'useful'})
        with self.assertRaises(HTTPException):experiment.review('b'*32,'verify-fire',{})
        report=experiment.review(report['id'],'verify-fire',{'guide:useful':'uncertain'})
        self.assertEqual(report['summary']['splits']['verification']['reranked']['fully_judged'],1) # empty negative pool only

    async def test_one_second_budget_cancels_model_and_stops_two_successive_failures(self):
        self.hang=True
        started=asyncio.get_running_loop().time();report=await experiment.start('rapide','all',1000)
        await asyncio.wait_for(experiment.ACTIVE[report['id']],5)
        report=experiment.status();self.assertEqual(report['reason'],'repeated_failures');self.assertEqual(len(report['cases']),2)
        self.assertEqual(len(self.calls),2);self.assertLess(asyncio.get_running_loop().time()-started,3)
        for case in report['cases']:
            self.assertEqual(case['methods']['rewritten']['error'],'latency_budget')
            self.assertLess(case['methods']['rewritten']['elapsed_ms'],1300)
            self.assertEqual(case['methods']['baseline']['ids'],['guide:distractor'])
        self.assertFalse(report['summary']['enabled_by_default'])

    async def test_finished_stream_has_numerical_progress_without_private_thinking(self):
        report=await self.finish();call=report['cases'][0]['model_calls'][0]
        self.assertEqual(call['frames'],1);self.assertGreater(call['thinking_characters'],0);self.assertGreater(call['answer_characters'],0)
        self.assertIsInstance(call['first_frame_ms'],int);self.assertNotIn('PRIVATE REASONING',json.dumps(report))

    async def test_unavailable_controller_during_model_preserves_diagnostic_not_memory_exhaustion(self):
        self.hang=True;report=await experiment.start();await asyncio.wait_for(self.started.wait(),2)
        with patch.object(operations,'status',AsyncMock(return_value={'online':True,'control_available':False,'control_error':'timeout','control_elapsed_ms':5000,'memory':{}})):
            await asyncio.wait_for(experiment.ACTIVE[report['id']],4)
        report=experiment.status();self.assertEqual(report['reason'],'hardware_unavailable')
        self.assertEqual(report['failure_sample']['control_error'],'timeout');self.assertFalse(report['failure_sample']['ram_sample_available'])

    async def test_missing_calibration_review_and_known_regression_cannot_validate_option(self):
        report=await self.finish('all')
        for case in report['cases'][1:]:
            report=experiment.review(report['id'],case['id'],{r['id']:'useful' if r['id']=='guide:useful' else 'unrelated' for r in case['candidates']})
        self.assertEqual(report['summary']['decision'],'needs_review')
        report=self.judge_all(report)
        case=report['cases'][0];case['methods']['baseline']['ids']=['guide:useful'];case['methods']['reranked']['ids']=['guide:distractor'];case['methods']['rewritten']['ids']=['guide:distractor']
        self.assertFalse(experiment.summarize(report)['candidates_to_confirm'])

    async def test_pause_mid_request_and_immediate_cancel_keep_report_without_resuming(self):
        self.hang=True;report=await experiment.start();await asyncio.wait_for(self.started.wait(),2);self.pause=True
        await asyncio.wait_for(experiment.ACTIVE[report['id']],4)
        self.assertEqual(experiment.status()['reason'],'paused')
        self.pause=False;await experiment.start();await experiment.cancel()
        self.assertEqual(experiment.status()['reason'],'user_cancelled');self.assertFalse(experiment.running())

    async def test_large_index_manifest_is_summarized_and_missing_video_measurement_refuses_conclusion(self):
        self.large_coverage=True;report=await self.finish('all')
        raw=json.dumps(report);self.assertLess(len(raw),20000);self.assertNotIn('PRIVATE-PATH',raw)
        self.assertEqual(report['cases'][0]['coverage'][0]['local_index']['archives'],400)
        self.missing_video=True;report=await self.finish()
        self.assertEqual(report['status'],'interrupted');self.assertEqual(report['reason'],'hardware_unavailable')
        self.assertEqual(report['summary']['decision'],'needs_measurements')

    def test_reference_is_bundled_with_service_and_matches_static_copy(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual((root/'pilot/search-reference.json').read_bytes(),(root/'portal/interface/search-reference.json').read_bytes())
