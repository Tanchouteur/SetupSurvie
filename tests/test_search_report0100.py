"""Multilingual native indexes and opt-in traces, without corpus or inference."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,AsyncMock
from urllib.parse import parse_qs,urlsplit
from fastapi import HTTPException
from pilot import archive_index,library,retrieval,store,kiwix_queries


class Report0100Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        p=patch.object(store,'ROOT',self.root/'state');p.start();self.addCleanup(p.stop);store.init()
        self.addAsyncCleanup(kiwix_queries.close)

    def plan(self):return retrieval.plan('feu',library.search_terms('feu'),library.SYNONYMS)

    async def test_http_diagnostic_is_explicit_and_does_not_change_normal_search_calls(self):
        import httpx
        from pilot.app import app
        found=library.SearchResults([],{'status':'complete'})
        with patch.object(library,'search',AsyncMock(return_value=found)) as search:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
                self.assertEqual((await client.get('/api/search?q=feu')).status_code,200)
                self.assertNotIn('diagnostic',search.await_args.kwargs)
                self.assertEqual((await client.get('/api/search?q=feu&diagnostic=true')).status_code,200)
                self.assertIs(search.await_args.kwargs['diagnostic'],True)

    async def test_incompatible_native_languages_do_not_exhaust_request_budget(self):
        books=[{'book':'ted_mul_'+str(i),'language':'eng,fra','fulltext':True} for i in range(14)]
        books += [{'book':'practical_fr_'+str(i),'language':'fra','fulltext':True} for i in range(100)]
        calls=[]
        async def get(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.extend(values['books.name'])
            self.assertFalse(any(name.startswith('ted_mul_') for name in values['books.name']))
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',get):
            _,normal=await library.search_archives(lambda lang:'feu','',5,query_plan=self.plan())
            _,detailed=await library.search_archives(lambda lang:'feu','',5,query_plan=self.plan(),diagnostic=True)
        self.assertEqual(normal['searched'],100);self.assertEqual(normal['not_searched'],0)
        self.assertEqual(normal['native_incompatible'],14);self.assertEqual(normal['status'],'partial')
        self.assertNotIn('trace',normal);self.assertNotIn('index_requirements',normal)
        self.assertEqual(len(detailed['index_requirements']),14)
        self.assertTrue(any(row['stage']=='fulltext' and row['outcome']=='success' for row in detailed['trace']))
        self.assertTrue(all(row['cached'] for row in detailed['trace']))

    async def test_trace_retains_categorical_errors_beyond_short_error_summary(self):
        books=[{'book':'wikipedia_fr_'+str(i),'language':'fra','fulltext':True} for i in range(15)]
        async def get(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            raise HTTPException(400,'PRIVATE PROVIDER BODY')
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',get):
            _,coverage=await library.search_archives(lambda lang:'feu','',5,query_plan=self.plan(),diagnostic=True)
        errors=[row for row in coverage['trace'] if row['outcome']=='error']
        self.assertEqual(len(errors),15);self.assertEqual(len(coverage['errors']),12)
        self.assertTrue(all(row['reason']=='http_error' and row['http_status']==400 for row in errors))
        self.assertNotIn('PRIVATE',json.dumps(coverage))

    async def test_forced_local_copy_does_not_replace_a_compatible_native_fulltext_index(self):
        book={'book':'native_fr','language':'fra','fulltext':True}
        manifest={'native_fr.zim':{'archive':'native_fr.zim','status':'ready','has_fulltext_index':True,'kiwix_language_compatible':True}}
        calls=[]
        async def get(path):
            calls.append(path)
            return (b'[]','application/json') if path.startswith('/suggest?') else (b'<rss><channel/></rss>','application/xml')
        with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(archive_index,'manifest',return_value=manifest),patch.object(library,'get',get):
            _,coverage=await library.search_archives(lambda lang:'feu','',5,query_plan=self.plan())
        self.assertEqual(coverage['searched'],1);self.assertTrue(any(path.startswith('/search?') for path in calls))

    async def test_real_native_multilingual_archive_gets_local_complement_and_is_reused(self):
        try:
            from libzim.writer import Creator
            from kiwix_search_smoke import Article
        except ImportError:self.skipTest('Optional libzim reader required')
        source=self.root/'multilingual.zim';index=store.ROOT/'archive-index'
        with Creator(source).config_indexing(True,'fra') as writer:
            for key,value in {'Name':'multilingual','Title':'Fixture multilingue','Language':'fra,eng'}.items():writer.add_metadata(key,value)
            writer.add_item(Article('Feu','Techniques de production de feu','Friction, fixture fictive sans instruction.'))
        result=archive_index.build_archive(source,index)
        self.assertTrue(result['has_fulltext_index']);self.assertFalse(result['kiwix_language_compatible'])
        self.assertEqual(result['status'],'ready');self.assertEqual(result['index_reason'],'native_multilingual')
        published=next(index.glob('*.sqlite'));mtime=published.stat().st_mtime_ns
        archive_index.build_archive(source,index);self.assertEqual(published.stat().st_mtime_ns,mtime)
        (index/'manifest.json').write_text(json.dumps({'schema':1,'archives':{source.name:result}}))
        book={'book':'multilingual','title':'Fixture multilingue','language':'fra,eng','fulltext':True}
        async def get(path):
            self.assertTrue(path.startswith('/suggest?'),'The prepared archive must use SQLite, not the rejecting native API')
            return b'[]','application/json'
        with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(library,'get',get):
            found=await library.search('faire du feu',diagnostic=True,kind='documents')
        self.assertTrue(any(row['id']=='zim:multilingual/Feu' and row.get('match')=='local_index' for row in found))
        self.assertEqual(found.coverage['locally_indexed'],1);self.assertEqual(found.coverage['native_incompatible'],0)
        self.assertEqual(found.coverage['local_query']['searched'],1)
        single=self.root/'ted_mul_single.zim'
        with Creator(single).config_indexing(True,'eng') as writer:
            for key,value in {'Name':'ted_mul_single','Title':'Fixture mono-code mul','Language':'mul'}.items():writer.add_metadata(key,value)
            writer.add_item(Article('Fire','Fire making','Fictional fixture.'))
        accepted=archive_index.build_archive(single,index)
        self.assertEqual(accepted['status'],'kiwix_index');self.assertTrue(accepted['kiwix_language_compatible'])
