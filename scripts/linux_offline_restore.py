"""Activate a verified transfer on a Linux systemd machine using the bundled tools."""
import argparse
import hashlib
import ipaddress
import os
from pathlib import Path
import subprocess
import sys

import linux_host
import setup
import transfer
from delivery_paths import destination
from pilot import durable


def unit_contents(base, name, *, initial=False, public_kit=False):
    tools = base / 'outils-linux'
    engine = name + '-docker.service'
    socket = f'/run/{name}/docker.sock'
    work = base / 'private'
    engine_args = [
        tools / 'bin/dockerd', '--firewall-backend=nftables',
        '--config-file=' + str(base / 'restauration-docker.json'),
        '--host=unix://' + socket, '--data-root=' + str(base / 'stockage-docker'),
        '--exec-root=/run/' + name + '/exec', '--pidfile=/run/' + name + '/docker.pid',
    ]
    environment = linux_host.unit_quote(f'PATH={tools}/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin')
    mount = linux_host.unit_quote(base)
    engine_command = ' '.join(linux_host.unit_quote(value, True) for value in engine_args)
    common = (
        f'RequiresMountsFor={mount}\n'
        'StartLimitIntervalSec=0\n'
    )
    engine_unit = (
        '[Unit]\nDescription=Docker dédié à la restauration SetupSurvie\n' + common
        + '[Service]\nType=notify\nDelegate=yes\nRestart=on-failure\nRestartSec=10\n'
        + f'RuntimeDirectory={name}\nRuntimeDirectoryMode=0700\nEnvironment={environment}\n'
        + 'ExecStartPre=/usr/sbin/sysctl -q -w net.ipv4.ip_forward=1\n'
        + f'ExecStart={engine_command}\n'
        + '[Install]\nWantedBy=multi-user.target\n'
    )
    entrypoint = 'linux_auto_install.py' if initial else 'linux_offline_restore.py'
    app_dir = setup.ROOT
    if public_kit:
        entrypoint = 'linux_public_kit.py'
        app_dir = base / 'application'
    command = ' '.join(linux_host.unit_quote(value, True) for value in (
        tools / 'bin/python3', app_dir / 'scripts' / entrypoint, base, '--demarrage',
    ))
    stop_args = ['/bin/bash'] if public_kit else []
    stop_args.extend((app_dir / 'scripts/survie.sh', '--work-dir', work, 'down'))
    stop = ' '.join(linux_host.unit_quote(value, True) for value in stop_args)
    description = 'SetupSurvie' if initial or public_kit else 'SetupSurvie restauré hors ligne'
    app_unit = (
        f'[Unit]\nDescription={description}\nAfter={engine}\nRequires={engine}\n' + common
        + '[Service]\nType=oneshot\nRemainAfterExit=yes\nTimeoutStartSec=infinity\n'
        + f'Environment={environment}\n'
        + 'Environment=' + linux_host.unit_quote(f'DOCKER_CONFIG={tools}/docker-cli') + '\n'
        + 'Environment=' + linux_host.unit_quote('DOCKER_HOST=unix://' + socket) + '\n'
        + f'ExecStart={command}\nExecStop={stop}\n'
        + '[Install]\nWantedBy=multi-user.target\n'
    )
    return {engine: engine_unit, name + '.service': app_unit}


def publish_managed(path, content):
    if path.is_symlink() or path.exists() and (not path.is_file() or path.read_bytes() != content):
        raise setup.SetupError(f'Fichier existant différent, conservé : {path}')
    if not path.exists():
        durable.write_bytes(path, content)


def bind_controller_to_engine():
    gateways = setup.run(
        ['docker', 'network', 'inspect', 'bridge', '--format', '{{range .IPAM.Config}}{{println .Gateway}}{{end}}'],
        capture=True, timeout=20,
    ).split()
    for gateway in gateways:
        if ipaddress.ip_address(gateway).version == 4:
            os.environ['SURVIE_SYSTEM_DOCKER_GATEWAY'] = gateway
            return
    raise setup.SetupError('Le réseau interne Docker ne fournit pas de passerelle IPv4.')


