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
                state.update(phase='interrupted', message='Opération interrompue. Préparez une nouvelle sélection pour reprendre les fichiers partiels.')
                self.write(state)
        return state

    def status(self):
        state = self.current()
        result = {k: state[k] for k in ('phase', 'message', 'options', 'id') if k in state}
        result['index_reader_ready']=self.index_ready()
        from pilot.archive_index import status as index_status
        result['search_index']=index_status(Path(self.config['data_dir'])/'state/pilot/archive-index')
        result.update(available=True, themes=[{'id': k, 'label': v['label']} for k, v in kiwix_select.themes().items()])
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

    def index_ready(self):
        return self.index_python().is_file() and (self.app.work/'search-tools/reader-ready.json').is_file()

    def index_python(self):
        return self.app.work/'search-tools'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

    def start(self, action, body):
        with locked(destination(self.app.work, 'library-web/operation.lock')):
            return self.start_locked(action, body)

    def start_locked(self, action, body):
        state = self.current()
        if state['phase'] in ACTIVE:
            raise setup.SetupError('Une opération documentaire est déjà en cours.')
        self.check_storage()
        if action in ('index','index-prepare'):
            if action=='index' and not self.index_ready():raise setup.SetupError('Préparez d’abord l’outil d’indexation depuis les réglages.')
            state={'id':uuid.uuid4().hex,'phase':'starting','options':{}}
            self.paths(state['id']).mkdir(parents=True)
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

    def pause(self):
        state = self.current()
        if state['phase'] not in ('starting', 'planning', 'downloading'):
            raise setup.SetupError('Aucun téléchargement ou recherche à mettre en pause.')
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
            if state['action']=='index-prepare':
                update('downloading','Préparation de l’outil de recherche (Internet requis une seule fois)…')
                import venv
                environment=self.app.work/'search-tools'
                venv.EnvBuilder(with_pip=False).create(environment)
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                subprocess.run([str(self.index_python()),'-m','ensurepip','--upgrade'],check=True,timeout=120,**hidden)
                wheels=self.app.work/'search-tools-wheels';wheels.mkdir(exist_ok=True)
                commands=[[str(self.index_python()),'-m','pip','download','--only-binary=:all:','--no-deps','--dest',str(wheels),'-r',str(setup.ROOT/'scripts/requirements-index.txt')],
                    [str(self.index_python()),'-m','pip','install','--no-index','--find-links',str(wheels),'-r',str(setup.ROOT/'scripts/requirements-index.txt')]]
                if list(wheels.glob('libzim-3.13.1-*.whl')):commands=commands[1:]
                for command in commands:
                    check();subprocess.run(command,check=True,timeout=300,**hidden)
                setup.write_json(environment/'reader-ready.json',{'libzim':'3.13.1'},private=True)
                update('completed','Outil d’indexation prêt. La création des index peut fonctionner hors ligne.')
            elif state['action']=='index':
                update('downloading','Indexation locale des archives, sans IA. La bibliothèque reste accessible…')
                hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                process=subprocess.Popen([str(self.index_python()),str(setup.ROOT/'scripts/index_archives.py'),'--zim-dir',str(root/'library/zim'),'--state-dir',str(root/'state/pilot'),'--cancel',str(folder/'cancel')],**hidden)
                code=process.wait()
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
            update('paused', 'Préparation géographique arrêtée. Les zones existantes sont conservées ; relancez cette zone pour recommencer.' if state.get('action') in ('geography','routing') else 'Opération mise en pause. Les fichiers partiels sont conservés pour la reprise.')
        except Exception as exc:
            print(type(exc).__name__, str(exc), flush=True)
            update('error', 'L’indexation ou sa préparation a échoué ; les anciens index restent disponibles. Vérifiez le suivi et l’espace libre.' if state.get('action') in ('index','index-prepare') else 'L’opération a échoué. Les fichiers existants sont conservés. Vérifiez la connexion Internet et l’espace libre, puis réessayez.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True); parser.add_argument('--backend', choices=['lab', 'compose'], required=True)
    parser.add_argument('--job', required=True); args = parser.parse_args()
    app = setup.Installation(args.work_dir)
    Manager(app, app.load(), args.backend).run(args.job)
