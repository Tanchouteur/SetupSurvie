import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
from pilot import engine,library,operations,store,translations as tr


class TranslationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);guides=self.root/'guides';guides.mkdir()
        (guides/'manual.en.txt').write_text('Keep water clean.\n'*300)
        for obj,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',guides),
                               (operations,'status',AsyncMock(return_value={'online':True})),(engine,'LOCK',asyncio.Semaphore(1)),(tr,'CONTROL_LOCK',asyncio.Lock())]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        store.init();library.index_guides()
        self.source='guide:manual.en.txt'
        with store.connect() as db:db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','alice','Question',0))

    async def asyncTearDown(self):
        tasks=list(tr.ACTIVE.values())
        for task in tasks:task.cancel()
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)
        tr.ACTIVE.clear()

    async def create(self):
        with patch.object(tr,'launch'):
            return await tr.create('alice',self.source,'c','rapide')

    async def test_chunks_preserve_all_characters_and_bound_requests(self):
        text=('abc\ndef ghi '*500)+'last'
        parts=list(tr.chunks(text))
        self.assertEqual(''.join(parts),text)
        self.assertTrue(all(0<len(p)<=2200 for p in parts))

    async def test_page_progress_keeps_partial_and_unreadable_pages_distinct(self):
        item=await self.create()
        with store.connect() as db:
            db.execute('DELETE FROM translation_parts WHERE translation_id=?',(item['id'],))
            for position,page,status in [(0,1,'done'),(1,1,'pending'),(2,2,'done'),(3,3,'unreadable'),(4,4,'pending')]:
                db.execute('INSERT INTO translation_parts(translation_id,position,page,source_text,translated,status) VALUES(?,?,?,?,?,?)',(item['id'],position,page,'Fictional source','Texte fictif' if status=='done' else '',status))
        data=tr.status(item['id'],'alice')
        self.assertEqual((data['pages'],data['pages_done'],data['pages_partial'],data['pages_unreadable']),(4,1,1,1))
        self.assertEqual(data['current_page'],1);self.assertEqual(data['last_done_position'],2)
        with store.connect() as db:db.execute("UPDATE translation_parts SET status='done',translated='Suite fictive' WHERE translation_id=? AND position=1",(item['id'],))
        data=tr.status(item['id'],'alice')
        self.assertEqual(data['pages_done'],2);self.assertEqual(data['pages_partial'],0);self.assertEqual(data['current_page'],4)
        with self.assertRaises(HTTPException):tr.status(item['id'],'bob')

    async def test_completion_is_private_saved_and_exportable_after_restart(self):
        item=await self.create()
        self.assertEqual(store.conversation_source('c')['id'],self.source)
        with patch.object(tr,'translate',AsyncMock(return_value=('Eau propre.','tiny-fixture'))):await tr.run(item['id'])
        state=tr.status(item['id'],'alice')
        self.assertEqual(state['status'],'completed');self.assertEqual(state['done'],state['total'])
        store.init()
        self.assertIn('Eau propre.',tr.export(item['id'],'alice'))
        self.assertIn('non vérifiée',tr.export(item['id'],'alice'))
        with self.assertRaises(HTTPException):tr.export(item['id'],'bob')

    async def test_error_then_resume_uses_saved_snapshot_and_keeps_finished_parts(self):
        item=await self.create();calls=0
        async def fail_second(text,mode,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:raise ValueError('Refus test : essayez un autre mode.')
            return 'Premier passage traduit.','model-one'
        with patch.object(tr,'translate',side_effect=fail_second):await tr.run(item['id'])
        state=tr.status(item['id'],'alice');self.assertEqual(state['status'],'error');self.assertEqual(state['done'],1)
        (library.GUIDES/'manual.en.txt').write_text('Changed original must not replace the snapshot.')
        with patch.object(tr,'launch'):await tr.resume(item['id'],'alice','moyenne')
        with patch.object(tr,'translate',AsyncMock(return_value=('Suite traduite.','model-two'))) as translate:await tr.run(item['id'])
        self.assertNotIn('Changed original',translate.call_args.args[0])
        state=tr.status(item['id'],'alice');self.assertEqual(state['done'],state['total'])
        self.assertEqual(state['parts'][0]['model'],'model-one')
        self.assertEqual(state['parts'][1]['model'],'model-two')

    async def test_pause_cancels_inflight_fragment_and_preserves_previous_translation(self):
        item=await self.create();started=asyncio.Event()
        async def wait(text,mode,**kwargs):started.set();await asyncio.Event().wait()
        with patch.object(tr,'translate',side_effect=wait):
            tr.launch(item['id']);await asyncio.wait_for(started.wait(),1)
            state=await tr.pause(item['id'],'alice')
        self.assertEqual(state['status'],'paused');self.assertEqual(state['done'],0)
        self.assertNotIn(item['id'],tr.ACTIVE)
        store.init();self.assertEqual(tr.status(item['id'],'alice')['status'],'paused')

    async def test_stop_preserves_done_parts_and_resumes_only_explicitly(self):
        item=await self.create();started=asyncio.Event();calls=0
        async def translate(text,mode,**kwargs):
            nonlocal calls
            calls+=1
            if calls==1:return 'Eau propre.','fixture'
            started.set();await asyncio.Event().wait()
        with patch.object(tr,'translate',side_effect=translate):
            tr.launch(item['id']);await asyncio.wait_for(started.wait(),2)
            stopped=await tr.stop(item['id'],'alice')
        self.assertEqual(stopped['status'],'stopped');self.assertEqual(stopped['done'],1)
        self.assertNotIn(item['id'],tr.ACTIVE);store.init()
        self.assertEqual(tr.status(item['id'],'alice')['status'],'stopped')
        with patch.object(tr,'launch') as launch:
            resumed=await tr.resume(item['id'],'alice')
            self.assertEqual(resumed['status'],'queued');launch.assert_called_once_with(item['id'])
        self.assertEqual(tr.status(item['id'],'alice')['parts'][0]['translated'],'Eau propre.')

    async def test_delete_joins_worker_and_removes_only_owned_private_work(self):
        item=await self.create();started=asyncio.Event();finished=asyncio.Event()
        from pilot import publications
        with store.connect() as db:publications.reserve(db,item['id'],'alice',{'id':self.source,'title':'Private draft metadata'},True)
        async def wait(text,mode,**kwargs):
            started.set()
            try:await asyncio.Event().wait()
            finally:finished.set()
        with patch.object(tr,'translate',side_effect=wait):
            tr.launch(item['id']);await asyncio.wait_for(started.wait(),2)
            with self.assertRaises(HTTPException):await tr.delete(item['id'],'bob')
            result=await tr.delete(item['id'],'alice')
        self.assertTrue(result['deleted']);self.assertTrue(finished.is_set());self.assertNotIn(item['id'],tr.ACTIVE)
        self.assertTrue((library.GUIDES/'manual.en.txt').is_file())
        with self.assertRaises(HTTPException):tr.status(item['id'],'alice')
        with store.connect() as db:
            for table in ('translations','translation_parts','translation_checks'):
                column='id' if table=='translations' else 'translation_id'
                self.assertEqual(db.execute('SELECT count(*) FROM '+table+' WHERE '+column+'=?',(item['id'],)).fetchone()[0],0)
            self.assertFalse(db.execute('SELECT 1 FROM settings WHERE key=?',('auto-translation:'+item['id'],)).fetchone())
            self.assertFalse(db.execute('SELECT 1 FROM translation_publications WHERE translation_id=?',(item['id'],)).fetchone())
            self.assertTrue(db.execute('SELECT 1 FROM conversations WHERE id=?',('c',)).fetchone())

    async def test_delete_keeps_an_already_published_translation(self):
        from pilot import publications
        item=await self.create()
        with patch.object(tr,'translate',AsyncMock(return_value=('Eau propre.','fixture'))):await tr.run(item['id'])
        public=publications.state(item['id'])
        self.assertTrue(public['source_id'])
        path=library.GUIDES/public['source_id'][6:];before=path.read_bytes()
        result=await tr.delete(item['id'],'alice')
        self.assertEqual(result['publication']['source_id'],public['source_id']);self.assertEqual(path.read_bytes(),before)
        self.assertTrue((await library.source(public['source_id']))['text'])

    async def test_resume_cannot_recreate_work_while_deletion_joins_its_worker(self):
        item=await self.create();started=asyncio.Event();cancelling=asyncio.Event();release=asyncio.Event()
        async def translate(text,mode,**kwargs):
            started.set()
            try:await asyncio.Event().wait()
            finally:cancelling.set();await release.wait()
        with patch.object(tr,'translate',side_effect=translate):
            tr.launch(item['id']);await asyncio.wait_for(started.wait(),2)
            deleting=asyncio.create_task(tr.delete(item['id'],'alice'));await asyncio.wait_for(cancelling.wait(),2)
            resuming=asyncio.create_task(tr.resume(item['id'],'alice'));await asyncio.sleep(.01)
            self.assertFalse(deleting.done());self.assertFalse(resuming.done())
            release.set();await asyncio.wait_for(deleting,2)
            with self.assertRaises(HTTPException) as error:await resuming
            self.assertEqual(error.exception.status_code,404);self.assertNotIn(item['id'],tr.ACTIVE)

    async def test_restart_pauses_and_does_not_resume_inference_automatically(self):
        item=await self.create();store.init()
        state=tr.status(item['id'],'alice');self.assertEqual(state['status'],'paused')
        self.assertIn('redémarré',state['error'])

    async def test_game_pause_blocks_start_resume_and_next_fragment(self):
        paused={'online':False,'paused':True,'message':'Mode jeu'}
        with patch.object(operations,'status',AsyncMock(return_value=paused)),patch.object(tr,'launch') as launch:
            with self.assertRaises(HTTPException):await tr.create('alice',self.source,'c','rapide')
            launch.assert_not_called()
        item=await self.create()
        with patch.object(operations,'status',AsyncMock(side_effect=[{'online':True},paused])),patch.object(tr,'translate',AsyncMock(return_value=('Traduit','tiny'))) as translate:
            await tr.run(item['id'])
        self.assertEqual(translate.await_count,1)
        self.assertEqual(tr.status(item['id'],'alice')['status'],'paused')
        with patch.object(operations,'status',AsyncMock(return_value=paused)),patch.object(tr,'launch') as launch:
            with self.assertRaises(HTTPException):await tr.resume(item['id'],'alice')
            launch.assert_not_called()

    async def test_pause_detected_during_fragment_preparation_is_still_a_pause(self):
        item=await self.create()
        with patch.object(tr,'translate',AsyncMock(side_effect=HTTPException(503,'Mode jeu : reprendre volontairement.'))):await tr.run(item['id'])
        state=tr.status(item['id'],'alice');self.assertEqual(state['status'],'paused');self.assertEqual(state['done'],0)

    async def test_other_accounts_cannot_start_on_or_resume_another_conversation(self):
        with self.assertRaises(HTTPException):await tr.create('bob',self.source,'c','rapide')
        item=await self.create()
        with self.assertRaises(HTTPException):await tr.pause(item['id'],'bob')
        with self.assertRaises(HTTPException):await tr.resume(item['id'],'bob')

    async def test_pdf_uses_all_original_pages_and_marks_blank_pages(self):
        writer=PdfWriter()
        for text in ['First water page','','Middle page three','Middle page four','Middle page five','Last shelter page']:
            page=writer.add_blank_page(width=300,height=400)
            if text:
                page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
                stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+text+') Tj ET').encode());page[NameObject('/Contents')]=stream
        writer.write(library.GUIDES/'six.en.pdf');library.index_guides()
        source,parts=await tr.extract('guide:six.en.pdf#page=3')
        self.assertEqual(source['id'],'guide:six.en.pdf')
        self.assertEqual([p[0] for p in parts],[1,2,3,4,5,6])
        self.assertEqual(parts[1][2],'unreadable');self.assertIn('Last shelter',parts[5][1])
        _,subset=await tr.extract(source['id'],3,5)
        self.assertEqual([p[0] for p in subset],[3,4,5])
        with self.assertRaises(HTTPException):await tr.extract(source['id'],1,10)
        self.source=source['id'];item=await self.create()
        with patch.object(tr,'translate',AsyncMock(return_value=('Texte français','tiny'))):await tr.run(item['id'])
        state=tr.status(item['id'],'alice')
        self.assertEqual(state['done'],5);self.assertEqual(state['unreadable'],1)
        self.assertIn('OCR nécessaire',tr.export(item['id'],'alice'))

    async def test_inference_shares_chat_lock(self):
        item=await self.create();await engine.LOCK.acquire()
        with patch.object(tr,'translate',AsyncMock(return_value=('Texte','tiny'))) as translate:
            tr.launch(item['id']);await asyncio.sleep(.01);translate.assert_not_awaited()
            engine.LOCK.release();await tr.ACTIVE[item['id']]
        self.assertEqual(tr.status(item['id'],'alice')['status'],'completed')

    async def test_ollama_schema_and_refusal_or_truncation_are_not_accepted(self):
        real_client=httpx.AsyncClient
        cases=[({'status':'translated','translation':'Texte français.'},'stop',True),
               ({'status':'refused','translation':''},'stop',False),
               ({'status':'translated','translation':'Partial'},'length',False),
               ({'status':'translated','translation':"I’m sorry, but I cannot help."},'stop',False)]
        for result,reason,ok in cases:
            def handler(request):
                payload=json.loads(request.content)
                self.assertEqual(payload['format'],tr.SCHEMA)
                self.assertEqual(payload['messages'][1],{'role':'user','content':'Water source text'})
                event={'message':{'content':json.dumps(result)},'done':True,'done_reason':reason}
                return httpx.Response(200,content=(json.dumps(event)+'\n').encode())
            with patch.object(tr.model_runtime,'describe',AsyncMock(return_value={'available':False,'native_context':None})),patch.object(tr.httpx,'AsyncClient',side_effect=lambda **kw:real_client(transport=httpx.MockTransport(handler),**kw)):
                if ok:self.assertEqual((await tr.translate('Water source text','rapide'))[0],'Texte français.')
                else:
                    with self.assertRaises(ValueError):await tr.translate('Water source text','rapide')


if __name__=='__main__':unittest.main()


class PublicationCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_publication_joins_its_filesystem_thread(self):
        import threading
        from pilot import publications
        entered=threading.Event();release=threading.Event();finished=threading.Event()
        def writer(*args):
            entered.set()
            try:release.wait(3)
            finally:finished.set()
            return {'source_id':'guide:fixture'}
        with patch.object(publications,'LOCK',asyncio.Lock()),patch.object(publications,'_publish',side_effect=writer):
            task=asyncio.create_task(publications.publish('fixture','alice'))
            self.assertTrue(await asyncio.to_thread(entered.wait,1));task.cancel()
            await asyncio.sleep(.02)
            self.assertFalse(task.done());self.assertTrue(publications.LOCK.locked())
            release.set()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertTrue(finished.is_set());self.assertFalse(publications.LOCK.locked())
