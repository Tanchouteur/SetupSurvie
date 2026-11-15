"""Source links cannot rewrite prose or invent references from model JSON."""
import unittest
from pilot import citation_links,engine,research


class CitationLinkTests(unittest.TestCase):
    def setUp(self):
        self.refs={};engine.reference(self.refs,{'id':'a','title':'Notice A','text':'Valeur fictive 17 unités.'},True)
        engine.reference(self.refs,{'id':'b','title':'Notice B','text':'Valeur fictive 23 unités.'},True)
        engine.reference(self.refs,{'id':'unread','title':'Non lu'})

    def test_server_fragments_get_read_source_numbers_without_rewriting_answer(self):
        answer='La première valeur est 17 unités. La seconde valeur est 23 unités.'
        linked,report=citation_links.apply(answer,{'citations':[{'fragment_id':'f0','source_number':1},{'fragment_id':'f1','source_number':2}]},self.refs)
        self.assertEqual(linked,'La première valeur est 17 unités. [1] La seconde valeur est 23 unités. [2]')
        self.assertEqual(report,{'applied':2,'rejected':0})

    def test_unknown_fragments_and_unread_sources_do_not_create_attribution(self):
        answer='Phrase répétée. Phrase répétée. Une observation fictive.'
        for identifier,number in (('invented',1),('f99',1),('f2',3),('f2',99),('f2',True)):
            linked,report=citation_links.apply(answer,{'citations':[{'fragment_id':identifier,'source_number':number}]},self.refs)
            self.assertEqual(linked,answer);self.assertEqual(report['applied'],0);self.assertEqual(report['rejected'],1)

    def test_citation_inside_last_table_cell_remains_visible_without_an_extra_column(self):
        answer='| Notice | Valeur | Source |\n| --- | --- | --- |\n| A | 17 unités | Notice A |'
        part=citation_links.fragments(answer)[-1]
        linked,report=citation_links.apply(answer,{'citations':[{'fragment_id':part['id'],'source_number':1}]},self.refs)
        self.assertEqual(linked,answer[:-1].rstrip()+' [1] |')
        self.assertEqual(report,{'applied':1,'rejected':0})
        self.assertEqual(part['text'],'| A | 17 unités | Notice A |')

    def test_code_is_not_modified_or_mistaken_for_documentary_citations(self):
        answer='```python\nresultat = tableau[1] + tableau[99]\n```'
        linked,report=citation_links.apply(answer,{'citations':[{'fragment_id':'f0','source_number':1}]},self.refs)
        self.assertEqual(linked,answer);self.assertEqual(report['rejected'],1)
        self.assertEqual(research.citation_numbers(answer),set())
        self.assertIn('tableau[99]',citation_links.unverified(answer,self.refs))

    def test_linker_prompt_is_bounded_and_distinct_from_question_answer_generation(self):
        messages=citation_links.messages('Une observation fictive.',self.refs,2000)
        self.assertIsNotNone(messages);self.assertLessEqual(research.size(messages),2000)
        self.assertIn('Ne réécris aucun fait',messages[0]['content'])
        self.assertNotIn('Non lu',messages[1]['content'])
        self.assertIsNone(citation_links.messages('x'*4000,self.refs,2000))


if __name__=='__main__':unittest.main()
