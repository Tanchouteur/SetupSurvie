"""First-install safety and recovery, without Docker, downloads or real accounts."""
import json
from pathlib import Path
import shutil
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
        self.calls = []

    def tearDown(self):
        self.space.stop(); self.records.stop(); self.tmp.cleanup()

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


if __name__ == '__main__':
    unittest.main()
