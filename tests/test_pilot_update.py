import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
import pilot_update as update


class Services:
    def __init__(self,app,c,fail=False):self.app,self.c,self.fail=app,c,fail;self.starts=0;self.stops=0
    def stop(self):self.stops+=1
    def start(self):
        self.starts+=1
        if self.starts==1:
            # Simulate startup modifying the DB before a failed health check.
            (Path(self.c['data_dir'])/'state/pilot/pilot.db').write_bytes(b'migrated')
    def check(self,version):
        if self.fail and self.starts==1:raise setup.SetupError('Unhealthy new service')


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
        self.source=self.base/'source';self.root=self.base/'installed';self.data=self.base/'data';self.work=self.base/'private'
        self.source.mkdir();self.root.mkdir()
        for base,version in [(self.source,'0.1.2'),(self.root,'0.1.1')]:
            for name in ('scripts','pilot','portal','deploy'):(base/name).mkdir()
            for path in ('scripts/setup.py','scripts/pilot_update.py','compose.yaml','pilot/app.py','portal/index.html'):(base/path).write_text('version '+version)
            (base/'pilot/app.py').write_text("VERSION='"+version+"'\n")
            (base/'deploy/release.json').write_text(json.dumps({'version':version,'data_schema':1}))
            for name in ('versions.json','discovery-packages.json'):(base/'deploy'/name).write_text('{}')
        with patch.object(setup,'ROOT',self.source):
            self.package=self.base/'update.zip';self.digest=update.build(self.package)
        with patch.object(setup,'ROOT',self.root):
            self.app=setup.Installation(self.work);self.c=self.app.init('linux',self.data,cpu=True)
        self.c['app_dir']=str(self.root);setup.write_json(self.app.settings_path,self.c,private=True)
        for path,body in [('state/pilot/pilot.db',b'old-db'),('state/openwebui/webui.db',b'accounts-and-history'),('models/blob',b'large-model-sentinel'),('library/zim/book.zim',b'archive-sentinel'),('state/openwebui/cache/file',b'cache-sentinel')]:
            target=self.data/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        (self.work/'inference-paused.json').write_text('{"reason":"user_gaming"}')
    def run_update(self,fail=False):
        service=Services(self.app,self.c,fail)
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'):
            result=update.apply(self.app,self.package,self.digest,service)
        return result,service
    def assert_static_data(self):
        self.assertEqual((self.data/'models/blob').read_bytes(),b'large-model-sentinel')
        self.assertEqual((self.data/'library/zim/book.zim').read_bytes(),b'archive-sentinel')
        self.assertEqual((self.data/'state/openwebui/webui.db').read_bytes(),b'accounts-and-history')
        self.assertEqual((self.data/'state/openwebui/cache/file').read_bytes(),b'cache-sentinel')
        self.assertTrue((self.work/'inference-paused.json').exists())
    def test_update_changes_code_and_preserves_accounts_models_and_pause(self):
        result,service=self.run_update()
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.2')
        self.assertTrue((result/'previous/portal/index.html').is_file());self.assert_static_data()
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'complete')
        self.assertFalse((self.work/'update.lock').exists())

    def test_first_install_wrappers_do_not_break_legacy_update_allowlist(self):
        for name in ('Mettre-a-jour-SetupSurvie.cmd','Installer-SetupSurvie.cmd','1-Preparer-le-PC.cmd','2-Installer-SetupSurvie.cmd'):
            (self.source/name).write_text('first install fixture')
        (self.source/'scripts/install-windows.ps1').write_text('installer implementation fixture')
        with patch.object(setup,'ROOT',self.source):
            package=self.base/'with-installers.zip';digest=update.build(package)
        legacy_files=('README.md','AGENTS.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml')
        with patch.object(update,'FILES',legacy_files):
            manifest=update.unpack(package,digest,self.base/'legacy-unpacked')
        names={entry['path'] for entry in manifest['files']}
        self.assertNotIn('Installer-SetupSurvie.cmd',names)
        self.assertNotIn('Mettre-a-jour-SetupSurvie.cmd',names)
        self.assertNotIn('1-Preparer-le-PC.cmd',names)
        self.assertIn('scripts/install-windows.ps1',names)
    def test_failed_health_restores_previous_code_and_database(self):
        with self.assertRaises(setup.SetupError):self.run_update(fail=True)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assert_static_data()
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'rolled_back')
    def test_untrusted_archive_or_traversal_rejected_before_service_stop(self):
        with self.assertRaises(setup.SetupError):update.unpack(self.package,'0'*64,self.base/'staged')
        with zipfile.ZipFile(self.package,'a') as archive:archive.writestr('app/../../secret',b'bad')
        with self.assertRaises(setup.SetupError):update.unpack(self.package,setup.file_hash(self.package),self.base/'staged')
        self.assertFalse((self.base/'secret').exists())
    def test_dependency_change_rejected_without_stopping_service(self):
        (self.root/'deploy/versions.json').write_text('{"different":true}');service=Services(self.app,self.c)
        with patch.object(setup,'ROOT',self.root),self.assertRaises(setup.SetupError):update.apply(self.app,self.package,self.digest,service)
        self.assertEqual(service.stops,0);self.assert_static_data()
    def test_development_checkout_and_repeat_refused(self):
        (self.root/'.git').mkdir()
        with self.assertRaises(setup.SetupError),patch.object(setup,'ROOT',self.root):update.apply(self.app,self.package,self.digest)
        (self.root/'.git').rmdir();self.run_update()
        with self.assertRaises(setup.SetupError):self.run_update()
    def test_finished_update_recovery_never_reverts_new_user_data(self):
        self.run_update();(self.data/'state/pilot/pilot.db').write_bytes(b'new-conversation')
        with self.assertRaises(setup.SetupError):update.recover(self.app,self.work/'update.json',Services(self.app,self.c))
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'new-conversation')
    def test_power_cut_after_code_rename_is_recoverable_from_saved_copy(self):
        operation,service=self.run_update()
        j=json.loads((self.work/'update.json').read_text());j['phase']='switched'
        setup.write_json(self.work/'update.json',j,private=True)
        # Recovery after a power cut uses the script in updates/<id>/previous.
        with patch.object(setup,'ROOT',operation/'previous'):
            update.recover(self.app,self.work/'update.json',service)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assert_static_data()


if __name__=='__main__':unittest.main()
