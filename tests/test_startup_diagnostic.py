"""Refusals and read-only probes on fake HTTP; never starts an engine/model."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx
from fastapi import HTTPException
from pilot import engine,operations,startup_diagnostic as diagnostic,store


class StartupDiagnosticTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        p=patch.object(store,'ROOT',Path(temp.name));p.start();self.addCleanup(p.stop)
        store.init()
        self.model=engine.MODES['rapide']['model'];self.calls=[]
        state={'online':False,'paused':False,'control_available':True,'operation':'start','memory':{'total':32*1024**3,'available':6*1024**3},'error':'PRIVATE SECRET','last_engine_action':{'status':'failed','action':'start','stage':'waiting_for_api','error_kind':'SetupError','elapsed_ms':45001,'raw':'PRIVATE PATH'}}
        p=patch.object(operations,'status',AsyncMock(return_value=state));p.start();self.addCleanup(p.stop)
        original=httpx.AsyncClient
        async def handler(request):
            self.calls.append((request.method,request.url.path))
            if request.url.path=='/api/version':return httpx.Response(200,json={'version':'0.40.16','secret':'PRIVATE SECRET'})
            if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':self.model,'size':1000,'private':'PRIVATE PATH'},{'name':'OTHER PRIVATE MODEL'}]})
            if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[{'name':self.model,'context_length':32768,'size':1200,'size_vram':500,'details':'PRIVATE SECRET'}]})
            raise AssertionError(request.url)
        p=patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=httpx.MockTransport(handler),**kw));p.start();self.addCleanup(p.stop)

    async def test_readonly_snapshot_separates_controller_and_direct_engine(self):
        report=await diagnostic.report('fixture','rapide')
        self.assertFalse(report['current']['controller']['online'])
        self.assertEqual(report['current']['ollama']['version']['state'],'responding')
        self.assertTrue(report['current']['ollama']['installed']['selected_present'])
        self.assertEqual(report['current']['ollama']['running']['selected']['context_length'],32768)
        self.assertEqual({path for method,path in self.calls},{'/api/version','/api/ps','/api/tags'})
        self.assertTrue(all(method=='GET' for method,path in self.calls))
        raw=json.dumps(report);self.assertNotIn('PRIVATE',raw);self.assertNotIn(engine.OLLAMA,raw)
        self.assertFalse(report['current']['model_loaded_by_this_check']);operations.status.assert_awaited_once_with(fresh=True)

    async def test_refusal_is_preserved_bounded_and_never_changes_the_response(self):
        for _ in range(22):
            error=HTTPException(409,'Private refused detail')
            with self.assertRaises(HTTPException) as caught:
                async with diagnostic.observe('calibration','rapide','fixture'):raise error
            self.assertIs(caught.exception,error)
        rows=diagnostic.history();self.assertEqual(len(rows),20)
        self.assertTrue(all(r['phase']=='refused_before_start' and r['http_status']==409 for r in rows))
        self.assertNotIn('Private refused',diagnostic.location().read_text())
        self.assertEqual(rows[-1]['observed']['controller']['last_engine_action']['stage'],'waiting_for_api')
        self.assertEqual(diagnostic.location().stat().st_mode&0o777,0o600)

    async def test_success_and_invalid_mode_never_collect_or_create_an_attempt(self):
        async with diagnostic.observe('calibration','rapide','fixture'):pass
        with self.assertRaises(HTTPException):
            async with diagnostic.observe('calibration','arbitrary private model','fixture'):raise HTTPException(409,'no')
        self.assertEqual(self.calls,[]);self.assertFalse(diagnostic.location().exists())

    async def test_optional_failure_cannot_mask_the_original_refusal(self):
        error=HTTPException(503,'original failure')
        with patch.object(diagnostic,'snapshot',AsyncMock(side_effect=OSError('PRIVATE PATH'))):
            with self.assertRaises(HTTPException) as caught:
                async with diagnostic.observe('performance','rapide','fixture'):raise error
        self.assertIs(caught.exception,error)

    async def test_unreachable_api_and_unknown_mode_are_explicit(self):
        def offline(request):raise httpx.ConnectError('PRIVATE HOST')
        # Restore constructor before installing the alternate mock.
        from httpx import _client
        with patch.object(httpx,'AsyncClient',side_effect=lambda **kw:_client.AsyncClient(transport=httpx.MockTransport(offline),**kw)):
            report=await diagnostic.report('fixture','not-an-installed-profile')
        self.assertIsNone(report['model']);self.assertTrue(all(r['state']=='connection_error' for r in report['current']['ollama'].values()))
        self.assertNotIn('PRIVATE',json.dumps(report))
