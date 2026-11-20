"""Manage a new Linux installation, including recovery after interruption."""
import argparse
import os
import socket
import subprocess
import sys

import content
import json
from delivery_paths import destination
import linux_offline_restore as system
import setup
from pilot import durable


def installation_plan(base, packs):
    available = {item['pack'] for item in content.catalog()}
    unknown = set(packs) - available
    if unknown:
        raise setup.SetupError('Lots documentaires inconnus : ' + ', '.join(sorted(unknown)))
    plan = {'schema': 1, 'packs': sorted(set(packs)), 'mode': 'cpu'}
    path = destination(base, 'installation-linux.json')
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != plan:
            raise setup.SetupError('Relancez avec les mêmes lots documentaires que lors du premier lancement.')
    else:
        setup.write_json(path, plan, private=True)
    return plan


def start(base):
    work = destination(base, 'private')
    data = destination(base, 'data')
    path = destination(base, 'installation-linux.json')
    plan = json.loads(path.read_text(encoding='utf-8'))
    completion = destination(work, 'installation-linux-terminee')
    app = setup.Installation(work)
    system.bind_controller_to_engine()
    if completion.is_file():
        app.up(app.load())
        return
    if not app.settings_path.exists():
        for port in (8080, 8081, 3000, 8443, 8444, 8445, 11435, 11436):
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', port)) == 0:
                    raise setup.SetupError(f'Port {port} occupé. Libérez-le avant de relancer.')
    arguments = ['--work-dir', str(work), 'install', '--target', 'linux', '--cpu',
                 '--no-startup', '--data-dir', str(data)]
    for pack in plan['packs']:
        arguments.extend(('--content-pack', pack))
    setup.main(arguments)
    config = app.load()
    config['app_dir'] = str(setup.ROOT)
    setup.write_json(app.settings_path, config, private=True)
    durable.write_bytes(completion, b'Installation initiale terminee.\n', private=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=setup.safe_path)
    parser.add_argument('--content-pack', action='append', default=[])
    parser.add_argument('--demarrage', action='store_true')
    args = parser.parse_args()
    base = args.destination
    if os.geteuid() != 0 or setup.ROOT.resolve() != base / 'application':
        parser.error('Exécutez le lanceur administrateur depuis le dossier préparé.')
    try:
        if args.demarrage:
            start(base)
        else:
            system.check_service_tree(base)
            name = system.service_name(base, initial=True)
            system.check_engine(name)
            installation_plan(base, args.content_pack)
            system.launch_services(base, name, initial=True)
            print('SetupSurvie est installé. Ouvrez http://127.0.0.1:8080 sur cette machine.')
    except (OSError, ValueError, KeyError, setup.SetupError, subprocess.SubprocessError) as error:
        print('Installation interrompue :', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
