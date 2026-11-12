import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from pilot import accounts, app as gateway, engine, library, operations,store,translations


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
                               (accounts,'native',AsyncMock(side_effect=native)),(library,'books',AsyncMock(return_value=[])),
                               (operations,'status',AsyncMock(return_value={'online':True,'message':'Prêt'}))]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        self.client=TestClient(gateway.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)

    def login(self,who='alice'):
        response=self.client.post('/api/auth/login',json={'email':who,'password':'example-password'})
        self.assertEqual(response.status_code,200);return response

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
            self.assertEqual(self.client.put('/api/conversations/'+conv+'/source',json={'source_id':'guide:guide.en.txt'},headers={'Authorization':'Bearer bob'}).status_code,404)
            source.assert_not_awaited()

    def test_translation_endpoints_isolation_restart_export_and_deletion(self):
        self.login();library.GUIDES.mkdir();(library.GUIDES/'guide.en.txt').write_text('Useful water guide')
        library.index_guides();headers={'Origin':'http://testserver'}
        with patch.object(translations,'launch'):
            response=self.client.post('/api/translations',json={'source_id':'guide:guide.en.txt'},headers=headers)
        self.assertEqual(response.status_code,202);item=response.json();key=item['id'];conv=item['conversation_id']
        self.assertEqual(self.client.get('/api/conversations/'+conv).json()['translations'],[key])
        for suffix in ['', '/export']:
            self.assertEqual(self.client.get('/api/translations/'+key+suffix,headers={'Authorization':'Bearer bob'}).status_code,404)
        self.assertEqual(self.client.post('/api/translations/'+key+'/pause',json={},headers={'Authorization':'Bearer bob'}).status_code,404)
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

    def test_cookie_has_30_days_httponly_and_secure_on_https(self):
        response=self.login()
        header=response.headers['set-cookie'].lower()
        self.assertIn('max-age=2592000',header);self.assertIn('httponly',header);self.assertIn('samesite=lax',header)
        response=self.client.post('/api/auth/login',json={'email':'alice','password':'example'},headers={'Origin':'http://testserver','X-Forwarded-Proto':'https'})
        self.assertIn('; Secure',response.headers['set-cookie'])

    def test_cross_origin_mutation_and_cookie_without_origin_are_rejected(self):
        self.login()
        for headers in [{},{'Origin':'http://evil.invalid'}]:
            response=self.client.post('/api/auth/recovery-code',headers=headers)
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
            command.assert_awaited_once_with('plan',{'themes':['energie'],'languages':['fr','en'],'max_add_gb':5})
        self.assertEqual(self.client.post('/api/admin/library/download',json={'id':'../outside'},headers={'Origin':'http://testserver'}).status_code,422)

    def test_delete_conversation_checks_owner_and_active_jobs_and_removes_data(self):
        self.login()
        with patch.object(engine,'launch'):
            created=self.client.post('/api/questions',json={'message':'À supprimer'},headers={'Origin':'http://testserver'}).json()
        path='/api/conversations/'+created['conversation_id']
        self.assertEqual(self.client.delete(path,headers={'Authorization':'Bearer bob'}).status_code,404)
        self.assertEqual(self.client.delete(path,headers={'Origin':'http://testserver'}).status_code,409)
        trace=store.ROOT/'traces'/f"{created['id']}.json";trace.parent.mkdir();trace.write_text('trace')
        with store.connect() as db:db.execute("UPDATE jobs SET status='done' WHERE id=?",(created['id'],))
        self.assertEqual(self.client.delete(path,headers={'Origin':'http://testserver'}).status_code,200)
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertFalse(trace.exists())
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

    def test_recovery_code_hashed_single_use_and_replaced(self):
        self.login()
        response=self.client.post('/api/auth/recovery-code',headers={'Origin':'http://testserver'})
        code=response.json()['code']
        with store.connect() as db:row=dict(db.execute('SELECT * FROM recovery').fetchone())
        self.assertNotIn(code,json.dumps(row));self.assertTrue(store.consume_code('alice',code));self.assertFalse(store.consume_code('alice',code))
        new=store.recovery_code('alice');self.assertNotEqual(new,code);self.assertFalse(store.consume_code('alice',code));self.assertTrue(store.consume_code('alice',new))

    def test_logout_revokes_token_even_if_upstream_still_accepts_it(self):
        self.login()
        self.assertEqual(self.client.post('/api/auth/logout',headers={'Origin':'http://testserver'}).status_code,200)
        self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer alice'}).status_code,401)

    def test_utf8_password_validated_before_consuming_recovery_code(self):
        with patch.object(accounts,'native_account') as account:
            response=self.client.post('/api/auth/recover',json={'email':'alice','code':'A'*32,'new_password':'é'*40})
            self.assertEqual(response.status_code,400);account.assert_not_called()

    def test_job_isolation_and_cancel_before_start(self):
        self.login()
        with patch.object(engine,'launch'):
            response=self.client.post('/api/questions',json={'message':'Question de test','mode':'rapide'},headers={'Origin':'http://testserver'})
        self.assertEqual(response.status_code,200);identifier=response.json()['id']
        self.assertEqual(self.client.get('/api/jobs/'+identifier).status_code,200)
        self.assertEqual(self.client.get('/api/jobs/'+identifier,headers={'Authorization':'Bearer bob'}).status_code,404)
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
