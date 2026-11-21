#!/usr/bin/env python3
"""Offline relocation of an installed portable SetupSurvie. Standard library only."""
from contextlib import ExitStack, contextmanager, nullcontext
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

import setup
from pilot import durable
from delivery_paths import destination, locked

KIND = 'SetupSurvie complete transfer'
BLOCK = 16 * 1024 * 1024
# Runtime identities are never portable. Leases remain untouched on the source.
RUNTIME = {'control-process.json', 'native-ollama.json', 'discovery-process.json',
           'control.stop', 'docker-start-attempt.json', 'transfer-guard.json', 'compose.env'}


def data_lease(relative):
    return relative.startswith('data/') and relative.endswith('.lock.lease')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def guard(work):
    if (Path(work)/'transfer-guard.json').exists():
        raise setup.SetupError('Transfert en cours ou installation remplacée. Ouvrez Transférer SetupSurvie pour reprendre ou revenir à la source.')


def roots(app, config):
    result = {'application': setup.safe_path(config.get('app_dir', setup.ROOT)),
              'data': setup.safe_path(config['data_dir']), 'private': app.work}
    if len(set(result.values())) != 3:
        raise setup.SetupError('Logiciel, données et réglages doivent avoir des dossiers distincts.')
    if result['data'].is_relative_to(app.work) or app.work.is_relative_to(result['data']):
        raise setup.SetupError('Données et réglages imbriqués : séparation nécessaire avant transfert.')
    for role,name in (('maintenance-archive','maintenance'),('updates-archive','updates')):
        path=result['application'].parent/name
        if path.is_dir() and path not in result.values():result[role]=path
    if os.name=='nt' and os.environ.get('LOCALAPPDATA'):
        cache=Path(os.environ['LOCALAPPDATA'])/'SetupSurvie/installateurs'
        if cache.is_dir():result['installers-cache']=cache.resolve()
    return result


def ollama_manifest_target(root, relative, path, target):
    """Allow only Ollama v2 metadata links to regular blobs in the same model store."""
    parts=relative.split('/')
    if os.name=='nt' or len(parts)<5 or parts[:2]!=['models','manifests-v2']:
        raise setup.SetupError('Lien symbolique refusé hors des manifestes Ollama Linux.')
    name=Path(target).name
    if not re.fullmatch(r'sha256-[a-f0-9]{64}',name):
        raise setup.SetupError('Lien de manifeste Ollama vers un bloc non reconnu.')
    blob=destination(root,'models/blobs/'+name)
    if target!=os.path.relpath(blob,path.parent) or not blob.is_file():
        raise setup.SetupError('Lien de manifeste Ollama externe ou bloc absent.')
    return target


def ollama_manifest_link(root, relative):
    path=destination(root,relative,allow_leaf_symlink=True)
    return ollama_manifest_target(root,relative,path,os.readlink(path))


def manifest_links(dest, inventory, *, publish=False):
    root=destination(dest,'data')
    for relative, target in inventory.get('ollama_links',{}).items():
        path=destination(root,relative,allow_leaf_symlink=True)
        if publish and not path.is_symlink():
            ollama_manifest_target(root,relative,path,target)
            path.symlink_to(target)
            durable.sync_directory(path.parent)
        if ollama_manifest_link(root,relative)!=target:
            raise setup.SetupError('Lien de manifeste Ollama modifié ; bascule refusée.')


def inventory(source, docker_disks=()):
    """Every regular file, with explicit exclusions; no hidden traversal of links."""
    files, excluded, empty = [], [], []
    ollama_links, directory_modes = {}, {}
    docker_disks = {Path(path) for path in docker_disks}
    def unreadable(error):
        raise error
    for role, root in source.items():
        if not root.is_dir():raise setup.SetupError('Dossier source absent : '+role)
        nested = {p for p in source.values() if p != root and p.is_relative_to(root)}
        seen = set()
        for folder, dirs, names in os.walk(root, followlinks=False, onerror=unreadable):
            parent = Path(folder)
            kept = []
            for name in dirs:
                path = parent/name
                if path in nested:continue
                relative=path.relative_to(root).as_posix()
                if name in ('.git', '__pycache__') or role=='private' and name=='search-tools':
                    excluded.append(role+'/'+relative);continue
                if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                    raise setup.SetupError('Lien ou jonction refusé dans '+role)
                if role=='data' and relative=='tools/youtube/venv':
                    excluded.append(role+'/'+relative);continue
                kept.append(name)
            dirs[:] = kept
            relative_dir = parent.relative_to(root).as_posix()
            if relative_dir != '.':
                destination(Path('/validation'),relative_dir)
                key=relative_dir.casefold()
                if key in seen:raise setup.SetupError('Noms ambigus entre Windows et Linux.')
                seen.add(key)
                relative_path=role+'/'+relative_dir
                empty.append(relative_path)
                if os.name!='nt':directory_modes[relative_path]=stat.S_IMODE(parent.stat().st_mode)&0o777
            for name in sorted(names):
                path = parent/name
                relative = path.relative_to(root).as_posix()
                if relative.casefold() in seen:raise setup.SetupError('Noms ambigus entre Windows et Linux.')
                seen.add(relative.casefold())
                if role=='data' and path.is_symlink():
                    ollama_links[relative]=ollama_manifest_link(root,relative)
                    continue
                destination(root,relative)
                if (role == 'private' and (name in RUNTIME or name.endswith('.lease'))
                    or data_lease(role+'/'+relative) or name.endswith(('.pyc','-shm'))):
                    excluded.append(role+'/'+relative);continue
                if name.lower().endswith(('.vhd','.vhdx')):
                    if path in docker_disks and stat.S_ISREG(path.lstat().st_mode):
                        excluded.append(role+'/'+relative);continue
                    history=re.fullmatch(r'diagnostics/docker-recovery-\d{4}-\d{2}-\d{2}/(?:main/ext4|disk/docker_data)\.vhdx',relative)
                    template=relative=='tools/DockerDesktop/resources/wsl/ext4.vhdx'
                    if role!='data' or not (history or template):
                        raise setup.SetupError('Disque virtuel non identifié détecté ; copie refusée.')
                if name.endswith('.transfer-part'):raise setup.SetupError('Nom réservé au transfert déjà présent dans la source.')
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):raise setup.SetupError('Fichier spécial refusé : '+role+'/'+relative)
                files.append({'path':role+'/'+relative, 'bytes':info.st_size,
                              'mtime_ns':info.st_mtime_ns, 'mode':stat.S_IMODE(info.st_mode)})
    return {'files':sorted(files,key=lambda r:r['path']), 'directories':empty, 'excluded':excluded, 'ollama_links':ollama_links, 'directory_modes':directory_modes}


def matches_frozen_inventory(current, frozen):
    frozen_paths={record['path'] for record in frozen}
    # Read-only SQLite checks can create empty sidecars for existing databases.
    # Previously inventoried WALs and new WALs with content still matter.
    return [record for record in current if not (
        record['path'].endswith('-wal')
        and record['bytes']==0
        and record['path'] not in frozen_paths
        and record['path'][:-4] in frozen_paths
    )]==frozen


