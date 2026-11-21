"""Offline install and immutable recovery point for a dedicated Linux machine."""
import argparse
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import uuid

from delivery_paths import destination, locked
import linux_offline_restore as system
from pilot import durable
import setup
import transfer


def phase(message):
    print(message, flush=True)


def transfer_manifest(source):
    journal = transfer.read(destination(source, 'transfer.json'))
    valid = (transfer.KIND, 1, 'linux', 'copied')
    if tuple(journal.get(key) for key in ('kind', 'schema', 'target', 'phase')) != valid:
        raise setup.SetupError('Le SSD doit contenir une copie Linux vérifiée et jamais activée.')
    if not journal.get('images_sha256') or not journal.get('images_manifest_sha256'):
        raise setup.SetupError('Images Docker absentes de la copie.')
    inventory = journal['inventory']
    files = [record['path'] for record in inventory['files']]
    essentials = {'application/compose.yaml', 'application/deploy/release.json',
                  'application/scripts/restaurer-linux-hors-ligne.sh', 'private/settings.json'}
    if len(files) != len(set(files)) or not essentials.issubset(files):
        raise setup.SetupError('Inventaire incomplet ou noms de fichiers en double.')
    return journal


def walk_bottom_up(root):
    def unreadable(error):
        raise error
    return os.walk(root, topdown=False, onerror=unreadable)


def protected_tree(root):
    """Each directory and regular file must be immutable, including for root writes."""
    for directory, directories, files in walk_bottom_up(root):
        for path in [*(Path(directory) / name for name in files), Path(directory)]:
            if path.is_symlink():
                continue
            info = path.stat()
            if info.st_uid != 0 or info.st_mode & 0o022 or not immutable(path):
                raise setup.SetupError('Point de restauration non protégé ou incomplet.')
        if any((Path(directory) / name).is_symlink() for name in directories):
            raise setup.SetupError('Lien de répertoire dans le point de restauration.')


def immutable(path):
    # FS_IOC_GETFLAGS on supported Linux x86-64, FS_IMMUTABLE_FL.
    with_flags = bytearray(8)
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        fcntl.ioctl(descriptor, 0x80086601, with_flags, True)
        return bool(struct.unpack_from('I', with_flags)[0] & 0x10)
    finally:
        os.close(descriptor)


def seal(root):
    for directory, _, files in walk_bottom_up(root):
        paths = [Path(directory) / name for name in files] + [Path(directory)]
        changes = []
        for path in paths:
            if path.is_symlink() or immutable(path):
                continue
            path.chmod(stat.S_IMODE(path.stat().st_mode) & ~0o222)
            changes.append(path)
        for index in range(0, len(changes), 128):
            setup.run(['chattr', '+i', *changes[index:index + 128]])
    protected_tree(root)


def check_sealing(recovery):
    probe = destination(recovery, 'test-protection')
    sealed = False
    try:
        if not probe.exists():
            durable.write_bytes(probe, b'')
        setup.run(['chattr', '+i', probe], capture=True)
        sealed = immutable(probe)
        if not sealed:
            raise setup.SetupError('Le disque ne protège pas le point de restauration.')
    except (OSError, setup.SetupError) as error:
        raise setup.SetupError(
            'Choisissez un disque Linux qui prend en charge les fichiers immuables, par exemple ext4.') from error
    finally:
        if probe.exists():
            if sealed:
                setup.run(['chattr', '-i', probe])
            probe.unlink()


IMAGE_ARCHIVES = (('images.tar', 'images_sha256'), ('images.tar.json', 'images_manifest_sha256'))
COPY_MARGIN = 256 * 1024**2


def remaining_bytes(source, target, journal):
    amounts = [(record['path'], record['bytes']) for record in journal['inventory']['files']]
    amounts.extend((name, destination(source, name).stat().st_size) for name, _ in IMAGE_ARCHIVES)
    return sum(max(0, size - partial_size(target, name)) for name, size in amounts)


