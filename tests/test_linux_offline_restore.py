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

    def test_unit_file_orders_engine_and_escapes_paths(self):
        units = restore.unit_contents(self.base, 'setupsurvie-test')
        app = units['setupsurvie-test.service']
        engine = units['setupsurvie-test-docker.service']
        self.assertIn('Requires=setupsurvie-test-docker.service', app)
        self.assertIn('DOCKER_HOST=unix:///run/setupsurvie-test/docker.sock', app)
        self.assertIn('Copie é 42%%/outils-linux/docker-cli"', app)
        self.assertIn('RequiresMountsFor="' + str(self.base).replace('%', '%%') + '"', engine)
        self.assertIn('--data-root=' + str(self.base).replace('%', '%%') + '/stockage-docker"', engine)

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
        with patch.object(transfer, 'read', return_value=self.journal), \
                patch.object(transfer, 'prepare') as prepare, patch.object(transfer, 'activate') as activate:
            restore.start(self.base)
        prepare.assert_not_called()
        activate.assert_called_once_with(self.base)

    def test_existing_different_unit_is_preserved(self):
        service = self.base / 'setupsurvie.service'
        restore.publish_managed(service, b'original')
        restore.publish_managed(service, b'original')
        with self.assertRaisesRegex(setup.SetupError, 'existant différent'):
            restore.publish_managed(service, b'autre')
        self.assertEqual(service.read_bytes(), b'original')
