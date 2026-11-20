"""Temporary maintenance site and shared status (scripts/maintenance_site.py)."""
import json
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import maintenance_site  # noqa: E402
import pilot_update  # noqa: E402
import transfer  # noqa: E402

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def wait_for(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(.02)
    return False


def get(url, method='GET', data=None):
    request = urllib.request.Request(url, method=method, data=data)
    try:
        response = OPENER.open(request, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers), response.read()


class StatusWriterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = Path(temp.name)
        (self.data/'catalog').mkdir()

    def test_phases_mark_unavailability_rollback_and_final_state(self):
        writer = maintenance_site.StatusWriter(self.data, installed='0.67.4', available='0.68.0')
        writer.progress('git')
        self.assertFalse(maintenance_site.read_status(self.data)['unavailable'])
        writer.progress('backup', current=3, total=10)
        status = maintenance_site.read_status(self.data)
        self.assertTrue(status['unavailable'])
        self.assertEqual((status['state'], status['title']), ('running', 'Sauvegarde des données'))
        writer.progress('rollback')
        writer.progress('error', 'Étape interrompue.')
        status = maintenance_site.read_status(self.data)
        self.assertEqual(status['state'], 'failed')
        self.assertTrue(status['rolled_back'])
        self.assertFalse(status['unavailable'])
        self.assertEqual([step['phase'] for step in status['steps']], ['git', 'backup', 'rollback', 'error'])

    def test_lines_are_bounded_and_unknown_phases_ignored(self):
        writer = maintenance_site.StatusWriter(self.data)
        writer.progress('not-a-phase', 'ignored')
        for number in range(80):
            writer.line(f'ligne {number}  avec   espaces')
        writer.save(force=True)
        status = maintenance_site.read_status(self.data)
        self.assertEqual(len(status['lines']), maintenance_site.MAX_LINES)
        self.assertTrue(status['lines'][-1].endswith('ligne 79 avec espaces'))
        self.assertEqual(status['steps'], [])

    def test_unreadable_or_oversized_status_is_ignored(self):
        path = maintenance_site.status_path(self.data)
        path.write_text('{')
        self.assertIsNone(maintenance_site.read_status(self.data))
        path.write_text(json.dumps({'x': 'y' * 300_000}))
        self.assertIsNone(maintenance_site.read_status(self.data))

    def test_powershell_launcher_uses_the_same_phases(self):
        script = (ROOT/'scripts/update-windows.ps1').read_text(encoding='utf-8-sig')
        block = script[script.index('$script:updateStages = @{'):]
        block = block[:block.index('\n}')]
        keys = re.findall(r'^\s+(\w+) = ', block, re.MULTILINE)
        self.assertEqual(sorted(keys), sorted(maintenance_site.PHASES))
        unavailable = re.search(r"\$script:unavailablePhases = @\(([^)]*)\)", script).group(1)
        self.assertEqual(re.findall(r"'(\w+)'", unavailable), list(maintenance_site.UNAVAILABLE))

    def test_direct_update_publishes_status_without_launcher(self):
        app = type('App', (), {'load': lambda self: {'data_dir': str(self.data)}})()
        app.data = self.data
        with patch.dict('os.environ', {'SURVIE_UPDATE_PROGRESS': ''}), patch.object(pilot_update, 'STATUS', None):
            pilot_update.start_status(app, 'apply')
            self.assertIsNotNone(pilot_update.STATUS)
            pilot_update.report_progress('stop')
        self.assertEqual(maintenance_site.read_status(self.data)['phase'], 'stop')
        with patch.dict('os.environ', {'SURVIE_UPDATE_PROGRESS': '1'}), patch.object(pilot_update, 'STATUS', None):
            pilot_update.start_status(app, 'apply')
            self.assertIsNone(pilot_update.STATUS)


class SiteTests(unittest.TestCase):
    def start(self, status=lambda: {'schema': 1, 'state': 'running', 'title': 'Sauvegarde'}, **options):
        port = options.pop('port', None) or free_port()
        site = maintenance_site.Site(status, bind='127.0.0.1', ports=((port, False),), **options).start()
        self.addCleanup(site.close)
        self.assertTrue(wait_for(lambda: site.servers, options.get('wait', 5) + 2))
        return site, f'http://127.0.0.1:{port}'

    def test_routes_serve_status_page_and_refuse_api(self):
        site, base = self.start()
        code, headers, body = get(base+'/catalog/maintenance.json')
        self.assertEqual(code, 200)
        self.assertEqual(headers['X-SetupSurvie-Maintenance'], '1')
        self.assertEqual(json.loads(body)['served_by'], 'maintenance')
        code, headers, body = get(base+'/#/bibliotheque')
        self.assertEqual(code, 503)
        self.assertIn('maintenance-standalone', body.decode())
        self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(get(base+'/api/health')[0], 503)
        self.assertTrue(json.loads(get(base+'/api/health')[2])['maintenance'])
        self.assertEqual(get(base+'/api/conversations', 'POST', b'{}')[0], 503)
        self.assertEqual(get(base+'/maintenance-view.js')[0], 200)
        self.assertEqual(get(base+'/../../private/settings.json')[0], 503)

    def test_failing_status_provider_still_answers(self):
        def broken():
            raise OSError('unreadable')
        _, base = self.start(broken)
        status = json.loads(get(base+'/catalog/maintenance.json')[2])
        self.assertEqual(status['state'], 'running')

    def test_waits_for_the_port_then_releases_it_on_close(self):
        port = free_port()
        holder = socket.socket()
        holder.bind(('127.0.0.1', port))
        holder.listen()
        site = maintenance_site.Site(lambda: None, bind='127.0.0.1', ports=((port, False),), wait=10).start()
        self.addCleanup(site.close)
        time.sleep(.7)
        self.assertEqual(site.servers, [])
        holder.close()
        self.assertTrue(wait_for(lambda: site.servers, 5))
        self.assertEqual(get(f'http://127.0.0.1:{port}/api/health')[0], 503)
        site.close()
        self.assertTrue(maintenance_site.wait_until_free('127.0.0.1', port, timeout=1))

    def test_assets_stay_in_memory_when_the_application_is_renamed(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        portal = Path(temp.name)/'portal'
        shutil.copytree(ROOT/'portal', portal, ignore=shutil.ignore_patterns('vendor', 'design', 'interface', '*.pdf'))
        assets = maintenance_site.load_assets(portal)
        shutil.rmtree(portal)
        _, base = self.start(assets=assets)
        self.assertEqual(get(base+'/maintenance-view.css')[0], 200)
        self.assertIn(b'maintenance-standalone', get(base+'/')[2])

    def test_disabled_site_opens_nothing(self):
        with patch.dict('os.environ', {'SURVIE_MAINTENANCE_SITE': '0'}):
            self.assertIsNone(maintenance_site.open_site({'data_dir': '/nonexistent'}))

    @unittest.skipUnless(shutil.which('openssl'), 'openssl absent')
    def test_https_reuses_caddy_local_certificates(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        data = Path(temp.name)
        folder = data/'state/caddy/caddy/certificates/local/survie.local'
        folder.mkdir(parents=True)
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=survie.local',
                        '-keyout', str(folder/'survie.local.key'), '-out', str(folder/'survie.local.crt')],
                       check=True, capture_output=True)
        tls = maintenance_site.tls_contexts(data, 'survie.local')
        self.assertIsNotNone(tls)
        port = free_port()
        site = maintenance_site.Site(lambda: {'state': 'running'}, bind='127.0.0.1', ports=((port, True),), tls=tls).start()
        self.addCleanup(site.close)
        self.assertTrue(wait_for(lambda: site.servers))
        client = ssl.create_default_context()
        client.check_hostname = False
        client.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=client))
        with opener.open(f'https://127.0.0.1:{port}/catalog/maintenance.json', timeout=3) as response:
            self.assertEqual(json.loads(response.read())['served_by'], 'maintenance')
        self.assertIsNone(maintenance_site.tls_contexts(data/'missing', 'survie.local'))


