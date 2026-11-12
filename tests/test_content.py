import hashlib
import io
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

    def test_default_budget_is_500_decimal_gb(self):
        self.assertEqual(content.DEFAULT_BUDGET,500_000_000_000)

    def test_background_download_can_leave_services_untouched(self):
        import linux_lab as lab
        item={**self.item,'pack':'health'}
        with patch.object(sys,'argv',['content.py','download','--lab','--no-refresh','--pack','health']),patch.object(content,'catalog',return_value=[item]),patch.object(content,'download') as download,patch.object(content,'check_capacity'),patch.object(lab,'checked_mount'),patch.object(lab,'MOUNT',self.root),patch.object(lab,'podman') as podman:
            content.main()
            download.assert_called_once_with(self.root/'data',[item],budget=500_000_000_000,storage_root=self.root)
            podman.assert_not_called()


if __name__=='__main__':unittest.main()
