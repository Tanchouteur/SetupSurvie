"""Opt-in Windows boot recovery for one pinned library plan, independent of AI."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time


def runtime(work_dir):
    work=Path(work_dir).resolve()
    config=json.loads((work/'settings.json').read_text(encoding='utf-8-sig'))
    application=Path(config['app_dir']).resolve()
    if config['target']!='windows' or not application.is_dir():
        raise ValueError('Application Windows installée requise.')
    sys.path.insert(0,str(application/'scripts'))
    import setup
    return setup.Installation(work),config


def configure(work_dir, selection, jobs=2):
    app,config=runtime(work_dir)
    import setup,content
    if type(jobs) is not int or not 1<=jobs<=3:raise ValueError('Un à trois transferts requis.')
    root=setup.safe_path(config['data_dir'])
    plan=Path(selection).resolve()
    if not plan.is_relative_to((root/'catalog').resolve()):
        raise ValueError('Le plan doit être conservé dans le catalogue de cette installation.')
    value=json.loads(plan.read_text(encoding='utf-8'))
    if value.get('schema')!=1 or value.get('kind')!='SetupSurvie Kiwix thematic selection':
        raise ValueError('Plan figé Kiwix non reconnu.')
    if not content.catalog(plan):raise ValueError('Sélection vide.')
    state={'schema':1,'enabled':True,'selection':str(plan),'sha256':setup.file_hash(plan),
           'data_dir':str(root),'jobs':jobs,'inference_autostart':False}
    setup.write_json(app.work/'content-resume.json',state,private=True)
    # This durable preference is used by setup.up from 0.1.27. The login
    # wrapper also supports older installed launchers with the pause marker.
    config['inference_autostart']=False
    setup.write_json(app.settings_path,config,private=True)
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
    import setup,content_retry
    from delivery_paths import locked
    root=setup.safe_path(config['data_dir'])
    state=json.loads((app.work/'content-resume.json').read_text(encoding='utf-8'))
    if state.get('schema')!=1 or state.get('enabled') is not True:return 'disabled'
    if setup.safe_path(state['data_dir'])!=root:raise ValueError('Le dossier de données a changé ; réactiver explicitement la reprise.')
    plan=Path(state['selection']).resolve()
    if not plan.is_relative_to((root/'catalog').resolve()) or setup.file_hash(plan)!=state['sha256']:
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
    guard=locked(root/'catalog/content-supervisor.lock')
    try:guard.__enter__()
    except setup.SetupError as exc:
        if isinstance(exc.__cause__,OSError):return 'already_running'
        raise
    try:
        if (root/'catalog/content-supervisor.pause').exists():return 'paused'
        import content
        items=content.catalog(plan)
        if not content_retry.remaining(root,items):return 'complete'
        log=root/'diagnostics/bibliotheque-auto.log'
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a',encoding='utf-8',buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
            setup.write_json(root/'diagnostics/bibliotheque-transfer.json',{
                'pid':os.getpid(),'identity':app.native_identity(os.getpid()),'started':time.time(),
                'plan':str(plan),'log':str(log),'errors':str(log),'state':'reprise_automatique',
                'supervision':str(root/'catalog/content-retry.json')})
            print('Reprise automatique Windows ; aucun démarrage du moteur IA.',flush=True)
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('enable','run','probe','prepare-login','disable'))
    parser.add_argument('--work-dir',required=True)
    parser.add_argument('--selection');parser.add_argument('--jobs',type=int,choices=(1,2,3),default=2)
    args=parser.parse_args()
    if args.action=='enable':
        if not args.selection:parser.error('--selection requis.')
        print(configure(args.work_dir,args.selection,args.jobs));return
    if args.action=='prepare-login':prepare_login(args.work_dir);return
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
