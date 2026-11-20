"""Durable verified download events and automatic coordinator; tiny local data."""
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,search_index_queue as queue,library_tasks,discovery


class SearchIndexQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.app=setup.Installation(self.root/'private');self.config=self.app.init('linux',self.root/'data',cpu=True)
        self.data=Path(self.config['data_dir']);self.file=self.data/'library/zim/sample.zim';self.file.write_bytes(b'tiny fixture')
        self.item={'path':'library/zim/sample.zim','sha256':'a'*64}
        self.manager=library_tasks.Manager(self.app,self.config,'compose')

    def test_only_verified_archive_event_enters_queue_and_ack_is_conditional(self):
        queue.enqueue(self.data,{'path':'library/guides/not-zim.pdf'})
        self.assertEqual(queue.summary(self.data)['pending'],0)
        queue.enqueue(self.data,self.item);selection=queue.read(self.data)['pending']
        queue.enqueue(self.data,self.item);self.assertEqual(selection,queue.read(self.data)['pending'])
        queue.acknowledge(self.data,selection,{'results':[{'archive':'sample.zim','status':'kiwix_index'}]})
        self.assertEqual(queue.summary(self.data)['pending'],0)
        queue.enqueue(self.data,self.item);self.assertEqual(queue.summary(self.data)['pending'],0)
        queue.enqueue(self.data,{**self.item,'sha256':'b'*64});self.assertEqual(queue.summary(self.data)['pending'],1)
        queue.acknowledge(self.data,selection,{'results':[{'archive':'sample.zim','status':'kiwix_index'}]})
        self.assertEqual(queue.summary(self.data)['pending'],1,'Older run cannot acknowledge a newer event')

    def test_restart_preserves_queue_and_user_pause(self):
        queue.enqueue(self.data,self.item);queue.hold(self.data,'user')
        self.assertEqual(queue.read(self.data)['hold'],'user')
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start') as start:
            self.manager.auto_index();start.assert_not_called()

    def test_auto_starts_after_managed_job_finishes_without_starting_ai(self):
        queue.enqueue(self.data,self.item)
        setup.write_json(self.app.work/'inference-paused.json',{'reason':'user_pause'})
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start') as start:
            self.manager.auto_index();start.assert_called_once_with('index',{'automatic':True})
        setup.write_json(self.app.work/'inference-paused.json',{'reason':'user_gaming'})
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start') as start:
            self.manager.auto_index();start.assert_not_called()

    def test_auto_does_not_replace_a_selection_waiting_for_download(self):
        queue.enqueue(self.data,self.item);self.manager.write({'phase':'planned','id':'b'*32})
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start') as start:
            self.manager.auto_index();start.assert_not_called()

    def test_missing_tool_and_storage_deferral_are_visible_without_raw_errors(self):
        queue.enqueue(self.data,self.item)
        self.assertEqual(self.manager.status()['index_queue']['waiting_reason'],'missing_reader')
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start',side_effect=setup.SetupError('Marge de stockage insuffisante /private/path')):
            self.manager.auto_index();status=self.manager.status()
        self.assertEqual(status['index_queue']['waiting_reason'],'insufficient_storage')
        self.assertNotIn('/private/path',json.dumps(status))

    def test_changed_archive_is_not_automatically_indexed_as_previously_verified(self):
        queue.enqueue(self.data,self.item);selection=queue.read(self.data)['pending']
        self.file.write_bytes(b'new unverified content')
        with self.assertRaises(queue.SourceChanged):queue.validate_selection(self.data,selection)
        self.assertEqual(queue.read(self.data)['hold'],'source_changed')
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(self.manager,'start') as start:
            self.manager.auto_index();start.assert_not_called()
        queue.enqueue(self.data,{**self.item,'sha256':'b'*64})
        self.assertEqual(queue.read(self.data)['hold'],'')
        queue.validate_selection(self.data,queue.read(self.data)['pending'])

    def test_category_job_restarts_in_the_window_only_after_automatic_pause(self):
        state = {'phase': 'paused', 'action': 'category-index', 'id': 'b'*32,
                 'options': {'automatic': True}}
        self.manager.write(state)
        folder = self.manager.paths(state['id'])
        folder.mkdir(parents=True, exist_ok=True)
        report = self.data/'state/pilot/category-index/progress.json'
        setup.write_json(report, {'phase': 'paused'})
        with patch.object(self.manager, 'index_ready', return_value=True), patch.object(self.manager, 'start') as start:
            self.manager.auto_index()
            start.assert_not_called()
            (folder/'auto-pause').touch()
            with patch.object(queue, 'in_window', return_value=False):
                self.manager.auto_index()
            start.assert_not_called()
            self.manager.auto_index()
            start.assert_called_once_with('category-index', {'automatic': True})

    def test_returned_archive_is_eligible_at_the_next_automatic_run(self):
        self.manager.write({'phase': 'completed', 'action': 'category-index', 'id': 'b'*32})
        archive_key = library_tasks.collection_sort.archive(self.file.name)
        sorting = library_tasks.collection_sort.Sort().change([archive_key], 'other')
        library_tasks.collection_sort.save(self.data/'catalog', sorting)
        with patch.object(self.manager, 'index_ready', return_value=True), patch.object(self.manager, 'start') as start:
            self.manager.auto_index()
            start.assert_not_called()
            library_tasks.collection_sort.save(self.data/'catalog', library_tasks.collection_sort.Sort())
            self.manager.auto_index()
            start.assert_called_once_with('category-index', {'automatic': True})

    def test_window_handles_midnight_and_settings_reject_unknown_values(self):
        opts={'start_hour':22,'end_hour':6}
        for hour,expected in [(21,False),(22,True),(0,True),(5,True),(6,False)]:
            self.assertEqual(queue.in_window(opts,datetime(2026,1,1,hour)),expected)
        for body in [{'workers':17},{'workers':True},{'start_hour':24},{'command':'anything'}]:
            with self.assertRaises(setup.SetupError):queue.settings(self.data,body)

    def test_interrupted_parent_does_not_overlook_a_live_index_child(self):
        state={'phase':'downloading','action':'index','pid':999999999,'identity':'not-live','index_pid':os.getpid(),'index_identity':discovery.identity(os.getpid())}
        self.manager.write(state);self.assertEqual(self.manager.current()['phase'],'downloading')
        state['index_pid']=999999998;self.manager.write(state)
        self.assertEqual(self.manager.current()['phase'],'interrupted');self.assertEqual(queue.read(self.data)['hold'],'interrupted')

    def test_finished_probe_failure_is_recovered_without_retaining_a_ready_marker(self):
        state={'id':'e'*32,'phase':'downloading','action':'index','options':{},'pid':999999999,'identity':'not-live','index_pid':999999998,'index_identity':'not-live'}
        marker=self.app.work/'search-tools/reader-ready.json';setup.write_json(marker,{'libzim':'3.13.1'})
        self.manager.write(state)
        setup.write_json(self.data/'state/pilot/archive-index/progress.json',{'job_id':state['id'],'phase':'partial','reader_probe':{'schema':1,'ok':False,'error':'fts5_unavailable'},'results':[]})
        value=self.manager.current();self.assertEqual(value['phase'],'error');self.assertIn('SQLite',value['message']);self.assertFalse(marker.exists())
        self.assertEqual(self.manager.status()['reader_probe']['error'],'fts5_unavailable')
