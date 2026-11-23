"""Human-selected relevance expectations, tiny fictional excerpts, no real advice."""
import json
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit
from pilot import collection_sort,library,network,retrieval,store


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

    async def test_real_guide_index_distinguishes_a_repair_request_from_a_price_request(self):
        rows=[('bicycle-task.fr.txt','Mécanique vélo/Réparer un pneu','Texte de recette fictif : réparer un pneu de vélo, 17 repères inventés. Aucun conseil réel.'),
              ('bicycle-prices.fr.txt','Prix de réparation d’un vélo','Extrait fictif des prix de réparation du vélo, aucune procédure.')]
        metadata=json.loads((library.GUIDES/'metadata.json').read_text())
        for path,title,text in rows:
            (library.GUIDES/path).write_text(text);metadata.append({'path':path,'title':title,'language':'fr'})
        (library.GUIDES/'metadata.json').write_text(json.dumps(metadata));library.index_guides()
        tasks=await library.search('réparer un vélo')
        self.assertEqual(tasks[0]['id'],'guide:bicycle-task.fr.txt');self.assertIn('guide:bicycle-prices.fr.txt',[item['id'] for item in tasks])
        read=await library.source(tasks[0]['id']);self.assertIn('17 repères inventés',read['text'])
        prices=await library.search('prix de réparation d’un vélo');self.assertEqual(prices[0]['id'],'guide:bicycle-prices.fr.txt')

    async def test_different_pdf_pages_group_without_losing_navigation(self):
        with store.connect() as db:
            for page in [2,8,12]:db.execute('INSERT INTO passages VALUES(?,?,?,?,?)',(f'guide:manual.pdf#page={page}',f'Manuel — page {page}',f'/guides/manual.pdf#page={page}','fr','Feu, techniques et production. Extrait fictif.'))
        found=await library.search('feu')
        pdfs=[r for r in found if r['id'].startswith('guide:manual.pdf')]
        self.assertEqual(len(pdfs),1);self.assertEqual(len(pdfs[0]['other_matches']),2)
        self.assertTrue(all('#page=' in r['id'] for r in pdfs[0]['other_matches']))

    async def test_unknown_subject_does_not_fabricate_results(self):
        self.assertEqual(await library.search('propulsion quantique inexistante'),[])

    async def test_civil_protection_finds_official_guidance_vocabulary(self):
        with store.connect() as db:
            db.execute('INSERT INTO passages VALUES(?,?,?,?,?)', (
                'guide:consignes.pdf#page=9', 'Se préparer aux crises — page 9',
                '/guides/consignes.pdf#page=9', 'fr',
                'Menace en lien avec un engagement majeur. Respectez les consignes des autorités et rejoignez un abri.',
            ))
        for query in ('protection civile en temps de guerre', 'abri en cas de bombardement'):
            with self.subTest(query=query):
                found=await library.search(query,domain='resilience')
                self.assertIn('guide:consignes.pdf#page=9',[item['id'] for item in found])

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


    async def test_autonomy_surfaces_only_strong_main_encyclopedia_fallbacks(self):
        books = [
            {'id': 'zim:wikipedia_fr_all/Orage', 'book': 'wikipedia_fr_all',
             'kind': 'article', 'title': 'Orage', 'excerpt': 'Phénomène météorologique.',
             'language': 'fr'},
            {'id': 'zim:wikipedia_fr_all/Feu', 'book': 'wikipedia_fr_all',
             'kind': 'article', 'title': 'Production de feu', 'excerpt': 'Allumage fictif.',
             'language': 'fr'},
            {'id': 'zim:wiktionary_fr_all/Orage', 'book': 'wiktionary_fr_all',
             'kind': 'article', 'title': 'Orage', 'excerpt': 'Reconnaître un orage.',
             'language': 'fr'},
            {'id': 'zim:encyclopedie-environnement_fr_all/Orage', 'book': 'encyclopedie-environnement_fr_all',
             'kind': 'article', 'title': 'Orage', 'excerpt': 'Reconnaître un orage.',
             'language': 'fr'},
            {'id': 'zim:wikipedia_fr_all/Tanner', 'book': 'wikipedia_fr_all',
             'kind': 'article', 'title': 'Classification de Tanner', 'excerpt': 'Description de la peau.',
             'language': 'fr'},
        ]
        # A fixture without a named publisher exercises the guide-kind condition.
        with patch.object(library, 'search_archives', AsyncMock(return_value=(books, {'status': 'complete'}))):
            results = await library.search('reconnaître un orage', domain='resilience', kind='documents')
            self.assertEqual([row['id'] for row in results], [books[0]['id']])
            self.assertTrue(results[0]['reference_fallback'])
            self.assertFalse(await library.search('tanner une peau', domain='resilience', kind='documents'))
            results = await library.search('faire du feu', domain='resilience', kind='documents')
            self.assertEqual(results[0]['id'], 'guide:feu.fr.txt')
            self.assertFalse(any(row.get('reference_fallback') for row in results))

    async def test_technical_forums_offer_a_precise_reference_below_a_practical_guide(self):
        forum = 'diy.stackexchange.com_en_all'
        entry = {'id': f'zim:{forum}/question', 'book': forum, 'kind': 'article', 'language': 'en',
                 'title': 'How to repair a leaking pipe', 'excerpt': 'Fictional search fixture.'}
        context = {'id': 'zim:ifixit_fr_all/aquarium', 'book': 'ifixit_fr_all', 'kind': 'article',
                   'language': 'fr', 'title': 'Remplacement du filtre de l’aquarium',
                   'excerpt': 'Un cas fictif de réparation de fuite liée à un tuyau.'}
        guide = {**context, 'id': 'zim:ifixit_fr_all/tuyau',
                 'title': 'Réparer une fuite sur un tuyau'}
        rows = [entry, context, {**entry, 'id': f'zim:{forum}/other',
                                'title': 'How to repair a table'}]
        with patch.object(library, 'search_archives', AsyncMock(return_value=(rows, {'status': 'complete'}))), \
             patch.object(network, 'CATALOG', store.ROOT):
            query = 'réparer une fuite de tuyau'
            results = await library.search(query, domain='resilience', kind='documents')
            self.assertEqual([row['id'] for row in results], [entry['id'], context['id']])
            self.assertEqual(results[0]['classification']['source_role'], 'reference')
            self.assertNotIn('reference_fallback', results[0])
            french = await library.search(query, 'fr', domain='resilience', kind='documents')
            self.assertEqual([row['id'] for row in french], [context['id']])

            rows.append(guide)
            results = await library.search(query, domain='resilience', kind='documents')
            self.assertEqual([row['id'] for row in results], [guide['id'], context['id']])

            rows.remove(guide)
            collection_sort.save(store.ROOT, collection_sort.Sort(other=frozenset({collection_sort.archive(forum)})))
            results = await library.search(query, domain='resilience', kind='documents')
            self.assertEqual([row['id'] for row in results], [context['id']])

    def test_encyclopedia_fallback_prefers_the_exact_spelled_subject_over_an_accent_homograph(self):
        bee_home = {'id': 'zim:wikipedia_fr_all/Ruche', 'title': 'Ruche', 'language': 'fr'}
        grape = {'id': 'zim:wikipedia_fr_all/Ruche_vin', 'title': 'Ruché', 'language': 'fr'}
        index = {'id': 'zim:wikipedia_fr_all/Ruche_homonymie', 'title': 'Ruche (homonymie)', 'language': 'fr'}
        query = 'installer une ruche'
        plan = retrieval.plan(query, library.search_terms(query), library.SYNONYMS)
        self.assertEqual([item['id'] for item in retrieval.encyclopedic_matches([grape, index, bee_home], plan, 3)],
                         [bee_home['id']])
        self.assertTrue(retrieval.encyclopedic_matches([grape], plan, 3))

    def test_practical_guide_pages_stay_in_autonomie_whatever_the_page_words(self):
        page = {'id': 'guide:msf.fr.pdf#page=251', 'title': 'Médicaments essentiels — page 251',
                'provenance': 'MSF — https://example.invalid — édition 2026', '_text': 'Paracétamol. Histoire et sciences.'}
        self.assertEqual(retrieval.application_domains(page, ['culture']), ['resilience'])
        unknown = {**page, 'provenance': 'Éditeur inconnu — https://example.invalid'}
        self.assertEqual(retrieval.application_domains(unknown, ['culture']), ['culture'])
        self.assertNotIn('chez', library.search_terms("soigner une diarrhée chez l'enfant"))

    def test_guide_title_naming_the_subject_relaxes_a_natural_question(self):
        query = "Comment rendre l'eau potable en cas de coupure d'eau ?"
        plan = retrieval.plan(query, library.search_terms(query), library.SYNONYMS)
        page = {'title': 'Eau : traitement au point d’utilisation — page 1', 'excerpt': 'Rendre l’eau potable.',
                '_text': 'Traitement de l’eau potable en urgence. Extrait fictif.'}
        generic = {'title': 'Abri : sécurité de la construction — page 4', 'excerpt': 'Stocker le matériel.',
                   '_text': 'Sécurité du chantier. Extrait fictif.'}
        self.assertTrue(retrieval.subject_in_passage(page, plan))
        query = 'stocker une arme en sécurité'
        plan = retrieval.plan(query, library.search_terms(query), library.SYNONYMS)
        self.assertFalse(retrieval.subject_in_passage(generic, plan))

    def test_pdf_page_text_counts_only_when_query_terms_are_close(self):
        query = 'posologie du paracétamol'
        plan = retrieval.plan(query, library.search_terms(query), library.SYNONYMS)
        close = {'title': 'Médicaments essentiels — page 40', 'excerpt': 'Comprimés à 500 mg.',
                 '_text': 'Paracétamol oral. Posologie chez l’adulte : extrait fictif sans dose réelle.'}
        apart = {'title': 'Médicaments essentiels — page 3', 'excerpt': 'Sommaire.',
                 '_text': 'Posologie générale. ' + 'mot ' * 80 + 'Paracétamol cité dans une autre partie.'}
        self.assertTrue(retrieval.subject_in_passage(close, plan))
        self.assertFalse(retrieval.subject_in_passage(apart, plan))

    async def test_pdf_passages_need_the_subject_in_the_visible_match(self):
        items = [
            ('guide:jardin.fr.pdf#page=1', 'Jardin scolaire', '', 'fr', 'Éviter les insectes et organiser le jardin.'),
            ('guide:habitat.fr.pdf#page=2', 'Limiter les moisissures', '', 'fr', 'Comment éviter les moisissures.'),
        ]
        with store.connect() as db:
            db.executemany('INSERT INTO passages VALUES(?,?,?,?,?)', items)
        results = await library.search('éviter les moisissures', kind='documents')
        self.assertEqual([row['id'] for row in results], [items[1][0]])
