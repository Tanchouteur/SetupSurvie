"""Install a public kit with a dedicated offline Docker engine on Linux."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from delivery_paths import destination
import linux_offline_restore as system
import linux_offline_tools
import linux_recovery
import pilot_kit
import setup


def prepare_maintenance(root, base, *, point):
    tools = destination(root, linux_offline_tools.KIT_FOLDER)
    data = destination(base, 'data')
    for item in linux_offline_tools.kit_items(root):
        relative = Path(item['path']).relative_to(linux_offline_tools.KIT_FOLDER)
        linux_recovery.copy_verified(tools, data, {**item, 'path': relative.as_posix(), 'mode': 0o600},
                                     item['sha256'])
    admin = destination(base, 'application/scripts/linux_recovery_admin.sh')
    setup.run(['/bin/bash', admin, 'prepare-maintenance', base])
    if point:
        setup.run(['/bin/bash', admin, 'point', base])


def install(root, base, *, point=True):
    if setup.ROOT.resolve() != root/'app' or base.is_relative_to(root) or root.is_relative_to(base):
        raise setup.SetupError('Ouvrez le kit d’origine et choisissez un autre disque.')
    system.check_service_tree(base, directories=('outils-linux',))
    linux_offline_tools.prepare_kit(root, verify_only=True)
    name = system.service_name(base, initial=True)
    system.check_engine(name)
    job = pilot_kit.install_job(destination(base, pilot_kit.KIT_INSTALL_JOURNAL))
    unit = Path('/etc/systemd/system') / (name + '.service')
    if point and job and job['phase'] == 'complete' and unit.is_file():
        # A point being copied fences the active installation. Only its
        # maintenance launcher may release the fence.
        prepare_maintenance(root, base, point=True)
        setup.run(['systemctl', 'enable', name + '.service'])
        print('Le point de restauration est vérifié et protégé.', flush=True)
        return
    engine = name + '-docker.service'
    units = system.unit_contents(base, name, public_kit=True)
    system.publish_units(base, {engine: units[engine]})
    try:
        setup.run(['systemctl', 'start', engine])
        os.environ['DOCKER_HOST'] = f'unix:///run/{name}/docker.sock'
        system.bind_controller_to_engine()
        work = destination(base, 'private')
        pilot_kit.install(root, 'linux', destination(base, 'data'), work,
                          cpu=True, graphical=True, progress=lambda line: print(line, flush=True))
        system.check_service_tree(base)
        system.launch_services(base, name, public_kit=True)
    except (OSError, ValueError, KeyError, setup.SetupError, subprocess.SubprocessError):
        work = base/'private'
        if (work/'control-process.json').is_file():
            import control
            try:
                control.stop(setup.Installation(work))
            except (OSError, ValueError, KeyError, setup.SetupError):
                print('Vérifiez l’arrêt du contrôleur de cette copie avant de réessayer.', file=sys.stderr)
        try:
            setup.run(['systemctl', 'stop', engine])
        except setup.SetupError:
            print(f'Impossible d’arrêter le moteur de cette copie : {engine}', file=sys.stderr)
        raise
    prepare_maintenance(root, base, point=point)
    print('SetupSurvie est installé. Le SSD peut être retiré.', flush=True)


def start(base):
    system.bind_controller_to_engine()
    pilot_kit.start_installed(base)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=setup.safe_path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--kit', type=setup.safe_path)
    mode.add_argument('--demarrage', action='store_true')
    parser.add_argument('--point', choices=('yes', 'no'))
    args = parser.parse_args()
    if os.geteuid() != 0 or not Path('/run/systemd/system').is_dir():
        parser.error('Utilisez le lanceur graphique sur un Linux démarré normalement.')
    try:
        if args.demarrage:
            start(args.destination)
        else:
            install(args.kit, args.destination, point=args.point != 'no')
    except (OSError, ValueError, KeyError, setup.SetupError, subprocess.SubprocessError) as error:
        print('Installation interrompue :', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
