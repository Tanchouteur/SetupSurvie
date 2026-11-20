"""Shared maintenance status and temporary site while SetupSurvie services are stopped.

An update or a complete copy stops every container, including Caddy. This module
binds the portal ports only during that window, serves a small page and the
status JSON, then releases the ports before the services restart. It keeps its
assets in memory because the application directory is renamed during an update.
Standard library only; no command, file listing or credential is ever served.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import ssl
import threading
import time
import uuid

STATUS_NAME = 'maintenance.json'
PORTAL = Path(__file__).resolve().parents[1]/'portal'
ASSETS = {
    '/maintenance.html': ('maintenance.html', 'text/html; charset=utf-8'),
    '/maintenance-view.js': ('maintenance-view.js', 'text/javascript; charset=utf-8'),
    '/maintenance-view.css': ('maintenance-view.css', 'text/css; charset=utf-8'),
    '/branding/logo.png': ('branding/logo.png', 'image/png'),
    '/branding/favicon.ico': ('branding/favicon.ico', 'image/x-icon'),
}
# Same titles as scripts/update-windows.ps1; keep both lists aligned.
PHASES = {
    'setup': 'Vérification de l’installation',
    'git': 'Récupération de la version disponible',
    'build': 'Préparation du paquet',
    'package': 'Vérification du paquet et de l’espace disque',
    'apply': 'Sauvegarde et installation',
    'maintenance': 'Attente de la fin des travaux en cours',
    'stop': 'Arrêt des services',
    'backup': 'Sauvegarde des données',
    'switch': 'Installation de la nouvelle version',
    'start': 'Redémarrage des services',
    'check': 'Vérification du fonctionnement',
    'rollback': 'Restauration de la version précédente',
    'prune': 'Nettoyage des anciennes copies de mise à jour',
    'launcher': 'Actualisation des raccourcis et du lanceur',
    'done': 'Mise à jour terminée',
    'clean': 'Nettoyage terminé',
    'current': 'SetupSurvie est déjà à jour',
    'error': 'Mise à jour arrêtée',
}
# From this phase until the services answer again the site is unavailable.
UNAVAILABLE = ('apply', 'stop', 'backup', 'switch', 'start', 'check', 'rollback')
FINAL = {'done': 'completed', 'clean': 'completed', 'current': 'current', 'error': 'failed'}
PORTS = ((8080, False), (8443, True))
MAX_LINES = 40


def status_path(data_dir):
    return Path(data_dir)/'catalog'/STATUS_NAME


def read_status(data_dir):
    """Return the published status, or None when absent or unreadable."""
    path = status_path(data_dir)
    try:
        if path.stat().st_size > 256_000:
            return None
        value = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def publish_status(data_dir, value):
    """Atomic small write. The catalog folder is public to readers: no secret here."""
    path = status_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{STATUS_NAME}.{os.getpid()}.{threading.get_ident()}.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            # Windows refuses a replacement while a reader holds the file.
            time.sleep(.05 * (attempt + 1))
    temporary.unlink(missing_ok=True)


class StatusWriter:
    """Python writer used when no PowerShell launcher publishes the status."""

    def __init__(self, data_dir, kind='update', *, installed='', available='', operation_id=None):
        self.data_dir = data_dir
        now = time.time()
        self.value = {'schema': 1, 'id': operation_id or uuid.uuid4().hex, 'kind': kind, 'state': 'running',
                      'phase': 'setup', 'title': PHASES['setup'], 'detail': '', 'current': None, 'total': None,
                      'unavailable': False, 'installed': installed, 'available': available,
                      'rolled_back': False, 'started': now, 'updated': now, 'steps': [], 'lines': []}
        self.last_write = 0.0

    def progress(self, phase, detail='', current=None, total=None):
        title = PHASES.get(phase)
        if not title:
            return
        value = self.value
        changed = phase != value['phase'] or not value['steps']
        if changed:
            value['steps'].append({'phase': phase, 'title': title, 'at': time.time()})
            del value['steps'][:-30]
        if phase == 'rollback':
            value['rolled_back'] = True
        if phase in UNAVAILABLE:
            value['unavailable'] = True
        elif phase in ('prune', 'launcher', *FINAL):
            value['unavailable'] = False
        value.update(phase=phase, title=title, detail=str(detail or '')[:500],
                     current=current, total=total, state=FINAL.get(phase, 'running'))
        if detail:
            self.line(title + ' — ' + str(detail))
        elif changed:
            self.line(title)
        self.save(force=changed or phase in FINAL)

    def line(self, text):
        text = ' '.join(str(text).split())[:300]
        if text:
            self.value['lines'].append(time.strftime('[%H:%M:%S] ') + text)
            del self.value['lines'][:-MAX_LINES]

    def save(self, force=False):
        if not force and time.monotonic() - self.last_write < 1:
            return
        self.value['updated'] = time.time()
        try:
            publish_status(self.data_dir, self.value)
            self.last_write = time.monotonic()
        except OSError:
            pass  # The status is informative; the operation itself decides success.


def load_assets(root=PORTAL):
    assets = {}
    for route, (name, mime) in ASSETS.items():
        try:
            assets[route] = (root.joinpath(*name.split('/')).read_bytes(), mime)
        except OSError:
            pass
    if '/maintenance.html' not in assets:
        page = ('<!doctype html><meta charset="utf-8"><title>Maintenance de SetupSurvie</title>'
                '<p>SetupSurvie est en maintenance. Réessayez dans quelques minutes.</p>').encode('utf-8')
        assets['/maintenance.html'] = (page, 'text/html; charset=utf-8')
    return assets


def tls_contexts(data_dir, fallback_host):
    """Reuse Caddy's local certificates; HTTPS is skipped when none is usable."""
    root = Path(data_dir)/'state/caddy/caddy/certificates'
    contexts = {}
    try:
        folders = [folder for issuer in root.iterdir() if issuer.is_dir() for folder in issuer.iterdir() if folder.is_dir()]
    except OSError:
        return None
    for folder in folders:
        certificate, key = folder/(folder.name+'.crt'), folder/(folder.name+'.key')
        if not certificate.is_file() or not key.is_file():
            continue
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(certificate, key)
        except (OSError, ssl.SSLError, ValueError):
            continue
        contexts[folder.name.casefold()] = context
    if not contexts:
        return None
    default = contexts.get(str(fallback_host or '').casefold()) or next(iter(contexts.values()))

    def choose(connection, name, _context):
        chosen = contexts.get((name or '').casefold())
        if chosen:
            connection.context = chosen
    default.sni_callback = choose
    return default