def require_space(source, targets, journal):
    needed = sum(remaining_bytes(source, target, journal) for target in targets)
    docker = destination(source, 'images.tar').stat().st_size * 2
    if shutil.disk_usage(targets[0].parent).free < needed + docker + COPY_MARGIN:
        raise setup.SetupError('Place insuffisante pour les copies et la réinstallation des images Docker.')


def copy_payload(source, target, journal):
    """Copy only verified entries and re-create the allowed Ollama manifest links."""
    inventory = journal['inventory']
    transfer.manifest_links(source, inventory)
    records = inventory['files']
    if shutil.disk_usage(target.parent).free < remaining_bytes(source, target, journal) + COPY_MARGIN:
        raise setup.SetupError('Espace insuffisant pour copier les fichiers et les images Docker.')
    for folder in inventory['directories']:
        durable.mkdir(destination(target, folder))
    for number, record in enumerate(records, 1):
        relative = record['path']
        if number == 1 or number % 100 == 0:
            phase(f'Copie vérifiée : {number} / {len(records)} fichiers…')
        copy_verified(source, target, record, journal['verified'][relative])
    for name, key in IMAGE_ARCHIVES:
        info = destination(source, name).stat()
        copy_verified(source, target, {'path': name, 'bytes': info.st_size,
                                      'mtime_ns': info.st_mtime_ns, 'mode': 0o600}, journal[key])
    transfer.manifest_links(target, inventory, publish=True)
    transfer.restore_directory_modes(target, inventory)


def partial_size(target, relative):
    path = destination(target, relative)
    partial = path.with_name(path.name + '.transfer-part')
    return path.stat().st_size if path.is_file() else (
        partial.stat().st_size if not partial.is_symlink() and partial.is_file() else 0)


def copy_verified(source, target, record, expected):
    relative = record['path']
    original, copy = destination(source, relative), destination(target, relative)
    info = original.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size != record['bytes']:
        raise setup.SetupError('Fichier de secours absent ou incomplet : ' + relative)
    # Support filesystem timestamp precision can differ from that on the source.
    metadata = {**record, 'mtime_ns': info.st_mtime_ns}
    reported = 0
    def show_large_copy(operation, count, total):
        nonlocal reported
        if operation != 'Copie':
            return
        gibibytes = count // (1024 ** 3)
        if gibibytes > reported:
            reported = gibibytes
            phase(f'Copie en cours : {gibibytes} Gio sur {total / (1024 ** 3):.1f} Gio pour le fichier courant.')
    actual = transfer.copy_file(original, copy, metadata, show_large_copy)
    if actual != expected:
        raise setup.SetupError('Fichier de secours altéré : ' + relative)
    copy.chmod(record['mode'] & ~0o022)


def fill_target(source, target, journal, *, detached=False, portable_cpu=False):
    marker = target / '.copie-installation.json'
    identity = {'id': journal['id'], 'source': str(source)}
    if target.exists():
        if not marker.is_file() or transfer.read(marker) != identity:
            raise setup.SetupError('Dossier déjà utilisé. Choisissez une destination dédiée.')
    else:
        with tempfile.TemporaryDirectory(prefix='.copie-nouvelle-', dir=target.parent) as pending:
            empty = Path(pending)
            setup.write_json(empty / marker.name, identity, private=True)
            setup.run(['mv', '-T', '--no-clobber', empty, target])
            if empty.exists():
                raise setup.SetupError('Le dossier de destination est apparu pendant la préparation.')
            durable.sync_directory(target.parent)
    if (target / 'transfer.json').exists():
        local = transfer.read(target / 'transfer.json')
        if local.get('id') != journal['id']:
            raise setup.SetupError('La copie présente correspond à un autre support.')
        return
    copy_payload(source, target, journal)
    local = deepcopy(journal)
    if portable_cpu:
        local['linux_portable_cpu'] = True
    if detached:
        # Keep the real original paths for metadata substitution, never for a same-PC cutover.
        for role, path in local['source'].items():
            local.setdefault('source_aliases', {}).setdefault(role, path)
        local['source'] = {role: str(target.parent / '.source-absente' / role)
                           for role in local['source']}
    transfer.save(target, local)
    transfer.verify_copy(target)


