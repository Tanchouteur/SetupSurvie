"""Translation lifecycle on simulated local HTTP; no model, GPU or real manual."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx
from pilot import engine,model_runtime,operations,store,translations


class TranslationRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        setting=patch.object(store,'ROOT',Path(self.temp.name));setting.start();self.addCleanup(setting.stop);store.init()

    async def exercise(self,*,context=32768,native=16384,switch=False,empty=False,paused=False):
        requests=[];measures=[];real=httpx.AsyncClient;model=engine.MODES['rapide']['model']
        with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',('context:'+model,str(context)))
        def handler(request):
            if request.url.path=='/api/version':return httpx.Response(200,json={'version':'0.40.13'})
            if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':model,'digest':'a'*64}]})
            if request.url.path=='/api/show':return httpx.Response(200,json={'model_info':{'fixture.context_length':native}})
            if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[{'name':'other:local','context_length':8192}] if switch else []})
            payload=json.loads(request.content);requests.append(payload)
            if not payload['messages']:return httpx.Response(200,json={'done':True,'done_reason':'load'})
            if empty and len([row for row in requests if row['messages']])==1:event={'done':True,'done_reason':'load'}
            else:event={'message':{'content':json.dumps({'status':'translated','translation':'Le cadran fictif comporte 7 repères.'})},'done':True,'done_reason':'stop'}
            return httpx.Response(200,content=(json.dumps(event)+'\n').encode())
        with patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':paused,'message':'Mode jeu'})),\
             patch.object(translations.httpx,'AsyncClient',side_effect=lambda **kw:real(transport=httpx.MockTransport(handler),**kw)):
            result=await translations.translate('The fictional dial has 7 marks.','rapide',on_metrics=measures.append)
        return result,requests,measures[0]

    async def test_switch_prepares_target_before_translation_and_respects_native_context(self):
        result,requests,measure=await self.exercise(switch=True)
        self.assertIn('7',result[0]);self.assertEqual(requests[0]['messages'],[])
        self.assertEqual(requests[1]['messages'][-1]['content'],'The fictional dial has 7 marks.')
        self.assertTrue(all(row['options']['num_ctx']==16384 for row in requests))
        self.assertEqual(measure['requested_context'],32768);self.assertEqual(measure['context'],16384)
        self.assertTrue(measure['context_limited']);self.assertEqual(measure['model_preparations'][0]['status'],'ready')
        self.assertNotIn('fictional',json.dumps(measure))

    async def test_empty_acknowledgment_retries_the_same_fragment_once(self):
        _,requests,measure=await self.exercise(empty=True)
        self.assertEqual(requests[0],requests[1]);self.assertEqual(len(measure['model_retries']),1)

    async def test_pause_prevents_metadata_load_and_translation(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):await self.exercise(paused=True)

    async def test_context_too_small_does_not_truncate_source_or_start_model(self):
        with patch.object(operations,'status',AsyncMock(return_value={'online':True})),\
             patch.object(model_runtime,'describe',AsyncMock(return_value={'available':False,'native_context':256})),\
             patch.object(translations.httpx,'AsyncClient') as client:
            with self.assertRaisesRegex(ValueError,'dépasse le contexte'):await translations.translate('A fictional source. '*100,'rapide')
            client.assert_not_called()
