"""Automatic recovery of one pinned library plan after a restart, independent of AI.

Windows runs it from the startup task; Linux from the controller service."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time


PLAN_KINDS=('SetupSurvie Kiwix thematic selection','SetupSurvie library reference')


def runtime(work_dir):
    work=Path(work_dir).resolve()
    config=json.loads((work/'settings.json').read_text(encoding='utf-8-sig'))
    application=Path(config['app_dir']).resolve()
    if config['target'] not in ('windows','linux') or not application.is_dir():
        raise ValueError('Application installée requise.')
    sys.path.insert(0,str(application/'scripts'))
    import setup
    return setup.Installation(work),config


def authorized_plan_path(work,root,plan):
    if plan.is_relative_to((root/'catalog').resolve()):return True
    folder=(work/'library-web').resolve()
    try:parts=plan.relative_to(folder).parts
    except ValueError:return False
    import re
    return len(parts)==2 and re.fullmatch('[a-f0-9]{32}',parts[0]) is not None and parts[1]=='plan.json'


def configure(work_dir, selection, jobs=2):
    app,config=runtime(work_dir)
    import setup,content
    if type(jobs) is not int or not 1<=jobs<=3:raise ValueError('Un à trois transferts requis.')
    root=setup.safe_path(config['data_dir'])
    plan=Path(selection).resolve()
    if not authorized_plan_path(app.work,root,plan):
        raise ValueError('Le plan doit être conservé dans le catalogue de cette installation.')
    value=json.loads(plan.read_text(encoding='utf-8'))
    if value.get('schema')!=1 or value.get('kind') not in PLAN_KINDS:
        raise ValueError('Plan figé Kiwix ou fonds de référence non reconnu.')
    if not content.catalog(plan) and not (value.get('restoration') and plan.parent.parent == (app.work/'library-web').resolve()):
        raise ValueError('Sélection vide.')
    state={'schema':1,'enabled':True,'selection':str(plan),'sha256':setup.file_hash(plan),
           'data_dir':str(root),'jobs':jobs}
    setup.write_json(app.work/'content-resume.json',state,private=True)
    if config['target']!='windows':return app.work/'content-resume.json'
    stable=Path(config['app_dir']).parent/'maintenance/windows_resume.py'
    stable.parent.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).resolve()
    from pilot import durable
    for name in ('windows_resume.py','register-windows-resume.ps1','start-without-inference.ps1'):
        origin=source.with_name(name);target=stable.with_name(name)
        if origin.resolve()!=target.resolve():
            temp=target.with_suffix(target.suffix+'.pending')
            shutil.copyfile(origin,temp);durable.sync_file(temp);durable.publish(temp,target)
    return stable


def run(work_dir, *, probe=False):
    app,config=runtime(work_dir)
    if (app.work/"transfer-guard.json").exists():return "transfer_paused"
    import setup,content_retry
    from delivery_paths import locked
    root=setup.safe_path(config['data_dir'])
    state_path=app.work/'content-resume.json'
    if not state_path.is_file():return 'disabled'
    state=json.loads(state_path.read_text(encoding='utf-8'))
    if state.get('schema')!=1 or state.get('enabled') is not True:return 'disabled'
    if setup.safe_path(state['data_dir'])!=root:raise ValueError('Le dossier de données a changé ; réactiver explicitement la reprise.')
    plan=Path(state['selection']).resolve()
    if not authorized_plan_path(app.work,root,plan) or setup.file_hash(plan)!=state['sha256']:
        raise ValueError('Le plan a changé ; réactiver explicitement la reprise.')
    if type(state['jobs']) is not int or not 1<=state['jobs']<=3:raise ValueError('Nombre de transferts incorrect.')
    journal=app.work/'update.json'
    if journal.exists() and json.loads(journal.read_text(encoding='utf-8')).get('phase') not in ('complete','rolled_back'):
        raise ValueError('Mise à jour non terminée ; reprise différée.')
    if (root/'catalog/content-supervisor.pause').exists():return 'paused'
    # Probe runs under the real task account, without downloads, so verify its
    # public HTTPS access before declaring boot recovery ready.
    if probe:
        import urllib.request
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                'https://download.kiwix.org/',timeout=20) as response:
            if response.status!=200:raise ValueError('Test HTTPS refusé.')
            response.read(1024)
        setup.write_json(root/'diagnostics/windows-resume-probe.json',
                         {'ok':True,'https':True,'pid':os.getpid(),'time':time.time()})
        return 'probe_ok'
    # CLI and web downloads can hold only content.lock. Do not steal their
    # progress metadata when the installer watcher checks every five minutes.
    try:
        with locked(root/'catalog/content.lock'):pass
    except setup.SetupError as exc:
        if isinstance(exc.__cause__,OSError):return 'already_running'
        raise
    guard=locked(root/'catalog/content-supervisor.lock')
    try:guard.__enter__()
    except setup.SetupError as exc:
        if isinstance(exc.__cause__,OSError):return 'already_running'
        raise
    try:
        if (root/'catalog/content-supervisor.pause').exists():return 'paused'
        import content
        items=content.catalog(plan)
        web_job=plan.parent.name if plan.parent.parent==(app.work/'library-web').resolve() else None
        if not web_job and not content_retry.remaining(root,items):return 'complete'
        if web_job and (plan.parent/'cancel').exists():return 'paused'
        log=root/'diagnostics/bibliotheque-auto.log'
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a',encoding='utf-8',buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
            setup.write_json(root/'diagnostics/bibliotheque-transfer.json',{
                'pid':os.getpid(),'identity':app.native_identity(os.getpid()),'started':time.time(),
                'plan':str(plan),'log':str(log),'errors':str(log),'state':'reprise_automatique',
                'supervision':str(root/'catalog/content-retry.json')})
            print('Reprise automatique du téléchargement ; aucun démarrage du moteur IA.',flush=True)
            if web_job:
                import library_tasks
                manager=library_tasks.Manager(app,config,'compose')
                web_state=manager.read()
                if web_state.get('id')!=web_job or web_state.get('action')!='download':
                    raise ValueError('La sélection web a changé ; reprise explicite nécessaire.')
                if web_state.get('phase')=='completed':return 'complete'
                web_state.update(pid=os.getpid(),identity=app.native_identity(os.getpid()),started_at=time.time())
                manager.write(web_state);manager.run(web_job)
                result=manager.read()
                if result['phase']=='completed':return 'complete'
                if result['phase']=='paused':return 'paused'
                raise OSError('Reprise web incomplète : '+result.get('message','consulter le journal'))

            complete=content_retry.supervise(root,items,workers=state['jobs'],
                cancelled=lambda:(root/'catalog/content-supervisor.pause').exists())
            if not complete:raise OSError('Des contenus restent en attente ; prochaine reprise programmée.')
        return 'complete'
    finally:guard.__exit__(None,None,None)


def prepare_login(work_dir):
    """Set a pause only on a new Windows session, never during enable/probe."""
    app,config=runtime(work_dir)
    import setup
    if config.get('inference_autostart') is False:
        marker=app.work/'inference-paused.json'
        if not marker.exists():setup.write_json(marker,{'reason':'windows_no_inference_autostart'},private=True)


def frozen_plan(root,selection):
    """Keep the reference manifest used for a download inside the installation catalogue."""
    import setup,content
    plan=Path(selection).resolve()
    value=json.loads(plan.read_text(encoding='utf-8'))
    if value.get('kind')!='SetupSurvie library reference' or plan.is_relative_to((root/'catalog').resolve()):return plan
    target=content.destination(root,'catalog/library-reference-'+setup.file_hash(plan)[:16]+'.json')
    if not target.exists():setup.write_json(target,value)
    return target


def arm_if_installed(app,config,selection,jobs=2):
    """Windows: when the startup task is installed. Linux: the controller service resumes."""
    if not config.get('app_dir'):return
    if config.get('target')=='linux':configure(app.work,selection,jobs);return
    if config.get('target')!='windows':return
    marker=Path(config['app_dir']).parent/'maintenance/startup-settings.json'
    if marker.is_file():configure(app.work,selection,jobs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('enable','run','probe','prepare-login','disable','pause-site'))
    parser.add_argument('--work-dir',required=True)
    parser.add_argument('--selection');parser.add_argument('--jobs',type=int,choices=(1,2,3),default=2)
    args=parser.parse_args()
    if args.action=='enable':
        if not args.selection:parser.error('--selection requis.')
        print(configure(args.work_dir,args.selection,args.jobs));return
    if args.action=='prepare-login':prepare_login(args.work_dir);return
    if args.action=='pause-site':
        app,_=runtime(args.work_dir);import setup
        setup.write_json(app.work/'startup-paused.json',{'reason':'user_shutdown'},private=True);return
    if args.action=='disable':
        app,_=runtime(args.work_dir);import setup
        state=json.loads((app.work/'content-resume.json').read_text(encoding='utf-8'))
        state['enabled']=False;setup.write_json(app.work/'content-resume.json',state,private=True);return
    print(run(args.work_dir,probe=args.action=='probe'))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        # pythonw has no console: retain a useful diagnostic without secrets.
        try:
            app,config=runtime(sys.argv[sys.argv.index('--work-dir')+1]);import setup
            setup.write_json(Path(config['data_dir'])/'diagnostics/windows-resume-error.json',
                             {'error':str(exc),'time':time.time()})
        except Exception:pass
        sys.exit(1)
