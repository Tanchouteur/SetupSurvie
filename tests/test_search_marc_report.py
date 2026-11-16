"""Regressions derived from Marc's measured report, using synthetic snippets."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,AsyncMock
from urllib.parse import parse_qs,urlsplit
from pilot import engine,library,retrieval,store


class MarcReportTests(unittest.TestCase):
    def plan(self,q):return retrieval.plan(q,library.search_terms(q),library.SYNONYMS)

    def test_repair_and_preservation_intents_beat_unrelated_construction_and_food(self):
        def item(id,title,text=''):return {'id':id,'title':title,'excerpt':text,'language':'en'}
        cases=[('réparer un vélo',[item('generator','Bicycle generator: the ultimate DIY guide'),item('repair','Bicycle puncture repair')],'repair'),
               ('conserver les graines',[item('food','Conservation alimentaire USDA : Fruits'),item('seeds','Seed storage and saving')],'seeds'),
               ('rendre eau potable',[item('directive','Drinking Water Directive 2020'),item('treatment','Drinking water disinfection and treatment')],'treatment')]
        for query,items,expected in cases:self.assertEqual(retrieval.ordered(items,self.plan(query),5)[0]['id'],expected)

    def test_wiki_translation_language_and_navigation_pages_are_deprioritized(self):
        self.assertEqual(retrieval.article_language({'id':'zim:appropedia_en_all/Pedal_generator/hr','language':'eng'}),'hr')
        items=[{'id':'zim:wikipedia/Category:Fire_making','title':'Category:Fire making'}, {'id':'zim:wikipedia/Production','title':'Techniques de production de feu'}]
        self.assertEqual(retrieval.ordered(items,self.plan('faire du feu'),5)[0]['id'],items[1]['id'])

    def test_title_lookup_is_not_starved_by_many_slow_archives(self):
        catalog=[{'book':'slow'+str(i),'language':'eng','fulltext':True} for i in range(40)]+[{'book':'wikipedia_fr','language':'fra','fulltext':True}]
        async def run():
            title_started=asyncio.Event()
            async def get(path,*args):
                if path.startswith('/suggest?'):
                    title_started.set();return b'[]','application/json'
                await title_started.wait();return b'<rss><channel/></rss>','application/xml'
            # The test coordinates the simulated network requests. A persistent
            # cache hit may skip the title request that releases the full-text one.
            with tempfile.TemporaryDirectory() as d,patch.object(store,'ROOT',Path(d)), \
                    patch.object(library.search_cache,'budget',return_value=0), \
                    patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',get):
                return await asyncio.wait_for(library.search_archives(lambda lang:'feu','',5,query_plan=self.plan('faire du feu')),1)
        _,coverage=asyncio.run(run());self.assertGreater(coverage['title_searched'],0)

    def test_context_overrides_are_per_model(self):
        with tempfile.TemporaryDirectory() as d,patch.object(store,'ROOT',Path(d)):
            store.init();self.assertEqual(engine.context_size('a'),16384)
            with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',('context:a','32768'))
            self.assertEqual(engine.context_size('a'),32768);self.assertEqual(engine.context_size('b'),16384)
