"""Durable complete reading on tiny fictional sources; no actual inference."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from pilot import document_text,engine,library,operations,store,summaries as sm
import test_translations as translation_fixture


async def fictional_infer(item,messages,*,schema=None,output=None):
    data=json.loads(messages[-1]['content'])
    if 'units' in data:
        for unit in data['units']:
            if 'LAST FACT' in unit['text']:unit['text']=unit['text'][unit['text'].index('LAST FACT'):]
        return {'notes':[{'unit':unit['position'],'quote':unit['text'].strip()[:100],
            'text':unit['text'].strip()[:100]} for unit in data['units']]},'fake-model'
    if 'fragments' in data:return {'citations':[]},'fake-model'
    if 'sources' in data:return 'Fait fictif documenté [1].','fake-model'
    return {'notes':[{'text':child['text'][:1500],
        'supports':[child['id']]} for child in data['notes'][:8]]},'fake-model'


class SummaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await translation_fixture.TranslationTests.asyncSetUp(self)
        p=patch.object(engine,'POLICY',__import__('pathlib').Path(__file__).resolve().parents[1]/'deploy/assistant-system.fr.txt');p.start();self.addCleanup(p.stop)

    async def asyncTearDown(self):
        await sm.stop_all();sm.ACTIVE.clear()

    async def create(self,ids=None):
        with patch.object(sm,'launch'):
            return await sm.create('alice','Compare les faits fictifs','rapide','c',ids or [self.source])

    async def complete(self,item):
        with patch.object(sm,'infer',fictional_infer):await sm.run(item['id'])
        return sm.status(item['id'],'alice')

    async def test_complete_snapshot_and_notes_are_private_durable_and_idempotent(self):
        item=await self.create();state=await self.complete(item)
        self.assertNotEqual(item['conversation_id'],'c')
        self.assertEqual(state['status'],'completed',state.get('error'))
        self.assertEqual(state['read'],state['total']);self.assertGreater(state['read'],1)
        text=sm.export(item['id'],'alice');self.assertIn('Keep water clean',text)
        self.assertIn('non vérifiée',text);self.assertIn('empreinte',text)
        store.init();await sm.run(item['id'])
        self.assertEqual(len(store.messages(item['conversation_id'])),2)
        with self.assertRaises(HTTPException):sm.export(item['id'],'bob')
        with store.connect() as db:db.execute('DELETE FROM conversations WHERE id=?',(item['conversation_id'],))
        with store.connect() as db:
            for table in ('summary_jobs','summary_inputs','summary_parts','summary_nodes'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertTrue((library.GUIDES/'manual.en.txt').exists())

    async def test_late_passages_hierarchical_reduction_keep_source_graph(self):
        (library.GUIDES/'manual.en.txt').write_text(('Fictional ordinary fact. '*100+'\n')*43+'LAST FACT: reference rotor 59.\n')
        library.index_guides();item=await self.create();state=await self.complete(item)
        self.assertEqual(state['status'],'completed',state.get('error'))
        self.assertGreater(state['node_count'],5);self.assertEqual(state['pending'],0)
        self.assertIn('LAST FACT',sm.export(item['id'],'alice'))
        with store.connect() as db:
            nodes=[dict(row) for row in db.execute('SELECT * FROM summary_nodes WHERE summary_id=?',(item['id'],))]
        parents=[node for node in nodes if node['level']>0];self.assertTrue(parents)
        known={node['id'] for node in nodes}
        self.assertTrue(all(set(json.loads(node['children']))<=known for node in parents))
        self.assertTrue(all(note['pages']['1']==[1] for node in parents for note in json.loads(node['result'])))

    async def test_pause_and_resume_keep_finished_notes_and_original_snapshot(self):
        item=await self.create();await sm.snapshot(item)
        with patch.object(sm,'infer',fictional_infer):await sm.step(item)
        before=sm.status(item['id'],'alice');self.assertGreater(before['read'],0)
        sm.update(item['id'],'error','Fictional interruption')
        (library.GUIDES/'manual.en.txt').write_text('CHANGED ORIGINAL must not be mixed in.')
        with patch.object(sm,'launch'):await sm.resume(item['id'],'alice')
        state=await self.complete(item);self.assertEqual(state['status'],'completed',state.get('error'))
        self.assertNotIn('CHANGED ORIGINAL',sm.export(item['id'],'alice'))
        self.assertEqual(state['inputs'][0]['metadata']['sha256'],before['inputs'][0]['metadata']['sha256'])

    async def test_inflight_cancellation_does_not_save_a_partial_stage(self):
        item=await self.create();entered=asyncio.Event()
        async def blocked(*args,**kwargs):entered.set();await asyncio.Event().wait()
        with patch.object(sm,'infer',blocked):
            sm.launch(item['id']);await asyncio.wait_for(entered.wait(),3)
            result=await sm.pause(item['id'],'alice')
        self.assertEqual(result['status'],'paused');self.assertEqual(result['read'],0)
        self.assertEqual(result['node_count'],0)
        with patch.object(sm,'launch'):await sm.resume(item['id'],'alice')
        self.assertEqual((await self.complete(item))['status'],'completed')

    async def test_restart_requires_explicit_resume_and_preserves_notes(self):
        item=await self.create();await sm.snapshot(item)
        with patch.object(sm,'infer',fictional_infer):await sm.step(item)
        before=sm.status(item['id'],'alice');store.init()
        with patch.object(sm,'infer',AsyncMock()) as infer:await sm.run(item['id']);infer.assert_not_awaited()
        state=sm.status(item['id'],'alice');self.assertEqual(state['status'],'paused')
        self.assertEqual(state['node_count'],before['node_count'])

    async def test_game_pause_blocks_create_resume_and_next_stage(self):
        with patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':True})):
            with self.assertRaises(HTTPException):await self.create()
        item=await self.create();sm.update(item['id'],'paused')
        with patch.object(operations,'status',AsyncMock(return_value={'online':False})):
            with self.assertRaises(HTTPException):await sm.resume(item['id'],'alice')
            sm.update(item['id'],'queued')
            with patch.object(sm,'infer',AsyncMock()) as infer:await sm.run(item['id']);infer.assert_not_awaited()
        self.assertEqual(sm.status(item['id'],'alice')['status'],'paused')

    async def test_shared_inference_lock_and_priority_between_stages(self):
        item=await self.create();await sm.snapshot(item);entered=asyncio.Event()
        async def observed(*args,**kwargs):entered.set();return await fictional_infer(*args,**kwargs)
        await engine.LOCK.acquire()
        with patch.object(sm,'infer',observed):
            task=asyncio.create_task(sm.run(item['id']));await asyncio.sleep(.02);self.assertFalse(entered.is_set())
            engine.LOCK.release();await task
        self.assertTrue(entered.is_set())

    async def test_partial_documents_and_blank_pages_are_explicit(self):
        item=await self.create()
        with store.connect() as db:
            db.execute("INSERT INTO summary_inputs(summary_id,number,source_id,title) VALUES(?,2,'guide:missing.txt','Missing')",(item['id'],))
        original=document_text.extract
        async def extraction(*args,**kwargs):
            source,parts=await original(*args,**kwargs);return source,[*parts,(2,'','unreadable')]
        with patch.object(document_text,'extract',extraction):state=await self.complete(item)
        self.assertEqual(state['status'],'completed',state.get('error'))
        self.assertEqual(state['unreadable'],1);self.assertEqual(state['inputs'][1]['status'],'unavailable')
        self.assertIn('Lecture partielle',state['answer']);self.assertIn('1 page(s)',state['answer'])

    async def test_incomplete_citations_can_resume_only_the_final_stage(self):
        item=await self.create()
        async def no_refs(*args,**kwargs):
            result=await fictional_infer(*args,**kwargs)
            return ('Unlinked conclusion','fake') if not kwargs.get('schema') else result
        with patch.object(sm,'infer',no_refs):await sm.run(item['id'])
        state=sm.status(item['id'],'alice');self.assertEqual(state['status'],'incomplete')
        self.assertEqual(len(store.messages(item['conversation_id'])),1)
        before=state['node_count']
        with patch.object(sm,'launch'):await sm.resume(item['id'],'alice')
        state=await self.complete(item);self.assertEqual(state['node_count'],before)
        self.assertEqual(state['status'],'completed')

    async def test_pdf_reads_last_original_page_and_marks_blank_page(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
        writer=PdfWriter()
        for number in range(1,7):
            page=writer.add_blank_page(width=300,height=400)
            if number==2:continue
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
            stream=DecodedStreamObject();stream.set_data(f'BT /F1 12 Tf 20 100 Td (Fictional last-page reference {number}.) Tj ET'.encode());page[NameObject('/Contents')]=stream
        writer.write(library.GUIDES/'late.en.pdf');library.index_guides()
        item=await self.create(['guide:late.en.pdf']);state=await self.complete(item)
        self.assertEqual(state['unreadable'],1);self.assertEqual(state['total'],6)
        self.assertIn('reference 6',sm.export(item['id'],'alice'))
        self.assertEqual(store.messages(item['conversation_id'])[-1]['sources'][0]['pages'],[1,3,4,5,6])
        selected=await self.create(['guide:late.en.pdf#page=6']);state=await self.complete(selected)
        self.assertEqual(state['total'],1);self.assertEqual(state['nodes'][0]['notes'][0]['page'],6)

    def test_quotes_must_belong_to_exact_unit_and_offsets_survive_whitespace(self):
        units=[{'position':0,'source_number':1,'page':9,'offset':200,'text':'Prefix. Reference  59 kg. End.'}]
        notes=sm.leaf_notes({'notes':[{'unit':0,'quote':'Reference 59 kg.','text':'Fait.'}]},units)
        self.assertEqual(notes[0]['offset'],208);self.assertEqual(notes[0]['quote'],'Reference  59 kg.')
        for note in ({'unit':9,'quote':'Reference 59 kg.','text':'Fait.'},{'unit':0,'quote':'Reference 23 kg.','text':'Fait.'}):
            with self.assertRaises(ValueError):sm.leaf_notes({'notes':[note]},units)
        with self.assertRaises(ValueError):sm.merged_notes({'notes':[{'text':'bad','supports':[99]}]},[])

    def test_reduction_references_a_note_in_a_mixed_batch_not_every_source(self):
        children=[{'id':2,'result':json.dumps([{'text':'17 unités','source_number':1,'page':21,'quote':'17 unités'}, {'text':'59 unités','source_number':2,'page':21,'quote':'59 unités'}])}]
        notes=sm.merged_notes({'notes':[{'text':'17 unités','supports':['2:0']}]},children)
        self.assertEqual(notes[0]['source_numbers'],[1]);self.assertEqual(notes[0]['pages'],{'1':[21]})
        parent={'id':3,'result':json.dumps(notes)}
        self.assertEqual(sm.original_notes([parent],[*children,parent])[0]['source_number'],1)
        self.assertEqual(len(sm.original_notes([parent],[*children,parent])),1)

    async def test_all_truncated_or_unreadable_text_is_not_a_complete_summary(self):
        item=await self.create()
        with patch.object(document_text,'extract',AsyncMock(side_effect=HTTPException(413,'Aperçu incomplet'))):state=await self.complete(item)
        self.assertEqual(state['status'],'error');self.assertEqual(state['total'],0)
        self.assertEqual(len(store.messages(item['conversation_id'])),1)
        with patch.object(library,'source',AsyncMock(return_value={'text':'Truncated preview','text_truncated':True})):
            with self.assertRaises(HTTPException):await document_text.extract('zim:book/A/article',purpose='synthèse')


if __name__=='__main__':unittest.main()
