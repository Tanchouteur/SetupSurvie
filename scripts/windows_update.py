"""Install a stable Windows updater outside the replaceable application directory."""
import argparse
import os
from pathlib import Path
import shutil

import setup
from delivery_paths import destination


def install_transfer_protocol(base):
    """Register a fixed, argument-free PowerShell launch for this user only."""
    if os.name != 'nt':
        return
    import winreg
    key_path = r'Software\Classes\setupsurvie-transfert'
    owner = 'SetupSurvie managed transfer protocol v1'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            try:
                existing, _ = winreg.QueryValueEx(key, 'SetupSurvieOwner')
            except FileNotFoundError:
                return  # An unowned protocol must never be replaced.
            if existing != owner:
                return
    except FileNotFoundError:
        # A per-user registration would otherwise shadow a machine-wide handler.
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path):
                return
        except FileNotFoundError:
            pass

    # Windows may append the clicked URL to the command. WScript receives it,
    # but this fixed script never reads its arguments or forwards them to PS.
    script = destination(base, 'maintenance/transfer-browser.vbs')
    marker = "' SetupSurvie managed transfer protocol v1"
    if script.exists():
        try:
            if not script.read_text(encoding='utf-16').startswith(marker):
                return
        except (OSError, UnicodeError):
            return
    ps_script = destination(base, 'maintenance/transfer-windows.ps1')
    command = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + str(ps_script) + '" -Browser'
    body = marker + '\r\nCreateObject("WScript.Shell").Run "' + command.replace('"', '""') + '", 1, False\r\n'
    from pilot import durable
    durable.write_bytes(script, body.encode('utf-16'))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'URL:SetupSurvie transfer')
        winreg.SetValueEx(key, 'URL Protocol', 0, winreg.REG_SZ, '')
        winreg.SetValueEx(key, 'SetupSurvieOwner', 0, winreg.REG_SZ, owner)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r'\shell\open\command') as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ,
                          f'"{os.path.join(os.environ["SystemRoot"], "System32", "wscript.exe")}" //B //Nologo "{script}"')


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
           'if not "%SURVIE_NO_PAUSE%"=="1" if not "%~1"=="" if /I not "%~1"=="-Cleanup" pause\r\nexit /b %SURVIE_EXIT%\r\n'
    payload = body.encode('utf-8')
    if not launcher.is_file() or launcher.read_bytes() != payload:
        temporary = destination(base, 'Mettre-a-jour-SetupSurvie.cmd.tmp')
        temporary.write_bytes(payload)
        temporary.replace(launcher)
    from pilot import durable
    durable.write_bytes(destination(base, 'Transferer-SetupSurvie.cmd'),
        b'@echo off\r\nrem SetupSurvie managed transfer\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0maintenance\\transfer-windows.ps1" %*\r\nif errorlevel 1 pause\r\n')
    install_transfer_protocol(base)
    import windows_autostart
    windows_autostart.refresh(app, config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True)
    args = parser.parse_args()
    application = setup.Installation(args.work_dir)
    install_launcher(application, application.load())
