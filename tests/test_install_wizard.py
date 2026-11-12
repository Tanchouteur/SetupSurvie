"""First-install safety and recovery, without Docker, downloads or real accounts."""
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import install_wizard as wizard
import setup


class WizardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='survie wizard ')
        self.root = Path(self.tmp.name)
        self.base = self.root/'installation avec espaces'
        self.source = self.root/'source.py'
        self.source.write_text('# tiny fixture\n')
        self.entry = {'path': 'app/scripts/setup.py', 'bytes': self.source.stat().st_size,
                      'sha256': setup.file_hash(self.source)}
        self.records = patch.object(wizard, 'source_records', return_value=([(self.entry, self.source)], None))
        self.records.start()
        self.space = patch.object(wizard.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(100_000_000_000, 0, 100_000_000_000))
        self.space.start()
        self.ports = patch.object(wizard, 'port_busy', return_value=False)
        self.ports.start()
        self.calls = []

    def tearDown(self):
        self.ports.stop(); self.space.stop(); self.records.stop(); self.tmp.cleanup()

    def step(self, args):
        self.calls.append(list(map(str, args)))
        if 'init' in args:
            config = self.base/'prive/settings.json'
            if not config.exists():
                setup.write_json(config, {'secret': 'fixture-preserved', 'data_dir': str(self.base/'donnees')})

    def test_online_creates_independent_application_and_compatible_update_settings(self):
        wizard.install(self.base, lan_host='192.168.1.50', execute_step=self.step)
        self.assertEqual((self.base/'application/scripts/setup.py').read_text(), self.source.read_text())
        config = json.loads((self.base/'prive/settings.json').read_text())
        self.assertEqual(config['app_dir'], (self.base/'application').resolve().as_posix())
        self.assertEqual(config['secret'], 'fixture-preserved')
        installation = next(c for c in self.calls if 'install' in c)
        self.assertIn('--content-pack', installation)
        self.assertIn('--lan-host', installation)
        self.assertIn('gemma4:e4b', self.calls[-1])
        self.assertNotIn('--inference', str(self.calls))
        with self.assertRaisesRegex(setup.SetupError, 'déjà terminée'):
            wizard.install(self.base, resume=True, execute_step=self.step)

    def test_interrupted_configuration_requires_resume_and_preserves_new_documents(self):
        def fail(args):
            self.step(args)
            if 'install' in args:
                guide = self.base/'donnees/library/guides/notice.txt'
                guide.parent.mkdir(parents=True); guide.write_text('ajout utilisateur')
                raise setup.SetupError('simulated failure')
        with self.assertRaises(setup.SetupError):
            wizard.install(self.base, execute_step=fail)
        with self.assertRaisesRegex(setup.SetupError, '--resume'):
            wizard.install(self.base, execute_step=self.step)
        wizard.install(self.base, resume=True, execute_step=self.step)
        self.assertEqual((self.base/'donnees/library/guides/notice.txt').read_text(), 'ajout utilisateur')

    def test_interrupted_copy_is_repaired_but_changed_source_is_refused(self):
        with patch.object(wizard, 'copy_checked', side_effect=OSError('unplugged')):
            with self.assertRaises(OSError):
                wizard.install(self.base, execute_step=self.step)
        target = self.base/'application/scripts/setup.py'
        target.parent.mkdir(parents=True); target.write_text('corrupt')
        wizard.install(self.base, resume=True, execute_step=self.step)
        self.assertEqual(target.read_bytes(), self.source.read_bytes())

    def test_resume_options_or_source_cannot_change(self):
        with patch.object(wizard, 'copy_checked', side_effect=OSError('unplugged')):
            with self.assertRaises(OSError):
                wizard.install(self.base, execute_step=self.step)
        with self.assertRaisesRegex(setup.SetupError, 'options différentes'):
            wizard.install(self.base, resume=True, startup=False, execute_step=self.step)
        self.entry['sha256'] = 'a'*64
        with self.assertRaisesRegex(setup.SetupError, 'source a changé'):
            wizard.install(self.base, resume=True, execute_step=self.step)

    def test_occupied_data_and_not_enough_space_never_start_services(self):
        user = self.base/'donnees/important.txt'
        user.parent.mkdir(parents=True); user.write_text('keep')
        with self.assertRaisesRegex(setup.SetupError, 'occupés'):
            wizard.install(self.base, execute_step=self.step)
        self.assertEqual(user.read_text(), 'keep')
        user.unlink()
        self.space.stop()
        with patch.object(wizard.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(1, 0, 1)):
            with self.assertRaisesRegex(setup.SetupError, 'Espace insuffisant'):
                wizard.install(self.base, execute_step=self.step)
        self.assertFalse(self.calls)
        self.assertFalse((self.base/'.installation.json').exists())

    def test_path_overlap_traversal_and_concurrent_operation_are_refused(self):
        for base, kit in [(setup.ROOT/'data-new', None), (self.root/'kit/sub', self.root/'kit')]:
            with self.assertRaises(setup.SetupError):
                wizard.install(base, kit, execute_step=self.step)
        self.entry['path'] = 'app/../outside'
        with self.assertRaises(setup.SetupError):
            wizard.install(self.base, execute_step=self.step)
        self.assertFalse(self.calls)
        self.base.mkdir(exist_ok=True)
        with wizard.installation_lock(self.base):
            with self.assertRaisesRegex(setup.SetupError, 'déjà en cours'):
                with wizard.installation_lock(self.base):
                    self.fail('lock acquired twice')

    def test_kit_mode_uses_local_images_and_no_online_content_pack(self):
        kit = self.root/'kit'; kit.mkdir()
        wizard.install(self.base, kit, execute_step=self.step)
        self.assertIn('import-images', self.calls[-2])
        self.assertIn('--offline', self.calls[-1])
        self.assertNotIn('--content-pack', self.calls[-1])

    def test_corrupt_copy_never_becomes_final(self):
        self.entry['sha256'] = 'f'*64
        target = self.root/'target.py'
        with self.assertRaises(setup.SetupError):
            wizard.copy_checked(self.source, target, self.entry)
        self.assertFalse(target.exists())

    def test_busy_port_stops_before_source_audit_copy_or_download(self):
        with patch.object(wizard, 'port_busy', side_effect=lambda port: port == 8080):
            with self.assertRaisesRegex(setup.SetupError, 'mise à jour'):
                wizard.install(self.base, execute_step=self.step)
        wizard.source_records.assert_not_called()
        self.assertFalse(self.calls)
        self.assertFalse((self.base/'.installation.json').exists())

    def test_port_probe_detects_an_existing_local_listener(self):
        self.ports.stop()
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            port = listener.getsockname()[1]
            self.assertTrue(wizard.port_busy(port))
        self.assertFalse(wizard.port_busy(port))

    def test_resume_accepts_only_its_own_published_ports(self):
        work = self.base/'prive'
        setup.write_json(work/'settings.json', {'project': 'own-test', 'target': 'windows'})
        for output in ('[{"State":"running","Publishers":[{"PublishedPort":8080}]}]',
                       '{"State":"running","Publishers":[{"PublishedPort":8080}]}\n'):
            with patch.object(wizard, 'port_busy', side_effect=lambda port: port == 8080), \
                 patch.object(setup.Installation, 'compose', return_value=output) as compose:
                wizard.check_installation_ports(work)
                compose.assert_called_once()
        with patch.object(wizard, 'port_busy', side_effect=lambda port: port in (8080, 3000)), \
             patch.object(setup.Installation, 'compose', return_value='[{"State":"running","Publishers":[{"PublishedPort":8080}]}]'):
            with self.assertRaisesRegex(setup.SetupError, '3000'):
                wizard.check_installation_ports(work)

    def test_resume_does_not_trust_stale_native_process_markers(self):
        work = self.base/'prive'
        setup.write_json(work/'settings.json', {'project': 'own-test', 'target': 'windows'})
        setup.write_json(work/'native-ollama.json', {'pid': 123, 'binary': 'fixture'})
        with patch.object(wizard, 'port_busy', side_effect=lambda port: port == 11435), \
             patch.object(setup.Installation, 'native_owned', return_value=False):
            with self.assertRaisesRegex(setup.SetupError, '11435'):
                wizard.check_installation_ports(work)
        with patch.object(wizard, 'port_busy', side_effect=lambda port: port == 11435), \
             patch.object(setup.Installation, 'native_owned', return_value=True):
            wizard.check_installation_ports(work)

    def test_source_export_contains_single_and_legacy_launchers(self):
        self.records.stop()
        records, _ = wizard.source_records(None)
        names = {entry['path'] for entry, _ in records}
        for name in ('Installer-SetupSurvie.cmd', 'Mettre-a-jour-SetupSurvie.cmd', '1-Preparer-le-PC.cmd', '2-Installer-SetupSurvie.cmd', 'scripts/install-all-windows.ps1', 'scripts/update-windows.ps1', 'scripts/windows_update.py'):
            self.assertIn('app/'+name, names)


if __name__ == '__main__':
    unittest.main()