def restore_directory_modes(dest, inventory):
    if os.name=='nt':return
    # Parent directories must remain writable while files and links are published.
    for relative, mode in reversed(tuple(inventory.get('directory_modes',{}).items())):
        path=destination(dest,relative)
        path.chmod(mode & 0o777)
        durable.sync_directory(path)


def database_check(path):
    with path.open('rb') as stream:
        header=stream.read(16)
    if header != b'SQLite format 3\x00':
        if path.suffix in ('.db','.sqlite','.sqlite3') and path.stat().st_size:
            raise setup.SetupError('Base non reconnue ou corrompue (rapport privé disponible).')
        return False
    # Read-only still sees WAL; immutable=1 would silently ignore pending WAL data.
    try:
        from contextlib import closing
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:raise ValueError()
            if db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError()
    except (sqlite3.Error,ValueError) as exc:
        raise setup.SetupError('Cohérence SQLite refusée ; source conservée, aucune bascule.') from exc
    return True


def prerequisites(config):
    """Inventory presence, never imply installers cover Windows/WSL/drivers."""
    return {'python':sys.version.split()[0], 'docker_cli':bool(shutil.which('docker')),
            'ollama_native':bool(setup.Installation.ollama_binary()) if config['target']=='windows' else None,
            'system_bundle_complete':False,
            'other_windows':['Windows x64 opérationnel', 'Python 3.11+ avec Tk',
                             'Docker Desktop/WSL2 opérationnel', 'Ollama natif si IA souhaitée',
                             'pilote adapté au GPU'],
            'linux':'Conversion depuis Windows non qualifiée ; image Ollama Linux et prérequis spécifiques nécessaires.',
            'docker_storage':'Le transfert reconstitue SetupSurvie à partir de ses données et de ses images exportées. Le stockage actif et l’installation système de Docker Desktop se gèrent séparément.'}


def windows_host(source, dest, task_name=''):
    command=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
             str(setup.ROOT/'scripts/transfer-host-check.ps1'),'-Destination',str(dest)]
    if source is not None:
        command+=['-Source',str(source)]
    if task_name:
        command+=['-TaskName',task_name]
    host=json.loads(setup.run(command,capture=True,timeout=30))
    host['observed_at']=time.time()
    return host


DOCKER_COMPONENTS = {
    'backend': 'Moteur Docker en cours d’exécution',
    'registration': 'Programme Docker enregistré dans Windows',
    'data_images': 'Image(s) disque des données Docker repérée(s)',
    'wsl_system': 'Disque système Docker sous WSL repéré',
}
DOCKER_PLACEMENTS = {
    'source': 'sur le disque source',
    'destination': 'sur le disque de destination',
    'same_disk': 'sur le disque commun à la source et à la destination',
    'other': 'sur un autre disque physique',
    'multiple': 'sur plusieurs disques physiques',
    'unknown': 'emplacement indéterminé',
}


def docker_placement(host):
    """Summarize physical disk observations without exporting paths or disk numbers."""
    def number(info):
        return info.get('disk') if info.get('known') else None

    source=number(host.get('source',{}))
    dest=number(host.get('destination',{}))
    evidence=host.get('docker_evidence',{})
    statuses={}
    for component in DOCKER_COMPONENTS:
        disks={number(record['physical_disk']) for record in evidence.get(component,[])}
        if len(disks-{None})>1:
            status='multiple'
        elif not disks or None in disks:
            status='unknown'
        elif source is not None and source==dest and disks=={source}:
            status='same_disk'
        elif disks=={source}:
            status='source'
        elif disks=={dest}:
            status='destination'
        else:
            status='other' if dest is not None or source is not None else 'unknown'
        statuses[component]=status
    return {'observed_at':host.get('observed_at'),'components':statuses}


def describe_docker(host):
    statuses=docker_placement(host)['components']
    return '\n'.join(f'{label} · {DOCKER_PLACEMENTS[statuses[component]]}'
                    for component,label in DOCKER_COMPONENTS.items())+(
        '\nPour déplacer ou restaurer Docker, suivez la rubrique Docker Desktop du guide de transfert. '
        'Vérifiez ensuite Docker et SetupSurvie après redémarrage.')


def installed_docker_status(dest, journal):
    source_work=Path(journal['source']['private'])
    try:
        source_guard=read(source_work/'transfer-guard.json')
    except (OSError, ValueError):
        source_guard={}
    source=journal['source']['data'] if isinstance(source_guard,dict) and source_guard.get('id')==journal['id'] else None
    return windows_host(source,dest)


def refresh_docker_status(dest):
    if os.name!='nt':
        raise setup.SetupError('Le contrôle du placement de Docker Desktop est disponible sous Windows.')
    dest=setup.safe_path(dest)
    if not (dest/'transfer.json').is_file():
        raise setup.SetupError('Choisissez la destination existante du transfert ou utilisez Examiner pour une nouvelle copie.')
    with locked(dest/'operation.lock'):
        journal=read(dest/'transfer.json')
        if journal.get('kind')!=KIND or journal.get('schema')!=1:
            raise setup.SetupError('Transfert non reconnu.')
        if journal['phase'] in ('planned','copying'):
            raise setup.SetupError('Reprenez la copie avant d’actualiser le placement de Docker Desktop.')
        host=installed_docker_status(dest,journal)
        journal['docker_last_check']=host
        save(dest,journal);export_report(dest,journal)
        return host


def plan(app, dest):
    config=app.load();source=roots(app,config);dest=setup.safe_path(dest)
    for root in source.values():
        if dest==root or dest.is_relative_to(root) or root.is_relative_to(dest):
            raise setup.SetupError('Choisissez un nouveau dossier sur le disque destination, hors de la source.')
    if dest.exists() and not (dest/'transfer.json').is_file():
        raise setup.SetupError('Destination déjà présente : aucun remplacement. Choisissez un nouveau dossier.')
    if not (source['application']/'scripts/transfer.py').is_file():
        raise setup.SetupError('Mettez d’abord le logiciel source à jour avec cette livraison ; le lanceur de transfert doit être présent dans l’application installée.')
    if (app.work/'search-tools').is_dir():
        import search_index_tools
        search_index_tools.validate_cache(source['data']/'tools/search-index-wheels')
    host={}
    if os.name=='nt':
        startup_file=source['application'].parent/'maintenance/startup-settings.json'
        task_name=read(startup_file).get('task_name','') if startup_file.is_file() else ''
        host=windows_host(source['data'],dest,task_name)
        disk=host.get('destination',{})
        if not disk.get('known') or disk.get('filesystem') not in ('NTFS','ReFS'):
            raise setup.SetupError('Destination Windows : volume NTFS ou ReFS identifiable nécessaire pour les gros fichiers et leurs dates. Aucun formatage effectué.')
    for name in ('state/pilot/pilot.db','state/openwebui/webui.db'):
        path=source['data']/name
        if not path.is_file() or not path.stat().st_size:
            raise setup.SetupError('Une base attendue de l’installation est absente ou vide. Conservez la source pour diagnostic ; aucun transfert déclaré complet.')
    items=inventory(source,host.get('docker_disks',[]))
    if any(record['path'].endswith('/pyvenv.cfg') for record in items['files']):
        raise setup.SetupError('Un environnement Python supplémentaire doit disposer d’un adaptateur hors ligne avant transfert. Aucun arrêt effectué.')
    if 'data/tools/youtube/venv' in items['excluded']:
        import youtube_tools
        youtube_tools.validate_wheels(source['data']/'tools/youtube-wheels')
    total=sum(r['bytes'] for r in items['files'])
    parent=dest
    while not parent.exists():parent=parent.parent
    return {'schema':1,'kind':KIND,'id':uuid.uuid4().hex,'source':{k:str(v) for k,v in source.items()},'source_aliases':{'application':str(config.get('app_dir',source['application'])),'data':str(config['data_dir']),'private':str(app.work)},
            'release':read(source['application']/'deploy/release.json') if (source['application']/'deploy/release.json').is_file() else {'version':'unknown'},'destination':str(dest),'target':config['target'],'phase':'planned','created':time.time(),
            'inventory':items,'bytes':total,'free_bytes':shutil.disk_usage(parent).free,
            'prerequisites':prerequisites(config), 'host':host, 'checks':{}, 'adapted':[]}


