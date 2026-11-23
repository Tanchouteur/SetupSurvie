"""Number variants on real tiny guide indexes; no corpus, model or actual advice."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit

from pilot import library,research,retrieval,store


class InflectionSearchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.guides=root/'guides';self.guides.mkdir();self.metadata=[]
        for module,name,value in ((store,'ROOT',root/'state'),(library,'GUIDES',self.guides),(library,'books',AsyncMock(return_value=[]))):
            change=patch.object(module,name,value);change.start();self.addCleanup(change.stop)
        store.init();self.addAsyncCleanup(library.kiwix_queries.close)

    def add(self,key,title,text='Texte fictif réservé à la recherche, sans conseil réel.'):
        name=key+'.fr.txt';(self.guides/name).write_text(text)
        self.metadata.append({'path':name,'title':title,'language':'fr'})

    def index(self):
        (self.guides/'metadata.json').write_text(json.dumps(self.metadata));library.index_guides()

    async def test_common_singular_and_plural_forms_work_in_both_directions_on_the_actual_index(self):
        pairs=[('couteau','couteaux'),('tuyau','tuyaux'),('ruche','ruches'),('compteur','compteurs'),
               ('jardin','jardins'),('cheval','chevaux'),('journal','journaux'),('travail','travaux'),
               ('étau','étaux'),('bal','bals'),('bail','baux'),('joujou','joujoux'),('lieu','lieux')]
        for i,(singular,plural) in enumerate(pairs):
            self.add(f'singular-{i}',singular);self.add(f'plural-{i}',plural)
        self.index()
        for i,pair in enumerate(pairs):
            for query in pair:
                with self.subTest(query=query):
                    found=await library.search(query)
                    self.assertEqual({r['id'] for r in found},{f'guide:singular-{i}.fr.txt',f'guide:plural-{i}.fr.txt'})
                    self.assertEqual(found[0]['title'],query,'Exact wording must retain priority.')

    async def test_a_practical_question_keeps_its_other_subject_constraint(self):
        self.add('copper','Réparer les tuyaux en cuivre')
        self.add('plastic','Réparer les tuyaux en plastique')
        self.add('history','Histoire du cuivre')
        self.index()
        found=await library.search('réparer un tuyau en cuivre')
        self.assertEqual([row['id'] for row in found],['guide:copper.fr.txt'])
        self.assertIn('Texte fictif', (await library.source(found[0]['id']))['text'])

    async def test_invariant_words_do_not_silently_become_another_subject(self):
        for i,(query,other) in enumerate([('Paris','pari'),('cours','cour'),('poids','poid'),('sens','sen'),
                                        ('temps','temp'),('corps','corp'),('siemens','siemen'),('HTTPS','http')]):
            self.add(f'exact-{i}',query);self.add(f'other-{i}',other)
        self.index()
        for i,query in enumerate(('Paris','cours','poids','sens','temps','corps','siemens','HTTPS')):
            with self.subTest(query=query):
                self.assertEqual([r['id'] for r in await library.search(query)],[f'guide:exact-{i}.fr.txt'])

    async def test_model_references_and_frequency_values_remain_exact(self):
        self.add('wanted','UV5R 145MHz');self.add('other-model','UV5RS 145MHz');self.add('other-frequency','UV5R 146MHz');self.index()
        self.assertEqual([r['id'] for r in await library.search('UV5R 145MHz')],['guide:wanted.fr.txt'])

    async def test_ambiguous_normalized_terms_do_not_expand_into_a_different_word(self):
        self.add('vise','étaux');self.add('stall','étal');self.add('mail','email');self.add('enamel','émaux');self.index()
        for query,key in [('étaux','vise'),('étal','stall'),('email','mail'),('émaux','enamel')]:
            with self.subTest(query=query):self.assertEqual([r['id'] for r in await library.search(query)],[f'guide:{key}.fr.txt'])

    def test_related_forms_do_not_create_extra_required_groups_or_an_english_translation(self):
        plan=retrieval.plan('couteau couteaux',library.search_terms('couteau couteaux'),library.SYNONYMS)
        self.assertEqual(len(plan.groups),1)
        self.assertEqual(plan.title_en,'couteau','A guessed plural is not an English translation.')
        radio=retrieval.plan('radio',library.search_terms('radio'),library.SYNONYMS)
        self.assertIn('radio',radio.groups[0])

    def test_document_reading_selects_the_passage_with_the_other_number_form(self):
        text='Contexte fictif sans rapport. '*300+'Repère conservé : les couteaux sont le sujet de cet extrait fictif. '+'Autre contexte fictif. '*200
        parts=research.passages(text,'couteau',900)
        self.assertTrue(any('Repère conservé' in part['text'] for part in parts))
        self.assertTrue(all(text[part['offset']:part['next_offset']]==part['text'] for part in parts))

    async def title_search(self,primary_matches):
        calls=[];book={'book':'title_only_fr','title':'Fictional titles','language':'fra','fulltext':False}
        async def get(path,*args):
            if path.startswith('/suggest?'):
                term=parse_qs(urlsplit(path).query)['term'][0];calls.append(term)
                good=primary_matches or term=='tuyau cuivre'
                value=[{'kind':'path','path':'Copper' if good else 'Plastic','value':'Tuyau en cuivre' if good else 'Tuyaux en plastique'}]
                return json.dumps(value).encode(),'application/json'
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(library,'get',get):
            found=await library.search('tuyaux cuivre',diagnostic=True)
        self.assertEqual([r['id'] for r in found],['zim:title_only_fr/Copper'])
        return calls,found.coverage

    async def test_title_fallback_tries_an_alias_when_the_original_titles_miss_the_subject(self):
        calls,coverage=await self.title_search(False)
        self.assertEqual(calls,['tuyaux cuivre','tuyau cuivre'])
        self.assertEqual(coverage['title_refinement_requests'],1)
        self.assertEqual(coverage['status'],'partial','A title match does not invent a fulltext index.')

    async def test_a_useful_original_title_does_not_trigger_extra_requests(self):
        calls,coverage=await self.title_search(True)
        self.assertEqual(calls,['tuyaux cuivre']);self.assertEqual(coverage['title_refinement_requests'],0)

    def test_title_alias_attempts_are_bounded_and_keep_all_other_words(self):
        query='canaux journaux travaux cuivre'
        plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
        forms=retrieval.title_forms(plan)
        self.assertEqual(forms[0],query);self.assertLessEqual(len(forms),5)
        self.assertTrue(all('cuivre' in form and len(form.split())==4 for form in forms))


class TechnicalVocabularyTests(unittest.TestCase):
    def plan(self, query):
        return retrieval.plan(query, library.search_terms(query), library.SYNONYMS)

    def test_grounding_keeps_the_electrical_expression_together(self):
        plan = self.plan('mise à la terre d’une installation')
        self.assertEqual(plan.words, ['mise a la terre'])
        self.assertIn('grounding', plan.groups[0])
        hits = retrieval.ordered([
            {'id': 'guide:other', 'title': 'Installation de la nappe de l’écran', 'excerpt': 'Mettre à la terre.'},
            {'id': 'guide:grounding', 'title': 'Standards for Grounding and Lightning Protection'},
        ], plan, 5)
        self.assertEqual([hit['id'] for hit in hits], ['guide:grounding'])

    def test_seed_saving_matches_the_french_subject_without_unrelated_words(self):
        for query in ('seed saving for vegetable garden', 'conserver les graines du potager'):
            with self.subTest(query=query):
                plan = self.plan(query)
                self.assertEqual(plan.action, 'preserve')
                self.assertEqual(len(plan.groups), 2)
                self.assertTrue(any('potageres' in group for group in plan.groups))
                self.assertTrue(any('semences' in group for group in plan.groups))


if __name__=='__main__':unittest.main()
