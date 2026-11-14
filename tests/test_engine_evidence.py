"""Real tool orchestration with simulated HTTP responses, never real inference."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import engine,library,store

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

    def run_chat(self,messages,found=None,read=None,attached=None):
        payloads=[];client_class=httpx.AsyncClient
        def handler(request):
            payloads.append(json.loads(request.content))
            self.assertLessEqual(len(payloads),len(messages))
            event={'message':messages[len(payloads)-1],'done':True,'done_reason':'stop'}
            return httpx.Response(200,content=json.dumps(event).encode()+b'\n')
        with patch.object(engine,'POLICY',POLICY),patch.object(engine.httpx,'AsyncClient',side_effect=lambda **kw:client_class(transport=httpx.MockTransport(handler),**kw)),\
             patch.object(engine.library,'search',AsyncMock(return_value=found if found is not None else [])),patch.object(engine.library,'source',AsyncMock(side_effect=read or (lambda identifier:self.a))):
            asyncio.run(engine.run('j','u','c','rapide',attached))
        with store.connect() as db:
            row=dict(db.execute('SELECT * FROM jobs WHERE id="j"').fetchone())
        self.assertEqual(row['status'],'done',row.get('error'))
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

    def test_failed_archive_search_coverage_reaches_model_even_without_results(self):
        found=library.SearchResults([],{'status':'unavailable','warning':'Recherche incomplète'})
        payloads,answer=self.run_chat([self.call('search_library',{'query':'feu'}),{'content':'La recherche est incomplète.'}],found)
        result=json.loads(payloads[1]['messages'][-1]['content'])
        self.assertEqual(result['results'],[])
        self.assertEqual(result['coverage']['status'],'unavailable')
        self.assertEqual(answer['sources'],[])

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
