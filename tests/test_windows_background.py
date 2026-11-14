import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import windows_background


class BackgroundLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='survie background ');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.work=self.root/'private';self.work.mkdir()
        (self.work/'settings.json').write_text(json.dumps({'data_dir':str(self.root/'data')}))
        (self.root/'startup-settings.json').write_text(json.dumps({'kind':'SetupSurvie managed Windows startup','work_dir':str(self.work)}))

    def test_background_child_has_no_console_and_preserves_failure_status(self):
        result=MagicMock(returncode=7)
        with patch.object(windows_background,'__file__',str(self.root/'windows_background.py')),patch.dict(os.environ,{'SystemRoot':'C:/Windows'}),patch.object(windows_background.subprocess,'CREATE_NO_WINDOW',0x08000000,create=True),patch.object(windows_background.subprocess,'run',return_value=result) as run:
            self.assertEqual(windows_background.run(self.work),7)
        args=run.call_args.args[0]
        self.assertIn('-NonInteractive',args);self.assertEqual(args[-1],'-Startup')
        self.assertEqual(run.call_args.kwargs['creationflags'],0x08000000)
        self.assertEqual(run.call_args.kwargs['stdin'],windows_background.subprocess.DEVNULL)
        self.assertNotIn('shell',run.call_args.kwargs)
        self.assertTrue((self.root/'data/diagnostics/startup-background.log').exists())

    def test_owner_mismatch_never_launches_powershell(self):
        (self.root/'startup-settings.json').write_text('{"kind":"other application"}')
        with patch.object(windows_background,'__file__',str(self.root/'windows_background.py')),patch.object(windows_background.subprocess,'run') as run:
            with self.assertRaises(ValueError):windows_background.run(self.work)
        run.assert_not_called()

    def test_healthy_paused_or_updating_site_starts_no_child(self):
        with patch.object(windows_background,'__file__',str(self.root/'windows_background.py')),patch.object(windows_background.subprocess,'run') as run:
            with patch.object(windows_background,'healthy',return_value=True):self.assertEqual(windows_background.run(self.work),0)
            (self.work/'startup-paused.json').write_text('{}')
            self.assertEqual(windows_background.run(self.work),0)
            (self.work/'startup-paused.json').unlink()
            (self.work/'update.json').write_text('{"phase":"switched"}')
            self.assertEqual(windows_background.run(self.work),1)
        run.assert_not_called()
