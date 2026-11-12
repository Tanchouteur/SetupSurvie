"""Real Windows shell links, only in a disposable CI profile; no services start."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name=='nt' and os.environ.get('CI')=='true','COM Windows vérifié uniquement dans le profil jetable de la CI.')
class WindowsShortcutTests(unittest.TestCase):
    def ps(self,code):
        encoded=base64.b64encode(("[Console]::OutputEncoding = [Text.UTF8Encoding]::new(); $ErrorActionPreference='Stop'; "+code).encode('utf-16le')).decode()
        value=subprocess.check_output(['powershell.exe','-NoProfile','-EncodedCommand',encoded],encoding='utf-8')
        return json.loads(value)

    def test_desktop_start_stop_and_login_shortcut_then_disable(self):
        with tempfile.TemporaryDirectory(prefix='survie réglages ') as folder:
            desktop=Path(folder)/'bureau';startup=Path(folder)/'demarrage'
            desktop.mkdir();startup.mkdir()
            paths=[desktop/'Ouvrir SetupSurvie.lnk',desktop/'Arrêter SetupSurvie.lnk',desktop/'SetupSurvie.lnk',startup/'SetupSurvie.lnk']
            args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/create-shortcuts.ps1'),'-WorkDir',folder,
                  '-DesktopDir',str(desktop),'-StartupDir',str(startup)]
            subprocess.run([*args,'-Startup'],check=True,capture_output=True)
            for p in (paths[0],paths[1],paths[3]):self.assertTrue(p.is_file())
            def properties(path):
                literal=str(path).replace("'","''")
                return self.ps("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+literal+"'); @{target=$s.TargetPath;arguments=$s.Arguments;icon=$s.IconLocation} | ConvertTo-Json -Compress")
            start=properties(paths[0]);stop=properties(paths[1]);automatic=properties(paths[3])
            self.assertIn('start-pilot.ps1',start['arguments']);self.assertIn('-OpenBrowser',start['arguments'])
            self.assertIn('stop-pilot.ps1',stop['arguments']);self.assertNotIn('-OpenBrowser',stop['arguments'])
            canonical=self.ps("(Resolve-Path -LiteralPath '"+folder.replace("'","''")+"').Path | ConvertTo-Json -Compress")
            self.assertIn(canonical,start['arguments']);self.assertIn(canonical,automatic['arguments'])
            self.assertNotIn('-OpenBrowser',automatic['arguments'])
            self.assertTrue(start['icon'].lower().endswith('favicon.ico,0'))
            subprocess.run([*args,'-DisableStartup'],check=True,capture_output=True)
            self.assertFalse(paths[3].exists());self.assertTrue(paths[0].exists());self.assertTrue(paths[1].exists())



if __name__=='__main__':unittest.main()
