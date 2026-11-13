import hashlib,json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,content,content_retry,windows_resume
from delivery_paths import locked

class WindowsRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.app=setup.Installation(self.root/'private')
        self.config=self.app.init('windows',self.root/'data',cpu=True)
        application=self.root/'application';(application/'scripts').mkdir(parents=True)
        self.config['app_dir']=str(application)
        setup.write_json(self.app.settings_path,self.config,private=True)
        self.data=Path(self.config['data_dir']);self.plan=self.data/'catalog/selection.json'
        self.item=dict(id='a',title='A',path='library/zim/a.zim',url='https://example.org/a.zim',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
        setup.write_json(self.plan,{'schema':1,'kind':'SetupSurvie Kiwix thematic selection','items':[self.item]})
        windows_resume.configure(self.app.work,self.plan)
    def test_enable_pins_selection_without_starting_or_pausing_current_ai(self):
        state=json.loads((self.app.work/'content-resume.json').read_text())
        self.assertEqual(state['sha256'],setup.file_hash(self.plan));self.assertEqual(state['jobs'],2)
        self.assertFalse((self.app.work/'inference-paused.json').exists())
        self.assertFalse(self.app.load()['inference_autostart'])
        self.assertTrue((self.root/'maintenance/windows_resume.py').is_file())
    def test_existing_supervisor_is_not_disturbed_or_metadata_replaced(self):
        marker=self.data/'diagnostics/bibliotheque-transfer.json'
        setup.write_json(marker,{'pid':12345,'state':'active'})
        before=marker.read_bytes()
        with locked(self.data/'catalog/content-supervisor.lock'),patch.object(content_retry,'supervise') as download:
            self.assertEqual(windows_resume.run(self.app.work),'already_running')
        download.assert_not_called();self.assertEqual(marker.read_bytes(),before)
    def test_resume_calls_only_downloader_and_preserves_partial(self):
        part=self.data/(self.item['path']+'.part');part.parent.mkdir(parents=True,exist_ok=True);part.write_bytes(b'a')
        def supervise(root,items,**kwargs):
            self.assertEqual(items,[self.item]);self.assertEqual(kwargs['workers'],2)
            self.assertEqual(part.read_bytes(),b'a');return True
        with patch.object(content_retry,'supervise',side_effect=supervise),patch.object(setup.Installation,'up') as up,patch.object(setup.Installation,'start_native') as native:
            self.assertEqual(windows_resume.run(self.app.work),'complete')
        up.assert_not_called();native.assert_not_called();self.assertEqual(part.read_bytes(),b'a')
        self.assertFalse((self.app.work/'inference-paused.json').exists())
    def test_changed_plan_or_unfinished_update_refuses_without_transfer(self):
        with patch.object(content_retry,'supervise') as download:
            setup.write_json(self.app.work/'update.json',{'phase':'switched'})
            with self.assertRaisesRegex(ValueError,'Mise à jour'):windows_resume.run(self.app.work)
            setup.write_json(self.app.work/'update.json',{'phase':'complete'})
            self.plan.write_text(self.plan.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'plan a changé'):windows_resume.run(self.app.work)
        download.assert_not_called()
    def test_explicit_pause_and_disabled_configuration_are_respected(self):
        pause=self.data/'catalog/content-supervisor.pause';pause.touch()
        self.assertEqual(windows_resume.run(self.app.work),'paused');self.assertTrue(pause.exists())
        state=json.loads((self.app.work/'content-resume.json').read_text());state['enabled']=False
        setup.write_json(self.app.work/'content-resume.json',state)
        self.assertEqual(windows_resume.run(self.app.work),'disabled')
    def test_completed_plan_does_not_restart_downloader(self):
        target=self.data/self.item['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'abc')
        setup.write_json(self.data/'catalog/downloaded-content.json',{'schema':1,'items':[self.item]})
        with patch.object(content_retry,'supervise') as download:
            self.assertEqual(windows_resume.run(self.app.work),'complete')
        download.assert_not_called()
    def test_login_sets_pause_but_keeps_existing_gaming_reason(self):
        windows_resume.prepare_login(self.app.work)
        marker=self.app.work/'inference-paused.json';self.assertTrue(marker.exists())
        setup.write_json(marker,{'reason':'gaming'})
        windows_resume.prepare_login(self.app.work)
        self.assertEqual(json.loads(marker.read_text()),{'reason':'gaming'})
    def test_persistent_no_autostart_policy_keeps_services_without_native_ai(self):
        import control,discovery
        config=self.app.load()
        with patch.object(self.app,'catalog'),patch.object(control,'start'),patch.object(discovery,'start'),patch.object(self.app,'start_native') as native,patch.object(self.app,'compose') as compose:
            self.app.up(config)
        native.assert_not_called()
        self.assertIn('pilot',compose.call_args.args)
        self.assertNotIn('ollama',compose.call_args.args[1:])
    def test_external_plan_and_invalid_jobs_refused(self):
        external=self.root/'external.json';external.write_bytes(self.plan.read_bytes())
        with self.assertRaises(ValueError):windows_resume.configure(self.app.work,external)
        for count in (0,4,True):
            with self.assertRaises(ValueError):windows_resume.configure(self.app.work,self.plan,count)

if __name__=='__main__':unittest.main()
