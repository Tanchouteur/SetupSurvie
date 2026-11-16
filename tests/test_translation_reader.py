"""Published French reading never uses private drafts or original snapshots."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pilot import library,publications,store,translations,translation_reader


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);guides=self.root/'guides';guides.mkdir()
        for target,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',guides)]:
            setting=patch.object(target,name,value);setting.start();self.addCleanup(setting.stop)
        store.init();(guides/'manual.en.txt').write_text('Fictional manual, 17 markers.');library.index_guides()

    def publish(self):
        async def run():
            with patch.object(translations,'launch'),patch.object(translations.operations,'status',AsyncMock(return_value={'online':True})):
                item=await translations.create('alice','guide:manual.en.txt',None,'rapide')
            with patch.object(translations.operations,'status',AsyncMock(return_value={'online':True})),patch.object(translations,'translate',AsyncMock(return_value=('Notice fictive, 17 repères. <script>fixture()</script>','fixture-model'))):await translations.run(item['id'])
            return translations.status(item['id'],'alice')
        return asyncio.run(run())

    def test_published_page_survives_conversation_deletion_without_private_text(self):
        item=self.publish();choices=translation_reader.choices('guide:manual.en.txt')['translations']
        self.assertEqual(len(choices),1);self.assertEqual(choices[0]['freshness'],'unchanged');self.assertTrue(choices[0]['integrity_recorded'])
        with store.connect() as db:db.execute('DELETE FROM conversations WHERE id=?',(item['conversation_id'],))
        result=translation_reader.page(choices[0]['id'],'guide:manual.en.txt',1)
        self.assertTrue(result['available']);self.assertIn('<script>',result['parts'][0])
        # Strings are not trusted HTML; the client must render via textContent.
        self.assertNotIn('Fictional manual',json.dumps(result));self.assertNotIn('alice',json.dumps(result));self.assertNotIn('conversation',json.dumps(result))

    def test_changed_original_is_not_announced_as_current(self):
        self.publish();(library.GUIDES/'manual.en.txt').write_text('A different edition of the fixture.')
        self.assertEqual(translation_reader.choices('guide:manual.en.txt')['translations'][0]['freshness'],'changed')

    def test_draft_and_old_private_completed_translation_are_not_listed(self):
        async def prepare():
            with patch.object(translations,'launch'),patch.object(translations.operations,'status',AsyncMock(return_value={'online':True})):
                return await translations.create('alice','guide:manual.en.txt',None,'rapide')
        item=asyncio.run(prepare())
        self.assertEqual(translation_reader.choices('guide:manual.en.txt')['translations'],[])
        with store.connect() as db:db.execute("UPDATE translations SET status='completed' WHERE id=?",(item['id'],))
        self.assertEqual(translation_reader.choices('guide:manual.en.txt')['translations'],[])

    def test_changed_publication_and_cross_document_reference_are_refused(self):
        item=self.publish();identifier=item['publication']['source_id']
        with self.assertRaises(HTTPException):translation_reader.page(identifier,'guide:another.en.txt',1)
        path=library.GUIDES/identifier.removeprefix('guide:');path.write_text(path.read_text()+'Modified outside publication.')
        with self.assertRaises(HTTPException) as error:translation_reader.page(identifier,'guide:manual.en.txt',1)
        self.assertEqual(error.exception.status_code,409)
        self.assertEqual(len(translation_reader.choices('guide:manual.en.txt')['translations']),1)

    def test_outside_page_and_legacy_revision_remain_explicit(self):
        item=self.publish();identifier=item['publication']['source_id']
        self.assertFalse(translation_reader.page(identifier,'guide:manual.en.txt',2)['available'])
        with store.connect() as db:
            record=db.execute('SELECT source_meta FROM translation_publications').fetchone();meta=json.loads(record['source_meta']);meta.pop('source_revision')
            db.execute('UPDATE translation_publications SET source_meta=?',(json.dumps(meta),))
        self.assertEqual(translation_reader.choices('guide:manual.en.txt')['translations'][0]['freshness'],'unknown')

    def test_parser_preserves_all_sections_and_warnings_but_not_document_scripts(self):
        parser=translation_reader.Pages();parser.feed('<script>evil()</script><section id="page=7"><p class="notice">À relire.</p><p class="part">Texte &lt;img src=x&gt;.</p></section><section id="page=8"><p class="part">Suite.</p></section>')
        self.assertEqual(parser.pages,{7:{'parts':['Texte <img src=x>.'],'warnings':['À relire.']},8:{'parts':['Suite.'],'warnings':[]}})

    def test_choices_read_only_metadata_until_french_text_is_requested(self):
        self.publish()
        with patch.object(translation_reader,'publication',side_effect=AssertionError('Do not parse a book just to show a button.')):
            result=translation_reader.choices('guide:manual.en.txt')
        self.assertEqual(result['translations'][0]['pages'],[1])

    def test_public_api_is_read_only_and_works_without_an_inference_engine(self):
        from pilot import app as gateway
        item=self.publish();identifier=item['publication']['source_id']
        with TestClient(gateway.app) as client,patch.object(translations,'translate',side_effect=AssertionError('No inference in the reader.')):
            response=client.get('/api/library/french-reading',params={'original_id':'guide:manual.en.txt'})
            self.assertEqual(response.status_code,200);self.assertEqual(response.json()['translations'][0]['id'],identifier)
            response=client.get('/api/library/french-page',params={'id':identifier,'original_id':'guide:manual.en.txt','page':1})
            self.assertEqual(response.status_code,200);self.assertNotIn('alice',response.text)
            self.assertEqual(client.get('/api/library/french-page',params={'id':identifier,'original_id':'guide:manual.en.txt','page':0}).status_code,422)
            self.assertEqual(client.get('/api/library/french-reading',params={'original_id':'guide:../private/file'}).status_code,400)

    def test_archive_article_uses_the_published_text_and_preserves_archive_revision(self):
        zims=self.root/'zim';zims.mkdir();(zims/'fixture.zim').write_bytes(b'Fictional archive identity.')
        source={'id':'zim:fixture/A/article','title':'Fictional article','language':'en','text':'An article with 17 marks.'}
        async def run():
            with patch.dict('os.environ',{'ZIM_DIR':str(zims)}),patch.object(translations,'launch'),patch.object(translations.operations,'status',AsyncMock(return_value={'online':True})):
                with patch.object(library,'source',AsyncMock(return_value=source)):
                    item=await translations.create('alice',source['id'],None,'rapide')
                with patch.object(translations,'translate',AsyncMock(return_value=('Un article avec 17 repères.','fixture'))):await translations.run(item['id'])
                choices=translation_reader.choices(source['id'])['translations']
                self.assertEqual(choices[0]['freshness'],'unchanged')
                self.assertEqual(translation_reader.page(choices[0]['id'],source['id'],1)['parts'],['Un article avec 17 repères.'])
        asyncio.run(run())
