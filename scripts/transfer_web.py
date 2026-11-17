"""Read-only browser view for the transfer assistant on the server PC."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
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


def browser_status(destination):
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
    def reply(self, mime, body):
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        port = self.server.server_port
        if self.headers.get('Host') not in (f'127.0.0.1:{port}', f'localhost:{port}'):
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == '/api/suivi-copie':
            try:
                status = browser_status(self.server.destination)
            except (OSError, ValueError, KeyError):
                self.send_error(503)
                return
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

    def log_message(self, *args):
        pass


class Monitor:
    def __init__(self, destination, port=PORT):
        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.server.destination = destination
        self.worker = Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.2}, daemon=True)
        self.worker.start()

    def move(self, destination):
        self.server.destination = destination

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