def hash_progress(path, progress=lambda *args:None, phase='Contrôle SHA-256'):
    digest=hashlib.sha256();total=path.stat().st_size;count=0
    with path.open('rb') as stream:
        while block:=stream.read(BLOCK):
            digest.update(block);count+=len(block);progress(phase,count,total)
    return digest.hexdigest()


def copy_file(source, target, record, progress):
    """Resume a large file using its verified prefix; never trust a partial's size."""
    durable.mkdir(target.parent)
    partial=target.with_name(target.name+'.transfer-part')
    if partial.is_symlink() or partial.exists() and not partial.is_file():raise setup.SetupError('Partiel non régulier refusé.')
    expected=(record['bytes'],record['mtime_ns'])
    def unchanged():
        s=source.stat()
        if (s.st_size,s.st_mtime_ns)!=expected:raise setup.SetupError('Source modifiée pendant le transfert : reprise refusée.')
    unchanged()
    if target.is_file():
        digest=hash_progress(source,progress,'Vérification source')
        if target.stat().st_size==record['bytes'] and hash_progress(target,progress)==digest:
            return digest
        raise setup.SetupError('Copie publiée corrompue : conservez ce dossier et choisissez une nouvelle destination.')
    offset=0;digest=hashlib.sha256()
    with source.open('rb') as src:
        if partial.exists():
            with partial.open('rb') as old:
                while chunk:=old.read(BLOCK):
                    if src.read(len(chunk))!=chunk:
                        raise setup.SetupError('Partiel différent de la source ; conservé pour diagnostic. Choisissez une nouvelle destination.')
                    digest.update(chunk);offset+=len(chunk)
                    progress('Vérification de la reprise',offset,record['bytes'])
            if os.name=='nt' and not partial.stat().st_mode & stat.S_IWRITE:
                # A previous run may have stopped after copying read-only attributes.
                partial.chmod(stat.S_IWRITE)
        with partial.open('ab') as out:
            while chunk:=src.read(BLOCK):
                out.write(chunk);out.flush();os.fsync(out.fileno())
                digest.update(chunk);offset+=len(chunk)
                progress('Copie',offset,record['bytes'])
    unchanged()
    if offset!=record['bytes'] or hash_progress(partial,progress)!=digest.hexdigest():
        raise setup.SetupError('Copie incomplète ou corrompue ; destination non démarrable.')
    # On Windows a read-only source may make the published copy read-only.
    # Flush using the still-writable handle before publishing those attributes.
    if os.name=='nt':
        with partial.open('rb+') as output:
            shutil.copystat(source,partial);os.fsync(output.fileno())
    else:
        shutil.copystat(source,partial);durable.sync_file(partial)
    durable.publish(partial,target)
    return digest.hexdigest()


@contextmanager
def stopped(app, config):
    import control, library_tasks, discovery
    from pilot_backup import maintenance
    data=Path(config['data_dir'])
    # Marker is written BEFORE stopping, and survives our process dying.
    library_tasks.shutdown(app,config)
    control.stop(app)
    discovery.stop(app)
    with ExitStack() as stack:
        stack.enter_context(locked(data/'catalog/content-supervisor.lock'))
        stack.enter_context(maintenance(app,config))
        stack.enter_context(locked(app.work/'search-tools-prepare.lock'))
        stack.enter_context(locked(data/'tools/youtube-prepare.lock'))
        # Remove only this project's containers: Docker cannot auto-restart an old
        # bind mount after reboot. No daemon shutdown or foreign container action.
        app.render(config);app.compose(config,'down','--timeout','60')
        app.stop_native(config)
        if app.compose(config,'ps','--all','--quiet',capture=True):
            raise setup.SetupError('Des services source restent présents ; copie refusée.')
        yield


def save(dest, journal):
    setup.write_json(dest/'transfer.json',journal,private=True)


def copy_status(dest):
    path=dest/'Suivi-transfert.json'
    if not path.is_file():
        return {}
    status=read(path)
    if status['state']=='running':
        import discovery
        if not status['identity'] or discovery.identity(status['pid'])!=status['identity']:
            status['state']='interrupted'
    return status


@contextmanager
def track_copy(dest, journal, callback):
    import discovery
    status={'state':'running','phase':'Arrêt de SetupSurvie et inventaire',
            'pid':os.getpid(),'identity':discovery.identity(os.getpid()),
            'bytes_total':journal['bytes'],'bytes_verified':0,'files_done':0,
            'files_total':len(journal['inventory']['files'])}
    last_write=0
    def update(phase, n=0, total=0, *, force=False, **values):
        nonlocal last_write
        changed=phase!=status['phase']
        status.update(phase=phase, file_bytes=n, file_total=total, **values)
        if force or time.monotonic()-last_write>=2:
            status['updated_at']=time.time()
            setup.write_json(dest/'Suivi-transfert.json',status)
            last_write=time.monotonic()
        if force or changed and n==0:
            callback(phase,n,total)
    update(status['phase'],force=True)
    try:
        yield update
    except (Exception, KeyboardInterrupt) as exc:
        reason='Reprise nécessaire.'
        if isinstance(exc,OSError) and (exc.errno==errno.ENOSPC or getattr(exc,'winerror',None)==112):
            reason='Espace insuffisant sur le disque de destination.'
        elif isinstance(exc,OSError):
            reason='Erreur de lecture ou d’écriture. Vérifiez les deux disques et le diagnostic privé.'
        elif isinstance(exc,setup.SetupError):
            reason='Un contrôle a échoué. Consultez le diagnostic privé avant de reprendre.'
        try:
            update(status['phase'],force=True,state='interrupted',reason=reason)
        except OSError:
            pass
        raise
    else:
        update('Copie vérifiée',force=True,state='copied')


