"""Controller failure reasons are numeric/categorical and never include credentials."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import httpx
from pilot import operations


class OperationsDiagnosticTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_http_and_bad_json_are_distinct_and_raw_body_is_not_exposed(self):
        client=httpx.AsyncClient
        for kind in ('timeout','http_error','invalid_response'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temporary:
                async def handler(request):
                    if request.url.path!='/status':return httpx.Response(200,json={'version':'fixture'})
                    if kind=='timeout':raise httpx.ReadTimeout('PRIVATE TOKEN AND HOST')
                    if kind=='http_error':return httpx.Response(503,text='PRIVATE TOKEN AND HOST')
                    return httpx.Response(200,json=[])
                with patch.object(operations,'TOKEN','PRIVATE TOKEN'),patch.object(operations,'CACHE',{}),patch.object(operations,'UPDATED',0),patch.object(operations.network,'CATALOG',Path(temporary)),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:client(transport=httpx.MockTransport(handler),**kw)):
                    data=await operations.status(fresh=True)
                self.assertEqual(data['control_error'],kind);self.assertFalse(data['control_available']);self.assertTrue(data['online'])
                self.assertNotIn('PRIVATE',str(data));self.assertIn('control_elapsed_ms',data)
