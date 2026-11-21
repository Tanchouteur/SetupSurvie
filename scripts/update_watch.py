"""Check for a newer `main` and launch the existing Windows updater on request.

Runs inside the host controller. The check only fetches the separate maintenance
clone and reads `origin/main` without touching its working tree. Applying an
update stays the job of `update-windows.ps1` and `pilot_update.py`, which stop
this controller; the launched updater is therefore an independent process.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import uuid

import setup
import maintenance_site

REPOSITORY = 'https://github.com/Tanchouteur/SetupSurvie.git'
INTERVAL = 15 * 60
FIRST_CHECK = 120
MANUAL_SPACING = 60
STALE_RUNNING = 1200  # Same limit as portal/maintenance-view.js.
VERSION = re.compile(r'\d+\.\d+\.\d+')


def version_tuple(value):
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError('version')
    return tuple(map(int, value.split('.')))


def find_git():
    if os.name != 'nt':
        return shutil.which('git')
    system = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    powershell = system/'System32/WindowsPowerShell/v1.0/powershell.exe'
    command = (r". .\windows-common.ps1; Update-SurviePath; "
               '[Console]::OutputEncoding = [Text.UTF8Encoding]::new(); Find-SurvieGit')
    try:
        result = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                                 '-Command', command], cwd=Path(__file__).resolve().parent, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=30, **hidden())
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return result.stdout.decode('utf-8', 'replace').strip() or None
    return None


def hidden():
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}


class Watcher:
    def __init__(self, app, config, *, git=None, repository=REPOSITORY, clock=time.monotonic):
        self.app, self.config = app, config
        self.git = git
        self.repository = repository
        self.clock = clock
        self.lock = threading.Lock()
        self.checking = False
        self.process = None
        self.last_manual = None
        self.next_check = clock() + FIRST_CHECK
        self.cache_path = app.work/'update-check.json'
        self.result = self.load()

    # Installation shape -------------------------------------------------
    def application(self):
        value = self.config.get('app_dir')
        return setup.safe_path(value) if value else None

    def base(self):
        application = self.application()
        return application.parent if application else None

    def launcher(self):
        base = self.base()
        return base/'maintenance/update-windows.ps1' if base else None

    def source(self):
        base = self.base()
        return base/'maintenance/source' if base else None

    def supported(self):
        application, launcher = self.application(), self.launcher()
        return bool(self.config.get('target') == 'windows' and application and launcher
                    and launcher.is_file() and not (application/'.git').exists())

    def installed(self):
        try:
            return json.loads((setup.ROOT/'deploy/release.json').read_text(encoding='utf-8'))['version']
        except (OSError, ValueError, KeyError):
            return ''

    # Cached result ------------------------------------------------------
    def load(self):
        try:
            value = json.loads(self.cache_path.read_text(encoding='utf-8'))
            return value if isinstance(value, dict) and value.get('schema') == 1 else {}
        except (OSError, ValueError):
            return {}

    def status(self):
        installed = self.installed()
        with self.lock:
            result = dict(self.result)
            checking = self.checking
        available = result.get('available', '')
        try:
            newer = bool(available) and version_tuple(available) > version_tuple(installed)
        except ValueError:
            newer = False
        current = maintenance_site.read_status(self.config['data_dir']) or {}
        running = current.get('state') == 'running' and time.time() - float(current.get('updated') or 0) < STALE_RUNNING
        return {'supported': self.supported(), 'installed': installed, 'available': available if newer else '',
                'update_available': newer, 'changes': result.get('changes', []) if newer else [],
                'checked_at': result.get('checked_at'), 'error': result.get('error', ''),
                'checking': checking, 'running': running,
                'transfer_in_progress': (self.app.work/'transfer-guard.json').exists()}

    # Check ----------------------------------------------------------------
    def tick(self):
        if self.clock() >= self.next_check and self.supported():
            self.next_check = self.clock() + INTERVAL
            self.check()

    def request_check(self):
        if not self.supported():
            raise setup.SetupError('La vérification des mises à jour depuis le portail concerne les installations Windows.')
        now = self.clock()
        if self.last_manual is not None and now - self.last_manual < MANUAL_SPACING:
            return False
        self.last_manual = now
        self.next_check = now + INTERVAL
        return self.check()

    def check(self):
        with self.lock:
            if self.checking:
                return False
            self.checking = True
        threading.Thread(target=self.run_check, daemon=True).start()
        return True

    def git_output(self, *arguments, timeout=60):
        environment = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never', 'LC_ALL': 'C'}
        result = subprocess.run([self.git, '-C', str(self.source()), *arguments], capture_output=True,
                                timeout=timeout, env=environment, stdin=subprocess.DEVNULL, **hidden())
        if result.returncode:
            raise setup.SetupError('git')
        return result.stdout.decode('utf-8', 'replace')

    def run_check(self):
        result = {'schema': 1, 'checked_at': time.time()}
        try:
            current = maintenance_site.read_status(self.config['data_dir']) or {}
            if current.get('state') == 'running' and time.time() - float(current.get('updated') or 0) < STALE_RUNNING:
                raise setup.SetupError('Une opération de maintenance est en cours ; vérification reportée.')
            self.git = self.git or find_git()
            source = self.source()
            if not self.git:
                raise setup.SetupError(
                    'Git est introuvable sur le PC serveur. Lancez la préparation du PC Windows pour installer Git, '
                    'puis utilisez le raccourci Mettre à jour SetupSurvie.')
            if not source or not (source/'.git').exists():
                raise setup.SetupError('Le dépôt de maintenance n’est pas encore préparé : utilisez une fois le raccourci Mettre à jour SetupSurvie.')
            if self.git_output('remote', 'get-url', 'origin').strip().rstrip('/') != self.repository:
                raise setup.SetupError('Le dépôt de maintenance ne pointe pas vers le dépôt prévu.')
            try:
                self.git_output('fetch', '--quiet', 'origin', 'main', timeout=180)
            except (setup.SetupError, subprocess.TimeoutExpired):
                raise setup.SetupError(
                    'Hors ligne pour les mises à jour. Vérifiez la connexion Internet du PC serveur. '
                    'Si elle fonctionne, GitHub ou l’accès au dépôt peut être indisponible.')
            release = json.loads(self.git_output('show', 'origin/main:deploy/release.json'))
            available = release['version']
            version_tuple(available)
            subjects = self.git_output('log', '--no-merges', '--format=%s', '-n', '15', 'HEAD..origin/main')
            result.update(available=available,
                          changes=[' '.join(line.split())[:160] for line in subjects.splitlines() if line.strip()][:15])
        except setup.SetupError as exc:
            result['error'] = str(exc) if str(exc) != 'git' else 'Le dépôt de maintenance n’a pas pu être lu.'
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            result['error'] = 'Le dépôt de maintenance n’a pas pu être lu.'
        with self.lock:
            if 'error' in result and self.result.get('available'):
                # Keep the last known version: an offline check does not erase it.
                result.update(available=self.result['available'], changes=self.result.get('changes', []))
            self.result = result
            self.checking = False
        try:
            setup.write_json(self.cache_path, result, private=True)
        except OSError:
            pass

    # Launch ---------------------------------------------------------------
    def start_update(self):
        if not self.supported():
            raise setup.SetupError('La mise à jour depuis le portail concerne les installations Windows avec le raccourci de mise à jour.')
        if (self.app.work/'transfer-guard.json').exists():
            raise setup.SetupError('Un transfert est en cours : la mise à jour attendra sa fin.')
        journal = self.app.work/'update.json'
        if journal.is_file():
            try:
                phase = json.loads(journal.read_text(encoding='utf-8')).get('phase')
            except ValueError:
                phase = None
            if phase not in ('complete', 'rolled_back'):
                raise setup.SetupError('Une mise à jour précédente doit être récupérée sur le PC serveur.')
        status = self.status()
        if status['running'] or (self.process and self.process.poll() is None):
            raise setup.SetupError('Une mise à jour ou une copie est déjà en cours.')
        operation = uuid.uuid4().hex
        writer = maintenance_site.StatusWriter(self.config['data_dir'], 'update', installed=status['installed'],
                                               available=status['available'], operation_id=operation)
        writer.progress('setup', 'Lancement demandé depuis le portail.')
        logs = self.base()/'maintenance/logs'
        logs.mkdir(parents=True, exist_ok=True)
        system = Path(os.environ.get('SystemRoot', r'C:\Windows'))
        command = [str(system/'System32/WindowsPowerShell/v1.0/powershell.exe'), '-NoProfile', '-ExecutionPolicy', 'Bypass',
                   '-File', str(self.launcher()), '-ConsoleOnly', '-OperationId', operation]
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        environment = {**os.environ, 'SURVIE_NO_PAUSE': '1'}
        environment.pop('SURVIE_UPDATE_PROGRESS', None)
        try:
            with (logs/('portail-'+time.strftime('%Y%m%d-%H%M%S')+'.log')).open('ab') as log:
                self.process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, cwd=str(self.base()),
                                                env=environment, creationflags=flags)
        except OSError:
            writer.progress('error', 'Le programme de mise à jour n’a pas pu être lancé.')
            raise setup.SetupError('Le programme de mise à jour n’a pas pu être lancé sur le PC serveur.')
        threading.Thread(target=self.watch_launch, args=(self.process, operation), daemon=True).start()
        return operation

    def watch_launch(self, process, operation):
        """Report an updater that stops before publishing anything itself."""
        code = process.wait()
        current = maintenance_site.read_status(self.config['data_dir']) or {}
        if current.get('id') == operation and current.get('state') == 'running':
            writer = maintenance_site.StatusWriter(self.config['data_dir'], 'update', operation_id=operation)
            writer.value.update({key: current[key] for key in ('started', 'installed', 'available', 'steps', 'lines') if key in current})
            writer.progress('error', 'Le programme de mise à jour s’est arrêté (code %s). Consultez maintenance\\logs sur le PC serveur.' % code)
