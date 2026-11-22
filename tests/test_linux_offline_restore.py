import hashlib
import io
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_offline_restore as restore
import setup
import transfer


@unittest.skipUnless(sys.platform == "linux", "Restauration système Linux.")
class OfflineRestoreTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.base = Path(directory) / 'Copie é 42%'
        self.base.mkdir()
        self.journal = {'kind': transfer.KIND, 'schema': 1, 'target': 'linux',
                        'source': {'private': str(Path(directory) / 'source')},
                        'phase': 'copied'}

    def test_launcher_dispatches_without_system_python(self):
        transfer.bundle_launcher(self.base)
        scripts = self.base / 'application/scripts'
        scripts.mkdir(parents=True)
        launcher = scripts / 'restaurer-linux-hors-ligne.sh'
        launcher.write_text('#!/bin/sh\nprintf "%s" "$1"\n')
        launcher.chmod(0o700)
        result = subprocess.run([str(self.base / 'transferer-setupsurvie.sh'), '--restaurer-hors-ligne'],
                                check=True, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stdout, str(self.base))

    def test_public_kit_launcher_falls_back_to_the_graphical_admin_path_without_python(self):
        kit = self.base/'Kit'
        scripts = kit/'app/scripts'
        scripts.mkdir(parents=True)
        (kit/'manifest.json').touch()
        tools = kit/'installateurs-linux/tools/linux-offline-installers'
        tools.mkdir(parents=True)
        (tools/'python-archive.txt').touch()
        (scripts/'linux_recovery_gui.sh').write_text('printf "%s\\n" "$@"\n')
        shell_tools = self.base/'bin'
        shell_tools.mkdir()
        missing = shell_tools/'python3'
        missing.write_text('#!/bin/sh\nexit 127\n')
        missing.chmod(0o755)
        result = subprocess.run(
            ['sh', ROOT/'scripts/restaurer-donnees-linux.sh', '--install', kit],
            check=True, capture_output=True, text=True, timeout=10,
            env={**os.environ, 'PATH': str(shell_tools)+':'+os.environ['PATH']},
        )
        self.assertEqual(result.stdout.splitlines(), ['install-kit', str(kit)])

    @unittest.skipUnless(platform.machine() == 'x86_64', 'Installateurs Linux x86-64.')
    def test_extracted_tools_remove_group_write_permissions(self):
        app = self.base / 'application'
        scripts = app / 'scripts'
        scripts.mkdir(parents=True)
        (app / 'deploy').mkdir()
        launcher = scripts / 'installer-outils-linux-hors-ligne.sh'
        shutil.copy2(ROOT / 'scripts' / launcher.name, launcher)
        cache = self.base / 'data/tools/linux-offline-installers'
        cache.mkdir(parents=True)
        (cache / 'python-archive.txt').write_text('python-3.13.tar.gz\n')
        python_stub = b'''#!/bin/sh
case "$1:$2" in
    -m:venv) mkdir -p "$4/bin"; cp /bin/true "$4/bin/python";;
    -c:*) unlink "$3/bin/python"; rmdir "$3/bin" "$3";;
esac
'''
        archives = {
            'docker.tar.gz': ('docker/docker', b'#!/bin/sh\nexit 0\n'),
            'python-3.13.tar.gz': ('python/bin/python3', python_stub),
        }
        for name, (member, blob) in archives.items():
            with tarfile.open(cache / name, 'w:gz') as archive:
                info = tarfile.TarInfo(member)
                info.mode, info.size = 0o777, len(blob)
                archive.addfile(info, io.BytesIO(blob))
        (cache / 'docker-compose').write_bytes(b'#!/bin/sh\nexit 0\n')
        names = (*archives, 'docker-compose')
        (app / 'deploy/linux-offline-installers.txt').write_text(''.join(
            f"{hashlib.sha256((cache / name).read_bytes()).hexdigest()} 0 {name} https://example.invalid\n"
            for name in names))
        shell_tools = self.base / 'shell-tools'
        shell_tools.mkdir()
        (shell_tools / 'nft').symlink_to('/bin/true')
        target = self.base / 'outils'
        result = subprocess.run(['bash', str(launcher), str(self.base / 'data'), str(target)],
                                env={**os.environ, 'PATH': str(shell_tools) + ':' + os.environ['PATH']},
                                capture_output=True, text=True, timeout=20, umask=0o002)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((target / 'python/bin/python3').stat().st_mode & 0o022, 0)
        self.assertTrue((target / '.setupsurvie-restauration').is_file())

        (cache / 'docker.tar.gz').unlink()
        (cache / 'docker-compose').unlink()
        python_only = self.base / 'python seulement'
        result = subprocess.run(['bash', str(launcher), '--python-seul', str(self.base / 'data'),
                                 str(python_only)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((python_only / 'bin/python3').is_file())
        self.assertFalse((python_only / 'bin/docker').exists())

    def test_unit_file_orders_engine_and_escapes_paths(self):
        units = restore.unit_contents(self.base, 'setupsurvie-test')
        app = units['setupsurvie-test.service']
        engine = units['setupsurvie-test-docker.service']
        self.assertIn('Requires=setupsurvie-test-docker.service', app)
        self.assertIn('DOCKER_HOST=unix:///run/setupsurvie-test/docker.sock', app)
        self.assertIn('Copie é 42%%/outils-linux/docker-cli"', app)
        self.assertIn('RequiresMountsFor="' + str(self.base).replace('%', '%%') + '"', engine)
        self.assertIn('--data-root=' + str(self.base).replace('%', '%%') + '/stockage-docker"', engine)

    def test_public_kit_activates_a_dedicated_engine_before_copy_and_restarts_from_local_application(self):
        import linux_public_kit
        kit = self.base.parent/'Kit'
        (kit/'app').mkdir(parents=True)
        with patch.dict(os.environ, {}, clear=True), patch.object(setup, 'ROOT', kit/'app'), \
             patch.object(restore, 'check_service_tree'), patch.object(restore, 'check_engine'), \
             patch.object(restore, 'publish_units') as publish, patch.object(setup, 'run') as run, \
             patch.object(restore, 'bind_controller_to_engine'), patch.object(restore, 'launch_services') as launch, \
             patch('linux_offline_tools.prepare_kit') as verify_tools, patch('pilot_kit.install') as install, \
             patch.object(linux_public_kit, 'prepare_maintenance') as maintenance:
            linux_public_kit.install(kit, self.base)
            name = restore.service_name(self.base, initial=True)
            verify_tools.assert_called_once_with(kit, verify_only=True)
            engine = name + '-docker.service'
            self.assertEqual(list(publish.call_args.args[1]), [engine])
            run.assert_called_once_with(['systemctl', 'start', engine])
            self.assertEqual(os.environ['DOCKER_HOST'], f'unix:///run/{name}/docker.sock')
            self.assertEqual(install.call_args.args, (kit, 'linux', self.base/'data', self.base/'private'))
            self.assertTrue(install.call_args.kwargs['cpu'])
            self.assertTrue(install.call_args.kwargs['graphical'])
            launch.assert_called_once_with(self.base, name, public_kit=True)
            maintenance.assert_called_once_with(kit, self.base, point=True)
            service = restore.unit_contents(self.base, name, public_kit=True)[name+'.service']
            self.assertIn('/application/scripts/linux_public_kit.py', service)
            self.assertNotIn(str(kit), service)
            self.assertNotIn('--kit', service)

    def test_public_kit_maintenance_can_create_point_or_defer_it(self):
        import linux_public_kit
        kit = self.base.parent/'Kit'
        tool_list = [{'path': 'installateurs-linux/tools/linux-offline-installers/docker-compose',
                      'bytes': 4, 'sha256': 'test'}]
        for enabled in (True, False):
            with self.subTest(enabled=enabled), patch('linux_offline_tools.kit_items', return_value=tool_list), \
                 patch('linux_recovery.copy_verified') as copy, patch.object(setup, 'run') as run:
                linux_public_kit.prepare_maintenance(kit, self.base, point=enabled)
                self.assertEqual(copy.call_args.args[2]['path'], 'tools/linux-offline-installers/docker-compose')
                self.assertEqual([call.args[0][-2] for call in run.call_args_list],
                                 ['prepare-maintenance', 'point'] if enabled else ['prepare-maintenance'])

    def test_public_kit_retries_a_protected_point_before_touching_the_active_installation(self):
        import linux_public_kit
        kit = self.base.parent/'Kit'
        (kit/'app').mkdir(parents=True)
        with patch.object(setup, 'ROOT', kit/'app'), patch.object(restore, 'check_service_tree'), \
             patch('linux_offline_tools.prepare_kit'), patch.object(restore, 'check_engine'), \
             patch('pilot_kit.install_job', return_value={'phase': 'complete'}), \
             patch.object(Path, 'is_file', return_value=True), patch('pilot_kit.install') as install, \
             patch.object(linux_public_kit, 'prepare_maintenance') as maintenance, patch.object(setup, 'run') as run:
            linux_public_kit.install(kit, self.base)
        install.assert_not_called()
        maintenance.assert_called_once_with(kit, self.base, point=True)
        run.assert_called_once_with(['systemctl', 'enable', restore.service_name(self.base, initial=True)+'.service'])

    def test_public_kit_copy_failure_stops_only_its_dedicated_engine(self):
        import linux_public_kit
        kit = self.base.parent/'Kit'
        (kit/'app').mkdir(parents=True)
        with patch.dict(os.environ, {}, clear=True), patch.object(setup, 'ROOT', kit/'app'), \
             patch.object(restore, 'check_service_tree'), patch.object(restore, 'check_engine'), \
             patch.object(restore, 'publish_units'), patch.object(setup, 'run') as run, \
             patch.object(restore, 'bind_controller_to_engine'), patch.object(restore, 'launch_services') as launch, \
             patch('linux_offline_tools.prepare_kit'), patch('pilot_kit.install', side_effect=OSError('SSD retiré')):
            with self.assertRaisesRegex(OSError, 'SSD retiré'):
                linux_public_kit.install(kit, self.base)
        engine = restore.service_name(self.base, initial=True) + '-docker.service'
        self.assertEqual([call.args[0] for call in run.call_args_list],
                         [['systemctl', 'start', engine], ['systemctl', 'stop', engine]])
        launch.assert_not_called()

    def test_rejects_local_source_and_relocated_activation(self):
        Path(self.journal['source']['private']).mkdir()
        with self.assertRaisesRegex(setup.SetupError, 'Source détectée'):
            restore.check_transfer(self.base, self.journal)
        Path(self.journal['source']['private']).rmdir()
        self.journal.update(phase='activating', destination='/srv/ailleurs')
        with self.assertRaisesRegex(setup.SetupError, 'autre dossier'):
            restore.check_transfer(self.base, self.journal)

    def test_activation_recovery_skips_preparation(self):
        self.journal.update(phase='activating', destination=str(self.base))
        with patch.object(restore, 'bind_controller_to_engine'), \
                patch.object(transfer, 'read', return_value=self.journal), \
                patch.object(transfer, 'prepare') as prepare, patch.object(transfer, 'activate') as activate:
            restore.start(self.base)
        prepare.assert_not_called()
        activate.assert_called_once_with(self.base)

    def test_dedicated_engine_uses_the_ipv4_bridge_gateway(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(setup, 'run', return_value='fd00::1\n172.29.0.1'):
            restore.bind_controller_to_engine()
            self.assertEqual(os.environ['SURVIE_SYSTEM_DOCKER_GATEWAY'], '172.29.0.1')

    def test_existing_different_unit_is_preserved(self):
        service = self.base / 'setupsurvie.service'
        restore.publish_managed(service, b'original')
        restore.publish_managed(service, b'original')
        with self.assertRaisesRegex(setup.SetupError, 'existant différent'):
            restore.publish_managed(service, b'autre')
        self.assertEqual(service.read_bytes(), b'original')
