"""Observed title pitfalls, with fictional equal excerpts, never verified articles."""
import unittest
from pilot import library,retrieval


class TitleScopeTests(unittest.TestCase):
    def ordered(self,query,titles,text):
        plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
        rows=[{'id':'zim:fixture/'+str(i),'title':title,'excerpt':text,'language':'en','_rank':i,
               'classification':{'method':'automatic','document_type':'unknown'}} for i,title in enumerate(titles)]
        return retrieval.ordered(rows,plan,10)

    def test_installation_precedes_incidental_questions_and_hazard_overviews(self):
        titles=['Should I upgrade my electrical panel during a solar installation',
                'Simplest solar panel home installation to power electric heaters?',
                'Occupational hazards of solar panel installation',
                'How many solar panels should a beginner install?',
                'Should I upgrade my electrical panel during a DIY solar installation?',
                'DIY solar panel installation safety risks',
                'DIY Solar Panel Install']
        for query in ('installer un panneau solaire','how to install a solar panel'):
            with self.subTest(query=query):
                rows=self.ordered(query,titles,'Fictional solar panel installation text. No actual instructions.')
                self.assertEqual(rows[0]['title'],titles[-1]);self.assertEqual(len(rows),7)
                self.assertTrue(all(row['classification']['document_type']=='unknown' for row in rows))

    def test_explicit_how_to_diagnose_precedes_a_specific_screen_repair(self):
        for query,titles in [
            ('réparer un poste radio',['1998-2003 Mazda Radio LCD Screen Repair','How to diagnose and repair a radio?']),
            ('réparer une radio',['Réparation écran autoradio Mazda','Comment diagnostiquer et réparer une radio ?']),
            ('radio repair',['Radio screen repair','Radio repair manual']),
            ('radio repair',['Radio screen repair','How should I diagnose and repair a radio?']),
            ('radio repair',['Radio screen repair','How do you diagnose and repair a radio?']),
            ('réparer une radio',['Réparation écran radio','Manuel de réparation radio'])]:
            with self.subTest(query=query):
                rows=self.ordered(query,titles,'Fictional radio repair diagnostic text. No actual instructions.')
                self.assertEqual(rows[0]['title'],titles[-1]);self.assertEqual(len(rows),2)

    def test_literal_subject_keeps_function_words_in_its_title_match(self):
        titles=['Any help with the History of a Fleetwood Bicycle 1963',
                'Pedaling History Bicycle Museum','Histoire du vélo']
        rows=self.ordered('histoire du vélo',titles,'Fictional bicycle history text.')
        self.assertEqual(rows[0]['title'],'Histoire du vélo');self.assertEqual(len(rows),3)
        self.assertEqual(self.ordered('les fractions',['Some fractions','Les fractions'],'Fictional fractions text.')[0]['title'],'Les fractions')

    def test_food_preservation_queries_keep_the_subject_in_both_languages(self):
        for query in ('conservation des aliments','conservation alimentaire','comment conserver la nourriture','food preservation'):
            with self.subTest(query=query):
                plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
                self.assertEqual(retrieval.title_forms(plan),['conservation des aliments'])
                self.assertEqual(retrieval.title_forms(plan,english=True),['food preservation'])
        for title in ('Conservation des aliments','Conserver les aliments','Stockage de la nourriture','Food storage'):
            with self.subTest(title=title):
                self.assertIn('resilience',retrieval.domains({'title':title}))

    def test_practical_search_ranks_topic_resources_ahead_of_reference_entries(self):
        query='conservation des aliments'
        plan=retrieval.plan(query,library.search_terms(query),library.SYNONYMS)
        candidates=[
            {'id':'zim:wiktionary_fr/Thésaurus:conservation_des_aliments','title':'Thésaurus:conservation des aliments','excerpt':'Vocabulaire de la conservation des aliments.'},
            {'id':'zim:wikisource_fr/Page:Traité_des_alimens/10','title':'Page:Traité des alimens/10','excerpt':'Mention de la conservation des aliments.'},
            {'id':'zim:wikipedia_fr/Conservation_des_aliments','title':'Conservation des aliments','excerpt':''},
            {'id':'zim:wikibooks_fr/Guide','title':'Conservation alimentaire','excerpt':'Présentation fictive de la conservation des aliments.'},
        ]
        ordered=retrieval.ordered(candidates,plan,10)
        self.assertEqual({row['id'] for row in ordered[:2]},{candidates[2]['id'],candidates[3]['id']})
        self.assertEqual(len(ordered),len(candidates))
        explicit=retrieval.plan(query,library.search_terms(query),library.SYNONYMS,collection='wiktionary')
        self.assertGreater(retrieval.rank(candidates[0],explicit),retrieval.rank(candidates[0],plan))

    def test_contextual_subjects_are_still_found_when_explicitly_requested(self):
        for query,title in [
            ('occupational hazards of solar panel installation','Occupational hazards of solar panel installation'),
            ('should I upgrade my electrical panel during a solar installation','Should I upgrade my electrical panel during a solar installation'),
            ('how many solar panels should a beginner install','How many solar panels should a beginner install?')]:
            with self.subTest(query=query):
                rows=self.ordered(query,[title,'DIY Solar Panel Install'],'Fictional solar panel installation text, no instructions.')
                self.assertEqual(rows[0]['title'],title)


if __name__=='__main__':unittest.main()
