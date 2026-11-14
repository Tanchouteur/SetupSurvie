"""Human-selected relevance expectations, tiny fictional excerpts, no real advice."""
import json
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit
from pilot import library,retrieval,store


DOCUMENTS=[
 ('botanique','Botanique — quiz','Quiz : quelle proposition est juste ? La sève comme allume feu est une réponse proposée, pas une procédure.'),
 ('var','Risques d’incendies dans le Var','Règlement départemental de prévention. Feu, incendie et risques.'),
 ('metaux','Métallurgie ancienne','Histoire du feu et des métaux. Production de fer.'),
 ('feu','Techniques de production de feu','Présentation des techniques de production du feu. Friction et percussion ; comparaison des méthodes. Extrait fictif sans instructions.'),
 ('generateur','Construction d’un générateur à pédales','Pedal generator construction. Materials, assembly diagram and checks. Fixture only.'),
 ('cyclisme','Histoire du cyclisme','Histoire de la pédale et du vélo.'),
 ('eau','Guide de potabilisation de l’eau','Drinking water treatment. Purification, equipment and checks. Fictional fixture.'),
 ('abri','Construction d’un abri','Shelter construction and roof design. Fictional fixture.'),
 ('radio','Réparation des radios','Radio repair and antenna inspection. Fictional fixture.'),
 ('graines','Conserver des semences','Seed storage and conservation. Fictional fixture.'),
 ('couture','Réparer un vêtement','Sewing and mending clothes. Fictional fixture.'),
 ('piles','Entretien des batteries','Battery maintenance and electrical inspection. Fictional fixture.'),
]


class SearchRelevanceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);guides=root/'guides';guides.mkdir()
        for key,title,text in DOCUMENTS:(guides/(key+'.fr.txt')).write_text(text,encoding='utf-8')
        (guides/'metadata.json').write_text(json.dumps([{'path':key+'.fr.txt','title':title,'language':'fr','provenance':'Fictional relevance fixture'} for key,title,_ in DOCUMENTS]))
        for name,value in [('ROOT',root/'state')]:
            p=patch.object(store,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(library,'GUIDES',guides);p.start();self.addCleanup(p.stop)
        p=patch.object(library,'books',AsyncMock(return_value=[]));p.start();self.addCleanup(p.stop)
        store.init();library.index_guides()
        self.addAsyncCleanup(library.kiwix_queries.close)

    async def test_practical_queries_rank_expected_documents_first_across_domains_and_variants(self):
        cases=[('faire du feu','feu'),('comment faire un feu','feu'),('allumer un feu','feu'),('peux tu m’expliquer comment faire du feu','feu'),('faire des feux','feu'),('techniques de feu','feu'),
               ('fabriquer un générateur à pédales','generateur'),('génératrice pédale','generateur'),('fabrication générateur pédales','generateur'),
               ('comment rendre eau potable','eau'),('eau potable','eau'),('construire un abri','abri'),('toit abri','abri'),
               ('réparer radio','radio'),('comment stocker les graines','graines'),('conservation semences','graines'),
               ('couture','couture'),('entretien batterie','piles')]
        for query,key in cases:
            with self.subTest(query=query):
                found=await library.search(query)
                self.assertTrue(found,query)
                self.assertEqual(found[0]['id'],'guide:'+key+'.fr.txt',[(r['title'],r['excerpt']) for r in found])
                self.assertNotIn('_text',found[0])

    async def test_other_intents_are_not_hidden_by_practical_ranking(self):
        for query,key in [('quiz botanique','botanique'),('risques incendies Var','var'),('histoire cyclisme','cyclisme'),('métallurgie','metaux')]:
            with self.subTest(query=query):self.assertEqual((await library.search(query))[0]['id'],'guide:'+key+'.fr.txt')

    async def test_different_pdf_pages_group_without_losing_navigation(self):
        with store.connect() as db:
            for page in [2,8,12]:db.execute('INSERT INTO passages VALUES(?,?,?,?,?)',(f'guide:manual.pdf#page={page}',f'Manuel — page {page}',f'/guides/manual.pdf#page={page}','fr','Feu, techniques et production. Extrait fictif.'))
        found=await library.search('feu')
        pdfs=[r for r in found if r['id'].startswith('guide:manual.pdf')]
        self.assertEqual(len(pdfs),1);self.assertEqual(len(pdfs[0]['other_matches']),2)
        self.assertTrue(all('#page=' in r['id'] for r in pdfs[0]['other_matches']))

    async def test_unknown_subject_does_not_fabricate_results(self):
        self.assertEqual(await library.search('propulsion quantique inexistante'),[])

    async def test_punctuation_and_search_syntax_remain_data(self):
        for query in ['" OR NOT * - ( )','feu" OR title:secret','😊']:
            with self.subTest(query=query):await library.search(query)

    async def test_wikipedia_is_a_scope_not_a_required_word_in_the_article(self):
        catalogue=[{'book':'wikipedia_fr','title':'Wikipédia','language':'fra','fulltext':True},
                   {'book':'appropedia_fr','title':'Appropedia','language':'fra','fulltext':True}]
        called=[]
        async def fetch(path,*args):
            params=parse_qs(urlsplit(path).query);called.append((path,params))
            if path.startswith('/suggest?'):
                return json.dumps([{'kind':'path','path':'A/Techniques_de_production_de_feu','label':'Techniques de production de feu','value':'Techniques de production de feu'}]).encode(),'application/json'
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=catalogue)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('faire du feu dans Wikipédia')
        self.assertEqual(len(found),1);self.assertIn('Techniques_de_production_de_feu',found[0]['id'])
        self.assertTrue(all(p.get('content',p.get('books.name'))==['wikipedia_fr'] for _,p in called))
        self.assertTrue(all('wikipedia' not in p.get('pattern',[''])[0].lower() for _,p in called))
        self.assertEqual(found.coverage['collection'],'wikipedia')

    async def test_fulltext_excerpt_wins_when_title_lookup_finishes_first(self):
        title_seen=asyncio.Event()
        async def fetch(path,*args):
            if path.startswith('/suggest?'):
                title_seen.set()
                return json.dumps([{'kind':'path','path':'Fire_making','label':'Fire making','value':'Fire making'}]).encode(),'application/json'
            await title_seen.wait()
            return b'<rss><channel><item><title>Fire making</title><link>/content/wikipedia_en/Fire_making</link><description>Actual indexed excerpt: friction and percussion, fictional data.</description></item></channel></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=[{'book':'wikipedia_en','language':'eng','fulltext':True}])),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('feu')
        article=next(r for r in found if r['id']=='zim:wikipedia_en/Fire_making')
        self.assertIn('Actual indexed excerpt',article['excerpt'])
        self.assertNotEqual(article.get('match'),'title')

    async def test_title_lookup_survives_fulltext_outage_and_rejects_external_or_traversal_paths(self):
        async def fetch(path,*args):
            if not path.startswith('/suggest?'):
                from fastapi import HTTPException
                raise HTTPException(400,'Fixture: no fulltext')
            return json.dumps([{'kind':'path','path':p,'label':'Fire making — '+p} for p in ['A/Fire_making','Wikijunior:Survie','https://evil.invalid/x','../private','%2e%2e/private']]+[{'kind':'pattern','path':'A/not-an-article'}]).encode(),'application/json'
        with patch.object(library,'books',AsyncMock(return_value=[{'book':'wikipedia_en','title':'Wikipedia','language':'eng','fulltext':True}])),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('faire du feu')
        self.assertEqual({r['id'] for r in found if r['id'].startswith('zim:')},{'zim:wikipedia_en/A/Fire_making','zim:wikipedia_en/Wikijunior:Survie'})
        self.assertEqual(found.coverage['status'],'partial')
