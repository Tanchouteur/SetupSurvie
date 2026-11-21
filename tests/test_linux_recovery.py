import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

if sys.platform == 'linux':
    import linux_recovery as recovery
    import setup
    import transfer


@unittest.skipUnless(sys.platform == 'linux', 'Installation système Linux.')
class LinuxRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.source = self.directory / 'SSD externe'
        self.source.mkdir()
        self.state = self.directory / '.SetupSurvie-secours'
        self.state.mkdir()
        self.active = self.directory / 'SetupSurvie'
        self.files = {
            'application/compose.yaml': b'services: {}',
            'application/deploy/release.json': b'{"version":"0.77.0"}',
            'application/scripts/restaurer-linux-hors-ligne.sh': b'#!/bin/sh\n',
            'private/settings.json': b'{"target":"linux","cpu":false}',
            'data/guide.txt': b'Contenu du point de restauration',
        }
        records = []
        for name, content in self.files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o755 if name.endswith('.sh') else 0o640)
            info = path.stat()
            records.append({'path': name, 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns,
                            'mode': info.st_mode & 0o777})
        archives = {'images.tar': b'images', 'images.tar.json': b'{}'}
        for name, content in archives.items():
            (self.source / name).write_bytes(content)
        def digest(data):
            return hashlib.sha256(data).hexdigest()
        self.journal = {
            'kind': transfer.KIND, 'schema': 1, 'target': 'linux', 'phase': 'copied', 'id': 'copy-id',
            'release': {'version': '0.77.0'},
            'source': {'private': '/srv/source/private', 'application': '/srv/source/application',
                       'data': '/srv/source/data'},
            'destination': str(self.source),
            'inventory': {'files': records, 'directories': [], 'ollama_links': {}, 'directory_modes': {}},
            'verified': {name: digest(content) for name, content in self.files.items()},
            'images_sha256': digest(archives['images.tar']),
            'images_manifest_sha256': digest(archives['images.tar.json']),
        }
        transfer.save(self.source, self.journal)

    def test_default_creates_point_and_activates_only_working_copy(self):
        with patch.object(recovery, 'check_sealing'), patch.object(recovery, 'seal'), \
                patch.object(recovery, 'protected_tree'), patch.object(recovery, 'activate') as activate, \
                patch.object(recovery, 'install_shortcut'):
            recovery.install(self.state, self.source, self.active, True)
            recovery.install(self.state, self.source, self.active, True)
        point = self.state / 'point'
        self.assertTrue((point / 'point-de-restauration.json').is_file())
        recovery.require_ready(self.state, point)
        self.assertEqual((point / 'data/guide.txt').read_bytes(), self.files['data/guide.txt'])
        self.assertNotEqual((point / 'data/guide.txt').stat().st_ino, (self.active / 'data/guide.txt').stat().st_ino)
        self.assertEqual([call.args for call in activate.call_args_list], [(self.active,), (self.active,)])

    def test_opt_out_only_copies_to_active(self):
        with patch.object(recovery, 'activate'), patch.object(recovery, 'install_shortcut'):
            recovery.install(self.state, self.source, self.active, False)
        self.assertFalse((self.state / 'point').exists())
        self.assertEqual((self.active / 'data/guide.txt').read_bytes(), self.files['data/guide.txt'])

    def test_prepare_uses_cpu_on_the_portable_working_copy(self):
        recovery.fill_target(self.source, self.active, self.journal, portable_cpu=True)
        transfer.prepare(self.active)
        self.assertTrue(transfer.read(self.active / 'private/settings.json')['cpu'])
        self.assertFalse(transfer.read(self.source / 'private/settings.json')['cpu'])

    def test_changed_support_is_refused_before_activation(self):
        (self.source / 'data/guide.txt').write_bytes(b'X' * len(self.files['data/guide.txt']))
        with patch.object(recovery, 'activate') as activate, patch.object(recovery, 'install_shortcut'):
            with self.assertRaisesRegex(setup.SetupError, 'altéré'):
                recovery.install(self.state, self.source, self.active, False)
        activate.assert_not_called()

    def test_restoration_preserves_old_data_and_resumes_after_failed_activation(self):
        point = self.state / 'point'
        recovery.fill_target(self.source, point, self.journal)
        with patch.object(recovery, 'seal'):
            recovery.seal_point(point, self.journal)
        with self.assertRaisesRegex(setup.SetupError, 'création du point'):
            recovery.require_ready(self.state, point)
        recovery.mark_ready(self.state, point)
        self.active.mkdir()
        (self.active / 'plus-recent').write_text('à conserver')
        activated = []
        def activate(base):
            if not activated:
                activated.append(base)
                raise setup.SetupError('arrêt injecté')
            self.assertEqual(base, self.active)
        def systemctl(command):
            if command[0] == 'mv':
                command[-2].rename(command[-1])
        with patch.object(recovery, 'protected_tree'), patch.object(recovery, 'managed_unit', return_value='dedicated'), \
                patch.object(recovery.setup, 'run', side_effect=systemctl) as service, \
                patch.object(recovery.subprocess, 'run', return_value=SimpleNamespace(returncode=3)), \
                patch.object(recovery, 'activate', side_effect=activate):
            with self.assertRaisesRegex(setup.SetupError, 'arrêt injecté'):
                recovery.restore(self.state, self.active)
            recovery.restore(self.state, self.active)
        (saved,) = self.state.glob('ancienne-installation-*')
        self.assertEqual((saved / 'plus-recent').read_text(), 'à conserver')
        self.assertFalse((self.state / 'remplacement.json').exists())
        self.assertEqual(transfer.read(point / 'transfer.json'), self.journal)
        self.assertNotEqual(transfer.read(self.active / 'transfer.json')['source'], self.journal['source'])
        self.assertEqual(sum(call.args[0][1] == 'disable' for call in service.call_args_list), 1)

    def test_copy_restarts_from_a_verified_partial(self):
        partial = self.active / 'data/guide.txt.transfer-part'
        partial.parent.mkdir(parents=True)
        partial.write_bytes(self.files['data/guide.txt'][:10])
        journal = recovery.transfer_manifest(self.source)
        recovery.copy_payload(self.source, self.active, journal)
        self.assertEqual((self.active / 'data/guide.txt').read_bytes(), self.files['data/guide.txt'])
        self.assertFalse(partial.exists())

    def test_existing_point_releases_only_its_transfer_guard(self):
        work = self.active / 'private'
        work.mkdir(parents=True)
        point = self.state / 'point'
        point.mkdir()
        transfer.save(point, self.journal)
        guard = work / 'transfer-guard.json'
        setup.write_json(guard, {'id': 'other'})
        with patch.object(recovery.setup, 'run') as service:
            with self.assertRaisesRegex(setup.SetupError, 'différent'):
                recovery.release_current_source(self.active, point, 'dedicated')
            service.assert_not_called()
            setup.write_json(guard, {'id': self.journal['id']})
            recovery.release_current_source(self.active, point, 'dedicated')
        self.assertFalse(guard.exists())
        service.assert_called_once_with(['systemctl', 'start', 'dedicated.service'])

    def test_bundle_launchers_public_and_data_private(self):
        scripts = self.source / 'application/scripts'
        for name in ('installer-depuis-le-ssd.desktop', 'linux_recovery_gui.sh', 'linux_recovery_admin.sh'):
            (scripts / name).write_bytes((ROOT / 'scripts' / name).read_bytes())
        transfer.publish_linux_installer(self.source, self.journal)
        launcher = self.source / 'Installer-SetupSurvie.desktop'
        self.assertIn(' install ', launcher.read_text())
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
        self.assertIn(' maintenance-select ', (self.source / 'Entretien-SetupSurvie.desktop').read_text())
        for name in ('application', 'data', 'images.tar', 'private', 'transfer.json'):
            self.assertEqual((self.source / name).stat().st_mode & 0o077, 0)


    def test_graphical_install_passes_opt_out_and_finishes_progress(self):
        scripts = self.directory / 'interface'
        scripts.mkdir()
        (scripts / 'linux_recovery_gui.sh').write_bytes((ROOT / 'scripts/linux_recovery_gui.sh').read_bytes())
        (scripts / 'linux_recovery_admin.sh').touch()
        (scripts / 'zenity').write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '--file-selection) printf "/srv/Disque SSD\\n";;\n'
            '--list) if [ "$2" = --radiolist ]; then printf "autre\\n"; fi;;\n'
            '--progress) cat >"$RESULT.progress";;\n'
            '--question) exit 1;;\n'
            'esac\n')
        (scripts / 'pkexec').write_text(
            '#!/bin/sh\nprintf "%s\\n" "$@" >"$RESULT.args"\n'
            'printf "Préparation de la copie de travail…\\n"\n')
        for name in ('zenity', 'pkexec'):
            (scripts / name).chmod(0o755)
        result = self.directory / 'test'
        subprocess.run(['bash', scripts / 'linux_recovery_gui.sh', 'install', self.source],
                       check=True, timeout=10, env={**os.environ,
                           'RESULT': str(result), 'PATH': f'{scripts}:{os.environ["PATH"]}'})
        self.assertEqual(result.with_suffix('.args').read_text().splitlines()[-4:],
                         ['install', str(self.source), '/srv/Disque SSD/SetupSurvie', 'no'])
        self.assertEqual(result.with_suffix('.progress').read_text().splitlines(),
                         ['# Préparation de la copie de travail…', '100'])
