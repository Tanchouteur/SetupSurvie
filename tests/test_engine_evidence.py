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

    def run_chat(self,messages,found=None,read=None,attached=None,expected_status='done',failure=False,native_context=131072,cancel_model=False,other_model=False,paused=False):
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
            event={'message':messages[len(payloads)-1],'done':True,'done_reason':'stop'}
            return httpx.Response(200,content=json.dumps(event).encode()+b'\n')
        with patch.object(engine,'POLICY',POLICY),patch.object(operations,'status',AsyncMock(return_value={'online':True,'paused':paused})),patch.object(engine.httpx,'AsyncClient',side_effect=lambda **kw:client_class(transport=httpx.MockTransport(handler),**kw)),\
             patch.object(engine.library,'search',AsyncMock(return_value=found if found is not None else [])),patch.object(engine.library,'source',AsyncMock(side_effect=read or (lambda identifier:self.a))):
            asyncio.run(engine.run('j','u','c','rapide',attached))
            self.lookup_calls=engine.library.search.await_args_list
        with store.connect() as db:
            row=dict(db.execute('SELECT * FROM jobs WHERE id="j"').fetchone())
        self.assertEqual(row['status'],expected_status,row.get('error'))
        return payloads,store.messages('c')[-1]

    @staticmethod
    def call(name,arguments):
        return {'tool_calls':[{'function':{'name':name,'arguments':arguments}}]}

    def test_read_metadata_replaces_search_metadata_and_only_read_citations_are_saved(self):
        messages=[self.call('search_library',{'query':'notice'}),self.call('read_source',{'id':'guide:a'}),
                  {'content':'Le document indique 10 kg (2010, édition A) [1]. Citation non lue [2], inventée [99].'}]
        payloads,answer=self.run_chat(messages,[{**self.a,'document_date':'2026'},self.b])
        search_result=json.loads(payloads[1]['messages'][-1]['content'])
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
        measured=assistant_metrics.read('j');self.assertEqual(measured['phases_ms']['reading'],40);self.assertEqual(measured['cache_hits']['read'],1)
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
        _,answer=self.run_chat([{'content':'Aucun document n’existe dans la bibliothèque, affirmation fictive erronée.'}],found)
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
        _,answer=self.run_chat([self.call('read_source',{'id':self.a['id']}),{'content':'Citation fictive non étayée [1].'}])
        self.assertEqual(answer['sources'],[]);self.assertEqual(answer['documentary']['sources_read'],0)
        self.assertEqual(answer['documentary']['failed_reads'],1)

    def test_empty_attached_document_is_distinct_from_a_missing_document(self):
        self.a={**self.a,'text':''}
        payloads,answer=self.run_chat([{'content':'Citation fictive non étayée [1].'}],attached=self.a['id'])
        self.assertTrue(any('ne fournit pas de texte lisible' in message['content'] for message in payloads[0]['messages']))
        self.assertEqual(answer['sources'],[]);self.assertEqual(answer['documentary']['sources_read'],0)
        self.assertEqual(answer['documentary']['failed_reads'],1)

    def test_practical_question_receives_read_documents_before_first_model_call(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        payloads,answer=self.run_chat([{'content':'La source consultée décrit le sujet [1].'}],[self.a])
        tools=[json.loads(m['content']) for m in payloads[0]['messages'] if m['role']=='tool']
        self.assertTrue(any(t.get('text')==self.a['text'] for t in tools))
        self.assertEqual(answer['sources'][0]['id'],self.a['id'])

    def test_summary_and_friction_requests_prepare_reading_before_first_model_call(self):
        for question in ('Fait un synthese sur les info des document sur comment faire du feux',
                         'Des méthodes d’allumage au frottement (comme le feu de bois) ?'):
            with self.subTest(question=question):
                with store.connect() as db:db.execute("UPDATE messages SET content=? WHERE conversation_id='c' AND role='user'",(question,))
                payloads,answer=self.run_chat([{'content':'Source fictive consultée [1].'}],[self.a])
                tools=[json.loads(message['content']) for message in payloads[0]['messages'] if message['role']=='tool']
                self.assertTrue(any(value.get('text')==self.a['text'] for value in tools))
                self.assertEqual(answer['documentary']['sources_read'],1)

    def test_model_can_reuse_prepared_subject_with_a_shorter_formulation(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment faire du feu ?' WHERE conversation_id='c'")
        self.run_chat([self.call('search_library',{'query':'feu'}),{'content':'Source déjà lue [1].'}],[self.a])
        self.assertEqual(len(self.lookup_calls),1)
        self.assertEqual(store.messages('c')[-1]['documentary']['searches'],1)

    def test_an_explicit_change_of_action_is_not_the_prepared_search(self):
        with store.connect() as db:db.execute("UPDATE messages SET content='Comment réparer un vélo ?' WHERE conversation_id='c'")
        self.run_chat([self.call('search_library',{'query':'construire un vélo'}),{'content':'Autre action demandée.'}],[self.a])
        self.assertEqual(len(self.lookup_calls),2)

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

    def test_repeated_searches_are_cached_within_the_same_question(self):
        self.run_chat([self.call('search_library',{'query':'notice'}),self.call('search_library',{'query':'notice'}),{'content':'Fin sans source lue.'}],[self.a])
        self.assertEqual(len(self.lookup_calls),1)

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
        _,answer=self.run_chat(messages,read=lambda key:(_ for _ in ()).throw(HTTPException(404,'Absent')))
        self.assertEqual(answer['sources'],[])

    def test_attached_partial_document_carries_edition_and_does_not_turn_archive_date_into_document_date(self):
        source={**self.a,'document_date':'','archive_date':'2026-05','text':'Première page. '*500}
        payloads,answer=self.run_chat([{'content':'Date du document inconnue ; édition A [1]. Cet extrait ne permet pas de conclure.'}],read=lambda _:source,attached='guide:a')
        attached=payloads[0]['messages'][1]['content']
        self.assertIn('"document_date": ""',attached)
        self.assertIn('"archive_date": "2026-05"',attached)
        self.assertIn('Le texte peut être incomplet',attached)
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
