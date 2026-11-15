import json
import unittest
from pilot import store
import test_engine_evidence as fixture


class IllustrationEngineTests(unittest.TestCase):
    setUp=fixture.EvidenceTests.setUp
    run_chat=fixture.EvidenceTests.run_chat

    def prepare(self,images=True):
        self.a={'id':'zim:book/A/notice','title':'Notice fictive','text':'Le schéma de montage annonce 17 unités.','language':'fr',
            'images':[{'id':'zim:book/I/schema.svg','alt':'Montage fictif 17 unités','caption':'Schéma original fictif.'}] if images else []}
        with store.connect() as db:db.execute("UPDATE messages SET content='Compare le montage et montre le schéma original.' WHERE role='user'")

    def test_original_selection_is_saved_with_read_source_after_real_model_protocol(self):
        self.prepare()
        payloads,answer=self.run_chat([{'content':'{"selected":["v0"]}'},{'content':'Le montage donne 17 unités [1].'}],selected=[self.a['id']])
        source=answer['sources'][0]
        self.assertEqual(source['figures'][0]['id'],'zim:book/I/schema.svg');self.assertEqual(source['figure_status'],'selected')
        self.assertEqual(payloads[0]['format']['properties']['selected']['items']['enum'],['v0'])
        self.assertNotIn('figure_candidates',source)
        self.assertIn('Tu ne vois pas leurs pixels',payloads[0]['messages'][0]['content'])

    def test_unknown_selection_cannot_replace_source_and_does_not_lose_the_answer(self):
        self.prepare()
        _,answer=self.run_chat([{'content':'{"selected":["invented"]}'},{'content':'Le montage donne 17 unités [1].'}],selected=[self.a['id']])
        self.assertEqual(answer['content'],'Le montage donne 17 unités [1].')
        self.assertEqual(answer['sources'][0]['figure_status'],'unavailable');self.assertEqual(answer['sources'][0]['figures'],[])

    def test_no_visual_candidate_needs_no_extra_model_call(self):
        self.prepare(False)
        calls,answer=self.run_chat([{'content':'Le montage donne 17 unités [1].'}],selected=[self.a['id']])
        self.assertEqual(len(calls),1);self.assertEqual(answer['sources'][0]['figure_status'],'none')

    def test_optional_visual_tool_keeps_one_response_per_model_call(self):
        self.prepare()
        with store.connect() as db:db.execute("UPDATE messages SET content='Compare le montage fictif.' WHERE role='user'")
        payloads,answer=self.run_chat([fixture.EvidenceTests.call('source_illustrations',{}),{'content':'{"selected":["v0"]}'},{'content':'Le montage indique 17 unités [1].'}],selected=[self.a['id']])
        packet=payloads[-1]['messages'];calls=[m for m in packet if m.get('tool_calls') and m['tool_calls'][0]['function']['name']=='source_illustrations']
        self.assertEqual(len(calls),1)
        self.assertEqual(len([m for m in packet if m['role']=='tool' and m.get('tool_name')=='source_illustrations']),1)
        self.assertEqual(answer['sources'][0]['figures'][0]['id'],'zim:book/I/schema.svg')

    def test_visual_metadata_is_not_transmitted_in_the_free_text_read_packet(self):
        self.prepare();self.a['images']=[{'id':'zim:book/I/'+str(i)+'.svg','caption':'Large original caption. '*50} for i in range(100)]
        with store.connect() as db:db.execute("UPDATE messages SET content='Que dit la notice fictive ?' WHERE role='user'")
        payloads,answer=self.run_chat([fixture.EvidenceTests.call('read_source',{'id':self.a['id']}),{'content':'Valeur 17 unités [1].'}])
        result=json.loads(payloads[-1]['messages'][-1]['content']);self.assertNotIn('figure_candidates',result)
        self.assertIn('17 unités',answer['content'])
