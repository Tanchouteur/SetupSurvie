"""Real tool orchestration with simulated HTTP responses, never real inference."""
import asyncio
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import engine,library,store,assistant_metrics,documentary,operations

POLICY=Path(__file__).resolve().parents[1]/'deploy/assistant-system.fr.txt'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.state=patch.object(store,'ROOT',Path(self.temp.name));self.state.start();self.addCleanup(self.state.stop)
        store.init()
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','u','Fixture',0))
            db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',('c','user','Que dit la notice fictive ?',0))
            db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('j','u','c','rapide','queued',0,0))
        self.a={'id':'guide:a','title':'Notice A','language':'fr','text':'Charge annoncée : 10 kg.','document_date':'2010','edition':'A'}
        self.b={'id':'guide:b','title':'Notice B','language':'fr','text':'Charge annoncée : 20 kg.','document_date':'2024','edition':'B'}

    def run_chat(self,messages,found=None,read=None,attached=None,expected_status='done',failure=False,native_context=131072,cancel_model=False,other_model=False,paused=False,selected=None,search=None,pause_during_review=False):
        payloads=[];client_class=httpx.AsyncClient
        self.loads=[]
        def handler(request):
            if request.url.path=='/api/version':return httpx.Response(200,json={'version':'0.12.0'})
            if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':engine.MODES['rapide']['model'],'digest':'a'*64}]})
            if request.url.path=='/api/show':return httpx.Response(200,json={'model_info':{'fixture.context_length':native_context}})
            if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[{'name':'other:local','context_length':8192}] if other_model else []})
            if cancel_model:raise asyncio.CancelledError()
            if failure:return httpx.Response(500,json={'error':'Fixture error with private path /not-for-export'})
            payload=json.loads(request.content)
            if not payload.get('messages'):
                self.loads.append(payload)
                return httpx.Response(200,json={'done':True,'done_reason':'load'})
            payloads.append(payload)
            self.assertLessEqual(len(payloads),len(messages))
            message=messages[len(payloads)-1]
            event={'message':message(payload) if callable(message) else message,'done':True,'done_reason':'stop'}
            return httpx.Response(200,content=json.dumps(event).encode()+b'\n')
        with patch.object(engine,'POLICY',POLICY),patch.object(operations,'status',AsyncMock(side_effect=lambda **kw:{'online':True,'paused':paused or pause_during_review and engine.MEASUREMENTS['j'].stage=='procedure_review'})),patch.object(engine.httpx,'AsyncClient',side_effect=lambda **kw:client_class(transport=httpx.MockTransport(handler),**kw)),\
             patch.object(engine.library,'search',AsyncMock(side_effect=search,return_value=found if found is not None else [])),patch.object(engine.library,'source',AsyncMock(side_effect=read or (lambda identifier:self.a))):
            asyncio.run(engine.run('j','u','c','rapide',attached,source_ids=selected))
            self.lookup_calls=engine.library.search.await_args_list
        with store.connect() as db:
            row=dict(db.execute('SELECT * FROM jobs WHERE id="j"').fetchone())
        self.assertEqual(row['status'],expected_status,row.get('error'))
        return payloads,store.messages('c')[-1]

    @staticmethod
    def call(name,arguments):
        return {'tool_calls':[{'function':{'name':name,'arguments':arguments}}]}

    def test_small_context_explains_the_setting_without_exceeding_it(self):
        payloads,saved=self.run_chat([],native_context=8192,expected_status='incomplete')
        self.assertEqual(payloads,[])
        self.assertIn('8192',saved['content']);self.assertIn('Paramètres → Assistant',saved['content'])
        measured=assistant_metrics.read('j')
        self.assertEqual(measured['failure'],'context_budget')
        self.assertEqual(measured['context'],8192);self.assertEqual(measured['model_calls'],[])

    def test_empty_document_preparation_keeps_general_help_and_no_fictitious_sources(self):
        question='Comment organiser l’apprentissage culturel des enfants ?'
        with store.connect() as db:db.execute("UPDATE messages SET content=? WHERE conversation_id='c' AND role='user'",(question,))
        def reply(payload):
            instructions='\n'.join(m['content'] for m in payload['messages'] if m['role']=='system')
            self.assertIn('ne fournit aucun passage lisible',instructions)
            self.assertNotIn('Des passages documentaires ont été préparés',instructions)
            self.assertIn('connaissances générales',instructions)
            self.assertIn('l’âge et le niveau des enfants',instructions)
            self.assertIn('dosages, potabilité, électricité, structure',instructions)
            packets=[json.loads(m['content']) for m in payload['messages'] if m.get('tool_name')=='read_sources']
            self.assertEqual(packets[0]['results'],[])
            return {'content':'À partir de connaissances générales, voici un exemple adaptable : alterner lecture et activité. Quels âges ont les enfants ?'}
        _,answer=self.run_chat([reply],found=[])
        self.assertEqual(answer['sources'],[])
        self.assertIn('connaissances générales',answer['content'])
        self.assertEqual(assistant_metrics.read('j')['sources_read'],0)

    def test_unreadable_search_hit_is_not_presented_as_documentary_evidence(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment utiliser la notice fictive ?' WHERE conversation_id='c' AND role='user'")
        def reply(payload):
            instructions='\n'.join(m['content'] for m in payload['messages'] if m['role']=='system')
            self.assertIn('ne fournit aucun passage lisible',instructions)
            self.assertIn('commande exacte d’appareil',instructions)
            self.assertNotIn('Des passages documentaires ont été préparés',instructions)
            return {'content':'Je ne peux pas vérifier les commandes de cette notice illisible. Donnez sa référence ; je peux expliquer les principes généraux séparément.'}
        def failed(identifier):raise HTTPException(503,'Fixture unavailable')
        _,answer=self.run_chat([reply],found=[self.a],read=failed)
        self.assertEqual(answer['sources'],[])
        self.assertEqual(assistant_metrics.read('j')['sources_read'],0)

    def test_textual_tool_proposals_get_one_native_retry_then_explicit_failure(self):
        proposal={'content':'{"name":"search_library","arguments":{"query":"notice"}}'}
        payloads,answer=self.run_chat([proposal,proposal],expected_status='incomplete')
        self.assertEqual(len(payloads),2);self.assertEqual(self.lookup_calls,[])
        self.assertIn('sans réussir à appeler',answer['content'])
        self.assertEqual(assistant_metrics.read('j')['failure'],'tool_protocol')

    def test_native_retry_can_read_and_answer_after_textual_proposal(self):
        proposal={'content':'Je vais chercher.\n```json\n{"name":"read_source","arguments":{"id":"guide:a"}}\n```'}
        payloads,answer=self.run_chat([proposal,self.call('read_source',{'id':'guide:a'}),{'content':'La notice annonce 10 kg [1].'}])
        self.assertEqual(len(payloads),3);self.assertEqual(len(answer['sources']),1)
        self.assertEqual(assistant_metrics.read('j')['tool_protocol_retries'],1)

    def test_empty_reply_after_protocol_retry_keeps_the_specific_failure(self):
        self.run_chat([{'content':'{"name":"calculate","arguments":{"expression":"2+2"}}'},{'content':''},{'content':''}],expected_status='incomplete')
        self.assertEqual(assistant_metrics.read('j')['failure'],'tool_protocol')

    def test_malformed_native_arguments_return_a_tool_error_and_keep_conversation(self):
        payloads,answer=self.run_chat([self.call('calculate','not JSON'),{'content':'Le calcul n’a pas abouti.'}])
        self.assertIn('error',json.loads(payloads[1]['messages'][-1]['content']))
        call=next(row for row in payloads[1]['messages'] if row.get('tool_calls'))['tool_calls'][0]
        self.assertEqual(call['function']['arguments'],{})
        self.assertIn('pas abouti',answer['content'])

    def test_historical_source_pointer_is_reloaded_with_new_numbers(self):
        with store.connect() as db:
            db.execute("DELETE FROM messages WHERE conversation_id='c'")
            db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',('c','user','Notice A','[]',0))
            db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',('c','assistant','Ancienne valeur [42].',json.dumps([{'id':'guide:a','title':'Ancien titre','number':42}]),1))
            db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',('c','user','Et les conditions ?',2))
        payloads,answer=self.run_chat([self.call('read_source',{'id':'guide:a'}),{'content':'La source relue annonce 10 kg [1].'}])
        hints=next(row['content'] for row in payloads[0]['messages'] if 'historical_sources' in row['content'])
        self.assertIn('consulted": false',hints);self.assertNotIn('number',hints)
        self.assertEqual(answer['sources'][0]['number'],1);self.assertEqual(answer['sources'][0]['title'],'Notice A')

    def test_followup_without_native_calls_rereads_and_rejects_inherited_citations(self):
        with store.connect() as db:
            db.execute("DELETE FROM messages WHERE conversation_id='c'")
            db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',('c','assistant','Ancienne réponse [42].',json.dumps([{'id':'guide:a','title':'Ancien titre','number':42}]),0))
            db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',('c','user','Et les précautions pour cette procédure ?',1))
        payloads,answer=self.run_chat([{'content':'La notice relue annonce 10 kg [1].'}])
        self.assertEqual(assistant_metrics.read('j')['continued_sources'],1)
        packet=json.loads(next(row['content'] for row in payloads[0]['messages'] if row.get('tool_name')=='read_sources'))
        self.assertEqual(packet['results'][0]['number'],1);self.assertEqual(len(answer['sources']),1)

    def test_unread_numeric_citation_without_search_is_never_treated_as_done(self):
        _,answer=self.run_chat([{'content':'Ancienne affirmation [42].'}],expected_status='incomplete')
        self.assertEqual(answer['sources'],[])
        self.assertNotIn('[42]',answer['content'])

    def test_procedural_review_adds_exact_starting_condition_and_survives_failed_review(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment utiliser le cadran fictif ?' WHERE conversation_id='c'")
        source={**self.a,'text':'Avant de commencer, sélectionner la ligne supérieure du cadran fictif. Choisir un canal libre.'}
        _,answer=self.run_chat([{'content':'Choisir un canal libre [1].'},{'content':'{"missing_conditions":["condition-0"]}'}],[source],read=lambda _:source)
        self.assertIn('> Avant de commencer, sélectionner la ligne supérieure',answer['content'])
        self.assertEqual(assistant_metrics.read('j')['procedure_review']['selected'],1)
        _,answer=self.run_chat([{'content':'Choisir un canal libre [1].'},{'content':'JSON indisponible'}],[source],read=lambda _:source)
        self.assertEqual(answer['content'],'Choisir un canal libre [1].')
        self.assertEqual(assistant_metrics.read('j')['procedure_review']['status'],'unavailable')

    def test_pause_after_writing_prevents_the_optional_review_call(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment utiliser le cadran fictif ?' WHERE conversation_id='c'")
        source={**self.a,'text':'Avant de commencer, sélectionner la ligne supérieure du cadran fictif.'}
        payloads,answer=self.run_chat([{'content':'Réponse fictive conservée [1].'}],[source],read=lambda _:source,pause_during_review=True)
        self.assertEqual(len(payloads),1);self.assertEqual(answer['content'],'Réponse fictive conservée [1].')
        self.assertEqual(assistant_metrics.read('j')['procedure_review']['status'],'unavailable')

    def test_read_metadata_replaces_search_metadata_and_only_read_citations_are_saved(self):
        messages=[self.call('search_library',{'query':'notice'}),self.call('read_source',{'id':'guide:a'}),
                  {'content':'Le document indique 10 kg (2010, édition A) [1]. Citation non lue [2], inventée [99].'}]
        payloads,answer=self.run_chat([*messages,{'content':'{"citations":[]}'}],[{**self.a,'document_date':'2026'},self.b],expected_status='incomplete')
        search_result=json.loads(next(m['content'] for m in payloads[1]['messages'] if m['role']=='tool' and m.get('tool_name')=='search_library'))
        self.assertFalse(search_result['results'][0]['consulted'])
        read_result=json.loads(payloads[2]['messages'][-1]['content'])
        self.assertTrue(read_result['consulted']);self.assertEqual(read_result['document_date'],'2010')
        self.assertEqual(answer['sources'][0]['number'],1)
        self.assertEqual(answer['sources'][0]['document_date'],'2010')
        self.assertEqual(len(answer['sources']),1)
        self.assertIn('Je ne sais pas',payloads[0]['messages'][0]['content'])

    def test_measurements_have_no_question_answer_source_text_or_private_reasoning(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Question privée spéciale' WHERE conversation_id='c'")
        self.run_chat([{'content':'Réponse privée spéciale','thinking':'Raisonnement privé spécial'}])
        measured=assistant_metrics.read('j');raw=json.dumps(measured,ensure_ascii=False)
        for word in ('Question privée','Réponse privée','Raisonnement privé','/not-for-export'):self.assertNotIn(word,raw)
        self.assertEqual(measured['status'],'done');self.assertIsNotNone(measured['first_text_ms'])
        self.assertGreater(measured['budgets'][0]['tool_estimate'],0)
        allocation=measured['budgets'][0]
        self.assertLessEqual(allocation['input_estimate']+allocation['output']+allocation['template_reserve'],allocation['context'])

    def test_failed_model_call_still_persists_sanitized_metrics(self):
        self.run_chat([],failure=True,expected_status='failed')
        measured=assistant_metrics.read('j')
        self.assertEqual(measured['status'],'failed');self.assertEqual(measured['engine_http_status'],500)
        self.assertEqual(measured['failure'],'engine_http_error');self.assertNotIn('/not-for-export',json.dumps(measured))

    def test_switch_does_not_consume_question_or_duplicate_saved_answer(self):
        payloads,answer=self.run_chat([{'content':'Notice consultée [1].'}],attached=self.a['id'],other_model=True)
        self.assertEqual(len(self.loads),1);self.assertEqual(len(payloads),1)
        self.assertEqual(self.loads[0]['model'],payloads[0]['model'])
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])
        self.assertEqual(len(store.messages('c')),2)
        measured=assistant_metrics.read('j');self.assertEqual(measured['model_preparations'][0]['status'],'ready')

    def test_empty_first_response_is_recovered_within_same_job(self):
        payloads,answer=self.run_chat([{'content':''},{'content':'Réponse finale fictive.'}])
        self.assertEqual(payloads[0],payloads[1]);self.assertEqual(len(store.messages('c')),2)
        self.assertEqual(answer['content'],'Réponse finale fictive.')
        self.assertEqual(len(assistant_metrics.read('j')['model_retries']),1)

    def test_pause_after_queue_prevents_model_load_and_generation(self):
        payloads,_=self.run_chat([],other_model=True,paused=True,expected_status='failed')
        self.assertEqual(payloads,[]);self.assertEqual(self.loads,[])
        self.assertEqual(assistant_metrics.read('j')['failure'],'engine_paused')

    def test_model_failure_keeps_read_excerpts_in_reopened_history(self):
        _,answer=self.run_chat([],attached=self.a['id'],failure=True,expected_status='failed')
        self.assertEqual(answer['role'],'assistant');self.assertIn(self.a['text'],answer['content'])
        self.assertIn('ne constituent pas une synthèse validée',answer['content'])
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])
        self.assertEqual(answer['documentary']['sources_read'],1)
        self.assertEqual(assistant_metrics.read('j')['status'],'failed')

    def test_context_uses_native_limit_and_records_the_reduction(self):
        with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',('context:'+engine.MODES['rapide']['model'],'65536'))
        payloads,_=self.run_chat([{'content':'Réponse fictive.'}],native_context=16384)
        self.assertEqual(payloads[0]['options']['num_ctx'],16384)
        measured=assistant_metrics.read('j');self.assertTrue(measured['context_limited']);self.assertEqual(measured['requested_context'],65536)

    def test_attached_source_prepared_by_request_is_not_fetched_again(self):
        engine.PENDING['j']={'started':time.monotonic()-.05,'preparation_ms':10,'reading_ms':40,'source':self.a}
        def forbidden(identifier):raise AssertionError('The already read source must be reused.')
        _,answer=self.run_chat([{'content':'Notice consultée [1].'}],attached=self.a['id'],read=forbidden)
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])
        measured=assistant_metrics.read('j');self.assertGreaterEqual(measured['phases_ms']['reading'],40);self.assertEqual(measured['cache_hits']['read'],1)
        self.assertNotIn('j',engine.PENDING)

    def test_failed_archive_search_coverage_reaches_model_even_without_results(self):
        found=library.SearchResults([],{'status':'unavailable','warning':'Recherche incomplète'})
        payloads,answer=self.run_chat([self.call('search_library',{'query':'feu'}),{'content':'La recherche est incomplète.'}],found)
        result=json.loads(payloads[1]['messages'][-1]['content'])
        self.assertEqual(result['results'],[])
        self.assertEqual(result['coverage']['status'],'unavailable')
        self.assertEqual(answer['sources'],[])
        self.assertEqual(answer['documentary']['status'],'unavailable')
        self.assertEqual(answer['documentary']['sources_read'],0)

    def test_model_absence_claim_does_not_replace_observed_search_and_reads(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        found=library.SearchResults([self.a],{'status':'partial','domain':'resilience'})
        _,answer=self.run_chat([{'content':'Aucun document n’existe dans la bibliothèque, affirmation fictive erronée.'},{'content':'{"citations":[]}'}],found,expected_status='incomplete')
        self.assertIn('affirmation fictive',answer['content'])
        self.assertEqual(answer['documentary']['status'],'partial');self.assertEqual(answer['documentary']['sources_read'],1)
        self.assertEqual(answer['documentary']['results'],1);self.assertEqual(answer['documentary']['scope'],'targeted')
        self.assertEqual(assistant_metrics.read('j')['documentary'],{key:value for key,value in answer['documentary'].items() if key!='consulted_sources'})
        self.assertEqual(answer['documentary']['consulted_sources'],[{'id':self.a['id'],'title':self.a['title']}])
        self.assertNotIn(self.a['id'],json.dumps(assistant_metrics.read('j')['documentary']))

    def test_failed_read_is_saved_as_unread_without_becoming_a_citation(self):
        def unavailable(identifier):raise HTTPException(404,'PRIVATE READ FAILURE')
        _,answer=self.run_chat([self.call('read_source',{'id':'guide:missing'}),{'content':'Texte fictif sans source lue.'}],read=unavailable)
        self.assertEqual(answer['documentary']['sources_read'],0);self.assertEqual(answer['documentary']['failed_reads'],1)
        self.assertEqual(answer['documentary']['status'],'partial');self.assertEqual(answer['sources'],[])

    def test_automatic_read_failure_is_observed_even_if_model_claims_a_procedure(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        def unreadable(identifier):raise HTTPException(404,'PRIVATE FAILED EXTRACTION')
        found=library.SearchResults([self.a],{'status':'complete'})
        _,answer=self.run_chat([{'content':'Procédure fictive sans document lu.'}],found,read=unreadable)
        self.assertEqual(answer['documentary']['status'],'partial');self.assertEqual(answer['documentary']['failed_reads'],1)
        self.assertEqual(answer['documentary']['sources_read'],0);self.assertEqual(answer['documentary']['consulted_sources'],[])
        self.assertEqual(answer['sources'],[])

    def test_cancellation_preserves_observed_work_without_fabricating_an_answer(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        with self.assertRaises(asyncio.CancelledError):self.run_chat([],library.SearchResults([self.a],{'status':'partial'}),cancel_model=True)
        summary=documentary.for_job('j');self.assertEqual(summary['status'],'partial');self.assertEqual(summary['sources_read'],1)
        self.assertEqual(summary['consulted_sources'],[{'id':self.a['id'],'title':self.a['title']}])
        self.assertEqual(len(store.messages('c')),1);self.assertNotIn('j',engine.DOCUMENTARY)
        with store.connect() as db:self.assertEqual(db.execute('SELECT status FROM jobs WHERE id=?',('j',)).fetchone()[0],'cancelled')

    def test_optional_evidence_failure_preserves_the_answer_and_numerical_fallback(self):
        with store.connect() as db:
            db.execute('DROP TABLE documentary_evidence');db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        _,answer=self.run_chat([{'content':'Texte fictif consulté [1].'}],library.SearchResults([self.a],{'status':'complete'}))
        self.assertNotIn('documentary',answer);self.assertEqual(answer['sources'][0]['id'],self.a['id'])
        self.assertEqual(assistant_metrics.read('j')['documentary']['sources_read'],1)

    def test_empty_extraction_is_not_a_consulted_or_cited_source(self):
        self.a={**self.a,'text':'   '}
        _,answer=self.run_chat([self.call('read_source',{'id':self.a['id']}),{'content':'Citation fictive non étayée [1].'}],expected_status='incomplete')
        self.assertEqual(answer['sources'],[]);self.assertEqual(answer['documentary']['sources_read'],0)
        self.assertEqual(answer['documentary']['failed_reads'],1)

    def test_empty_attached_document_is_distinct_from_a_missing_document(self):
        self.a={**self.a,'text':''}
        payloads,answer=self.run_chat([{'content':'Citation fictive non étayée [1].'}],attached=self.a['id'],expected_status='incomplete')
        self.assertTrue(any('ne fournit pas de texte lisible' in message['content'] for message in payloads[0]['messages']))
        self.assertEqual(answer['sources'],[]);self.assertEqual(answer['documentary']['sources_read'],0)
        self.assertEqual(answer['documentary']['failed_reads'],1)

    def test_practical_question_receives_read_documents_before_first_model_call(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        payloads,answer=self.run_chat([{'content':'La source consultée décrit le sujet [1].'}],[self.a])
        tools=[json.loads(m['content']) for m in payloads[0]['messages'] if m['role']=='tool']
        self.assertTrue(any(part['text']==self.a['text'] for t in tools for row in t.get('results',[]) for part in row.get('passages',[])))
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])

    def test_summary_and_friction_requests_prepare_reading_before_first_model_call(self):
        for question in ('Fait un synthese sur les info des document sur comment faire du feux',
                         'Des méthodes d’allumage au frottement (comme le feu de bois) ?'):
            with self.subTest(question=question):
                with store.connect() as db:db.execute("UPDATE messages SET content=? WHERE conversation_id='c' AND role='user'",(question,))
                payloads,answer=self.run_chat([{'content':'Source fictive consultée [1].'}],[self.a])
                tools=[json.loads(message['content']) for message in payloads[0]['messages'] if message['role']=='tool']
                self.assertTrue(any(part['text']==self.a['text'] for value in tools for row in value.get('results',[]) for part in row.get('passages',[])))
                self.assertEqual(answer['documentary']['sources_read'],1)

    def test_summary_reads_five_documents_with_late_passages_before_generation(self):
        question='Fais une synthèse des documents sur la température du compost'
        with store.connect() as db:
            db.execute("UPDATE messages SET content=? WHERE role='user'",(question,))
            db.execute('INSERT INTO settings VALUES(?,?)',('context:'+engine.MODES['rapide']['model'],'32768'))
        sources={f'guide:{i}':{'id':f'guide:{i}','title':f'Document fictif {i}','text':('Introduction sans rapport. '*300)+f'\nCompost et température : valeur fictive {i}.\n'} for i in range(5)}
        payloads,answer=self.run_chat([{'content':'Les documents présentent des observations différentes [1] [2] [3] [4] [5].'}],list(sources.values()),read=sources.__getitem__)
        packets=[json.loads(message['content']) for message in payloads[0]['messages'] if message['role']=='tool']
        rows=[row for packet in packets for row in packet.get('results',[]) if row.get('passages')]
        self.assertEqual(len(rows),5)
        for row in rows:self.assertTrue(any('valeur fictive' in part['text'] and (part['offset']>3000 or not row['partial_read']) for part in row['passages']))
        self.assertEqual(len(answer['sources']),5);self.assertEqual(answer['documentary']['sources_read'],5)

    def test_summary_without_valid_citations_gets_one_final_revision(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Fais une synthèse des documents sur le compost' WHERE role='user'")
        payloads,answer=self.run_chat([{'content':'La charge fictive indiquée vaut 10 kg.'},{'content':json.dumps({'citations':[{'fragment_id':'f0','source_number':1}]})}],[self.a])
        self.assertEqual(len(payloads),2);self.assertEqual(payloads[-1]['tools'],[])
        self.assertIn('format',payloads[-1]);self.assertIn('10 kg. [1]',answer['content'])
        self.assertEqual(payloads[-1]['think'],'low')
        self.assertEqual(assistant_metrics.read('j')['citation_revisions'],1)
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])

    def test_chosen_five_sources_are_read_without_search_and_source_text_stays_in_tool_data(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Fais une synthèse des documents sur la température du compost' WHERE role='user'")
        sources={f'guide:{i}':{'id':f'guide:{i}','title':'Notice fictive '+str(i),'text':('Préface fictive sans consigne. '*200)+f'\nCompost et température : valeur fictive {i}. DOCUMENT-INSTRUCTION-FICTIVE-IGNORER.\n'} for i in range(5)}
        payloads,answer=self.run_chat([{'content':'Cinq observations fictives [1] [2] [3] [4] [5].'}],read=sources.__getitem__,selected=list(sources))
        self.assertEqual(self.lookup_calls,[]);self.assertEqual(answer['documentary']['sources_read'],5)
        system='\n'.join(message['content'] for message in payloads[0]['messages'] if message['role']=='system')
        self.assertNotIn('DOCUMENT-INSTRUCTION-FICTIVE-IGNORER',system)
        packet=json.loads(next(message['content'] for message in payloads[0]['messages'] if message['role']=='tool'))
        self.assertEqual(len(packet['results']),5)
        for row in packet['results']:self.assertTrue(any('valeur fictive' in part['text'] for part in row['passages']))
        measured=assistant_metrics.read('j');self.assertEqual(measured['selected_sources'],5);self.assertEqual(measured['prepared_sources'],5)

    def test_an_unavailable_chosen_document_does_not_block_other_reads(self):
        sources={self.a['id']:self.a,self.b['id']:self.b}
        def read(identifier):
            if identifier not in sources:raise HTTPException(404,'Fictional unavailable source')
            return sources[identifier]
        _,answer=self.run_chat([{'content':'Charges différentes [1] [2].'}],read=read,selected=['guide:missing',*sources])
        self.assertEqual(answer['documentary']['sources_read'],2);self.assertEqual(answer['documentary']['failed_reads'],1)
        self.assertEqual({source['id'] for source in answer['sources']},set(sources))
        self.assertEqual(assistant_metrics.read('j')['selected_sources'],3)

    def test_link_format_does_not_spend_the_answer_thinking_budget(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Fais une synthèse des documents sur le compost' WHERE role='user'")
        with patch.dict(engine.MODES,{'rapide':{**engine.MODES['rapide'],'model':'gemma4:e4b','think':True}}):
            payloads,_=self.run_chat([{'content':'La charge fictive vaut 10 kg.'},{'content':json.dumps({'citations':[{'fragment_id':'f0','source_number':1}]})}],[self.a])
        self.assertIs(payloads[0]['think'],True);self.assertIs(payloads[1]['think'],False)
        self.assertEqual(payloads[0]['model'],payloads[1]['model'])

    def test_failed_reference_revision_returns_actual_excerpts_without_certifying_summary(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Fais une synthèse des documents sur le compost' WHERE role='user'")
        _,answer=self.run_chat([{'content':'Source inventée [99].'},{'content':'Encore inventée [99].'}],[self.a],expected_status='incomplete')
        self.assertIn('ne constituent pas une synthèse validée',answer['content'])
        self.assertIn(self.a['text'],answer['content']);self.assertNotIn('[99]',answer['content'])
        self.assertEqual(assistant_metrics.read('j')['failure'],'citation_check')

    def test_missing_link_format_keeps_useful_original_prose_with_a_clear_limit(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Fais une synthèse des documents sur le compost' WHERE role='user'")
        _,answer=self.run_chat([{'content':'Le document donne une charge fictive de 10 kg.'},{'content':'JSON de liaison indisponible.'}],[self.a],expected_status='incomplete')
        self.assertIn('charge fictive de 10 kg',answer['content']);self.assertIn('Références à vérifier',answer['content'])
        self.assertEqual(answer['sources'],[]);self.assertEqual(answer['documentary']['sources_read'],1)

    def test_batch_reading_tool_preserves_independent_source_evidence(self):
        sources={self.a['id']:self.a,self.b['id']:self.b}
        payloads,answer=self.run_chat([self.call('read_sources',{'ids':list(sources),'query':'charge fictive'}),{'content':'Charges différentes [1] [2].'}],read=sources.__getitem__)
        packet=json.loads(payloads[1]['messages'][-1]['content']);self.assertEqual(len(packet['results']),2)
        self.assertEqual(answer['documentary']['sources_read'],2)

    def test_two_rounds_without_new_evidence_stop_repeated_research(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE role='user'")
        payloads,_=self.run_chat([self.call('search_library',{'query':'feu'}),self.call('search_library',{'query':'feu'}),{'content':'Source disponible [1].'}],[self.a])
        self.assertEqual(len(self.lookup_calls),1)
        self.assertEqual(payloads[-1]['tools'],[])
        self.assertEqual(assistant_metrics.read('j')['research_stop'],'no_new_evidence')

    def test_model_can_reuse_prepared_subject_with_a_shorter_formulation(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        self.run_chat([self.call('search_library',{'query':'feu'}),{'content':'Source déjà lue [1].'}],[self.a])
        self.assertEqual(len(self.lookup_calls),1)
        self.assertEqual(store.messages('c')[-1]['documentary']['searches'],1)

    def test_an_explicit_change_of_action_is_not_the_prepared_search(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment réparer un vélo ?' WHERE conversation_id='c'")
        self.run_chat([self.call('search_library',{'query':'construire un vélo'}),{'content':'Autre action demandée [1].'}],[self.a])
        self.assertEqual(len(self.lookup_calls),2)

    def test_equipment_procedures_prepare_without_an_enumerated_device_or_verb(self):
        for question in ('Comment mémoriser une fréquence dans mon poste ?', 'Comment détartrer cette cafetière ?', 'Sur un modèle inconnu, comment calibrer le capteur ?', 'Quelle longueur de brin faut-il pour ce montage ?', 'À 433 MHz, quelle est la longueur totale du dipôle ?'):
            self.assertEqual(engine.document_request([{'role':'user','content':question}]),(question,''))
        self.assertIsNone(engine.document_request([{'role':'user','content':'Comment calculer 12 fois 8 ?'}]))

    def test_notice_command_searches_device_but_reads_with_the_full_question(self):
        question='Selon la notice du contrôleur TQ-917, quelle touche affiche son identifiant ? Donne la commande exacte.'
        source={**self.a,'title':'Notice TQ-917','text':'Fixture fictive TQ-917. La touche REPERE affiche l’identifiant.'}
        with store.connect() as db:db.execute("UPDATE messages SET content=? WHERE conversation_id='c' AND role='user'",(question,))
        def answer(payload):
            self.assertTrue(any(m.get('content')==question for m in payload['messages']))
            packet=json.loads(next(m['content'] for m in payload['messages'] if m.get('tool_name')=='read_sources'))
            self.assertIn('REPERE',packet['results'][0]['passages'][0]['text'])
            return {'content':'La notice fictive indique REPERE [1].'}
        _,saved=self.run_chat([answer],found=[source],read=lambda _:source)
        self.assertEqual(self.lookup_calls[0].args[0],'TQ-917')
        self.assertEqual(len(saved['sources']),1)
        trace=json.loads((Path(self.temp.name)/'traces/j.json').read_text())
        read=next(row for row in trace['tools'] if row.get('tool')=='read_sources')
        self.assertIn('affiche son identifiant',read['arguments']['query'])

    def test_wikipedia_followup_uses_previous_user_subject(self):
        history=[{'role':'user','content':'Comment faire du feu ?'}, {'role':'assistant','content':'Aucun document, affirmation non établie.'}, {'role':'user','content':'Et dans Wikipédia tu ne trouves rien ?'}]
        query,collection=engine.document_request(history)
        self.assertEqual(query,history[0]['content']);self.assertEqual(collection,'wikipedia')
        specific=history+[{'role':'user','content':'réparer une radio dans Wikipédia'}]
        self.assertEqual(engine.document_request(specific),('réparer une radio dans Wikipédia','wikipedia'))
        followups=history+[{'role':'user','content':'Et dans Appropedia ?'},{'role':'user','content':'Et dans Wikipédia ?'}]
        self.assertEqual(engine.document_request(followups),('Comment faire du feu ?','wikipedia'))
        self.assertEqual(engine.document_request(history+[{'role':'user','content':'Trouve un document sur les radios dans Wikipédia'}]),('Trouve un document sur les radios dans Wikipédia','wikipedia'))
        self.assertIsNone(engine.document_request([{'role':'user','content':'Combien font 12 fois 3 ?'}]))
        self.assertIsNone(engine.document_request([{'role':'user','content':'Cherche un puits proche de moi'}]))

    def test_context_compaction_keeps_latest_question_and_valid_tool_pairs(self):
        messages=[{'role':'system','content':'Consignes '+('s'*3000)}, {'role':'user','content':'Ancien sujet '+('h'*3000)}, {'role':'assistant','content':'Ancienne réponse '+('a'*3000)}, {'role':'user','content':'Comment construire un abri ?'}]
        for i in range(4):
            messages.extend([{'role':'assistant','content':'','thinking':'internal '*3000,'tool_calls':[{'id':str(i),'function':{'name':'read_source','arguments':{'id':'guide:a'}}}]}, {'role':'tool','tool_call_id':str(i),'content':json.dumps({'text':'Passage '*1500,'partial_read':False,'more':False})}])
        self.assertTrue(engine.fit_context(messages,maximum=6500))
        self.assertLessEqual(len(json.dumps(messages,ensure_ascii=False).encode()),6500)
        self.assertTrue(any(m.get('content')=='Comment construire un abri ?' for m in messages))
        calls={c['id'] for m in messages for c in m.get('tool_calls',[])}
        self.assertTrue(all(m['tool_call_id'] in calls for m in messages if m['role']=='tool'))
        self.assertTrue(all('thinking' not in m for m in messages))
        self.assertTrue(all(json.loads(m['content'])['partial_read'] for m in messages if m['role']=='tool'))

    def test_context_compaction_never_keeps_half_a_formula_in_single_or_batch_reads(self):
        from pilot.math_text import marked,BLOCKS
        for batch in (False,True):
            text=('x'*240)+'\n'+marked(r'\frac{'+('a'*600)+'}{19}')+('z'*2000)
            value={'results':[{'passages':[{'offset':40,'text':text,'next_offset':40+len(text)}]}]} if batch else {'offset':40,'text':text,'next_offset':40+len(text)}
            messages=[{'role':'system','content':'Policy'}, {'role':'user','content':'Question'},*engine.tool_messages('read_sources' if batch else 'read_source',{},value,'formula')]
            self.assertTrue(engine.fit_context(messages,maximum=1500))
            result=json.loads(messages[-1]['content']);part=result['results'][0]['passages'][0] if batch else result
            self.assertEqual(part['text'],text[:len(part['text'])])
            self.assertEqual(part['next_offset'],40+len(part['text']))
            self.assertEqual(part['text'].count('```math'),len(list(BLOCKS.finditer(part['text']))))
            self.assertNotIn(r'\frac',part['text'])

    def test_explicit_read_continues_at_formula_boundary_with_original_offsets(self):
        from pilot.math_text import marked,BLOCKS
        text=('Avant. '*497)+'\n'+marked(r'\frac{19}{7}')+' Après.'*300
        source={**self.a,'text':text}
        def next_read(payload):
            part=json.loads(payload['messages'][-1]['content'])
            self.assertEqual(part['text'],text[part['offset']:part['next_offset']]);self.assertTrue(part['more'])
            self.assertNotIn('```math',part['text'])
            return self.call('read_source',{'id':'guide:a','offset':part['next_offset']})
        def answer(payload):
            part=json.loads(payload['messages'][-1]['content'])
            self.assertEqual(part['text'],text[part['offset']:part['next_offset']])
            self.assertIn(r'\frac{19}{7}',part['text']);self.assertEqual(len(list(BLOCKS.finditer(part['text']))),1)
            return {'content':'Passage fictif lu [1].'}
        self.run_chat([self.call('read_source',{'id':'guide:a','offset':0}),next_read,answer],read=lambda _:source)

    def test_long_archive_identifiers_fit_before_model_call_without_changing_context_or_question(self):
        question='Fais une synthèse des documents sur les techniques pour faire du feu.'
        with store.connect() as db:db.execute('UPDATE messages SET content=? WHERE conversation_id=\'c\'',(question,))
        sources=[{'id':'zim:encyclopedie/A/'+str(i)+'-'+'path'*35,
            'title':'Techniques pour faire du feu — '+str(i)+' titre "fr" \\ '*8,'language':'fr',
            'document_date':'2026','edition':'Édition complète '+str(i),'provenance':'Origine fictive '+('a'*100),
            'text':(f'Notice fictive {i}, technique pour faire du feu : friction et percussion, valeur inventée {i+10} unités. '*40)} for i in range(12)]
        byid={source['id']:source for source in sources}
        def answer(payload):
            packet=json.loads(next(message['content'] for message in payload['messages'] if message.get('tool_name')=='read_sources'))
            return {'content':'\n'.join('La notice de recette mentionne la friction ['+str(row['number'])+'].' for row in packet['results'])}
        with patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}):
            payloads,saved=self.run_chat([answer],sources,read=lambda key:byid[key])
        self.assertEqual(len(payloads),1);payload=payloads[0]
        self.assertEqual(payload['options']['num_ctx'],16384);self.assertEqual(payload['options']['num_predict'],4096)
        self.assertTrue(any(message.get('content')==question for message in payload['messages']))
        packet=json.loads(next(message['content'] for message in payload['messages'] if message.get('tool_name')=='read_sources'))
        self.assertGreaterEqual(len(packet['results']),3);self.assertTrue(packet['selection_limited'])
        self.assertEqual(packet['results'][0]['id'],sources[0]['id'])
        for row in packet['results']:
            self.assertEqual(row['title'],byid[row['id']]['title']);self.assertEqual(row['edition'],byid[row['id']]['edition'])
            for part in row['passages']:self.assertEqual(part['text'],byid[row['id']]['text'][part['offset']:part['next_offset']])
        measured=assistant_metrics.read('j');self.assertEqual(measured['status'],'done')
        self.assertEqual(measured['sources_read'],len(packet['results']))
        allocation=measured['budgets'][0]
        self.assertLessEqual(allocation['input_estimate']+allocation['output']+allocation['template_reserve'],allocation['context'])
        self.assertLessEqual(measured['reading_packets'][0]['encoded_bytes'],measured['reading_packets'][0]['maximum_bytes'])
        self.assertEqual(len(saved['sources']),len(packet['results']))

    def test_repeated_searches_are_cached_within_the_same_question(self):
        self.run_chat([self.call('search_library',{'query':'notice'}),self.call('search_library',{'query':'notice'}),{'content':'Fin avec la source effectivement lue [1].'}],[self.a])
        self.assertEqual(len(self.lookup_calls),1)

    def test_plain_equipment_question_reads_search_hit_before_the_model_can_stop(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Le clavier du poste est bloqué ; peux-tu rechercher la procédure ?' WHERE conversation_id='c'")
        payloads,answer=self.run_chat([self.call('search_library',{'query':'verrouillage clavier'}),{'content':'La notice donne la procédure [1].'}],[self.a])
        tools=[m for m in payloads[-1]['messages'] if m['role']=='tool']
        self.assertEqual([m['tool_name'] for m in tools],['search_library','read_sources'])
        self.assertFalse(json.loads(tools[0]['content'])['results'][0]['consulted'])
        self.assertEqual(json.loads(tools[1]['content'])['results'][0]['passages'][0]['text'],self.a['text'])
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])
        self.assertEqual(answer['documentary']['sources_read'],1)

    def test_a_complementary_search_reads_the_new_document_without_rereading_the_first(self):
        read=[]
        def source(identifier):read.append(identifier);return {self.a['id']:self.a,self.b['id']:self.b}[identifier]
        def lookup(query,*args,**kwargs):return [self.a] if query=='first' else [self.b]
        _,answer=self.run_chat([self.call('search_library',{'query':'first'}),self.call('search_library',{'query':'second'}),{'content':'Les deux notices diffèrent [1] [2].'}],read=source,search=lookup)
        self.assertEqual(read,[self.a['id'],self.b['id']])
        self.assertEqual({row['id'] for row in answer['sources']},{self.a['id'],self.b['id']})

    def test_failed_automatic_read_cannot_validate_a_search_excerpt_citation(self):
        def missing(identifier):raise HTTPException(404,'PRIVATE READ FAILURE')
        _,answer=self.run_chat([self.call('search_library',{'query':'notice'}),{'content':'La notice dit ceci [1].'},{'content':'{"citations":[]}'}],[self.a],read=missing,expected_status='incomplete')
        self.assertEqual(answer['sources'],[])
        self.assertEqual(answer['documentary']['sources_read'],0)
        self.assertGreater(answer['documentary']['failed_reads'],0)
        self.assertNotIn('PRIVATE READ FAILURE',answer['content'])

    def test_repeated_source_read_uses_the_same_evidence_without_network_reload(self):
        calls=[]
        def read(identifier):calls.append(identifier);return self.a
        _,answer=self.run_chat([self.call('read_source',{'id':'guide:a'}),self.call('read_source',{'id':'guide:a'}),{'content':'Notice consultée [1].'}],read=read)
        self.assertEqual(calls,['guide:a']);self.assertEqual(len(answer['sources']),1)

    def test_fast_mode_enforces_a_budget_even_if_model_calls_a_disabled_tool(self):
        messages=[self.call('search_library',{'query':word}) for word in ['premiere','deuxieme','troisieme','quatrieme']]
        payloads,_=self.run_chat(messages,[self.a],expected_status='incomplete')
        self.assertEqual(len(self.lookup_calls),3)
        self.assertEqual(payloads[-1]['tools'],[])

    def test_contradictory_documents_keep_both_dates_and_references(self):
        messages=[self.call('read_source',{'id':'guide:a'}),self.call('read_source',{'id':'guide:b'}),
                  {'content':'La notice A de 2010 indique 10 kg [1] ; B de 2024 indique 20 kg [2]. Elles se contredisent. Je ne sais pas d’après les documents disponibles quelle révision correspond à cette boîte.'}]
        _,answer=self.run_chat(messages,read=lambda key:self.a if key=='guide:a' else self.b)
        self.assertEqual([s['document_date'] for s in answer['sources']],['2010','2024'])

    def test_empty_search_or_failed_read_cannot_create_a_cited_source(self):
        messages=[self.call('search_library',{'query':'inconnue'}),self.call('read_source',{'id':'guide:missing'}),
                  {'content':'Je ne sais pas d’après les documents disponibles. Il manque la notice [1].'}]
        _,answer=self.run_chat(messages,read=lambda key:(_ for _ in ()).throw(HTTPException(404,'Absent')),expected_status='incomplete')
        self.assertEqual(answer['sources'],[])

    def test_attached_partial_document_carries_edition_and_does_not_turn_archive_date_into_document_date(self):
        source={**self.a,'document_date':'','archive_date':'2026-05','text':'Première page. '*500}
        payloads,answer=self.run_chat([{'content':'Date du document inconnue ; édition A [1]. Cet extrait ne permet pas de conclure.'}],read=lambda _:source,attached='guide:a')
        packet=json.loads(next(message['content'] for message in payloads[0]['messages'] if message['role']=='tool'))
        attached=packet['results'][0]
        self.assertEqual(attached['document_date'],'');self.assertEqual(attached['archive_date'],'2026-05')
        self.assertEqual(attached['edition'],'A');self.assertTrue(attached['partial_read'])
        self.assertEqual(answer['sources'][0]['document_date'],'')

    def test_search_alone_is_not_exposed_to_the_browser_as_read_evidence(self):
        refs={};engine.reference(refs,self.a)
        self.assertEqual(engine.read_references(refs),[])
        engine.reference(refs,self.a,True)
        self.assertEqual(len(engine.read_references(refs)),1)
        self.assertNotIn('consulted',engine.read_references(refs)[0])

    def test_extraction_limit_is_reported_even_when_current_excerpt_has_no_next_page(self):
        source={**self.a,'text_truncated':True,'text':'Extrait disponible seulement.'}
        payloads,_=self.run_chat([self.call('read_source',{'id':'guide:a'}),{'content':'Je ne sais pas : extraction incomplète [1].'}],read=lambda _:source)
        result=json.loads(payloads[1]['messages'][-1]['content'])
        self.assertFalse(result['more'])
        self.assertTrue(result['partial_read']);self.assertTrue(result['text_limit_reached'])

    def test_answer_and_job_are_committed_together_even_when_trace_disk_write_fails(self):
        def failed_trace(*args,**kwargs):
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT status FROM jobs WHERE id='j'").fetchone()[0],'done')
                self.assertEqual(db.execute("SELECT count(*) FROM messages WHERE role='assistant'").fetchone()[0],1)
            raise OSError('fixture disk failure')
        with patch.object(engine.durable,'write_bytes',side_effect=failed_trace):
            _,answer=self.run_chat([{'content':'Réponse de fixture conservée.'}])
        self.assertEqual(answer['content'],'Réponse de fixture conservée.')


if __name__=='__main__':unittest.main()
