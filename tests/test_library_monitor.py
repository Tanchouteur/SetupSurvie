"""Tiny, read-only fixtures; no database, archive hashing, worker or network."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import library_monitor as monitor


class LibraryMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'data';self.work=Path(self.temp.name)/'private'
        self.root.mkdir();self.work.mkdir()
        self.item={'id':'garden','path':'library/zim/garden.zim','title':'Jardin','bytes':6,'sha256':hashlib.sha256(b'abcdef').hexdigest()}
        self.identity={'path':'pythonw.exe','created':'123'}
        self.write(self.root/'catalog/plan.json',{'items':[self.item]})
        self.write(self.root/'diagnostics/bibliotheque-transfer.json',{'pid':123,'identity':self.identity,'plan':str(self.root/'catalog/plan.json'),'started':time.time()-10,'log':'SECRET'})
        self.write(self.root/'catalog/content-progress.json',{'active':[{'id':'garden','bytes':0,'total':6}]})
        current=patch.object(monitor.discovery,'identity',return_value=self.identity);current.start();self.addCleanup(current.stop)

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

    def result(self):return monitor.snapshot(self.root,self.work)

    def test_index_activity_tracks_live_child_and_does_not_report_it_as_download(self):
        (self.root/'diagnostics/bibliotheque-transfer.json').unlink()
        self.write(self.work/'library-web/state.json',{'id':'a'*32,'action':'index','phase':'downloading','pid':101,'identity':{'path':'old','created':'0'},'index_pid':202,'index_identity':self.identity})
        self.write(self.root/'state/pilot/archive-index/progress.json',{'archives':3,'completed':2,'articles':40,'results':[{'error':'SECRET'}]})
        value=self.result();self.assertEqual(value['phase'],'indexing');self.assertTrue(value['worker_alive']);self.assertEqual(value['index_progress']['articles'],40)
        self.assertNotIn('SECRET',json.dumps(value))
        self.write(self.work/'library-web/state.json',{'id':'b'*32,'action':'index-prepare','phase':'downloading','pid':202,'identity':self.identity})
        self.assertEqual(self.result()['phase'],'index_preparation')

    def test_shared_size_reads_a_tiny_file_while_its_writer_is_open(self):
        path=self.root/'tiny.part'
        with path.open('wb') as writer:
            writer.write(b'abc');writer.flush()
            self.assertEqual(monitor.shared_size(path),3)

    def test_shared_handle_size_corrects_lagging_directory_and_redacts_private_metadata(self):
        with patch.object(monitor,'shared_size',return_value=4):value=self.result()
        self.assertEqual(value['active'][0]['bytes'],4);self.assertEqual(value['phase'],'downloading')
        raw=json.dumps(value);self.assertNotIn(str(self.root),raw);self.assertNotIn('SECRET',raw);self.assertNotIn('pid',raw)
        self.assertFalse(value['commands'])

    def test_full_partial_is_verifying_not_available(self):
        with patch.object(monitor,'shared_size',return_value=6):value=self.result()
        self.assertEqual(value['phase'],'verifying');self.assertEqual(value['verified_bytes'],0)

    def test_receipt_requires_same_path_hash_size_and_deduplicates(self):
        self.write(self.root/'catalog/downloaded-content.json',{'items':[dict(self.item,sha256='f'*64)]})
        self.assertEqual(self.result()['verified_count'],0)
        self.write(self.root/'catalog/downloaded-content.json',{'items':[self.item,self.item]})
        value=self.result();self.assertEqual(value['verified_count'],1);self.assertEqual(value['phase'],'verified')

    def test_pid_reuse_and_unknown_identity_never_claim_live_transfer(self):
        with patch.object(monitor.discovery,'identity',return_value={'path':'other','created':'456'}):
            value=self.result();self.assertEqual(value['phase'],'interrupted');self.assertEqual(value['active'],[])
        with patch.object(monitor.discovery,'identity',return_value=None),patch('delivery_paths.process_alive',return_value=True):
            self.assertEqual(self.result()['phase'],'unknown')

    def test_progress_before_worker_and_unrelated_item_are_ignored(self):
        path=self.root/'catalog/content-progress.json';os.utime(path,(1,1))
        self.assertEqual(self.result()['active'],[]);self.assertTrue(self.result()['stale'])
        self.write(path,{'active':[{'id':'other','bytes':100,'total':100}]})
        self.assertEqual(self.result()['active'],[])

    def test_waiting_retry_is_bound_to_current_owner_and_hides_errors(self):
        self.write(self.root/'catalog/content-progress.json',{'status':'waiting_retry'})
        self.write(self.root/'catalog/content-retry.json',{'pid':123,'next_retry_at':12345,'failed':{'garden':{'error':'SECRET'},'other':{}}})
        value=self.result();self.assertEqual(value['phase'],'waiting_retry');self.assertEqual(value['pending_errors'],1)
        self.assertNotIn('SECRET',json.dumps(value))

    def test_old_retry_errors_do_not_hide_a_plan_now_fully_verified(self):
        self.write(self.root/'catalog/downloaded-content.json',{'items':[self.item]})
        self.write(self.root/'catalog/content-retry.json',{'pid':123,'failed':{'garden':{'error':'old 404'}}})
        value=self.result();self.assertEqual(value['phase'],'verified');self.assertEqual(value['pending_errors'],0)

    def test_malformed_or_external_plan_fails_without_reading_external_file(self):
        self.write(self.root/'diagnostics/bibliotheque-transfer.json',{'pid':123,'identity':self.identity,'plan':'/not-authorized/secret'})
        value=self.result();self.assertEqual(value['phase'],'unknown');self.assertNotIn('/not-authorized',json.dumps(value))

    def test_no_state_is_idle_and_reads_do_not_write_or_acquire_locks(self):
        (self.root/'diagnostics/bibliotheque-transfer.json').unlink()
        before=sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        self.assertEqual(self.result()['phase'],'idle')
        self.assertEqual(before,sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))

    def test_web_job_and_independent_transfer_have_consistent_totals(self):
        (self.root/'diagnostics/bibliotheque-transfer.json').unlink()
        job='a'*32
        self.write(self.work/'library-web/state.json',{'id':job,'action':'download','phase':'downloading','pid':123,'identity':self.identity,'started_at':time.time()-10})
        self.write(self.work/'library-web'/job/'plan.json',{'items':[self.item]})
        value=self.result();self.assertEqual(value['source'],'web');self.assertEqual(value['total_bytes'],6)

    def test_web_geography_has_no_private_coordinates(self):
        (self.root/'diagnostics/bibliotheque-transfer.json').unlink()
        self.write(self.work/'library-web/state.json',{'id':'a'*32,'action':'geography','phase':'downloading','pid':123,'identity':self.identity,'options':{'lat':43.12}})
        value=self.result();self.assertEqual(value['kind'],'geography');self.assertNotIn('lat',json.dumps(value))
