#!/usr/bin/env python3
"""Small offline software updates with stopped-service snapshot and rollback."""
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys
import time
import uuid
import zipfile

import setup
from pilot import durable
from delivery_paths import destination,locked
from pilot_backup import backup
from pilot_kit import checked_entries

FOLDERS=('scripts','pilot','portal','deploy','docs','fixtures','tests','assets')
# Keep this root allowlist compatible with already installed 0.1.16 readers.
# First-install wrappers belong to source/kit deliveries, not software updates.
FILES=('README.md','AGENTS.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml')
SERVICES=('open-webui','kiwix','pilot','portal')


def release_at(root):
    path=root/'deploy/release.json'
    if path.is_file():return json.loads(path.read_text(encoding='utf-8'))
    # Older pilots predate release.json. Read a constant; never execute their code.
    for node in ast.parse((root/'pilot/app.py').read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in node.targets) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
            return {'version':node.value.value,'data_schema':1}
    raise setup.SetupError('Version installée impossible à identifier.')


def version_tuple(value):
    if not re.fullmatch(r'\d+\.\d+\.\d+',value):raise setup.SetupError('Version logicielle non valide.')
    return tuple(map(int,value.split('.')))


def build(output):
    output=setup.safe_path(output)
    if output.exists():raise setup.SetupError('Le paquet existe déjà.')
    paths=[p for name in FOLDERS for p in (setup.ROOT/name).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    paths += [setup.ROOT/n for n in FILES if (setup.ROOT/n).is_file()]
    records=[];output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.part')
    version=json.loads((setup.ROOT/'deploy/release.json').read_text(encoding='utf-8'))
    api_version=re.search(r"^VERSION=['\"]([^'\"]+)['\"]",(setup.ROOT/'pilot/app.py').read_text(encoding='utf-8'),re.MULTILINE)
    if not api_version or api_version.group(1)!=version['version']:
        raise setup.SetupError('Version du manifeste différente de celle de l’API ; paquet non créé.')
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(paths):
                relative=path.relative_to(setup.ROOT).as_posix()
                if path.stat().st_size>10_000_000:raise setup.SetupError('Fichier logiciel trop volumineux : '+relative)
                archive.write(path,'app/'+relative)
                records.append({'path':relative,'bytes':path.stat().st_size,'sha256':setup.file_hash(path),'executable':bool(path.stat().st_mode&0o111)})
            archive.writestr('update.json',json.dumps({'schema':1,'kind':'SetupSurvie software update','release':version,'files':records},ensure_ascii=False))
        durable.sync_file(temporary)
        durable.publish(temporary,output)
    except BaseException:
        temporary.unlink(missing_ok=True);raise
    digest=setup.file_hash(output)
    durable.write_bytes(output.with_name(output.name+'.sha256'),(digest+'  '+output.name+'\n').encode('utf-8'))
    print('Paquet logiciel :',output,'\nSHA-256 :',digest)
    return digest


def unpack(package,expected,dest):
    if not isinstance(expected,str) or len(expected)!=64 or setup.file_hash(package)!=expected.lower():
        raise setup.SetupError('Empreinte du paquet incorrecte. Utiliser celle communiquée par Louis.')
    with zipfile.ZipFile(package) as archive:
        entries=archive.infolist();names=[e.filename for e in entries]
        if len(set(n.casefold() for n in names))!=len(names) or len(entries)>5000 or sum(e.file_size for e in entries)>100_000_000:
            raise setup.SetupError('Archive ambiguë ou trop volumineuse.')
        if any(e.is_dir() or (e.external_attr>>16)&0o170000==0o120000 for e in entries):raise setup.SetupError('Liens et entrées de répertoire refusés.')
        if archive.getinfo('update.json').file_size>2_000_000:raise setup.SetupError('Manifeste trop volumineux.')
        manifest=json.loads(archive.read('update.json'))
        if manifest.get('schema')!=1 or manifest.get('kind')!='SetupSurvie software update':raise setup.SetupError('Paquet non reconnu.')
        records=manifest['files'];paths=[r['path'] for r in records]
        if len(set(p.casefold() for p in paths))!=len(paths) or set(names)!={'update.json',*('app/'+p for p in paths)}:
            raise setup.SetupError('Contenu différent du manifeste.')
        for record in records:
            relative=record['path'];path=destination(dest,relative)
            if relative not in FILES and relative.split('/')[0] not in FOLDERS:raise setup.SetupError('Fichier non logiciel refusé.')
            info=archive.getinfo('app/'+relative)
            if info.file_size!=record['bytes'] or info.file_size>10_000_000:raise setup.SetupError('Taille incorrecte.')
            raw=archive.read(info)
            if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise setup.SetupError('Fichier logiciel altéré.')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            path.chmod(0o755 if record.get('executable') else 0o644)
        for name in ('scripts/setup.py','scripts/pilot_update.py','deploy/versions.json','deploy/release.json','compose.yaml','pilot/app.py','portal/index.html'):
            if name not in paths:raise setup.SetupError('Paquet incomplet : '+name)
        release=json.loads((dest/'deploy/release.json').read_text(encoding='utf-8'))
        if release!=manifest['release'] or release.get('data_schema')!=1:raise setup.SetupError('Migration de données non prise en charge.')
    return manifest


class Services:
    def __init__(self,app,c):self.app,self.c=app,c
    def stop(self):
        import control,discovery
        control.stop(self.app);discovery.stop(self.app)
        self.app.compose(self.c,'stop',*SERVICES)
    def start(self):
        # Do not start Ollama, consume VRAM, pull images or change a gaming pause.
        import control,discovery
        self.app.render(self.c)
        self.app.compose(self.c,'up','-d','--no-deps','--force-recreate','--pull','never','--wait','--wait-timeout','420',*SERVICES)
        control.start(self.app,self.c)
        try:discovery.start(self.app,self.c)
        except (setup.SetupError,OSError,ValueError) as exc:print('Nom local indisponible ; accès IP conservé :',exc)
        self.app.compose(self.c,'exec','-T','pilot','python','-m','pilot.configure')
    def check(self,version):
        for _ in range(30):
            try:
                state=self.app.request('http://127.0.0.1:8080/api/health',timeout=3)
                if state.get('ok') and state.get('version')==version:
                    self.app.request('http://127.0.0.1:3000/health',timeout=5)
                    inference=self.app.request('http://127.0.0.1:8080/api/inference',timeout=5)
                    if not inference.get('control_available'):raise setup.SetupError('Contrôleur du moteur inaccessible après mise à jour.')
                    return
            except (OSError,ValueError,setup.SetupError):pass
            time.sleep(1)
        raise setup.SetupError('La nouvelle version ne répond pas correctement.')


def restore_snapshot(snapshot,app,c):
    report=json.loads((snapshot/'backup.json').read_text(encoding='utf-8'));entries=checked_entries(snapshot,report)
    data=Path(c['data_dir'])
    for entry,_ in entries:
        if not entry['path'].startswith(('data/state/','data/library/guides/')) and entry['path'] not in ('private/settings.json','private/identifiants.txt','private/inference-paused.json','data/catalog/downloaded-content.json'):
            raise setup.SetupError('Sauvegarde non reconnue ; restauration manuelle requise.')
    # Only mutable service state; models, ZIM and caches are never removed.
    for name in ('state/pilot','state/caddy'):
        folder=destination(data,name)
        if folder.exists():shutil.rmtree(folder)
    folder=destination(data,'state/openwebui')
    if folder.exists():
        for path in folder.iterdir():
            if path.name=='cache':continue
            if path.is_symlink():raise setup.SetupError('Lien dans les états ; restauration manuelle requise.')
            if path.is_dir():shutil.rmtree(path)
            else:path.unlink()
    directories=set()
    for entry,source in entries:
        relative=entry['path']
        if relative.startswith('data/state/'):target=destination(data,relative.removeprefix('data/'))
        elif relative in ('private/settings.json','private/identifiants.txt'):target=destination(app.work,relative.removeprefix('private/'))
        else:continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(0o600)
        durable.sync_file(target)
        for parent in target.parents:
            directories.add(parent)
            if parent in (data,app.work):break
    for parent in sorted(directories,key=lambda p:len(p.parts),reverse=True):durable.sync_directory(parent)


def recover(app,journal,services):
    j=json.loads(journal.read_text(encoding='utf-8'));root=Path(j['application']);previous=Path(j['previous']);snapshot=Path(j['snapshot'])
    if j['phase'] in ('complete','rolled_back'):raise setup.SetupError('Cette opération est terminée ; aucun état utilisateur ne sera écrasé.')
    services.stop()
    if previous.exists():
        if root.exists():durable.publish(root,root.with_name(root.name+'.failed-'+uuid.uuid4().hex[:8]))
        durable.publish(previous,root)
    if (snapshot/'backup.json').is_file():restore_snapshot(snapshot,app,services.c)
    setup.ROOT=root
    services.start();services.check(j['old_version'])
    j['phase']='rolled_back';setup.write_json(journal,j,private=True)


def apply(app,package,digest,services=None):
    c=app.load();root=setup.safe_path(c.get('app_dir',setup.ROOT));data=setup.safe_path(c['data_dir'])
    if (root/'.git').exists() or root!=setup.ROOT.resolve():raise setup.SetupError('Utiliser le lanceur de l’application installée, jamais un dépôt de développement ou le kit.')
    if not c.get('app_dir'):raise setup.SetupError('Installation ancienne : migrer une fois le code hors du kit avant la mise à jour.')
    for other in (data,app.work):
        if root==other or root.is_relative_to(other) or other.is_relative_to(root):raise setup.SetupError('Code, données et réglages doivent être séparés.')
    if Path(c['app_dir']).is_symlink():raise setup.SetupError('Application liée refusée.')
    services=services or Services(app,c)
    with locked(app.work/'update.lock'):
        journal=app.work/'update.json'
        if journal.exists() and json.loads(journal.read_text(encoding='utf-8'))['phase'] not in ('complete','rolled_back'):
            raise setup.SetupError('Une mise à jour interrompue doit être récupérée avant de continuer.')
        operation=destination(root.parent,'updates/'+uuid.uuid4().hex)
        durable.mkdir(operation);operation.chmod(0o700)
        staged=operation/'new';previous=operation/'previous';snapshot=operation/'snapshot'
        manifest=unpack(Path(package),digest,staged)
        old_release=release_at(root)
        if version_tuple(manifest['release']['version'])<=version_tuple(old_release['version']):raise setup.SetupError('Version déjà installée ou plus ancienne ; aucun remplacement effectué.')
        if manifest['release']['data_schema']!=old_release['data_schema']:raise setup.SetupError('Migration de schéma non prise en charge par cette mise à jour.')
        for relative in ('deploy/versions.json','deploy/discovery-packages.json'):
            if json.loads((root/relative).read_text(encoding='utf-8'))!=json.loads((staged/relative).read_text(encoding='utf-8')):raise setup.SetupError('Ce paquet exige de nouvelles dépendances ; utiliser une livraison dédiée.')
        # Offline mDNS wheels are not present in a source checkout; preserve them.
        if (root/'vendor').is_dir():
            if (root/'vendor').is_symlink() or any(p.is_symlink() for p in (root/'vendor').rglob('*')):raise setup.SetupError('Lien dans les dépendances locales refusé.')
            shutil.copytree(root/'vendor',staged/'vendor')
        snapshot_bytes=sum(p.stat().st_size for name in ('state/pilot','state/openwebui','state/caddy','library/guides') for p in (data/name).rglob('*') if p.is_file() and not p.is_symlink() and 'cache' not in p.relative_to(data).parts)
        if shutil.disk_usage(root).free<snapshot_bytes+2_000_000_000:raise setup.SetupError('Marge libre insuffisante pour la sauvegarde et le remplacement.')
        durable.sync_tree(staged)
        j={'phase':'prepared','application':str(root),'previous':str(previous),'snapshot':str(snapshot),
           'old_version':old_release['version'],'new_version':manifest['release']['version']}
        setup.write_json(journal,j,private=True)
        try:
            services.stop()
            backup(app,c,snapshot,resume=False)
            j['phase']='snapshot_ready';setup.write_json(journal,j,private=True)
            durable.publish(root,previous);durable.publish(staged,root)
            j['phase']='switched';setup.write_json(journal,j,private=True)
            services.start();services.check(j['new_version'])
            j['phase']='complete';setup.write_json(journal,j,private=True)
        except BaseException:
            try:recover(app,journal,services)
            except BaseException as error:raise setup.SetupError('Mise à jour interrompue ; conserver le dossier updates et lancer recover. '+str(error))
            raise
        print('Mise à jour terminée :',j['new_version'],'; données conservées. Sauvegarde privée :',operation)
        return operation


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('build');b.add_argument('output')
    a=sub.add_parser('apply');a.add_argument('package');a.add_argument('--sha256',required=True);a.add_argument('--work-dir',required=True)
    r=sub.add_parser('recover');r.add_argument('--work-dir',required=True)
    args=p.parse_args()
    if args.action=='build':build(args.output);return
    app=setup.Installation(args.work_dir)
    if args.action=='apply':apply(app,args.package,args.sha256)
    else:
        # Recovery and application share the same OS lease, including after a crash.
        with locked(app.work/'update.lock'):
            recover(app,app.work/'update.json',Services(app,app.load()))


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
