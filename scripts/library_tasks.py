#!/usr/bin/env python3
"""Fixed, resumable host jobs for the administrator's Kiwix library controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

import content
import discovery
import kiwix_select
import geography_data
import routing_prepare
import setup
import search_index_queue as index_queue
from delivery_paths import destination, locked

ACTIVE = {'starting', 'planning', 'downloading', 'refreshing'}


class Paused(Exception):
    pass


def shutdown(app,config,*,timeout=120):
    """User shutdown differs from an update: prevent detached jobs restarting services."""
    manager=Manager(app,config,'compose')
    state=manager.current()
    if state['phase'] in ('starting','planning','downloading'):
        try:manager.pause()
        except setup.SetupError:
            if manager.current()['phase'] in ACTIVE:raise
    import control
    control.stop(app)
    deadline=time.monotonic()+timeout
    while manager.current()['phase'] in ACTIVE:
        if time.monotonic()>=deadline:
            raise setup.SetupError('Une préparation termine encore son arrêt. Patientez puis réessayez ; les fichiers partiels sont conservés.')
        time.sleep(.2)


class Manager:
    def __init__(self, app, config, backend):
        self.app, self.config, self.backend = app, config, backend
        self.directory = app.work / 'library-web'
        self.state_path = self.directory / 'state.json'

    def read(self):
        return json.loads(self.state_path.read_text(encoding='utf-8')) if self.state_path.exists() else {'phase': 'idle'}

    def write(self, state):
        identifier = state.get('youtube_list')
        if identifier and state['phase'] in ('completed','paused','error','interrupted'):
            keys = ('id','phase','message','options','action','youtube_list')
            result = {key: state[key] for key in keys if key in state}
            result['youtube'] = self.youtube_progress(state['id'])
            setup.write_json(self.youtube_result_path(identifier),result,private=True)
        setup.write_json(self.state_path, state, private=True)

    def paths(self, job):
        if not re.fullmatch('[a-f0-9]{32}', job):
            raise setup.SetupError('Opération documentaire non valide.')
        return self.directory / job

    def check_storage(self):
        root = setup.safe_path(self.config['data_dir'])
        scope = None
        if self.backend == 'lab':
            import linux_lab as lab
            lab.checked_mount(); scope = lab.MOUNT
            if root != lab.MOUNT / 'data':
                raise setup.SetupError('Données du laboratoire hors du volume dédié.')
        content.check_capacity(root, storage_root=scope)
        return root, scope

    def current(self):
        state = self.read()
        if state['phase'] in ACTIVE:
            lost = discovery.identity(state['pid']) != state.get('identity') if state.get('pid') else time.time() - state.get('started_at', 0) > 10
            if lost:
                # The worker can finish between the first read and the PID check.
                state = self.read()
                if state['phase'] not in ACTIVE:return state
                if state.get('action')=='youtube-download':
                    child=state.get('index_pid');identity=state.get('index_identity')
                    if child and identity and discovery.identity(child)==identity:return state
                if state.get('action')=='video-inventory':
                    child=state.get('index_pid');identity=state.get('index_identity')
                    if child and identity and discovery.identity(child)==identity:return state
                    report_path=Path(self.config['data_dir'])/'state/pilot/zim-videos/progress.json'
                    try:report=json.loads(report_path.read_text(encoding='utf-8'))
                    except (OSError,ValueError):report={}
                    if report.get('job_id')==state.get('id') and report.get('phase') in ('completed','partial','paused'):
                        state.update(phase={'completed':'completed','partial':'error','paused':'paused'}[report['phase']],message='État de l’inventaire vidéo récupéré après l’arrêt du superviseur.')
                        self.write(state);return state
                if state.get('action')=='index':
                    child=state.get('index_pid');identity=state.get('index_identity')
                    if child and identity and discovery.identity(child)==identity:return state
                    from pilot.archive_index import status as index_status
                    root=Path(self.config['data_dir']);report=index_status(root/'state/pilot/archive-index')
                    if state.get('id') and report.get('job_id')==state['id'] and report.get('phase') in ('completed','partial','paused'):
                        index_queue.acknowledge(root,state.get('options',{}).get('selection',{}),report)
                        state.update(phase={'completed':'completed','partial':'error','paused':'paused'}[report['phase']],message='État de l’indexation récupéré après l’arrêt du superviseur.')
                        self.reader_failed(report,state)
                        if report['phase']=='partial':index_queue.hold(root,'error')
                        self.write(state);return state
                    index_queue.hold(root,'interrupted')
                state.update(phase='interrupted', message='Opération interrompue. Préparez une nouvelle sélection pour reprendre les fichiers partiels.')
                self.write(state)
        return state

    def status(self):
        state = self.current()
        result = {k: state[k] for k in ('phase', 'message', 'options', 'id', 'reader_probe') if k in state}
        result['index_reader_ready']=self.index_ready()
        result['initial_video_inventory_pending'] = (self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST).is_file()
        result['index_queue']=index_queue.summary(Path(self.config['data_dir']))
        queued=result['index_queue'];waiting=''
        if queued['pending']:
            if queued['hold']:waiting=queued['hold']
            elif not queued['settings']['enabled']:waiting='disabled'
            elif index_queue.gaming(self.app.work):waiting='gaming'
            elif not index_queue.in_window(queued['settings']):waiting='schedule'
            elif not result['index_reader_ready']:waiting='missing_reader'
            elif state['phase']=='planned':waiting='selection_pending'
            elif state['phase'] in ACTIVE:waiting='other_operation' if state.get('action')!='index' else ''
            else:waiting=index_queue.read(Path(self.config['data_dir'])).get('last_attempt',{}).get('reason','')
        queued['waiting_reason']=waiting
        from pilot.archive_index import status as index_status
        result['search_index']=index_status(Path(self.config['data_dir'])/'state/pilot/archive-index')
        result.update(available=True, themes=[{'id': k, 'label': v['label']} for k, v in kiwix_select.themes().items()])
        result['action']=state.get('action')
        if state.get('action')=='youtube-download' and state.get('id'):
            result['youtube']=self.youtube_progress(state['id'])
            result['youtube_list']=state.get('youtube_list')
        if state.get('id'):
            if state['phase'] in ACTIVE and (self.paths(state['id']) / 'cancel').exists():
                result.update(pause_requested=True, message='Pause demandée. Attente de la fin de l’échange en cours ; les fichiers partiels seront conservés.')
            plan_path = self.paths(state['id']) / 'plan.json'
            if plan_path.is_file():
                plan = json.loads(plan_path.read_text(encoding='utf-8'))
                result['plan'] = {k: plan[k] for k in ('candidates', 'remaining_download_bytes', 'missing_themes', 'library_bytes')}
                result['plan']['count'] = len(plan['items'])
                result['plan']['legacy_selection'] = 'include_supplements' not in plan
                result['plan']['learning_coverage'] = plan.get('learning_coverage',[])
            if state['phase'] == 'downloading':
                progress = Path(self.config['data_dir']) / 'catalog/content-progress.json'
                if progress.is_file():
                    value = json.loads(progress.read_text(encoding='utf-8'))
                    result['progress'] = {k: value[k] for k in ('id', 'bytes', 'total', 'status', 'workers') if k in value}
                    result['progress']['active'] = [{k: entry[k] for k in ('id','title','bytes','total','status') if k in entry} for entry in value.get('active',[])]
        return result

    def auto_index(self):
        root=Path(self.config['data_dir']);state=self.current();queue=index_queue.read(root)
        gaming = index_queue.gaming(self.app.work)
        allowed=queue['settings']['enabled'] and index_queue.in_window(queue['settings']) and not gaming
        if state['phase'] in ACTIVE:
            if state.get('action')=='video-inventory' and gaming:
                self.pause(automatic=True)
            if state.get('action')=='index' and state.get('options',{}).get('automatic') and not allowed:
                self.pause(automatic=True)
            return
        request = self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST
        if (self.backend == 'compose' and state['phase'] != 'planned' and request.is_file()
                and not gaming and self.index_ready()):
            with locked(destination(root, 'catalog/content.lock')), locked(destination(root, 'catalog/publication.lock')):
                self.start('video-inventory', {'automatic': True})
            return
        automatic = state.get('options', {}).get('automatic')
        resumable = state['phase'] == 'paused' and state.get('action') == 'index' and automatic
        initial_video_error = state['phase'] == 'error' and state.get('action') == 'video-inventory' and automatic
        if state['phase'] not in ('idle', 'completed') and not (resumable or initial_video_error):
            return
        if not allowed or not queue['pending'] or queue.get('hold') or not self.index_ready():return
        try:
            # Never start during any CLI/web content publication or backup.
            with locked(destination(root,'catalog/content.lock')),locked(destination(root,'catalog/publication.lock')):
                self.start('index',{'automatic':True})
                with index_queue.edit(root) as value:value.pop('last_attempt',None)
        except setup.SetupError as exc:
            reason='source_changed' if isinstance(exc,index_queue.SourceChanged) else 'insufficient_storage' if 'marge' in str(exc).lower() or 'budget' in str(exc).lower() else 'operation_busy'
            with index_queue.edit(root) as value:
                previous=value.get('last_attempt',{})
                if previous.get('reason')!=reason or time.time()-previous.get('at',0)>60:value['last_attempt']={'reason':reason,'at':time.time()}
            return

    def index_ready(self):
        import search_index_tools
        return search_index_tools.ready(self.app)

    def index_python(self):
        return self.app.work/'search-tools'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


    def reader_failed(self,report,state):
        result=report.get('reader_probe',{})
        if result.get('ok') is not False:return False
        import index_reader_probe
        (self.app.work/'search-tools/reader-ready.json').unlink(missing_ok=True)
        state.update(reader_probe=result,phase='error',message=index_reader_probe.MESSAGES.get(result.get('error'),index_reader_probe.MESSAGES['probe_unavailable']))
        return True

    def start(self, action, body):
        with locked(destination(self.app.work, 'library-web/operation.lock')):
            return self.start_locked(action, body)

    def start_locked(self, action, body):
        state = self.current()
        if state['phase'] in ACTIVE:
            raise setup.SetupError('Une opération documentaire est déjà en cours.')
        self.check_storage()
        if action in ('index','index-prepare','video-inventory'):
            if action in ('index','video-inventory') and not self.index_ready():raise setup.SetupError('Préparez d’abord l’outil d’indexation depuis les réglages.')
            if action=='video-inventory' and index_queue.gaming(self.app.work):raise setup.SetupError('Le mode jeu est actif. Reprenez l’inventaire vidéo après la pause ; les résultats terminés restent disponibles.')
            automatic=body.get('automatic') is True
            root=Path(self.config['data_dir'])
            selection=index_queue.read(root)['pending'] if action=='index' else {}
            if action=='index' and automatic:index_queue.validate_selection(root,selection)
            if action=='index' and not automatic:index_queue.hold(root,'')
            state={'id':uuid.uuid4().hex,'phase':'starting','options':{'automatic':automatic,'selection':selection}}
            self.paths(state['id']).mkdir(parents=True)
        elif action=='youtube-download':
            state=self.youtube_job(state,body)
        elif action in ('geography','routing'):
            options = geography_data.validate(body)
            state = {'id': uuid.uuid4().hex, 'phase': 'starting', 'options': options}
            self.paths(state['id']).mkdir(parents=True)
        elif action == 'plan':
            requested = body.get('themes')
            size = body.get('max_add_gb', 0)
            languages = body.get('languages', ['fr', 'en'])
            supplements=body.get('include_supplements',False)
            if type(supplements) is not bool:raise setup.SetupError('Choix des compléments non valide.')
            if not isinstance(requested, list) or not requested or len(requested) > len(kiwix_select.themes()) or any(not isinstance(t, str) or t not in kiwix_select.themes() for t in requested):
                raise setup.SetupError('Choisissez au moins un thème proposé.')
            if type(size) is not int or size < 0:
                raise setup.SetupError('Le plafond de téléchargement doit être positif, ou 0 pour tous les ajouts possibles.')
            if not isinstance(languages, list) or not languages or any(l not in ('fr', 'en') for l in languages):
                raise setup.SetupError('Choisissez le français, l’anglais ou les deux.')
            state = {'id': uuid.uuid4().hex, 'phase': 'starting', 'options': {
                'themes': list(dict.fromkeys(requested)), 'max_add_gb': size, 'languages': list(dict.fromkeys(languages)),'include_supplements':supplements}}
            self.paths(state['id']).mkdir(parents=True)
        elif action == 'download':
            if body.get('id') != state.get('id') or state['phase'] not in ('planned', 'paused', 'error'):
                raise setup.SetupError('Préparez une sélection avant de télécharger.')
            plan_path = self.paths(state['id']) / 'plan.json'
            if not plan_path.is_file() or not content.catalog(plan_path):
                raise setup.SetupError('Cette sélection ne contient aucun ajout à télécharger.')
            state['phase'] = 'starting'
        else:
            raise setup.SetupError('Action documentaire inconnue.')
        folder = self.paths(state['id'])
        (folder / 'cancel').unlink(missing_ok=True)
        (folder / 'ready').unlink(missing_ok=True)
        state.update(action=action, pid=None, started_at=time.time(), message='Préparation de l’opération…')
        self.write(state)
        try:
            kwargs = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
            with (folder / 'worker.log').open('ab') as log:
                process = subprocess.Popen([sys.executable, str(setup.ROOT / 'scripts/library_tasks.py'),
                    '--work-dir', str(self.app.work), '--backend', self.backend, '--job', state['id']],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log, **kwargs)
            state.update(pid=process.pid, identity=discovery.identity(process.pid))
            if not state['identity']:
                raise setup.SetupError('Le processus documentaire ne peut pas être suivi.')
            self.write(state); (folder / 'ready').touch()
        except Exception:
            state.update(phase='error', message='Le transfert n’a pas pu démarrer. Réessayez depuis le PC serveur.')
            self.write(state); raise
        if action == 'video-inventory':
            (self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST).unlink(missing_ok=True)

    def youtube_job(self,previous,body):
        """A list saved by the site in state/pilot/youtube-lists, or the paused one."""
        if body.get('resume') is True:
            if previous.get('action')!='youtube-download' or previous['phase'] not in ('paused','interrupted','error'):
                raise setup.SetupError('Aucun téléchargement YouTube à reprendre.')
            text=(self.paths(previous['id'])/'liste.txt').read_text(encoding='utf-8');height=previous['options']['max_height'];identifier=previous.get('youtube_list')
        else:
            identifier=body.get('list');height=body.get('max_height',480)
            if not isinstance(identifier,str) or not re.fullmatch('[a-f0-9]{32}',identifier):raise setup.SetupError('Liste de vidéos non valide.')
            if height not in (360,480,720):raise setup.SetupError('Qualité non valide : 360, 480 ou 720.')
            source=Path(self.config['data_dir'])/'state/pilot/youtube-lists'/(identifier+'.txt')
            if source.is_symlink() or not source.is_file() or source.stat().st_size>300_000:raise setup.SetupError('Liste de vidéos introuvable ; déposez-la de nouveau.')
            text=source.read_text(encoding='utf-8')
        from pilot.youtube_list import parse_list
        entries,_=parse_list(text)
        if not entries:raise setup.SetupError('La liste ne contient aucune adresse de vidéo YouTube valide.')
        state={'id':uuid.uuid4().hex,'phase':'starting','options':{'max_height':height,'videos':len(entries)},'youtube_list':identifier}
        folder=self.paths(state['id']);folder.mkdir(parents=True)
        setup.write_json(folder/'liste.json',{'count':len(entries)},private=True)
        (folder/'liste.txt').write_text(text,encoding='utf-8')
        if identifier:self.youtube_result_path(identifier).unlink(missing_ok=True)
        return state

    def youtube_result_path(self, identifier):
        if not re.fullmatch('[a-f0-9]{32}', identifier):
            raise setup.SetupError('Liste de vidéos non valide.')
        return self.directory / 'youtube-results' / (identifier + '.json')

    def youtube_result(self, identifier):
        path = self.youtube_result_path(identifier)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def youtube_progress(self,job):
        try:return json.loads((self.paths(job)/'progress.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):return {}

    def pause(self,automatic=False,*,state=None):
        if state is None:state = self.current()
        if state['phase'] not in ('starting', 'planning', 'downloading'):
            raise setup.SetupError('Aucun téléchargement ou recherche à mettre en pause.')
        if state.get('action')=='index' and not automatic:index_queue.hold(Path(self.config['data_dir']),'user')
        (self.paths(state['id']) / 'cancel').touch()

    def run(self, job):
        folder = self.paths(job)
        for _ in range(100):
            if (folder / 'ready').exists(): break
            time.sleep(.05)
        else: return
        state = self.read()
        if state.get('id') != job: return
        def update(phase, message):
            state.update(phase=phase, message=message); self.write(state)
        def check():
            if (folder / 'cancel').exists(): raise Paused()
        try:
            root, scope = self.check_storage()
            check()
            if state['action']=='youtube-download':
                update('downloading','Téléchargement des vidéos YouTube et de leurs sous-titres…')
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                command=[sys.executable,'-X','utf8',str(setup.ROOT/'scripts/youtube_videos.py'),'download',str(folder/'liste.txt'),
                    '--data-dir',str(root),'--max-height',str(state['options']['max_height']),'--progress',str(folder/'progress.json'),'--cancel',str(folder/'cancel')]
                with (folder/'youtube.log').open('ab') as log:
                    process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**hidden)
                    state.update(index_pid=process.pid,index_identity=discovery.identity(process.pid));self.write(state)
                    code=process.wait()
                report=self.youtube_progress(job)
                if report.get('phase')=='paused' or (folder/'cancel').exists():raise Paused()
                if code not in (0,2) or report.get('phase')!='completed':
                    raise setup.SetupError('Le téléchargement des vidéos n’a pas pu se terminer. Vérifiez Internet et l’espace libre, puis reprenez : les vidéos déjà rangées sont conservées.')
                counts=report.get('counts',{})
                update('completed',f"Téléchargement terminé : {counts.get('downloaded',0)} vidéo(s) ajoutée(s), {counts.get('skipped',0)} déjà présente(s), "
                       f"{counts.get('error',0)+counts.get('refused',0)} non téléchargée(s). "
                       +(f"{report['remaining']} restante(s), à reprendre après avoir libéré de l’espace. " if report.get('remaining') else '')
                       +'Le site répertorie les vidéos téléchargées.')
            elif state['action']=='index-prepare':
                update('downloading','Préparation de l’outil de recherche (Internet requis une seule fois)…')
                import search_index_tools
                search_index_tools.prepare(self.app,self.config,check=check,force=True)
                state['reader_probe']=json.loads((self.app.work/'search-tools/reader-ready.json').read_text(encoding='utf-8')).get('probe')
                update('completed','Outil d’indexation prêt. La création des index peut fonctionner hors ligne.')
            elif state['action']=='video-inventory':
                update('downloading','Examen des vidéos et pistes dans les collections, sans Internet ni IA…')
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                command=[str(self.index_python()),'-X','utf8',str(setup.ROOT/'scripts/inventory_zim_videos.py'),
                    '--zim-dir',str(root/'library/zim'),'--state-dir',str(root/'state/pilot'),'--cancel',str(folder/'cancel'),'--job-id',job]
                workers=index_queue.read(root)['settings']['workers']
                if workers:command+=['--workers',str(workers)]
                process=subprocess.Popen(command,**hidden)
                state.update(index_pid=process.pid,index_identity=discovery.identity(process.pid));self.write(state)
                code=process.wait();check()
                report=json.loads((root/'state/pilot/zim-videos/progress.json').read_text(encoding='utf-8'))
                if code or report.get('job_id')!=job or report.get('phase')!='completed':raise setup.SetupError('Certaines collections n’ont pas pu être examinées. Les inventaires terminés restent disponibles ; consultez le rapport vidéo.')
                update('completed','Inventaire des vidéos terminé. Leur présence ne valide pas leur lecture ou leurs sous-titres.')
            elif state['action']=='index':
                update('downloading','Indexation locale des archives, sans IA. La bibliothèque reste accessible…')
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                command=[str(self.index_python()),'-X','utf8',str(setup.ROOT/'scripts/index_archives.py'),'--zim-dir',str(root/'library/zim'),'--state-dir',str(root/'state/pilot'),'--cancel',str(folder/'cancel'),'--job-id',job]
                if state['options'].get('automatic'):
                    selection=folder/'index-selection.json'
                    setup.write_json(selection,[Path(p).name for p in state['options']['selection']],private=True)
                    command+=['--selection',str(selection)]
                workers=index_queue.read(root)['settings']['workers']
                if workers:command+=['--workers',str(workers)]
                process=subprocess.Popen(command,**hidden)
                state.update(index_pid=process.pid,index_identity=discovery.identity(process.pid));self.write(state)
                code=process.wait()
                from pilot.archive_index import status as index_status
                report=index_status(root/'state/pilot/archive-index')
                if any(r.get('error') in ('ImportError','ModuleNotFoundError') for r in report.get('results',[])):(self.app.work/'search-tools/reader-ready.json').unlink(missing_ok=True)
                if report.get('job_id')==job and self.reader_failed(report,state):
                    import search_index_tools
                    self.write(state)
                    raise search_index_tools.ReaderUnavailable(report['reader_probe'])
                if report.get('job_id')==job:index_queue.acknowledge(root,state['options'].get('selection',{}),report)
                check()
                if code:raise setup.SetupError('Certaines archives n’ont pas pu être indexées ; consultez le suivi.')
                update('completed','Indexation terminée. Les nouveaux passages sont disponibles dans la recherche.')
            elif state['action'] == 'routing':
                update('downloading', 'Préparation des routes et chemins hors ligne…')
                routing_prepare.prepare_area(root, state['options'], backend=self.backend, storage_root=scope, check=check,
                    progress=lambda message: update('downloading', message))
                check(); update('refreshing', 'Démarrage des moteurs de calcul de trajets…')
                routing_prepare.start_services(self.app,self.config,self.backend)
                update('completed', 'Routes et chemins préparés pour la marche, la moto et la petite voiture.')
            elif state['action'] == 'geography':
                update('downloading', 'Préparation de la géographie hors ligne…')
                geography_data.prepare(root, state['options'], storage_root=scope, check=check,
                    progress=lambda message: update('downloading', message))
                update('completed', 'Adresses, lieux et relief sélectionné prêts hors ligne.')
            elif state['action'] == 'plan':
                update('planning', 'Recherche des collections adaptées à vos thèmes…')
                def reader(*args, **kwargs):
                    check(); return kiwix_select.fetch(*args, **kwargs)
                raw = reader(kiwix_select.CATALOG_URL)
                options = state['options']
                plan = kiwix_select.select(kiwix_select.parse_feed(raw), root, options['themes'],
                    languages=tuple(kiwix_select.LANGUAGES[l] for l in options['languages']),
                    max_add=options['max_add_gb'] * 1_000_000_000 or None, storage_root=scope, reader=reader,include_supplements=options.get('include_supplements',False))
                check(); plan['catalog_sha256'] = hashlib.sha256(raw).hexdigest()
                setup.write_json(folder / 'plan.json', plan, private=True)
                update('planned', 'Sélection prête. Vérifiez les ajouts proposés avant de télécharger.')
            else:
                items = content.catalog(folder / 'plan.json')
                update('downloading', 'Téléchargement et vérification des archives…')
                # Use the existing downloader and its lock, integrity and budget checks.
                # Cancellation is checked before each network request/write/hash block.
                import windows_resume
                windows_resume.arm_if_installed(self.app,self.config,folder/'plan.json',2)
                import content_retry
                pending=content_retry.remaining(root,items)
                content.download(root, pending, storage_root=scope, workers=2, cancelled=lambda: (folder / 'cancel').exists())
                check(); update('refreshing', 'Mise à disposition des nouvelles collections…')
                self.app.catalog(self.config)
                if self.backend == 'lab':
                    import linux_lab as lab
                    lab.podman('restart', lab.PREFIX + 'kiwix', *([lab.PREFIX+'pilot'] if any(i['path'].startswith('library/guides/') for i in items) else []), capture=True)
                else:
                    self.app.compose(self.config, 'restart', 'kiwix', *(['pilot'] if any(i['path'].startswith('library/guides/') for i in items) else []))
                update('completed', 'Archives téléchargées et vérifiées. La bibliothèque est actualisée.')
        except (Paused, content.DownloadPaused):
            update('paused', 'Préparation géographique arrêtée. Les zones existantes sont conservées ; relancez cette zone pour recommencer.' if state.get('action') in ('geography','routing') else 'Téléchargement YouTube en pause. Les vidéos rangées et la vidéo en cours sont conservées ; « Reprendre » continue la liste.' if state.get('action')=='youtube-download' else 'Opération mise en pause. Les fichiers partiels sont conservés pour la reprise.')
        except Exception as exc:
            if state.get('action')=='index':index_queue.hold(Path(self.config['data_dir']),'error')
            if state.get('action') in ('index','index-prepare') and getattr(exc,'report',None):state['reader_probe']=exc.report
            print(type(exc).__name__, str(exc), flush=True)
            update('error',getattr(exc,'public_message',None) or ('L’indexation ou sa préparation a échoué ; les anciens index restent disponibles. Vérifiez le suivi et l’espace libre.' if state.get('action') in ('index','index-prepare') else 'L’opération a échoué. Les fichiers existants sont conservés. Vérifiez la connexion Internet et l’espace libre, puis réessayez.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True); parser.add_argument('--backend', choices=['lab', 'compose'], required=True)
    parser.add_argument('--job', required=True); args = parser.parse_args()
    app = setup.Installation(args.work_dir)
    Manager(app, app.load(), args.backend).run(args.job)
