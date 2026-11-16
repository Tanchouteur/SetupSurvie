"""A 500-page tiny synthetic PDF, simulated translation, durable resume/publication."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
from pilot import engine,library,operations,store,translations


class LongTranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_500_pages_are_snapshotted_resumed_and_last_page_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);guides=root/'guides';guides.mkdir();path=guides/'fictional-book.en.pdf'
            writer=PdfWriter()
            for number in range(1,501):
                page=writer.add_blank_page(width=300,height=400)
                page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
                stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td (Fictional page '+str(number)+'. No practical instructions.) Tj ET').encode());page[NameObject('/Contents')]=stream
            writer.write(path)
            with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides),patch.object(engine,'LOCK',asyncio.Semaphore(1)),patch.object(operations,'status',AsyncMock(return_value={'online':True})),patch.object(translations,'launch'):
                store.init();library.index_guides();item=await translations.create('fixture','guide:'+path.name,None,'rapide')
                self.assertEqual(item['total'],500);self.assertEqual(item['pages'],500)
                calls=0
                async def first_pass(text,mode,**kwargs):
                    nonlocal calls
                    calls+=1
                    if calls==8:raise ValueError('Controlled interruption of the synthetic test.')
                    return text.replace('Fictional page','Page fictive').replace('No practical instructions.','Aucun conseil pratique.'),'fixture-one'
                with patch.object(translations,'translate',side_effect=first_pass):await translations.run(item['id'])
                state=translations.status(item['id'],'fixture');self.assertEqual(state['done'],7);self.assertEqual(state['status'],'error')
                first=state['parts'][0]['translated'];store.init()
                # A source replacement must not contaminate the saved snapshot.
                path.write_bytes(b'Replaced fixture, deliberately unreadable.')
                await translations.resume(item['id'],'fixture','moyenne')
                async def remaining(text,mode,**kwargs):
                    self.assertNotIn('Replaced fixture',text)
                    return text.replace('Fictional page','Page fictive').replace('No practical instructions.','Aucun conseil pratique.'),'fixture-two'
                with patch.object(translations,'translate',side_effect=remaining):await translations.run(item['id'])
                state=translations.status(item['id'],'fixture');self.assertEqual(state['done'],500);self.assertEqual(state['status'],'completed')
                self.assertEqual(state['parts'][0]['translated'],first);self.assertEqual(state['parts'][0]['model'],'fixture-one')
                final=translations.status(item['id'],'fixture',490);self.assertEqual(final['parts'][-1]['page'],500);self.assertEqual(final['parts'][-1]['model'],'fixture-two')
                self.assertIn('Page fictive 500.',translations.export(item['id'],'fixture'))
                publication=state['publication']['source_id'];self.assertTrue(publication)
                self.assertIn('Page fictive 500.',(await library.source(publication))['text'])
