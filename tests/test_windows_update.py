import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
import windows_update


class WindowsUpdateLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='survie mise a jour ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'installation avec espaces'
        self.application = self.base/'application'
        self.application.mkdir(parents=True)
        self.source = self.root/'source/scripts'
        self.source.mkdir(parents=True)
        for name in ('update-windows.ps1', 'windows-common.ps1', 'transfer-windows.ps1'):
            (self.source/name).write_text('# fixture '+name)
        self.app = setup.Installation(self.root/'prive ailleurs')
        self.config = {'target': 'windows', 'app_dir': self.application.as_posix()}
        source = patch.object(setup, 'ROOT', self.source.parent)
        source.start(); self.addCleanup(source.stop)
        protocol = patch.object(windows_update, 'install_transfer_protocol')
        protocol.start(); self.addCleanup(protocol.stop)

    def test_stable_launcher_and_metadata_support_private_folder_outside_installation(self):
        windows_update.install_launcher(self.app, self.config)
        launcher = self.base/'Mettre-a-jour-SetupSurvie.cmd'
        self.assertIn(b'%~dp0maintenance\\update-windows.ps1', launcher.read_bytes())
        metadata = json.loads((self.base/'maintenance/update-settings.json').read_text())
        self.assertEqual(metadata['work_dir'], str(self.app.work))
        self.assertEqual((self.base/'maintenance/windows-common.ps1').read_bytes(), (self.source/'windows-common.ps1').read_bytes())
        # Recovery remains reachable while the replaceable application is absent.
        self.application.rmdir()
        self.assertTrue(launcher.is_file())
        self.assertTrue((self.base/'maintenance/update-windows.ps1').is_file())

    def test_refresh_preserves_maintenance_checkout_and_user_files(self):
        windows_update.install_launcher(self.app, self.config)
        marker = self.base/'maintenance/source/preserved.txt'
        marker.parent.mkdir(); marker.write_text('keep')
        (self.source/'update-windows.ps1').write_text('# newer fixture')
        windows_update.install_launcher(self.app, self.config)
        self.assertEqual(marker.read_text(), 'keep')
        self.assertEqual((self.base/'maintenance/update-windows.ps1').read_text(), '# newer fixture')

    def test_unrelated_launcher_is_not_overwritten(self):
        launcher = self.base/'Mettre-a-jour-SetupSurvie.cmd'
        launcher.write_text('unrelated user file')
        with self.assertRaisesRegex(setup.SetupError, 'ne nous appartient pas'):
            windows_update.install_launcher(self.app, self.config)
        self.assertEqual(launcher.read_text(), 'unrelated user file')
        self.assertFalse((self.base/'maintenance').exists())

    def test_development_checkout_and_non_windows_target_do_not_receive_launcher(self):
        (self.application/'.git').mkdir()
        with self.assertRaises(setup.SetupError):
            windows_update.install_launcher(self.app, self.config)
        windows_update.install_launcher(self.app, dict(self.config, target='linux'))
        self.assertFalse((self.base/'Mettre-a-jour-SetupSurvie.cmd').exists())

    def test_setup_installs_stable_updater_before_creating_shortcuts(self):
        with patch.object(setup.shutil, 'which', return_value='powershell-fixture'), patch.object(setup, 'run') as run:
            self.app.install_windows_shortcuts(self.config, startup=False)
        self.assertTrue((self.base/'Mettre-a-jour-SetupSurvie.cmd').is_file())
        self.assertIn('-DisableStartup', run.call_args.args[0])
        self.assertIn(str(self.app.work), run.call_args.args[0])


class TransferProtocolTests(unittest.TestCase):
    class Key:
        def __init__(self, path): self.path = path
        def __enter__(self): return self
        def __exit__(self, *args): pass

    def test_registration_ignores_url_and_preserves_unowned_key(self):
        values = {}
        machine = {}
        def open_key(root, path):
            store = machine if root == 2 else values
            if path not in store: raise FileNotFoundError(path)
            return self.Key(path)
        def create_key(root, path):
            values.setdefault(path, {})
            return self.Key(path)
        def get_value(key, name):
            if name not in values[key.path]: raise FileNotFoundError(name)
            return values[key.path][name], 1
        def set_value(key, name, reserved, kind, value):
            values[key.path][name] = value
        registry = types.SimpleNamespace(HKEY_CURRENT_USER=1, HKEY_LOCAL_MACHINE=2, REG_SZ=1, OpenKey=open_key,
                                         CreateKey=create_key, QueryValueEx=get_value, SetValueEx=set_value)
        key = r'Software\Classes\setupsurvie-transfert'
        with tempfile.TemporaryDirectory(prefix='survie protocole ') as folder, \
             patch.dict(sys.modules, {'winreg': registry}), \
             patch.object(windows_update, 'os', types.SimpleNamespace(
                 name='nt', path=windows_update.os.path, environ=windows_update.os.environ)), \
             patch.dict(windows_update.os.environ, {'SystemRoot': r'C:\Windows'}):
            base = Path(folder)
            (base/'maintenance').mkdir()
            values[key] = {'': 'Autre application'}
            windows_update.install_transfer_protocol(base)
            self.assertEqual(values[key], {'': 'Autre application'})
            self.assertFalse((base/'maintenance/transfer-browser.vbs').exists())
            del values[key]
            machine[key] = {'': 'Autre application'}
            windows_update.install_transfer_protocol(base)
            self.assertNotIn(key, values)
            del machine[key]
            (base/'maintenance/transfer-browser.vbs').write_text('fichier personnel')
            windows_update.install_transfer_protocol(base)
            self.assertNotIn(key, values)
            (base/'maintenance/transfer-browser.vbs').unlink()
            windows_update.install_transfer_protocol(base)
            command = values[key+r'\shell\open\command']['']
            script = (base/'maintenance/transfer-browser.vbs').read_text(encoding='utf-16')
            self.assertIn('wscript.exe', command.lower())
            self.assertNotIn('%1', command)
            self.assertIn('-Browser', script)
            self.assertNotIn('Arguments', script)
            windows_update.install_transfer_protocol(base)
            self.assertEqual(values[key]['SetupSurvieOwner'], 'SetupSurvie managed transfer protocol v1')
