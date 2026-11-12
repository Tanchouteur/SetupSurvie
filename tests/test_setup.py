"""Tests for data preservation, offline behavior and generated deployment settings."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('survie_setup', Path(__file__).resolve().parents[1] / 'scripts/setup.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='survie test ')
        self.base = Path(self.tmp.name)
        self.app = setup.Installation(self.base / 'private')
        self.config = self.app.init('linux', self.base / 'data with spaces', cpu=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_installation_uses_requested_default_login_without_resetting_existing_account(self):
        self.assertEqual(self.config['admin_email'],'admin@survie.local')
        config={**self.config,'admin_password':'changed-by-owner'}
        setup.write_json(self.app.settings_path,config,private=True)
        self.assertEqual(self.app.init('linux',cpu=True)['admin_password'],'changed-by-owner')

    def test_repeat_keeps_secrets_and_user_data(self):
        doc = Path(self.config['data_dir']) / 'library/guides/private.txt'
        doc.write_text('Mon document', encoding='utf-8')
        again = self.app.init('linux', cpu=True)
        self.assertEqual(again, self.config)
        self.assertEqual(doc.read_text(encoding='utf-8'), 'Mon document')

    def test_reinstall_cannot_silently_move_data_or_change_system(self):
        with self.assertRaises(setup.SetupError):
            self.app.init('linux', self.base / 'another', cpu=True)
        with self.assertRaises(setup.SetupError):
            self.app.init('windows')

    def test_demo_preserves_existing_document_and_symlink_not_catalogued(self):
        root = Path(self.config['data_dir']) / 'library/guides'
        target = root / 'box.en.txt'
        target.write_text('Version conservée', encoding='utf-8')
        outside = self.base / 'outside.txt'
        outside.write_text('secret', encoding='utf-8')
        (root / 'linked.txt').symlink_to(outside)
        self.app.demo(self.config)
        self.assertEqual(target.read_text(encoding='utf-8'), 'Version conservée')
        catalog = json.loads((Path(self.config['data_dir']) / 'catalog/guides.json').read_text())
        self.assertNotIn('linked.txt', [d['path'] for d in catalog['documents']])
        self.assertIn('box.en.html', [d['path'] for d in catalog['documents']])

    def test_offline_missing_cache_fails_before_any_subprocess(self):
        with patch.object(self.app, 'compose') as compose:
            with self.assertRaises(setup.SetupError):
                self.app.prepare(self.config, offline=True)
            compose.assert_not_called()

    def test_readiness_requires_matching_embedding_revision(self):
        cache = Path(self.config['data_dir']) / 'state/openwebui/cache/embedding-ready.json'
        setup.write_json(cache, setup.VERSIONS['embedding'])
        setup.write_json(Path(self.config['data_dir'])/'state/openwebui/cache/whisper/ready.json',setup.VERSIONS['speech'])
        root=Path(self.config['data_dir'])/'state/openwebui/cache'
        for name in ['embedding/bge-m3/config.json','embedding/bge-m3/tokenizer.json','embedding/bge-m3/model.safetensors','whisper/faster-whisper-small/model.bin','whisper/faster-whisper-small/config.json','whisper/faster-whisper-small/tokenizer.json']:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('fixture')
        with patch.object(self.app, 'compose') as compose:
            self.app.prepare(self.config, offline=True)
            compose.assert_not_called()
        setup.write_json(cache, {'revision':'old'})
        with self.assertRaises(setup.SetupError):
            self.app.prepare(self.config, offline=True)

    def test_no_cloud_model_is_pulled(self):
        with patch.object(self.app, 'request') as request:
            for model in ('model:cloud', 'model:20b-cloud'):
                with self.assertRaises(setup.SetupError):
                    self.app.pull_model(self.config, model)
            request.assert_not_called()

    def test_stop_native_does_not_kill_unowned_or_reused_pid(self):
        setup.write_json(self.app.work / 'native-ollama.json', {'pid':123, 'binary':'example', 'identity':None})
        windows = dict(self.config, target='windows')
        with patch.object(self.app, 'native_owned', return_value=False), patch.object(setup, 'run') as run:
            self.app.stop_native(windows)
            run.assert_not_called()

    def test_imported_images_use_verified_local_ids_without_registry_access(self):
        service='portal'
        self.config['local_images']={service:{'reference':setup.VERSIONS['images'][service], 'id':'sha256:'+'a'*64}}
        self.app.render(self.config)
        self.assertIn("PORTAL_IMAGE='sha256:"+'a'*64+"'", self.app.env_path.read_text())

    def test_import_accepts_podman_hex_ids_and_docker_prefixed_ids_without_pull(self):
        archive=self.base/'images.tar';archive.write_bytes(b'archive fixture')
        images=[{'service':name,'reference':reference,'id':format(index+1,'064x')} for index,(name,reference) in enumerate(setup.VERSIONS['images'].items())]
        setup.write_json(Path(str(archive)+'.json'),{'images':images,'sha256':setup.file_hash(archive)})
        calls=[]
        def command(args,**kwargs):
            calls.append(args)
            if args[:3]==['docker','image','inspect']:return json.dumps([{'Id':'sha256:'+args[3]}])
            self.assertEqual(args[:3],['docker','image','load']);return ''
        with patch.object(setup,'run',side_effect=command):self.app.import_images(self.config,archive)
        self.assertTrue(all(entry['id'].startswith('sha256:') for entry in self.config['local_images'].values()))
        self.assertFalse(any('pull' in args for args in calls))

    def test_sensitive_settings_cannot_be_in_public_library(self):
        app=setup.Installation(self.base / 'exposed/library/private')
        with self.assertRaises(setup.SetupError):
            app.init('linux', self.base / 'exposed', cpu=True)

    def test_pull_failure_is_not_reported_as_prepared(self):
        with patch.object(self.app, 'request', return_value={'error':'model not found'}), patch.object(self.app, 'record') as record:
            with self.assertRaises(setup.SetupError):
                self.app.pull_model(self.config, 'missing:model')
            record.assert_not_called()

    def test_native_existing_server_is_not_started_on_linux(self):
        with patch.object(setup.subprocess, 'Popen') as process:
            self.app.start_native(self.config)
            process.assert_not_called()

    def test_shortcuts_only_for_windows_and_startup_can_be_disabled(self):
        with patch.object(setup,'run') as run:
            self.app.install_windows_shortcuts(self.config)
            run.assert_not_called()
        windows={**self.config,'target':'windows'}
        with patch.object(setup.shutil,'which',return_value='powershell.exe'),patch.object(setup,'run') as run:
            self.app.install_windows_shortcuts(windows)
            args=run.call_args.args[0]
            self.assertIn(str(setup.ROOT/'scripts/create-shortcuts.ps1'),args)
            self.assertEqual(args[-1],'-Startup')
            self.assertEqual(args[args.index('-WorkDir')+1],str(self.app.work))
            self.app.install_windows_shortcuts(windows,startup=False)
            self.assertEqual(run.call_args.args[0][-1],'-DisableStartup')

    def test_stop_native_cleanup_even_if_docker_is_unavailable(self):
        import control,discovery
        with patch.object(setup,'Installation',return_value=self.app),patch.object(control,'stop'),patch.object(discovery,'stop'),patch.object(self.app,'compose',side_effect=setup.SetupError('Docker unavailable')),patch.object(self.app,'stop_native') as native:
            with self.assertRaises(setup.SetupError):setup.main(['--work-dir',str(self.app.work),'down'])
        native.assert_called_once_with(self.config)

    def test_local_import_cannot_use_another_image_version(self):
        self.config['local_images'] = {'portal': {'reference':'unrelated', 'id':'sha256:abc'}}
        with self.assertRaises(setup.SetupError):
            self.app.render(self.config)

    def test_hash_rejects_corrupted_offline_kit_before_docker(self):
        archive = self.base / 'images.tar'
        archive.write_bytes(b'wrong')
        setup.write_json(Path(str(archive)+'.json'), {'sha256':'invalid'})
        with patch.object(setup, 'run') as run:
            with self.assertRaises(setup.SetupError):
                self.app.import_images(self.config, archive)
            run.assert_not_called()

    def test_compose_windows_cpu_and_gpu_with_spaces(self):
        for target, cpu in [('windows', False), ('linux', True), ('linux', False)]:
            with self.subTest(target=target, cpu=cpu):
                c = dict(self.config, target=target, cpu=cpu)
                self.app.render(c)
                result = subprocess.run(self.app.command(c, 'config', '--format', 'json'), capture_output=True, text=True,env=self.app.environment())
                self.assertEqual(result.returncode, 0, result.stderr)
                services = json.loads(result.stdout)['services']
                self.assertEqual(services['open-webui']['environment']['ENABLE_SIGNUP'], 'false')
                self.assertEqual(services['open-webui']['environment']['WEBUI_SECRET_KEY'], self.config['secret'])
                self.assertEqual(services['portal']['volumes'][2]['source'], str(Path(c['data_dir']) / 'catalog'))
                self.assertEqual('ollama' in services, target == 'linux')
                if target == 'linux':
                    gpu = services['ollama'].get('deploy', {}).get('resources', {}).get('reservations', {}).get('devices', [])
                    self.assertEqual(bool(gpu), not cpu)


if __name__ == '__main__':
    unittest.main()
