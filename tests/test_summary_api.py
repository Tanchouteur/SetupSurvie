"""Real API ownership, isolation, restart and optional-feature regressions."""
import unittest
from unittest.mock import AsyncMock,patch
import test_pilot_api as api_fixture
from pilot import engine,library,operations,store,summaries


class SummaryAPITests(unittest.TestCase):
    setUp=api_fixture.PilotAPITests.setUp
    login=api_fixture.PilotAPITests.login
    headers={'Origin':'http://testserver'}

    def create(self):
        self.login();library.GUIDES.mkdir(exist_ok=True);(library.GUIDES/'a.fr.txt').write_text('Fait documentaire fictif. Aucun guide réel.')
        library.index_guides()
        with patch.object(summaries,'launch'):
            response=self.client.post('/api/summaries',json={'source_ids':['guide:a.fr.txt'],'question':'Compare ces faits fictifs'},headers=self.headers)
        self.assertEqual(response.status_code,202,response.text);return response.json()

    def test_background_job_routes_pause_resume_and_conversation_restore(self):
        item=self.create();conv=self.client.get('/api/conversations/'+item['conversation_id']).json()
        self.assertEqual(conv['summary_jobs'][0]['id'],item['id']);self.assertEqual(len(conv['selected_sources']),1)
        self.assertEqual(self.client.get('/api/summaries/'+item['id']).status_code,200)
        self.assertEqual(self.client.post('/api/summaries/'+item['id']+'/pause',json={},headers=self.headers).json()['status'],'paused')
        with patch.object(summaries,'launch') as launch:
            response=self.client.post('/api/summaries/'+item['id']+'/resume',json={'mode':'rapide'},headers=self.headers)
            self.assertEqual(response.status_code,202,response.text);launch.assert_called_once()
        self.assertEqual(self.client.get('/api/summaries/'+item['id']+'/export').status_code,200)
        self.assertEqual(self.client.get('/api/summaries/'+item['id']+'?offset=-1').status_code,422)

    def test_active_work_cannot_be_deleted_or_interleaved_with_questions_and_edits(self):
        item=self.create();conv=item['conversation_id']
        with patch.object(engine,'launch') as launch:
            for method,path,body in [('post','/api/questions',{'message':'New','conversation_id':conv}),('put','/api/conversations/'+conv+'/sources',{'source_ids':[]}),('put','/api/conversations/'+conv+'/source',{'source_id':None}),('delete','/api/conversations/'+conv,None)]:
                response=getattr(self.client,method)(path,headers=self.headers,**({'json':body} if body is not None else {}))
                self.assertEqual(response.status_code,409,response.text)
            launch.assert_not_called()
        self.client.post('/api/summaries/'+item['id']+'/pause',json={},headers=self.headers)
        self.assertEqual(self.client.delete('/api/conversations/'+conv,headers=self.headers).status_code,200)
        self.assertEqual(self.client.get('/api/summaries/'+item['id']).status_code,404)

    def test_another_profile_cannot_read_resume_or_export_the_snapshot(self):
        item=self.create();self.login('bob')
        with patch.object(library,'source',AsyncMock()) as read:
            for method,suffix,body in [('get','',None),('get','/export',None),('post','/pause',{}),('post','/resume',{})]:
                response=getattr(self.client,method)('/api/summaries/'+item['id']+suffix,headers=self.headers,**({'json':body} if body is not None else {}))
                self.assertEqual(response.status_code,404,response.text)
            response=self.client.post('/api/summaries',json={'conversation_id':item['conversation_id']},headers=self.headers)
            self.assertEqual(response.status_code,404);read.assert_not_awaited()

    def test_only_one_active_summary_per_profile_and_no_inference_on_status(self):
        item=self.create()
        with patch.object(summaries,'launch') as launch:
            result=self.client.post('/api/summaries',json={'source_ids':['guide:a.fr.txt']},headers=self.headers)
            self.assertEqual(result.status_code,409);launch.assert_not_called()
        with patch.object(operations,'status',side_effect=AssertionError('Status/export never starts a model')):
            self.assertEqual(self.client.get('/api/summaries/'+item['id']).status_code,200)
            self.assertEqual(self.client.get('/api/summaries/'+item['id']+'/export').status_code,200)
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM summary_jobs').fetchone()[0],1)

    def test_resume_waits_for_a_question_in_the_same_conversation(self):
        item=self.create();conv=item['conversation_id']
        self.client.post('/api/summaries/'+item['id']+'/pause',json={},headers=self.headers)
        with patch.object(engine,'launch'):
            self.assertEqual(self.client.post('/api/questions',json={'message':'Question durant la pause','conversation_id':conv},headers=self.headers).status_code,200)
        with patch.object(summaries,'launch') as launch:
            response=self.client.post('/api/summaries/'+item['id']+'/resume',json={},headers=self.headers)
            self.assertEqual(response.status_code,409);launch.assert_not_called()
        self.assertEqual(self.client.get('/api/summaries/'+item['id']).json()['status'],'paused')

    def test_optional_summary_failure_leaves_core_available(self):
        self.create()
        with store.connect() as db:db.execute('DROP TABLE summary_jobs')
        self.assertEqual(self.client.post('/api/summaries',json={'source_ids':['guide:a.fr.txt']},headers=self.headers).status_code,503)
        self.assertEqual(self.client.get('/api/conversations').status_code,200)
        with patch.object(engine,'launch'):
            self.assertEqual(self.client.post('/api/questions',json={'message':'Question sans synthèse','source_ids':[]},headers=self.headers).status_code,200)