def start(base):
    journal = transfer.read(base / 'transfer.json')
    phase = check_transfer(base, journal)
    bind_controller_to_engine()
    if phase in ('copied', 'adapting'):
        transfer.prepare(base)
        phase = 'prepared'
    if phase in ('prepared', 'activating'):
        transfer.activate(base)
    else:
        app = setup.Installation(base / 'private')
        app.up(app.load())


def check_transfer(base, journal):
    if (journal.get('kind'), journal.get('schema'), journal.get('target')) != (transfer.KIND, 1, 'linux'):
        raise setup.SetupError('Une copie de transfert Linux est requise.')
    if Path(journal['source']['private']).exists():
        raise setup.SetupError('Source détectée sur cette machine. Utilisez la bascule locale du transfert.')
    phase = journal['phase']
    if phase not in ('copied', 'adapting', 'prepared', 'activating', 'active'):
        raise setup.SetupError('Copie indisponible. Terminez le transfert sur la source.')
    if phase in ('active', 'activating') and journal.get('destination') != str(base):
        raise setup.SetupError('Copie déjà activée ou en cours d’activation dans un autre dossier.')
    return phase


def check_service_tree(base, *, directories=('application', 'outils-linux')):
    for parent in (base, *base.parents):
        if parent.stat().st_uid != 0 or parent.stat().st_mode & 0o022:
            raise setup.SetupError(f'Le dossier doit appartenir à root et être protégé en écriture : {parent}')
    for directory in directories:
        root = destination(base, directory)
        for path in (root, *root.rglob('*')):
            info = path.lstat()
            if path.is_symlink():
                if directory != 'outils-linux' or not path.resolve().is_relative_to(root):
                    raise setup.SetupError('Lien externe dans les fichiers du service : ' + str(path))
            elif info.st_uid != 0 or info.st_mode & 0o022:
                raise setup.SetupError('Droits insuffisamment restrictifs pour un service système : ' + str(path))


def service_name(base, *, initial=False):
    prefix = 'setupsurvie-installation-' if initial else 'setupsurvie-hors-ligne-'
    return prefix + hashlib.sha256(os.fsencode(base)).hexdigest()[:16]


def check_engine(name):
    engine = name + '-docker.service'
    status = subprocess.run(['systemctl', 'is-active', '--quiet', engine], check=False)
    if status.returncode and subprocess.run(['pgrep', '-x', 'dockerd'], stdout=subprocess.DEVNULL,
                                            check=False).returncode != 1:
        raise setup.SetupError('Un autre Docker fonctionne sur la cible. Choisissez une machine dédiée ou la bascule manuelle.')



def publish_units(base, units):
    config = destination(base, 'restauration-docker.json')
    engine_store = destination(base, 'stockage-docker')
    if not config.exists() and engine_store.exists():
        raise setup.SetupError('Stockage Docker déjà présent, laissé en place.')
    publish_managed(config, b'{}\n')
    for unit, content in units.items():
        publish_managed(Path('/etc/systemd/system') / unit, content.encode('utf-8'))
    setup.run(['systemctl', 'daemon-reload'])


def launch_services(base, name, *, initial=False, public_kit=False):
    service = name + '.service'
    engine = name + '-docker.service'
    publish_units(base, unit_contents(base, name, initial=initial, public_kit=public_kit))
    try:
        setup.run(['systemctl', 'start', service])
    except setup.SetupError as error:
        raise setup.SetupError(f'Consultez journalctl -u {engine} -u {service}, puis relancez la même commande.') from error
    setup.run(['systemctl', 'enable', service])


def install(base):
    journal = transfer.read(base / 'transfer.json')
    phase = check_transfer(base, journal)
    check_service_tree(base)
    name = service_name(base)
    check_engine(name)
    if phase in ('copied', 'adapting') or (phase == 'prepared' and journal.get('destination') != str(base)):
        transfer.prepare(base)
    launch_services(base, name)
    print('SetupSurvie restauré. Ouvrez http://127.0.0.1:8080 sur cette machine.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=setup.safe_path)
    parser.add_argument('--demarrage', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('La restauration automatique nécessite les droits administrateur.')
    if setup.ROOT.resolve() != args.destination / 'application':
        parser.error('Lancez la restauration depuis la copie.')
    try:
        (start if args.demarrage else install)(args.destination)
    except (OSError, ValueError, KeyError, setup.SetupError, subprocess.SubprocessError) as error:
        print('Restauration interrompue :', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
