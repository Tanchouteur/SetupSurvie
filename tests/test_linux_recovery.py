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

    def test_group_writable_application_directory_is_protected_on_copy_and_resume(self):
        self.journal['inventory']['directories'].append('application/deploy')
        self.journal['inventory']['directory_modes']['application/deploy'] = 0o775
        recovery.fill_target(self.source, self.active, self.journal)
        directory = self.active / 'application/deploy'
        self.assertEqual(directory.stat().st_mode & 0o777, 0o755)
        directory.chmod(0o775)
        recovery.fill_target(self.source, self.active, self.journal)
        self.assertEqual(directory.stat().st_mode & 0o777, 0o755)

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

    def test_nested_activation_does_not_inherit_maintenance_tools(self):
        recovery.fill_target(self.source, self.active, self.journal)
        with patch.dict(os.environ, {'PATH': '/maintenance/outils-linux/bin'}), \
                patch.object(recovery.setup, 'run') as run, \
                patch.object(recovery.setup.Installation, 'request'):
            recovery.activate(self.active)
        self.assertNotIn('/maintenance/', run.call_args_list[0].kwargs['env']['PATH'])
        self.assertEqual(run.call_args_list[0].args[0][0], '/bin/bash')

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

    def test_duplicate_can_resume_after_remount_and_exports_a_ready_second_disk(self):
        self.add_graphical_launchers()
        manifest = self.source / 'transfer.json'
        original_manifest = manifest.read_bytes()
        real_copy = recovery.copy_payload

        def interrupted(source, target, journal):
            partial = target / 'data/guide.txt.transfer-part'
            partial.parent.mkdir()
            partial.write_bytes(self.files['data/guide.txt'][:10])
            raise OSError('câble débranché')

        with patch.object(recovery, 'copy_payload', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'câble débranché'):
                recovery.duplicate(self.source, self.active)
        self.assertFalse((self.active / 'Installer-SetupSurvie.desktop').exists())
        self.assertEqual(manifest.read_bytes(), original_manifest)

        moved = self.directory / 'SSD remonté'
        self.source.rename(moved)
        with patch.object(recovery, 'copy_payload', wraps=real_copy) as payload:
            recovery.duplicate(moved, self.active)
            recovery.duplicate(moved, self.active)
        payload.assert_called_once()
        self.assertEqual((self.active / 'transfer.json').read_bytes(), original_manifest)
        self.assertIn(' duplicate ', (self.active / 'Dupliquer-SetupSurvie.desktop').read_text())
        self.assertTrue((self.active / 'Installer-SetupSurvie.desktop').is_file())
        self.assertFalse((self.active / 'data/guide.txt.transfer-part').exists())
        self.assertEqual((self.active / 'private').stat().st_mode & 0o077, 0)
        self.assertEqual((moved / 'transfer.json').read_bytes(), original_manifest)

    def test_duplicate_does_not_publish_a_corrupt_or_unrelated_destination(self):
        self.active.mkdir()
        (self.active / 'document').write_text('à conserver')
        with self.assertRaisesRegex(setup.SetupError, 'Dossier déjà utilisé'):
            recovery.duplicate(self.source, self.active)
        self.assertEqual((self.active / 'document').read_text(), 'à conserver')
        target = self.directory / 'Disque de test'
        (self.source / 'data/guide.txt').write_bytes(b'X' * len(self.files['data/guide.txt']))
        with self.assertRaisesRegex(setup.SetupError, 'altéré'):
            recovery.duplicate(self.source, target)
        self.assertFalse((target / 'Installer-SetupSurvie.desktop').exists())
        self.assertFalse((target / 'transfer.json').exists())

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

    def interrupted_local_point(self, phase='copying'):
        point = self.state / 'point'
        point.mkdir()
        work = self.active / 'private'
        work.mkdir(parents=True)
        copy_id = 'a12b' * 8
        journal = {**self.journal, 'phase': phase, 'id': copy_id, 'destination': str(point),
                   'source': {role: str(self.active / role) for role in ('application', 'data', 'private')}}
        transfer.save(point, journal)
        guard = work / 'transfer-guard.json'
        setup.write_json(guard, {'id': copy_id, 'destination': str(point)})
        return point, guard, self.state / ('point-interrompu-' + copy_id)

    def test_cancel_after_interruption_between_archive_and_guard_removal(self):
        point, guard, archived = self.interrupted_local_point()
        partial = point / 'guide.transfer-part'
        partial.write_text('données partielles')
        user_file = self.active / 'mes-guides'
        user_file.write_text('document actuel')
        sync = recovery.durable.sync_directory

        def cut_after_rename(directory):
            if directory == self.state and archived.is_dir():
                raise OSError('coupure après publication')
            sync(directory)

        with (
            patch.object(recovery, 'managed_unit', return_value='dedicated'),
            patch.object(recovery.setup, 'run') as service,
            patch.object(recovery.setup.Installation, 'request') as health,
        ):
            with patch.object(recovery.durable, 'sync_directory', side_effect=cut_after_rename):
                with self.assertRaisesRegex(OSError, 'coupure après publication'):
                    recovery.cancel_point(self.state, self.active)
            service.assert_not_called()
            self.assertTrue(guard.is_file())
            self.assertTrue(archived.is_dir())
            recovery.cancel_point(self.state, self.active)
        self.assertFalse(guard.exists())
        self.assertFalse(point.exists())
        self.assertEqual((archived / partial.name).read_text(), 'données partielles')
        self.assertEqual(user_file.read_text(), 'document actuel')
        service.assert_called_once_with(['systemctl', 'start', 'dedicated.service'])
        health.assert_called_once_with('http://127.0.0.1:8080/api/health')

    def test_cancel_preserves_a_complete_point(self):
        point, guard, archived = self.interrupted_local_point('copied')
        before = (point / 'transfer.json').read_bytes()
        with (
            patch.object(recovery, 'managed_unit', return_value='dedicated'),
            patch.object(recovery.setup, 'run'),
            patch.object(recovery.setup.Installation, 'request'),
        ):
            recovery.cancel_point(self.state, self.active)
        self.assertFalse(guard.exists())
        self.assertFalse(archived.exists())
        self.assertEqual((point / 'transfer.json').read_bytes(), before)

    def test_cancel_refuses_guard_for_a_different_transfer(self):
        point, guard, archived = self.interrupted_local_point()
        setup.write_json(guard, {'id': 'a12b' * 8, 'destination': '/disque/externe'})
        with (
            patch.object(recovery, 'managed_unit', return_value='dedicated'),
            patch.object(recovery.setup, 'run') as service,
        ):
            with self.assertRaisesRegex(setup.SetupError, 'Un autre transfert'):
                recovery.cancel_point(self.state, self.active)
        self.assertTrue(guard.exists())
        self.assertTrue(point.is_dir())
        self.assertFalse(archived.exists())
        service.assert_not_called()

    def test_cancel_refuses_when_a_restoration_is_in_progress(self):
        (self.state / 'remplacement.json').write_text('{}')
        with patch.object(recovery, 'managed_unit') as unit:
            with self.assertRaisesRegex(setup.SetupError, 'restauration en cours'):
                recovery.cancel_point(self.state, self.active)
        unit.assert_not_called()

    def test_cancel_moves_empty_point_left_before_journal_publication(self):
        point = self.state / 'point'
        point.mkdir()
        self.active.mkdir()
        with (
            patch.object(recovery, 'managed_unit', return_value='dedicated'),
            patch.object(recovery.setup, 'run'),
            patch.object(recovery.setup.Installation, 'request'),
        ):
            recovery.cancel_point(self.state, self.active)
        self.assertFalse(point.exists())
        self.assertEqual(len(list(self.state.glob('point-interrompu-*'))), 1)

    def test_cancel_can_restart_when_unfenced_point_has_an_unreadable_journal(self):
        point, guard, _ = self.interrupted_local_point()
        guard.unlink()
        (point / 'transfer.json').write_text('copie endommagée')
        with (
            patch.object(recovery, 'managed_unit', return_value='dedicated'),
            patch.object(recovery.setup, 'run') as service,
            patch.object(recovery.setup.Installation, 'request'),
        ):
            recovery.cancel_point(self.state, self.active)
        self.assertEqual((point / 'transfer.json').read_text(), 'copie endommagée')
        service.assert_called_once_with(['systemctl', 'start', 'dedicated.service'])

    def add_graphical_launchers(self):
        scripts = self.source / 'application/scripts'
        for name in ('installer-depuis-le-ssd.desktop', 'linux_recovery_gui.sh', 'linux_recovery_admin.sh'):
            path = scripts / name
            path.write_bytes((ROOT / 'scripts' / name).read_bytes())
            record = {'path': 'application/scripts/' + name, 'bytes': path.stat().st_size,
                      'mtime_ns': path.stat().st_mtime_ns, 'mode': 0o755}
            self.journal['inventory']['files'].append(record)
            self.journal['verified'][record['path']] = setup.file_hash(path)
        transfer.save(self.source, self.journal)

    def test_bundle_launchers_public_and_data_private(self):
        self.add_graphical_launchers()
        transfer.publish_linux_installer(self.source, self.journal)
        launcher = self.source / 'Installer-SetupSurvie.desktop'
        self.assertIn(' install ', launcher.read_text())
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
        self.assertIn(' maintenance-select ', (self.source / 'Entretien-SetupSurvie.desktop').read_text())
        for name in ('application', 'data', 'images.tar', 'private', 'transfer.json'):
            self.assertEqual((self.source / name).stat().st_mode & 0o077, 0)


    def test_graphical_install_and_duplication_pass_options_and_finish_progress(self):
        scripts = self.directory / 'interface'
        scripts.mkdir()
        (scripts / 'linux_recovery_gui.sh').write_bytes((ROOT / 'scripts/linux_recovery_gui.sh').read_bytes())
        (scripts / 'linux_recovery_admin.sh').touch()
        (scripts / 'zenity').write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '--file-selection) printf "/srv/Disque SSD\\n";;\n'
            '--list) case "$*" in *--title="Entretien de SetupSurvie"*) printf "cancel-point\\n";; '
            '*--radiolist*) printf "autre\\n";; esac;;\n'
            '--progress) cat >"$RESULT.progress";;\n'
            '--question) case "$*" in *--ok-label=Dupliquer*|*--ok-label=Installer*|*--ok-label="Redémarrer SetupSurvie"*) exit 0;; '
            '*) exit 1;; esac;;\n'
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
        arguments = result.with_suffix('.args').read_text().splitlines()
        self.assertEqual(arguments[0], '--disable-internal-agent')
        self.assertEqual(arguments[-4:],
                         ['install', str(self.source), '/srv/Disque SSD/SetupSurvie', 'no'])
        self.assertEqual(result.with_suffix('.progress').read_text().splitlines(),
                         ['# Préparation de la copie de travail…', '100'])

        subprocess.run(['bash', scripts / 'linux_recovery_gui.sh', 'install-kit', self.source],
                       check=True, timeout=10, env={**os.environ,
                           'RESULT': str(result), 'PATH': f'{scripts}:{os.environ["PATH"]}'})
        arguments = result.with_suffix('.args').read_text().splitlines()
        self.assertEqual(arguments[-3:-1], ['install-kit', str(self.source)])
        self.assertTrue(arguments[-1].startswith('/srv/Disque SSD/SetupSurvie-Kit-'))

        subprocess.run(['bash', scripts / 'linux_recovery_gui.sh', 'duplicate', self.source],
                       check=True, timeout=10, env={**os.environ,
                           'RESULT': str(result), 'PATH': f'{scripts}:{os.environ["PATH"]}'})
        arguments = result.with_suffix('.args').read_text().splitlines()
        self.assertEqual(arguments[-3:], ['duplicate', str(self.source),
                                          '/srv/Disque SSD/SetupSurvie-Secours'])

        subprocess.run(['bash', scripts / 'linux_recovery_gui.sh', 'maintenance', self.active],
                       check=True, timeout=10, env={**os.environ,
                           'RESULT': str(result), 'PATH': f'{scripts}:{os.environ["PATH"]}'})
        arguments = result.with_suffix('.args').read_text().splitlines()
        self.assertEqual(arguments[-2:], ['cancel-point', str(self.active)])