def maintenance_view(dest, operation, started):
    """Portal status during the copy, read from the destination tracker only.

    Nothing is written into the source while it is frozen: the inventory must not change."""
    status=copy_status(dest)
    state=status.get('state','running')
    total=status.get('bytes_total') or 0
    done=status.get('bytes_verified') or 0
    files_total=status.get('files_total') or 0
    detail=''
    if state=='interrupted':
        detail=status.get('reason') or 'Copie interrompue. Reprenez-la depuis Transférer SetupSurvie sur le PC serveur.'
    elif files_total:
        detail=f"{status.get('files_done',0):,} fichiers vérifiés sur {files_total:,}".replace(',','\u202f')
    return {'schema':1,'id':operation,'kind':'transfer',
            'state':{'interrupted':'failed','copied':'completed'}.get(state,'running'),
            'phase':'copy','title':status.get('phase') or 'Copie complète de SetupSurvie','detail':detail,
            'current':done if total else None,'total':total or None,'unit':'bytes',
            'file_bytes':status.get('file_bytes') or 0,'file_total':status.get('file_total') or 0,
            'destination':str(dest),'unavailable':True,'started':started,
            'updated':status.get('updated_at') or started,'steps':[],'lines':[]}


def export_report(dest, journal):
    # No paths, filenames, users, settings values, DB contents or raw tool logs.
    report={k:journal.get(k) for k in ('schema','kind','id','phase','created','bytes','prerequisites','release','target')}
    report['files']=len(journal.get('inventory',{}).get('files',[]))
    report['ollama_manifest_links']=len(journal.get('inventory',{}).get('ollama_links',{}))
    report['verified_files']=len(journal.get('verified',{}))
    report['databases_checked']=len(journal.get('databases',[]))
    report['adapted_files']=len(journal.get('adapted',[]))
    report['checks']=journal.get('checks',{})
    if journal.get('source_retirement'):
        report['source_retirement']={role: entry['stage'] for role,entry in journal['source_retirement'].items()}
    host=journal.get('host',{})
    latest=journal.get('docker_last_check',host)
    report['storage']={'destination_filesystem':host.get('destination',{}).get('filesystem'),
                       'different_physical_disk':host.get('source',{}).get('disk')!=host.get('destination',{}).get('disk') if host.get('source',{}).get('known') and host.get('destination',{}).get('known') else None,
                       'docker_location_recorded':bool(latest.get('docker') or latest.get('docker_disks')), 'docker_moved':False}
    if journal.get('target')=='windows':
        report['storage']['docker_placement']=docker_placement(latest)
    report['incomplete_files_preserved']=sum(r['path'].endswith(('.part','.pending','.tmp')) for r in journal.get('inventory',{}).get('files',[]))
    report['pending']=['Recherche et ouverture par un utilisateur',
                       'IA : essai explicite après levée de pause', 'Redémarrage et réseau externe débranché',
                       'Activation sur un autre PC : recette séparée']
    setup.write_json(dest/'Rapport-transfert.json',report)
    launcher='transferer-setupsurvie.sh' if journal.get('target')=='linux' else 'Transferer-SetupSurvie.cmd'
    graphical = (dest / 'Installer-SetupSurvie.desktop').is_file()
    first_step = ('Double-cliquez sur Installer-SetupSurvie.desktop pour installer hors ligne.\n'
                  if graphical else f'Ouvrez {launcher} pour vérifier, activer ou revenir à la source.\n')
    docker_help=('Sous Windows, utilisez Vérifier Docker pour repérer le moteur et son stockage.\n'
                 if journal.get('target')=='windows' else
                 'Le guide HTML décrit le choix du disque, les prérequis et la reprise.\n')
    durable.write_bytes(dest/'LIRE-MOI-SECOURS.txt',
        (f"SetupSurvie — copie privée du foyer\nÉtat : {journal['phase']}\n"
         f'{first_step}'
         'Les données sont dans data ; les guides PDF dans data/library/guides.\n'
         'Documentation complète : application/docs ; guide court : LISEZ-MOI.html.\n'
         'Ne supprimez pas la source. Ne démarrez pas deux installations.\n'
         f'{docker_help}Suivez le guide de transfert pour déplacer Docker ou préparer un autre PC.\n').encode('utf-8'))
    import html
    guide=setup.ROOT/'docs/exploitation/transfert-installation.md'
    body=guide.read_text(encoding='utf-8') if guide.exists() else 'Consultez application/docs/exploitation/manuel-de-secours.md'
    durable.write_bytes(dest/'LISEZ-MOI.html',('<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Transférer SetupSurvie</title><style>body{max-width:70em;margin:2em auto;padding:1em;font:18px sans-serif}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Transférer SetupSurvie</h1><pre>'+html.escape(body)+'</pre></html>').encode('utf-8'))


def bundle_launcher(base):
    # No root .cmd is added to compatible update packages: generated locally.
    durable.write_bytes(base/'Transferer-SetupSurvie.cmd',
        b'@echo off\r\nrem SetupSurvie managed transfer\r\nif exist "%~dp0data\\tools\\Python312\\python.exe" (\r\n"%~dp0data\\tools\\Python312\\python.exe" -X utf8 "%~dp0application\\scripts\\transfer_wizard.py" --base "%~dp0."\r\nexit /b %ERRORLEVEL%\r\n)\r\npy -3 -X utf8 "%~dp0application\\scripts\\transfer_wizard.py" --base "%~dp0."\r\nif errorlevel 1 pause\r\n')
    durable.write_bytes(base/'transferer-setupsurvie.sh',
        b'#!/bin/sh\nbase=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1\n'
        b'if [ "$#" = 1 ] && [ "$1" = --restaurer-hors-ligne ]; then\n'
        b'    exec "$base/application/scripts/restaurer-linux-hors-ligne.sh" "$base"\n'
        b'fi\nexec python3 "$base/application/scripts/transfer_wizard.py" --base "$base" "$@"\n')
    (base/'transferer-setupsurvie.sh').chmod(0o700)


def publish_linux_installer(base, journal):
    if journal['target'] != 'linux':
        return
    scripts = base / 'application/scripts'
    template = scripts / 'installer-depuis-le-ssd.desktop'
    if not template.is_file():
        return
    interface = base / 'Interface-SetupSurvie'
    interface.mkdir(mode=0o755, exist_ok=True)
    interface.chmod(0o755)
    for name in ('linux_recovery_gui.sh', 'linux_recovery_admin.sh'):
        durable.write_bytes(interface / name, (scripts / name).read_bytes())
    shortcut = base / 'Installer-SetupSurvie.desktop'
    durable.write_bytes(shortcut, template.read_bytes())
    shortcut.chmod(0o755)
    # Reveal the launchers while keeping the data and journals private.
    maintenance = base / 'Entretien-SetupSurvie.desktop'
    durable.write_bytes(maintenance, template.read_text(encoding='utf-8')
                        .replace('Name=Installer SetupSurvie', 'Name=Entretien de SetupSurvie')
                        .replace('Installer SetupSurvie depuis ce disque de secours',
                                 'Entretenir une installation existante')
                        .replace(' install ', ' maintenance-select ').encode())
    maintenance.chmod(0o755)
    public = {interface.name, shortcut.name, maintenance.name, 'LISEZ-MOI.html', 'LIRE-MOI-SECOURS.txt'}
    for entry in base.iterdir():
        if entry.name not in public and not entry.is_symlink():
            entry.chmod(stat.S_IMODE(entry.stat().st_mode) & ~0o077)
    base.chmod(0o755)
    durable.sync_directory(base)


