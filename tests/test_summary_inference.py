"""The real model adapter on a simulated HTTP stream, never a live model."""
import json
import unittest
from unittest.mock import AsyncMock,patch
import httpx
import test_translations as translation_fixture
from pilot import engine,model_runtime,operations,summaries


class SummaryInferenceTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=translation_fixture.TranslationTests.asyncSetUp
    async def test_adapter_preserves_context_schema_and_rejects_unfinished_output(self):
        original=httpx.AsyncClient;seen=[];reason='stop'
        async def transport(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200,text=json.dumps({'message':{'content':'{"notes":[]}'},'done':True,'done_reason':reason})+'\n')
        with patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=httpx.MockTransport(transport),**kw)),\
             patch.object(model_runtime,'describe',AsyncMock(return_value={'available':False,'native_context':8192})),\
             patch.object(operations,'status',AsyncMock(return_value={'online':True})):
            schema=summaries.evidence_schema([0])
            result,_=await summaries.infer({'id':'fake','mode':'rapide'},[{'role':'user','content':'Fictional'}],schema=schema)
            self.assertEqual(result,{'notes':[]});self.assertEqual(seen[-1]['options']['num_ctx'],8192)
            self.assertEqual(seen[-1]['format'],schema)
            reason='length'
            with self.assertRaises(ValueError):await summaries.infer({'id':'fake','mode':'rapide'},[{'role':'user','content':'Fictional'}],schema=schema)

    async def test_context_guard_refuses_to_truncate_text_silently(self):
        with patch.object(model_runtime,'describe',AsyncMock(return_value={'available':False,'native_context':512})),patch.object(httpx,'AsyncClient') as client:
            with self.assertRaises(ValueError):await summaries.infer({'id':'fake','mode':'rapide'},[{'role':'user','content':'x'*30000}])
            client.assert_not_called()
