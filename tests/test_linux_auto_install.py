from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_auto_install as installer
import setup


class LinuxAutoInstallTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_resume_requires_the_same_packs_regardless_of_order(self):
        plan = installer.installation_plan(self.base, ['water', 'health', 'water'])
        self.assertEqual(plan['packs'], ['health', 'water'])
        self.assertEqual(installer.installation_plan(self.base, ['health', 'water']), plan)
        with self.assertRaisesRegex(setup.SetupError, 'mêmes lots'):
            installer.installation_plan(self.base, ['health'])

    def test_unknown_pack_does_not_persist_plan(self):
        with self.assertRaisesRegex(setup.SetupError, 'inconnus'):
            installer.installation_plan(self.base, ['ce-lot-n-existe-pas'])
        self.assertFalse((self.base / 'installation-linux.json').exists())

    def test_boot_after_completion_does_not_repeat_installation(self):
        installer.installation_plan(self.base, [])
        app = setup.Installation(self.base / 'private')
        app.init('linux', self.base / 'data', False, True)
        (app.work / 'installation-linux-terminee').touch()
        with patch.object(installer.system, 'bind_controller_to_engine'), \
                patch.object(setup, 'main') as install, patch.object(setup.Installation, 'up') as up:
            installer.start(self.base)
        install.assert_not_called()
        up.assert_called_once()

    def test_interrupted_install_has_no_completion_marker(self):
        installer.installation_plan(self.base, ['health'])
        app = setup.Installation(self.base / 'private')
        app.init('linux', self.base / 'data', False, True)
        with patch.object(installer.system, 'bind_controller_to_engine'), \
                patch.object(setup, 'main', side_effect=setup.SetupError('interruption')) as install:
            with self.assertRaisesRegex(setup.SetupError, 'interruption'):
                installer.start(self.base)
        self.assertIn('--no-startup', install.call_args.args[0])
        self.assertIn('health', install.call_args.args[0])
        self.assertFalse((app.work / 'installation-linux-terminee').exists())