def point_path(recovery):
    return destination(recovery, 'point')


def seal_point(point, journal):
    receipt = point / 'point-de-restauration.json'
    if not receipt.is_file():
        transfer.verify_copy(point)
        setup.write_json(receipt, {'schema': 1, 'transfer': journal['id'],
                                   'version': journal['release']['version'],
                                   'manifest_sha256': setup.file_hash(point / 'transfer.json')},
                         private=True)
    seal(point)
    durable.sync_directory(point.parent)


def read_point(point):
    if not point.is_dir():
        raise setup.SetupError('Aucun point de restauration disponible.')
    protected_tree(point)
    receipt = transfer.read(point / 'point-de-restauration.json')
    journal = transfer_manifest(point)
    if (receipt.get('schema') != 1 or receipt.get('transfer') != journal['id']
            or receipt.get('manifest_sha256') != setup.file_hash(point / 'transfer.json')):
        raise setup.SetupError('Le manifeste du point de restauration a changé.')
    return journal


def mark_ready(recovery, point):
    receipt = {'manifest_sha256': setup.file_hash(point / 'transfer.json')}
    setup.write_json(recovery / 'point-verifie.json', receipt, private=True)


def require_ready(recovery, point):
    receipt = recovery / 'point-verifie.json'
    if (not receipt.is_file() or transfer.read(receipt).get('manifest_sha256')
            != setup.file_hash(point / 'transfer.json')):
        raise setup.SetupError('La création du point n’est pas terminée. Reprenez l’installation ou la création du point.')


def activate(base):
    journal = transfer.read(base / 'transfer.json')
    if journal['phase'] != 'active':
        script = destination(base, 'application/scripts/restaurer-linux-hors-ligne.sh')
        phase('Installation des outils et démarrage de SetupSurvie…')
        # The maintenance tools can include nft. Only the system PATH tells
        # the nested bootstrap whether its own service needs a bundled copy.
        env = {**os.environ, 'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'}
        setup.run(['/bin/bash', script, base], env=env)
    # Enabling the unit can have failed after the transfer became active.
    unit = system.service_name(base) + '.service'
    setup.run(['systemctl', 'start', unit])
    setup.run(['systemctl', 'enable', unit])
    setup.Installation(base / 'private').request('http://127.0.0.1:8080/api/health')


def install(recovery, source, base, create_point):
    journal = transfer_manifest(source)
    specification = {'operation': 'install', 'source': str(source), 'id': journal['id'], 'point': create_point}
    state = recovery / 'installation.json'
    if state.exists() and transfer.read(state) != specification:
        raise setup.SetupError('Reprenez avec le même SSD et le même choix de point de restauration.')
    if base.exists() and not (base / '.copie-installation.json').is_file():
        raise setup.SetupError('Le dossier choisi contient déjà une installation ou des fichiers.')
    active_manifest = base / 'transfer.json'
    if not active_manifest.is_file() or transfer.read(active_manifest).get('phase') != 'active':
        targets = [base, point_path(recovery)] if create_point else [base]
        require_space(source, targets, journal)
    if not state.exists():
        setup.write_json(state, specification, private=True)
    install_shortcut(recovery, base)
    if create_point:
        point = point_path(recovery)
        if not (point / 'point-de-restauration.json').is_file():
            check_sealing(recovery)
        if not (point / 'point-de-restauration.json').is_file():
            fill_target(source, point, journal)
        phase('Protection du point de restauration…')
        seal_point(point, journal)
        source, journal = point, read_point(point)
    phase('Préparation de la copie de travail…')
    fill_target(source, base, journal, portable_cpu=True)
    activate(base)
    if create_point:
        mark_ready(recovery, point)


