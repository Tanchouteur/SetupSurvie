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
import collection_tasks
from pilot import category_index, collection_sort, zim_video_inventory
import discovery
import kiwix_select
import geography_data
import routing_prepare
import setup
import search_index_queue as index_queue
from delivery_paths import destination, locked

ACTIVE = {'starting', 'planning', 'downloading', 'refreshing'}
QUEUE_PREPARATIONS = {'index', 'index-prepare', 'category-index', 'video-inventory'}


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

    def check_storage(self,reserve=15_000_000_000):
        root = setup.safe_path(self.config['data_dir'])
        scope = None
        if self.backend == 'lab':
            import linux_lab as lab
            lab.checked_mount(); scope = lab.MOUNT
            if root != lab.MOUNT / 'data':
                raise setup.SetupError('Données du laboratoire hors du volume dédié.')
        content.check_capacity(root, storage_root=scope, reserve=reserve)
        return root, scope

    def current(self):
        state = self.read()
        if state['phase'] in ACTIVE:
            lost = discovery.identity(state['pid']) != state.get('identity') if state.get('pid') else time.time() - state.get('started_at', 0) > 10
            if lost:
                # The worker can finish between the first read and the PID check.
                state = self.read()
                if state['phase'] not in ACTIVE:return state
                if state.get('action') in ('youtube-download','category-index'):
                    child=state.get('index_pid');identity=state.get('index_identity')
                    if child and identity and discovery.identity(child)==identity:return state
                    if state.get('action')=='category-index':
                        root=Path(self.config['data_dir'])/'state/pilot'
                        report=category_index.read_status(root)
                        if report.get('job_id')==state.get('id') and report['phase'] in ('completed','paused'):
                            state.update(phase=report['phase'],message='État de la préparation Wikipédia récupéré.')
                            self.write(state)
                            return state
                if state.get('action')=='video-inventory':
                    child=state.get('index_pid');identity=state.get('index_identity')
                    if child and identity and discovery.identity(child)==identity:return state
                    report_path=Path(self.config['data_dir'])/'state/pilot/zim-videos/progress.json'
                    try:report=json.loads(report_path.read_text(encoding='utf-8'))
                    except (OSError,ValueError):report={}
                    if report.get('job_id')==state.get('id') and report.get('phase') in ('completed','partial','paused'):
                        phase = report['phase']
                        if zim_video_inventory.partial_with_all_archives(report):
                            state.update(phase='completed', message=zim_video_inventory.LIMITED_INVENTORY_MESSAGE)
                        else:
                            state.update(phase='error' if phase == 'partial' else phase,
                                         message='État de l’inventaire vidéo récupéré après l’arrêt du superviseur.')
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
                message = ('Téléchargement interrompu. Retrouvez la reprise dans la File d’attente.'
                           if state.get('action') == 'download' else 'Opération interrompue. Relancez la préparation.')
                state.update(phase='interrupted', message=message)
                self.write(state)
        return state

    def status(self):
        state = self.current()
        result = {k: state[k] for k in ('phase', 'message', 'options', 'id', 'reader_probe') if k in state}
        result['index_reader_ready']=self.index_ready()
        result['initial_video_inventory_pending'] = (self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST).is_file()
        result['index_queue']=index_queue.summary(Path(self.config['data_dir']))
        queued=result['index_queue']
        queued['waiting_reason']=self.index_waiting_reason(queued, state, result['index_reader_ready'])
        from pilot.archive_index import status as index_status
        result['search_index']=index_status(Path(self.config['data_dir'])/'state/pilot/archive-index')
        root=Path(self.config['data_dir'])
        result['category_index']=category_index.availability(root/'library/zim',root/'state/pilot',collection_sort.load(root/'catalog'))[0]
        if result['category_index']['phase']=='running' and (state.get('action')!='category-index' or state['phase'] not in ACTIVE):
            result['category_index']['phase']='interrupted'
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

    def index_waiting_reason(self, queued, state, reader_ready):
        if not queued['pending']:return ''
        if queued['hold']:return queued['hold']
        if not queued['settings']['enabled']:return 'disabled'
        if index_queue.gaming(self.app.work):return 'gaming'
        if not index_queue.in_window(queued['settings']):return 'schedule'
        if not reader_ready:return 'missing_reader'
        if state['phase']=='planned':return 'selection_pending'
        if state['phase'] in ACTIVE:return 'other_operation' if state.get('action')!='index' else ''
        if state['phase'] in ('paused','error','interrupted') and state.get('action') != 'index':
            return 'other_operation_stopped'
        return index_queue.read(Path(self.config['data_dir'])).get('last_attempt',{}).get('reason','')

    def pending_video_archives(self, root):
        from pilot.archive_index import status as index_status
        report = index_status(root/'state/pilot/zim-videos')
        usable = report['phase'] in ('not_prepared', 'completed') or (
            report['phase'] == 'partial' and all(
                row.get('status') in zim_video_inventory.EXAMINED_STATUSES for row in report.get('results', [])))
        return len(zim_video_inventory.unexamined_files(root/'library/zim', report)) if usable else 0

    def queue_paused(self):
        return (Path(self.config['data_dir']) / 'state/pilot/work-queue.pause').is_file()

    def auto_index(self):
        root = Path(self.config['data_dir'])
        state = self.current()
        if self.queue_paused():
            if (state.get('action') in QUEUE_PREPARATIONS
                    and state['phase'] in ('starting', 'planning', 'downloading')
                    and not (self.paths(state['id']) / 'cancel').exists()):
                self.pause(automatic=bool(state.get('options', {}).get('automatic')), state=state)
            return
        queue = index_queue.read(root)
        gaming = index_queue.gaming(self.app.work)
        allowed=queue['settings']['enabled'] and index_queue.in_window(queue['settings']) and not gaming
        if state['phase'] in ACTIVE:
            if state.get('action')=='video-inventory' and (gaming or state.get('options',{}).get('automatic') and not allowed):
                self.pause(automatic=True)
            if state.get('action') in ('index','category-index') and state.get('options',{}).get('automatic') and not allowed:
                self.pause(automatic=True)
            return
        request = self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST
        video_resume = (state.get('action') == 'video-inventory' and state.get('options', {}).get('automatic')
                        and state['phase'] == 'paused' and (self.paths(state['id'])/'auto-pause').is_file())
        if allowed and video_resume and self.index_ready():
            with locked(destination(root, 'catalog/content.lock')), locked(destination(root, 'catalog/publication.lock')):
                self.start('video-inventory', {'automatic': True})
            return
        if (self.backend == 'compose' and state['phase'] != 'planned' and request.is_file()
                and allowed and self.index_ready()):
            with locked(destination(root, 'catalog/content.lock')), locked(destination(root, 'catalog/publication.lock')):
                self.start('video-inventory', {'automatic': True})
            return
        automatic_category_resume = (state.get('action') == 'category-index' and
            state.get('options', {}).get('automatic') and
            (state['phase'] == 'interrupted' or state['phase'] == 'paused' and
             (self.paths(state['id']) / 'auto-pause').is_file()))
        if (allowed and (automatic_category_resume or not queue['pending']) and self.index_ready() and
                (state['phase'] in ('idle', 'completed') or automatic_category_resume)):
            category,_=category_index.availability(root/'library/zim',root/'state/pilot',collection_sort.load(root/'catalog'))
            if category['phase'] in ('outdated','not_prepared') or automatic_category_resume and category['phase'] != 'completed':
                try:
                    with locked(destination(root, 'catalog/content.lock')), locked(destination(root, 'catalog/publication.lock')):
                        self.start('category-index',{'automatic':True})
                except setup.SetupError:pass
                return
        # Existing ZIM indexes remain usable. Only examine new or changed
        # archives during the configured window and after pending text indexes.
        if (allowed and not queue['pending'] and self.index_ready() and
                state['phase'] in ('idle', 'completed') and self.pending_video_archives(root)):
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
        if action in QUEUE_PREPARATIONS and self.queue_paused():
            raise setup.SetupError('Reprenez la file pour lancer cette préparation.')
        state = self.current()
        if state['phase'] in ACTIVE:
            raise setup.SetupError('Une opération documentaire est déjà en cours.')
        storage = self.check_storage(0) if action=='collection-exclude' else self.check_storage()
        if action == 'category-index':
            if not self.index_ready():raise setup.SetupError('Préparez d’abord l’outil d’indexation depuis les réglages.')
            if index_queue.gaming(self.app.work):raise setup.SetupError('Le mode jeu est actif. Reprenez l’indexation après la pause.')
            root=Path(self.config['data_dir'])
            if not category_index.sources(root/'library/zim',collection_sort.load(root/'catalog')):raise setup.SetupError('Le fonds principal ne contient aucune archive disponible.')
            state={'id':uuid.uuid4().hex,'phase':'starting','options':{'automatic':body.get('automatic') is True}}
            self.paths(state['id']).mkdir(parents=True)
        elif action in ('index','index-prepare','video-inventory'):
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
        elif action == 'collection-exclude':
            keys = collection_tasks.validate_keys(body)
            current = collection_tasks.preview(Path(self.config['data_dir']), keys)
            if not current['files'] or current['token'] != body.get('token'):
                raise setup.SetupError('Affichez et confirmez la liste actuelle des fichiers à supprimer.')
            state = {'id': uuid.uuid4().hex, 'phase': 'starting',
                     'options': {'keys': sorted(keys), 'token': current['token']}}
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
            try:
                collection_tasks.merge(Path(self.config['data_dir']), body.get('collection_sort'))
            except ValueError as exc:
                raise setup.SetupError(str(exc)) from exc
            state = {'id': uuid.uuid4().hex, 'phase': 'starting', 'options': {
                'themes': list(dict.fromkeys(requested)), 'max_add_gb': size, 'languages': list(dict.fromkeys(languages)),'include_supplements':supplements}}
            self.paths(state['id']).mkdir(parents=True)
        elif action == 'download':
            if 'reference_confirmation' in body:
                import library_reference
                root, scope = storage
                previous = state.get('options', {}).get('reference_restore')
                if not previous and (state['phase'] == 'planned' or (
                    state.get('action') == 'download' and state['phase'] in ('paused', 'error', 'interrupted')
                )):
                    raise setup.SetupError('Reprenez d’abord le téléchargement précédent depuis la File d’attente.')
                with locked(root/'catalog/content.lock'):
                    reference = library_reference.load()
                    sorting = collection_sort.load(root/'catalog')
                    plan = library_reference.restoration_plan(root, reference, sorting, storage_root=scope)
                    if plan['confirmation_token'] != body['reference_confirmation']:
                        raise setup.SetupError('La bibliothèque a changé. Actualisez la comparaison avant de confirmer.')
                    if not any(plan[key] for key in ('downloads', 'removals', 'moves')):
                        raise setup.SetupError('La bibliothèque correspond déjà à la référence.')
                    if not plan['space_sufficient']:
                        raise setup.SetupError('L’espace libre est insuffisant pour préparer les éditions de référence.')
                    names = {row['archive'] for row in plan['downloads']}
                    state = {'id': uuid.uuid4().hex, 'phase': 'planned', 'options': {'reference_restore': True}}
                    folder = self.paths(state['id'])
                    folder.mkdir(parents=True)
                    setup.write_json(folder/'plan.json', {
                        'schema': 1, 'kind': library_reference.KIND,
                        'items': [item for item in reference['items'] if Path(item['path']).name in names],
                        'candidates': [], 'remaining_download_bytes': plan['download_bytes'],
                        'missing_themes': [], 'library_bytes': 0, 'include_supplements': False,
                        'restoration': {**{key: plan[key] for key in ('downloads', 'moves', 'removals', 'states')},
                                        'manifest': reference['items']},
                    }, private=True)
                body = {'id': state['id']}
            elif 'reference_archive' in body:
                import library_reference
                archive = body['reference_archive']
                root, scope = storage
                reference = library_reference.load()
                item = next((item for item in reference['items'] if Path(item['path']).name == archive), None)
                if item is None:
                    raise setup.SetupError('Cette édition ne figure pas dans la référence.')
                if not collection_sort.load(root/'catalog').permits(collection_sort.path_key(item['path']), 'all'):
                    raise setup.SetupError('Cette collection est exclue par le classement actuel.')
                previous_download = state['phase'] == 'planned' or (
                    state.get('action') == 'download' and state['phase'] in ('paused', 'error', 'interrupted')
                )
                if previous_download:
                    if state.get('options', {}).get('reference_archive') != archive:
                        raise setup.SetupError('Reprenez d’abord le téléchargement précédent depuis la File d’attente.')
                else:
                    if content.destination(root, item['path']).exists():
                        raise setup.SetupError('Cette édition est déjà sur le disque. Actualisez la comparaison.')
                    report = library_reference.preview(root, {'items': [item]}, collection_sort.load(root/'catalog'), storage_root=scope)
                    if report['download_bytes'] + content.STORAGE_RESERVE > report['available_bytes']:
                        raise setup.SetupError('L’espace libre est insuffisant pour télécharger cette archive.')
                    state = {'id': uuid.uuid4().hex, 'phase': 'planned', 'options': {'reference_archive': archive}}
                    folder = self.paths(state['id'])
                    folder.mkdir(parents=True)
                    setup.write_json(folder/'plan.json', {
                        'schema': 1, 'kind': library_reference.KIND, 'items': [item],
                        'candidates': [], 'remaining_download_bytes': report['download_bytes'],
                        'missing_themes': [], 'library_bytes': 0, 'include_supplements': False,
                    }, private=True)
                body = {'id': state['id']}
            if body.get('id') != state.get('id') or state['phase'] not in ('planned', 'paused', 'error', 'interrupted'):
                raise setup.SetupError('Préparez une sélection avant de télécharger.')
            plan_path = self.paths(state['id']) / 'plan.json'
            if not plan_path.is_file() or (not content.catalog(plan_path) and not state['options'].get('reference_restore')):
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
        return state['id']

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
        folder = self.paths(state['id'])
        if state.get('action') in ('category-index', 'video-inventory'):
            marker = folder / 'auto-pause'
            if automatic and not (folder / 'cancel').exists():
                marker.touch()
            elif not automatic:
                marker.unlink(missing_ok=True)
        (folder / 'cancel').touch()

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
            root, scope = self.check_storage(0) if state['action']=='collection-exclude' else self.check_storage()
            check()
            if state['action']=='collection-exclude':
                update('refreshing','Suppression des fichiers confirmés…')
                keys=set(state['options']['keys'])
                if self.backend == 'lab':
                    import linux_lab as lab
                    if any(key.startswith('zim:') for key in keys):lab.podman('stop',lab.PREFIX+'kiwix',capture=True)
                elif any(key.startswith('zim:') for key in keys):
                    self.app.compose(self.config,'stop','kiwix')
                try:
                    recovered=collection_tasks.exclude(root,keys,state['options']['token'])
                    update('refreshing','Fichiers supprimés. Actualisation du catalogue et redémarrage des services…')
                    self.app.catalog(self.config)
                finally:
                    if self.backend == 'lab':
                        lab.podman('start',lab.PREFIX+'kiwix',capture=True)
                        lab.podman('restart',lab.PREFIX+'pilot',capture=True)
                    else:
                        self.app.compose(self.config,'start','kiwix')
                        self.app.compose(self.config,'restart','pilot')
                update('completed',f'Collections supprimées et exclues. {recovered/1e9:.2f} Go de fichiers retirés.')
            elif state['action']=='youtube-download':
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
                items=report.get('items',[])
                duplicates=sum(item.get('reason')=='duplicate_in_list' for item in items)
                rejected_lines=sum(item.get('status')=='refused' and not item.get('id') for item in items)
                existing=counts.get('skipped',0)-duplicates
                failed=counts.get('error',0)+counts.get('refused',0)-rejected_lines
                update('completed',f"Téléchargement terminé : {counts.get('downloaded',0)} vidéo(s) ajoutée(s), {existing} déjà présente(s), "
                       f"{failed} non téléchargée(s). "
                       +(f"{duplicates+rejected_lines} ligne(s) écartée(s) de la liste. " if duplicates or rejected_lines else '')
                       +(f"{report['remaining']} restante(s), à reprendre après avoir libéré de l’espace. " if report.get('remaining') else '')
                       +'Le site répertorie les vidéos téléchargées.')
            elif state['action']=='category-index':
                update('downloading','Classement des archives du fonds principal…')
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                command=[str(self.index_python()),'-X','utf8',str(setup.ROOT/'scripts/index_categories.py'),
                         '--data-dir',str(root),'--cancel',str(folder/'cancel'),'--job-id',job]
                process=subprocess.Popen(command,**hidden)
                state.update(index_pid=process.pid,index_identity=discovery.identity(process.pid));self.write(state)
                code=process.wait();check()
                report=category_index.read_status(root/'state/pilot')
                if code or report['phase'] not in ('completed','outdated'):
                    raise setup.SetupError('Le classement du fonds principal doit être repris.')
                message = ('Classement des archives du fonds principal terminé.' if report['phase']=='completed'
                           else 'Le fonds principal a changé pendant le classement.')
                update('completed',message)
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
                if code or report.get('job_id') != job:
                    update('error', 'L’examen des vidéos a échoué. Les résultats précédents restent disponibles.')
                elif zim_video_inventory.partial_with_all_archives(report):
                    update('completed', zim_video_inventory.LIMITED_INVENTORY_MESSAGE)
                elif report.get('phase') == 'completed':
                    update('completed', 'Inventaire des vidéos terminé. Leur présence ne valide pas leur lecture ou leurs sous-titres.')
                else:
                    update('error', 'Certaines collections n’ont pas pu être examinées. Consultez le rapport vidéo avant de relancer.')
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
                if state['options'].get('reference_restore'):
                    import library_reference
                    plan = json.loads((folder/'plan.json').read_text(encoding='utf-8'))
                    pending, staged = library_reference.restoration_downloads(root, plan)
                    content.download(root, pending, storage_root=scope, workers=2,
                                     cancelled=lambda: (folder/'cancel').exists(),
                                     confirmed_reference=True, stage_paths=staged)
                    check()
                    update('refreshing', 'Vérification des éditions avant de retirer les anciens fichiers…')
                    stopped = False
                    def stop_kiwix():
                        nonlocal stopped
                        if plan['restoration']['removals'] or staged:
                            if self.backend == 'lab':
                                import linux_lab as lab
                                lab.podman('stop', lab.PREFIX + 'kiwix', capture=True)
                            else:
                                self.app.compose(self.config, 'stop', 'kiwix')
                            stopped = True
                    try:
                        library_reference.finish_restoration(root, plan, check, stop_kiwix)
                        self.app.catalog(self.config)
                    finally:
                        if stopped:
                            if self.backend == 'lab':
                                import linux_lab as lab
                                lab.podman('start', lab.PREFIX + 'kiwix', capture=True)
                            else:
                                self.app.compose(self.config, 'start', 'kiwix')
                    if not stopped and items:
                        if self.backend == 'lab':
                            import linux_lab as lab
                            lab.podman('restart', lab.PREFIX + 'kiwix', capture=True)
                        else:
                            self.app.compose(self.config, 'restart', 'kiwix')
                    update('completed', 'La bibliothèque a été remise à l’état de la référence.')
                    return
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
            if state.get('action')=='category-index':
                update('error','La préparation des index Wikipédia doit être reprise. La recherche habituelle reste disponible.')
                return
            if state.get('action')=='collection-exclude':
                update('error','La suppression ou l’actualisation a été interrompue. Rechargez les collections pour voir les fichiers restants.')
                return
            update('error',getattr(exc,'public_message',None) or ('L’indexation ou sa préparation a échoué ; les anciens index restent disponibles. Vérifiez le suivi et l’espace libre.' if state.get('action') in ('index','index-prepare') else 'L’opération a échoué. Les fichiers existants sont conservés. Vérifiez la connexion Internet et l’espace libre, puis réessayez.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True); parser.add_argument('--backend', choices=['lab', 'compose'], required=True)
    parser.add_argument('--job', required=True); args = parser.parse_args()
    app = setup.Installation(args.work_dir)
    Manager(app, app.load(), args.backend).run(args.job)
