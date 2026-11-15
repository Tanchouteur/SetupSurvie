"""Observed work survives model mistakes, without making a claim of answer quality."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import httpx
from pilot import documentary,store,assistant_metrics,durable


class DocumentaryTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        p=patch.object(store,'ROOT',Path(temporary.name));p.start();self.addCleanup(p.stop);store.init()
        with store.connect() as db:
            for identifier in ('c','other'):db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(identifier,'u','Fixture',0))
            for identifier,conversation,role in [(1,'c','user'),(2,'c','assistant'),(3,'other','assistant')]:
                db.execute('INSERT INTO messages(id,conversation_id,role,content,created) VALUES(?,?,?,?,?)',(identifier,conversation,role,'Unchanged fictional message',0))
            db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('j','u','c','rapide','running',0,0))

    def test_repeated_queries_and_sources_do_not_inflate_observed_counts(self):
        observed=documentary.Evidence()
        value={'results':[{'id':'guide:a'}],'coverage':{'status':'partial','domain':'resilience'}}
        for _ in range(3):observed.record('search_library',{'query':'PRIVATE_QUESTION'},value,key=('same',))
        for _ in range(3):observed.record('read_source',{'id':'guide:a'},{'id':'guide:a','text':'PRIVATE_TEXT','more':True})
        result=observed.summary()
        self.assertEqual(result,{'schema':1,'status':'partial','scope':'targeted','searches':1,'results':1,'sources_read':1,'failed_reads':0,'partial_reads':1})
        self.assertNotIn('PRIVATE',json.dumps(result));self.assertNotIn('guide:a',json.dumps(result))

    def test_read_failures_and_successful_retries_are_not_absence_claims(self):
        observed=documentary.Evidence();observed.record('search_library',{}, {'results':[],'coverage':{'status':'complete'}})
        observed.record('read_source',{'id':'guide:a','offset':50},{'error':'PRIVATE ERROR'})
        self.assertEqual(observed.summary()['status'],'partial');self.assertEqual(observed.summary()['failed_reads'],1)
        observed.record('read_source',{'id':'guide:a','offset':50},{'id':'guide:canonical','text':'A fictional passage','partial_read':True})
        self.assertEqual(observed.summary()['status'],'complete');self.assertEqual(observed.summary()['failed_reads'],0)
        self.assertEqual(observed.summary()['sources_read'],1);self.assertEqual(observed.summary()['partial_reads'],1)

    def test_zero_matches_unknown_coverage_favorites_and_attached_document_stay_distinct(self):
        observed=documentary.Evidence();self.assertEqual(observed.summary()['status'],'not_run')
        observed.record('search_library',{}, {'results':[],'coverage':{'status':'complete'}})
        self.assertEqual(observed.summary()['status'],'complete');self.assertEqual(observed.summary()['results'],0)
        unknown=documentary.Evidence();unknown.record('search_library',{}, {'results':[]})
        self.assertEqual(unknown.summary()['status'],'unknown')
        favorites=documentary.Evidence();favorites.record('search_library',{'favorites_only':True},{'results':[]})
        self.assertEqual(favorites.summary()['scope'],'favorites');self.assertEqual(favorites.summary()['status'],'complete')
        attached=documentary.Evidence();attached.record('read_source',{'id':'guide:a'},{'id':'guide:a','text':'Fictional passage'})
        self.assertEqual(attached.summary()['scope'],'document');self.assertEqual(attached.summary()['status'],'not_run')

    def test_bad_search_and_empty_text_are_observed_without_private_payloads(self):
        observed=documentary.Evidence();observed.record('search_library',{}, {'error':'PRIVATE ERROR'})
        self.assertEqual(observed.summary()['status'],'unavailable')
        observed.record('read_source',{'id':'private/path'},{'text':'   '})
        self.assertEqual(observed.summary()['sources_read'],0);self.assertEqual(observed.summary()['failed_reads'],1)
        observed.record('search_library',{}, {'results':None,'coverage':{'status':[]}})
        self.assertNotIn('PRIVATE',json.dumps(observed.summary()))

    def test_parser_keeps_only_known_numerical_data_and_rejects_fake_validation(self):
        valid=documentary.Evidence().summary()
        self.assertEqual(documentary.clean({**valid,'question':'PRIVATE'}),valid)
        for changed in ({'sources_read':True},{'searches':-1},{'results':float('nan')},{'status':'verified'},{'scope':[]},{'schema':True}):
            self.assertIsNone(documentary.clean({**valid,**changed}))
        self.assertIsNone(documentary.clean('x'*2049))

    def test_persisted_summary_is_linked_to_the_answer_and_survives_job_cleanup(self):
        summary=documentary.Evidence().summary();summary.update(status='partial',searches=1)
        self.assertTrue(documentary.save('j',summary));self.assertEqual(documentary.for_job('j'),{**summary,'consulted_sources':[]})
        self.assertNotIn('documentary',store.messages('c')[0])
        with store.connect() as db:self.assertTrue(documentary.save('j',summary,message_id=2,db=db))
        self.assertEqual(store.messages('c')[-1]['documentary'],{**summary,'consulted_sources':[]})
        with store.connect() as db:db.execute('DELETE FROM jobs WHERE id=?',('j',))
        self.assertEqual(store.messages('c')[-1]['documentary'],{**summary,'consulted_sources':[]})
        with store.connect() as db:db.execute('DELETE FROM conversations WHERE id=?',('c',))
        self.assertIsNone(documentary.for_job('j'))

    def test_summary_cannot_attach_to_another_conversation_or_user_message(self):
        summary=documentary.Evidence().summary()
        self.assertFalse(documentary.save('j',summary,message_id=3))
        self.assertFalse(documentary.save('j',summary,message_id=1))
        self.assertFalse(documentary.save('missing',summary,message_id=2))
        self.assertNotIn('documentary',store.messages('other')[0])

    def test_missing_optional_table_preserves_legacy_messages_and_core_schema(self):
        with store.connect() as db:
            columns=[tuple(row) for row in db.execute('PRAGMA table_info(messages)')]
            db.execute('DROP TABLE documentary_evidence')
        self.assertFalse(documentary.save('j',documentary.Evidence().summary()))
        self.assertIsNone(documentary.for_job('j'));self.assertEqual(documentary.for_messages('c'),{})
        self.assertEqual(store.messages('c')[-1]['content'],'Unchanged fictional message')
        store.init()
        with store.connect() as db:self.assertEqual([tuple(row) for row in db.execute('PRAGMA table_info(messages)')],columns)
        self.assertNotIn('documentary',store.messages('c')[-1])

    def test_consulted_links_are_bounded_private_metadata_not_measurement_text(self):
        sources=[{'id':'guide:'+str(i)+'é'*1900,'title':'Document '+str(i),'text':'PRIVATE SOURCE','question':'PRIVATE QUESTION'} for i in range(15)]
        cleaned=documentary.clean_sources(sources)
        self.assertLessEqual(len(cleaned),12);self.assertLessEqual(len(json.dumps(cleaned)),40000)
        self.assertTrue(all(set(row)=={'id','title'} for row in cleaned))
        self.assertEqual(documentary.clean_sources([{'id':'javascript:alert(1)','title':'PRIVATE'}]),[])
        summary=documentary.Evidence().summary()
        self.assertTrue(documentary.save('j',summary,sources=cleaned,message_id=2))
        self.assertEqual(store.messages('c')[-1]['documentary']['consulted_sources'],cleaned)
        durable.write_bytes(assistant_metrics.path('j'),json.dumps({'schema':1,'documentary':{**summary,'consulted_sources':sources,'question':'PRIVATE'}}).encode(),private=True)
        self.assertEqual(assistant_metrics.read('j')['documentary'],summary)
        self.assertNotIn('PRIVATE',json.dumps(assistant_metrics.read('j')))


class DocumentaryApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        p=patch.object(store,'ROOT',Path(temporary.name));p.start();self.addCleanup(p.stop);store.init()
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','u','Fixture',0))
            db.execute('INSERT INTO messages(id,conversation_id,role,content,created) VALUES(?,?,?,?,?)',(1,'c','assistant','Fictional model statement',0))
            db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('j','u','c','rapide','done',0,0))
        from pilot import app as gateway
        self.gateway=gateway;gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'u'}
        self.addCleanup(gateway.app.dependency_overrides.pop,gateway.user,None)

    async def test_summary_and_uncited_consulted_links_use_the_same_profile_checks(self):
        summary=documentary.Evidence().summary();summary.update(status='partial',searches=1,sources_read=1)
        documentary.save('j',summary,sources=[{'id':'guide:fixture','title':'Fictional source'}],message_id=1)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.gateway.app),base_url='http://fixture') as client:
            job=(await client.get('/api/jobs/j')).json();conversation=(await client.get('/api/conversations/c')).json()
            self.assertEqual(job['documentary'],conversation['messages'][0]['documentary'])
            self.assertEqual(job['documentary']['consulted_sources'][0]['id'],'guide:fixture')
            self.gateway.app.dependency_overrides[self.gateway.user]=lambda:{'id':'other'}
            for path in ('/api/jobs/j','/api/conversations/c'):
                response=await client.get(path);self.assertEqual(response.status_code,404);self.assertNotIn('guide:fixture',response.text)

    async def test_job_can_read_sanitized_numerical_fallback_without_optional_table(self):
        summary=documentary.Evidence().summary();summary.update(status='partial',searches=1)
        with store.connect() as db:db.execute('DROP TABLE documentary_evidence')
        durable.write_bytes(assistant_metrics.path('j'),json.dumps({'schema':1,'documentary':{**summary,'question':'PRIVATE'}}).encode(),private=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.gateway.app),base_url='http://fixture') as client:
            response=await client.get('/api/jobs/j');self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['documentary'],summary);self.assertNotIn('PRIVATE',response.text)


if __name__=='__main__':unittest.main()
