"""Linux host integration: rootless Docker access and start at boot.

Windows has its own launchers and scheduled tasks. On Linux the host processes
(controller, local name announcement, automatic indexing) are started by
``survie.sh up``; a systemd user service keeps them running outside a terminal
and after a reboot. Nothing here needs root.
"""
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import time

import setup

LOOPBACK_ENV='DOCKERD_ROOTLESS_ROOTLESSKIT_DISABLE_HOST_LOOPBACK'
# rootlesskit maps the host loopback to this address when it is allowed.
ROOTLESS_GATEWAY='10.0.2.2'


def docker_rootless():
    try:options=setup.run(['docker','info','--format','{{json .SecurityOptions}}'],capture=True,timeout=30)
    except setup.SetupError:return False
    return 'name=rootless' in options


def docker_socket(environ=None):
    environ=os.environ if environ is None else environ
    host=environ.get('DOCKER_HOST','')
    if host.startswith('unix://'):return Path(host[len('unix://'):]),True
    runtime=environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}'
    return Path(runtime)/'docker.sock',False


def rootlesskit_arguments(socket,proc=Path('/proc')):
    """Arguments of the rootlesskit serving this socket, or None when unknown."""
    state='--state-dir='+str(socket.parent/'dockerd-rootless')
    for folder in proc.iterdir():
        if not folder.name.isdigit():continue
        try:arguments=(folder/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        arguments=[a.decode('utf-8','replace') for a in arguments if a]
        if arguments and Path(arguments[0]).name=='rootlesskit' and state in arguments:return arguments
    return None


def user_unit_dir():
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'systemd/user'


def systemctl(*arguments,capture=False):
    return setup.run(['systemctl','--user',*arguments],capture=capture,timeout=120)


def ensure_host_loopback(proc=Path('/proc')):
    """Containers must reach the controller through the host loopback.

    Returns a short French status line. Raises SetupError with the exact
    remedy when the daemon cannot be adjusted automatically.
    """
    socket,custom=docker_socket()
    arguments=rootlesskit_arguments(socket,proc)
    if arguments is None:return 'Docker rootless : réglage réseau non vérifiable, contrôle après démarrage.'
    if '--disable-host-loopback' not in arguments:return 'Docker rootless : accès des conteneurs au contrôleur local autorisé.'
    unit=user_unit_dir()/'docker.service'
    if custom or not unit.is_file():
        raise setup.SetupError('Docker rootless empêche les conteneurs de joindre le contrôleur local. Redémarrez ce démon Docker avec '
                               f'{LOOPBACK_ENV}=false puis relancez l’installation. Voir docs/installation/README.md.')
    dropin=unit.parent/'docker.service.d/setupsurvie-host-loopback.conf'
    dropin.parent.mkdir(parents=True,exist_ok=True)
    dropin.write_text(f'# Ajouté par SetupSurvie : accès des conteneurs au contrôleur local (127.0.0.1).\n[Service]\nEnvironment={LOOPBACK_ENV}=false\n',encoding='utf-8')
    systemctl('daemon-reload');systemctl('restart','docker.service')
    for _ in range(60):
        if docker_rootless():return 'Docker rootless reconfiguré pour SetupSurvie : '+str(dropin)
        time.sleep(1)
    raise setup.SetupError('Docker ne répond plus après sa reconfiguration ; consultez « systemctl --user status docker ».')


def unit_name(c):return 'setupsurvie-'+c['project']+'.service'


def unit_quote(value,exec_argument=False):
    """Quote one systemd word, preserving specifiers and optional exec variables."""
    value=str(value)
    if any(ch in value for ch in '\r\n\x00'):
        raise setup.SetupError('Chemin invalide pour le service de démarrage.')
    value=value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')
    if exec_argument:value=value.replace('$','$$')
    return '"'+value+'"'


def unit_text(app,c,environ=None):
    environ=os.environ if environ is None else environ
    docker=shutil.which('docker',path=environ.get('PATH')) or shutil.which('docker')
    if not docker:raise setup.SetupError('Programme docker introuvable pour le démarrage automatique.')
    paths=[str(Path(docker).parent),'/usr/local/bin','/usr/bin','/bin']
    lines=['[Unit]','Description=SetupSurvie (bibliothèque et assistant local)',
           'After=network-online.target docker.service','Wants=network-online.target','StartLimitIntervalSec=0','',
           '[Service]','Type=oneshot','RemainAfterExit=yes','Restart=on-failure','RestartSec=15','TimeoutStartSec=900',
           'Environment='+unit_quote('PATH='+':'.join(dict.fromkeys(paths)))]
    if environ.get('DOCKER_HOST'):lines.append('Environment='+unit_quote('DOCKER_HOST='+environ['DOCKER_HOST']))
    survie=setup.ROOT/'scripts/survie.sh'
    command=unit_quote(survie,True)+' --work-dir '+unit_quote(app.work,True)
    lines+=[f'ExecStart={command} up',f'ExecStop={command} down','',
            '[Install]','WantedBy=default.target','']
    for line in lines:
        if any(ch in line for ch in '\r\n\x00'):raise setup.SetupError('Chemin invalide pour le service de démarrage.')
    return '\n'.join(lines)


def linger_enabled(user=None):
    user=user or getpass.getuser()
    try:value=setup.run(['loginctl','show-user',user,'-p','Linger','--value'],capture=True,timeout=30)
    except setup.SetupError:return None
    return value.strip()=='yes'


def install_autostart(app,c):
    """Install and enable the user service. Returns status lines."""
    folder=user_unit_dir();folder.mkdir(parents=True,exist_ok=True)
    target=folder/unit_name(c)
    setup.durable.write_bytes(target,unit_text(app,c).encode('utf-8'))
    systemctl('daemon-reload');systemctl('enable',unit_name(c))
    # Hand the host processes over to the service so that they survive the
    # end of this terminal or installer session.
    import control
    import discovery
    control.stop(app);discovery.stop(app)
    systemctl('restart',unit_name(c))
    status=['Démarrage automatique Linux : service utilisateur '+unit_name(c)+' activé et démarré.']
    linger=linger_enabled()
    if linger is False:
        try:setup.run(['loginctl','enable-linger',getpass.getuser()],capture=True,timeout=60);linger=linger_enabled()
        except setup.SetupError:pass
    if linger:status.append('Le service démarre avec le PC, même sans ouverture de session.')
    else:status.append('Attention : le service attend l’ouverture de session de cet utilisateur. Pour un démarrage sans session : '
                       'sudo loginctl enable-linger '+getpass.getuser()+'.')
    return status


def remove_autostart(c):
    target=user_unit_dir()/unit_name(c)
    if not target.exists():return False
    try:systemctl('disable',unit_name(c))
    except setup.SetupError:pass
    target.unlink();systemctl('daemon-reload')
    return True


def controller_reachable(app,c):
    """Check from the pilot container, as the portal does."""
    script=('import os,urllib.request,urllib.error\n'
            'try:urllib.request.urlopen(os.environ["PILOT_CONTROL_URL"]+"/",timeout=5);print("ok")\n'
            'except urllib.error.HTTPError:print("ok")\n'
            'except Exception as error:print("ko",type(error).__name__)\n')
    try:return app.compose(c,'exec','-T','pilot','python','-c',script,capture=True,timeout=60).startswith('ok')
    except (setup.SetupError,subprocess.SubprocessError):return False
