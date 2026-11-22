"""Conversational instructions must not become mandatory document keywords."""
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock,patch
from pilot import engine,library,retrieval,research
from pilot import store


class DocumentaryRequestTests(unittest.TestCase):
    def plan(self,question):return retrieval.plan(question,library.search_terms(question),library.SYNONYMS)

    def test_exact_notice_commands_prepare_a_search_before_requesting_the_manual(self):
        cases=[
            ('Selon la notice du contrôleur TQ-917, quelle touche efface sa mémoire ? Donne la commande exacte.','TQ-917'),
            ('Quelle commande indique le manuel du poste RZ-614 pour afficher son identifiant ?','RZ-614'),
            ('D’après la notice du contrôleur TQ-917, combien de secondes faut-il garder la touche appuyée ?','TQ-917'),
            ('According to the UV-5R manual, which button opens the settings?','UV-5R'),
        ]
        for question,reference in cases:
            with self.subTest(question=question):
                self.assertEqual(engine.document_request([{'role':'user','content':question}]),(question,''))
                self.assertEqual(research.notice_search_query(research.primary_query(question)),reference)

    def test_notice_reference_is_not_invented_or_reduced_to_one_of_several_devices(self):
        for question in ('Quelle touche indique la notice de mon appareil ?',
                         'Selon les notices TQ-917 et TQ-918, quelle commande diffère ?',
                         'Quel bouton ouvre le programme de demain ?', 'Calcule 12 fois 4'):
            with self.subTest(question=question):self.assertEqual(research.notice_search_query(question),question)

    def test_notice_followup_keeps_the_users_reference_and_collection_not_the_models_claim(self):
        history=[{'role':'user','content':'Selon la notice TQ-917 dans Wikipédia, quelle touche affiche son identifiant ?'},
                 {'role':'assistant','content':'La référence serait TQ-918. Aucun manuel disponible.'},
                 {'role':'user','content':'Et pour revenir à l’accueil, quelle touche ?'}]
        query,collection=engine.document_request(history)
        self.assertEqual(collection,'wikipedia');self.assertIn('TQ-917',query);self.assertNotIn('TQ-918',query)
        self.assertIn('revenir à l’accueil',query);self.assertNotIn('identifiant',query)
        self.assertEqual(research.notice_search_query(query),'TQ-917')
        self.assertEqual(engine.document_request(history[:-1]+[{'role':'user','content':'Et pour revenir à l’accueil, quelle touche dans Appropedia ?'}])[1],'appropedia')
        self.assertIsNone(engine.document_request(history[:-1]+[{'role':'user','content':'Et pour cette touche dans mes favoris ?'}]))
        self.assertIsNone(engine.document_request(history[:-1]+[{'role':'user','content':'Combien font 12 fois 3 ?'}]))
        changed=history[:-1]+[{'role':'user','content':'Comment planter des tomates ?'},history[-1]]
        query=engine.document_request(changed)
        self.assertTrue(query is None or 'TQ-917' not in query[0])

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

    def test_documents_describing_a_subject_do_not_require_the_description_verb(self):
        cases=[
            ('Fais une synthèse des documents expliquant comment faire du feu. Présente les techniques et cite les sources.', ['feu']),
            ('Résume les notices qui expliquent comment réparer un vélo', ['velo']),
            ('Prépare un résumé des guides décrivant la corrosion sur acier dans Wikipédia', ['corrosion','acier']),
            ('Give me a summary of the documents that explain how to start a fire', ['fire']),
        ]
        for question,words in cases:
            with self.subTest(question=question):
                plan=self.plan(research.primary_query(question))
                self.assertEqual(plan.words,words)
                self.assertEqual(plan.collection,'wikipedia' if 'Wikipédia' in question else '')
        # A verb inside the actual subject remains part of the search.
        question='Fais une synthèse des documents sur les modèles expliquant la corrosion sur acier'
        self.assertEqual(retrieval.search_subject(question),'les modeles expliquant la corrosion sur acier')

    def test_friction_followup_prepares_reading_before_the_model_decides_what_to_do(self):
        question='Des méthodes d’allumage au frottement (comme le feu de bois) ?'
        prepared=engine.document_request([{'role':'user','content':question}]);self.assertIsNotNone(prepared)
        plan=self.plan(question);self.assertNotIn('comme',plan.words)
        group=next(group for group in plan.groups if 'frottement' in group);self.assertIn('friction',group)

    def test_factual_questions_search_the_library_before_answering(self):
        for question in ('Quelle est la posologie du paracétamol pour un adulte ?',
                         'Quelles règles de sécurité pour la chasse sous-marine en apnée ?',
                         'Que faire en cas d’accident nucléaire ?', 'Pourquoi le pain lève-t-il ?'):
            with self.subTest(question=question):
                self.assertEqual(engine.document_request([{'role':'user','content':question}]),(question,''))
        for question in ('Bonjour', 'Merci beaucoup', 'Combien font deux plus deux ?'):
            self.assertIsNone(engine.document_request([{'role':'user','content':question}]))

    def test_numeric_answer_instructions_do_not_cancel_document_reading(self):
        for question in (
            'À partir des documents locaux, quelle longueur théorique faut-il pour un brin quart d’onde à 145 MHz ? Distingue le calcul théorique d’une dimension de fabrication.',
            'Comment dimensionner une pompe ? Donne le calcul et cite les sources.',
            'Calcule avec les documents la longueur théorique d’un dipôle à 433 MHz',
        ):
            with self.subTest(question=question):
                self.assertIsNotNone(engine.document_request([{'role':'user','content':question}]))
        for question in ('Calcule 12 * 4', 'Combien font deux plus deux ?', 'Convertir 2 m en cm'):
            self.assertIsNone(engine.document_request([{'role':'user','content':question}]))


class DocumentarySearchTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);root=Path(temporary.name)
        guides=root/'guides';guides.mkdir()
        documents=[('notice.fr.txt','Notice TQ-917','Contrôleur fictif TQ-917. Pour afficher l’identifiant du test, appuyer sur REPERE. Cette notice est une fixture sans appareil réel.'),
                   ('fire.fr.txt','Techniques de production de feu','Friction et percussion. Fire making avec du bois. Extrait fictif sans méthode réelle.'),
                   ('chemistry.fr.txt','Synthèse chimique de l’ammoniac','Synthèse chimique ammoniac. Données entièrement fictives.')]
        for name,title,text in documents:(guides/name).write_text(text,encoding='utf-8')
        (guides/'metadata.json').write_text(json.dumps([{'path':name,'title':title,'language':'fr'} for name,title,_ in documents]))
        for target,name,value in [(store,'ROOT',root/'state'),(library,'GUIDES',guides),(library,'books',AsyncMock(return_value=[]))]:
            changed=patch.object(target,name,value);changed.start();self.addCleanup(changed.stop)
        store.init();library.index_guides();self.addAsyncCleanup(library.kiwix_queries.close)

    async def test_reference_finds_the_manual_without_requiring_conversational_framing_in_it(self):
        question='Selon la notice du contrôleur TQ-917, quelle touche affiche son identifiant ? Donne la commande exacte.'
        query,collection=engine.document_request([{'role':'user','content':question}])
        found=await library.search(research.notice_search_query(research.primary_query(query)),collection=collection)
        self.assertEqual(found[0]['id'],'guide:notice.fr.txt')
        source=await library.source(found[0]['id']);self.assertIn('REPERE',source['text'])

    async def test_summary_instruction_finds_and_opens_the_same_source_as_its_topic(self):
        for question in ('comment faire du feu','Fait un synthese sur les info des document sur comment faire du feux',
                         'Fais une synthèse des documents expliquant comment faire du feu',
                         'Des méthodes d’allumage au frottement (comme le feu de bois) ?'):
            with self.subTest(question=question):
                found=await library.search(question,domain='resilience')
                self.assertTrue(found);self.assertEqual(found[0]['id'],'guide:fire.fr.txt')
                self.assertIn('Friction',(await library.source(found[0]['id']))['text'])

    async def test_technical_synthesis_stays_searchable(self):
        found=await library.search('synthèse chimique ammoniac')
        self.assertEqual(found[0]['id'],'guide:chemistry.fr.txt')


if __name__=='__main__':unittest.main()