def managed_unit(base):
    for initial in (False, True):
        name = system.service_name(base, initial=initial)
        if (Path('/etc/systemd/system') / (name + '.service')).is_file():
            return name
    raise setup.SetupError('Ce raccourci prend en charge les installations Linux système dédiées.')


def create_existing_point(recovery, base):
    if (recovery / 'remplacement.json').exists():
        raise setup.SetupError('Reprenez la restauration en cours avant de créer un point.')
    point = point_path(recovery)
    if point.is_dir() and (point / 'point-de-restauration.json').is_file() and immutable(point):
        read_point(point)
        if not (recovery / 'point-verifie.json').is_file():
            release_current_source(base, point, managed_unit(base))
            mark_ready(recovery, point)
        phase('Le point de restauration existant est déjà protégé.')
        return
    unit = managed_unit(base)
    app = destination(base, 'application')
    work = setup.Installation(base / 'private')
    validate_local_layout(base, work.load())
    if not point.exists():
        check_sealing(recovery)
    if not (point / 'transfer.json').is_file() or transfer.read(point / 'transfer.json')['phase'] != 'copied':
        phase('Préparation du point depuis l’installation actuelle. Le portail sera indisponible pendant la copie.')
        env = {**os.environ, 'DOCKER_HOST': f'unix:///run/{unit}/docker.sock',
               'SURVIE_MAINTENANCE_SITE': '0'}
        setup.run(['systemctl', 'start', unit + '-docker.service'])
        setup.run(['systemctl', 'stop', unit + '.service'])
        try:
            setup.run([sys.executable, app / 'scripts/transfer.py', 'copy', point,
                       '--work-dir', base / 'private'], env=env)
        finally:
            release_current_source(base, point, unit)
    else:
        release_current_source(base, point, unit)
    seal_point(point, transfer_manifest(point))
    mark_ready(recovery, point)
    install_shortcut(recovery, base)


def release_current_source(base, point, unit):
    work = base / 'private'
    with locked(work / 'update.lock'), locked(work / 'transfer.lock'):
        guard = work / 'transfer-guard.json'
        if guard.is_file():
            journal = transfer.read(point / 'transfer.json')
            if transfer.read(guard).get('id') != journal.get('id'):
                raise setup.SetupError('Un transfert différent protège l’installation.')
            if journal.get('phase') != 'copied':
                # Keep an interrupted point and the source fence so the exact copy can resume.
                raise setup.SetupError('Copie interrompue. Rouvrez l’assistant et relancez la création du point.')
            guard.unlink()
            durable.sync_directory(work)
    setup.run(['systemctl', 'start', unit + '.service'])


def validate_local_layout(base, config):
    if (config.get('target') != 'linux'
            or config.get('app_dir') != str(base / 'application')
            or config.get('data_dir') != str(base / 'data')
            or (base / 'data').is_mount()):
        raise setup.SetupError('Cette installation possède des dossiers séparés. Le point automatique exige un dossier système dédié.')


def restore(recovery, base):
    point = point_path(recovery)
    journal = read_point(point)
    require_ready(recovery, point)
    state_path = recovery / 'remplacement.json'
    if state_path.exists():
        state = transfer.read(state_path)
    else:
        unit = managed_unit(base)
        state = {'id': uuid.uuid4().hex, 'unit': unit}
        setup.write_json(state_path, state, private=True)
    suffix = state['id']
    if len(suffix) != 32 or any(c not in '0123456789abcdef' for c in suffix):
        raise setup.SetupError('Journal de remplacement invalide.')
    saved = destination(recovery, 'ancienne-installation-' + suffix)
    staged = destination(recovery, 'nouvelle-copie-' + suffix)
    if not saved.exists():
        for name in ('.', 'data', 'private', 'application', 'stockage-docker'):
            if (base / name).is_mount():
                raise setup.SetupError('Un dossier de l’installation est un point de montage. Aucune bascule effectuée.')
        require_space(point, [staged], journal)
        phase('Vérification et copie du point protégé…')
        fill_target(point, staged, journal, detached=True, portable_cpu=True)
        transfer.verify_copy(staged)
        work = destination(base, 'private')
        with locked(work / 'update.lock'), locked(work / 'transfer.lock'), locked(base / 'operation.lock'):
            archive_active(base, saved, state['unit'])
    if not base.exists():
        os.rename(staged, base)
        durable.sync_directory(recovery)
        durable.sync_directory(base.parent)
    activate(base)
    state_path.unlink()
    durable.sync_directory(recovery)
    phase('L’ancienne installation a été conservée dans le dossier de secours : ' + str(saved))


