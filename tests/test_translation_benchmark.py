"""40 actual generated PDF pages; model and host counters are simulated."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import engine,operations,store,translations,translation_benchmark as bench


class TranslationBenchmarkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.calls=[];self.paused=False;self.started=asyncio.Event()
        for module,name,value in [(store,'ROOT',self.root),(engine,'LOCK',asyncio.Semaphore(1)),(engine,'ACTIVE',{}),
            (translations,'ACTIVE',{}),(bench,'ACTIVE',{}),(bench,'REPORTS',{}),(bench,'INTERVAL',.01)]:self.mock(module,name,value)
        store.init();self.mock(bench,'competing',lambda:False)
        self.mock(operations,'status',AsyncMock(side_effect=lambda **kw:{'online':True,'paused':self.paused}))
        self.mock(operations,'performance',AsyncMock(return_value={'available':True,'memory':{'total':32*1024**3,'available':12*1024**3},'cpu':{'percent':42},'gpus':[],'disks':[]}))
        async def translated(text,mode,*,on_metrics=None):
            self.calls.append(text)
            if on_metrics:on_metrics({'context':16384,'requested_context':32768,'runtime_after':{'running':{'context_length':16384}},
                'model_calls':[{'prompt_eval_count':100,'eval_count':200,'load_ms':3,'eval_ms':10}], 'answer':'DO_NOT_EXPORT_PRIVATE'})
            await asyncio.sleep(.001)
            return 'Texte de recette en français, sans valeur pratique. '+text.replace('The ','Le '),'fake-model'
        self.translated=translated;self.translate=self.mock(translations,'translate',translated)

    def mock(self,module,name,value):
        patcher=patch.object(module,name,value);mocked=patcher.start();self.addCleanup(patcher.stop);return mocked

    async def asyncTearDown(self):await bench.pause()

    async def finish(self):
        task=next(iter(bench.ACTIVE.values()),None)
        if task:await asyncio.wait_for(task,20)
        return bench.status(full=True)

    async def test_forty_pages_shared_extraction_chunking_and_translation_export_only_counters(self):
        report=await bench.start('rapide','fixture');self.assertEqual(report['status'],'running')
        result=await self.finish();self.assertEqual(result['status'],'completed',result.get('reason'))
        self.assertEqual(result['pages_done'],40);self.assertEqual(result['fixture']['pages'],40)
        self.assertEqual(result['fixture']['source_words'],9600);self.assertGreater(result['fixture']['bytes'],50000)
        self.assertEqual(result['parts_done'],len(self.calls));self.assertEqual(len(result['page_timings']),40)
        self.assertTrue(all(row['complete'] for row in result['page_timings']))
        self.assertGreater(result['source_words_per_minute'],0);self.assertTrue(result['samples'])
        self.assertEqual(result['parts'][0]['metrics']['runtime_after']['running']['context_length'],16384)
        self.assertNotIn('parts',bench.status());self.assertNotIn('samples',bench.status())
        exported=json.dumps(result)
        for forbidden in ('DO_NOT_EXPORT_PRIVATE','narrator visits','source_text','translated','source.pdf'):self.assertNotIn(forbidden,exported)
        with store.connect() as db:
            for table in ('translations','conversations','messages','translation_parts'):self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertTrue((bench.directory(result['id'])/'source.pdf').exists());self.assertFalse(result['settings']['published'])

    async def test_pause_resume_retains_finished_pages_and_measures_each_session(self):
        async def delayed(text,mode,**kwargs):
            if self.calls:self.started.set();await asyncio.Event().wait()
            return await self.translated(text,mode,**kwargs)
        translations.translate=delayed
        await bench.start('rapide','fixture');await asyncio.wait_for(self.started.wait(),10)
        result=await bench.pause();self.assertEqual(result['status'],'paused');self.assertEqual(result['parts_done'],1)
        translations.translate=self.translated;await bench.resume();done=await self.finish()
        self.assertEqual(done['status'],'completed');self.assertEqual(len(done['sessions']),2)
        self.assertEqual(len(self.calls),done['fixture']['parts'])
        self.assertTrue(any(row['status']=='interrupted' for row in done['parts']))

    async def test_quality_error_keeps_rejected_candidate_private_without_publication(self):
        async def bad(text,mode,**kwargs):return 'Valeur ajoutée 99999999 unités.','bad-model'
        translations.translate=bad
        await bench.start('rapide','fixture');result=await self.finish()
        self.assertEqual(result['status'],'paused');self.assertEqual(result['reason'],'quality_blocked');self.assertEqual(result['parts_done'],0)
        self.assertEqual(result['parts'][0]['quality']['status'],'blocked')
        work=bench.work(result);self.assertIn('99999999',work[0]['rejected'][0]['candidate'])
        self.assertNotIn('99999999',json.dumps(result))

    async def test_restart_waits_for_explicit_resume_and_detects_changed_pdf(self):
        self.mock(bench,'launch',lambda report:None)
        report=await bench.start('rapide','fixture');self.assertEqual(report['status'],'paused');self.assertEqual(report['reason'],'service_restarted')
        parts,fixture=bench.prepare(report['id']);saved=bench.load();saved['fixture']=fixture;bench.save(saved)
        path=bench.directory(report['id'])/'source.pdf';path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaises(ValueError):bench.work(bench.load())
        self.assertEqual(self.calls,[])

    async def test_mode_game_prevents_launch_and_cancels_an_in_flight_call(self):
        self.paused=True
        with self.assertRaises(HTTPException):await bench.start('rapide','fixture')
        self.paused=False
        async def waiting(text,mode,**kwargs):self.started.set();await asyncio.Event().wait()
        translations.translate=waiting
        await bench.start('rapide','fixture');await asyncio.wait_for(self.started.wait(),10);self.paused=True
        result=await self.finish();self.assertEqual(result['reason'],'paused');self.assertFalse(engine.LOCK.locked())

    async def test_api_read_only_until_explicit_start_and_family_only(self):
        from pilot import app as gateway
        role={'id':'fixture','role':'reader'}
        async def user():return role
        gateway.app.dependency_overrides[gateway.user]=user;self.addCleanup(gateway.app.dependency_overrides.clear)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/admin/translation-benchmark')).status_code,403)
            role['role']='admin';result=(await client.get('/api/admin/translation-benchmark/report')).json()
            self.assertEqual(result['status'],'not_started');self.assertEqual(self.calls,[])
            self.assertEqual((await client.post('/api/admin/translation-benchmark/start',json={'mode':'missing'})).status_code,400)


if __name__=='__main__':unittest.main()