class ServicesTests(unittest.TestCase):
    def test_site_opens_after_stop_and_closes_before_restart(self):
        events = []

        class Site:
            def close(self):
                events.append('site-close')

        class App:
            work = Path('/nonexistent')
            def compose(self, config, *args, **kwargs):
                events.append('compose-'+args[0])
            def render(self, config):
                pass

        services = pilot_update.Services(App(), {'target': 'linux', 'data_dir': '/nonexistent'})
        modules = {'control': type(sys)('control'), 'discovery': type(sys)('discovery')}
        for module in modules.values():
            module.stop = lambda app: None
            module.start = lambda app, config: None
        with patch.dict(sys.modules, modules), \
                patch.object(maintenance_site, 'open_site', side_effect=lambda config: events.append('site-open') or Site()):
            services.stop()
            services.stop()  # A rollback stops again: still a single page.
            services.start()
        self.assertEqual(events[:4], ['compose-stop', 'site-open', 'compose-stop', 'site-close'])
        self.assertLess(events.index('site-close'), events.index('compose-up'))
        self.assertIsNone(services.site)


class TransferViewTests(unittest.TestCase):
    def test_copy_progress_is_read_from_the_destination_only(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        dest = Path(temp.name)/'dest'
        dest.mkdir()
        self.assertEqual(transfer.maintenance_view(dest, 'abc', 10)['state'], 'running')
        report = {'state': 'interrupted', 'phase': 'Copie', 'reason': 'Espace insuffisant sur le disque de destination.',
                  'bytes_total': 4e9, 'bytes_verified': 1e9, 'files_done': 3, 'files_total': 9, 'updated_at': 20}
        (dest/'Suivi-transfert.json').write_text(json.dumps(report))
        view = transfer.maintenance_view(dest, 'abc', 10)
        self.assertEqual((view['state'], view['detail'], view['current'], view['unit']),
                         ('failed', report['reason'], 1e9, 'bytes'))
        report.update(state='copied')
        (dest/'Suivi-transfert.json').write_text(json.dumps(report))
        self.assertEqual(transfer.maintenance_view(dest, 'abc', 10)['state'], 'completed')


if __name__ == '__main__':
    unittest.main()
