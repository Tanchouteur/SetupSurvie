#!/usr/bin/env python3
"""Portable pilot kit: public content and model files, never personal accounts."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import sys
import time
import subprocess

import setup
from pilot import durable


def checked_entries(root,manifest,progress=None):
    from delivery_paths import destination
    if not isinstance(manifest,dict) or not isinstance(manifest.get('files'),list):
        raise setup.SetupError('Manifeste de fichiers non valide.')
    root=Path(root);seen=set()
    result=[]
    for number,entry in enumerate(manifest['files'],1):
        if not isinstance(entry,dict) or not isinstance(entry.get('path'),str):raise setup.SetupError('Entrée de manifeste non valide.')
        relative=entry['path']
        if relative.casefold() in seen:raise setup.SetupError('Chemin dupliqué ou ambigu dans le manifeste : '+relative)
        seen.add(relative.casefold())
        if type(entry.get('bytes')) is not int or entry['bytes']<0 or not isinstance(entry.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',entry['sha256']):
            raise setup.SetupError('Taille ou empreinte de manifeste non valide.')
        path=destination(root,relative)
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise setup.SetupError('Fichier de kit absent ou chemin non valide : '+entry['path'])
        if path.stat().st_size!=entry['bytes'] or setup.file_hash(path)!=entry['sha256']:
            raise setup.SetupError('Kit incomplet ou modifié : '+entry['path'])
        result.append((entry,path))
        if progress:progress(number,len(manifest['files']),entry['bytes'])
    return result


def export_lab(destination,english=True):
    import linux_lab as lab
    lab.checked_mount()
    dest=setup.safe_path(destination)
    # The Linux lab's export must stay inside the size-limited SSD volume.
    if not dest.is_relative_to(lab.MOUNT):raise setup.SetupError('Le kit doit rester sur le volume SSD dédié.')
    marker=dest/'kit-building.json'
    if dest.exists() and (not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('kind')!='SetupSurvie public pilot kit'):
        raise setup.SetupError('Destination existante non reconnue ; choisissez un dossier vide.')
    dest.mkdir(parents=True,exist_ok=True)
    setup.write_json(marker,{'kind':'SetupSurvie public pilot kit'})
    records=[]

    def copy(source,relative):
        if source.is_symlink() or not source.is_file():raise setup.SetupError('Fichier non régulier : '+str(source))
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(dest).free < source.stat().st_size+15_000_000_000:
            raise setup.SetupError('Marge de stockage insuffisante ; export interrompu et reprenable.')
        if not target.exists() or target.stat().st_size!=source.stat().st_size:
            partial=target.with_name(target.name+'.copying');shutil.copyfile(source,partial);partial.replace(target)
        digest=setup.file_hash(target)
        # Check the source too: never label an old same-size copy as current.
        if digest!=setup.file_hash(source):
            shutil.copyfile(source,target);digest=setup.file_hash(target)
        records.append({'path':relative,'bytes':target.stat().st_size,'sha256':digest})
        print('KIT',relative,flush=True)

    data=lab.MOUNT/'data'
    profiles=json.loads((setup.ROOT/'deploy/model-profiles.json').read_text(encoding='utf-8'))['profiles']
    blobs=set()
    for model in sorted({p['model'] for p in profiles}):
        name,tag=model.split(':',1)
        manifest=data/'models/manifests/registry.ollama.ai/library'/name/tag
        parsed=json.loads(manifest.read_text(encoding='utf-8'))
        copy(manifest,'payload/'+manifest.relative_to(data).as_posix())
        for layer in [parsed['config'],*parsed['layers']]:blobs.add(layer['digest'].replace(':','-'))
    for blob in sorted(blobs):copy(data/'models/blobs'/blob,'payload/models/blobs/'+blob)
    receipt=data/'catalog/downloaded-content.json'
    if receipt.is_file():copy(receipt,'payload/catalog/downloaded-content.json')
    for path in sorted((data/'library/zim').glob('*.zim')):
        if not english and path.name.startswith('wikipedia_en_'):continue
        copy(path,'payload/library/zim/'+path.name)
    for path in sorted((data/'library/guides').rglob('*')):
        if path.is_file():copy(path,'payload/'+path.relative_to(data).as_posix())
    if (data/'library/maps').is_symlink():raise setup.SetupError('Le dossier des cartes ne doit pas être un lien.')
    for path in sorted((data/'library/maps').rglob('*')):
        if path.is_file() and not path.name.endswith('.part'):
            copy(path,'payload/'+path.relative_to(data).as_posix())
    cache=data/'state/openwebui/cache'
    for name in ['embedding','embedding-ready.json','whisper','tiktoken']:
        source=cache/name
        files=sorted(source.rglob('*')) if source.is_dir() else [source]
        for path in files:
            if path.is_file() and '.cache' not in path.relative_to(cache).parts:
                copy(path,'payload/'+path.relative_to(data).as_posix())
    image_path=dest/'images.tar'
    image_records=[]
    import kit_maps
    image_records,_=kit_maps.image_records(lab,(data/'library/maps/routing/current/manifest.json').is_file())
    saved=json.loads((dest/'images.tar.json').read_text(encoding='utf-8')) if (dest/'images.tar.json').is_file() else {}
    if not image_path.exists() or saved.get('images')!=image_records or setup.file_hash(image_path)!=saved.get('sha256'):
        temporary=dest/'images.tar.copying'
        lab.podman('save','--format','docker-archive','--multi-image-archive','-o',str(temporary),*[r['id'] for r in image_records])
        temporary.replace(image_path)
    image_hash=setup.file_hash(image_path)
    setup.write_json(dest/'images.tar.json',{'images':image_records,'sha256':image_hash})
    records.extend({'path':p.name,'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in [image_path,dest/'images.tar.json'])
    for name in ['scripts','pilot','portal','deploy','docs','fixtures','tests','assets']:
        for path in sorted((setup.ROOT/name).rglob('*')):
            if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts and path.suffix!='.pyc':
                copy(path,'app/'+path.relative_to(setup.ROOT).as_posix())
    for name in ['README.md','AGENTS.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml','Installer-SetupSurvie.cmd','Mettre-a-jour-SetupSurvie.cmd','1-Preparer-le-PC.cmd','2-Installer-SetupSurvie.cmd','Dupliquer-Kit-SetupSurvie.cmd']:
        copy(setup.ROOT/name,'app/'+name)
    for path in sorted((lab.MOUNT/'tools/discovery-wheels').iterdir()):
        if path.is_file():copy(path,'app/vendor/discovery/'+path.name)
    index_wheels=data/'tools/search-index-wheels'
    if index_wheels.is_dir():
        for path in sorted(index_wheels.iterdir()):
            if path.is_file() and not path.is_symlink() and path.suffix in ('.whl','.json'):copy(path,'app/vendor/search-index/'+path.name)
    complete_youtube_caches(data)
    for source,relative in youtube_vendor(data):copy(source,relative)
    setup.write_json(dest/'manifest.json',{'schema':1,'kind':'SetupSurvie public pilot kit','files':records,
        'models':sorted({p['model'] for p in profiles}),'english_wikipedia':english,
        'notice':'Aucun compte, secret, historique ni certificat privé du PC source. Python, Docker Desktop, Ollama et pilote NVIDIA requis sur Windows.'})
    marker.unlink()
    print('KIT PRÊT',dest,flush=True)


def install(root,target,data_dir,work_dir,lan_address=None,*,startup=True):
    import collection_tasks
    from pilot import collection_sort
    if (root/'kit-building.json').exists():raise setup.SetupError('Kit encore en préparation.')
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    entries=checked_entries(root,manifest)
    if any(e['path']=='payload/library/maps/routing/current/manifest.json' for e in manifest['files']):
        images=json.loads((root/'images.tar.json').read_text(encoding='utf-8'))
        if not any(e['service']=='routing' for e in images['images']):raise setup.SetupError('Le kit contient des routes mais pas leur moteur hors ligne.')
    if setup.ROOT.resolve()!=(root/'app').resolve():raise setup.SetupError('Exécutez le lanceur situé dans kit/app/scripts.')
    data=setup.safe_path(data_dir);work=setup.safe_path(work_dir)
    application=work.parent/'application'
    for path in (root,data,work):
        if application==path or application.is_relative_to(path) or path.is_relative_to(application):
            raise setup.SetupError('Le dossier application doit être séparé du kit, des données et des réglages.')
    if application.exists():raise setup.SetupError('Le dossier application existe déjà ; utiliser la mise à jour, pas une réinstallation.')
    if (data.exists() and any(data.iterdir())) or (work.exists() and any(work.iterdir())):
        raise setup.SetupError('Installation du kit réservée à des dossiers de données et réglages vides.')
    preset = next((path for entry,path in entries if entry['path'] == 'app/'+collection_tasks.DEFAULT_SORT_PATH), None)
    sorting = collection_sort.read_file(preset) if preset else collection_sort.Sort()
    payload = [(entry,path) for entry,path in entries if entry['path'].startswith('payload/')
               and sorting.permits(collection_sort.path_key(entry['path'].removeprefix('payload/')), 'all')]
    if shutil.disk_usage(data.parent if data.parent.exists() else root).free < sum(e['bytes'] for e,_ in payload)+15_000_000_000:
        raise setup.SetupError('Espace libre insuffisant pour copier les données du kit.')
    durable.mkdir(application)
    for entry,path in entries:
        if not entry['path'].startswith('app/'):continue
        destination=application/Path(entry['path']).relative_to('app')
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
        shutil.copymode(path,destination)
    setup.ROOT=application
    app=setup.Installation(work)
    c=app.init(target,data,lan=bool(lan_address))
    c['app_dir']=application.as_posix();setup.write_json(app.settings_path,c,private=True)
    if lan_address:c['lan_host']=setup.lan_host(lan_address);setup.write_json(app.settings_path,c,private=True);app.render(c)
    for entry,path in payload:
        relative=Path(entry['path']).relative_to('payload');destination=data/relative
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
    import search_index_queue
    if preset:
        collection_tasks.seed(data, sorting)
    for entry,path in payload:
        if entry['path'].startswith('payload/library/zim/'):
            target=data/Path(entry['path']).relative_to('payload')
            if setup.file_hash(target)!=entry['sha256']:raise setup.SetupError('Copie de l’archive non conforme ; indexation non lancée.')
            search_index_queue.enqueue(data,{'path':entry['path'].removeprefix('payload/'),'sha256':entry['sha256']})
    durable.sync_tree(application);durable.sync_tree(data)
    app.import_images(c,root/'images.tar');app.doctor(c);app.prepare(c,offline=True)
    import search_index_tools
    try:
        if not search_index_tools.prepare(app,c,offline=True):print('Indexation complémentaire : outil absent du kit, préparation nécessaire dans les réglages.')
    except (OSError,ValueError,setup.SetupError,subprocess.SubprocessError):print('Outil d’indexation incompatible ou incomplet ; les autres documents restent disponibles. Réessayez dans les réglages.')
    setup.prepare_youtube_tools(c,True)
    app.up(c);app.verify(c)
    app.install_windows_shortcuts(c,startup=startup)
    setup.schedule_initial_videos(app,c,offline=True)
    app.addresses(c)
    print('Identifiants propres à cette installation :',app.work/'identifiants.txt')
    print('Application installée, indépendante du kit :',application)


def complete_youtube_caches(data):
    """Add the Windows and Linux files of yt-dlp/Deno/FFmpeg before export.

    Uses Internet when a pinned file is missing; an outage only leaves the
    tool to be prepared at first use on the target PC."""
    import youtube_tools
    try:
        for system in ('windows','linux'):youtube_tools.cache_target(data,system,'3.13')
    except (OSError,ValueError,setup.SetupError,subprocess.SubprocessError) as error:
        print('Outils YouTube incomplets dans le kit ('+str(error)[:200]+') ; ils seront préparés au premier téléchargement avec Internet.')


def youtube_vendor(data):
    """Verified yt-dlp/Deno wheels and FFmpeg archives of the data folder, for the kit.

    Prepare them for every target first, e.g. on the lab:
    python scripts/youtube_tools.py --data-dir DATA --cache-target windows:3.13"""
    import youtube_tools
    tools=data/'tools'
    wheels=tools/'youtube-wheels'
    if (wheels/'manifest.json').is_file():
        youtube_tools.validate_wheels(wheels)
        for path in sorted(wheels.iterdir()):
            if path.is_file() and not path.is_symlink() and path.suffix in ('.whl','.json'):yield path,'app/vendor/youtube/wheels/'+path.name
    ffmpeg=youtube_tools.manifest()['ffmpeg']
    for system in ('windows','linux'):
        archive=tools/'ffmpeg-archives'/ffmpeg[system]['file']
        if archive.is_file() and archive.stat().st_size==ffmpeg[system]['bytes'] and youtube_tools.file_hash(archive)==ffmpeg[system]['sha256']:
            yield archive,'app/vendor/youtube/ffmpeg/'+archive.name


def refresh_app(root):
    if (root/'kit-building.json').exists():raise setup.SetupError('Attendre la fin de l’export initial.')
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    records=[entry for entry in manifest['files'] if not entry['path'].startswith('app/')]
    paths=[]
    for name in ['scripts','pilot','portal','deploy','docs','fixtures','tests','assets']:
        paths.extend(p for p in (setup.ROOT/name).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    paths.extend(setup.ROOT/name for name in ['README.md','AGENTS.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml','Installer-SetupSurvie.cmd','Mettre-a-jour-SetupSurvie.cmd','1-Preparer-le-PC.cmd','2-Installer-SetupSurvie.cmd','Dupliquer-Kit-SetupSurvie.cmd'])
    for source in paths:
        relative='app/'+source.relative_to(setup.ROOT).as_posix();dest=root/relative
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        records.append({'path':relative,'bytes':dest.stat().st_size,'sha256':setup.file_hash(dest)})
    wheels=Path(os.environ.get('SURVIE_DISCOVERY_WHEELS',setup.ROOT/'vendor/discovery'))
    if not wheels.exists():wheels=Path('/run/media/louis/SetupSurvie/tools/discovery-wheels')
    if not wheels.is_dir():raise setup.SetupError('Paquets de découverte réseau absents : impossible de finaliser le kit.')
    for source in sorted(wheels.iterdir()):
        if not source.is_file():continue
        relative='app/vendor/discovery/'+source.name;dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
        records.append({'path':relative,'bytes':dest.stat().st_size,'sha256':setup.file_hash(dest)})
    index_wheels=Path(os.environ.get('SURVIE_INDEX_WHEELS',setup.ROOT/'vendor/search-index'))
    if not index_wheels.is_dir():index_wheels=root/'app/vendor/search-index'
    if index_wheels.is_dir():
        for source in sorted(index_wheels.iterdir()):
            if not source.is_file() or source.is_symlink() or source.suffix not in ('.whl','.json'):continue
            relative='app/vendor/search-index/'+source.name;dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
            records.append({'path':relative,'bytes':dest.stat().st_size,'sha256':setup.file_hash(dest)})
    youtube=Path(os.environ.get('SURVIE_YOUTUBE_TOOLS',setup.ROOT/'vendor/youtube'))
    if not youtube.is_dir():youtube=root/'app/vendor/youtube'
    if youtube.is_dir():
        for source in sorted(p for p in youtube.rglob('*') if p.is_file() and not p.is_symlink()):
            relative='app/vendor/youtube/'+source.relative_to(youtube).as_posix();dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
            records.append({'path':relative,'bytes':dest.stat().st_size,'sha256':setup.file_hash(dest)})
    manifest['files']=records;setup.write_json(root/'manifest.json',manifest)
    print('Application du kit mise à jour ; données lourdes conservées.')


def refresh_library(root,data):
    """Add pinned and downloaded public items; never export mutable user state."""
    from delivery_paths import destination,locked
    root=setup.safe_path(root);data=setup.safe_path(data)
    if (root/'kit-building.json').exists():raise setup.SetupError('Kit encore en préparation.')
    with locked(destination(root,'library-refresh.lock')):
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        records={entry['path']:entry for entry in manifest['files']}
        sources=[]
        import content
        public={i['path']:i for i in content.catalog()}
        receipt=content.destination(data,'catalog/downloaded-content.json')
        if receipt.exists():public.update({i['path']:i for i in content.catalog(receipt)})
        for item in public.values():
            relative='payload/'+item['path'];existing=records.get(relative);dest=destination(root,relative)
            if existing and existing['bytes']==item['bytes'] and existing['sha256']==item['sha256'] and dest.is_file() and dest.stat().st_size==item['bytes']:continue
            path=destination(data,item['path'])
            if not path.is_file():continue
            if path.stat().st_size!=item['bytes'] or setup.file_hash(path)!=item['sha256']:raise setup.SetupError('Contenu source non vérifié : '+item['id'])
            sources.append((path,'payload/'+item['path'],item['sha256']))
        meta=destination(data,'library/guides/metadata.json')
        if meta.is_file():
            allowed={i['path'].removeprefix('library/guides/') for i in public.values() if i['path'].startswith('library/guides/')}
            metadata=[i for i in json.loads(meta.read_text(encoding='utf-8')) if i.get('path') in allowed]
            public_meta=destination(root,'library-metadata-public.json')
            setup.write_json(public_meta,metadata)
            sources.append((public_meta,'payload/library/guides/metadata.json',setup.file_hash(public_meta)))
        missing=sum(p.stat().st_size for p,relative,digest in sources if relative not in records or records[relative]['sha256']!=digest)
        if shutil.disk_usage(root).free<missing+15_000_000_000:raise setup.SetupError('Marge libre insuffisante pour compléter le kit.')
        for source,relative,digest in sources:
            dest=destination(root,relative);dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.is_file() or setup.file_hash(dest)!=digest:
                temporary=destination(root,relative+'.copying');shutil.copyfile(source,temporary)
                if setup.file_hash(temporary)!=digest:raise setup.SetupError('Copie interrompue ou source modifiée.')
                temporary.replace(dest)
            records[relative]={'path':relative,'bytes':dest.stat().st_size,'sha256':digest}
        destination(root,'library-metadata-public.json').unlink(missing_ok=True)
        manifest['files']=list(records.values())
        manifest['english_wikipedia']=any(e['path'].startswith('payload/library/zim/wikipedia_en_all_') for e in records.values())
        setup.write_json(root/'manifest.json',manifest)
    print('Bibliothèque du kit actualisée sans recopier les modèles ni les états personnels.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    p=subs.add_parser('export-lab');p.add_argument('destination');p.add_argument('--english-wikipedia',action=argparse.BooleanOptionalAction,default=True)
    p=subs.add_parser('verify');p.add_argument('kit')
    p=subs.add_parser('duplicate');p.add_argument('kit');p.add_argument('destination')
    p=subs.add_parser('prepare-windows');p.add_argument('kit');p.add_argument('--verify-only',action='store_true')
    p=subs.add_parser('refresh-app');p.add_argument('kit')
    p=subs.add_parser('refresh-library');p.add_argument('kit');p.add_argument('--data-dir',required=True)
    p=subs.add_parser('refresh-maps-lab');p.add_argument('kit');p.add_argument('--geography',action='append',default=[]);p.add_argument('--routing',action='store_true')
    p=subs.add_parser('recover-maps');p.add_argument('kit')
    p=subs.add_parser('install');p.add_argument('kit');p.add_argument('--target',choices=['windows','linux'],required=True);p.add_argument('--data-dir',required=True);p.add_argument('--work-dir',required=True);p.add_argument('--lan-host',type=setup.lan_host)
    p.add_argument('--startup',action=argparse.BooleanOptionalAction,default=True,help='Windows : démarrer à l’ouverture de session ; --no-startup conserve les raccourcis manuels.')
    args=parser.parse_args()
    if args.action=='export-lab':export_lab(args.destination,args.english_wikipedia)
    elif args.action=='duplicate':
        import kit_duplicate
        kit_duplicate.duplicate(args.kit, args.destination)
    elif args.action=='prepare-windows':
        import windows_kit_installers
        windows_kit_installers.prepare(args.kit, verify_only=args.verify_only)
    elif args.action=='refresh-app':refresh_app(setup.safe_path(args.kit))
    elif args.action=='refresh-library':refresh_library(setup.safe_path(args.kit),setup.safe_path(args.data_dir))
    elif args.action=='refresh-maps-lab':
        import kit_maps
        kit_maps.refresh_lab(setup.safe_path(args.kit),args.geography,args.routing)
    elif args.action=='recover-maps':
        import kit_maps
        kit_maps.recover(setup.safe_path(args.kit))
    elif args.action=='verify':
        import kit_audit
        root=setup.safe_path(args.kit)
        if (root/'kit-building.json').exists():raise setup.SetupError('Kit encore en préparation.')
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'));done=0;last=time.monotonic()
        def progress(number,total,size):
            nonlocal done,last
            done+=size
            if time.monotonic()-last>10 or number==total:
                print(f'Vérification : {number}/{total} fichiers, {done/1e9:.2f} Go contrôlés',flush=True);last=time.monotonic()
        checked_entries(root,manifest,progress)
        print('Toutes les empreintes du kit sont conformes.');print(json.dumps(kit_audit.validate(root,manifest),ensure_ascii=False))
    else:install(setup.safe_path(args.kit),args.target,args.data_dir,args.work_dir,args.lan_host,startup=args.startup)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
