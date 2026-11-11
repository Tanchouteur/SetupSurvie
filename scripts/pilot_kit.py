#!/usr/bin/env python3
"""Portable pilot kit: public content and model files, never personal accounts."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

import setup


def checked_entries(root,manifest):
    result=[]
    for entry in manifest['files']:
        path=root/entry['path']
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise setup.SetupError('Fichier de kit absent ou chemin non valide : '+entry['path'])
        if path.stat().st_size!=entry['bytes'] or setup.file_hash(path)!=entry['sha256']:
            raise setup.SetupError('Kit incomplet ou modifié : '+entry['path'])
        result.append((entry,path))
    return result


def export_lab(destination,english=False):
    import linux_lab as lab
    lab.checked_mount()
    dest=setup.safe_path(destination)
    # The Linux lab's export must stay inside the size-limited SSD volume.
    if not dest.is_relative_to(lab.MOUNT):raise setup.SetupError('Le kit doit rester sur le volume SSD dédié.')
    marker=dest/'kit-building.json'
    if dest.exists() and not marker.exists():raise setup.SetupError('Destination existante non reconnue ; choisissez un dossier vide.')
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
    profiles=json.loads((setup.ROOT/'deploy/model-profiles.json').read_text())['profiles']
    blobs=set()
    for model in sorted({p['model'] for p in profiles}):
        name,tag=model.split(':',1)
        manifest=data/'models/manifests/registry.ollama.ai/library'/name/tag
        parsed=json.loads(manifest.read_text())
        copy(manifest,'payload/'+manifest.relative_to(data).as_posix())
        for layer in [parsed['config'],*parsed['layers']]:blobs.add(layer['digest'].replace(':','-'))
    for blob in sorted(blobs):copy(data/'models/blobs'/blob,'payload/models/blobs/'+blob)
    for path in sorted((data/'library/zim').glob('*.zim')):
        if not english and path.name.startswith('wikipedia_en_'):continue
        copy(path,'payload/library/zim/'+path.name)
    for path in sorted((data/'library/guides').rglob('*')):
        if path.is_file():copy(path,'payload/'+path.relative_to(data).as_posix())
    cache=data/'state/openwebui/cache'
    for name in ['embedding','embedding-ready.json','whisper','tiktoken']:
        source=cache/name
        files=sorted(source.rglob('*')) if source.is_dir() else [source]
        for path in files:
            if path.is_file() and '.cache' not in path.relative_to(cache).parts:
                copy(path,'payload/'+path.relative_to(data).as_posix())
    image_path=dest/'images.tar'
    image_records=[]
    for service in ('open-webui','kiwix','portal','ollama'):
        inspected=json.loads(lab.podman('image','inspect',lab.reference(service),capture=True).stdout)[0]
        image_records.append({'service':service,'id':inspected['Id'],'reference':setup.VERSIONS['images'][service]})
    if not image_path.exists():
        temporary=dest/'images.tar.copying'
        lab.podman('save','--format','docker-archive','--multi-image-archive','-o',str(temporary),*[r['id'] for r in image_records])
        temporary.replace(image_path)
    image_hash=setup.file_hash(image_path)
    setup.write_json(dest/'images.tar.json',{'images':image_records,'sha256':image_hash})
    records.extend({'path':p.name,'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in [image_path,dest/'images.tar.json'])
    for name in ['scripts','pilot','portal','deploy','docs','fixtures','tests']:
        for path in sorted((setup.ROOT/name).rglob('*')):
            if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts and path.suffix!='.pyc':
                copy(path,'app/'+path.relative_to(setup.ROOT).as_posix())
    for name in ['README.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml']:
        copy(setup.ROOT/name,'app/'+name)
    for path in sorted((lab.MOUNT/'tools/discovery-wheels').iterdir()):
        if path.is_file():copy(path,'app/vendor/discovery/'+path.name)
    setup.write_json(dest/'manifest.json',{'schema':1,'kind':'SetupSurvie public pilot kit','files':records,
        'models':sorted({p['model'] for p in profiles}),'english_wikipedia':english,
        'notice':'Aucun compte, secret, historique ni certificat privé du PC source. Python, Docker Desktop, Ollama et pilote NVIDIA requis sur Windows.'})
    marker.unlink()
    print('KIT PRÊT',dest,flush=True)


def install(root,target,data_dir,work_dir,lan_address=None):
    if (root/'kit-building.json').exists():raise setup.SetupError('Kit encore en préparation.')
    manifest=json.loads((root/'manifest.json').read_text())
    checked_entries(root,manifest)
    if setup.ROOT.resolve()!=(root/'app').resolve():raise setup.SetupError('Exécutez le lanceur situé dans kit/app/scripts.')
    data=setup.safe_path(data_dir);work=setup.safe_path(work_dir)
    if (data.exists() and any(data.iterdir())) or (work.exists() and any(work.iterdir())):
        raise setup.SetupError('Installation du kit réservée à des dossiers de données et réglages vides.')
    if shutil.disk_usage(data.parent if data.parent.exists() else root).free < sum(e['bytes'] for e in manifest['files'] if e['path'].startswith('payload/'))+15_000_000_000:
        raise setup.SetupError('Espace libre insuffisant pour copier les données du kit.')
    app=setup.Installation(work)
    c=app.init(target,data,lan=bool(lan_address))
    if lan_address:c['lan_host']=setup.lan_host(lan_address);setup.write_json(app.settings_path,c,private=True);app.render(c)
    for entry,path in checked_entries(root,{'files':[e for e in manifest['files'] if e['path'].startswith('payload/')]}):
        relative=Path(entry['path']).relative_to('payload');destination=data/relative
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
    app.import_images(c,root/'images.tar');app.doctor(c);app.prepare(c,offline=True);app.up(c);app.verify(c)
    app.addresses(c)
    print('Identifiants propres à cette installation :',app.work/'identifiants.txt')


def refresh_app(root):
    if (root/'kit-building.json').exists():raise setup.SetupError('Attendre la fin de l’export initial.')
    manifest=json.loads((root/'manifest.json').read_text())
    records=[entry for entry in manifest['files'] if not entry['path'].startswith('app/')]
    paths=[]
    for name in ['scripts','pilot','portal','deploy','docs','fixtures','tests']:
        paths.extend(p for p in (setup.ROOT/name).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    paths.extend(setup.ROOT/name for name in ['README.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml'])
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
    manifest['files']=records;setup.write_json(root/'manifest.json',manifest)
    print('Application du kit mise à jour ; données lourdes conservées.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    p=subs.add_parser('export-lab');p.add_argument('destination');p.add_argument('--english-wikipedia',action='store_true')
    p=subs.add_parser('verify');p.add_argument('kit')
    p=subs.add_parser('refresh-app');p.add_argument('kit')
    p=subs.add_parser('install');p.add_argument('kit');p.add_argument('--target',choices=['windows','linux'],required=True);p.add_argument('--data-dir',required=True);p.add_argument('--work-dir',required=True);p.add_argument('--lan-host',type=setup.lan_host)
    args=parser.parse_args()
    if args.action=='export-lab':export_lab(args.destination,args.english_wikipedia)
    elif args.action=='refresh-app':refresh_app(setup.safe_path(args.kit))
    elif args.action=='verify':
        root=setup.safe_path(args.kit);checked_entries(root,json.loads((root/'manifest.json').read_text()));print('Toutes les empreintes du kit sont conformes.')
    else:install(setup.safe_path(args.kit),args.target,args.data_dir,args.work_dir,args.lan_host)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
