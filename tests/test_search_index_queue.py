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
