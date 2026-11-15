"""Real HTTP/store/guide fixtures. No model, production state or real documents."""
import unittest
from unittest.mock import AsyncMock,patch
import test_pilot_api as api_fixture
from pilot import engine,library,operations,store,translations


class AssociationAPITests(unittest.TestCase):
    setUp=api_fixture.PilotAPITests.setUp
    login=api_fixture.PilotAPITests.login
    headers={'Origin':'http://testserver'}

    def prepare(self):
        self.login();library.GUIDES.mkdir(exist_ok=True)
        for name in ('a','b','c'):(library.GUIDES/(name+'.en.txt')).write_text('Fictional notice '+name+'. No real instructions.')
        library.index_guides()

    def create(self,ids=('a','b')):
        response=self.client.post('/api/conversations',json={'source_ids':['guide:'+name+'.en.txt' for name in ids]},headers=self.headers)
        self.assertEqual(response.status_code,201,response.text)
        return response.json()['conversation_id']

    def selected(self,identifier):return self.client.get('/api/conversations/'+identifier).json()['selected_sources']

    def test_selection_is_durable_without_loading_or_requiring_a_model(self):
        self.prepare()
        with patch.object(operations,'status',side_effect=AssertionError('Selection must work while paused')),patch.object(engine,'launch') as launch:
            conversation=self.create();launch.assert_not_called()
            self.assertEqual([row['id'] for row in self.selected(conversation)],['guide:a.en.txt','guide:b.en.txt'])
            self.assertEqual(self.client.get('/api/conversations/'+conversation).json()['source']['id'],'guide:a.en.txt')
            self.assertEqual(self.client.delete('/api/conversations/'+conversation,headers=self.headers).status_code,200)
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM conversation_document_choices').fetchone()[0],0)
        self.assertTrue((library.GUIDES/'a.en.txt').exists())

    def test_omitted_and_legacy_primary_fields_keep_the_multiple_selection(self):
        self.prepare();conversation=self.create()
        with patch.object(engine,'launch') as launch:
            for fields in ({},{'source_id':'guide:a.en.txt'}):
                response=self.client.post('/api/questions',json={'message':'Compare ces notices fictives','conversation_id':conversation,**fields},headers=self.headers)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(launch.call_args.kwargs['source_ids'],['guide:a.en.txt','guide:b.en.txt'])
                with store.connect() as db:db.execute("UPDATE jobs SET status='done'")
        self.assertEqual(len(self.selected(conversation)),2)
        self.assertEqual(self.client.get('/api/conversations/'+conversation).json()['title'],'Compare ces notices fictives')

    def test_selection_changes_and_questions_cannot_overlap_an_active_answer(self):
        self.prepare();conversation=self.create()
        with patch.object(engine,'launch'):
            self.assertEqual(self.client.post('/api/questions',json={'message':'Première question','conversation_id':conversation},headers=self.headers).status_code,200)
            self.assertEqual(self.client.post('/api/questions',json={'message':'Question concurrente','conversation_id':conversation},headers=self.headers).status_code,409)
            self.assertEqual(self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':[]},headers=self.headers).status_code,409)
            self.assertEqual(self.client.put('/api/conversations/'+conversation+'/source',json={'source_id':None},headers=self.headers).status_code,409)
        self.assertEqual(len(self.selected(conversation)),2)
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM messages WHERE conversation_id=?',(conversation,)).fetchone()[0],1)

    def test_known_unavailable_selection_can_be_kept_or_removed_without_reading_it(self):
        self.prepare();conversation=self.create();(library.GUIDES/'b.en.txt').unlink()
        source=library.source
        with patch.object(library,'source',AsyncMock(side_effect=source)) as read:
            response=self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:a.en.txt','guide:b.en.txt','guide:c.en.txt']},headers=self.headers)
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual([call.args[0] for call in read.await_args_list],['guide:c.en.txt'])
            self.assertEqual(self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:a.en.txt']},headers=self.headers).status_code,200)
        self.assertEqual([row['id'] for row in self.selected(conversation)],['guide:a.en.txt'])

    def test_owner_is_checked_before_any_document_is_opened(self):
        self.prepare();conversation=self.create();self.login('bob')
        with patch.object(library,'source',AsyncMock()) as read:
            response=self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:c.en.txt']},headers=self.headers)
            self.assertEqual(response.status_code,404);read.assert_not_awaited()

    def test_invalid_new_documents_or_excessive_selection_preserve_existing_choices(self):
        self.prepare();conversation=self.create()
        self.assertEqual(self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:../private.txt']},headers=self.headers).status_code,404)
        self.assertEqual(self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['http://remote.invalid/']},headers=self.headers).status_code,422)
        self.assertEqual(self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:'+str(i) for i in range(13)]},headers=self.headers).status_code,422)
        self.assertEqual(len(self.selected(conversation)),2)
        response=self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:a.en.txt','guide:a.en.txt']},headers=self.headers)
        self.assertEqual(response.status_code,200,response.text);self.assertEqual(len(self.selected(conversation)),1)

    def test_legacy_edits_and_return_from_rollback_do_not_resurrect_old_choices(self):
        self.prepare();conversation=self.create()
        with store.connect() as db:db.execute('UPDATE conversation_sources SET source_id=?,title=? WHERE conversation_id=?',('guide:c.en.txt','Legacy choice',conversation))
        self.assertEqual([row['id'] for row in self.selected(conversation)],['guide:c.en.txt'])
        with store.connect() as db:db.execute('DELETE FROM conversation_sources WHERE conversation_id=?',(conversation,))
        self.assertEqual(self.selected(conversation),[])

    def test_optional_multi_table_failure_does_not_disable_the_single_association(self):
        self.prepare();conversation=self.create(('a',))
        with store.connect() as db:db.execute('DROP TABLE conversation_document_choices')
        response=self.client.put('/api/conversations/'+conversation+'/sources',json={'source_ids':['guide:a.en.txt','guide:b.en.txt']},headers=self.headers)
        self.assertEqual(response.status_code,503);self.assertEqual([row['id'] for row in self.selected(conversation)],['guide:a.en.txt'])
        response=self.client.put('/api/conversations/'+conversation+'/source',json={'source_id':'guide:c.en.txt'},headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(self.selected(conversation)[0]['id'],'guide:c.en.txt')

    def test_chat_without_selection_does_not_require_optional_association_module(self):
        self.prepare()
        from pilot import app as gateway
        original=gateway.importlib.import_module
        def importing(name,*args,**kwargs):
            if name=='.associations':raise ImportError('Fictional optional module failure')
            return original(name,*args,**kwargs)
        with patch.object(gateway.importlib,'import_module',side_effect=importing),patch.object(engine,'launch'):
            response=self.client.post('/api/questions',json={'message':'Question sans document associé','source_ids':[]},headers=self.headers)
        self.assertEqual(response.status_code,200,response.text)

    def test_pause_remains_effective_even_if_online_status_has_not_caught_up(self):
        self.prepare()
        with patch.object(operations,'status',AsyncMock(return_value={'paused':True,'online':True,'message':'Pause fictive'})),patch.object(engine,'launch') as launch:
            response=self.client.post('/api/questions',json={'message':'Question pendant pause','source_ids':[]},headers=self.headers)
        self.assertEqual(response.status_code,503);launch.assert_not_called()

    def test_starting_translation_selects_its_source_and_retains_the_other_documents(self):
        self.prepare();conversation=self.create()
        with patch.object(translations,'launch'):
            response=self.client.post('/api/translations',json={'source_id':'guide:b.en.txt','conversation_id':conversation},headers=self.headers)
        self.assertEqual(response.status_code,202,response.text)
        self.assertEqual([row['id'] for row in self.selected(conversation)],['guide:b.en.txt','guide:a.en.txt'])


if __name__=='__main__':unittest.main()
