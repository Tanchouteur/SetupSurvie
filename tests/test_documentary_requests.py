"""Conversational instructions must not become mandatory document keywords."""
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock,patch
from pilot import engine,library,retrieval
from pilot import store


class DocumentaryRequestTests(unittest.TestCase):
    def plan(self,question):return retrieval.plan(question,library.search_terms(question),library.SYNONYMS)

    def test_marcs_actual_summary_request_keeps_the_topic_instead_of_the_output_format(self):
        questions=['Fait un synthese sur les info des document sur comment faire du feux',
                   'Fais une synthèse des informations des documents sur comment faire du feu',
                   'Peux-tu me faire un résumé des documents concernant comment faire du feu ?',
                   'Résume les documents sur comment faire du feu',
                   'Give me a summary of the documents about how to start a fire']
        for question in questions:
            with self.subTest(question=question):
                plan=self.plan(question);self.assertEqual(plan.words,['feu'] if 'fire' not in question else ['fire'])
                self.assertEqual(plan.action,'ignite');self.assertEqual(plan.original,question)
                self.assertIsNotNone(engine.document_request([{'role':'user','content':question}]))

    def test_instructions_do_not_hide_real_technical_synthesis_subjects(self):
        for question in ('synthèse chimique ammoniac','synthèse des protéines','résumé statistique','histoire de la synthèse musicale'):
            with self.subTest(question=question):
                plan=self.plan(question)
                self.assertTrue(any(word in plan.words for word in ('synthese','resume')))
        question='Fais une synthèse des documents sur la synthèse chimique de l’ammoniac'
        self.assertIn('synthese',self.plan(question).words);self.assertIn('ammoniac',self.plan(question).words)

    def test_real_subject_prepositions_and_source_scope_are_preserved(self):
        question='Fais une synthèse des documents sur la corrosion sur acier dans Wikipédia'
        plan=self.plan(question);self.assertIn('corrosion',plan.words);self.assertIn('acier',plan.words)
        self.assertEqual(plan.collection,'wikipedia')
        self.assertEqual(retrieval.search_subject('Résume le document associé'),'Résume le document associé')

    def test_friction_followup_prepares_reading_before_the_model_decides_what_to_do(self):
        question='Des méthodes d’allumage au frottement (comme le feu de bois) ?'
        prepared=engine.document_request([{'role':'user','content':question}]);self.assertIsNotNone(prepared)
        plan=self.plan(question);self.assertNotIn('comme',plan.words)
        group=next(group for group in plan.groups if 'frottement' in group);self.assertIn('friction',group)


class DocumentarySearchTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);root=Path(temporary.name)
        guides=root/'guides';guides.mkdir()
        documents=[('fire.fr.txt','Techniques de production de feu','Friction et percussion. Fire making avec du bois. Extrait fictif sans méthode réelle.'),
                   ('chemistry.fr.txt','Synthèse chimique de l’ammoniac','Synthèse chimique ammoniac. Données entièrement fictives.')]
        for name,title,text in documents:(guides/name).write_text(text,encoding='utf-8')
        (guides/'metadata.json').write_text(json.dumps([{'path':name,'title':title,'language':'fr'} for name,title,_ in documents]))
        for target,name,value in [(store,'ROOT',root/'state'),(library,'GUIDES',guides),(library,'books',AsyncMock(return_value=[]))]:
            changed=patch.object(target,name,value);changed.start();self.addCleanup(changed.stop)
        store.init();library.index_guides();self.addAsyncCleanup(library.kiwix_queries.close)

    async def test_summary_instruction_finds_and_opens_the_same_source_as_its_topic(self):
        for question in ('comment faire du feu','Fait un synthese sur les info des document sur comment faire du feux',
                         'Des méthodes d’allumage au frottement (comme le feu de bois) ?'):
            with self.subTest(question=question):
                found=await library.search(question,domain='resilience')
                self.assertTrue(found);self.assertEqual(found[0]['id'],'guide:fire.fr.txt')
                self.assertIn('Friction',(await library.source(found[0]['id']))['text'])

    async def test_technical_synthesis_stays_searchable(self):
        found=await library.search('synthèse chimique ammoniac')
        self.assertEqual(found[0]['id'],'guide:chemistry.fr.txt')


if __name__=='__main__':unittest.main()
