"""Kiwix protocol fixtures reproduce multilingual HTTP 400, no corpus/model."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from html import escape
from unittest.mock import AsyncMock,patch
from urllib.parse import urlsplit,parse_qs,quote
from fastapi import HTTPException
from pilot import library,store


class KiwixSearchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        patcher=patch.object(store,'ROOT',Path(self.temp.name));patcher.start();self.addCleanup(patcher.stop);store.init()
        self.catalog=[{'book':'wikipedia_fr','language':'fra','fulltext':True,'title':'Wikipédia'},
                      {'book':'manual_en','language':'eng','fulltext':True,'title':'Manual'},
                      {'book':'multi','language':'eng,fra','fulltext':True,'title':'Multilingue'},
                      {'book':'video','language':'fra','fulltext':False,'title':'Vidéos'}]
        self.addAsyncCleanup(library.kiwix_queries.close)

    def xml(self,book,title='Feu de camp'):
        return f'<rss><channel><item><title>{title}</title><link>/content/{book}/Feu_de_camp</link><description>Extrait fictif sur le sujet demandé.</description></item></channel></rss>'.encode(), 'application/xml'

    async def test_fire_query_searches_explicit_archives_separates_languages_and_reports_unindexed(self):
        calls=[]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.append(values)
            self.assertNotIn('books.filter.lang',values)
            names=values['books.name']
            if 'multi' in names:self.assertEqual(names,['multi'])
            return self.xml(names[0])
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('comment faire un feu')
        self.assertEqual(len(found),3)
        self.assertEqual(found.coverage['searched'],3);self.assertEqual(found.coverage['without_fulltext'],1)
        self.assertEqual(found.coverage['native_incompatible'],1)
        english=next(c for c in calls if c['books.name']==['manual_en'])
        self.assertEqual(english['pattern'],['fire'])
        self.assertTrue(all(r['id'].startswith('zim:') for r in found))

    async def test_rejected_batch_retries_individual_archives_without_hiding_success(self):
        catalog=[dict(self.catalog[0],book=name) for name in ['a','broken','b']]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            names=parse_qs(urlsplit(path).query)['books.name']
            if len(names)>1 or names==['broken']:raise HTTPException(400,'Different languages')
            return self.xml(names[0])
        with patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('feu')
        self.assertEqual(len(found),2);self.assertEqual(found.coverage['searched'],2)
        self.assertEqual(found.coverage['failed'],1);self.assertEqual(found.coverage['status'],'partial')
        self.assertIn('partielle',found.coverage['warning'])

    async def test_catalogue_outage_is_not_a_valid_empty_search(self):
        with patch.object(library,'books',AsyncMock(return_value=library.Catalog(available=False))):
            found=await library.search('feu')
        self.assertEqual(found,[]);self.assertEqual(found.coverage['status'],'unavailable')
        self.assertIn('ne prouvent pas',found.coverage['warning'])

    async def test_exact_language_filter_includes_multilingual_but_not_unrelated_language(self):
        calls=[]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.extend(values['books.name']);return self.xml(values['books.name'][0])
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            await library.search('feu',language='fr')
        self.assertEqual(set(calls),{'wikipedia_fr','video'})

    async def test_duplicate_hits_are_deduplicated_and_unknown_books_rejected(self):
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            return self.xml('not_in_catalogue')
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('feu')
        self.assertEqual(found,[])

    async def test_catalogue_parses_language_namespaces_uuid_and_fulltext_flags(self):
        xml=b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/"><entry><id>urn:uuid:12345678-1234-1234-1234-123456789012</id><title>Test</title><dc:language>fra</dc:language><tags>_ftindex:yes;_pictures:yes</tags><link type="text/html" href="/content/test/"/></entry></feed>'
        with patch.object(library,'get',AsyncMock(return_value=(xml,'application/xml'))):value=await library.books()
        self.assertEqual(value[0]['book'],'test');self.assertEqual(value[0]['language'],'fra')
        self.assertTrue(value[0]['fulltext']);self.assertTrue(value[0]['search_id'])

    async def test_html_escaped_suggestion_paths_share_the_native_fulltext_identity(self):
        cases=[('Compost_et_l&apos;urbanisme',"Compost_et_l'urbanisme"),('Compost &amp; jardin','Compost & jardin'),
               ('Compost_&#233;t&#233;','Compost_été'),('Compost_%26amp%3B','Compost_&amp;')]
        zims=Path(self.temp.name)/'zim';zims.mkdir()
        for edition,(suggested,expected) in enumerate(cases,1):
            with self.subTest(path=suggested):
                # Each mocked response is a different archive edition. Keep the
                # real disk-cache invalidation instead of reusing an old fixture.
                (zims/'wikipedia_fr.zim').write_bytes(b'x'*edition)
                await library.kiwix_queries.close()
                async def reader(path):
                    if path.startswith('/suggest?'):return json.dumps([{'kind':'path','value':'Compost','path':suggested}]).encode(),'application/json'
                    link='/content/wikipedia_fr/'+quote(expected,safe='/')
                    return ('<rss><channel><item><title>Compost</title><link>'+escape(link)+'</link><description>Compost, extrait fictif.</description></item></channel></rss>').encode(),'application/xml'
                with patch.object(library,'books',AsyncMock(return_value=self.catalog[:1])),patch.object(library,'get',reader),patch.dict('os.environ',{'ZIM_DIR':str(zims)}):
                    found=await library.search('compost')
                self.assertEqual([row['id'] for row in found],['zim:wikipedia_fr/'+expected])

    async def test_title_only_paths_decode_entities_before_rejecting_unsafe_paths(self):
        paths=['&#47;&#47;other.invalid/path','https&#58;//other.invalid/path','&#46;&#46;/private','folder/&#46;&#46;/private','folder&#92;private','%252e%252e/private']
        async def reader(path):
            if path.startswith('/suggest?'):return json.dumps([{'kind':'path','value':'Compost','path':p} for p in paths]).encode(),'application/json'
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=self.catalog[:1])),patch.object(library,'get',reader):
            found=await library.search('compost')
        self.assertEqual(found,[])

    async def test_request_budget_is_bounded_and_unsearched_books_are_disclosed(self):
        catalog=[dict(self.catalog[0],book='wikipedia_fr_'+str(i)) for i in range(45)]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            return self.xml(parse_qs(urlsplit(path).query)['books.name'][0])
        with patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)) as get:
            found=await library.search('feu')
        self.assertLessEqual(get.await_count,36);self.assertGreater(found.coverage['not_searched'],0)
        self.assertEqual(found.coverage['status'],'partial')
