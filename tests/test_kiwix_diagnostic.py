"""Tiny HTTP fixtures only: no Docker, archives, models or real installation."""
import json
import os
import signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import diagnose_kiwix as diagnostic


class Handler(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.calls.append(self.path)
        path = urlsplit(self.path).path
        if path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/private')
            self.end_headers()
            return
        self.send_response(503 if path == '/error' else 200)
        self.send_header('Content-Type', 'text/event-stream' if path in ('/api/search', '/partial', '/incomplete') else 'text/plain')
        self.end_headers()
        try:
            if path == '/slow':
                time.sleep(1)
            elif path in ('/api/search', '/partial', '/incomplete'):
                self.wfile.write(b': heartbeat\n\ndata: {"state":"working"}\n\n')
                payload = {'state': 'results', 'results': [{'id': 'tiny'}],
                           'coverage': {'status': 'partial', 'searched': 1}}
                self.wfile.write(('data: ' + json.dumps(payload) + '\r\n\r\n').encode())
                self.wfile.flush()
                if path == '/incomplete':
                    return
                if parse_qs(urlsplit(self.path).query).get('q') == ['stall']:
                    time.sleep(1)
                time.sleep(1 if path == '/partial' else .08)
                payload.update(state='done', coverage={'status': 'complete', 'searched': 1,
                                                      'cache_hits': 2, 'trace': []})
                self.wfile.write(('data: ' + json.dumps(payload) + '\n\n').encode())
            elif path == '/api/library/search-diagnostic':
                self.wfile.write(b'{"version":"fixture","catalog":{"collections":1},"kiwix":{"state":"reachable"}}')
            elif path == '/search':
                self.wfile.write(b'<rss><channel><item><title>Fictif</title></item></channel></rss>')
            elif path == '/bad':
                self.wfile.write(b'<html>Error</html>')
            elif path == '/large':
                self.wfile.write(b'x' * (diagnostic.MAX_BYTES + 1))
            else:
                self.wfile.write(b'Kiwix fixture')
        except (BrokenPipeError, ConnectionResetError):
            pass


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def probe(self, path, kind='access', timeout=3):
        return diagnostic.measure(self.base + path, kind, timeout, time.monotonic() + 5)

    def args(self):
        return diagnostic.parser().parse_args(['--portal', self.base, '--kiwix', self.base,
            '--query', 'eau & vélo', '--book', 'tiny_fr_2026', '--collection', 'tiny_fr_2026',
            '--output', 'unused.json'])

    def test_sequential_repetition_and_correct_scoping(self):
        Handler.calls.clear()
        report = diagnostic.run(self.args())
        self.assertEqual(report['status'], 'measured')
        self.assertEqual(len(report['steps']), 7)
        self.assertTrue(all(s['status'] == 'complete' for s in report['steps']))
        self.assertEqual([urlsplit(c).path for c in Handler.calls],
                         ['/api/library/search-diagnostic', '/', '/search', '/api/search', '/', '/search', '/api/search'])
        native = parse_qs(urlsplit(Handler.calls[2]).query)
        self.assertEqual(native['books.name'], ['tiny_fr_2026'])
        self.assertEqual(native['pattern'], ['eau & vélo'])
        portal = parse_qs(urlsplit(Handler.calls[3]).query)
        self.assertEqual(portal['collection'], ['tiny_fr_2026'])
        self.assertEqual(portal['stream'], ['true'])
        self.assertEqual(report['resources'], 'inconnu')
        for row in (report['steps'][3], report['steps'][6]):
            self.assertEqual(row['updates_received'], 1)
            self.assertLess(row['first_results_ms'], row['elapsed_ms'])
            self.assertEqual(row['coverage']['cache_hits'], 2)
        self.assertIsNotNone(report['steps'][2]['first_results_ms'])

    def test_partial_results_survive_deadline(self):
        row = self.probe('/partial', 'stream', .5)
        self.assertEqual(row['status'], 'timeout')
        self.assertEqual(row['result_count'], 1)
        self.assertIsNotNone(row['first_results_ms'])
        self.assertEqual(row['coverage']['status'], 'partial')
        self.assertLess(row['elapsed_ms'], 1500)

    def test_http_invalid_format_size_and_redirect(self):
        for path, kind in [('/error', 'access'), ('/bad', 'xml'), ('/bad', 'json'),
                           ('/bad', 'stream'), ('/incomplete', 'stream'), ('/large', 'access'), ('/redirect', 'access')]:
            with self.subTest(path=path, kind=kind):
                row = self.probe(path, kind)
                self.assertEqual(row['status'], 'error')
        self.assertNotIn('/private', Handler.calls)

    def test_global_budget_stops_following_steps(self):
        args = self.args()
        args.max_seconds = .02
        def slow(*_):
            time.sleep(.03)
            return {'status': 'timeout'}
        report = diagnostic.run(args, slow)
        self.assertEqual(report['status'], 'budget_exhausted')
        self.assertEqual(len(report['steps']), 1)

    def test_cancel_stops_and_exports_partial_report(self):
        def cancelled(*_):
            return {'status': 'cancelled', 'result_count': 1}
        report = diagnostic.run(self.args(), cancelled)
        self.assertEqual(report['status'], 'cancelled')
        self.assertEqual(len(report['steps']), 1)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'report.json'
            argv = ['diagnose_kiwix.py', '--query', 'eau', '--book', 'tiny', '--collection', 'tiny', '--output', str(target)]
            with patch.object(sys, 'argv', argv), patch.object(diagnostic, 'run', return_value=report):
                self.assertEqual(diagnostic.main(), 130)
                self.assertEqual(json.loads(target.read_text())['status'], 'cancelled')
                with self.assertRaises(FileExistsError):
                    diagnostic.main()

    @unittest.skipIf(os.name == 'nt', 'SIGINT Unix ; Ctrl+C Windows à vérifier sur cible')
    def test_real_cli_ctrl_c_exports_received_results(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'interrupted.json'
            Handler.calls.clear()
            process = subprocess.Popen([sys.executable, diagnostic.__file__, '--portal', self.base,
                '--kiwix', self.base, '--query', 'stall', '--book', 'tiny', '--collection', 'tiny',
                '--output', str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 5
                while not any('/api/search?' in call for call in Handler.calls) and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(any('/api/search?' in call for call in Handler.calls))
                time.sleep(.1)
                process.send_signal(signal.SIGINT)
                _, errors = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 130, errors.decode())
                report = json.loads(target.read_text())
                self.assertEqual(report['status'], 'cancelled')
                self.assertEqual(report['steps'][-1]['status'], 'cancelled')
                self.assertEqual(report['steps'][-1]['result_count'], 1)
                self.assertIsNotNone(report['steps'][-1]['first_results_ms'])
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=3)

    def test_local_resources_unknown_service_values(self):
        with patch.object(diagnostic.runtime_resources, 'available_memory', return_value=None):
            resources = diagnostic.local_resources()
        self.assertEqual(resources['available_memory_bytes'], 'inconnu')
        self.assertEqual(resources['kiwix_cpu'], 'inconnu')

    def test_cli_rejects_unbounded_or_broad_requests(self):
        script = Path(diagnostic.__file__)
        for extra in (['--timeout', 'nan'], ['--max-seconds', 'inf'], ['--collection', 'group:all'],
                      ['--book', 'a,b'], ['--portal', 'http://user:password@localhost']):
            result = subprocess.run([sys.executable, str(script), '--query', 'eau', '--book', 'tiny',
                '--collection', 'tiny', '--output', 'unused.json', *extra], capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