class Server(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    # Windows SO_REUSEADDR would let two listeners share the port.
    allow_reuse_address = os.name != 'nt'

    def __init__(self, address, site, tls=None):
        self.site, self.tls = site, tls
        super().__init__(address, Handler)

    def finish_request(self, request, client_address):
        # Handshake in the connection thread, never in the accept loop.
        request.settimeout(10)
        if self.tls:
            try:
                request = self.tls.wrap_socket(request, server_side=True)
            except (OSError, ssl.SSLError):
                return
        with self.site.active_lock:
            self.site.active += 1
        try:
            super().finish_request(request, client_address)
        finally:
            with self.site.active_lock:
                self.site.active -= 1
            if self.tls:
                try:
                    request.close()
                except OSError:
                    pass


class Handler(BaseHTTPRequestHandler):
    server_version = 'SetupSurvie-maintenance'
    sys_version = ''
    timeout = 10

    def log_message(self, *args):
        pass

    def reply(self, code, body, mime, extra=()):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-SetupSurvie-Maintenance', '1')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        for name, value in extra:
            self.send_header(name, value)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)
        self.close_connection = True

    def json(self, code, value, extra=()):
        self.reply(code, json.dumps(value, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8', extra)

    def do_GET(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        site = self.server.site
        if path == '/catalog/'+STATUS_NAME:
            self.json(200, site.status())
        elif path == '/api/health':
            self.json(503, {'ok': False, 'maintenance': True}, (('Retry-After', '10'),))
        elif path.startswith('/api/') or path == '/health':
            self.json(503, {'detail': 'SetupSurvie est en maintenance. Le suivi est affiché sur l’accueil.', 'maintenance': True},
                      (('Retry-After', '10'),))
        elif path in site.assets and path != '/maintenance.html':
            body, mime = site.assets[path]
            self.reply(200, body, mime)
        else:
            body, mime = site.assets['/maintenance.html']
            self.reply(503, body, mime, (('Retry-After', '10'),))

    do_HEAD = do_GET

    def refuse(self):
        self.json(503, {'detail': 'SetupSurvie est en maintenance. Réessayez après la fin du suivi affiché sur l’accueil.',
                        'maintenance': True}, (('Retry-After', '10'),))

    do_POST = do_PUT = do_DELETE = do_PATCH = refuse


class Site:
    """Bind in background threads, retrying while Docker releases the ports."""

    def __init__(self, status, *, bind='0.0.0.0', ports=PORTS, tls=None, wait=180, assets=None):
        self.provider = status
        self.assets = assets or load_assets()
        self.bind, self.ports, self.tls, self.wait = bind, ports, tls, wait
        self.servers, self.threads = [], []
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.active_lock = threading.Lock()
        self.active = 0

    def status(self):
        try:
            value = self.provider()
        except (OSError, ValueError, KeyError, TypeError):
            value = None
        if not isinstance(value, dict):
            value = {'schema': 1, 'state': 'running', 'kind': 'maintenance', 'title': 'Maintenance en cours',
                     'detail': 'SetupSurvie redémarre. Cette page se met à jour toute seule.', 'unavailable': True}
        return {**value, 'served_by': 'maintenance'}

    def start(self):
        for port, secure in self.ports:
            if secure and not self.tls:
                continue
            thread = threading.Thread(target=self.serve, args=(port, self.tls if secure else None), daemon=True)
            thread.start()
            self.threads.append(thread)
        return self

    def serve(self, port, tls):
        deadline = time.monotonic() + self.wait
        while not self.stopping.is_set():
            try:
                server = Server((self.bind, port), self, tls)
            except OSError:
                if time.monotonic() >= deadline:
                    print(f'Page de maintenance indisponible sur le port {port}.', flush=True)
                    return
                self.stopping.wait(.5)
                continue
            with self.lock:
                if self.stopping.is_set():
                    server.server_close()
                    return
                self.servers.append(server)
            server.serve_forever(poll_interval=.2)
            return

    def close(self):
        self.stopping.set()
        with self.lock:
            servers, self.servers = self.servers, []
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=5)
        deadline = time.monotonic() + 3
        while self.active and time.monotonic() < deadline:
            time.sleep(.05)
        for port, secure in self.ports:
            if not secure or self.tls:
                wait_until_free(self.bind, port)


def wait_until_free(bind, port, timeout=10):
    """Return once a fresh listener could bind, as the restarted services will."""
    deadline = time.monotonic() + timeout
    while True:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if os.name != 'nt':
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind((bind, port))
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(.2)
        finally:
            probe.close()


def enabled():
    return os.environ.get('SURVIE_MAINTENANCE_SITE', '1') != '0'


def open_site(config, status=None, *, wait=180):
    """Start the site for an installation whose services are (being) stopped."""
    if not enabled():
        return None
    data = config['data_dir']
    provider = status or (lambda: read_status(data))
    try:
        tls = tls_contexts(data, config.get('lan_host', 'localhost'))
    except (OSError, ssl.SSLError, ValueError):
        tls = None
    return Site(provider, bind=config.get('bind', '0.0.0.0'), tls=tls, wait=wait).start()


@contextmanager
def running(config, status=None, *, wait=180):
    site = open_site(config, status, wait=wait)
    try:
        yield site
    finally:
        if site:
            site.close()
