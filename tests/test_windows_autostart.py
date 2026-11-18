import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,windows_autostart,windows_resume,content
from delivery_paths import locked

class AutoStartTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.app=setup.Installation(self.root/'private')
        self.c=self.app.init('windows',self.root/'data',cpu=True)
        application=self.root/'application';application.mkdir();self.c['app_dir']=str(application)
        setup.write_json(self.app.settings_path,self.c)
    def test_launcher_captures_portable_tools_and_preserves_private_settings(self):
        docker=Path(self.c['data_dir'])/'tools/DockerDesktop/resources/bin/docker.exe';docker.parent.mkdir(parents=True);docker.write_bytes(b'fixture')
        desktop=docker.parent.parent.parent/'Docker Desktop.exe';desktop.write_bytes(b'fixture')
        ollama=Path(self.c['data_dir'])/'tools/Ollama/ollama.exe';ollama.parent.mkdir(parents=True);ollama.write_bytes(b'fixture')
        original=self.app.settings_path.read_bytes()
        launcher=windows_autostart.prepare(self.app,self.c,python=sys.executable,find=lambda name:None)
        runtime=json.loads((launcher.parent/'startup-settings.json').read_text())
        self.assertEqual(runtime['desktop'],str(desktop));self.assertIn(str(ollama.parent),runtime['paths'])
        self.assertEqual(runtime['python'],str(Path(sys.executable).resolve()))
        after=self.app.load();self.assertEqual(after,json.loads(original))
        self.assertFalse((self.app.work/'inference-paused.json').exists())
        self.assertTrue((launcher.parent/'register-startup-windows.ps1').is_file())
    def test_repeated_prepare_is_stable_and_unknown_owner_refused(self):
        launcher=windows_autostart.prepare(self.app,self.c)
        record=launcher.parent/'startup-settings.json';before=record.read_bytes()
        windows_autostart.prepare(self.app,self.c);self.assertEqual(record.read_bytes(),before)
        record.write_text('{"kind":"another application"}')
        with self.assertRaises(setup.SetupError):windows_autostart.prepare(self.app,self.c)
    def test_other_platforms_or_noninstalled_code_do_not_create_launcher(self):
        self.assertIsNone(windows_autostart.prepare(self.app,{**self.c,'target':'linux'}))
        self.assertIsNone(windows_autostart.prepare(self.app,{k:v for k,v in self.c.items() if k!='app_dir'}))
    def test_active_cli_keeps_its_progress_and_is_not_replaced(self):
        windows_autostart.prepare(self.app,self.c)
        plan=Path(self.c['data_dir'])/'catalog/selection.json'
        setup.write_json(plan,{'schema':1,'kind':'SetupSurvie Kiwix thematic selection','items':[{'id':'a','title':'a','path':'library/zim/a.zim','url':'https://example.org/a.zim','bytes':1,'sha256':'a'*64}]})
        windows_resume.arm_if_installed(self.app,self.c,plan)
        progress=Path(self.c['data_dir'])/'catalog/content-progress.json';setup.write_json(progress,{'active':'original'})
        before=progress.read_bytes()
        with locked(Path(self.c['data_dir'])/'catalog/content.lock'):
            self.assertEqual(windows_resume.run(self.app.work),'already_running')
        self.assertEqual(progress.read_bytes(),before)
    def test_new_installation_waits_for_a_user_selected_plan(self):
        windows_autostart.prepare(self.app,self.c)
        self.assertEqual(windows_resume.run(self.app.work),'disabled')
        self.assertFalse((self.app.work/'content-resume.json').exists())

    def test_shortcuts_cli_respects_disable_option_without_starting_services(self):
        with patch.object(setup,'Installation',return_value=self.app),patch.object(self.app,'install_windows_shortcuts') as shortcuts,patch.object(self.app,'up') as up:
            setup.main(['--work-dir',str(self.app.work),'shortcuts','--no-startup'])
        shortcuts.assert_called_once_with(self.app.load(),startup=False);up.assert_not_called()

    def test_private_web_plan_is_allowed_only_at_its_exact_job_path(self):
        data=Path(self.c['data_dir']);work=self.app.work
        self.assertTrue(windows_resume.authorized_plan_path(work,data,work/'library-web'/('a'*32)/'plan.json'))
        self.assertFalse(windows_resume.authorized_plan_path(work,data,work/'library-web'/'unknown'/'plan.json'))
        self.assertFalse(windows_resume.authorized_plan_path(work,data,work/'settings.json'))

    def test_update_refresh_keeps_preferences_and_uses_owned_task_only(self):
        windows_autostart.prepare(self.app,self.c)
        config={**self.app.load(),'inference_autostart':True};setup.write_json(self.app.settings_path,config)
        before=self.app.settings_path.read_bytes()
        with patch.object(windows_autostart,'os') as operating,patch.object(windows_autostart.shutil,'which',return_value='powershell-fixture'),patch.object(setup,'run') as run:
            operating.name='nt';windows_autostart.refresh(self.app,config)
        self.assertEqual(self.app.settings_path.read_bytes(),before)
        self.assertIn('-RefreshOnly',run.call_args.args[0])
        self.assertTrue((self.root/'maintenance/windows_background.py').exists())

    def test_update_migrates_legacy_default_but_preserves_user_pause(self):
        windows_autostart.prepare(self.app,self.c)
        record=self.root/'maintenance/startup-settings.json'
        legacy=json.loads(record.read_text());legacy.pop('inference_default_migrated')
        setup.write_json(record,legacy)
        config={**self.app.load(),'inference_autostart':False}
        setup.write_json(self.app.settings_path,config)
        marker=self.app.work/'inference-paused.json'
        setup.write_json(marker,{'reason':'user_gaming'})
        windows_autostart.refresh(self.app,config)
        self.assertTrue(self.app.load()['inference_autostart'])
        self.assertEqual(json.loads(marker.read_text())['reason'],'user_gaming')
        legacy=json.loads(record.read_text());legacy.pop('inference_default_migrated')
        setup.write_json(record,legacy)
        config={**self.app.load(),'inference_autostart':False}
        setup.write_json(self.app.settings_path,config)
        setup.write_json(marker,{'reason':'windows_no_inference_autostart'})
        windows_autostart.refresh(self.app,config)
        self.assertFalse(marker.exists())
        # A later explicit preference must not be migrated repeatedly.
        config={**self.app.load(),'inference_autostart':False}
        setup.write_json(self.app.settings_path,config)
        windows_autostart.refresh(self.app,config)
        self.assertFalse(self.app.load()['inference_autostart'])

    def test_unconfigured_update_does_not_enable_startup(self):
        with patch.object(setup,'run') as run:windows_autostart.refresh(self.app,self.c)
        run.assert_not_called()
        self.assertFalse((self.root/'maintenance/startup-settings.json').exists())

if __name__=='__main__':unittest.main()
