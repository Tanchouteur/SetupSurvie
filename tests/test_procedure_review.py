import unittest
from pilot import procedure_review


class ProcedureReviewTests(unittest.TestCase):
    def setUp(self):
        self.text='Avant de commencer, sélectionner la ligne supérieure du cadran fictif. Ensuite choisir un canal libre.'
        self.references={'guide:a':{'number':2,'consulted':True}}
        self.trace=[{'tool':'read_sources','result':{'results':[{'id':'guide:a','passages':[{'offset':0,'text':self.text}]}]}}]

    def test_only_actual_read_sentences_are_candidates_and_model_selects_ids(self):
        parts=procedure_review.segments(self.trace,self.references)
        self.assertEqual(parts,[{'id':'condition-0','source_number':2,'text':'Avant de commencer, sélectionner la ligne supérieure du cadran fictif.'}])
        answer,result=procedure_review.apply('Choisir un canal [2].',{'missing_conditions':['condition-0']},parts)
        self.assertIn('> '+parts[0]['text'],answer);self.assertEqual(result,{'selected':1,'rejected':0})
        self.references['guide:a']['consulted']=False
        self.assertEqual(procedure_review.segments(self.trace,self.references),[])

    def test_fabricated_condition_rejected_and_document_markup_escaped(self):
        parts=[{'id':'condition-0','source_number':2,'text':'Avant : <img src=x> [99] [2] ![x](https://external/)'}]
        answer,result=procedure_review.apply('Texte',{'missing_conditions':['invented']},parts)
        self.assertEqual(answer,'Texte');self.assertEqual(result['rejected'],1)
        answer,_=procedure_review.apply('Texte',{'missing_conditions':['condition-0']},parts)
        self.assertNotIn('<img',answer);self.assertNotIn('![x]',answer)
        self.assertEqual(__import__('pilot.research',fromlist=['citation_numbers']).citation_numbers(answer),{2})
        self.assertIn('` [2] `',answer)

    def test_review_budget_and_no_selection_preserve_answer(self):
        parts=procedure_review.segments(self.trace,self.references)
        self.assertIsNone(procedure_review.packet('Comment faire ?','Réponse',parts,20))
        self.assertIsNotNone(procedure_review.packet('Comment faire ?','Réponse',parts,4000))
        self.assertEqual(procedure_review.apply('Texte',{'missing_conditions':[]},parts),('Texte',{'selected':0,'rejected':0}))

    def test_prerequisite_question_does_not_trigger_another_procedure_check(self):
        self.assertFalse(procedure_review.requested('Et quelles conditions dois-je vérifier avant cette procédure ?'))
        self.assertTrue(procedure_review.requested('Et comment reprendre les étapes de cette procédure ?'))
