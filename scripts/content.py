#!/usr/bin/env python3
"""Download selected, pinned offline contents without touching accounts or models."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
import threading
import time
from datetime import datetime,timezone
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
from delivery_paths import locked
from pilot import collection_sort, durable

CATALOG=setup.ROOT/'deploy/content-catalog.json'
STORAGE_RESERVE = 15_000_000_000


class DownloadPaused(Exception):
    """Cooperative stop: keep partials, never publish an unverified file."""
    pass


def free_space(root, storage_root=None):
    if storage_root is None:
        return shutil.disk_usage(root).free
    scope = Path(storage_root)
    if not scope.is_mount() or not root.resolve().is_relative_to(scope.resolve()):
        raise setup.SetupError('Volume de stockage absent ou extérieur aux données.')
    free = shutil.disk_usage(scope).free
    if sys.platform == 'linux':
        # A sparse loop image shares space with the rest of its physical SSD.
        device = scope.stat().st_dev
        attribute = Path(f'/sys/dev/block/{os.major(device)}:{os.minor(device)}/loop/backing_file')
        try:
            backing = Path(attribute.read_text().rstrip('\n'))
        except FileNotFoundError:
            pass
        else:
            if not backing.is_file():
                raise setup.SetupError('Fichier du volume de stockage inaccessible.')
            free = min(free, shutil.disk_usage(backing.parent).free)
    return free


def check_capacity(root, missing=0, *, budget=None, reserve=STORAGE_RESERVE, storage_root=None):
    """Enforce the supplied budget and physical reserve before writing."""
    free = free_space(root, storage_root)
    library = destination(root, 'library')
    used = sum(p.stat().st_size for p in library.rglob('*') if p.is_file() and not p.is_symlink())
    if (budget is not None and used + missing > budget) or free < missing + reserve:
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


def catalog(path=CATALOG):
    data=json.loads(Path(path).read_text(encoding='utf-8'));items=data['items'];seen=set();paths=set()
    for item in items:
        relative=item['path'];url=urllib.parse.urlsplit(item['url'])
        destination(Path.cwd(),relative)
        if not relative.startswith(('library/guides/','library/zim/')) or item['id'] in seen or relative.casefold() in paths:
            raise setup.SetupError('Catalogue ambigu ou chemin non documentaire.')
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.fragment:
            raise setup.SetupError('URL HTTPS publique requise.')
        if type(item['bytes']) is not int or item['bytes'] <= 0 or not re.fullmatch('[a-f0-9]{64}',item['sha256']):
            raise setup.SetupError('Taille ou empreinte absente du catalogue.')
        seen.add(item['id']);paths.add(relative.casefold())
    return items


def transfer(root,item,opener=None,progress=None,before_write=None,cancelled=None,write_lock=None):
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
        from content_mirrors import opener_for, network_open
        open_url=opener or opener_for(root,item,check) or network_open
        with open_url(request,timeout=60) as response:
            if urllib.parse.urlsplit(response.geturl()).scheme!='https':raise setup.SetupError('Redirection non HTTPS refusée.')
            status=response.status
            if status==206:
                match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
                if not match or tuple(map(int,match.groups()))!=(offset,size-1,size):raise setup.SetupError('Réponse partielle incohérente ; aucun ajout au fichier.')
            elif status==200:
                # Some PDF servers ignore Range. Compare their prefix instead of
                # truncating bytes already downloaded, even on a short response.
                if offset:
                    with partial.open('rb') as existing:
                        left=offset
                        while left:
                            check()
                            block=response.read(min(1024*1024,left))
                            if not block or block!=existing.read(len(block)):
                                raise setup.SetupError('Le serveur ignore la reprise et ne fournit pas le préfixe attendu ; partiel conservé.')
                            left-=len(block)
            else:raise setup.SetupError('Réponse HTTP inattendue : '+str(status))
            if response.headers.get('Content-Encoding','identity')!='identity':raise setup.SetupError('Contenu compressé inattendu.')
            with partial.open('ab' if offset else 'wb') as out:
                while chunk:=response.read(min(1024*1024,size-offset+1)):
                    check()
                    if offset+len(chunk)>size:raise setup.SetupError('Le serveur dépasse la taille annoncée.')
                    with write_lock if write_lock is not None else nullcontext():
                        check()
                        if before_write:before_write(len(chunk))
                        out.write(chunk);out.flush();offset+=len(chunk)
                    if progress:progress(offset,size)
                out.flush();os.fsync(out.fileno())
    if partial.stat().st_size!=size:raise setup.SetupError('Téléchargement interrompu ; relancer la même commande pour reprendre.')
    if digest(partial)!=item['sha256']:raise setup.SetupError('Empreinte incorrecte ; fichier partiel conservé, jamais publié.')
    check()
    partial.chmod(0o644)
    durable.sync_file(partial)
    durable.publish(partial,target)
    return 'downloaded'


def record_download(root,item,state):
    """Caller holds the shared metadata lock for this read/modify/publish."""
    receipt=destination(root,'catalog/downloaded-content.json')
    published={i['path']:i for i in catalog(receipt)} if receipt.exists() else {}
    published={path:entry for path,entry in published.items() if entry['id']!=item['id']}
    published[item['path']]=item
    setup.write_json(receipt,{'schema':1,'items':list(published.values())})
    if item['path'].startswith('library/guides/'):
        meta=root/'library/guides/metadata.json'
        if meta.is_symlink():raise setup.SetupError('Métadonnées liées refusées.')
        records=json.loads(meta.read_text()) if meta.exists() else []
        relative=item['path'].removeprefix('library/guides/')
        previous=next((r for r in records if r.get('path')==relative),{})
        records=[r for r in records if r.get('path')!=relative]
        records.append({'path':relative,'title':item['title'],'language':item['language'],
            'provenance':item['publisher']+' — '+item['url']+' — édition '+item['edition']+(' — '+item['notes'] if item.get('notes') else ''),'licence':item['licence'],
            'edition':item['edition'],'document_date':item.get('document_date',previous.get('document_date','')),
            'collected_at':datetime.now(timezone.utc).date().isoformat() if state=='downloaded' else previous.get('collected_at','')})
        setup.write_json(meta,records)


def download(root,items,*,budget=None,reserve=15_000_000_000,storage_root=None,cancelled=None,
             workers=1,continue_on_error=False,repair_tls=None):
    if type(workers) is not int or not 1<=workers<=3:
        raise setup.SetupError('Choisissez entre un et trois téléchargements simultanés.')
    items=list(items)
    if len({i['path'].casefold() for i in items})!=len(items) or len({i['id'] for i in items})!=len(items):
        raise setup.SetupError('Sélection de téléchargement ambiguë.')
    root=setup.safe_path(root)
    if not root.is_dir():raise setup.SetupError('Le dossier de données doit déjà exister sur le disque choisi.')
    with locked(destination(root,'catalog/content.lock')):
        sorting = collection_sort.load(root / 'catalog')
        items = [item for item in items if sorting.permits(collection_sort.path_key(item['path']), 'all')]
        if not items:
            return []
        missing=0
        for item in items:
            final=destination(root,item['path']);part=destination(root,item['path']+'.part')
            if not final.exists():missing+=max(0,item['bytes']-(part.stat().st_size if part.exists() else 0))
        check_capacity(root,missing,budget=budget,reserve=reserve,storage_root=storage_root)
        # Shared read-only monitoring for direct Linux/Windows CLI transfers too.
        # The pinned plan contains only public bibliographic metadata, never URLs or logs.
        import discovery
        active_plan=root/'catalog/active-content-plan.json'
        setup.write_json(active_plan,{'items':[{k:i[k] for k in ('id','title','path','bytes','sha256') if k in i} for i in items]})
        setup.write_json(root/'diagnostics/content-transfer.json',{'pid':os.getpid(),
            'identity':discovery.identity(os.getpid()),'started':time.time(),'plan':str(active_plan)})
        metadata=threading.RLock();writes=threading.Lock();stop=threading.Event()
        active={};results=[];last_report=0;first_error=None
        def stopped():
            return stop.is_set() or bool(cancelled and cancelled())
        def report(item,done,total,status,force=False):
            nonlocal last_report
            with metadata:
                active[item['id']]={'id':item['id'],'title':item['title'],'bytes':done,'total':total,'status':status}
                now=time.monotonic()
                if force or now-last_report>=.5:
                    setup.write_json(root/'catalog/content-progress.json',{
                        **active[item['id']], 'status':'downloading', 'workers':workers,
                        'active':list(active.values())})
                    last_report=now
        def run(item):
            if stopped():raise DownloadPaused()
            print(item['title'],flush=True)
            part=destination(root,item['path']+'.part')
            report(item,part.stat().st_size if part.exists() else 0,item['bytes'],'downloading',True)
            def progress(done,total):report(item,done,total,'downloading')
            def before_write(count):
                check_capacity(root,count+1_000_000,budget=budget,reserve=reserve,storage_root=storage_root)
            try:
                try:
                    state=transfer(root,item,progress=progress,before_write=before_write,cancelled=stopped,write_lock=writes)
                except Exception as exc:
                    if not repair_tls or 'CERTIFICATE_VERIFY_FAILED' not in str(exc):raise
                    if stopped():raise DownloadPaused()
                    repair_tls(item['url'])
                    state=transfer(root,item,progress=progress,before_write=before_write,cancelled=stopped,write_lock=writes)
                with metadata:
                    record_download(root,item,state)
                    import search_index_queue
                    search_index_queue.enqueue(root,item)
                return {'id':item['id'],'status':state}
            except DownloadPaused:
                stop.set();raise
            except Exception as exc:
                if not continue_on_error:stop.set();raise
                print(f"En attente : {item['id']} — {exc}. Les autres contenus continuent.",file=sys.stderr,flush=True)
                return {'id':item['id'],'status':'failed','error':str(exc)}
            except BaseException:
                stop.set();raise
            finally:
                with metadata:
                    active.pop(item['id'],None)
                    setup.write_json(root/'catalog/content-progress.json',{**next(iter(active.values()),{}),'status':'downloading',
                        'workers':workers,'active':list(active.values())})
        # All writers are joined before releasing the OS lock, even on failure/pause.
        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix='library') as pool:
            futures=[pool.submit(run,item) for item in items]
            try:
                for future in as_completed(futures):
                    try:results.append(future.result())
                    except BaseException as exc:
                        if first_error is None or (isinstance(first_error,DownloadPaused) and not isinstance(exc,DownloadPaused)):
                            first_error=exc
                        stop.set()
            except BaseException:
                stop.set();raise
        if first_error is not None:
            setup.write_json(root/'catalog/content-progress.json',{'status':'interrupted','active':[],
                'message':'Relancer la même commande pour reprendre ; aucun fichier non vérifié publié.'})
            raise first_error
        setup.write_json(root/'catalog/content-progress.json',{'status':'incomplete' if any(r['status']=='failed' for r in results) else 'done',
            'workers':workers,'active':[],'results':results})
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
    p.add_argument('--budget-gb',type=int,default=0,help='0 : pas de plafond documentaire hors laboratoire.');p.add_argument('--work-dir')
    p.add_argument('--lab',action='store_true',help='Montage Linux vérifié, marge physique contrôlée sur le SSD.')
    p.add_argument('--no-refresh',action='store_true',help='Télécharger seulement ; actualiser les services séparément hors du service de transfert.')
    p.add_argument('--jobs',type=int,choices=(1,2,3),default=2,help='Téléchargements simultanés (2 par défaut).')
    p.add_argument('--selection',type=Path,help='Plan figé créé par kiwix_select.py ; utilise ses archives sélectionnées.')
    args=p.parse_args()
    if args.selection:
        if args.pack or args.id:p.error('--selection ne se combine pas avec --pack ou --id.')
        plan=json.loads(args.selection.read_text(encoding='utf-8'))
        if plan.get('schema')!=1 or plan.get('kind')!='SetupSurvie Kiwix thematic selection':p.error('Plan de sélection Kiwix non reconnu.')
        items=catalog(args.selection);selected=items
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
    if args.budget_gb<0:p.error('Budget positif ou 0 pour aucun plafond.')
    budget=args.budget_gb*1_000_000_000 or None
    download_and_refresh(args,app,c,root,selected,budget,storage_root)


def download_and_refresh(args,app,c,root,selected,budget,storage_root):
    if app and getattr(args,'selection',None):
        import windows_resume
        windows_resume.arm_if_installed(app,c,args.selection,args.jobs)
    # Keep publication and restarts within the same backup exclusion window.
    with locked(destination(root,'catalog/publication.lock')):
        download(root,selected,budget=budget,storage_root=storage_root,workers=args.jobs)
        check_capacity(root,100_000,budget=budget,storage_root=storage_root)
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
