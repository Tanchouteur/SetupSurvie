import json
from pathlib import Path
from queue import Queue
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import setup
import transfer_web


class TransferWebTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.dest = Path(temporary.name) / 'Nouveau SSD'
        self.monitor = transfer_web.Monitor(self.dest, port=0)
        self.addCleanup(self.monitor.close)
        self.url = f'http://127.0.0.1:{self.monitor.server.server_port}'
        self.open = build_opener(ProxyHandler({})).open

    def test_browser_shows_selected_destination_and_redacts_process_identity(self):
        with self.open(self.url + transfer_web.PAGE, timeout=3) as response:
            self.assertIn('Dossier de destination', response.read().decode('utf-8'))
        setup.write_json(self.dest / 'Suivi-transfert.json', {
            'state': 'interrupted', 'phase': 'Copie', 'pid': 42, 'identity': {'private': True},
            'bytes_verified': 15, 'bytes_total': 30,
        })
        with self.open(self.url + '/api/suivi-copie', timeout=3) as response:
            state = json.load(response)
        self.assertEqual(state['destination'], str(self.dest))
        self.assertEqual(state['bytes_verified'], 15)
        self.assertEqual(state['state'], 'interrupted')
        self.assertNotIn('pid', state)
        self.assertNotIn('identity', state)

    def test_browser_view_rejects_foreign_origin_host_and_non_monitor_files(self):
        request = Request(self.url + '/api/suivi-copie', headers={'Host': 'another.example'})
        with self.assertRaises(HTTPError) as denied:
            self.open(request, timeout=3)
        self.assertEqual(denied.exception.code, 403)
        with self.assertRaises(HTTPError) as missing:
            self.open(self.url + '/transfer.json', timeout=3)
        self.assertEqual(missing.exception.code, 404)

    def test_command_requires_local_origin_session_token_and_confirmation(self):
        queue = Queue(maxsize=1)
        monitor = transfer_web.Monitor(self.dest, port=0, commands=queue)
        self.addCleanup(monitor.close)
        origin = f'http://127.0.0.1:{monitor.server.server_port}'
        url = origin + '/api/suivi-copie/action'
        def send(token, confirmed, request_origin=origin):
            body = json.dumps({'action': 'copy', 'destination': str(self.dest),
                               'confirmed': confirmed}).encode()
            request = Request(url, data=body, headers={
                'Origin': request_origin, 'X-SetupSurvie-Transfer': token,
                'Content-Type': 'application/json',
            })
            return self.open(request, timeout=3)
        with self.assertRaises(HTTPError) as denied:
            send('wrong', True)
        self.assertEqual(denied.exception.code, 403)
        with self.assertRaises(HTTPError) as denied:
            send(monitor.server.token, True, 'http://foreign.test')
        self.assertEqual(denied.exception.code, 403)
        with self.assertRaises(HTTPError) as missing:
            send(monitor.server.token, False)
        self.assertEqual(missing.exception.code, 400)
        with send(monitor.server.token, True) as response:
            self.assertEqual(response.status, 202)
        self.assertEqual(queue.get_nowait(), ('copy', str(self.dest)))
