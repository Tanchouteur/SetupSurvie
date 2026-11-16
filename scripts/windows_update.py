"""Install a stable Windows updater outside the replaceable application directory."""
import argparse
from pathlib import Path
import shutil

import setup
from delivery_paths import destination


def install_launcher(app, config):
    if config['target'] != 'windows' or not config.get('app_dir'):
        return
    application = setup.safe_path(config['app_dir'])
    if (application/'.git').exists():
        raise setup.SetupError('Le lanceur de mise à jour exige une application installée, pas un dépôt de développement.')
    base = application.parent
    launcher = destination(base, 'Mettre-a-jour-SetupSurvie.cmd')
    transfer_launcher = destination(base, 'Transferer-SetupSurvie.cmd')
    if transfer_launcher.exists() and 'rem SetupSurvie managed transfer' not in transfer_launcher.read_text(encoding='utf-8-sig'):
        raise setup.SetupError('Un lanceur de transfert existe déjà et ne nous appartient pas. Aucun remplacement.')
    if launcher.exists():
        previous = launcher.read_text(encoding='utf-8-sig')
        if 'rem SetupSurvie managed updater' not in previous and 'maintenance\\mettre-a-jour.ps1' not in previous:
            raise setup.SetupError('Le fichier Mettre-a-jour-SetupSurvie.cmd existe et ne nous appartient pas. Aucun remplacement effectué.')
    for name in ('update-windows.ps1', 'windows-common.ps1', 'transfer-windows.ps1'):
        source = setup.ROOT/'scripts'/name
        target = destination(base, 'maintenance/'+name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or setup.file_hash(source) != setup.file_hash(target):
            temporary = destination(base, 'maintenance/'+name+'.tmp')
            shutil.copyfile(source, temporary)
            temporary.replace(target)
    setup.write_json(destination(base, 'maintenance/update-settings.json'),
                     {'schema': 1, 'work_dir': str(app.work)}, private=True)
    body = '@echo off\r\nrem SetupSurvie managed updater\r\n' \
           'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0maintenance\\update-windows.ps1" %*\r\n' \
           'set "SURVIE_EXIT=%ERRORLEVEL%"\r\n' \
           'if not "%SURVIE_NO_PAUSE%"=="1" pause\r\nexit /b %SURVIE_EXIT%\r\n'
    payload = body.encode('utf-8')
    if not launcher.is_file() or launcher.read_bytes() != payload:
        temporary = destination(base, 'Mettre-a-jour-SetupSurvie.cmd.tmp')
        temporary.write_bytes(payload)
        temporary.replace(launcher)
    from pilot import durable
    durable.write_bytes(destination(base, 'Transferer-SetupSurvie.cmd'),
        b'@echo off\r\nrem SetupSurvie managed transfer\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0maintenance\\transfer-windows.ps1" %*\r\nif errorlevel 1 pause\r\n')
    import windows_autostart
    windows_autostart.refresh(app, config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True)
    args = parser.parse_args()
    application = setup.Installation(args.work_dir)
    install_launcher(application, application.load())
