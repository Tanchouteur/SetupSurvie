import hashlib
import io
from contextlib import redirect_stderr
import json
from pathlib import Path
import sys
import tempfile
import unittest
from collections import namedtuple
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import content
import setup


class Response(io.BytesIO):
    def __init__(self,body,status=200,headers=None):
        super().__init__(body);self.status=status;self.headers=headers or {}
    def geturl(self):return 'https://example.org/book.pdf'


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.raw=b'%PDF-document-content'
        self.item={'id':'book','path':'library/guides/book.pdf','url':'https://example.org/book.pdf','bytes':len(self.raw),'sha256':hashlib.sha256(self.raw).hexdigest()}

    def test_initial_download_rejects_a_saved_plan_with_english_wikipedia(self):
        plan = self.root / 'initial-library-plan.json'
        for name in ('wikipedia_en_all_nopic_2026-06.zim', 'wikipedia_en-simple_all_maxi_2026-09.zim'):
            with self.subTest(name=name):
                item = {**self.item, 'path': 'library/zim/' + name, 'pack': 'kiwix-themes'}
                setup.write_json(plan, {'schema': 1, 'kind': 'SetupSurvie Kiwix thematic selection', 'items': [item]})
                args = ['content.py', 'download', '--data-dir', str(self.root), '--selection', str(plan)]
                with patch.object(content, 'download_and_refresh') as download, redirect_stderr(io.StringIO()) as err:
                    with patch.object(sys, 'argv', args + ['--initial-installation']), self.assertRaises(SystemExit) as stopped:
                        content.main()
                    self.assertEqual(stopped.exception.code, 2)
                    self.assertIn('édition anglaise de Wikipédia', err.getvalue())
                    download.assert_not_called()
                    with patch.object(sys, 'argv', args):
                        content.main()
                    self.assertEqual(download.call_args.args[4], [item])
    def test_verified_zim_download_enqueues_indexing_but_bad_hash_does_not(self):
        import search_index_queue
        item={**self.item,'path':'library/zim/book.zim','title':'Tiny fixture'}
        from unittest.mock import patch
        import content_mirrors
        with patch.object(content_mirrors,'network_open',return_value=Response(self.raw)):
            content.download(self.root,[item],reserve=0)
        self.assertEqual(search_index_queue.summary(self.root)['pending'],1)
        bad={**item,'path':'library/zim/bad.zim','id':'bad','sha256':'0'*64}
        with patch.object(content_mirrors,'network_open',return_value=Response(self.raw)):
            with self.assertRaises(setup.SetupError):content.download(self.root,[bad],reserve=0)
        self.assertEqual(search_index_queue.summary(self.root)['pending'],1)

    def test_resume_verified_file_and_idempotent_repeat(self):
        part=content.destination(self.root,self.item['path']+'.part');part.parent.mkdir(parents=True);part.write_bytes(self.raw[:5])
        def opener(req,**kwargs):
            self.assertEqual(req.headers['Range'],'bytes=5-')
            return Response(self.raw[5:],206,{'Content-Range':f'bytes 5-{len(self.raw)-1}/{len(self.raw)}'})
        self.assertEqual(content.transfer(self.root,self.item,opener),'downloaded')
        self.assertFalse(part.exists())
        self.assertEqual(content.transfer(self.root,self.item,lambda *_:self.fail('Must not download twice')),'present')
    def test_server_ignoring_range_restarts_without_duplicating(self):
        part=content.destination(self.root,self.item['path']+'.part');part.parent.mkdir(parents=True);part.write_bytes(self.raw[:5])
        content.transfer(self.root,self.item,lambda *a,**k:Response(self.raw))
        self.assertEqual((self.root/self.item['path']).read_bytes(),self.raw)
    def test_ignored_range_with_short_or_changed_prefix_preserves_partial(self):
        part=content.destination(self.root,self.item['path']+'.part');part.parent.mkdir(parents=True)
        before=self.raw[:10]
        for response in (self.raw[:3],b'wrong-prefix',self.raw[:12]):
            part.write_bytes(before)
            with self.assertRaises(setup.SetupError):
                content.transfer(self.root,self.item,lambda *a,**k:Response(response))
            self.assertTrue(part.read_bytes().startswith(before))
            self.assertGreaterEqual(part.stat().st_size,len(before))
            self.assertFalse((self.root/self.item['path']).exists())

    def test_bad_range_hash_oversize_and_truncated_never_published(self):
        for body,status,headers in [(self.raw,206,{'Content-Range':'bytes 1-3/4'}),(self.raw[:-1]+b'x',200,{}),(self.raw+b'x',200,{}),(self.raw[:2],200,{})]:
            with self.subTest(status=status,body=body):
                part=content.destination(self.root,self.item['path']+'.part');part.unlink(missing_ok=True)
                with self.assertRaises(setup.SetupError):content.transfer(self.root,self.item,lambda *a,**k:Response(body,status,headers))
                self.assertFalse((self.root/self.item['path']).exists())
    def test_paths_and_symlink_parents_rejected(self):
        for path in ('../private','/tmp/a','C:/private','library/../private','library\\guides\\a','library//a','library/a.'):
            with self.assertRaises(setup.SetupError):content.destination(self.root,path)
        try:(self.root/'library').symlink_to(self.root.parent,target_is_directory=True)
        except OSError:self.skipTest('Création de lien non autorisée sur ce système.')
        with self.assertRaises(setup.SetupError):content.destination(self.root,'library/secret')
    def test_existing_unknown_file_preserved(self):
        path=content.destination(self.root,self.item['path']);path.parent.mkdir(parents=True);path.write_bytes(b'user-data')
        with self.assertRaises(setup.SetupError):content.transfer(self.root,self.item)
        self.assertEqual(path.read_bytes(),b'user-data')

    def test_pause_during_integrity_check_preserves_unpublished_partial(self):
        checks=0
        def cancelled():
            nonlocal checks
            checks+=1
            return checks>=5
        with self.assertRaises(content.DownloadPaused):
            content.transfer(self.root,self.item,lambda *a,**k:Response(self.raw),cancelled=cancelled)
        self.assertFalse((self.root/self.item['path']).exists())
        self.assertEqual((self.root/(self.item['path']+'.part')).read_bytes(),self.raw)
    def test_budget_rejected_before_network_and_lock_released(self):
        with patch.object(content,'transfer') as transfer:
            with self.assertRaises(setup.SetupError):content.download(self.root,[self.item],budget=1,reserve=0)
            transfer.assert_not_called()
        self.assertFalse((self.root/'catalog/content.lock').exists())

    def test_documents_exclude_models_caches_and_kit_but_disk_keeps_reserve(self):
        data=self.root/'data';data.mkdir()
        (data/'library').mkdir();(data/'library/book.pdf').write_bytes(b'x'*20)
        (data/'models').mkdir();(data/'models/model').write_bytes(b'x'*100)
        (self.root/'kit').write_bytes(b'x'*100)
        usage=namedtuple('Usage','total used free')
        with patch.object(Path,'is_mount',return_value=True),patch.object(content.shutil,'disk_usage',return_value=usage(590,480,110)):
            with self.assertRaises(setup.SetupError):
                content.check_capacity(data,81,budget=100,reserve=15,storage_root=self.root)
            self.assertEqual(content.check_capacity(data,80,budget=100,reserve=15,storage_root=self.root),20)
            with self.assertRaises(setup.SetupError):
                content.check_capacity(data,1,budget=100,reserve=110,storage_root=self.root)

    def test_absent_mount_rejected_before_network(self):
        with patch.object(Path,'is_mount',return_value=False),patch.object(content,'transfer') as transfer:
            with self.assertRaises(setup.SetupError):
                content.download(self.root,[self.item],storage_root=self.root)
            transfer.assert_not_called()

    def test_runtime_budget_stop_preserves_partial_and_never_publishes(self):
        def guard(count):raise setup.SetupError('Budget changé pendant le transfert')
        with self.assertRaises(setup.SetupError):
            content.transfer(self.root,self.item,lambda *a,**k:Response(self.raw),before_write=guard)
        self.assertFalse((self.root/self.item['path']).exists())
        self.assertEqual((self.root/(self.item['path']+'.part')).stat().st_size,0)

    def test_loop_capacity_counts_the_real_ssd_space(self):
        backing = self.root/'storage.img'
        backing.touch()
        usage = namedtuple('Usage', 'total used free')
        read_text = Path.read_text

        def sysfs(path, *args, **kwargs):
            if Path(path).as_posix().endswith('/loop/backing_file'):
                return str(backing)+'\n'
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'is_mount', return_value=True), \
                patch.object(content.sys, 'platform', 'linux'), \
                patch.object(content.os, 'major', create=True, return_value=7), \
                patch.object(content.os, 'minor', create=True, return_value=0), \
                patch.object(Path, 'read_text', sysfs), \
                patch.object(content.shutil, 'disk_usage', side_effect=[usage(900, 10, 890), usage(900, 890, 10)]):
            with self.assertRaises(setup.SetupError):
                content.check_capacity(self.root, 5, reserve=6, storage_root=self.root)

    def test_metadata_distinguishes_edition_from_collection_and_keeps_unknown_old_collection_unknown(self):
        item={**self.item,'title':'Notice','language':'fr','publisher':'Fixture','edition':'2010','licence':'Test'}
        with patch.object(content,'check_capacity'),patch.object(content,'transfer',return_value='downloaded'):
            content.download(self.root,[item],reserve=0)
        path=self.root/'library/guides/metadata.json'
        first=json.loads(path.read_text())[0]
        self.assertEqual(first['edition'],'2010');self.assertEqual(first['document_date'],'')
        self.assertRegex(first['collected_at'],r'^\d{4}-\d{2}-\d{2}$')
        with patch.object(content,'check_capacity'),patch.object(content,'transfer',return_value='present'):
            content.download(self.root,[item],reserve=0)
        self.assertEqual(json.loads(path.read_text())[0]['collected_at'],first['collected_at'])
        first.pop('collected_at');path.write_text(json.dumps([first]))
        with patch.object(content,'check_capacity'),patch.object(content,'transfer',return_value='present'):
            content.download(self.root,[item],reserve=0)
        self.assertEqual(json.loads(path.read_text())[0]['collected_at'],'')

    def test_background_download_can_leave_services_untouched(self):
        import linux_lab as lab
        item={**self.item,'pack':'health'}
        with patch.object(sys,'argv',['content.py','download','--lab','--no-refresh','--pack','health']),patch.object(content,'catalog',return_value=[item]),patch.object(content,'download') as download,patch.object(content,'check_capacity'),patch.object(lab,'checked_mount'),patch.object(lab,'MOUNT',self.root),patch.object(lab,'podman') as podman:
            content.main()
            # Windows temporary paths may use an 8.3 alias resolved by safe_path.
            download.assert_called_once_with((self.root/'data').resolve(),[item],budget=None,storage_root=self.root,workers=2)
            podman.assert_not_called()


    def test_lab_download_refreshes_only_library_services(self):
        import linux_lab as lab
        item={**self.item,'pack':'health'}
        installation=type('Installation',(),{'__init__':lambda self,root:None,'load':lambda self:{},'catalog':lambda self,c:None})
        with patch.object(sys,'argv',['content.py','download','--lab','--pack','health']),patch.object(content,'catalog',return_value=[item]),patch.object(content,'download'),patch.object(content,'check_capacity'),patch.object(content,'install_templates'),patch.object(lab,'checked_mount'),patch.object(lab,'MOUNT',self.root),patch.object(lab.setup,'Installation',installation),patch.object(lab,'podman') as podman:
            content.main()
        podman.assert_called_once_with('restart',lab.PREFIX+'kiwix',lab.PREFIX+'pilot',capture=True)

if __name__=='__main__':unittest.main()
