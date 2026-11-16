"""One campaign, fake model/host only. No corpus, stress or inference downloads."""
import asyncio
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import assistant_metrics,engine,library,model_runtime,operations,performance as perf,store,translations


class Found(list):coverage={'status':'partial','searched':2,'failed':1,'processing':{'thread_cpu_ms':4},'private':'do-not-export'}


class PerformanceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.calls=[];self.pause=False;self.fail=False;self.hang=False;self.started=asyncio.Event()
        for module,key,value in [(store,'ROOT',Path(temp.name)),(perf,'ACTIVE',{}),(perf,'REPORTS',{}),(perf,'INTERVAL',.01),(perf,'BASELINE',.01),
                                 (engine,'LOCK',asyncio.Semaphore(1)),(engine,'ACTIVE',{}),(translations,'ACTIVE',{}),(engine,'MEASUREMENTS',{})]:
            self.mock(module,key,value)
        store.init()
        self.mock(perf.calibration,'running',lambda:False);self.mock(perf.calibration,'summary_activity',lambda:False)
        self.mock(perf,'competing',lambda:bool(engine.ACTIVE or translations.ACTIVE))
        self.mock(operations,'status',AsyncMock(side_effect=lambda **kw:{'online':True,'paused':self.pause}))
        self.mock(operations,'performance',AsyncMock(return_value={'available':False,'reason':'controller_update_required'}))
        self.mock(model_runtime,'describe',AsyncMock(return_value={'available':True,'installed':True,'native_context':8192,'model':engine.MODES['rapide']['model'],'running':None,'other_models':0}))
        async def search(query,**kw):
            self.calls.append(query);await kw['on_update']([{'id':'private-id'}])
            return Found([{'id':'private-id','text':'private secret document'}])
        self.mock(library,'search',search)
        async def run(job,user,conversation,mode,**kw):
            if self.hang:self.started.set();await asyncio.Event().wait()
            measured=assistant_metrics.Measurement(job,'model',mode,8192)
            measured.value.update(documentary={'schema':1,'status':'partial','scope':'library','searches':1,'results':2,'sources_read':1,'failed_reads':0,'partial_reads':1})
            measured.finish('done')
            with store.connect() as db:db.execute("UPDATE jobs SET status='done',answer='PRIVATE answer from documents' WHERE id=?",(job,))
        self.mock(engine,'run',run)
        original=httpx.AsyncClient
        async def handler(request):
            self.calls.append(request.url.path)
            payload=json.loads(request.content)
            self.assertEqual(payload['options']['num_predict'],512)
            self.assertNotIn('tools',payload);self.assertNotEqual(payload.get('keep_alive'),0)
            if self.hang:self.started.set();await asyncio.Event().wait()
            if self.fail:return httpx.Response(200,content=b'{"error":"out of memory"}\n')
            return httpx.Response(200,content=json.dumps({'done':True,'done_reason':'stop','message':{'content':'PRIVATE synthetic answer'},'load_duration':1000000,'eval_duration':2000000,'eval_count':3}).encode()+b'\n')
        self.mock(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))

    def mock(self,target,key,value):
        p=patch.object(target,key,value);p.start();self.addCleanup(p.stop)

    async def finish(self):
        report=await perf.start('rapide','family','fixture')
        await asyncio.wait_for(perf.ACTIVE[report['id']],5)
        return perf.status(full=True)

    async def test_full_campaign_separates_repeats_exports_no_private_text_and_cleans_jobs(self):
        report=await self.finish()
        self.assertEqual(report['status'],'completed',report)
        self.assertEqual(report['reason'],'completed')
        self.assertEqual([r['kind'] for r in report['steps']],['classical']*6+['generation']*2+['documentary']*2+['selected_documentary'])
        self.assertEqual(self.calls[:6],[q for q in perf.QUERIES for _ in (1,2)])
        self.assertTrue(report['samples']);self.assertEqual(report['samples'][0]['reason'],'controller_update_required')
        raw=json.dumps(report)
        for forbidden in ('PRIVATE','private-id','private secret','do-not-export','_monotonic','_job'):self.assertNotIn(forbidden,raw)
        with store.connect() as db:
            for table in ('conversations','jobs','messages'):self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
            self.assertIsNone(db.execute("SELECT value FROM settings WHERE key LIKE 'context:%'").fetchone())
        self.assertEqual(perf.status()['sample_count'],len(report['samples']));self.assertNotIn('samples',perf.status())

    async def test_pause_runs_classical_but_never_contacts_model(self):
        self.pause=True;report=await self.finish()
        self.assertEqual(len(report['steps']),11)
        self.assertTrue(all(r['status']=='not_run' and r['reason']=='paused' for r in report['steps'][6:]))
        self.assertNotIn('/api/chat',self.calls)

    async def test_model_memory_failure_kept_and_does_not_abort_classical_report(self):
        self.fail=True;report=await self.finish()
        self.assertEqual(report['status'],'completed')
        self.assertEqual(report['reason'],'completed_with_gaps')
        self.assertEqual(report['steps'][6]['reason'],'memory_error')
        self.assertEqual(report['steps'][6]['status'],'failed')

    async def test_cancel_in_flight_keeps_completed_steps_and_releases_lock(self):
        self.hang=True;report=await perf.start('rapide','family','fixture');await asyncio.wait_for(self.started.wait(),3)
        result=await perf.cancel()
        self.assertEqual(result['status'],'cancelled');self.assertEqual(len(result['steps']),7)
        self.assertFalse(engine.LOCK.locked());self.assertFalse(perf.running())
        self.assertTrue(all(r['status']=='completed' for r in result['steps'][:6]))

    async def test_immediate_cancel_and_restart_are_explicit(self):
        await perf.start('rapide','family','fixture');result=await perf.cancel(reason='service_restarted')
        self.assertEqual(result['status'],'cancelled');self.assertEqual(result['reason'],'service_restarted')
        self.assertFalse(perf.running());self.assertFalse(perf.REPORTS)
        value=perf.load();value['status']='running';perf.save(value)
        self.assertEqual(perf.status()['status'],'interrupted')

    async def test_only_one_campaign_and_existing_activity_has_priority(self):
        engine.ACTIVE['existing']=object()
        with self.assertRaises(HTTPException) as caught:await perf.start('rapide','family','fixture')
        self.assertEqual(caught.exception.status_code,409)
        engine.ACTIVE.clear();await perf.start('rapide','family','fixture')
        with self.assertRaises(HTTPException):await perf.start('rapide','family','fixture')
        await perf.cancel()

    async def test_api_is_admin_only_and_opening_or_exporting_does_not_start_a_test(self):
        from pilot import app as gateway
        role={'id':'family','role':'reader'}
        async def user():return role
        gateway.app.dependency_overrides[gateway.user]=user
        self.addCleanup(gateway.app.dependency_overrides.clear)
        # Bypass the model MockTransport: exercise the actual ASGI routing.
        # HTTPX's client class remains available on its implementation module.
        from httpx._client import AsyncClient
        async with AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/admin/performance')).status_code,403)
            role['role']='admin'
            self.assertEqual((await client.get('/api/admin/performance')).json()['status'],'not_started')
            self.assertEqual((await client.get('/api/admin/performance/report')).json()['status'],'not_started')
            self.assertFalse(perf.running());self.assertEqual(self.calls,[])
            response=await client.post('/api/admin/performance/start',json={'mode':'rapide'})
            self.assertEqual(response.status_code,202,response.text)
            await perf.cancel()

    def test_interpretation_requires_analysis_even_with_full_cpu_disk_and_vram(self):
        report={'steps':[{'id':'search-1','kind':'classical'}],'samples':[{'available':True,'step':'search-1','cpu':{'max_core_percent':100},'disks':[{'data_disk':True,'busy_percent':100}],'gpus':[{'total':8,'used':8}]}]}
        result=perf.interpretation(report)
        self.assertEqual(result['causal_conclusion'],'needs_analysis')
        self.assertEqual(len(result['observations']),2)
        self.assertNotIn('vram',json.dumps(result))
