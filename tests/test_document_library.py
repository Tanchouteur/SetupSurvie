"""Publication, bookmarks and failure isolation with tiny documents, no model."""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import time
import threading
import unittest
from unittest.mock import AsyncMock,patch

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
from pilot import app as gateway,library,publications,store,translations,engine


class DocumentLibraryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.guides=self.root/'guides';self.guides.mkdir()
        for target,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',self.guides)]:
            setting=patch.object(target,name,value);setting.start();self.addCleanup(setting.stop)
        self.user={'id':'alice','name':'Alice','role':'user'}
        gateway.app.dependency_overrides[gateway.user]=lambda:self.user
        self.addCleanup(gateway.app.dependency_overrides.clear)
        self.addCleanup(gateway.DEGRADED.clear)
        store.init()
        (self.guides/'manual.en.txt').write_text('Fictional repair manual. Read the original warnings.',encoding='utf-8')
        self.pdf()
        with store.connect() as db:
            db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',('manual.en.txt','Manual fixture','en','Synthetic fixture','Fixture only'))
            db.execute('INSERT INTO guide_dates VALUES(?,?,?,?)',('manual.en.txt','2015','Edition A','2026-11-12'))
        library.index_guides()
        self.client=TestClient(gateway.app);self.addCleanup(self.client.close)
        self.client.headers['Origin']='http://testserver'
        native=patch.object(gateway.accounts,'native',AsyncMock(side_effect=lambda *args,**kwargs:self.user))
        native.start();self.addCleanup(native.stop)
        self.client.cookies.set(gateway.COOKIE,'fixture-only')

    def pdf(self):
        writer=PdfWriter()
        for n in range(1,7):
            page=writer.add_blank_page(width=300,height=400)
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
            stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+('Helix rotor' if n==6 else 'Introduction')+') Tj ET').encode())
            page[NameObject('/Contents')]=stream
        writer.write(self.guides/'rotor.en.pdf')

    def pending_translation(self):
        with patch.object(translations.operations,'status',AsyncMock(return_value={'online':True,'paused':False,'operation':None})),patch.object(translations,'launch'):
            response=self.client.post('/api/translations',json={'source_id':'guide:manual.en.txt','mode':'rapide'})
        self.assertEqual(response.status_code,202,response.text)
        item=response.json()
        with store.connect() as db:
            db.execute("UPDATE translation_parts SET translated=?,status='done',model='fixture-model' WHERE translation_id=?",('Réparation turbine. <script>alert(1)</script> Respectez les avertissements.',item['id']))
        return item

    def complete(self):
        item=self.pending_translation()
        asyncio.run(translations.run(item['id']))
        result=self.client.get('/api/translations/'+item['id']).json()
        self.assertEqual(result['status'],'completed',result)
        return result

    def test_completed_translation_is_public_searchable_and_survives_conversation_deletion(self):
        item=self.complete();identifier=item['publication']['source_id']
        self.assertIsNotNone(identifier,item)
        original=self.client.get('/api/source',params={'id':identifier}).json()
        self.assertTrue(original['is_ai_translation']);self.assertEqual(original['original_document_date'],'2015')
        target=self.guides/identifier.removeprefix('guide:')
        html=target.read_text(encoding='utf-8')
        self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html)
        self.assertIn('fixture-model',html);self.assertIn('non vérifiée',html)
        self.assertNotIn('alice',html)
        self.assertEqual(self.client.put('/api/favorites',json={'source_id':identifier}).status_code,200)
        self.assertEqual(self.client.delete('/api/conversations/'+item['conversation_id']).status_code,200)
        self.assertTrue(target.is_file())
        self.assertEqual(self.client.get('/api/source',params={'id':identifier}).status_code,200)
        self.assertEqual(self.client.get('/api/translations/'+item['id']).status_code,404)
        gateway.app.dependency_overrides.clear()
        found=self.client.get('/api/search',params={'q':'turbine','translations_only':'true'}).json()['results']
        self.assertTrue(any(r['id'].split('#page=')[0]==identifier for r in found))
        self.assertEqual(self.client.get('/api/library/translations').json()['results'][0]['id'],identifier)

    def test_favorites_searches_late_pdf_pages_before_limiting_and_is_account_owned(self):
        for n in range(15):(self.guides/f'distractor{n}.en.txt').write_text('Helix rotor '*50)
        library.index_guides()
        self.assertEqual(self.client.put('/api/favorites',json={'source_id':'guide:rotor.en.pdf#page=6'}).status_code,200)
        result=self.client.get('/api/search',params={'q':'helix','favorites_only':'true','limit':1}).json()['results']
        self.assertEqual(result[0]['id'],'guide:rotor.en.pdf#page=6')
        self.assertEqual(self.client.get('/api/favorites').json()['results'][0]['id'],'guide:rotor.en.pdf')
        self.user={'id':'bob','name':'Bob','role':'user'}
        self.assertEqual(self.client.get('/api/favorites').json()['results'],[])
        self.assertEqual(self.client.get('/api/search',params={'q':'helix','favorites_only':'true'}).json()['results'],[])
        self.client.delete('/api/favorites',params={'source_id':'guide:rotor.en.pdf'})
        self.user={'id':'alice','name':'Alice','role':'user'}
        self.assertEqual(len(self.client.get('/api/favorites').json()['results']),1)
        gateway.app.dependency_overrides.clear()
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/api/favorites').status_code,401)
        self.assertEqual(self.client.get('/api/search',params={'q':'helix','favorites_only':'true'}).status_code,401)

    def test_article_favorite_search_uses_its_snapshot_without_global_kiwix_top_results(self):
        article={'id':'zim:book/article','title':'Article fixture','url':'/content/book/article','language':'eng','text':'Rare quartz calibration word.'}
        with patch.object(library,'source',AsyncMock(return_value=article)):
            self.assertEqual(self.client.put('/api/favorites',json={'source_id':article['id']}).status_code,200)
        with patch.object(library,'books',AsyncMock(side_effect=AssertionError('No remote query'))):
            found=self.client.get('/api/search',params={'q':'quartz','favorites_only':'true','language':'en'}).json()['results']
        self.assertEqual(found[0]['id'],article['id'])
        self.assertEqual(len(self.client.get('/api/favorites?language=en').json()['results']),1)

    def test_unavailable_document_directory_does_not_erase_the_last_index(self):
        with patch.object(library,'GUIDES',self.root/'unmounted'):
            with self.assertRaises(OSError):library.index_guides()
        self.assertEqual(self.client.get('/api/source',params={'id':'guide:manual.en.txt'}).status_code,200)

    def test_publication_failure_retains_translation_original_search_and_favorites_then_retries(self):
        item=self.pending_translation()
        with patch.object(publications,'_publish',side_effect=OSError('fixture disk failure')):
            asyncio.run(translations.run(item['id']))
        status=self.client.get('/api/translations/'+item['id']).json()
        self.assertEqual(status['status'],'completed');self.assertTrue(status['publication']['error'])
        self.assertEqual(self.client.get('/api/source',params={'id':'guide:manual.en.txt'}).status_code,200)
        self.assertEqual(self.client.put('/api/favorites',json={'source_id':'guide:manual.en.txt'}).status_code,200)
        self.assertEqual(self.client.delete('/api/conversations/'+item['conversation_id']).status_code,409)
        self.user={'id':'bob','role':'user'}
        self.assertEqual(self.client.post('/api/translations/'+item['id']+'/publish').status_code,404)
        self.user={'id':'alice','role':'user'}
        self.assertEqual(self.client.post('/api/translations/'+item['id']+'/publish').status_code,200)
        self.assertEqual(self.client.delete('/api/conversations/'+item['conversation_id']).status_code,200)

    def test_optional_module_error_does_not_break_source_search_or_health(self):
        real=gateway.importlib.import_module
        def load(name,*args,**kwargs):
            if name=='.publications':raise ImportError('fixture unavailable module')
            return real(name,*args,**kwargs)
        with patch.object(gateway.importlib,'import_module',side_effect=load):
            self.assertEqual(self.client.get('/api/library/translations').status_code,503)
            self.assertEqual(self.client.get('/api/source',params={'id':'guide:manual.en.txt'}).status_code,200)
            with patch.object(library,'books',AsyncMock(return_value=[])):
                self.assertEqual(self.client.get('/api/search',params={'q':'repair'}).status_code,200)
            self.assertTrue(self.client.get('/api/health').json()['ok'])
            self.assertIn('publications',self.client.get('/api/health').json()['degraded_features'])

    def test_startup_reindex_failure_preserves_previous_index_and_serves_core(self):
        async def check():
            with patch.object(library,'index_guides',side_effect=RuntimeError('fixture indexing failure')):
                async with gateway.lifespan(gateway.app):
                    health=await gateway.health()
                    self.assertTrue(health['ok']);self.assertIn('index',health['degraded_features'])
                    self.assertEqual((await library.source('guide:manual.en.txt'))['id'],'guide:manual.en.txt')
        asyncio.run(check())

    def test_slow_optional_index_does_not_hold_startup_forever(self):
        release=threading.Event()
        async def check():
            with patch.object(gateway,'STARTUP_FEATURE_TIMEOUT',.02),patch.object(library,'index_guides',side_effect=lambda:release.wait(3)):
                try:
                    async with gateway.lifespan(gateway.app):
                        self.assertTrue((await gateway.health())['ok'])
                        self.assertIn('index',gateway.DEGRADED)
                        self.assertEqual((await library.source('guide:manual.en.txt'))['id'],'guide:manual.en.txt')
                finally:release.set()
        asyncio.run(check())

    def test_publication_module_outage_does_not_fail_the_translation_itself(self):
        item=self.pending_translation()
        with patch.object(publications,'automatic',side_effect=RuntimeError('fixture module bug')):
            asyncio.run(translations.run(item['id']))
        self.assertEqual(self.client.get('/api/translations/'+item['id']).json()['status'],'completed')
        asyncio.run(publications.recover())
        self.assertIsNotNone(self.client.get('/api/translations/'+item['id']).json()['publication']['source_id'])

    def test_original_pdf_supports_ranges_and_refuses_non_pdf_or_escape(self):
        response=self.client.get('/api/original',params={'id':'guide:rotor.en.pdf'},headers={'Range':'bytes=0-9'})
        self.assertEqual(response.status_code,206);self.assertEqual(len(response.content),10)
        self.assertEqual(response.headers['content-type'],'application/pdf')
        self.assertEqual(self.client.get('/api/original',params={'id':'guide:manual.en.txt'}).status_code,400)
        self.assertEqual(self.client.get('/api/original',params={'id':'guide:../private.pdf'}).status_code,404)

    def test_emergency_list_failure_keeps_the_search_index_and_publication(self):
        original=library.durable.write_bytes
        def write(path,*args,**kwargs):
            if Path(path).name=='_setupsurvie-index.json':raise OSError('fixture full read-only target')
            return original(path,*args,**kwargs)
        with patch.object(library.durable,'write_bytes',side_effect=write):
            item=self.complete()
        self.assertIsNotNone(item['publication']['source_id'])
        self.assertEqual(self.client.get('/api/source',params={'id':'guide:manual.en.txt'}).status_code,200)

    def test_recovery_after_file_written_but_indexing_interrupted_is_idempotent(self):
        item=self.pending_translation()
        with patch.object(library,'index_guides',side_effect=OSError('fixture interrupted index')):
            asyncio.run(translations.run(item['id']))
        path=self.guides/('TRAD-'+item['id']+'.fr.html')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.client.get('/api/translations/'+item['id']).json()['status'],'completed')
        asyncio.run(publications.recover())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
        self.assertIsNotNone(self.client.get('/api/translations/'+item['id']).json()['publication']['source_id'])

    def test_legacy_translation_is_not_retroactively_published_without_explicit_action(self):
        item=self.pending_translation()
        with store.connect() as db:
            db.execute('DELETE FROM settings WHERE key=?',('auto-translation:'+item['id'],))
            db.execute('DELETE FROM translation_publications WHERE translation_id=?',(item['id'],))
            db.execute("UPDATE translations SET status='completed',updated=? WHERE id=?",(time.time(),item['id']))
        asyncio.run(publications.recover())
        self.assertEqual(self.client.get('/api/library/translations').json()['results'],[])
        response=self.client.post('/api/translations/'+item['id']+'/publish')
        self.assertEqual(response.status_code,200,response.text)
        path=self.guides/response.json()['source_id'].removeprefix('guide:')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.client.post('/api/translations/'+item['id']+'/publish').status_code,200)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)


if __name__=='__main__':unittest.main()
