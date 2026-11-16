#!/usr/bin/env python3
"""Offline relocation of an installed portable SetupSurvie. Standard library only."""
from contextlib import ExitStack, contextmanager
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
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


def inventory(source):
    """Every regular file, with explicit exclusions; no hidden traversal of links."""
    files, excluded, empty = [], [], []
    for role, root in source.items():
        if not root.is_dir():raise setup.SetupError('Dossier source absent : '+role)
        nested = {p for p in source.values() if p != root and p.is_relative_to(root)}
        seen = set()
        for folder, dirs, names in os.walk(root, followlinks=False):
            parent = Path(folder)
            kept = []
            for name in dirs:
                path = parent/name
                if path in nested:continue
                if name in ('.git', '__pycache__') or role=='private' and name=='search-tools':
                    excluded.append(role+'/'+path.relative_to(root).as_posix());continue
                if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                    raise setup.SetupError('Lien ou jonction refusé dans '+role)
                kept.append(name)
            dirs[:] = kept
            relative_dir = parent.relative_to(root).as_posix()
            if relative_dir != '.':
                destination(Path('/validation'),relative_dir)
                key=relative_dir.casefold()
                if key in seen:raise setup.SetupError('Noms ambigus entre Windows et Linux.')
                seen.add(key);empty.append(role+'/'+relative_dir)
            for name in sorted(names):
                path = parent/name
                relative = path.relative_to(root).as_posix()
                destination(root,relative)
                if role == 'private' and (name in RUNTIME or name.endswith('.lease')) or name.endswith(('.pyc','-shm')):
                    excluded.append(role+'/'+relative);continue
                if name.lower().endswith(('.vhd','.vhdx')):raise setup.SetupError('Disque virtuel détecté : déplacez Docker depuis ses réglages, sans copier son disque en service.')
                if name.endswith('.transfer-part'):raise setup.SetupError('Nom réservé au transfert déjà présent dans la source.')
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):raise setup.SetupError('Fichier spécial refusé : '+role+'/'+relative)
                if relative.casefold() in seen:raise setup.SetupError('Noms ambigus entre Windows et Linux.')
                seen.add(relative.casefold())
                files.append({'path':role+'/'+relative, 'bytes':info.st_size,
                              'mtime_ns':info.st_mtime_ns, 'mode':stat.S_IMODE(info.st_mode)})
    return {'files':sorted(files,key=lambda r:r['path']), 'directories':empty, 'excluded':excluded}


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
            'docker_storage':'Le disque virtuel Docker reste séparé. Aucun VHDX ni volume étranger copié. Vérifier Disk image location dans Docker Desktop.'}


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
        host=json.loads(setup.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(setup.ROOT/'scripts/transfer-host-check.ps1'),'-Source',str(source['data']),'-Destination',str(dest),'-TaskName',task_name],capture=True))
        disk=host.get('destination',{})
        if not disk.get('known') or disk.get('filesystem') not in ('NTFS','ReFS'):
            raise setup.SetupError('Destination Windows : volume NTFS ou ReFS identifiable nécessaire pour les gros fichiers et leurs dates. Aucun formatage effectué.')
    for name in ('state/pilot/pilot.db','state/openwebui/webui.db'):
        path=source['data']/name
        if not path.is_file() or not path.stat().st_size:
            raise setup.SetupError('Une base attendue de l’installation est absente ou vide. Conservez la source pour diagnostic ; aucun transfert déclaré complet.')
    items=inventory(source)
    if any(record['path'].endswith('/pyvenv.cfg') for record in items['files']):
        raise setup.SetupError('Un environnement Python supplémentaire doit disposer d’un adaptateur hors ligne avant transfert. Aucun arrêt effectué.')
    total=sum(r['bytes'] for r in items['files'])
    parent=dest
    while not parent.exists():parent=parent.parent
    return {'schema':1,'kind':KIND,'id':uuid.uuid4().hex,'source':{k:str(v) for k,v in source.items()},
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
        with partial.open('ab') as out:
            while chunk:=src.read(BLOCK):
                out.write(chunk);out.flush();os.fsync(out.fileno())
                digest.update(chunk);offset+=len(chunk)
                progress('Copie',offset,record['bytes'])
    unchanged()
    if offset!=record['bytes'] or hash_progress(partial,progress)!=digest.hexdigest():
        raise setup.SetupError('Copie incomplète ou corrompue ; destination non démarrable.')
    shutil.copystat(source,partial)
    durable.sync_file(partial);durable.publish(partial,target)
    return digest.hexdigest()


@contextmanager
def stopped(app, config):
    import library_tasks, discovery
    from pilot_backup import maintenance
    data=Path(config['data_dir'])
    # Marker is written BEFORE stopping, and survives our process dying.
    library_tasks.shutdown(app,config)
    discovery.stop(app)
    with ExitStack() as stack:
        stack.enter_context(locked(data/'catalog/content-supervisor.lock'))
        stack.enter_context(maintenance(app,config))
        stack.enter_context(locked(app.work/'search-tools-prepare.lock'))
        # Remove only this project's containers: Docker cannot auto-restart an old
        # bind mount after reboot. No daemon shutdown or foreign container action.
        app.render(config);app.compose(config,'down','--timeout','60')
        app.stop_native(config)
        if app.compose(config,'ps','--all','--quiet',capture=True):
            raise setup.SetupError('Des services source restent présents ; copie refusée.')
        yield


def save(dest, journal):
    setup.write_json(dest/'transfer.json',journal,private=True)


def export_report(dest, journal):
    # No paths, filenames, users, settings values, DB contents or raw tool logs.
    report={k:journal.get(k) for k in ('schema','kind','id','phase','created','bytes','prerequisites','release','target')}
    report['files']=len(journal.get('inventory',{}).get('files',[]))
    report['verified_files']=len(journal.get('verified',{}))
    report['databases_checked']=len(journal.get('databases',[]))
    report['adapted_files']=len(journal.get('adapted',[]))
    report['checks']=journal.get('checks',{})
    host=journal.get('host',{})
    report['storage']={'destination_filesystem':host.get('destination',{}).get('filesystem'),
                       'different_physical_disk':host.get('source',{}).get('disk')!=host.get('destination',{}).get('disk') if host.get('source',{}).get('known') and host.get('destination',{}).get('known') else None,
                       'docker_location_recorded':bool(host.get('docker')), 'docker_moved':False}
    report['incomplete_files_preserved']=sum(r['path'].endswith(('.part','.pending','.tmp')) for r in journal.get('inventory',{}).get('files',[]))
    report['pending']=['Essai Windows réel chez Marc', 'Recherche et ouverture par un utilisateur',
                       'IA : essai explicite après levée de pause', 'Redémarrage et réseau externe débranché',
                       'Autre PC Windows et Linux : recettes distinctes non réalisées']
    setup.write_json(dest/'Rapport-transfert.json',report)
    durable.write_bytes(dest/'LIRE-MOI-SECOURS.txt',
        ('SetupSurvie — copie privée du foyer\nÉtat : '+journal['phase']+'\n'
         'Ouvrez Transferer-SetupSurvie.cmd pour vérifier, activer ou revenir à la source.\n'
         'Les données sont dans data ; les guides PDF dans data/library/guides.\n'
         'Documentation complète : application/docs ; guide court : LISEZ-MOI.html.\n'
         'Ne supprimez pas la source. Ne démarrez pas deux installations.\n'
         'Docker et les prérequis du PC ne sont pas déplacés automatiquement.\n').encode('utf-8'))
    import html
    guide=setup.ROOT/'docs/exploitation/transfert-installation.md'
    body=guide.read_text(encoding='utf-8') if guide.exists() else 'Consultez application/docs/exploitation/manuel-de-secours.md'
    durable.write_bytes(dest/'LISEZ-MOI.html',('<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Transférer SetupSurvie</title><style>body{max-width:70em;margin:2em auto;padding:1em;font:18px sans-serif}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Transférer SetupSurvie</h1><pre>'+html.escape(body)+'</pre></html>').encode('utf-8'))


def bundle_launcher(base):
    # No root .cmd is added to compatible update packages: generated locally.
    durable.write_bytes(base/'Transferer-SetupSurvie.cmd',
        b'@echo off\r\nrem SetupSurvie managed transfer\r\nif exist "%~dp0data\\tools\\Python312\\python.exe" (\r\n"%~dp0data\\tools\\Python312\\python.exe" -X utf8 "%~dp0application\\scripts\\transfer_wizard.py" --base "%~dp0."\r\nexit /b %ERRORLEVEL%\r\n)\r\npy -3 -X utf8 "%~dp0application\\scripts\\transfer_wizard.py" --base "%~dp0."\r\nif errorlevel 1 pause\r\n')
    durable.write_bytes(base/'transferer-setupsurvie.sh',
        b'#!/bin/sh\nexec python3 "$(dirname "$0")/application/scripts/transfer_wizard.py" --base "$(dirname "$0")"\n')
    (base/'transferer-setupsurvie.sh').chmod(0o700)


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
            durable.mkdir(dest);dest.chmod(0o700);save(dest,journal)
        existing=app.work/'transfer-guard.json'
        if existing.exists() and read(existing).get('id')!=journal['id']:
            raise setup.SetupError('Un autre transfert protège cette source. Reprenez-le ou revenez à la source.')
        setup.write_json(existing,{'id':journal['id'],'destination':str(dest)},private=True)
        journal['phase']='copying';save(dest,journal);export_report(dest,journal)
        with stop_context(app,config):
            # Reinventory ONLY on first stop. Never silently merge changed source states.
            current=inventory(roots(app,config))
            if not journal.get('frozen'):
                journal['inventory']=current;journal['bytes']=sum(r['bytes'] for r in current['files']);journal['frozen']=True;save(dest,journal)
            elif current['files']!=journal['inventory']['files']:
                raise setup.SetupError('La source a changé depuis l’arrêt. Reprise refusée ; aucun mélange de deux états.')
            for folder in journal['inventory']['directories']:durable.mkdir(destination(dest,folder))
            verified=journal.setdefault('verified',{})
            databases=journal.setdefault('databases',[])
            for number,record in enumerate(journal['inventory']['files'],1):
                relative=record['path'];role,tail=relative.split('/',1)
                origin=destination(Path(journal['source'][role]),tail)
                target=destination(dest,relative)
                progress('Fichier '+str(number)+' / '+str(len(journal['inventory']['files'])),0,record['bytes'])
                # Source databases are checked BEFORE their bytes are accepted.
                is_db=database_check(origin)
                verified[relative]=copy_file(origin,target,record,progress)
                if is_db and relative not in databases:databases.append(relative)
                save(dest,journal)
            for relative in databases:database_check(destination(dest,relative))
            if export_images:
                archive=dest/'images.tar'
                if not archive.exists() or not (dest/'images.tar.json').exists():
                    # An interrupted docker save is untrusted, keep it for diagnosis.
                    if archive.exists():durable.publish(archive,dest/('images-interrupted-'+uuid.uuid4().hex+'.tar'))
                    app.export_images(config,archive)
                image_info=read(dest/'images.tar.json')
                if setup.file_hash(archive)!=image_info['sha256']:raise setup.SetupError('Archive Docker corrompue.')
                journal['images_sha256']=image_info['sha256']
                journal['images_manifest_sha256']=setup.file_hash(dest/'images.tar.json')
            journal['phase']='copied';save(dest,journal)
        bundle_launcher(dest)
        journal['checks']['source_stopped']=True
        save(dest,journal);export_report(dest,journal)
        return journal


def verify_copy(dest):
    dest=setup.safe_path(dest);journal=read(dest/'transfer.json')
    if journal.get('kind')!=KIND or journal.get('schema')!=1 or journal['phase'] not in ('copied','adapting','prepared'):
        raise setup.SetupError('Copie inachevée : reprenez le transfert, aucun démarrage possible.')
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
                if value==variant or value.startswith(variant+'/') or value.startswith(variant+'\\'):
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
        if host=='windows':
            import windows_autostart
            windows_autostart.prepare(app,config,preserve_preferences=True)
        # Journal for copied settings includes import/local image changes.
        journal.setdefault('adapted_hashes',{})['private/settings.json']=setup.file_hash(app.settings_path)
        save(dest,journal)
        (app.work/'transfer-guard.json').unlink()
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
        save(dest,journal);export_report(dest,journal)


def validate_mounts(app, config):
    ids=app.compose(config,'ps','--quiet',capture=True).split()
    if not ids:raise setup.SetupError('Aucun service destination démarré.')
    info=json.loads(setup.run(['docker','inspect',*ids],capture=True))
    source_roots=[setup.safe_path(config['data_dir']),setup.ROOT.resolve()]
    for container in info:
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
        if container.get('State',{}).get('Health',{}).get('Status')!='healthy':
            raise setup.SetupError('Service non sain après transfert.')


def rollback(dest):
    dest=setup.safe_path(dest);journal=read(dest/'transfer.json')
    if journal.get('kind')!=KIND:raise setup.SetupError('Transfert non reconnu.')
    source_work=Path(journal['source']['private'])
    source=setup.Installation(source_work);config=source.load()
    # Always stop destination first, even after an interrupted activation.
    if journal['phase'] in ('active','validated','activating') and (dest/'private/settings.json').is_file():
        command=local_runtime(dest)+['stop-destination',str(dest)]
        setup.run(command)
    marker=source_work/'transfer-guard.json'
    if not marker.is_file() or read(marker).get('id')!=journal['id']:
        raise setup.SetupError('Protection source absente ou différente ; aucun démarrage automatique.')
    marker.unlink();durable.sync_directory(source_work)
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
    parser.add_argument('action',choices=['copy','prepare','verify','activate','rollback','stop-destination'])
    parser.add_argument('destination');parser.add_argument('--work-dir')
    args=parser.parse_args();dest=setup.safe_path(args.destination)
    if args.action=='copy':
        if not args.work_dir:parser.error('--work-dir requis')
        transfer(setup.Installation(args.work_dir),dest,progress=lambda phase,n,total:print(phase,n,'/',total,flush=True))
    elif args.action=='prepare':prepare(dest)
    elif args.action=='verify':verify_copy(dest);print('Empreintes et bases contrôlées ; fonctionnement réel à essayer séparément.')
    elif args.action=='activate':activate(dest)
    elif args.action=='rollback':rollback(dest)
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
