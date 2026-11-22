#!/usr/bin/env python3
"""Stopped-service user snapshot, complementary to the immutable public pilot kit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path
import shutil
import secrets
import socket
import sys
import time

import setup
import index_locks
from pilot import durable
from delivery_paths import destination as checked_destination,locked

RESTORE_JOURNAL = 'restauration.json'
RESTORE_PHASES = ('copying', 'activating', 'complete')
PRIVATE_FILES=('settings.json','identifiants.txt','inference-paused.json')
PRIVATE_DATA=('data/state/pilot/','data/state/openwebui/','data/state/caddy/','data/library/guides/')
PRIVATE_CATALOG=('data/catalog/downloaded-content.json','data/catalog/collection-sort.json')
# Rebuilt from the ZIM archives without Internet or AI; often hundreds of GB.
REBUILDABLE=(('state','pilot','category-index'),)


def rebuildable(relative):
    """True for derived state that backups skip and restorations keep in place."""
    parts=Path(relative).parts
    return any(parts[:len(prefix)]==prefix for prefix in REBUILDABLE)


def separate_roots(*roots):
    for number,path in enumerate(roots):
        for other in roots[:number]:
            if path==other or path.is_relative_to(other) or other.is_relative_to(path):
                raise setup.SetupError('Sauvegarde, kit, données, application et réglages doivent être dans des dossiers séparés sans chevauchement.')


def backup(app,c,destination,*,resume=True):
    with maintenance(app,c):
        return stopped_backup(app,c,destination,resume=resume,identity=backup_identity(c))


@contextmanager
def maintenance(app,c,*,pause_video_inventory=False):
    """Exclude web jobs, CLI transfers and index writers throughout maintenance."""
    with locked(checked_destination(app.work,'library-web/operation.lock')):
        state=checked_destination(app.work,'library-web/state.json')
        if state.is_file():
            from library_tasks import ACTIVE, Manager
            job = json.loads(state.read_text(encoding='utf-8'))
            if pause_video_inventory and job.get('action') == 'video-inventory' and job.get('phase') in ACTIVE:
                manager = Manager(app,c,'compose')
                job = manager.current()
                if job['phase'] in ('starting','planning','downloading'):
                    print('Inventaire vidéo en cours : demande de pause. Les résultats et le point de reprise sont conservés.',flush=True)
                    manager.pause(state=job)
                    deadline = time.monotonic()+60
                    while job['phase'] in ACTIVE and time.monotonic()<deadline:
                        time.sleep(.25)
                        job = manager.current()
            if job.get('phase') in ACTIVE:
                raise setup.SetupError('Une préparation documentaire est encore active. Mettez-la en pause depuis Mon appareil et attendez son arrêt avant de réessayer.')
        data=Path(c['data_dir'])
        with locked(checked_destination(data,'catalog/publication.lock')),locked(checked_destination(data,'catalog/content.lock')),index_locks.stopped(checked_destination(data,'state/pilot/archive-index')),locked(checked_destination(data,'state/pilot/zim-videos/operation.lock')):
            yield


def copy_snapshot_file(source, target, relative):
    shutil.copyfile(source, target)
    target.chmod(0o600)
    digest = setup.file_hash(target)
    durable.sync_file(target)
    return {'path': relative, 'bytes': target.stat().st_size, 'sha256': digest}


def restore_identity(release, versions):
    # Open WebUI owns a separate database schema from the SetupSurvie pilot.
    identity = {key: release[key] for key in ('version', 'data_schema')}
    identity['open_webui'] = versions['images']['open-webui']
    return identity


def backup_identity(config):
    root = Path(config.get('app_dir') or setup.ROOT)
    release = root/'deploy/release.json'
    versions = root/'deploy/versions.json'
    if not release.is_file() or not versions.is_file():
        return None
    try:
        return restore_identity(json.loads(release.read_text(encoding='utf-8')),
                                json.loads(versions.read_text(encoding='utf-8')))
    except (OSError, ValueError, KeyError, TypeError):
        # Keep the same-system backup usable when version files are incomplete.
        return None


def host_target():
    return {'win32': 'windows', 'linux': 'linux'}.get(sys.platform)


def portable_settings(saved, target):
    saved['target'] = target
    saved['cpu'] = saved['target'] == 'linux'
    saved['bind'] = '127.0.0.1'
    for key in ('lan_host', 'docker_rootless', 'routing_image', 'inference_autostart'):
        saved.pop(key, None)


def validate_portable_restore(report, kit, public, public_entries, source_target):
    from kit_audit import validate
    if source_target not in ('windows', 'linux'):
        raise setup.SetupError('Système de la sauvegarde inconnu.')
    identity = report.get('installation')
    if report.get('schema') != 1 or not identity:
        raise setup.SetupError('Version de sauvegarde inconnue. Créez une nouvelle sauvegarde depuis l’installation d’origine.')
    paths = {entry['path']: path for entry, path in public_entries}
    release = paths.get('app/deploy/release.json')
    versions = paths.get('app/deploy/versions.json')
    if not release or not versions:
        raise setup.SetupError('Version et composants du kit manquants.')
    version_data = json.loads(versions.read_text(encoding='utf-8'))
    expected = restore_identity(json.loads(release.read_text(encoding='utf-8')), version_data)
    if identity != expected:
        raise setup.SetupError('Kit incompatible avec la sauvegarde. Choisissez un kit de la même version et avec la même image Open WebUI.')
    validate(kit, public)
    return version_data


def check_portable_layout(files):
    # Windows folds case even when Linux can distinguish two names, including
    # directory names. Check the merged tree before creating any destination.
    tree = {}
    for file in files:
        for path in (file, *file.parents):
            key = path.as_posix().casefold()
            value = (path.as_posix(), path == file)
            if tree.setdefault(key, value) != value:
                raise setup.SetupError('Conflit de noms entre le kit et la sauvegarde : '+path.as_posix())


def portable_restore_preflight(copies, *, activating=False):
    # Sum space needed for all destinations on a shared filesystem. On Windows
    # st_dev is not reliable across drives, so use the nearest existing drive.
    volumes = {}
    for target, size in copies:
        ancestor = target.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        volume = ancestor.drive.casefold() if os.name == 'nt' else ancestor.stat().st_dev
        previous, _ = volumes.get(volume, (0, ancestor))
        volumes[volume] = (previous + size, ancestor)
    for size, ancestor in volumes.values():
        if shutil.disk_usage(ancestor).free < size + 20 * 1024**3:
            raise setup.SetupError('Espace insuffisant sur le disque de destination : '+str(ancestor))
    ports = () if activating else (8080, 8081, 3000, 8443, 8444, 8445, 11435, 11436)
    for port in ports:
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise setup.SetupError(f'Port {port} occupé. Arrêtez l’ancienne installation ou choisissez un autre ordinateur.')
    setup.run(['docker', 'compose', 'version'], capture=True, timeout=30)
    if setup.run(['docker', 'info', '--format', '{{.OSType}}'], capture=True, timeout=30) != 'linux':
        raise setup.SetupError('Docker doit utiliser les conteneurs Linux.')


def restore_copy(entry, source, target, *, verify=False):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if entry['path'].startswith('app/'):
        if os.name != 'nt':
            target.chmod((source.stat().st_mode & 0o755) | 0o600)
    elif entry['path'].startswith(('private/', 'data/')):
        target.chmod(0o600)
    if verify and (target.stat().st_size != entry['bytes'] or setup.file_hash(target) != entry['sha256']):
        raise setup.SetupError('Copie non conforme sur la destination : '+entry['path'])


def stopped_backup(app,c,destination,*,resume=True,services_stopped=False,progress=None,identity=None):
    data=Path(c['data_dir']);dest=setup.safe_path(destination)
    if dest.exists() or dest.is_relative_to(data) or dest.is_relative_to(app.work):
        raise setup.SetupError('Choisissez une nouvelle destination hors des données et des réglages.')
    durable.mkdir(dest);dest.chmod(0o700)
    try:
        if not services_stopped:
            app.compose(c,'stop','portal','pilot','open-webui')
        sources=[(checked_destination(app.work,name),'private/'+name) for name in PRIVATE_FILES]
        receipt=checked_destination(data,'catalog/downloaded-content.json')
        sources.append((receipt,'data/catalog/downloaded-content.json'))
        sources.append((checked_destination(data,'catalog/collection-sort.json'),'data/catalog/collection-sort.json'))
        for name in ['state/pilot','state/openwebui','state/caddy','library/guides']:
            for path in sorted((data/name).rglob('*')):
                relative=path.relative_to(data)
                if 'cache' in relative.parts or rebuildable(relative) or path.name.endswith('-shm') or relative.parts[0]=='state' and path.name.endswith('.lease'):continue
                if path.is_symlink():raise setup.SetupError('Lien refusé dans la sauvegarde : '+relative.as_posix())
                if path.is_file():sources.append((path,'data/'+relative.as_posix()))
        sources = [(source, relative) for source, relative in sources if source.exists()]
        data_root = data.resolve()
        private_sources = {app.work/name for name in PRIVATE_FILES}

        def copy_entry(entry):
            source, relative = entry
            if source.is_symlink() or (source not in private_sources and not source.resolve().is_relative_to(data_root)):
                raise setup.SetupError('Lien ou chemin externe refusé dans la sauvegarde.')
            return copy_snapshot_file(source, checked_destination(dest, relative), relative)

        seen = set()
        prepared = set()
        for _, relative in sources:
            if relative.casefold() in seen:
                raise setup.SetupError('Chemin dupliqué ou ambigu dans la sauvegarde : '+relative)
            seen.add(relative.casefold())
            parent = relative.rsplit('/', 1)[0]
            if parent not in prepared:
                checked_destination(dest, parent).mkdir(parents=True, exist_ok=True)
                prepared.add(parent)
        total = len(sources)
        last_report = time.monotonic()
        if progress:
            progress(0, total)
        files = []

        def collect(records):
            nonlocal last_report
            for record in records:
                files.append(record)
                now = time.monotonic()
                if progress and (now-last_report >= 2 or len(files) == total):
                    progress(len(files), total)
                    last_report = now

        if os.name == 'nt':
            # Bound queued copies and wait for in-flight writes before returning on error.
            with ThreadPoolExecutor(max_workers=4) as workers:
                for index in range(0, total, 128):
                    collect(workers.map(copy_entry, sources[index:index+128]))
        else:
            collect(map(copy_entry, sources))
            durable.sync_tree(dest, sync_files=False)
        report = {'schema': 1, 'files': files}
        if identity is not None:
            report['installation'] = identity
        setup.write_json(dest/'backup.json', report, private=True)
    finally:
        if resume:app.compose(c,'start','open-webui','pilot','portal')
    print('Sauvegarde privée créée :',dest)


def restore_inputs(source, kit, target):
    return {
        'backup': setup.file_hash(checked_destination(source, 'backup.json')),
        'kit': setup.file_hash(checked_destination(kit, 'manifest.json')),
        'target': target,
    }


def read_restore_job(path):
    if path.is_symlink():
        raise setup.SetupError('Lien de journal de restauration refusé.')
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(record, dict) or record.get('schema') != 1
            or record.get('phase') not in RESTORE_PHASES
            or not isinstance(record.get('project'), str)
            or not record['project'].startswith('survie-restored-')):
        raise setup.SetupError('Dossier de restauration non reconnu. Choisissez une destination vide.')
    return record


def verified_copy(entry, target):
    if not target.is_file():
        return False
    info = target.stat()
    return (info.st_nlink == 1 and info.st_size == entry['bytes']
            and setup.file_hash(target) == entry['sha256'])


def checked_destination_for_copy(entry, target, work, data, application):
    root = {'app': application, 'data': data, 'payload': data, 'private': work}[entry['path'].split('/')[0]]
    checked_destination(root, target.relative_to(root).as_posix())


def restore(source,kit,work_dir,data_dir,*,target=None,progress=None,resume=False):
    from pilot_kit import checked_entries
    source=setup.safe_path(source);kit=setup.safe_path(kit);data=setup.safe_path(data_dir);work=setup.safe_path(work_dir)
    application=work.parent/'application'
    separate_roots(source,kit,data,work,application)
    if target is not None and (target not in ('windows', 'linux') or target != host_target()):
        raise setup.SetupError('Le système demandé doit être celui de cet ordinateur.')
    portable = target is not None
    if resume and not portable:
        raise setup.SetupError('Précisez le système avec --target pour poursuivre la restauration.')
    journal = None
    job = None
    if portable:
        journal = checked_destination(work.parent, RESTORE_JOURNAL)
        separate_roots(source, kit, journal, work, data, application)
        job = read_restore_job(journal)
        if resume != (job is not None):
            raise setup.SetupError('Reprenez la restauration existante ou choisissez un nouveau dossier.')
        if job and job['phase'] == 'complete':
            raise setup.SetupError('Cette restauration est déjà terminée. Ouvrez l’installation restaurée.')
    if not job:
        for dest in (data, work, application):
            if dest.exists() and (dest == application or not dest.is_dir() or any(dest.iterdir())):
                raise setup.SetupError('Restauration uniquement vers des dossiers vides.')
    inputs = restore_inputs(source, kit, target) if portable else None
    paths = {'work': work.as_posix(), 'data': data.as_posix()}
    if job and (job.get('inputs') != inputs or job.get('paths') != paths):
        raise setup.SetupError('Cette restauration a commencé avec une autre sauvegarde, un autre kit ou une autre destination.')
    report=json.loads((source/'backup.json').read_text(encoding='utf-8'));entries=checked_entries(source,report)
    allowed_private={'private/'+name for name in PRIVATE_FILES}
    for entry,_ in entries:
        relative=entry['path']
        if relative not in allowed_private and relative not in PRIVATE_CATALOG and not relative.startswith(('data/state/','data/library/guides/')):
            raise setup.SetupError('Fichier de sauvegarde hors périmètre : '+relative)
    settings=next((path for entry,path in entries if entry['path']=='private/settings.json'),None)
    if settings is None:raise setup.SetupError('Réglages absents du manifeste de sauvegarde.')
    saved=json.loads(settings.read_text(encoding='utf-8'))
    host = host_target()
    if target is None and host is not None and saved['target'] != host:
        raise setup.SetupError('Sauvegarde d’un autre système. Indiquez --target linux ou --target windows sur la machine cible.')
    if progress:
        progress('Vérification du kit hors ligne…')
    public=json.loads((kit/'manifest.json').read_text(encoding='utf-8'));public_entries=checked_entries(kit,public)
    versions = setup.VERSIONS
    if portable:
        versions = validate_portable_restore(report, kit, public, public_entries, saved['target'])
        for entry, _ in entries:
            relative = entry['path']
            if relative.startswith('data/state/') and not relative.startswith(PRIVATE_DATA):
                raise setup.SetupError('Données du système source inconnues : '+relative)
        entries = [(entry, path) for entry, path in entries if not entry['path'].startswith('data/state/caddy/')]
        portable_settings(saved, target)
    saved['data_dir']=data.as_posix()
    saved['app_dir']=application.as_posix()
    saved['project'] = job['project'] if job else 'survie-restored-'+secrets.token_hex(4)
    # An image ID is platform-local; it is re-imported and verified below.
    saved.pop('local_images',None)
    copies = []
    for entry, path in entries:
        relative = entry['path']
        if relative.startswith('data/state/') and relative.endswith('.lease'):
            continue
        if relative.startswith('data/'):
            dest = data/Path(relative).relative_to('data')
        elif relative in allowed_private-{'private/settings.json'}:
            dest = work/Path(relative).relative_to('private')
        else:
            continue
        copies.append((entry, path, dest))
    private_destinations = {dest for _, _, dest in copies}
    if portable:
        data_paths = [dest.relative_to(data) for dest in private_destinations if dest.is_relative_to(data)]
        data_paths.extend(Path(entry['path']).relative_to('payload') for entry, _ in public_entries if entry['path'].startswith('payload/'))
        check_portable_layout(data_paths)
    for entry, path in public_entries:
        relative = entry['path']
        if relative.startswith('app/'):
            dest = application/Path(relative).relative_to('app')
        elif relative.startswith('payload/'):
            subpath = Path(relative).relative_to('payload')
            dest = data/subpath
            if dest in private_destinations and (subpath.parts[:2] == ('library', 'guides') or 'data/'+subpath.as_posix() in PRIVATE_CATALOG):
                continue
        else:
            continue
        copies.append((entry, path, dest))
    activating = job is not None and job['phase'] == 'activating'
    if portable:
        check_portable_layout([Path(entry['path']).relative_to('app') for entry, _, _ in copies if entry['path'].startswith('app/')])
        sizes = []
        if not activating:
            for entry, _, dest in copies:
                checked_destination_for_copy(entry, dest, work, data, application)
                existing = dest.stat().st_size if job and dest.is_file() else 0
                sizes.append((dest, max(0, entry['bytes'] - existing)))
        portable_restore_preflight(sizes, activating=activating)

    lock = locked(checked_destination(work.parent, 'restauration.lock')) if portable else nullcontext()
    with lock:
        if portable:
            if read_restore_job(journal) != job:
                raise setup.SetupError('La restauration a changé. Relancez le lanceur.')
            if job is None:
                job = {'schema': 1, 'phase': 'copying', 'inputs': inputs, 'paths': paths,
                       'project': saved['project']}
                setup.write_json(journal, job, private=True)
        if not activating:
            if portable:
                durable.mkdir(application)
                durable.mkdir(work)
                work.chmod(0o700)
            else:
                durable.mkdir(application.parent)
                application.mkdir(exist_ok=False)
                durable.sync_directory(application.parent)
            if progress:
                progress('Vérification et copie des fichiers…' if resume else 'Copie dans le nouveau dossier…')
            for entry, path, dest in copies:
                if portable:
                    checked_destination_for_copy(entry, dest, work, data, application)
                    if resume and verified_copy(entry, dest):
                        continue
                    # Replace a partial file by its directory entry; its inode
                    # could still be shared with another copy on this volume.
                    if dest.exists() and resume:
                        dest.unlink()
                restore_copy(entry, path, dest, verify=portable)
            if portable:
                pause = checked_destination(work, 'inference-paused.json')
                if not pause.exists():
                    setup.write_json(pause, {'reason': 'portable_restore'}, private=True)
            for folder in (application, data, work):
                if folder.exists():
                    durable.sync_tree(folder)
        previous_root, previous_versions = setup.ROOT, setup.VERSIONS
        try:
            setup.ROOT, setup.VERSIONS = application, versions
            app = setup.Installation(work)
            if activating:
                checked_destination(work, 'settings.json')
                config = app.load()
                expected = {key: saved[key] for key in ('project', 'target', 'data_dir', 'app_dir')}
                if any(config.get(key) != value for key, value in expected.items()):
                    raise setup.SetupError('Les réglages de la copie interrompue ont changé.')
            else:
                config = saved
                if portable:
                    checked_destination(work, 'settings.json')
                setup.write_json(app.settings_path, config, private=True)
                app.init(config['target'], data, cpu=config['cpu'])
                if portable:
                    app.doctor(config)
                if progress:
                    progress('Chargement des services hors ligne…')
                app.import_images(config, kit/'images.tar')
                app.prepare(config, True)
                if portable:
                    job['phase'] = 'activating'
                    setup.write_json(journal, job, private=True)
            if progress:
                progress('Démarrage et vérification de SetupSurvie…')
            app.up(config)
            app.verify(config)
            if portable:
                job['phase'] = 'complete'
                setup.write_json(journal, job, private=True)
        finally:
            setup.ROOT, setup.VERSIONS = previous_root, previous_versions
    if portable:
        print('Restauration vérifiée. Ouvrez http://127.0.0.1:8080 sur cet ordinateur. Le moteur IA reste en pause.')
    else:
        print('Restauration effectuée. Les mêmes ports sont utilisés : arrêter l’ancienne installation avant de démarrer celle-ci.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    p=subs.add_parser('backup');p.add_argument('destination');p.add_argument('--work-dir',required=True)
    p=subs.add_parser('restore');p.add_argument('source');p.add_argument('--kit',required=True);p.add_argument('--work-dir',required=True);p.add_argument('--data-dir',required=True)
    p.add_argument('--target',choices=('linux','windows'),help='Adapter la restauration au système de cet ordinateur (kit de même version requis).')
    p.add_argument('--resume', action='store_true', help='Reprendre vers le même dossier après une interruption.')
    args=parser.parse_args()
    if args.action=='backup':
        app=setup.Installation(args.work_dir);c=app.load();app.render(c);backup(app,c,args.destination)
    else:restore(args.source,args.kit,args.work_dir,args.data_dir,target=args.target,resume=args.resume)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
