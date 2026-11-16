"""Windows-specific diagnostics; no installation or live task changes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
POWERSHELL=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File']


@unittest.skipUnless(os.name=='nt','Windows real API required')
class WindowsTransferTests(unittest.TestCase):
    def test_powershell_syntax(self):
        script="""param([string]$Root)
$ErrorActionPreference='Stop'
foreach ($name in @('transfer-host-check.ps1','transfer-windows.ps1','create-shortcuts.ps1','startup-windows.ps1')) {
 $tokens=$null;$errors=$null
 [void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root ('scripts\\'+$name)),[ref]$tokens,[ref]$errors)
 if ($errors.Count) { throw ($name+': '+($errors | Out-String)) }
}
"""
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'parse.ps1';path.write_text(script,encoding='utf-8-sig')
            subprocess.run([*POWERSHELL,str(path),'-Root',str(ROOT)],check=True,capture_output=True)

    def test_volume_check_has_no_credentials_or_system_actions(self):
        with tempfile.TemporaryDirectory() as name:
            result=subprocess.run([*POWERSHELL,str(ROOT/'scripts/transfer-host-check.ps1'),'-Source',name,'-Destination',name],check=True,capture_output=True,text=True,encoding='utf-8')
        state=json.loads(result.stdout)
        self.assertTrue(state['destination']['known'])
        self.assertEqual(state['source']['disk'],state['destination']['disk'])
        self.assertFalse(state['startup_enabled'])
        self.assertNotIn('secret',result.stdout.lower())
