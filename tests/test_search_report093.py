"""0.9.3 report regressions; tiny paraphrased snippets, no real corpus/model."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit

from pilot import library,retrieval,store,kiwix_queries


class Report093Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        location=patch.object(store,'ROOT',Path(temp.name));location.start();self.addCleanup(location.stop);store.init()
        self.addAsyncCleanup(kiwix_queries.close)
        # Ordering assertions concern the native scheduler, independently of disk speed.
        cache=patch.dict('os.environ',{'PILOT_SEARCH_CACHE_BYTES':'0'});cache.start();self.addCleanup(cache.stop)

    def plan(self,query):return retrieval.plan(query,library.search_terms(query),library.SYNONYMS)

    def test_native_completion_flag_does_not_validate_an_unrelated_visible_excerpt(self):
        physics={'id':'zim:fixture/physics','title':'Physique fictive','excerpt':'Un lexique mentionne la propulsion dans un exercice fictif.','_query_complete':True}
        self.assertEqual(retrieval.ordered([physics],self.plan('propulsion quantique inexistante'),5),[])
        # A genuine native result can have no excerpt. Keep the named technical
        # device, without inventing an excerpt or confirming it is a procedure.
        device={'id':'zim:fixture/generator','title':'Pedal powered generator','excerpt':'...','_query_complete':True}
        self.assertEqual(retrieval.ordered([device],self.plan('fabriquer un générateur à pédales'),5)[0]['id'],device['id'])
        reviewed={'id':'guide:reviewed','title':'Bicycle handbook','excerpt':'','classification':{'method':'human','document_type':'manual'}}
        self.assertEqual(retrieval.ordered([reviewed],self.plan('réparer vélo'),5)[0]['id'],reviewed['id'])

    def test_repair_does_not_return_price_exercises_or_an_inventory_template(self):
        candidates=[{'id':'guide:prices','title':'Mathématiques — prix fictifs','excerpt':'Un vélo coûte 100 euros puis 20 euros.','_query_complete':True},
                    {'id':'guide:inventory','title':'Dossier familial','excerpt':'Modèle à remplir. Vélo, pompe : noter les notices et l’entretien.','_query_complete':True},
                    {'id':'zim:fixture/repair','title':'Bicycle maintenance and repair','excerpt':'Puncture repair, fictional fixture.'}]
        found=retrieval.ordered(candidates,self.plan('réparation vélo'),5)
        self.assertEqual([row['id'] for row in found],['zim:fixture/repair'])
        self.assertTrue(retrieval.ordered(candidates,self.plan('modèle dossier familial'),5))

    def test_two_concrete_concepts_survive_an_extra_unknown_word(self):
        water={'id':'zim:fixture/water','title':'Guide de potabilisation de l’eau','excerpt':'Traitement de l’eau, fixture fictive.','_query_complete':False}
        self.assertTrue(retrieval.ordered([water],self.plan('inconnu eau potable'),5))

    def test_fire_title_words_are_not_an_ignition_method(self):
        candidates=[{'id':'zim:fixture/unrelated','title':'Fire We Make','excerpt':'Correspondance dans le titre ; ouvrir la source pour en vérifier le contenu.','match':'title'},
                    {'id':'zim:fixture/computer','title':'Fire in the Valley: The Making of the Personal Computer','excerpt':'','_query_complete':True},
                    {'id':'zim:fixture/fire','title':'Techniques de production de feu','excerpt':'Friction, exemple fictif sans instruction.'}]
        self.assertEqual([row['id'] for row in retrieval.ordered(candidates,self.plan('comment faire du feu'),5)],['zim:fixture/fire'])

    async def test_last_waiter_cancels_work_but_one_departure_does_not_cancel_another_reader(self):
        started=asyncio.Event();finished=asyncio.Event();gate=asyncio.Event();calls=0
        async def reader(path):
            nonlocal calls;calls+=1;started.set()
            try:await gate.wait();return b'<rss><channel/></rss>','application/xml'
            finally:finished.set()
        first=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?shared','fulltext',reader))
        await started.wait();second=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?shared','fulltext',reader));await asyncio.sleep(.01)
        first.cancel();await asyncio.gather(first,return_exceptions=True)
        self.assertFalse(finished.is_set());self.assertFalse(second.done())
        gate.set();await second;self.assertEqual(calls,1)
        gate.clear();started.clear();finished.clear()
        lone=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?cancelled','fulltext',reader));await started.wait()
        lone.cancel();await asyncio.gather(lone,return_exceptions=True)
        self.assertTrue(finished.is_set());self.assertFalse(kiwix_queries.state()['flights'])
        lane=kiwix_queries.state()['fulltext'];await lane.acquire();await lane.acquire();previous=calls
        queued=asyncio.create_task(kiwix_queries.request(store.ROOT,'fixture','/search?queued','fulltext',reader));await asyncio.sleep(.01)
        queued.cancel();await asyncio.gather(queued,return_exceptions=True);lane.release();lane.release();await asyncio.sleep(.01)
        self.assertEqual(calls,previous);self.assertFalse(kiwix_queries.state()['flights'])

    async def test_practical_languages_and_true_indexes_precede_general_batches_and_large_archives(self):
        books=[{'book':'culture_fr_'+str(i),'language':'fra','fulltext':True} for i in range(130)]
        books += [{'book':'wikipedia_fr','language':'fra','fulltext':True}, {'book':'wikipedia_en','language':'eng','fulltext':True},
                  {'book':'wikibooks_fr','language':'fra','fulltext':False},{'book':'appropedia_en','language':'eng','fulltext':False}]
        manifest={row['book']+'.zim':{'archive':row['book']+'.zim','has_fulltext_index':True,'status':'kiwix_index','bytes':100} for row in books}
        calls=[]
        async def reader(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            names=parse_qs(urlsplit(path).query)['books.name'];calls.append(names)
            if any('wikipedia' in name for name in names):self.assertEqual(len(names),1)
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library.archive_index,'manifest',return_value=manifest),patch.object(library,'get',reader):
            _,coverage=await library.search_archives(lambda language:'generator','',5,query_plan=self.plan('générateur'))
        first=[call[0] for call in calls[:2]]
        self.assertEqual(set(first),{'wikibooks_fr','appropedia_en'})
        self.assertEqual(coverage['searched'],len(books));self.assertEqual(coverage['without_fulltext'],0)

    async def test_search_payload_keeps_index_counts_without_repeating_the_manifest(self):
        progress={'phase':'completed','archives':135,'completed':135,'articles':120,'workers':9,'results':[{'archive':'fixture'+str(i)+'.zim','status':'kiwix_index'} for i in range(135)]}
        with patch.object(library,'books',AsyncMock(return_value=[])),patch.object(library.archive_index,'status',return_value=progress):
            found=await library.search('comment faire du feu',kind='documents')
        self.assertEqual(found.coverage['local_index']['archives'],135)
        self.assertNotIn('results',found.coverage['local_index']);self.assertNotIn('fixture134',json.dumps(found.coverage))
        self.assertEqual(len(progress['results']),135)

    async def test_core_refinement_is_not_queued_after_every_general_collection(self):
        books=[{'book':'wikibooks_fr','language':'fra','fulltext':True},{'book':'appropedia_en','language':'eng','fulltext':True}]
        books += [{'book':'culture_fr_'+str(i),'language':'fra','fulltext':True} for i in range(30)]
        refined=asyncio.Event()
        async def reader(path):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);names=values['books.name'];pattern=values['pattern'][0]
            if all(name.startswith('culture') for name in names):await refined.wait()
            if len(pattern.split())==1:
                refined.set();book=names[0]
                return ('<rss><channel><item><title>Construction générateur à pédales</title><link>/content/'+book+'/Generator</link><description>Construction de générateur à pédales, fixture fictive sans procédure.</description></item></channel></rss>').encode(),'application/xml'
            return b'<rss><channel/></rss>','application/xml'
        def pattern(language,selected=None):return ' '.join(selected or ['generateur','pedales'])
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',reader):
            found,coverage=await asyncio.wait_for(library.search_archives(pattern,'',5,query_plan=self.plan('fabriquer un générateur à pédales')),1)
        self.assertTrue(refined.is_set());self.assertTrue(found);self.assertGreater(coverage['refinement_attempted'],0)
