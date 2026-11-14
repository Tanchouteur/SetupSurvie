"""Regressions from real 0.8 reports, on synthetic snippets and mocked HTTP only."""
import asyncio
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit
import httpx
from fastapi import HTTPException
from pilot import kiwix_queries,library,retrieval,store


class SearchFailureTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        p=patch.object(store,'ROOT',Path(temporary.name));p.start();self.addCleanup(p.stop);store.init()
        self.addAsyncCleanup(kiwix_queries.close)

    def plan(self,query):return retrieval.plan(query,library.search_terms(query),library.SYNONYMS)

    async def test_partial_word_fallback_does_not_make_false_results_on_unknown_need(self):
        candidates=[{'id':'guide:physics','title':'Physics exercises','excerpt':'Fictional exercise mentioning quantum theory.'},
                    {'id':'guide:notice','title':'Notice de moteur','excerpt':'Fictional description mentioning propulsion.'}]
        self.assertEqual(retrieval.ordered(candidates,self.plan('propulsion quantique inexistante'),5),[])
        # Native full-text results may legitimately have no excerpt in Kiwix.
        native={'id':'zim:fixture/abri','title':'Shelter construction','excerpt':'','_query_complete':True}
        self.assertEqual(retrieval.ordered([native],self.plan('toit abri'),5)[0]['id'],native['id'])
        candidates=[{'id':'guide:reading','title':'Exercice de lecture','excerpt':'Le vélo de Paul, exemple fictif.'},
                    {'id':'zim:manual/Puncture','title':'Bicycle puncture repair','excerpt':'Fictional mending instructions.'}]
        found=retrieval.ordered(candidates,self.plan('réparer une crevaison de vélo'),5)
        self.assertEqual([r['id'] for r in found],['zim:manual/Puncture'])
        exercise={'id':'quiz','title':'Botanique — quiz','excerpt':'Fictional question about fire.'}
        self.assertEqual(retrieval.ordered([exercise],self.plan('comment faire du feu'),5),[])
        self.assertEqual(retrieval.ordered([exercise],self.plan('quiz botanique'),5)[0]['id'],'quiz')

    async def test_bilingual_intent_search_reaches_french_archives_from_english_and_reverse(self):
        calls=[]
        async def get(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.append(values)
            book=values['books.name'][0]
            return ('<rss><channel><item><title>Bicycle puncture repair</title><link>/content/'+book+'/fixture</link><description>Fictional data.</description></item></channel></rss>').encode(),'application/xml'
        books=[{'book':'french','language':'fra','fulltext':True},{'book':'english','language':'eng','fulltext':True}]
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',get):
            await library.search('bicycle puncture repair');await library.search('réparer une crevaison de vélo')
        french=[v['pattern'][0] for v in calls if v['books.name']==['french']]
        english=[v['pattern'][0] for v in calls if v['books.name']==['english']]
        self.assertTrue(all('velo' in q and 'crevaison' in q for q in french),french)
        self.assertTrue(all('bicycle' in q and 'puncture' in q for q in english),english)
        self.assertEqual(self.plan('how to start a fire').words,['fire'])

    async def test_timeout_and_overload_do_not_fan_out_and_diagnostics_never_copy_raw_error(self):
        calls=[];books=[{'book':'book'+str(i),'language':'eng','fulltext':True} for i in range(6)]
        async def get(path):
            if path.startswith('/suggest?'):raise httpx.ConnectError('PRIVATE HOST PATH')
            calls.append(path);error=HTTPException(404,'PRIVATE PROVIDER BODY');error.upstream_status=503;raise error
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',get):
            _,coverage=await library.search_archives(lambda lang:'fire','',5,query_plan=self.plan('feu'))
        self.assertEqual(len(calls),1);self.assertEqual(coverage['failed'],6)
        self.assertEqual(coverage['error_counts'],{'http_error':1,'connection_error':4})
        self.assertTrue(any(e['http_status']==503 for e in coverage['errors']))
        self.assertNotIn('PRIVATE',json.dumps(coverage));self.assertLessEqual(len(coverage['errors']),12)
        async def timeout(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            calls.append(path);raise TimeoutError()
        calls.clear()
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',timeout):
            _,coverage=await library.search_archives(lambda lang:'fire','',5,query_plan=self.plan('feu'))
        self.assertEqual(len(calls),1);self.assertEqual(coverage['error_counts']['timeout'],1)

    async def test_successful_singleflight_and_cache_with_failure_retry(self):
        calls=0;gate=asyncio.Event()
        async def reader(path):
            nonlocal calls;calls+=1;await gate.wait();return b'<rss><channel/></rss>','application/xml'
        tasks=[asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?q=one','fulltext',reader)) for _ in range(2)]
        await asyncio.sleep(.01);gate.set();await asyncio.gather(*tasks);self.assertEqual(calls,1)
        _,cached=await kiwix_queries.request(store.ROOT,'fixture','/search?q=one','fulltext',reader);self.assertTrue(cached);self.assertEqual(calls,1)
        broken=AsyncMock(side_effect=[httpx.ConnectError('private'),(b'<rss><channel/></rss>','application/xml')])
        with self.assertRaises(httpx.ConnectError):await kiwix_queries.request(store.ROOT,'fixture','/search?q=two','fulltext',broken)
        await kiwix_queries.request(store.ROOT,'fixture','/search?q=two','fulltext',broken);self.assertEqual(broken.await_count,2)
        invalid=AsyncMock(side_effect=[(b'<html>error</html>','text/html'),(b'<rss><channel/></rss>','application/xml')])
        with self.assertRaises(ValueError):await kiwix_queries.request(store.ROOT,'fixture','/search?q=bad','fulltext',invalid)
        await kiwix_queries.request(store.ROOT,'fixture','/search?q=bad','fulltext',invalid);self.assertEqual(invalid.await_count,2)

    async def test_global_lanes_bound_two_searches_and_reserve_titles(self):
        current={'fulltext':0,'title':0};peak=dict(current);title_seen=asyncio.Event()
        async def reader(path):
            kind='title' if path.startswith('/suggest') else 'fulltext';current[kind]+=1;peak[kind]=max(peak[kind],current[kind])
            try:
                if kind=='title':title_seen.set()
                else:await asyncio.wait_for(title_seen.wait(),1)
                await asyncio.sleep(.01)
                return (b'[]','application/json') if kind=='title' else (b'<rss><channel/></rss>','application/xml')
            finally:current[kind]-=1
        tasks=[kiwix_queries.request(store.ROOT,'fixture','/search?'+str(i),'fulltext',reader) for i in range(12)]
        tasks+=[kiwix_queries.request(store.ROOT,'fixture','/suggest?'+str(i),'title',reader) for i in range(4)]
        await asyncio.wait_for(asyncio.gather(*tasks),2)
        self.assertEqual(peak,{'fulltext':2,'title':2});self.assertEqual(current,{'fulltext':0,'title':0})

    async def test_query_result_cache_is_bounded_expiring_and_cancellation_is_observed(self):
        response=b'<rss><channel>'+b' '*160000+b'</channel></rss>'
        reader=AsyncMock(return_value=(response,'application/xml'))
        for i in range(70):await kiwix_queries.request(store.ROOT,'fixture','/search?'+str(i),'fulltext',reader)
        shared=kiwix_queries.state();self.assertLessEqual(len(shared['cache']),kiwix_queries.MAX_ENTRIES);self.assertLessEqual(sum(len(v[1][0]) for v in shared['cache'].values()),kiwix_queries.MAX_BYTES)
        key=next(iter(shared['cache']));stamp,value=shared['cache'][key];shared['cache'][key]=(stamp-kiwix_queries.TTL-1,value)
        _,cached=await kiwix_queries.request(*key,'fulltext',reader);self.assertFalse(cached)
        gate=asyncio.Event();started=asyncio.Event()
        async def delayed(path):started.set();await gate.wait();return b'[]','application/json'
        task=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/suggest?cancel','title',delayed));await started.wait();task.cancel();await asyncio.gather(task,return_exceptions=True)
        await kiwix_queries.close();self.assertFalse(kiwix_queries.state()['flights'])
