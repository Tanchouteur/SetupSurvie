import json
import unittest
from pilot import tool_protocol


class ProtocolTests(unittest.TestCase):
    def test_prose_proposal_is_recognised_without_becoming_an_executed_call(self):
        value=json.dumps({'name':'search_library','arguments':{'query':'notice','collection':'invented'}})
        for content in [value,'Je vais chercher.\n```json\n'+value+'\n```']:
            self.assertTrue(tool_protocol.textual_call(content,'Comment régler le poste ?',{'search_library'}))

    def test_legitimate_examples_and_ordinary_json_stay_ordinary_text(self):
        proposal='{"name":"calculate","arguments":{"expression":"1+2"}}'
        self.assertFalse(tool_protocol.textual_call(proposal,'Explique ce JSON',{'calculate'}))
        for content in ['{"voltage":12}','La notice donne 12 V.','{"name":"other","arguments":{}}']:
            self.assertFalse(tool_protocol.textual_call(content,'Donne la tension',{'calculate'}))

    def test_nested_native_shape_and_malformed_values(self):
        self.assertTrue(tool_protocol.textual_call('{"tool_calls":[{"function":{"name":"calculate","arguments":{"expression":"2+2"}}}]}','Calcule',{'calculate'}))
        for value in [None,[],{'function':[]},{'function':None}]:self.assertEqual(tool_protocol.function(value),{})

    def test_history_presentation_does_not_forward_malformed_shapes(self):
        self.assertEqual(tool_protocol.presentation({'function':{'name':'calculate','arguments':'{"expression":"2+2"}'}})['function']['arguments'],{'expression':'2+2'})
        for call in [None,[],{'function':{'name':None,'arguments':'invalid'}},{'function':{'name':'bad-name','arguments':[]}}]:
            result=tool_protocol.presentation(call)
            self.assertEqual(result['function'],{'name':'unavailable_tool','arguments':{}})
