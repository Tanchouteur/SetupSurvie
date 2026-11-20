"""Update check and portal launch on the host (scripts/update_watch.py), with a real local Git."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import maintenance_site  # noqa: E402
import setup  # noqa: E402
import update_watch  # noqa: E402

GIT = shutil.which('git')
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 'test@example.invalid',
       'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@example.invalid', 'GIT_CONFIG_GLOBAL': os.devnull}


def git(*arguments, cwd=None):
    return subprocess.run([GIT, *arguments], cwd=cwd, env=ENV, check=True, capture_output=True, text=True).stdout


def release(folder, version):
    (folder/'deploy').mkdir(parents=True, exist_ok=True)
    (folder/'deploy/release.json').write_text(json.dumps({'version': version, 'data_schema': 1}))


@unittest.skipUnless(GIT, 'git absent')
class WatcherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        upstream = self.root/'upstream'
        upstream.mkdir()
        git('init', '-q', '-b', 'main', cwd=upstream)
        release(upstream, '0.67.4')
        git('add', '.', cwd=upstream)
        git('commit', '-q', '-m', 'Version installée', cwd=upstream)
        self.origin = self.root/'origin.git'
        git('clone', '-q', '--bare', str(upstream), str(self.origin))
        self.base = self.root/'SetupSurvie'
        git('clone', '-q', '--branch', 'main', str(self.origin), str(self.base/'maintenance/source'))
        (self.base/'maintenance/update-windows.ps1').write_text('# fixture')
        self.application = self.base/'application'
        release(self.application, '0.67.4')
        self.data = self.base/'donnees'
        (self.data/'catalog').mkdir(parents=True)
        self.app = setup.Installation(self.base/'prive')
        self.app.work.mkdir(parents=True)
        self.config = {'target': 'windows', 'app_dir': str(self.application), 'data_dir': str(self.data)}
        patcher = patch.object(setup, 'ROOT', self.application)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Publish a newer main, as Louis does with a push.
        work = self.root/'work'
        git('clone', '-q', str(self.origin), str(work))
        release(work, '0.68.0')
        git('commit', '-q', '-am', 'Suivre les mises à jour depuis le portail', cwd=work)
        git('push', '-q', 'origin', 'main', cwd=work)

    def watcher(self, **options):
        return update_watch.Watcher(self.app, self.config, git=GIT, repository=str(self.origin), **options)

    def test_check_reads_origin_main_without_touching_the_working_tree(self):
        watcher = self.watcher()
        before = git('rev-parse', 'HEAD', cwd=self.base/'maintenance/source')
        watcher.run_check()
        status = watcher.status()
        self.assertTrue(status['supported'])
        self.assertTrue(status['update_available'])
        self.assertEqual((status['installed'], status['available']), ('0.67.4', '0.68.0'))
        self.assertEqual(status['changes'], ['Suivre les mises à jour depuis le portail'])
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.base/'maintenance/source'), before)
        self.assertEqual(json.loads((self.app.work/'update-check.json').read_text())['available'], '0.68.0')
        # A new controller starts from the cached result.
        self.assertEqual(self.watcher().status()['available'], '0.68.0')

    def test_installed_version_hides_an_equal_or_older_main(self):
        release(self.application, '0.68.0')
        watcher = self.watcher()
        watcher.run_check()
        self.assertFalse(watcher.status()['update_available'])
        self.assertEqual(watcher.status()['changes'], [])

    def test_offline_check_keeps_the_last_known_version(self):
        watcher = self.watcher()
        watcher.run_check()
        shutil.rmtree(self.origin)
        watcher.run_check()
        status = watcher.status()
        self.assertIn('Internet', status['error'])
        self.assertEqual(status['available'], '0.68.0')

    def test_unexpected_remote_or_missing_clone_is_reported(self):
        watcher = update_watch.Watcher(self.app, self.config, git=GIT, repository='https://example.invalid/autre.git')
        watcher.run_check()
        self.assertIn('dépôt prévu', watcher.status()['error'])
        shutil.rmtree(self.base/'maintenance/source')
        watcher.run_check()
        self.assertIn('raccourci', watcher.status()['error'])

    def test_linux_and_development_installations_are_not_supported(self):
        self.assertFalse(update_watch.Watcher(self.app, {**self.config, 'target': 'linux'}).supported())
        (self.application/'.git').mkdir()
        self.assertFalse(self.watcher().supported())
        with self.assertRaises(setup.SetupError):
            self.watcher().start_update()

    def test_manual_checks_are_spaced(self):
        clock = [1000.0]
        watcher = self.watcher(clock=lambda: clock[0])
        with patch.object(watcher, 'check', return_value=True) as check:
            self.assertTrue(watcher.request_check())
            self.assertFalse(watcher.request_check())
            clock[0] += update_watch.MANUAL_SPACING + 1
            self.assertTrue(watcher.request_check())
        self.assertEqual(check.call_count, 2)

    def test_start_launches_the_stable_updater_and_publishes_a_first_status(self):
        watcher = self.watcher()
        watcher.run_check()

        class Process:
            def __init__(self, command, **options):
                self.command, self.options = command, options
            def wait(self):
                return 0
            def poll(self):
                return None

        with patch.object(update_watch.subprocess, 'Popen', side_effect=Process) as popen, \
                patch.object(update_watch.threading, 'Thread'):
            operation = watcher.start_update()
        command = popen.call_args.args[0]
        self.assertIn(str(self.base/'maintenance/update-windows.ps1'), command)
        self.assertEqual(command[-2:], ['-OperationId', operation])
        self.assertNotIn('SURVIE_UPDATE_PROGRESS', popen.call_args.kwargs['env'])
        status = maintenance_site.read_status(self.data)
        self.assertEqual((status['id'], status['state'], status['available']), (operation, 'running', '0.68.0'))
        with self.assertRaisesRegex(setup.SetupError, 'déjà en cours'):
            watcher.start_update()

    def test_start_is_refused_during_transfer_or_unrecovered_update(self):
        watcher = self.watcher()
        (self.app.work/'transfer-guard.json').write_text('{}')
        with self.assertRaisesRegex(setup.SetupError, 'transfert'):
            watcher.start_update()
        (self.app.work/'transfer-guard.json').unlink()
        (self.app.work/'update.json').write_text(json.dumps({'phase': 'switched'}))
        with self.assertRaisesRegex(setup.SetupError, 'récupérée'):
            watcher.start_update()
        self.assertIsNone(maintenance_site.read_status(self.data))

    def test_updater_stopping_before_its_first_report_is_shown_as_failed(self):
        watcher = self.watcher()
        writer = maintenance_site.StatusWriter(self.data, operation_id='a'*32)
        writer.progress('setup', 'Lancement demandé depuis le portail.')

        class Process:
            def wait(self):
                return 1
        watcher.watch_launch(Process(), 'a'*32)
        status = maintenance_site.read_status(self.data)
        self.assertEqual(status['state'], 'failed')
        self.assertIn('code 1', status['detail'])
        # A status already finished by the updater is never overwritten.
        writer = maintenance_site.StatusWriter(self.data, operation_id='b'*32)
        writer.progress('done')
        watcher.watch_launch(Process(), 'b'*32)
        self.assertEqual(maintenance_site.read_status(self.data)['state'], 'completed')

    def test_stale_running_status_does_not_block_forever(self):
        writer = maintenance_site.StatusWriter(self.data)
        writer.progress('backup')
        self.assertTrue(self.watcher().status()['running'])
        value = maintenance_site.read_status(self.data)
        value['updated'] -= update_watch.STALE_RUNNING + 10
        maintenance_site.publish_status(self.data, value)
        self.assertFalse(self.watcher().status()['running'])


if __name__ == '__main__':
    unittest.main()
