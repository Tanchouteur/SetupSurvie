import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
from pilot import engine,library,store


class LibraryPageTests(unittest.TestCase):
    def test_french_query_retrieves_english_passage_and_blank_pdf_needs_ocr(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);guides=base/'guides';guides.mkdir()
            (guides/'seeds.en.txt').write_text('Seed storage: keep seeds dry. Check storage conditions.')
            (guides/'doctor.en.txt').write_text('Where There Is No Doctor. How to examine a sick person.')
            writer=PdfWriter();writer.add_blank_page(width=300,height=400);writer.write(guides/'scanned.fr.pdf')
            with patch.object(store,'ROOT',base/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])):
                store.init();library.index_guides()
                found=asyncio.run(library.search('Comment stocker les graines ?'))
                self.assertEqual(found[0]['id'],'guide:seeds.en.txt')
                doctor=asyncio.run(library.search('examiner personne malade'))
                self.assertEqual(doctor[0]['id'],'guide:doctor.en.txt')
                report=library.index_report()
                self.assertEqual(next(r for r in report['documents'] if r['path']=='scanned.fr.pdf')['status'],'needs_ocr')
                self.assertEqual(report['indexed'],2)

    def test_search_reaches_last_pdf_page_and_links_illustrated_original(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);guides=base/'guides';guides.mkdir()
            writer=PdfWriter()
            for text in ['Introduction']*5+['Roof shelter useful construction details']:
                page=writer.add_blank_page(width=300,height=400)
                page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
                stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+text+') Tj ET').encode())
                page[NameObject('/Contents')]=stream
            writer.write(guides/'shelter.en.pdf')
            (guides/'metadata.json').write_text(json.dumps([{'path':'shelter.en.pdf','title':'Practical construction','language':'en','provenance':'Test fixture','licence':'Test'}]))
            with patch.object(store,'ROOT',base/'state'),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[])):
                store.init();self.assertEqual(library.index_guides(),1)
                found=asyncio.run(library.search("sort moi un document sur comment faire un toit d'un abri efficacement"))
                self.assertEqual(found[0]['id'],'guide:shelter.en.pdf#page=6')
                source=asyncio.run(library.source(found[0]['id']))
                self.assertTrue(source['preview']);self.assertTrue(source['url'].endswith('#page=6'))
                self.assertIn('Roof shelter',source['text'])
                # Cached extraction must remain searchable after a second index.
                for cached in (store.ROOT/'index-cache').glob('*.json'):cached.write_text('{torn fixture')
                self.assertEqual(library.index_guides(),1)
                self.assertEqual(len(asyncio.run(library.search('toit abri'))),1)
    def test_only_read_and_cited_sources_are_displayed(self):
        refs={'a':{'number':1,'consulted':False,'id':'a'},'b':{'number':2,'consulted':True,'id':'b'},'c':{'number':3,'consulted':True,'id':'c'}}
        self.assertEqual(engine.cited_sources('Un résultat [1], une source lue [2].',refs),[{'number':2,'id':'b'}])


if __name__=='__main__':unittest.main()
