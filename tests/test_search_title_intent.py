"""Task titles versus passing mentions; fictional snippets, no corpus or model."""
import unittest
from pilot import library,retrieval


class TitleIntentTests(unittest.TestCase):
    def ordered(self,query,title,background,text):
        plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
        candidates=[
            {'id':'guide:background','title':background,'excerpt':text,'language':'fr','_rank':0},
            {'id':'zim:fixture/task','title':title,'excerpt':'Correspondance dans le titre ; ouvrir la source pour en vérifier le contenu.',
             'language':'fra','match':'title','_rank':1,'classification':{'method':'automatic','document_type':'unknown'}},
        ]
        return retrieval.ordered(candidates,plan,5)

    def test_explicit_task_title_precedes_a_general_text_mentioning_the_action(self):
        cases=[
            ('réparer un vélo','Mécanique vélo/Réparer un pneu','Les vélos d’aujourd’hui','Analyse fictive de la réparation des vélos et de leur durée de vie, sans étapes.'),
            ('installer un panneau solaire','Installer un panneau solaire','Les panneaux solaires modernes','Analyse fictive : installer un panneau solaire influence le coût de l’énergie, sans procédure.'),
            ('entretenir une vanne','Entretenir une vanne','La vanne et son rôle','Analyse fictive de l’entretien de la vanne et de sa durée de vie, sans étapes.'),
            ('how to repair a bicycle','Repair a bicycle tyre','Modern bicycles','A fictional survey of bicycle repair costs, without a procedure.'),
            ('how to install a solar panel','Install a solar panel','Modern solar panels','A fictional survey: install a solar panel changes the cost of power, without a procedure.'),
        ]
        for query,title,background,text in cases:
            with self.subTest(query=query):
                found=self.ordered(query,title,background,text)
                self.assertEqual(found[0]['id'],'zim:fixture/task')
                self.assertIn('guide:background',[row['id'] for row in found])

    def test_explanation_why_does_not_receive_the_task_title_priority(self):
        cases=[
            ('comment stocker les semences','Stocker les semences','Pourquoi stocker les semences','Analyse fictive : le stockage des semences conserve la diversité, sans étapes.'),
            ('how to store seeds','How to store seeds','Why we are storing seeds','Fictional seed storage discussion, without steps.'),
        ]
        for query,title,background,text in cases:
            with self.subTest(query=query):
                self.assertEqual(self.ordered(query,title,background,text)[0]['id'],'zim:fixture/task')

    def test_why_and_how_keeps_its_explicit_instruction_cue(self):
        found=self.ordered('comment stocker les semences','Pourquoi et comment stocker les semences','Pourquoi stocker les semences',
                           'Analyse fictive du stockage des semences, sans étapes.')
        self.assertEqual(found[0]['id'],'zim:fixture/task')

    def test_action_word_on_another_subject_does_not_gain_priority(self):
        found=self.ordered('réparer un vélo','Réparer une tente','Les vélos et leur réparation',
                           'Texte fictif sur la réparation des vélos.')
        self.assertEqual(found[0]['id'],'guide:background')

    def test_historical_request_keeps_the_general_article(self):
        found=self.ordered('histoire de la réparation des vélos','Réparer un vélo','Histoire de la réparation des vélos',
                           'Texte historique fictif sur les vélos et leur réparation.')
        self.assertEqual(found[0]['id'],'guide:background')

    def test_why_question_requests_an_explanation_instead_of_a_procedure(self):
        for query in ['pourquoi réparer un vélo','why repair a bicycle']:
            with self.subTest(query=query):
                plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
                self.assertFalse(plan.practical)
                self.assertNotIn('pourquoi',plan.words);self.assertNotIn('why',plan.words)
        found=self.ordered('pourquoi stocker les semences','Stocker les semences','Pourquoi stocker les semences',
                           'Explication fictive du stockage des semences.')
        self.assertEqual(found[0]['id'],'guide:background')

    def test_why_and_how_question_still_requests_a_practical_answer(self):
        for query in ['pourquoi et comment réparer un vélo','why and how to repair a bicycle']:
            with self.subTest(query=query):
                plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
                self.assertTrue(plan.practical)

    def test_title_priority_does_not_mark_the_document_as_a_verified_procedure(self):
        found=self.ordered('installer un panneau solaire','Installer un panneau solaire','Les panneaux solaires modernes',
                           'Analyse fictive : installer un panneau solaire influence le coût de l’énergie, sans procédure.')
        task=next(row for row in found if row['id']=='zim:fixture/task')
        self.assertEqual(task['match'],'title')
        self.assertEqual(task['classification'],{'method':'automatic','document_type':'unknown'})

    def test_prices_and_cost_guides_do_not_precede_an_actual_task_title(self):
        cases=[
            ('réparer un vélo','Mécanique vélo/Réparer un pneu','Prix de réparation d’un vélo'),
            ('réparer un vélo','Mécanique vélo/Réparer un pneu','Guide des prix de réparation de vélos'),
            ('entretenir une vanne','Entretenir une vanne','Coût d’entretien d’une vanne'),
            ('how to repair a bicycle','Repair a bicycle tyre','Bicycle repair costs'),
            ('how to repair a bicycle','Repair a bicycle tyre','Guide to bicycle repair prices'),
        ]
        for query,task,prices in cases:
            with self.subTest(query=query,prices=prices):
                found=self.ordered(query,task,prices,'Extrait fictif de tarifs, aucun mode opératoire lu.')
                self.assertEqual(found[0]['id'],'zim:fixture/task');self.assertEqual(len(found),2)

    def test_explicit_price_questions_still_find_the_price_overview(self):
        for query,task,prices in [
            ('prix de réparation d’un vélo','Mécanique vélo/Réparer un pneu','Prix de réparation d’un vélo'),
            ('bicycle repair costs','Repair a bicycle tyre','Bicycle repair costs'),
        ]:
            with self.subTest(query=query):
                found=self.ordered(query,task,prices,'Extrait fictif de prix de réparation, sans étapes.')
                self.assertEqual(found[0]['id'],'guide:background')

    def test_explicit_instructions_can_discuss_cost_without_becoming_a_price_list(self):
        for query,task,prices in [
            ('réparer un vélo','Comment réparer un vélo à petit prix','Prix de réparation d’un vélo'),
            ('how to repair a bicycle','How to repair a bicycle at low cost','Bicycle repair costs'),
        ]:
            with self.subTest(query=query):
                self.assertEqual(self.ordered(query,task,prices,'Extrait fictif de prix.')[0]['id'],'zim:fixture/task')

    def test_procedures_precede_equipment_lists_for_a_task(self):
        cases = [
            ('réparer une crevaison de vélo',
             'Comment coller une rustine pour réparer une chambre à air de vélo',
             'Bicycles/Maintenance and Repair/Tools and Supplies/Puncture Repair Kit',
             'A fictional bicycle puncture repair kit with patch and tools.'),
            ('réparer une crevaison de vélo', 'Mécanique vélo/Matériel/Réparer une crevaison',
             'Matériel pour réparer une crevaison de vélo',
             'Liste fictive de fournitures pour réparer une crevaison de vélo.'),
            ('réparer une crevaison de vélo', 'Comment réparer une crevaison de vélo avec un kit',
             'Trousse pour réparer une crevaison de vélo',
             'Liste fictive de fournitures pour réparer une crevaison de vélo.'),
        ]
        for query, task, equipment, text in cases:
            with self.subTest(equipment=equipment):
                found = self.ordered(query, task, equipment, text)
                self.assertEqual([row['id'] for row in found], ['zim:fixture/task', 'guide:background'])

    def test_equipment_requests_keep_the_equipment_heading_first(self):
        for query, task, equipment in (
            ('kit de réparation de vélo', 'Réparer une crevaison de vélo', 'Kit de réparation de vélo'),
            ('quel matériel pour réparer un vélo', 'Réparer un vélo', 'Matériel pour réparer un vélo'),
            ('bicycle repair kit', 'How to repair a bicycle tyre', 'Bicycle Repair Kit'),
        ):
            with self.subTest(query=query):
                found = self.ordered(query, task, equipment, equipment + '. Liste fictive.')
                self.assertEqual(found[0]['id'], 'guide:background')

    def test_recognized_actions_work_without_a_how_or_comment_prefix(self):
        cases=[
            ('remplacer un roulement','Remplacer un roulement','Prix de remplacement d’un roulement'),
            ('affûtage d’un couteau','Aiguiser un couteau','Tarifs d’affûtage d’un couteau'),
            ('conserver des semences','Stockage des semences','Coût du stockage des semences'),
            ('filtrer l’eau','Filtrer l’eau','Prix de filtration de l’eau'),
            ('install a solar panel','Install a solar panel','Solar panel installation costs'),
        ]
        for query,task,prices in cases:
            with self.subTest(query=query):
                found=self.ordered(query,task,prices,'Extrait fictif de tarifs, sans instructions.')
                self.assertEqual(found[0]['id'],'zim:fixture/task');self.assertEqual(len(found),2)


if __name__=='__main__':unittest.main()