def copy_images(app, config, dest, progress):
    archive=dest/'images.tar'
    manifest=dest/'images.tar.json'
    if archive.is_file() and manifest.is_file():
        try:
            expected=read(manifest)['sha256']
        except (ValueError,KeyError):
            expected=None
        if expected and hash_progress(archive,progress,'Contrôle des images Docker')==expected:
            return expected,setup.file_hash(manifest)
    # A surviving docker save child can only write to its own temporary path.
    # Keep untrusted attempts for diagnosis and rebuild from the installed images.
    token=uuid.uuid4().hex
    if archive.exists():
        durable.publish(archive,dest/f'images-interrupted-{token}.tar')
    if manifest.exists():
        durable.publish(manifest,dest/f'images-interrupted-{token}.tar.json')
    staging=dest/f'images-export-{token}.tar.pending'
    sidecar=staging.with_name(staging.name+'.json')
    progress('Exportation des images Docker',force=True)
    app.export_images(config,staging)
    durable.sync_file(staging)
    expected=read(sidecar)['sha256']
    if hash_progress(staging,progress,'Contrôle des images Docker')!=expected:
        raise setup.SetupError('Archive Docker corrompue.')
    durable.publish(staging,archive)
    durable.publish(sidecar,manifest)
    return expected,setup.file_hash(manifest)


def transfer(app, dest, *, progress=lambda *args:None, stop_context=stopped, export_images=True):
    dest=setup.safe_path(dest)
    with locked(app.work/'update.lock'),locked(app.work/'transfer.lock'):
        config=app.load()
        if setup.safe_path(config.get('app_dir',setup.ROOT))!=setup.ROOT.resolve() and stop_context is stopped:
            raise setup.SetupError('Lancez le transfert depuis le logiciel de l’installation source.')
        update=app.work/'update.json'
        if update.exists() and read(update).get('phase') not in ('complete','rolled_back'):
            raise setup.SetupError('Terminez la récupération de la mise à jour avant transfert.')
        if dest.exists():
            if not (dest/'transfer.json').is_file():raise setup.SetupError('Destination déjà présente : aucun remplacement.')
            journal=read(dest/'transfer.json')
            if journal.get('schema')!=1 or journal.get('kind')!=KIND or journal['source']!={k:str(v) for k,v in roots(app,config).items()}:
                raise setup.SetupError('Destination liée à une autre source.')
            if journal['phase'] not in ('planned','copying'):
                raise setup.SetupError('Cette copie est déjà préparée. Utilisez Vérifier ou Activer.')
        else:
            journal=plan(app,dest)
            # Images need extra space. Inspect their logical size without exporting.
            image_bytes=0
            if export_images:
                topology=json.loads(app.compose(config,'config','--format','json',capture=True))
                for service in topology.get('services',{}).values():
                    for mount in service.get('volumes',[]):
                        if mount.get('type')!='bind':raise setup.SetupError('Volume Docker non inventorié : transfert refusé avant arrêt.')
                        path=setup.safe_path(mount['source'])
                        if not any(path==root or path.is_relative_to(root) for root in roots(app,config).values()):
                            raise setup.SetupError('Montage externe aux dossiers inventoriés : transfert refusé avant arrêt.')
                references=[app.image_reference(config,n) for n in ('open-webui','kiwix','portal')]
                if config['target']=='linux':references.append(app.image_reference(config,'ollama'))
                if (Path(config['data_dir'])/'library/maps/routing/current/manifest.json').is_file():
                    routing=read(setup.ROOT/'deploy/routing-engine.json')['image']
                    references.append(config.get('routing_image',{}).get('id',routing))
                for ref in set(references):
                    image_bytes+=int(json.loads(setup.run(['docker','image','inspect',ref],capture=True))[0]['Size'])
            if journal['free_bytes'] < journal['bytes']+image_bytes+256*1024**2:
                raise setup.SetupError('Place insuffisante : données, images Docker et marge de 256 Mio nécessaires. Source inchangée.')
            durable.mkdir(dest.parent);dest.mkdir();dest.chmod(0o700)
            durable.sync_directory(dest.parent);save(dest,journal)
        existing=app.work/'transfer-guard.json'
        if existing.exists() and read(existing).get('id')!=journal['id']:
            raise setup.SetupError('Un autre transfert protège cette source. Reprenez-le ou revenez à la source.')
        setup.write_json(existing,{'id':journal['id'],'destination':str(dest)},private=True)
        journal['phase']='copying';save(dest,journal);export_report(dest,journal)
        # While services are stopped, the portal ports show this copy's progress.
        page=nullcontext()
        if stop_context is stopped:
            import maintenance_site
            page=maintenance_site.running(config,lambda started=time.time():maintenance_view(dest,journal['id'],started),wait=900)
        with page, track_copy(dest,journal,progress) as report, stop_context(app,config):
            # Reinventory ONLY on first stop. Never silently merge changed source states.
            docker_disks=journal.get('host',{}).get('docker_disks',[])
            current=inventory(roots(app,config),docker_disks)
            if not journal.get('frozen'):
                journal['inventory']=current;journal['bytes']=sum(r['bytes'] for r in current['files']);journal['frozen']=True;save(dest,journal)
            else:
                previous=journal['inventory']['files']
                retained=[record for record in previous if not data_lease(record['path'])]
                if (current.get('ollama_links',{})!=journal['inventory'].get('ollama_links',{})
                    or not matches_frozen_inventory(current['files'],retained)):
                    raise setup.SetupError('La source a changé depuis l’arrêt. Reprise refusée ; aucun mélange de deux états.')
                frozen_modes=journal['inventory'].get('directory_modes')
                if frozen_modes is not None and current['directory_modes']!=frozen_modes:
                    raise setup.SetupError('Permissions source modifiées depuis l’arrêt ; reprise refusée.')
                if frozen_modes is None:
                    journal['inventory']['directory_modes']=current['directory_modes']
                if retained!=previous:
                    journal['inventory']={**current,'files':retained}
                    journal['bytes']=sum(record['bytes'] for record in retained)
                    journal['verified']={path:digest for path,digest in journal.get('verified',{}).items() if not data_lease(path)}
                    save(dest,journal)
            for folder in journal['inventory']['directories']:durable.mkdir(destination(dest,folder))
            verified=journal.setdefault('verified',{})
            databases=journal.setdefault('databases',[])
            confirmed=0
            last_save=time.monotonic()
            report('Copie et vérification des fichiers',force=True,bytes_total=journal['bytes'],
                   files_total=len(journal['inventory']['files']))
            for number,record in enumerate(journal['inventory']['files'],1):
                relative=record['path'];role,tail=relative.split('/',1)
                origin=destination(Path(journal['source'][role]),tail)
                target=destination(dest,relative)
                report('Vérification avant copie',0,record['bytes'],files_done=number-1,bytes_verified=confirmed)
                try:
                    # Source databases are checked before their bytes are accepted.
                    is_db=database_check(origin)
                    verified[relative]=copy_file(origin,target,record,report)
                except (OSError,setup.SetupError) as exc:
                    exc.add_note('Fichier concerné : '+relative)
                    raise
                if is_db and relative not in databases:databases.append(relative)
                confirmed+=record['bytes']
                if time.monotonic()-last_save>=5:
                    save(dest,journal);last_save=time.monotonic()
            manifest_links(dest,journal['inventory'],publish=True)
            restore_directory_modes(dest,journal['inventory'])
            save(dest,journal)
            report('Contrôle des bases de données',force=True,files_done=len(verified),bytes_verified=confirmed)
            for relative in databases:database_check(destination(dest,relative))
            if export_images:
                journal['images_sha256'],journal['images_manifest_sha256']=copy_images(app,config,dest,report)
            current=inventory(roots(app,config),docker_disks)
            if (current.get('ollama_links',{})!=journal['inventory'].get('ollama_links',{})
                or current['directory_modes']!=journal['inventory'].get('directory_modes',{})
                or not matches_frozen_inventory(current['files'],journal['inventory']['files'])):
                raise setup.SetupError('La source a changé pendant la copie : destination conservée sans validation.')
            bundle_launcher(dest)
            journal['checks']['source_stopped']=True
            publish_linux_installer(dest,journal)
            journal['phase']='copied';save(dest,journal);export_report(dest,journal)
        return journal


