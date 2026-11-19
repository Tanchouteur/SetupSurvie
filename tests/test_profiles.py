"""Password-free profiles, safe preservation and native bridge; tiny fixtures only."""
import asyncio
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pilot import accounts,app as gateway,library,profiles,store


@contextmanager
def native_database(path):
    db=sqlite3.connect(path)
    try:
        with db:yield db
    finally:db.close()


class ProfileTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.native=self.root/'native.db';self.guides=self.root/'guides';self.guides.mkdir()
        with native_database(self.native) as db:
            db.execute('CREATE TABLE user(id TEXT PRIMARY KEY,name TEXT,email TEXT,role TEXT)')
            db.execute("INSERT INTO user VALUES('original-alice','Alice','alice@survie.local','user')")
        for obj,key,value in [(store,'ROOT',self.root/'state'),(accounts,'DB_PATH',str(self.native)),(library,'GUIDES',self.guides)]:
            p=patch.object(obj,key,value);p.start();self.addCleanup(p.stop)
        store.init();profiles.initialize();self.client=TestClient(gateway.app);self.addCleanup(self.client.close)
        self.client.headers['Origin']='http://testserver'

    def test_existing_identity_keeps_history_and_source_database_bytes(self):
        before=hashlib.sha256(self.native.read_bytes()).digest()
        with store.connect() as db:
            db.execute("INSERT INTO conversations VALUES('history','original-alice','Ancien échange',0)")
        listed=self.client.get('/api/profiles').json()['profiles']
        self.assertTrue(any(p['id']=='original-alice' for p in listed))
        self.assertEqual(self.client.get('/api/conversations/history').status_code,404)
        self.assertEqual(self.client.post('/api/profiles/select',json={'id':'original-alice'}).status_code,200)
        self.assertEqual(self.client.get('/api/conversations/history').json()['title'],'Ancien échange')
        self.assertEqual(hashlib.sha256(self.native.read_bytes()).digest(),before)

    def test_family_works_with_no_cookie_and_without_native_service(self):
        self.native.unlink()
        with patch.object(accounts,'native',side_effect=AssertionError('No network dependency')):
            self.assertEqual(self.client.get('/api/profiles/current').json()['id'],profiles.DEFAULT)
            self.assertEqual(self.client.get('/api/conversations').status_code,200)
            self.assertEqual(self.client.get('/api/profiles').status_code,200)
        self.client.cookies.set(profiles.COOKIE,'missing-old-profile')
        self.assertEqual(self.client.get('/api/profiles/current').json()['id'],profiles.DEFAULT)

    def test_create_switch_persist_and_unknown_selection_never_removes_history(self):
        response=self.client.post('/api/profiles',json={'name':'Élodie'})
        self.assertEqual(response.status_code,201);created=response.json()
        self.assertEqual(set(created),{'id','name','role'})
        self.assertEqual(self.client.get('/api/profiles/current').json()['id'],created['id'])
        store.init();profiles.initialize()
        self.assertEqual(self.client.get('/api/profiles/current').json()['id'],created['id'])
        self.assertEqual(self.client.post('/api/profiles/select',json={'id':'unknown'}).status_code,404)
        self.assertEqual(self.client.get('/api/profiles/current').json()['id'],created['id'])
        self.assertEqual(self.client.post('/api/profiles/select',json={'id':profiles.DEFAULT}).status_code,200)
        self.assertEqual(self.client.get('/api/admin/users').status_code,200)
        self.assertEqual(self.client.post('/api/profiles',json={'name':'   '}).status_code,422)

    def test_portal_profile_does_not_duplicate_when_native_later_creates_its_account(self):
        p=profiles.create('Marc')
        with native_database(self.native) as db:
            db.execute('INSERT INTO user VALUES(?,?,?,?)',('new-native-id',p['name'],p['email'],'user'))
        found=profiles.listing()
        self.assertEqual(len([x for x in found if x['name']=='Marc']),1)
        self.assertEqual(profiles.selected(p['id'])['email'],p['email'])

    def test_orphan_identity_is_recovered_and_native_name_restored_when_available(self):
        with store.connect() as db:db.execute("INSERT INTO conversations VALUES('old','orphan','Saved',0)")
        profiles.sync();self.assertEqual(profiles.selected('orphan')['origin'],'recovered')
        with native_database(self.native) as db:db.execute("INSERT INTO user VALUES('orphan','Marc','marc@survie.local','admin')")
        profiles.sync();restored=profiles.selected('orphan')
        self.assertEqual(restored['name'],'Marc');self.assertEqual(restored['role'],'admin')
        self.assertEqual(restored['origin'],'native')

    def test_native_headers_come_from_selected_profile_not_untrusted_request_headers(self):
        self.client.post('/api/profiles/select',json={'id':'original-alice'})
        response=self.client.get('/api/profiles/webui-headers',headers={'X-Survie-Email':'fake','X-Survie-Role':'admin'})
        self.assertEqual(response.headers['X-Survie-Email'],'alice@survie.local')
        self.assertEqual(response.headers['X-Survie-Role'],'user')
        self.assertNotIn('token',response.text)
        p=profiles.create('Élodie');self.assertEqual(profiles.webui_headers(p)['X-Survie-Name'],'%C3%89lodie')

    def test_profile_change_blocks_stale_write_and_cross_origin_selection(self):
        self.client.post('/api/profiles/select',json={'id':'original-alice'})
        response=self.client.put('/api/favorites',json={'source_id':'guide:anything'},headers={'X-Survie-Profile':profiles.DEFAULT})
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.headers['X-Survie-Profile-Changed'],'true')
        response=self.client.post('/api/profiles/select',json={'id':profiles.DEFAULT},headers={'Origin':'http://evil.invalid'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.client.get('/api/profiles/current').json()['id'],'original-alice')

    def test_native_session_is_internal_and_needs_no_user_password(self):
        real=httpx.AsyncClient;p=profiles.create('Élodie')
        def handler(request):
            self.assertEqual(request.url.path,'/api/v1/auths/signin')
            self.assertEqual(request.headers['X-Survie-Email'],p['email'])
            self.assertEqual(request.headers['X-Survie-Name'],'%C3%89lodie')
            self.assertEqual(json.loads(request.content)['password'],'')
            return httpx.Response(200,json={'token':'fixture-internal-only'})
        with patch.object(accounts.httpx,'AsyncClient',side_effect=lambda **kw:real(transport=httpx.MockTransport(handler),**kw)):
            self.assertEqual(asyncio.run(accounts.profile_token(p)),'fixture-internal-only')
        with patch.object(accounts.httpx,'AsyncClient',side_effect=lambda **kw:real(transport=httpx.MockTransport(lambda r:httpx.Response(503)),**kw)):
            with self.assertRaises(HTTPException):asyncio.run(accounts.profile_token(p))
        self.assertEqual(self.client.get('/api/profiles/current').status_code,200)

    def test_model_downloads_require_the_settings_profile(self):
        self.client.post('/api/profiles/select',json={'id':'original-alice'})
        self.assertEqual(self.client.get('/api/admin/models').status_code,403)
        self.assertEqual(self.client.post('/api/admin/models/download',json={'model':'gemma4:e4b'}).status_code,403)
        self.assertEqual(self.client.post('/api/admin/models/cancel',json={'id':'a'*32}).status_code,403)

    def test_chat_microphone_endpoint_is_removed(self):
        result=self.client.post('/api/transcribe',files={'file':('fixture.webm',b'fixture','audio/webm')})
        self.assertEqual(result.status_code,404)

    def test_lab_access_refresh_changes_only_web_containers_and_keeps_pause(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        import linux_lab as lab
        from types import SimpleNamespace
        mount=self.root/'lab';(mount/'private').mkdir(parents=True)
        pause=mount/'private/inference-paused.json';pause.write_text('paused')
        c={'bind':'127.0.0.1','secret':'fixture','admin_email':'admin@survie.local','admin_password':'fixture'}
        with patch.object(lab,'MOUNT',mount),patch.object(lab,'configuration',return_value=(None,c)),patch.object(lab,'podman',return_value=SimpleNamespace(returncode=0)) as podman,patch.object(lab,'run_container') as run:
            lab.refresh_access()
        self.assertEqual([call.args[0] for call in run.call_args_list],['open-webui','portal'])
        self.assertFalse(any('ollama' in str(call) for call in podman.call_args_list))
        self.assertEqual(pause.read_text(),'paused')
        self.assertTrue((mount/'runtime/deploy/Caddyfile').is_file())
        self.assertIn('127.0.0.1:3000:3000',run.call_args_list[1].args[2])


if __name__=='__main__':unittest.main()
