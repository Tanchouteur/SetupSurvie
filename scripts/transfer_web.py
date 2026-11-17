"""Local browser view for the transfer assistant on the server PC."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Full
import secrets
from threading import Thread
from urllib.parse import urlsplit

import transfer

PORT = 18780
PAGE = '/suivi-copie.html'
URL = f'http://127.0.0.1:{PORT}{PAGE}'
PORTAL = Path(__file__).resolve().parents[1]/'portal'

ASSETS = {
    PAGE: 'text/html; charset=utf-8',
    '/suivi-copie.css': 'text/css; charset=utf-8',
    '/suivi-copie.js': 'text/javascript; charset=utf-8',
}
PROGRESS = ('state', 'phase', 'bytes_total', 'bytes_verified', 'files_done',
            'files_total', 'file_bytes', 'file_total', 'updated_at', 'reason')
STAGES = {
    'copied': 'Copie vérifiée',
    'adapting': 'Préparation en cours',
    'prepared': 'Disque prêt à être activé',
    'activating': 'Activation et contrôle des services',
    'active': 'SetupSurvie fonctionne depuis le nouveau disque',
    'returning_to_source': 'Retour à la source en cours',
    'returned_to_source': 'Retour à la source terminé',
}
COMMANDS = {'choose', 'examine', 'copy', 'prepare', 'verify', 'activate', 'rollback'}
CONFIRM = {'copy', 'activate', 'rollback'}


def browser_status(destination):
    if destination is None:
        return {'state': 'ready', 'phase': 'Choisissez la destination.', 'destination': ''}
    status = transfer.copy_status(destination)
    result = {key: status[key] for key in PROGRESS if key in status}
    result['destination'] = str(destination)
    result.setdefault('state', 'ready')
    result.setdefault('phase', 'Destination choisie')
    report = destination/'Rapport-transfert.json'
    if report.is_file():
        stage = transfer.read(report).get('phase')
        if stage in STAGES:
            result.update(state=stage, phase=STAGES[stage])
    return result


class Handler(BaseHTTPRequestHandler):
    def reply(self, mime, body, code=200):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def local_host(self):
        port = self.server.server_port
        return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

    def authorized(self):
        provided = self.headers.get('X-SetupSurvie-Transfer', '')
        return self.server.token and provided.isascii() and secrets.compare_digest(provided, self.server.token)

    def do_GET(self):
        if not self.local_host():
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == '/api/suivi-copie':
            try:
                status = browser_status(self.server.destination)
            except (OSError, ValueError, KeyError):
                self.send_error(503)
                return
            if self.authorized():
                status.update(commands=True, **self.server.activity)
            self.reply('application/json; charset=utf-8',
                       json.dumps(status, ensure_ascii=False).encode('utf-8'))
        elif path in ASSETS:
            asset = PORTAL/path.removeprefix('/')
            try:
                body = asset.read_bytes()
            except OSError:
                self.send_error(404)
                return
            self.reply(ASSETS[path], body)
        else:
            self.send_error(404)

    def do_POST(self):
        if urlsplit(self.path).path != '/api/suivi-copie/action':
            self.send_error(404)
            return
        origin = f'http://127.0.0.1:{self.server.server_port}'
        if not self.local_host() or self.headers.get('Origin') != origin or not self.authorized():
            self.send_error(403)
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 4096:
                raise ValueError
            self.connection.settimeout(5)
            data = json.loads(self.rfile.read(length))
            action = data.get('action')
            destination = data.get('destination')
            if (action not in COMMANDS or not isinstance(destination, str)
                or len(destination) > 1024 or (action in CONFIRM and data.get('confirmed') is not True)):
                raise ValueError
        except (OSError, ValueError, TypeError, AttributeError):
            self.send_error(400)
            return
        try:
            if self.server.activity.get('busy'):
                raise Full
            self.server.commands.put_nowait((action, destination))
        except Full:
            self.send_error(409)
            return
        self.reply('application/json; charset=utf-8', b'{}', 202)

    def log_message(self, *args):
        pass


class Monitor:
    def __init__(self, destination, port=PORT, *, commands=None):
        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.server.destination = destination
        self.server.commands = commands
        self.server.token = secrets.token_urlsafe(32) if commands is not None else None
        self.server.activity = {'busy': False, 'message': ''}
        self.worker = Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.2}, daemon=True)
        self.worker.start()

    def move(self, destination):
        self.server.destination = destination

    def activity(self, busy, message):
        self.server.activity = {'busy': busy, 'message': message}

    def browser_url(self):
        return URL + (f'#autorisation={self.server.token}' if self.server.token else '')

    def close(self):
        self.server.shutdown()
        self.server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    monitor = Monitor(parser.parse_args().destination.resolve())
    try:
        monitor.worker.join()
    except KeyboardInterrupt:
        monitor.close()
