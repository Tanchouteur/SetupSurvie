#!/usr/bin/env python3
"""Stopped-service user snapshot, complementary to the immutable public pilot kit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import secrets
import sys
import time

import setup
import index_locks
from pilot import durable
from delivery_paths import destination as checked_destination,locked

PRIVATE_FILES=('settings.json','identifiants.txt','inference-paused.json')


def separate_roots(*roots):
    for number,path in enumerate(roots):
        for other in roots[:number]:
            if path==other or path.is_relative_to(other) or other.is_relative_to(path):
                raise setup.SetupError('Sauvegarde, kit, données, application et réglages doivent être dans des dossiers séparés sans chevauchement.')


def backup(app,c,destination,*,resume=True):
    with maintenance(app,c):
        return stopped_backup(app,c,destination,resume=resume)


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


def stopped_backup(app,c,destination,*,resume=True,services_stopped=False,progress=None):
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
        for name in ['state/pilot','state/openwebui','state/caddy','library/guides']:
            for path in sorted((data/name).rglob('*')):
                relative=path.relative_to(data)
                if 'cache' in relative.parts or path.name.endswith('-shm') or relative.parts[0]=='state' and path.name.endswith('.lease'):continue
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
        setup.write_json(dest/'backup.json',{'schema':1,'files':files,'requires':'Le kit public correspondant fournit modèles, archives ZIM et caches ; cette sauvegarde contient comptes, conversations, guides et certificats privés.'},private=True)
    finally:
        if resume:app.compose(c,'start','open-webui','pilot','portal')
    print('Sauvegarde privée créée :',dest)


def restore(source,kit,work_dir,data_dir):
    from pilot_kit import checked_entries
    source=setup.safe_path(source);kit=setup.safe_path(kit);data=setup.safe_path(data_dir);work=setup.safe_path(work_dir)
    application=work.parent/'application'
    separate_roots(source,kit,data,work,application)
    for dest in [data,work]:
        if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):raise setup.SetupError('Restauration uniquement vers des dossiers vides.')
    report=json.loads((source/'backup.json').read_text(encoding='utf-8'));entries=checked_entries(source,report)
    public=json.loads((kit/'manifest.json').read_text(encoding='utf-8'));public_entries=checked_entries(kit,public)
    allowed_private={'private/'+name for name in PRIVATE_FILES}
    for entry,_ in entries:
        relative=entry['path']
        if relative not in allowed_private and relative!='data/catalog/downloaded-content.json' and not relative.startswith(('data/state/','data/library/guides/')):
            raise setup.SetupError('Fichier de sauvegarde hors périmètre : '+relative)
    settings=next((path for entry,path in entries if entry['path']=='private/settings.json'),None)
    if settings is None:raise setup.SetupError('Réglages absents du manifeste de sauvegarde.')
    saved=json.loads(settings.read_text(encoding='utf-8'))
    saved['data_dir']=data.as_posix()
    if application.exists():raise setup.SetupError('Le dossier application de restauration doit être absent.')
    durable.mkdir(application)
    for entry,path in public_entries:
        if not entry['path'].startswith('app/'):continue
        target=application/Path(entry['path']).relative_to('app')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);shutil.copymode(path,target)
    setup.ROOT=application
    saved['app_dir']=application.as_posix()
    saved['project']='survie-restored-'+secrets.token_hex(4)
    # An image ID is platform-local; it is re-imported and verified below.
    saved.pop('local_images',None)
    for entry,path in entries:
        if entry['path'].startswith('data/state/') and entry['path'].endswith('.lease'):continue
        if entry['path'].startswith('data/'):
            dest=data/Path(entry['path']).relative_to('data')
        elif entry['path'] in allowed_private-{'private/settings.json'}:dest=checked_destination(work,entry['path'].removeprefix('private/'))
        else:continue
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);dest.chmod(0o600)
    for entry,path in public_entries:
        if not entry['path'].startswith('payload/'):continue
        relative=Path(entry['path']).relative_to('payload');dest=data/relative
        if dest.exists() and (relative.parts[:2]==('library','guides') or relative==Path('catalog/downloaded-content.json')):continue
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    for folder in (application,data,work):
        if folder.exists():durable.sync_tree(folder)
    app=setup.Installation(work);setup.write_json(app.settings_path,saved,private=True)
    app.init(saved['target'],data,cpu=saved['cpu'])
    app.import_images(saved,kit/'images.tar');app.prepare(saved,True);app.up(saved);app.verify(saved)
    print('Restauration effectuée. Les mêmes ports sont utilisés : arrêter l’ancienne installation avant de démarrer celle-ci.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    p=subs.add_parser('backup');p.add_argument('destination');p.add_argument('--work-dir',required=True)
    p=subs.add_parser('restore');p.add_argument('source');p.add_argument('--kit',required=True);p.add_argument('--work-dir',required=True);p.add_argument('--data-dir',required=True)
    args=parser.parse_args()
    if args.action=='backup':
        app=setup.Installation(args.work_dir);c=app.load();app.render(c);backup(app,c,args.destination)
    else:restore(args.source,args.kit,args.work_dir,args.data_dir)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
