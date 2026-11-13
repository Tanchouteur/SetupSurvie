import hashlib
import shutil
from collections import namedtuple
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import content
import content_retry
import setup


class SupervisedDownloadTests(unittest.TestCase):
    def setUp(self):
        # Supervision fixtures are bytes, not a real production disk reservation.
        usage=namedtuple('Usage','total used free')(200_000_000_000,100_000_000_000,100_000_000_000)
        disk=patch.object(shutil,'disk_usage',return_value=usage);disk.start();self.addCleanup(disk.stop)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.items = [dict(id=name, title=name, path='library/guides/'+name+'.txt',
            url='https://example.org/'+name, bytes=3, sha256=hashlib.sha256(b'abc').hexdigest()) for name in ('a', 'b')]

    def publish(self, item):
        path = content.destination(self.root, item['path'])
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'abc')
        receipt = self.root/'catalog/downloaded-content.json'
        items = content.catalog(receipt) if receipt.exists() else []
        setup.write_json(receipt, {'schema': 1, 'items': [i for i in items if i['id'] != item['id']]+[item]})

    def test_verified_receipts_are_reused_without_network_or_large_hash_scan(self):
        for item in self.items: self.publish(item)
        download = Mock(side_effect=AssertionError('No download or scan needed'))
        self.assertTrue(content_retry.supervise(self.root, self.items, download=download, max_rounds=1))
        download.assert_not_called()

    def test_error_does_not_block_other_items_and_is_retried(self):
        calls = []
        def download(root, items, **kwargs):
            item = items[0]; calls.append(item['id'])
            if calls == ['a']: raise OSError('temporary network failure')
            self.publish(item)
        self.assertTrue(content_retry.supervise(self.root, self.items, download=download, retry_delay=0, max_rounds=2))
        self.assertEqual(calls, ['a', 'b', 'a'])
        self.assertEqual(content_retry.remaining(self.root, self.items), [])

    def test_certificate_error_uses_native_verified_probe_then_retries(self):
        count = 0
        def download(root, items, **kwargs):
            nonlocal count
            count += 1
            if count == 1: raise urllib.error.URLError('CERTIFICATE_VERIFY_FAILED')
            self.publish(items[0])
        trust = Mock(return_value=True)
        self.assertTrue(content_retry.supervise(self.root, self.items[:1], download=download, trust_refresh=trust, max_rounds=1))
        trust.assert_called_once_with(self.items[0]['url'])

    def test_exhausted_retries_leave_partial_and_report_incomplete(self):
        partial = content.destination(self.root, self.items[0]['path']+'.part')
        partial.parent.mkdir(parents=True); partial.write_bytes(b'a')
        self.assertFalse(content_retry.supervise(self.root, self.items[:1], download=Mock(side_effect=OSError('offline')), max_rounds=1))
        self.assertEqual(partial.read_bytes(), b'a')
        status = json.loads((self.root/'catalog/content-retry.json').read_text())
        self.assertEqual(status['status'], 'incomplete')
        self.assertEqual(status['pending'], ['a'])

    def test_changed_receipt_or_missing_file_is_not_treated_as_verified(self):
        self.publish(self.items[0])
        altered = dict(self.items[0], sha256='f'*64)
        self.assertEqual(content_retry.remaining(self.root, [altered]), [altered])
        (self.root/self.items[0]['path']).unlink()
        self.assertEqual(content_retry.remaining(self.root, self.items[:1]), self.items[:1])

    def test_parallel_supervisor_retries_only_failed_files(self):
        calls=[]
        def download(root,items,**kwargs):
            calls.append([i['id'] for i in items])
            self.assertEqual(kwargs['workers'],2)
            self.assertTrue(kwargs['continue_on_error'])
            results=[]
            for item in items:
                if len(calls)==1 and item['id']=='a':
                    results.append({'id':'a','status':'failed','error':'offline'})
                else:
                    self.publish(item);results.append({'id':item['id'],'status':'downloaded'})
            return results
        self.assertTrue(content_retry.supervise(self.root,self.items,download=download,workers=2,retry_delay=0,max_rounds=2))
        self.assertEqual(calls,[['a','b'],['a']])

    def test_native_probe_keeps_https_and_hides_its_console(self):
        curl = self.root/'System32/curl.exe'; curl.parent.mkdir(); curl.write_bytes(b'fixture')
        native = SimpleNamespace(name='nt', environ={'SystemRoot': str(self.root)})
        runner = Mock(return_value=SimpleNamespace(returncode=0))
        process = SimpleNamespace(run=runner, CREATE_NO_WINDOW=0x08000000)
        with patch.object(content_retry, 'os', native), patch.object(content_retry, 'subprocess', process):
            self.assertTrue(content_retry.refresh_windows_trust('https://example.org/guide'))
        command = runner.call_args.args[0]
        self.assertNotIn('--insecure', command); self.assertNotIn('-k', command)
        self.assertIn('--proto-redir', command); self.assertIn('=https', command)
        self.assertEqual(runner.call_args.kwargs['creationflags'], 0x08000000)
