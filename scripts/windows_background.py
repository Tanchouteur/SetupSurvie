"""GUI-subsystem entry point for scheduled startup; PowerShell never owns a console."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request


def healthy(config):
    try:
        expected=json.loads((Path(config['app_dir'])/'deploy/release.json').read_text(encoding='utf-8-sig'))['version']
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:8080/api/health',timeout=3) as response:state=json.load(response)
        return state.get('ok') is True and state.get('version')==expected
    except (OSError,ValueError,KeyError):return False


def run(work_dir, *, open_browser=False):
    stable=Path(__file__).resolve().parent
    state=json.loads((stable/'startup-settings.json').read_text(encoding='utf-8-sig'))
    work=Path(work_dir).resolve()
    if state.get('kind')!='SetupSurvie managed Windows startup' or Path(state['work_dir']).resolve()!=work:
        raise ValueError('Configuration de démarrage incohérente.')
    if (work/'transfer-guard.json').exists():return 1
    config=json.loads((work/'settings.json').read_text(encoding='utf-8-sig'))
    if not open_browser:
        if (work/'startup-paused.json').exists():return 0
        journal=work/'update.json'
        if journal.exists() and json.loads(journal.read_text(encoding='utf-8-sig')).get('phase') not in ('complete','rolled_back'):
            return 1
        # A routine health tick needs no shell, Python CLI or Docker command.
        # Download recovery has its own independent scheduled task.
        if healthy(config):return 0
    log=Path(config['data_dir'])/'diagnostics/startup-background.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    command=[str(shell),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
             '-File',str(stable/'startup-windows.ps1'),'-WorkDir',str(work),
             '-OpenBrowser' if open_browser else '-Startup']
    with log.open('ab') as stream:
        return subprocess.run(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,
                              creationflags=subprocess.CREATE_NO_WINDOW,timeout=540).returncode


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir','-WorkDir',required=True)
    parser.add_argument('-OpenBrowser',action='store_true')
    parser.add_argument('-Startup',action='store_true')
    args=parser.parse_args()
    try:raise SystemExit(run(args.work_dir,open_browser=args.OpenBrowser))
    except Exception:
        # pythonw has no usable stderr; record the failure rather than opening UI.
        import traceback
        with (Path(__file__).parent/'startup-background-error.log').open('a',encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        raise SystemExit(1)
