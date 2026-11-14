import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import HTTPException
from pilot import accounts, app as gateway, engine, library, operations,store,translations,profiles,catalogue,inventory,assistant_metrics,calibration,search_experiment


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

    def test_calibration_is_explicit_family_only_and_validates_settings(self):
        self.login('alice');headers={'Origin':'http://testserver'}
        self.assertEqual(self.client.get('/api/admin/assistant/calibration').status_code,403)
        self.assertEqual(self.client.post('/api/admin/assistant/calibration/start',json={},headers=headers).status_code,403)
        self.client.cookies.clear();self.login('admin')
        with patch.object(calibration,'start',AsyncMock(return_value={'id':'a'*32,'status':'running'})) as start:
            response=self.client.get('/api/admin/assistant/calibration');self.assertEqual(response.status_code,200);start.assert_not_called()
            self.assertEqual(self.client.post('/api/admin/assistant/calibration/start',json={'max_context':999999},headers=headers).status_code,422)
            self.assertEqual(self.client.post('/api/admin/assistant/calibration/start',json={'mode':'rapide','max_context':32768},headers=headers).status_code,202)
            self.assertEqual(start.await_args.kwargs['reserve_ram_bytes'],4*1024**3)
            self.assertEqual(start.await_args.kwargs['reserve_video_bytes'],512*1024**2)

    def test_search_experiment_is_explicit_family_only_with_bounded_options(self):
        self.login('alice');headers={'Origin':'http://testserver'}
        self.assertEqual(self.client.get('/api/admin/search-experiment').status_code,403)
        self.assertEqual(self.client.post('/api/admin/search-experiment/start',json={},headers=headers).status_code,403)
        self.client.cookies.clear();self.login('admin')
        with patch.object(search_experiment,'start',AsyncMock(return_value={'schema':1,'id':'a'*32,'status':'running','cases':[]})) as start:
            self.assertEqual(self.client.get('/api/admin/search-experiment').status_code,200);start.assert_not_called()
            self.assertEqual(self.client.post('/api/admin/search-experiment/start',json={'latency_budget_seconds':500},headers=headers).status_code,422)
            response=self.client.post('/api/admin/search-experiment/start',json={'suite':'verification','latency_budget_seconds':15},headers=headers)
            self.assertEqual(response.status_code,202);self.assertEqual(response.json()['version'],gateway.VERSION)
            self.assertEqual(start.await_args.args,('rapide','verification',15000))
        self.assertEqual(self.client.post('/api/admin/search-experiment/review',json={'id':'a'*32,'case_id':'verify-fire','judgments':{'x':'invented'}},headers=headers).status_code,422)

    def test_measurements_export_requires_job_owner_and_excludes_conversation(self):
        self.login('alice')
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('measure-c','alice','Private title',0))
            db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('measure-job','alice','measure-c','rapide','done',0,0))
        measured=assistant_metrics.Measurement('measure-job','fixture','rapide',16384);measured.finish('done')
        response=self.client.get('/api/jobs/measure-job/measurements')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['version'],gateway.VERSION)
        self.assertNotIn('Private title',response.text);self.assertNotIn('alice',response.text);self.assertNotIn('sources',response.json())
        self.client.cookies.clear();self.login('bob')
        self.assertEqual(self.client.get('/api/jobs/measure-job/measurements').status_code,404)

    def test_metadata_edits_require_family_revision_and_preserve_original_files(self):
        self.login('alice');headers={'Origin':'http://testserver'}
        library.GUIDES.mkdir(parents=True,exist_ok=True);path=library.GUIDES/'fixture.fr.txt';path.write_text('Fictional mechanism document.')
        library.index_guides();revision=catalogue.revision('guide:fixture.fr.txt',library.GUIDES,self.root/'zim')
        body={'source_id':'guide:fixture.fr.txt','revision':revision,'domains':['resilience','culture'],'document_type':'procedure','reviewed':True}
        self.assertEqual(self.client.put('/api/admin/library/classification',json=body,headers=headers).status_code,403)
        self.assertEqual(self.client.get('/api/admin/library/metadata-export').status_code,403)
        self.client.cookies.clear();self.login('admin')
        self.assertEqual(self.client.put('/api/admin/library/classification',json=body,headers=headers).status_code,200)
        info=self.client.get('/api/source',params={'id':body['source_id']}).json()['classification'];self.assertEqual(info['status'],'reviewed')
        self.assertEqual(self.client.put('/api/admin/library/classification',json={**body,'domains':['invalid']},headers=headers).status_code,422)
        path.write_text('Another edition, changed size.')
        self.assertEqual(self.client.put('/api/admin/library/classification',json=body,headers=headers).status_code,409)
        exported=self.client.get('/api/admin/library/metadata-export').json();self.assertEqual(len(exported['records']),1)
        self.assertNotIn('Fictional',json.dumps(exported));self.assertNotIn('admin',json.dumps(exported))
        self.assertEqual(self.client.delete('/api/admin/library/metadata',params={'source_id':body['source_id']},headers=headers).status_code,200)
        self.assertEqual(self.client.get('/api/admin/library/metadata-export').json()['records'],[])
        self.assertEqual(path.read_text(),'Another edition, changed size.')

    def test_collection_names_can_be_corrected_without_changing_archive_id(self):
        self.login('admin');headers={'Origin':'http://testserver'};zims=self.root/'zim';zims.mkdir();stem='example-channel_en_energy_2026-01';(zims/(stem+'.zim')).write_bytes(b'Archive fixture')
        with patch.object(inventory,'ZIMS',zims):
            revision=catalogue.revision('collection:'+stem,library.GUIDES,zims)
            body={'collection_id':stem,'revision':revision,'family':'Groupe de recette','variant':'Énergie et batteries'}
            response=self.client.put('/api/admin/library/collection-labels',json=body,headers=headers)
            self.assertEqual(response.status_code,200,response.text)
            row=self.client.get('/api/inventory').json()['books'][0]
        self.assertEqual(row['family'],body['family']);self.assertEqual(row['variant'],body['variant']);self.assertEqual(row['id'],stem)

    def test_missing_learning_catalogue_returns_friendly_error_without_blocking_search(self):
        with patch.object(gateway.learning,'RULES',self.root/'absent.json'):
            self.assertEqual(self.client.get('/api/library/learning').status_code,503)
        self.assertEqual(self.client.get('/api/search?q=').json(),{'results':[]})

    def test_search_reports_incomplete_archive_coverage_without_hiding_guide_results(self):
        found=library.SearchResults([{'id':'guide:test','title':'Test'}],{'status':'partial','failed':1,'warning':'Recherche partielle'})
        with patch.object(library,'search',AsyncMock(return_value=found)):
            data=self.client.get('/api/search?q=feu').json()
        self.assertEqual(data['results'][0]['id'],'guide:test')
        self.assertEqual(data['coverage']['status'],'partial')

    def test_context_and_index_commands_require_family_and_validate_inputs(self):
        self.login('alice');headers={'Origin':'http://testserver'}
        self.assertEqual(self.client.get('/api/admin/context').status_code,403)
        self.assertEqual(self.client.post('/api/admin/library/index/start',json={},headers=headers).status_code,403)
        self.client.cookies.clear();self.login('admin')
        model=engine.MODES['rapide']['model']
        self.assertEqual(self.client.post('/api/admin/context',json={'model':model,'tokens':32768},headers=headers).status_code,200)
        self.assertEqual(engine.context_size(model),32768)
        self.assertEqual(self.client.post('/api/admin/context',json={'model':model,'tokens':999},headers=headers).status_code,422)
        self.assertEqual(self.client.post('/api/admin/context',json={'model':'unknown','tokens':16384},headers=headers).status_code,400)
        with patch.object(operations,'library_command',AsyncMock(return_value={'accepted':True})) as command:
            self.assertEqual(self.client.post('/api/admin/library/index/start',json={},headers=headers).status_code,200)
            command.assert_awaited_once_with('index')
        self.assertEqual(self.client.get('/api/search?q=feu&domain=unknown').status_code,422)

    def test_index_schedule_is_family_only_and_uses_validated_fixed_command(self):
        self.login('alice');headers={'Origin':'http://testserver'}
        self.assertEqual(self.client.post('/api/admin/library/index-settings',json={'enabled':True},headers=headers).status_code,403)
        self.client.cookies.clear();self.login('admin')
        with patch.object(operations,'library_command',AsyncMock(return_value={'accepted':True})) as command:
            self.assertEqual(self.client.post('/api/admin/library/index-settings',json={'enabled':True,'start_hour':22,'end_hour':6,'workers':2},headers=headers).status_code,200)
            command.assert_awaited_once_with('index-settings',{'enabled':True,'start_hour':22,'end_hour':6,'workers':2})
        self.assertEqual(self.client.post('/api/admin/library/index-settings',json={'workers':17},headers=headers).status_code,422)

    def test_search_diagnostic_is_read_only_and_reports_safe_catalogue_errors(self):
        catalog=library.Catalog(available=False,error='catalog_timeout')
        with patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',AsyncMock(side_effect=HTTPException(404,'Fixture unavailable'))),patch.object(engine,'launch') as launch:
            result=self.client.get('/api/library/search-diagnostic')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['catalog']['error'],'catalog_timeout')
        self.assertEqual(result.json()['kiwix']['state'],'unavailable')
        launch.assert_not_called()

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

    def test_non_secret_profile_choice_is_persistent_and_usable_on_http_and_https(self):
        response=self.login()
        header=response.headers['set-cookie'].lower()
        self.assertIn('max-age=315360000',header);self.assertIn('httponly',header);self.assertIn('samesite=lax',header)
        response=self.client.post('/api/profiles/select',json={'id':'alice'},headers={'Origin':'http://testserver','X-Forwarded-Proto':'https'})
        self.assertNotIn('; Secure',response.headers['set-cookie'])

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
        with patch.dict(engine.PROGRESS,{identifier:{'stage':'reading','sources_found':3,'sources_read':1}}):
            state=self.client.get('/api/jobs/'+identifier)
            self.assertEqual(state.status_code,200);self.assertEqual(state.json()['progress']['stage'],'reading')
            self.assertEqual(state.json()['progress']['sources_read'],1)
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