def archive_active(base, saved, unit):
    phase('Mise à l’abri de l’ancienne installation, données comprises…')
    if unit != managed_unit(base):
        raise setup.SetupError('Le service SetupSurvie a changé pendant la préparation.')
    setup.run(['systemctl', 'disable', unit + '.service'])
    # ExecStop can be damaged along with the old installation. Stop its
    # dedicated daemon anyway and require that both units are inactive.
    subprocess.run(['systemctl', 'stop', unit + '.service'], check=False)
    setup.run(['systemctl', 'stop', unit + '-docker.service'])
    for service in (unit + '.service', unit + '-docker.service'):
        result = subprocess.run(['systemctl', 'is-active', '--quiet', service], check=False)
        if result.returncode != 3:
            raise setup.SetupError('Impossible de confirmer l’arrêt de ' + service)
    os.rename(base, saved)
    durable.sync_directory(base.parent)
    durable.sync_directory(saved.parent)


def install_shortcut(recovery, base):
    # The launcher lives outside the replaced active installation.
    gui = recovery / 'entretien/application/scripts/linux_recovery_gui.sh'
    bridge = Path('/usr/local/bin') / (system.service_name(base) + '-entretien')
    # Only pinned launcher code is exposed. Private recovery files stay inaccessible.
    scripts = Path('/usr/local/share') / (bridge.name + '-interface')
    if scripts.is_symlink() or scripts.exists() and (
            scripts.stat().st_uid != 0 or scripts.stat().st_mode & 0o022):
        raise setup.SetupError('Dossier de raccourci existant non protégé.')
    scripts.mkdir(parents=True, mode=0o755, exist_ok=True)
    scripts.chmod(0o755)
    durable.write_bytes(scripts / gui.name, gui.read_bytes())
    admin = scripts / 'linux_recovery_admin.sh'
    durable.write_bytes(admin, gui.with_name(admin.name).read_bytes())
    # The admin wrapper finds the protected runtime from the active installation path.
    body = ('#!/bin/sh\nexec /bin/bash ' + shlex.quote(str(scripts / gui.name))
            + ' maintenance ' + shlex.quote(str(base)) + '\n')
    durable.write_bytes(bridge, body.encode())
    bridge.chmod(0o755)
    shortcut = Path('/usr/local/share/applications') / (bridge.name + '.desktop')
    durable.write_bytes(shortcut, ('[Desktop Entry]\nType=Application\nName=Entretien de SetupSurvie\n'
                                   f'Exec={bridge}\nTerminal=false\nCategories=Utility;\n').encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recovery', type=Path)
    actions = parser.add_subparsers(dest='action', required=True)
    installer = actions.add_parser('install')
    installer.add_argument('source', type=setup.safe_path)
    installer.add_argument('base', type=setup.safe_path)
    installer.add_argument('point', choices=('yes', 'no'))
    for name in ('point', 'restore'):
        actions.add_parser(name).add_argument('base', type=setup.safe_path)
    args = parser.parse_args()
    try:
        if args.action == 'install':
            install(args.recovery, args.source, args.base, args.point == 'yes')
        elif args.action == 'point':
            create_existing_point(args.recovery, args.base)
        else:
            restore(args.recovery, args.base)
    except (OSError, ValueError, KeyError, TypeError, setup.SetupError, subprocess.SubprocessError) as error:
        print('Opération interrompue :', error, file=sys.stderr)
        return 1
    phase('Opération terminée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
