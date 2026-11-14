"""Early documents, bounded streams and generation-aware disk cache on tiny data."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch,AsyncMock
import httpx
from pilot import library,store,search_stream,search_cache,kiwix_queries


class SearchProgressTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)
        p=patch.object(store,'ROOT',self.root/'state');p.start();self.addCleanup(p.stop);store.init()
        self.addAsyncCleanup(kiwix_queries.close)

    async def test_guide_is_received_before_a_slow_native_catalogue_finishes(self):
        guides=self.root/'guides';guides.mkdir();(guides/'fire.en.txt').write_text('Fire making. Ignition example, fictional fixture without practical instructions.')
        gate=asyncio.Event();started=asyncio.Event();received=[]
        async def books():started.set();await gate.wait();return []
        async def update(found):received.append(found)
        with patch.object(library,'GUIDES',guides),patch.object(library,'books',books):
            library.index_guides();task=asyncio.create_task(library.search('faire du feu',on_update=update,budget=60))
            await asyncio.wait_for(started.wait(),2)
            self.assertTrue(any(any(row['id']=='guide:fire.en.txt' for row in found) for found in received))
            self.assertFalse(task.done());gate.set();final=await task
        self.assertTrue(final);self.assertTrue(all(found.coverage['running'] for found in received))
        self.assertNotIn('running',final.coverage)

    async def test_stream_delivers_early_snapshot_and_keeps_only_latest_pending_snapshot(self):
        gate=asyncio.Event()
        async def search(*args,on_update,**kwargs):
            for i in range(80):await on_update(library.SearchResults([{'id':str(i)}],{'running':True}))
            await gate.wait();return library.SearchResults([{'id':'final'}],{'status':'complete'})
        with patch.object(library,'search',search):
            stream=search_stream.packets('fixture');self.assertIn('working',await anext(stream))
            early=await asyncio.wait_for(anext(stream),1);self.assertIn('79',early)
            gate.set();last=await anext(stream);self.assertIn('"state":"done"',last);self.assertIn('final',last)
            await stream.aclose()

    async def test_disconnect_cancels_work_and_error_does_not_export_private_exception(self):
        started=asyncio.Event();stopped=asyncio.Event()
        async def pending(*args,**kwargs):
            started.set()
            try:await asyncio.Event().wait()
            finally:stopped.set()
        with patch.object(library,'search',pending):
            stream=search_stream.packets('fixture');await anext(stream);await started.wait();await stream.aclose()
            self.assertTrue(stopped.is_set())
        with patch.object(library,'search',AsyncMock(side_effect=RuntimeError('PRIVATE PATH TOKEN'))):
            frames=[frame async for frame in search_stream.packets('fixture')]
        self.assertIn('"state":"error"',frames[-1]);self.assertNotIn('PRIVATE',str(frames))

    async def test_http_stream_is_opt_in_and_uses_a_longer_bounded_budget(self):
        from pilot.app import app
        found=library.SearchResults([{'id':'guide:fixture'}],{'status':'complete'})
        with patch.object(library,'search',AsyncMock(return_value=found)) as search:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
                plain=await client.get('/api/search?q=fixture');self.assertIn('application/json',plain.headers['content-type'])
                streamed=await client.get('/api/search?q=fixture&stream=true')
                self.assertIn('text/event-stream',streamed.headers['content-type']);self.assertIn('"state":"done"',streamed.text)
                self.assertEqual(search.await_args.kwargs['budget'],60);self.assertIsNotNone(search.await_args.kwargs['on_update'])

    async def test_generation_change_ignores_old_memory_and_disk_responses(self):
        calls=0
        async def reader(path):
            nonlocal calls;calls+=1;return b'<rss><channel/></rss>','application/xml'
        with patch.object(search_cache,'RESERVE_BYTES',0):
            await kiwix_queries.request(store.ROOT,'fixture','/search?q=one','fulltext',reader,generation='a')
            await kiwix_queries.close()
            _,cached=await kiwix_queries.request(store.ROOT,'fixture','/search?q=one','fulltext',reader,generation='a')
            self.assertTrue(cached);self.assertEqual(calls,1)
            await kiwix_queries.request(store.ROOT,'fixture','/search?q=one','fulltext',reader,generation='b')
        self.assertEqual(calls,2)

    async def test_empty_stream_does_not_query_archives_and_plain_favorite_list_finishes(self):
        with patch.object(library,'search',AsyncMock(return_value=[{'id':'guide:favorite'}])) as search:
            frames=[frame async for frame in search_stream.packets('  ')];search.assert_not_awaited()
            self.assertIn('"results":[]',frames[-1])
            frames=[frame async for frame in search_stream.packets('fixture',favorite_user='fixture')]
            self.assertIn('guide:favorite',frames[-1]);self.assertIn('"state":"done"',frames[-1])

    async def test_invalid_native_response_is_never_reused_as_a_successful_cache_entry(self):
        calls=0
        async def reader(path):
            nonlocal calls;calls+=1
            if calls==1:return b'<html>Temporary upstream error</html>','text/html'
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(search_cache,'RESERVE_BYTES',0):
            with self.assertRaises(ValueError):
                await kiwix_queries.request(store.ROOT,'fixture','/search?q=retry','fulltext',reader,generation='a')
            await kiwix_queries.request(store.ROOT,'fixture','/search?q=retry','fulltext',reader,generation='a')
            await kiwix_queries.close()
            _,cached=await kiwix_queries.request(store.ROOT,'fixture','/search?q=retry','fulltext',reader,generation='a')
        self.assertTrue(cached);self.assertEqual(calls,2)

    async def test_slow_cache_writer_does_not_delay_results_and_shutdown_joins_the_file_user(self):
        entered=threading.Event();release=threading.Event();closed=threading.Event()
        def writer(*args):
            entered.set()
            try:release.wait(5)
            finally:closed.set()
        async def reader(path):return b'<rss><channel/></rss>','application/xml'
        with patch.object(search_cache,'write',writer):
            try:
                await asyncio.wait_for(kiwix_queries.request(store.ROOT,'fixture','/search?q=slow-disk','fulltext',reader,generation='a'),1)
                self.assertTrue(await asyncio.to_thread(entered.wait,1))
                stopping=asyncio.create_task(kiwix_queries.close());await asyncio.sleep(.02)
                self.assertFalse(stopping.done());self.assertFalse(closed.is_set())
            finally:release.set()
            await stopping;self.assertTrue(closed.is_set())

    async def test_cancelling_disk_read_waits_for_the_open_file_to_close(self):
        entered=threading.Event();release=threading.Event();closed=threading.Event()
        def reader(*args):
            entered.set()
            try:release.wait(5)
            finally:closed.set()
        with patch.object(search_cache,'read',reader):
            task=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?q=read','fulltext',AsyncMock(),generation='a'))
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait,1));task.cancel();await asyncio.sleep(.02)
                self.assertFalse(task.done());self.assertFalse(closed.is_set())
            finally:release.set()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertTrue(closed.is_set())

    async def test_native_response_after_old_three_second_limit_can_finish_in_extended_search(self):
        book={'book':'fixture_fr','language':'fra','fulltext':True}
        async def reader(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            await asyncio.sleep(3.1)
            return b'<rss><channel><item><title>Fire making</title><link>/content/fixture_fr/Fire</link><description>Friction and ignition, fictional fixture.</description></item></channel></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(library,'get',reader):
            short=await library.search('faire du feu');self.assertEqual(short.coverage['failed'],1)
            long=await library.search('faire du feu',budget=60)
        self.assertTrue(long);self.assertEqual(long.coverage['failed'],0);self.assertEqual(long.coverage['searched'],1)
        self.assertEqual(long.coverage['status'],'complete')


class SearchDiskCacheTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)
        p=patch.object(search_cache,'RESERVE_BYTES',0);p.start();self.addCleanup(p.stop)

    def test_snapshot_changes_on_archive_replacement_and_index_publication(self):
        zims=self.root/'zim';zims.mkdir();source=zims/'a.zim';source.write_bytes(b'one')
        books=[{'book':'a','language':'fra','search_id':'fixture'}];index=self.root/'index';index.mkdir()
        first=search_cache.snapshot(zims,books,index);source.write_bytes(b'longer')
        second=search_cache.snapshot(zims,books,index);self.assertNotEqual(first,second)
        (index/'manifest.json').write_text('{}');self.assertNotEqual(second,search_cache.snapshot(zims,books,index))

    def test_disk_quota_and_reserve_are_enforced_without_disabling_search(self):
        with patch.dict(os.environ,{'PILOT_SEARCH_CACHE_BYTES':'500'}):
            for i in range(10):search_cache.write(self.root,str(i),(b'x'*150,'application/xml'))
            kept=sum(search_cache.read(self.root,str(i)) is not None for i in range(10));self.assertLessEqual(kept,3)
        with patch.object(search_cache,'RESERVE_BYTES',10**30):search_cache.write(self.root,'no-space',(b'fixture','text/plain'))
        self.assertIsNone(search_cache.read(self.root,'no-space'))
        with patch.dict(os.environ,{'PILOT_SEARCH_CACHE_BYTES':'0'}):self.assertIsNone(search_cache.read(self.root,'9'))

    def test_missing_or_broken_cache_is_optional_and_budget_is_not_a_product_ceiling(self):
        self.assertIsNone(search_cache.read(self.root,'missing'))
        folder=self.root/'cache/search';folder.mkdir(parents=True);(folder/'responses.sqlite').write_bytes(b'not SQLite')
        self.assertIsNone(search_cache.read(self.root,'bad'));search_cache.write(self.root,'bad',(b'fixture','text/plain'))
        with patch.dict(os.environ,{'PILOT_SEARCH_CACHE_BYTES':'8000000000'}):self.assertEqual(search_cache.budget(),8_000_000_000)
