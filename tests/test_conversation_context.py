import unittest
from pilot import conversation_context


class ContextTests(unittest.TestCase):
    def test_identifiers_survive_followup_without_inheriting_proof_or_numbers(self):
        history=[{'role':'user','content':'Procédure A'},
                 {'role':'assistant','content':'Ancienne réponse [42].','sources':[],
                  'documentary':{'consulted_sources':[{'id':'guide:a','title':'Ancienne notice','number':42,'excerpt':'Ancienne valeur'}]}},
                 {'role':'user','content':'Et les conditions ?'}]
        result=conversation_context.previous_sources(history)
        self.assertEqual(result,{'previous_question':'Procédure A','historical_sources':[{'id':'guide:a','title':'Ancienne notice','consulted':False}]})

    def test_empty_latest_exchange_does_not_reach_back_to_unrelated_sources(self):
        history=[{'role':'assistant','sources':[{'id':'guide:a','title':'A'}]},
                 {'role':'user','content':'Autre sujet'}, {'role':'assistant','sources':[]}, {'role':'user','content':'Et ensuite ?'}]
        self.assertIsNone(conversation_context.previous_sources(history))

    def test_legacy_sources_and_invalid_metadata(self):
        history=[{'role':'assistant','sources':[{'id':'https://outside','title':'X'},{'id':'guide:a','title':'A'}]}, {'role':'user','content':'Suite'}]
        self.assertEqual(conversation_context.previous_sources(history)['historical_sources'],[{'id':'guide:a','title':'A','consulted':False}])
        history[0]['documentary']={'consulted_sources':[]}
        self.assertIsNone(conversation_context.previous_sources(history))

    def test_explicit_reference_is_distinct_from_a_new_subject(self):
        self.assertTrue(conversation_context.refers_back('Et quelles conditions pour cette procédure ?'))
        self.assertTrue(conversation_context.refers_back('Et à 446 MHz ?'))
        self.assertFalse(conversation_context.refers_back('Et comment réparer un vélo ?'))
