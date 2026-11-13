import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from pilot import accounts, app as gateway, engine, library, operations,store,translations,profiles


class PilotAPITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.users={key:{'id':key,'email':key+'@survie.local','role':'admin' if key=='admin' else 'user','name':key} for key in ['admin','alice','bob']}
        async def native(path,payload=None,token=None):
            if path=='/api/v1/auths/signin':
                key=payload['email'].split('@')[0];return {**self.users[key],'token':key}
            if path=='/api/v1/auths/':return self.users[token]
            if path=='/api/v1/auths/signout':return {'ok':True}
            raise AssertionError(path)
        for obj,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',self.root/'guides'),
                               (accounts,'native',AsyncMock(side_effect=native)),(profiles,'native_profiles',lambda:list(self.users.values())),(library,'books',AsyncMock(return_value=[])),
                               (operations,'status',AsyncMock(return_value={'online':True,'message':'Prêt'}))]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        self.client=TestClient(gateway.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)

    def login(self,who='alice'):
        response=self.client.post('/api/profiles/select',json={'id':who},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,200);return response

    def test_learning_paths_are_read_only_and_available_without_an_ai_session(self):
        with patch.object(engine,'launch') as launch,patch.object(operations,'status',side_effect=AssertionError('No engine needed')):
            response=self.client.get('/api/library/learning')
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(response.json()['domains']),14)
            self.assertEqual(len(response.json()['steps']),6)
            self.assertEqual(self.client.get('/api/conversations').status_code,200)
            launch.assert_not_called()

    def test_missing_learning_catalogue_returns_friendly_error_without_blocking_search(self):
        with patch.object(gateway.learning,'RULES',self.root/'absent.json'):
            self.assertEqual(self.client.get('/api/library/learning').status_code,503)
        self.assertEqual(self.client.get('/api/search?q=').json(),{'results':[]})

    def test_uploaded_document_preserves_declared_dates_and_rejects_impossible_dates(self):
        self.login('admin');headers={'Origin':'http://testserver'}
        response=self.client.post('/api/admin/guides',files={'file':('notice.txt',b'Volume : 40 litres.','text/plain')},
                                  data={'title':'Notice fictive','document_date':'2010-05','edition':'Deuxième édition'},headers=headers)
        self.assertEqual(response.status_code,200)
        source=self.client.get('/api/source',params={'id':response.json()['id']}).json()
        self.assertEqual(source['document_date'],'2010-05');self.assertEqual(source['edition'],'Deuxième édition')
        self.assertRegex(source['collected_at'],r'^\d{4}-\d{2}-\d{2}$')
        self.assertEqual(source['archive_date'],'')
        before=list(library.GUIDES.iterdir())
        response=self.client.post('/api/admin/guides',files={'file':('bad.txt',b'Fiction','text/plain')},
                                  data={'title':'Bad','document_date':'2026-02-30'},headers=headers)
        self.assertEqual(response.status_code,422);self.assertEqual(list(library.GUIDES.iterdir()),before)
        self.client.cookies.clear();self.login('alice')
        self.assertEqual(self.client.post('/api/admin/guides',files={'file':('x.txt',b'Fiction')},data={'title':'x'},headers=headers).status_code,403)

    def test_associated_document_survives_reopen_and_omitted_source_then_can_be_removed(self):
        self.login();library.GUIDES.mkdir();(library.GUIDES/'guide.en.txt').write_text('Useful water guide')
        library.index_guides();headers={'Origin':'http://testserver'}
        with patch.object(engine,'launch') as launch:
            created=self.client.post('/api/questions',json={'message':'Explique ce document','source_id':'guide:guide.en.txt'},headers=headers).json()
            conv=created['conversation_id']
            saved=self.client.get('/api/conversations/'+conv).json()
            self.assertEqual(saved['source']['id'],'guide:guide.en.txt')
            self.client.post('/api/questions',json={'message':'Et ensuite ?','conversation_id':conv},headers=headers)
            self.assertEqual(launch.call_args.args[-1],'guide:guide.en.txt')
        self.assertEqual(self.client.put('/api/conversations/'+conv+'/source',json={'source_id':None},headers=headers).status_code,200)
        self.assertIsNone(self.client.get('/api/conversations/'+conv).json()['source'])
        with patch.object(library,'source',new_callable=AsyncMock) as source:
            self.assertEqual(self.client.put('/api/conversations/'+conv+'/source',json={'source_id':'guide:guide.en.txt'},headers={'Cookie':profiles.COOKIE+'=bob','Origin':'http://testserver'}).status_code,404)
            source.assert_not_awaited()

    def test_translation_endpoints_isolation_restart_export_and_deletion(self):
        self.login();library.GUIDES.mkdir();(library.GUIDES/'guide.en.txt').write_text('Useful water guide')
        library.index_guides();headers={'Origin':'http://testserver'}
        with patch.object(translations,'launch'):
            response=self.client.post('/api/translations',json={'source_id':'guide:guide.en.txt'},headers=headers)
        self.assertEqual(response.status_code,202);item=response.json();key=item['id'];conv=item['conversation_id']
        self.assertEqual(self.client.get('/api/conversations/'+conv).json()['translations'],[key])
        for suffix in ['', '/export']:
            self.assertEqual(self.client.get('/api/translations/'+key+suffix,headers={'Cookie':profiles.COOKIE+'=bob','Origin':'http://testserver'}).status_code,404)
        self.assertEqual(self.client.post('/api/translations/'+key+'/pause',json={},headers={'Cookie':profiles.COOKIE+'=bob','Origin':'http://testserver'}).status_code,404)
        self.assertEqual(self.client.delete('/api/conversations/'+conv,headers=headers).status_code,409)
        self.assertEqual(self.client.post('/api/translations/'+key+'/pause',json={},headers=headers).status_code,200)
        self.assertIn('pas encore traduit',self.client.get('/api/translations/'+key+'/export').text)
        with patch.object(operations,'status',AsyncMock(return_value={'online':False,'paused':True,'message':'mode jeu'})),patch.object(translations,'launch') as launch:
            self.assertEqual(self.client.post('/api/translations/'+key+'/resume',json={},headers=headers).status_code,503)
            launch.assert_not_called()
        self.assertEqual(self.client.delete('/api/conversations/'+conv,headers=headers).status_code,200)
        self.assertEqual(self.client.get('/api/translations/'+key).status_code,404)
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM translation_parts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM conversation_sources').fetchone()[0],0)

    def test_full_library_profile_reaches_controller_without_old_gateway_limit(self):
        self.login('admin')
        with patch.object(operations,'library_command',AsyncMock(return_value={'accepted':True})) as command:
            response=self.client.post('/api/admin/library/plan',json={'themes':['eau']*29,'max_add_gb':0},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,202);self.assertEqual(command.call_args.args[1]['max_add_gb'],0)

    def test_profile_choice_is_persistent_httponly_and_secure_on_https(self):
        response=self.login()
        header=response.headers['set-cookie'].lower()
        self.assertIn('max-age=315360000',header);self.assertIn('httponly',header);self.assertIn('samesite=lax',header)
        response=self.client.post('/api/profiles/select',json={'id':'alice'},headers={'Origin':'http://testserver','X-Forwarded-Proto':'https'})
        self.assertIn('; Secure',response.headers['set-cookie'])

    def test_cross_origin_mutation_and_cookie_without_origin_are_rejected(self):
        self.login()
        for headers in [{},{'Origin':'http://evil.invalid'}]:
            response=self.client.post('/api/profiles/select',json={'id':'bob'},headers=headers)
            self.assertEqual(response.status_code,403)

    def test_reader_cannot_access_admin_or_other_history(self):
        self.login()
        with store.connect() as db:db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('private','bob','Secret',time.time()))
        self.assertEqual(self.client.get('/api/conversations/private').status_code,404)
        self.assertEqual(self.client.get('/api/admin/users').status_code,403)
        self.assertEqual(self.client.get('/api/conversations').json()['conversations'],[])

    def test_library_management_requires_admin_and_forwards_only_fixed_actions(self):
        self.login()
        with patch.object(operations,'library_command',new_callable=AsyncMock) as command:
            self.assertEqual(self.client.get('/api/admin/library').status_code,403)
            for action in ('plan','download','pause'):
                self.assertEqual(self.client.post('/api/admin/library/'+action,json={},headers={'Origin':'http://testserver'}).status_code,403)
            command.assert_not_called()
        self.client.cookies.clear()
        self.login('admin')
        with patch.object(operations,'library_command',new_callable=AsyncMock,return_value={'accepted':True}) as command:
            response=self.client.post('/api/admin/library/plan',json={'themes':['energie'],'max_add_gb':5},headers={'Origin':'http://testserver'})
            self.assertEqual(response.status_code,202)
            command.assert_awaited_once_with('plan',{'themes':['energie'],'languages':['fr','en'],'max_add_gb':5,'include_supplements':False})
        self.assertEqual(self.client.post('/api/admin/library/download',json={'id':'../outside'},headers={'Origin':'http://testserver'}).status_code,422)

    def test_delete_conversation_checks_owner_and_active_jobs_and_removes_data(self):
        self.login()
        with patch.object(engine,'launch'):
            created=self.client.post('/api/questions',json={'message':'À supprimer'},headers={'Origin':'http://testserver'}).json()
        path='/api/conversations/'+created['conversation_id']
        self.assertEqual(self.client.delete(path,headers={'Cookie':profiles.COOKIE+'=bob','Origin':'http://testserver'}).status_code,404)
        self.assertEqual(self.client.delete(path,headers={'Origin':'http://testserver'}).status_code,409)
        trace=store.ROOT/'traces'/f"{created['id']}.json";trace.parent.mkdir();trace.write_text('trace')
        with store.connect() as db:db.execute("UPDATE jobs SET status='done' WHERE id=?",(created['id'],))
        self.assertEqual(self.client.delete(path,headers={'Origin':'http://testserver'}).status_code,200)
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertFalse(trace.exists())
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

    def test_no_password_or_recovery_code_is_needed_after_old_sessions_expire(self):
        self.client.cookies.set(gateway.COOKIE,'expired-old-session')
        with patch.object(accounts,'native',side_effect=AssertionError('No upstream login')):
            self.assertEqual(self.client.get('/api/profiles/current').json()['id'],profiles.DEFAULT)
            self.login('bob')
            self.assertEqual(self.client.get('/api/profiles/current').json()['id'],'bob')
        self.assertNotIn('recovery_ready',self.client.get('/api/profiles/current').json())

    def test_password_endpoints_explain_the_new_profile_flow(self):
        for path in ('login','recover','recovery-code','logout'):
            self.assertEqual(self.client.post('/api/auth/'+path,json={}).status_code,410)

    def test_stale_tab_cannot_write_to_the_newly_selected_profile(self):
        self.login('alice');self.login('bob')
        response=self.client.post('/api/questions',json={'message':'Ancien onglet'},headers={'Origin':'http://testserver','X-Survie-Profile':'alice'})
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.headers['X-Survie-Profile-Changed'],'true')

    def test_job_isolation_and_cancel_before_start(self):
        self.login()
        with patch.object(engine,'launch'):
            response=self.client.post('/api/questions',json={'message':'Question de test','mode':'rapide'},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,200);identifier=response.json()['id']
        self.assertEqual(self.client.get('/api/jobs/'+identifier).status_code,200)
        self.assertEqual(self.client.get('/api/jobs/'+identifier,headers={'Cookie':profiles.COOKIE+'=bob','Origin':'http://testserver'}).status_code,404)
        self.assertEqual(self.client.post('/api/jobs/'+identifier+'/cancel',headers={'Origin':'http://testserver'}).status_code,200)
        self.assertEqual(self.client.get('/api/jobs/'+identifier).json()['status'],'cancelled')

    def test_paused_engine_is_explicit_and_does_not_create_a_job(self):
        self.login()
        with patch.object(operations,'status',AsyncMock(return_value={'online':False,'message':'Assistant en pause — mode jeu'})),patch.object(engine,'launch') as launch:
            response=self.client.post('/api/questions',json={'message':'Ma question'},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,503);self.assertIn('mode jeu',response.json()['detail']);launch.assert_not_called()
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

    def test_reader_cannot_force_engine_start(self):
        self.login()
        with patch.object(operations,'command') as command:
            response=self.client.post('/api/admin/inference/start',json={'force':True},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,403);command.assert_not_called()


if __name__=='__main__':unittest.main()
