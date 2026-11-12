#!/usr/bin/env python3
"""Download selected, pinned offline contents without touching accounts or models."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import urllib.parse
import urllib.request

import setup

CATALOG=setup.ROOT/'deploy/content-catalog.json'
DEFAULT_BUDGET=500_000_000_000


class DownloadPaused(Exception):
    """Cooperative stop: keep partials, never publish an unverified file."""
    pass


def check_capacity(root,missing=0,*,budget=DEFAULT_BUDGET,reserve=15_000_000_000,storage_root=None):
    """Cap documents once; enforce physical free space separately from test models."""
    scope=Path(storage_root) if storage_root is not None else root
    if storage_root is not None:
        if not scope.is_mount() or not root.resolve().is_relative_to(scope.resolve()):
            raise setup.SetupError('Volume de stockage absent ou extérieur aux données.')
        disk=shutil.disk_usage(scope)
    else:
        disk=shutil.disk_usage(root)
    library=destination(root,'library')
    used=sum(p.stat().st_size for p in library.rglob('*') if p.is_file() and not p.is_symlink())
    if used+missing>budget or disk.free<missing+reserve:
        raise setup.SetupError('Budget documentaire ou marge physique insuffisants ; transfert arrêté sans publication.')
    return used


def destination(root,relative):
    if not isinstance(relative,str) or any(c in relative for c in '\\:\x00<>"|?*'):
        raise setup.SetupError('Chemin de contenu non valide.')
    parts=PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or any(not p or p in ('.','..') or p.endswith((' ','.')) or re.fullmatch(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',p) for p in relative.split('/')):
        raise setup.SetupError('Chemin de contenu non valide.')
    path=root.joinpath(*parts)
    for parent in [path,*path.parents]:
        if parent==root.parent:break
        if parent.is_symlink():raise setup.SetupError('Lien symbolique refusé : '+relative)
    if not path.resolve().is_relative_to(root.resolve()):raise setup.SetupError('Chemin externe refusé.')
    return path


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:path.mkdir()
    except FileExistsError:raise setup.SetupError('Une opération est en cours ou a été interrompue : '+str(path))
    owner=path/'owner.json'
    try:
        import discovery
        setup.write_json(owner,{'pid':os.getpid(),'identity':discovery.identity(os.getpid())},private=True)
        yield
    finally:
        owner.unlink(missing_ok=True);path.rmdir()


def catalog(path=CATALOG):
    data=json.loads(Path(path).read_text(encoding='utf-8'));items=data['items'];seen=set();paths=set()
    for item in items:
        relative=item['path'];url=urllib.parse.urlsplit(item['url'])
        destination(Path.cwd(),relative)
        if not relative.startswith(('library/guides/','library/zim/')) or item['id'] in seen or relative.casefold() in paths:
            raise setup.SetupError('Catalogue ambigu ou chemin non documentaire.')
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.fragment:
            raise setup.SetupError('URL HTTPS publique requise.')
        if not isinstance(item['bytes'],int) or not 0<item['bytes']<=600_000_000_000 or not re.fullmatch('[a-f0-9]{64}',item['sha256']):
            raise setup.SetupError('Taille ou empreinte absente du catalogue.')
        seen.add(item['id']);paths.add(relative.casefold())
    return items


def transfer(root,item,opener=None,progress=None,before_write=None,cancelled=None):
    def check():
        if cancelled and cancelled():raise DownloadPaused()
    def digest(path):
        if cancelled is None:return setup.file_hash(path)
        value=hashlib.sha256()
        with path.open('rb') as stream:
            while block:=stream.read(8*1024*1024):
                check();value.update(block)
        check();return value.hexdigest()
    check()
    target=destination(root,item['path']);partial=destination(root,item['path']+'.part')
    size=item['bytes'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.stat().st_size==size and digest(target)==item['sha256']:return 'present'
        raise setup.SetupError('Fichier existant différent, conservé : '+str(target))
    offset=partial.stat().st_size if partial.exists() else 0
    if offset>size:raise setup.SetupError('Fichier partiel trop grand ; nettoyer ce téléchargement avant de reprendre.')
    if offset<size:
        check()
        request=urllib.request.Request(item['url'],headers={'Range':f'bytes={offset}-','Accept-Encoding':'identity','User-Agent':'SetupSurvie-offline-library/0.1'})
        open_url=opener or urllib.request.build_opener(urllib.request.ProxyHandler({})).open
        with open_url(request,timeout=60) as response:
            if urllib.parse.urlsplit(response.geturl()).scheme!='https':raise setup.SetupError('Redirection non HTTPS refusée.')
            status=response.status
            if status==206:
                match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
                if not match or tuple(map(int,match.groups()))!=(offset,size-1,size):raise setup.SetupError('Réponse partielle incohérente ; aucun ajout au fichier.')
            elif status==200:offset=0
            else:raise setup.SetupError('Réponse HTTP inattendue : '+str(status))
            if response.headers.get('Content-Encoding','identity')!='identity':raise setup.SetupError('Contenu compressé inattendu.')
            with partial.open('ab' if offset else 'wb') as out:
                while chunk:=response.read(min(1024*1024,size-offset+1)):
                    check()
                    if offset+len(chunk)>size:raise setup.SetupError('Le serveur dépasse la taille annoncée.')
                    if before_write:before_write(len(chunk))
                    out.write(chunk);offset+=len(chunk)
                    if progress:progress(offset,size)
                out.flush();os.fsync(out.fileno())
    if partial.stat().st_size!=size:raise setup.SetupError('Téléchargement interrompu ; relancer la même commande pour reprendre.')
    if digest(partial)!=item['sha256']:raise setup.SetupError('Empreinte incorrecte ; fichier partiel conservé, jamais publié.')
    check()
    partial.chmod(0o644)
    partial.replace(target)
    return 'downloaded'


def download(root,items,*,budget=DEFAULT_BUDGET,reserve=15_000_000_000,storage_root=None,cancelled=None):
    root=setup.safe_path(root)
    if not root.is_dir():raise setup.SetupError('Le dossier de données doit déjà exister sur le disque choisi.')
    with locked(destination(root,'catalog/content.lock')):
        missing=0
        for item in items:
            final=destination(root,item['path']);part=destination(root,item['path']+'.part')
            if not final.exists():missing+=max(0,item['bytes']-(part.stat().st_size if part.exists() else 0))
        check_capacity(root,missing,budget=budget,reserve=reserve,storage_root=storage_root)
        results=[]
        for item in items:
            print(item['title'],flush=True)
            def progress(done,total):
                setup.write_json(root/'catalog/content-progress.json',{'id':item['id'],'bytes':done,'total':total,'status':'downloading'})
            def before_write(count):
                check_capacity(root,count+1_000_000,budget=budget,reserve=reserve,storage_root=storage_root)
            try:state=transfer(root,item,progress=progress,before_write=before_write,cancelled=cancelled)
            except BaseException:
                setup.write_json(root/'catalog/content-progress.json',{'id':item['id'],'status':'interrupted','message':'Relancer la même commande pour reprendre ; aucun fichier non vérifié publié.'})
                raise
            results.append({'id':item['id'],'status':state})
            if item['path'].startswith('library/guides/'):
                meta=root/'library/guides/metadata.json'
                if meta.is_symlink():raise setup.SetupError('Métadonnées liées refusées.')
                records=json.loads(meta.read_text()) if meta.exists() else []
                relative=item['path'].removeprefix('library/guides/')
                records=[r for r in records if r.get('path')!=relative]
                records.append({'path':relative,'title':item['title'],'language':item['language'],
                    'provenance':item['publisher']+' — '+item['url']+' — édition '+item['edition']+(' — '+item['notes'] if item.get('notes') else ''),'licence':item['licence']})
                setup.write_json(meta,records)
        setup.write_json(root/'catalog/content-progress.json',{'status':'done','results':results})
        return results


def install_templates(root):
    """Publish blank guidance only; never overwrite a completed family document."""
    for source in (setup.ROOT/'deploy/library-templates').glob('*.md'):
        target=destination(root,'library/guides/REF-'+source.name)
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            target.chmod(0o644)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['list','download','clean-partials']);p.add_argument('--data-dir');p.add_argument('--pack',action='append',default=[]);p.add_argument('--id',action='append',default=[])
    p.add_argument('--budget-gb',type=int,default=500);p.add_argument('--work-dir')
    p.add_argument('--lab',action='store_true',help='Montage Linux vérifié ; 500 Go de documents, modèles et caches exclus ; marge physique contrôlée.')
    p.add_argument('--no-refresh',action='store_true',help='Télécharger seulement ; actualiser les services séparément hors du service de transfert.')
    p.add_argument('--selection',type=Path,help='Plan figé créé par kiwix_select.py ; utilise ses archives sélectionnées.')
    args=p.parse_args()
    if args.selection:
        if args.pack or args.id:p.error('--selection ne se combine pas avec --pack ou --id.')
        plan=json.loads(args.selection.read_text(encoding='utf-8'))
        if plan.get('schema')!=1 or plan.get('kind')!='SetupSurvie Kiwix thematic selection':p.error('Plan de sélection Kiwix non reconnu.')
        items=catalog(args.selection);selected=items
        if any(not i['path'].startswith('library/zim/') for i in items):p.error('Le plan Kiwix doit contenir uniquement des archives ZIM.')
    else:
        items=catalog();selected=[i for i in items if i['pack'] in args.pack or i['id'] in args.id]
    if args.action=='list':
        for i in items:print(i['id'],i['pack'],i['bytes'],i['title'])
        return
    if args.selection and not selected:
        print('Aucune nouvelle archive dans cette sélection ; rien à télécharger.');return
    if not selected or set(args.id)-{i['id'] for i in items} or set(args.pack)-{i['pack'] for i in items}:p.error('Choisir des --pack ou --id présents dans list.')
    storage_root=None
    if args.lab:
        import linux_lab as lab
        lab.checked_mount()
        storage_root=lab.MOUNT
        expected=lab.MOUNT/'data'
        if args.work_dir:p.error('--lab ne se combine pas avec --work-dir.')
        if args.data_dir and setup.safe_path(args.data_dir)!=expected:p.error('--lab utilise les données du volume dédié.')
        args.data_dir=str(expected)
    app=setup.Installation(args.work_dir) if args.work_dir else None
    c=app.load() if app else None
    if args.data_dir and c and setup.safe_path(args.data_dir)!=setup.safe_path(c['data_dir']):p.error('Le dossier doit correspondre à cette installation.')
    if not args.data_dir and not c:p.error('--data-dir ou --work-dir requis.')
    root=setup.safe_path(args.data_dir or c['data_dir'])
    if args.action=='clean-partials':
        with locked(destination(root,'catalog/content.lock')):
            for i in selected:destination(root,i['path']+'.part').unlink(missing_ok=True)
        print('Seuls les téléchargements partiels sélectionnés ont été supprimés.');return
    if not 1<=args.budget_gb<=600:p.error('Budget entre 1 et 600 Go.')
    download(root,selected,budget=args.budget_gb*1_000_000_000,storage_root=storage_root)
    check_capacity(root,100_000,budget=args.budget_gb*1_000_000_000,storage_root=storage_root)
    install_templates(root)
    if args.no_refresh:
        print('Téléchargements vérifiés ; actualisation des services à effectuer séparément.')
        return
    if args.lab:
        from linux_lab import setup as lab_setup
        lab_app=lab_setup.Installation(lab.MOUNT/'private')
        lab_app.catalog(lab_app.load())
        lab.podman('restart',lab.PREFIX+'kiwix',lab.PREFIX+'pilot',capture=True)
        print('Bibliothèque du laboratoire actualisée ; moteur IA inchangé.')
        return
    if app:
        app.catalog(c)
        app.compose(c,'restart','kiwix','pilot')
        print('Catalogue actualisé et recherche redémarrée, sans lancer de génération IA.')
    else:print('Téléchargement vérifié. Relancer le catalogue et la recherche avec le lanceur de cette installation.')


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc,file=sys.stderr);sys.exit(1)
