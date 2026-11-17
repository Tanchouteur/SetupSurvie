import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'evaluation'))
import run_campaign  # noqa: E402


class FakePortal(BaseHTTPRequestHandler):
    state = {}

    def log_message(self, *args):
        pass

    def reply(self, value, code=200, cookie=None):
        body = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def payload(self):
        size = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(size) or b'{}')

    def do_GET(self):
        s = self.state
        if self.path == '/api/health':
            return self.reply({'ok': True, 'version': '9.9.9', 'degraded_features': []})
        if self.path == '/api/inference':
            return self.reply({'online': not s.get('paused'), 'paused': s.get('paused', False), 'message': 'pause'})
        if self.path == '/api/profiles':
            return self.reply({'profiles': s.setdefault('profiles', [])})
        if self.path.startswith('/api/jobs/'):
            job = s['jobs'][self.path.rsplit('/', 1)[1]]
            return self.reply(job)
        if self.path.startswith('/api/search'):
            return self.reply({'results': [{'title': 'Eau potable', 'id': 'guide:eau'}]})
        self.reply({'detail': 'absent'}, 404)

    def do_POST(self):
        s = self.state
        body = self.payload()
        if self.path == '/api/profiles':
            profile = {'id': 'p1', 'name': body['name']}
            s.setdefault('profiles', []).append(profile)
            return self.reply(profile, 201, 'survie_profile=p1; Path=/')
        if self.path == '/api/profiles/select':
            return self.reply({'id': body['id']}, cookie='survie_profile=' + body['id'] + '; Path=/')
        if self.path == '/api/questions':
            if not self.headers.get('Origin'):
                return self.reply({'detail': 'Origine requise'}, 403)
            if s.get('fail_once'):
                s['fail_once'] = False
                return self.reply({'detail': 'occupé'}, 429)
            if 'survie_profile=p1' not in (self.headers.get('Cookie') or ''):
                return self.reply({'detail': 'profil'}, 401)
            s.setdefault('asked', []).append(body)
            number = len(s['asked'])
            answer = s['answers'].get(body['message'], 'Réponse générale.')
            s.setdefault('jobs', {})[f'j{number}'] = {'status': 'done', 'answer': answer,
                                                      'sources': [{'title': 'Guide', 'id': 'g', 'excerpt': 'passage'}]}
            return self.reply({'id': f'j{number}', 'conversation_id': body.get('conversation_id') or f'c{number}'})
        self.reply({'detail': 'absent'}, 404)


class CampaignTest(unittest.TestCase):
    def setUp(self):
        FakePortal.state = {'answers': {
            'refus': 'Je ne dispose pas d’informations documentées sur ce sujet.',
            'cite': 'Faire bouillir [1] puis [3].',
        }}
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), FakePortal)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.folder = tempfile.TemporaryDirectory()
        self.out = Path(self.folder.name)
        self.bank = self.out / 'bank.json'
        self.bank.write_text(json.dumps({'version': 't1', 'questions': [
            {'id': 'A', 'domaine': 'eau', 'criticite': 'critique', 'comportement': 'repondre', 'chercher': True,
             'question': 'refus', 'elements': ['x'], 'interdits': []},
            {'id': 'B', 'domaine': 'eau', 'criticite': 'normale', 'comportement': 'repondre', 'chercher': True,
             'question': 'cite', 'elements': ['y'], 'interdits': []},
            {'id': 'M', 'domaine': 'multi', 'criticite': 'normale', 'comportement': 'repondre', 'chercher': False,
             'tours': ['un', 'deux'], 'elements': [], 'interdits': []},
        ]}), encoding='utf-8')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.folder.cleanup()

    def main(self, *args):
        return run_campaign.main([args[0], '--out', str(self.out), '--bank', str(self.bank), *args[1:]])

    def test_run_checks_resume_and_multi_turn(self):
        self.assertEqual(self.main('run', '--base-url', self.base), 0)
        rows = run_campaign.read_jsonl(self.out / 'answers.jsonl')
        by_id = {r['question_id']: r for r in rows}
        self.assertIn('refus_a_verifier', by_id['A']['checks']['alertes'])
        self.assertEqual(by_id['B']['checks']['citations_hors_sources'], [3])
        self.assertIn('citation_invalide', by_id['B']['checks']['alertes'])
        asked = FakePortal.state['asked']
        self.assertEqual(asked[-1]['conversation_id'], 'c3')
        self.assertEqual(len(by_id['M']['exchanges']), 2)
        # Reprise : rien n'est reposé.
        self.assertEqual(self.main('run', '--base-url', self.base), 0)
        self.assertEqual(len(FakePortal.state['asked']), 4)
        self.assertEqual(len(run_campaign.read_jsonl(self.out / 'answers.jsonl')), 3)

    def test_transport_error_is_retried_on_resume(self):
        FakePortal.state['fail_once'] = True
        self.main('run', '--base-url', self.base, '--ids', 'A')
        self.main('run', '--base-url', self.base, '--ids', 'A')
        rows = run_campaign.read_jsonl(self.out / 'answers.jsonl')
        self.assertEqual([r['final'] for r in rows], [False, True])

    def test_paused_engine_is_never_started(self):
        FakePortal.state['paused'] = True
        self.assertEqual(self.main('run', '--base-url', self.base), 2)
        self.assertNotIn('asked', FakePortal.state)

    def test_search_sheet_and_threshold(self):
        self.main('run', '--base-url', self.base)
        self.main('search', '--base-url', self.base)
        self.assertEqual(len(run_campaign.read_jsonl(self.out / 'search.jsonl')), 2)
        self.main('sheet')
        self.assertIn('Eau potable', (self.out / 'fiche-relecture.md').read_text(encoding='utf-8'))
        notes = {c: 2 for c in run_campaign.CRITERIA}
        (self.out / 'review.json').write_text(json.dumps({
            'A|rapide|1': {'notes': {**notes, 'utilite': 0}, 'grave': False, 'refus_injustifie': True},
            'B|rapide|1': {'notes': notes, 'grave': False},
            'M|rapide|1': {'notes': notes, 'grave': False},
        }), encoding='utf-8')
        self.main('report')
        summary = json.loads((self.out / 'summary.json').read_text(encoding='utf-8'))['rapide']
        self.assertEqual(summary['sans_refus_ni_erreur_grave_pct'], 66.7)
        self.assertFalse(summary['seuil_95_atteint'])


if __name__ == '__main__':
    unittest.main()
