"""Incremental work stays bounded without changing sources, ranking or revisions."""
import asyncio
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import AsyncMock,patch
from pilot import catalogue,library,retrieval,store


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.root=Path(folder.name);self.guides=self.root/'guides';self.zims=self.root/'zim'
        self.guides.mkdir();self.zims.mkdir();(self.zims/'fixture.zim').write_bytes(b'fictional archive')

    def test_progressive_candidates_reuse_metadata_and_recheck_source_at_finalization(self):
        rows=[{'id':'zim:fixture/Fire_'+str(i),'title':'Fire making '+str(i),'excerpt':'Fictional fire making and friction.'} for i in range(40)]
        saved=catalogue.Snapshot();context=catalogue.SearchAnnotations(self.guides,self.zims,saved)
        with patch.object(catalogue,'revision',wraps=catalogue.revision) as revision:
            for end in range(5,41,5):
                batch=[dict(row) for row in rows[:end]];context.annotate(batch)
                expected=[dict(row) for row in rows[:end]];catalogue.annotate(expected,self.guides,self.zims,saved)
                self.assertEqual(batch,expected)
            self.assertEqual(context.evaluated,40)
            self.assertEqual(revision.call_count,9) # One per eight baseline calls, one in the streaming context.
            context.annotate([dict(row) for row in rows],fresh=True)
            self.assertEqual(revision.call_count,10)
        self.assertEqual(context.evaluated,40)
        self.assertEqual(context.source_checks,2)

    def test_changed_text_and_changed_archive_do_not_reuse_a_stale_classification(self):
        item={'id':'zim:fixture/Article','title':'Poésie','excerpt':'Texte fictif.'}
        rev=catalogue.revision(item['id'],self.guides,self.zims)
        saved=catalogue.Snapshot({item['id']:{'schema':1,'revision':rev,'domains':['resilience'],'document_type':'manual','status':'reviewed'}})
        context=catalogue.SearchAnnotations(self.guides,self.zims,saved)
        original=dict(item);context.annotate([original]);self.assertEqual(original['classification']['method'],'human')
        (self.zims/'fixture.zim').write_bytes(b'another fictional archive edition, different size')
        final=dict(item);context.annotate([final],fresh=True)
        self.assertEqual(final['classification']['status'],'source_changed');self.assertEqual(final['classification']['method'],'automatic')
        changed={**item,'title':'Quiz de botanique','excerpt':'Question fictive sur les plantes.'}
        context.annotate([changed]);self.assertEqual(changed['classification']['document_type'],'exercise')
        self.assertEqual(context.evaluated,3)

    def test_normalization_cache_changes_no_text_and_is_bounded(self):
        cache=retrieval.NormalCache()
        for text in ['Été / l’eau','Fire%20making','x &amp; y','', '漢字 café','\ud800']:
            self.assertEqual(cache(text),retrieval.normal(text));self.assertEqual(cache(text),retrieval.normal(text))
        self.assertEqual(cache.hits,6)
        with patch.object(cache,'MAX_BYTES',200),patch.object(cache,'MAX_ENTRIES',3):
            for i in range(20):self.assertEqual(cache('Texte fictif '+str(i)),retrieval.normal('Texte fictif '+str(i)))
            self.assertLessEqual(cache.bytes,200);self.assertLessEqual(len(cache.values),3)

    def test_cached_ranking_is_identical_when_a_candidate_changes(self):
        cache=retrieval.NormalCache();plan=retrieval.plan('comment faire du feu',library.search_terms('comment faire du feu'),library.SYNONYMS)
        rows=[{'id':'zim:fixture/Fire','title':'Fire making','excerpt':'Fictional fire and friction.'},
              {'id':'guide:quiz','title':'Quiz botanique','excerpt':'Question fictive sur le feu.'}]
        for revision in range(3):
            if revision:rows[0]={**rows[0],'excerpt':'Changed fictional fire excerpt '+str(revision)}
            expected=retrieval.ordered(rows,plan,5,normalizer=retrieval.normal)
            self.assertEqual(retrieval.ordered(rows,plan,5,normalizer=cache),expected)
        self.assertGreater(cache.hits,0)


class ProcessingSearchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.root=Path(folder.name);self.guides=self.root/'guides';self.guides.mkdir();self.zims=self.root/'zim';self.zims.mkdir()
        (self.zims/'fixture.zim').write_bytes(b'fictional archive')
        for obj,key,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',self.guides)]:
            p=patch.object(obj,key,value);p.start();self.addCleanup(p.stop)
        p=patch.dict(os.environ,{'ZIM_DIR':str(self.zims)});p.start();self.addCleanup(p.stop)
        store.init();self.addAsyncCleanup(library.kiwix_queries.close)

    async def test_stream_reuses_processing_and_reports_wall_and_cpu_separately(self):
        rows=[{'id':'zim:fixture/Fire_'+str(i),'title':'Fire making '+str(i),'excerpt':'Fictional fire and friction.','language':'eng','kind':'article'} for i in range(30)]
        async def archives(*args,on_update=None,**kwargs):
            for end in range(5,31,5):
                if on_update:await on_update(rows[:end],{'status':'partial','running':True})
            return rows,{'status':'complete','local_query':{}}
        updates=[]
        async def update(value):updates.append(value)
        with patch.object(library,'search_archives',archives),patch.object(catalogue,'revision',wraps=catalogue.revision) as revision:
            final=await library.search('faire du feu',on_update=update,diagnostic=True)
            self.assertLessEqual(revision.call_count,2)
        metrics=final.coverage['processing'];self.assertEqual(metrics['metadata_evaluations'],30)
        self.assertEqual(metrics['source_revision_checks'],2)
        self.assertLessEqual(metrics['normalization_cache_bytes'],retrieval.NormalCache.MAX_BYTES)
        self.assertGreater(metrics['normalization_hits'],0);self.assertGreater(metrics['snapshots'],6)
        self.assertGreaterEqual(metrics['selection_ms'],0);self.assertGreaterEqual(metrics['selection_cpu_ms'],0)
        self.assertTrue(updates);self.assertEqual([r['id'] for r in updates[-1]],[r['id'] for r in final])
        self.assertNotIn(str(self.root),str(metrics))

    async def test_final_result_rechecks_a_source_replaced_during_the_stream(self):
        row={'id':'zim:fixture/Article','title':'Poésie','excerpt':'Texte fictif.','language':'fr','kind':'article'}
        current=catalogue.revision(row['id'],self.guides,self.zims)
        catalogue.save(row['id'],{'domains':['resilience'],'document_type':'manual','status':'reviewed'},current,self.guides,self.zims)
        async def archives(*args,on_update=None,**kwargs):
            if on_update:await on_update([row],{'status':'partial','running':True})
            (self.zims/'fixture.zim').write_bytes(b'another fictional edition, changed during the query')
            return [row],{'status':'complete'}
        updates=[]
        async def update(value):updates.extend(value)
        with patch.object(library,'search_archives',archives):final=await library.search('poésie',on_update=update)
        self.assertTrue(any(item['classification']['method']=='human' for item in updates))
        self.assertEqual(final[0]['classification']['method'],'automatic')
        self.assertEqual(final[0]['classification']['status'],'source_changed')

    async def test_cancellation_joins_selection_before_leaving_its_worker_behind(self):
        entered=threading.Event();release=threading.Event();closed=threading.Event();original=catalogue.SearchAnnotations.annotate
        def blocked(context,items,**kwargs):
            entered.set()
            try:release.wait(10);return original(context,items,**kwargs)
            finally:closed.set()
        with patch.object(catalogue.SearchAnnotations,'annotate',blocked):
            task=asyncio.create_task(library.search('fire',on_update=AsyncMock()))
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait,3));task.cancel();await asyncio.sleep(.02)
                self.assertFalse(task.done());self.assertFalse(closed.is_set())
            finally:release.set()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertTrue(closed.is_set())


if __name__=='__main__':unittest.main()