def verify_copy(dest):
    dest=setup.safe_path(dest);journal=read(dest/'transfer.json')
    if journal.get('kind')!=KIND or journal.get('schema')!=1 or journal['phase'] not in ('copied','adapting','prepared'):
        raise setup.SetupError('Copie inachevée : reprenez le transfert, aucun démarrage possible.')
    manifest_links(dest,journal['inventory'])
    for record in journal['inventory']['files']:
        relative=record['path'];path=destination(dest,relative)
        # Adaptation is separately hashed. Original records remain an audit trail.
        digest=journal.get('adapted_hashes',{}).get(relative,journal['verified'].get(relative))
        candidates={digest}
        if journal['phase']=='adapting':candidates.add(journal.get('planned_hashes',{}).get(relative))
        if not path.is_file() or setup.file_hash(path) not in candidates:
            raise setup.SetupError('Fichier absent ou corrompu ; aucune bascule (détails dans le journal privé).')
        database_check(path)
    if journal.get('images_sha256') and (setup.file_hash(dest/'images.tar')!=journal['images_sha256'] or setup.file_hash(dest/'images.tar.json')!=journal['images_manifest_sha256']):
        raise setup.SetupError('Images Docker corrompues.')
    return journal


def translate_paths(value, mapping):
    if isinstance(value,dict):return {translate_paths(k,mapping):translate_paths(v,mapping) for k,v in value.items()}
    if isinstance(value,list):return [translate_paths(v,mapping) for v in value]
    if isinstance(value,str):
        for old,new in sorted(mapping.items(),key=lambda p:len(p[0]),reverse=True):
            for variant in (old,old.replace('\\','/'),old.replace('/','\\')):
                compared=value.casefold() if os.name=='nt' else value
                prefix=variant.casefold() if os.name=='nt' else variant
                if compared==prefix or compared.startswith(prefix+'/') or compared.startswith(prefix+'\\'):
                    return new+value[len(variant):].replace('\\','/')
    return value


