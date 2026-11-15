"""A large catalogue must not silently exhaust refinements at a fixed 32 calls."""
import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit

from pilot import archive_index,kiwix_queries,library,retrieval,store


class RefinementBudgetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);self.zims=root/'zim';self.zims.mkdir()
        p=patch.object(store,'ROOT',root/'state');p.start();self.addCleanup(p.stop);store.init()
        p=patch.dict(os.environ,{'ZIM_DIR':str(self.zims)});p.start();self.addCleanup(p.stop)
        self.addAsyncCleanup(kiwix_queries.close)
        self.books=[{'book':'wikipedia_fixture_'+str(i),'language':'fra','fulltext':True} for i in range(19)]
        self.books += [{'book':'technical_fixture_'+str(i),'language':'eng','fulltext':True} for i in range(101)]
        self.books += [{'book':'local_fixture_'+str(i),'language':'fra,eng','fulltext':True} for i in range(15)]
        self.manifest={b['book']+'.zim':{'archive':b['book']+'.zim','status':'ready','has_fulltext_index':True,'kiwix_language_compatible':False} for b in self.books[-15:]}
        self.plan=retrieval.plan('installer un panneau solaire',library.search_terms('installer un panneau solaire'),library.SYNONYMS)
        self.calls=[];self.active=0;self.peak=0

    def pattern(self,language,words=None):
        parts=words if words is not None else self.plan.words
        mapping={'panneau':'panel','solaire':'solar'} if language=='eng' else {}
        return ' '.join(mapping.get(word,word) for word in parts)+(' installation' if words is None else '')

    async def reader(self,path):
        if path.startswith('/suggest?'):return b'[]','application/json'
        values=parse_qs(urlsplit(path).query);self.calls.append(values);self.active+=1;self.peak=max(self.peak,self.active)
        try:
            await asyncio.sleep(.001)
            if 'technical_fixture_100' in values.get('books.name',[]) and values['pattern']==['solar']:
                return b'<rss><channel><item><title>Solar panel installation</title><link>/content/technical_fixture_100/Installation</link><description>Fictional installation text, no instructions.</description></item></channel></rss>','application/xml'
            return b'<rss><channel/></rss>','application/xml'
        finally:self.active-=1

    async def search(self,budget,reader=None):
        with patch.object(library,'books',AsyncMock(return_value=self.books)),patch.object(archive_index,'manifest',return_value=self.manifest),patch.object(library,'get',reader or self.reader):
            return await library.search_archives(self.pattern,'',8,query_plan=self.plan,diagnostic=True,budget=budget)

    async def test_long_search_reaches_late_refinement_after_all_primary_batches(self):
        rows,coverage=await self.search(60)
        self.assertTrue(any(row['id']=='zim:technical_fixture_100/Installation' for row in rows))
        self.assertEqual(coverage['primary_requests'],28)
        self.assertEqual(coverage['searched'],120);self.assertEqual(coverage['locally_indexed'],15)
        self.assertEqual(coverage['refinement_not_searched'],0);self.assertEqual(coverage['failed'],0)
        self.assertEqual(coverage['not_searched'],0);self.assertEqual(coverage['status'],'complete')
        self.assertLessEqual(self.peak,2);self.assertEqual(self.active,0)
        self.assertLessEqual(len(self.calls),coverage['request_limit'])
        self.assertLessEqual(len(coverage['trace']),40)
        self.assertEqual(retrieval.ordered(rows,self.plan,8)[0]['id'],'zim:technical_fixture_100/Installation')
        count=len(self.calls);repeated,warm=await self.search(60)
        self.assertEqual(rows,repeated);self.assertEqual(len(self.calls),count)
        self.assertEqual(warm['status'],'complete');self.assertGreater(warm['cache_hits'],32)

    async def test_short_assistant_api_preserves_its_existing_request_ceiling(self):
        rows,coverage=await self.search(12)
        self.assertEqual(coverage['request_limit'],32);self.assertEqual(len(self.calls),32)
        self.assertEqual(coverage['primary_requests'],28);self.assertFalse(rows)
        self.assertGreater(coverage['refinement_not_searched'],0);self.assertEqual(coverage['status'],'partial')

    async def test_expanded_budget_still_obeys_deadline_and_joins_cancelled_requests(self):
        entered=asyncio.Event()
        async def delayed(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            self.active+=1;entered.set()
            try:await asyncio.Event().wait()
            finally:self.active-=1
        timeout=asyncio.timeout
        with patch.object(library.asyncio,'timeout',lambda seconds:timeout(.04 if seconds==13 else seconds)):
            _,coverage=await self.search(13,delayed)
        self.assertTrue(entered.is_set());self.assertTrue(coverage['deadline_exceeded'])
        self.assertGreater(coverage['request_limit'],32);self.assertGreater(coverage['not_searched'],0)
        self.assertEqual(coverage['status'],'partial');self.assertEqual(self.active,0)


if __name__=='__main__':unittest.main()
