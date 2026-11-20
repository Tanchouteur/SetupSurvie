import json
import os
from pathlib import Path
import subprocess
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
                patch.object(installer, 'initial_model', return_value=setup.VERSIONS['default_model']), \
                patch.object(setup, 'main', side_effect=setup.SetupError('interruption')) as install:
            with self.assertRaisesRegex(setup.SetupError, 'interruption'):
                installer.start(self.base)
        self.assertIn('--no-startup', install.call_args.args[0])
        self.assertIn('health', install.call_args.args[0])
        self.assertFalse((app.work / 'installation-linux-terminee').exists())

    def test_first_boot_selects_compact_model_on_a_six_gib_system(self):
        installer.installation_plan(self.base, [])
        sysconf = {'SC_PHYS_PAGES': 6 * 1024 ** 3 // 4096, 'SC_PAGE_SIZE': 4096}
        with patch.object(installer.os, 'sysconf', side_effect=sysconf.__getitem__, create=True), \
                patch.object(installer.system, 'bind_controller_to_engine'), \
                patch.object(setup.Installation, 'doctor', side_effect=setup.SetupError('interruption')):
            with self.assertRaisesRegex(setup.SetupError, 'interruption'):
                installer.start(self.base)
        app = setup.Installation(self.base / 'private')
        self.assertEqual(app.load()['chat_model'], 'qwen3:1.7b-q4_K_M')
        self.assertIn('CHAT_MODEL=', app.env_path.read_text())
        self.assertIn('qwen3:1.7b-q4_K_M', app.env_path.read_text())
        resumed = app.init('linux', self.base / 'data', cpu=True, initial_chat_model=setup.VERSIONS['default_model'])
        self.assertEqual(resumed['chat_model'], 'qwen3:1.7b-q4_K_M')

    def test_initial_model_keeps_standard_model_on_a_larger_system(self):
        sysconf = {'SC_PHYS_PAGES': 32 * 1024 ** 3 // 4096, 'SC_PAGE_SIZE': 4096}
        with patch.object(installer.os, 'sysconf', side_effect=sysconf.__getitem__, create=True):
            self.assertEqual(installer.initial_model(), setup.VERSIONS['default_model'])

    def test_pilot_profile_and_subtitle_context_follow_compose_model(self):
        for model, context, think in (
            ('qwen3:1.7b-q4_K_M', 8192, False),
            (setup.VERSIONS['default_model'], 16384, 'low'),
        ):
            with self.subTest(model=model):
                result = subprocess.run(
                    [sys.executable, '-c', '''
import json
from pilot import captions, engine, store
store.init()
profile = captions.engine.MODES['rapide']
print(json.dumps([profile['model'], captions.engine.context_size(profile['model']), profile['think']]))
'''],
                    cwd=ROOT,
                    env={**os.environ, 'CHAT_MODEL': model, 'PILOT_STATE_DIR': str(self.base)},
                    check=True, capture_output=True, text=True,
                )
                self.assertEqual(json.loads(result.stdout), [model, context, think])
