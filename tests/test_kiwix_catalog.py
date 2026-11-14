import asyncio
from pathlib import Path
import tempfile
import unittest
from fastapi import HTTPException
from pilot import kiwix_catalog as catalog

XML=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Wikipedia fixture</title><link type="text/html" href="/content/wikipedia_fr/"/></entry></feed>'


class CatalogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        catalog.CACHE.clear()

    async def test_simultaneous_requests_share_one_read_and_subsequent_reads_use_cache(self):
        calls=[]
        async def reader(path,maximum):
            calls.append((path,maximum));await asyncio.sleep(.01);return XML,'application/xml'
        result=await asyncio.gather(*(catalog.load(self.root,'fixture',reader) for _ in range(10)))
        self.assertEqual(len(calls),1);self.assertTrue(all(r[0]['book']=='wikipedia_fr' for r in result))
        again=await catalog.load(self.root,'fixture',reader)
        self.assertEqual(again.info()['state'],'cached');self.assertEqual(len(calls),1)

    async def test_failed_refresh_keeps_dated_snapshot_and_safe_reason(self):
        async def reader(*args,**kwargs):return XML,'application/xml'
        first=await catalog.load(self.root,'fixture',reader)
        async def unavailable(*args,**kwargs):raise HTTPException(503,'Private upstream body must never appear')
        second=await catalog.load(self.root,'fixture',unavailable,refresh=True)
        self.assertTrue(second.available);self.assertEqual(second,first)
        self.assertEqual(second.info()['state'],'stale');self.assertEqual(second.info()['http_status'],503)
        self.assertNotIn('Private',str(second.info()))
        catalog.CACHE.clear()
        after_restart=await catalog.load(self.root,'fixture',unavailable,refresh=True)
        self.assertEqual(after_restart.info()['state'],'stale')

    async def test_timeout_without_snapshot_is_unavailable_not_empty_valid_catalogue(self):
        async def timeout(*args,**kwargs):raise TimeoutError()
        value=await catalog.load(self.root,'fixture',timeout)
        self.assertFalse(value.available);self.assertEqual(value.info()['error'],'catalog_timeout')

    async def test_html_response_is_not_a_valid_empty_catalogue(self):
        async def reader(*args,**kwargs):return b'<html>Wrong service</html>','text/html'
        value=await catalog.load(self.root,'fixture',reader)
        self.assertFalse(value.available);self.assertEqual(value.info()['error'],'invalid_catalog')

    async def test_valid_empty_catalogue_is_distinct_from_failure_and_endpoint_caches_are_isolated(self):
        async def reader(*args,**kwargs):return XML,'application/xml'
        await catalog.load(self.root,'first',reader)
        async def empty(*args,**kwargs):return b'<feed xmlns="http://www.w3.org/2005/Atom"/>','application/xml'
        value=await catalog.load(self.root,'second',empty)
        self.assertTrue(value.available);self.assertEqual(value,[]);self.assertEqual(value.info()['state'],'live')