def prepare(dest):
    dest=setup.safe_path(dest)
    with locked(dest/'operation.lock'):
        journal=verify_copy(dest)
        if journal['phase'] in ('active','validated'):raise setup.SetupError('Installation déjà active.')
        # Persist an adaptation plan BEFORE changing files, so power loss can resume.
        plan_path=dest/'adaptation.json'
        if not plan_path.exists() or read(plan_path).get('destination')!=str(dest) or journal['phase']=='prepared':
            mapping={old:(dest/role).as_posix() for role,old in journal['source'].items()}
            mapping.update({old:(dest/role).as_posix() for role,old in journal.get('source_aliases',{}).items()})
            if journal.get('destination') and journal['destination']!=str(dest):
                for role in journal['source']:mapping[str(Path(journal['destination'])/role)]=(dest/role).as_posix()
            edits={};texts={}
            # Host JSON metadata only. Never rewrite user text, conversations or DBs.
            for record in journal['inventory']['files']:
                relative=record['path']
                if relative.endswith('.json') and relative.startswith(('private/','data/catalog/')):
                    path=destination(dest,relative)
                    try:old=read(path)
                    except ValueError:continue
                    new=translate_paths(old,mapping)
                    if new!=old:edits[relative]=new
            for record in journal['inventory']['files']:
                relative=record['path']
                if relative.startswith(('private/','data/catalog/')) and Path(relative).suffix.lower() in ('.env','.ps1','.cmd','.ini','.toml','.xml','.cfg'):
                    path=destination(dest,relative)
                    try:original=path.read_text(encoding='utf-8')
                    except UnicodeError:raise setup.SetupError('Configuration texte non UTF-8 : adaptation refusée, source conservée.')
                    text=original
                    for old,new in sorted(mapping.items(),key=lambda pair:len(pair[0]),reverse=True):
                        for variant in set((old,old.replace('\\','/'),old.replace('/','\\'))):
                            text=text.replace(variant,new)
                    if text!=original:texts[relative]=text
            config=edits.get('private/settings.json',read(dest/'private/settings.json'))
            config.update({'data_dir':(dest/'data').as_posix(),'app_dir':(dest/'application').as_posix(),
                           'project':'survie-transfer-'+journal['id'][:8], 'inference_autostart':False})
            if config.get('target') == 'linux' and journal.get('linux_portable_cpu') is True:
                config['cpu'] = True
            edits['private/settings.json']=config
            queue_path=dest/'data/catalog/search-index-queue.json'
            if queue_path.is_file():
                queue=edits.get('data/catalog/search-index-queue.json',read(queue_path))
                queue.setdefault('settings',{})['enabled']=False
                edits['data/catalog/search-index-queue.json']=queue
            if (dest/'private/content-resume.json').is_file():
                resume=edits.get('private/content-resume.json',read(dest/'private/content-resume.json'))
                resume['enabled']=False
                edits['private/content-resume.json']=resume
            setup.write_json(plan_path,{'destination':str(dest),'edits':edits,'texts':texts},private=True)
        planned=read(plan_path);edits=planned['edits'];texts=planned.get('texts',{})
        journal['planned_hashes']={relative:hashlib.sha256((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')).hexdigest() for relative,value in edits.items()}
        journal['planned_hashes'].update({relative:hashlib.sha256(value.encode('utf-8')).hexdigest() for relative,value in texts.items()})
        journal['phase']='adapting';save(dest,journal)
        for relative,value in edits.items():
            setup.write_json(destination(dest,relative),value,private=True)
            journal.setdefault('adapted_hashes',{})[relative]=setup.file_hash(destination(dest,relative))
        for relative,value in texts.items():
            durable.write_bytes(destination(dest,relative),value.encode('utf-8'),private=True)
            journal.setdefault('adapted_hashes',{})[relative]=setup.file_hash(destination(dest,relative))
        journal['adapted']=list(edits)+list(texts)
        # A copied venv's interpreter/scripts contain absolute paths. Rebuild it
        # locally from verified wheel cache during activation, not by reindexing.
        setup.write_json(dest/'private/transfer-guard.json',{'id':journal['id'],'reason':'destination_not_activated'},private=True)
        journal['destination']=str(dest)
        journal['phase']='prepared';save(dest,journal);export_report(dest,journal)
        return journal


def local_runtime(dest):
    """Run copied code with a relocated portable interpreter when supplied."""
    executable=Path(sys.executable).resolve()
    portable=dest/'data/tools/Python312/python.exe'
    if portable.is_file():executable=portable
    else:
        journal=read(dest/'transfer.json')
        for role,old in journal['source'].items():
            old=Path(old)
            if executable.is_relative_to(old):
                candidate=dest/role/executable.relative_to(old)
                if not candidate.is_file():raise setup.SetupError('Le runtime Python relocalisé manque.')
                executable=candidate;break
    return [str(executable),'-X','utf8',str(dest/'application/scripts/transfer.py')]


def select_restored_cpu_model(config, inventory):
    import linux_host
    if not config.get('cpu') or config.get('chat_model') != setup.VERSIONS['default_model']:
        return
    profile = linux_host.compact_cpu_profile()
    if not profile or not linux_host.needs_compact_model(profile):
        return
    name, tag = profile['model'].split(':', 1)
    v1 = f'data/models/manifests/registry.ollama.ai/library/{name}/{tag}'
    v2 = f'models/manifests-v2/ollama.com/library/{name}/{tag}'
    copied = {record['path'] for record in inventory['files']}
    if v1 in copied or 'data/' + v2 in copied or v2 in inventory.get('ollama_links', {}):
        config['chat_model'] = profile['model']


def activate(dest):
    dest=setup.safe_path(dest)
    if setup.ROOT.resolve()!=dest/'application':
        return setup.run(local_runtime(dest)+['activate',str(dest)])
    with locked(dest/'operation.lock'):
        journal=read(dest/'transfer.json')
        if journal.get('kind')!=KIND or journal.get('schema')!=1:raise setup.SetupError('Transfert non reconnu.')
        recovering=journal['phase']=='activating'
        if recovering:
            stop_destination(dest)
            manifest_links(dest,journal['inventory'])
            for record in journal['inventory']['files']:
                relative=record['path']
                if relative.startswith(('application/','data/library/','data/models/')):
                    if setup.file_hash(destination(dest,relative))!=journal['verified'][relative]:raise setup.SetupError('Ressource modifiée pendant activation interrompue.')
            for relative in journal.get('databases',[]):database_check(destination(dest,relative))
            if setup.file_hash(dest/'images.tar')!=journal.get('images_sha256') or setup.file_hash(dest/'images.tar.json')!=journal.get('images_manifest_sha256'):
                raise setup.SetupError('Images Docker corrompues.')
        else:journal=verify_copy(dest)
        if journal['phase'] not in ('prepared','activating'):raise setup.SetupError('Préparez la destination avant activation.')
        app=setup.Installation(dest/'private');config=app.load()
        mapping={old:(dest/role).as_posix() for role,old in journal['source'].items()}
        os.environ['PATH']=os.pathsep.join(translate_paths(part,mapping) for part in os.environ.get('PATH','').split(os.pathsep))
        host='windows' if os.name=='nt' else 'linux'
        if config['target']!=host:raise setup.SetupError('Conversion Windows/Linux non qualifiée. Conservez la copie ; aucune activation effectuée.')
        # Same-PC source must still be fenced. A new PC needs the same prerequisites,
        # and receives local-only access until its own LAN is configured.
        source_work=Path(journal['source']['private'])
        same_pc=source_work.is_dir()
        if same_pc:
            marker=source_work/'transfer-guard.json'
            if not marker.is_file() or read(marker).get('id')!=journal['id']:
                raise setup.SetupError('La source a été réactivée. Arrêtez-la par un nouveau transfert avant bascule.')
            old=read(source_work/'settings.json')
            command=['docker','ps','--all','--quiet','--filter','label=com.docker.compose.project='+old['project']]
            if setup.run(command,capture=True):raise setup.SetupError('Des conteneurs source existent encore.')
        else:
            config['bind']='127.0.0.1';config.pop('lan_host',None)
        for port in (8080,8081,3000,8443,8444,8445,11435,11436):
            import socket
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',port))==0:raise setup.SetupError('Port occupé : '+str(port)+'. Aucun service étranger arrêté.')
        if setup.run(['docker','info','--format','{{.OSType}}'],capture=True)!='linux':
            raise setup.SetupError('Docker doit utiliser les conteneurs Linux.')
        if not journal.get('images_sha256'):raise setup.SetupError('Archive des images absente ; activation hors ligne impossible.')
        if host == 'linux':
            import linux_host
            config['docker_rootless'] = linux_host.docker_rootless()
            if not same_pc:
                select_restored_cpu_model(config, journal['inventory'])
        journal['phase']='activating';save(dest,journal);export_report(dest,journal)
        config.pop('local_images',None);config.pop('routing_image',None)
        setup.write_json(app.settings_path,config,private=True)
        app.import_images(config,dest/'images.tar')
        # Prevent an absent wheel from causing an implicit network installation.
        if any(p.startswith('private/search-tools') for p in journal['inventory']['excluded']):
            import search_index_tools
            cache=dest/'data/tools/search-index-wheels'
            search_index_tools.validate_cache(cache)
            search_index_tools.prepare(app,config,offline=True,force=True)
        # A copied Python environment may point to the source disk: rebuild it
        # from the copied verified caches, without Internet. Optional tool.
        try:
            import youtube_tools
            youtube_ready=youtube_tools.prepare(config['data_dir'],offline=True,force=True)
        except (OSError,ValueError,setup.SetupError,subprocess.SubprocessError):
            youtube_ready=False
        if 'data/tools/youtube/venv' in journal['inventory']['excluded']:
            journal['checks']['youtube_tools']='passed' if youtube_ready else 'unavailable'
        if host=='windows':
            import windows_autostart
            windows_autostart.prepare(app,config,preserve_preferences=True)
        # Journal for copied settings includes import/local image changes.
        journal.setdefault('adapted_hashes',{})['private/settings.json']=setup.file_hash(app.settings_path)
        save(dest,journal)
        (app.work/'transfer-guard.json').unlink()
        durable.sync_directory(app.work)
        try:
            app.render(config)
            # Document services only: inference remains an explicit user action.
            app.up(config)
            validate_mounts(app,config)
            probe_script=(setup.ROOT/'scripts/transfer_document_probe.py').read_text(encoding='utf-8')
            probe=json.loads(app.compose(config,'exec','-T','pilot','python','-c',probe_script,capture=True,timeout=120))
            journal['checks'].update(probe)
            if host=='windows':app.install_windows_shortcuts(config,startup=journal.get('host',{}).get('startup_enabled',False))
        except BaseException:
            setup.write_json(app.work/'transfer-guard.json',{'id':journal['id'],'reason':'activation_failed'},private=True)
            # Remove only our destination containers; do not leave an unvalidated
            # instance automatically restarting beside the old one.
            import control,discovery
            control.stop(app);discovery.stop(app)
            app.compose(config,'down','--timeout','60')
            raise
        journal['phase']='active';journal['checks']['mounts']=True
        journal['checks']['services_health']=True
        if host=='windows':
            try:
                journal['docker_last_check']=installed_docker_status(dest,journal)
            except (OSError,ValueError,setup.SetupError):
                # The placement probe is advisory. Container and document checks already passed.
                journal['docker_last_check']={}
            print(describe_docker(journal['docker_last_check']))
        save(dest,journal);export_report(dest,journal)


def validate_mounts(app, config, *, allow_ollama=False, app_root=None):
    ids=app.compose(config,'ps','--quiet',capture=True).split()
    if not ids:raise setup.SetupError('Aucun service destination démarré.')
    info=json.loads(setup.run(['docker','inspect',*ids],capture=True))
    core={'open-webui','kiwix','pilot','portal'}
    routers={'router-foot','router-motorcycle','router-car'} if (Path(config['data_dir'])/'library/maps/routing/current/manifest.json').is_file() else set()
    required_services=core|routers
    found=set()
    allowed_services=required_services|{'ollama'} if allow_ollama else required_services
    source_roots=[setup.safe_path(config['data_dir']),app_root or setup.ROOT.resolve()]
    for container in info:
        service=container.get('Config',{}).get('Labels',{}).get('com.docker.compose.service')
        if service not in allowed_services or service in found:raise setup.SetupError('Service absent, inattendu ou en double après transfert.')
        found.add(service)
        for mount in container.get('Mounts',[]):
            if mount.get('Type')!='bind':raise setup.SetupError('Volume non inventorié ; validation refusée.')
            source=mount['Source'].replace('/run/desktop/mnt/host/','').replace('/host_mnt/','')
            # Docker Desktop may normalize D:/ to /run/desktop/mnt/host/d/.
            normalized=source.replace('\\','/').casefold().lstrip('/')
            accepted=False
            for root in source_roots:
                expected=root.as_posix().casefold().lstrip('/')
                for variant in (expected,expected.replace(':/','/')):
                    if normalized==variant or normalized.startswith(variant+'/'):accepted=True
            if not accepted:raise setup.SetupError('Montage extérieur à la destination ; validation refusée.')
        state=container.get('State',{})
        if state.get('Running') is not True:raise setup.SetupError('Service arrêté après transfert.')
        # OSRM has no Docker HEALTHCHECK in the pinned image/Compose. Its HTTP
        # readiness is checked by transfer_document_probe, from the pilot network.
        if service in core and state.get('Health',{}).get('Status')!='healthy':
            raise setup.SetupError('Service non sain après transfert.')
    if not required_services.issubset(found):raise setup.SetupError('Certains services requis manquent après transfert.')


def rollback(dest):
    dest=setup.safe_path(dest);journal=read(dest/'transfer.json')
    if journal.get('kind')!=KIND:raise setup.SetupError('Transfert non reconnu.')
    source_work=Path(journal['source']['private'])
    # A return cannot remove the source fence while copy/update/activation is
    # still using it. Nonblocking OS leases report the competing operation.
    with locked(dest/'operation.lock'),locked(source_work/'update.lock'),locked(source_work/'transfer.lock'):
        return rollback_locked(dest)


def rollback_locked(dest):
    dest=setup.safe_path(dest);journal=read(dest/'transfer.json')
    if journal.get('kind')!=KIND:raise setup.SetupError('Transfert non reconnu.')
    if journal.get('source_retirement'):raise setup.SetupError('Le retrait de la source a commencé. Le retour vers cette installation est indisponible.')
    source_work=Path(journal['source']['private'])
    source=setup.Installation(source_work);config=source.load()
    # Always stop destination first, even after an interrupted activation.
    if journal['phase'] in ('active','validated','activating') and (dest/'private/settings.json').is_file():
        command=local_runtime(dest)+['stop-destination',str(dest)]
        setup.run(command)
    marker=source_work/'transfer-guard.json'
    if journal['phase']=='returned_to_source':
        return
    owned=marker.is_file() and read(marker).get('id')==journal['id']
    already_unlocked=journal['phase']=='returning_to_source' and not marker.exists()
    if not (owned or already_unlocked):
        raise setup.SetupError('Protection source absente ou différente ; aucun démarrage automatique.')
    journal['phase']='returning_to_source';save(dest,journal)
    marker.unlink(missing_ok=True);durable.sync_directory(source_work)
    journal['phase']='returned_to_source';save(dest,journal);export_report(dest,journal)
    # Use original code and settings. User chooses Ouvrir; never force IA on rollback.
    print('Destination arrêtée. Source disponible : utilisez son raccourci Ouvrir SetupSurvie. Les nouveaux changements sur le SSD ne sont pas fusionnés.')


def stop_destination(dest):
    app=setup.Installation(dest/'private');config=app.load()
    setup.write_json(app.work/'transfer-guard.json',{'reason':'returned_to_source'},private=True)
    import control,discovery
    control.stop(app);discovery.stop(app)
    app.render(config);app.compose(config,'down','--timeout','60');app.stop_native(config)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['copy','status','prepare','verify','activate','docker-status','rollback','stop-destination','retire-source'])
    parser.add_argument('destination');parser.add_argument('--work-dir');parser.add_argument('--confirm-id')
    args=parser.parse_args();dest=setup.safe_path(args.destination)
    if args.action=='copy':
        if not args.work_dir:parser.error('--work-dir requis')
        transfer(setup.Installation(args.work_dir),dest)
    elif args.action=='status':
        status=copy_status(dest)
        if not status:raise setup.SetupError('Aucun suivi disponible pour cette destination.')
        print(json.dumps({key:value for key,value in status.items() if key not in ('pid','identity')},ensure_ascii=False,indent=2))
    elif args.action=='prepare':prepare(dest)
    elif args.action=='verify':verify_copy(dest);print('Empreintes et bases contrôlées ; fonctionnement réel à essayer séparément.')
    elif args.action=='activate':activate(dest)
    elif args.action=='docker-status':print(describe_docker(refresh_docker_status(dest)))
    elif args.action=='rollback':rollback(dest)
    elif args.action=='retire-source':
        from transfer_retire import retire
        retire(dest,args.confirm_id)
    else:stop_destination(dest)


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,setup.SetupError):
        # Raw tool failures can carry environment/configuration. Keep detail private.
        import traceback
        import tempfile
        with tempfile.NamedTemporaryFile(prefix='setupsurvie-transfert-',suffix='.log',delete=False,mode='w',encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        print('Transfert interrompu. Aucune copie partielle déclarée prête. Diagnostic privé : '+stream.name,file=sys.stderr)
        sys.exit(1)
