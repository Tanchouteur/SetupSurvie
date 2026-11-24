import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import kit_duplicate
import linux_offline_tools
from pilot_kit import checked_entries
import setup
import transfer
import windows_kit_installers


class KitDuplicateTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.source = self.base / 'SSD initial'
        self.target = self.base / 'Deuxième SSD'
        self.source.mkdir()
        self.manifest = {'schema': 1, 'kind': 'SetupSurvie public pilot kit', 'files': []}
        self.add_file('app/Installer-SetupSurvie.cmd', b'fixture')
        self.add_file('payload/library/guides/exemple.txt', b'Guide hors ligne')
        self.enterContext(patch('kit_duplicate.kit_audit.validate'))

    def add_file(self, relative, body, add_to_manifest=True):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        record = {'path': relative, 'bytes': len(body), 'sha256': setup.file_hash(path)}
        if add_to_manifest:
            self.manifest['files'].append(record)
        return record

    def publish_manifest(self):
        setup.write_json(self.source / 'manifest.json', self.manifest)

    def test_resume_on_moved_support_and_duplicate_the_new_copy(self):
        self.publish_manifest()
        self.add_file('private/settings.json', b'fixture prive', add_to_manifest=False)
        copy_file = transfer.copy_file

        def interrupted(origin, target, entry, progress, **options):
            if target.name == 'exemple.txt':
                target.parent.mkdir(parents=True)
                target.with_name(target.name + '.transfer-part').write_bytes(origin.read_bytes()[:5])
                raise OSError('support débranché')
            return copy_file(origin, target, entry, progress, **options)

        with patch.object(transfer, 'copy_file', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'support débranché'):
                kit_duplicate.duplicate(self.source, self.target)
        self.assertTrue((self.target / kit_duplicate.MARKER).is_file())
        self.assertFalse((self.target / 'manifest.json').exists())
        moved = self.base / 'Support remonté'
        self.source.rename(moved)
        kit_duplicate.duplicate(moved, self.target)
        checked_entries(self.target, self.manifest)
        self.assertFalse((self.target / 'private').exists())
        self.assertFalse((self.target / kit_duplicate.MARKER).exists())
        third = self.base / 'Troisième SSD'
        kit_duplicate.duplicate(self.target, third)
        checked_entries(third, self.manifest)

    @unittest.skipUnless(sys.platform == 'linux', 'Lanceur de bureau Linux.')
    def test_linux_launcher_uses_its_own_kit_without_shell_prompt(self):
        self.publish_manifest()
        driver = self.base / 'python3'
        driver.write_text(
            '#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\nprintf "%s\\n" "$@"\n',
            encoding='utf-8',
        )
        driver.chmod(0o755)
        result = subprocess.run(
            ['/bin/sh', ROOT / 'scripts/dupliquer-kit-linux.sh', self.source / 'app' / '..'],
            env={**os.environ, 'PATH': str(self.base) + ':' + os.environ['PATH']},
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [str(self.source / 'app/scripts/kit_duplicate_gui.py'), str(self.source)],
        )

    @unittest.skipUnless(sys.platform == 'linux', 'Lanceur de bureau Linux.')
    def test_linux_launcher_uses_bundled_python_without_administrator(self):
        self.publish_manifest()
        tools = self.source/'installateurs-linux/tools/linux-offline-installers'
        tools.mkdir(parents=True)
        (tools/'python-archive.txt').touch()
        scripts = self.source/'app/scripts'
        scripts.mkdir()
        trace = self.base/'trace'
        temp = self.base/'temp'
        temp.mkdir()
        driver = self.base/'python3'
        driver.write_text('#!/bin/sh\nexit 127\n', encoding='utf-8')
        driver.chmod(0o755)
        zenity = self.base/'zenity'
        zenity.write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '--file-selection) printf "%s\\n" "$DISK";;\n'
            '--progress) cat >/dev/null;;\n'
            '--info) printf "verified\\n" >> "$TRACE";;\n'
            '--text-info) exit 1;;\nesac\n',
            encoding='utf-8',
        )
        zenity.chmod(0o755)
        bootstrap = scripts/'installer-outils-linux-hors-ligne.sh'
        bootstrap.write_text(
            'set -e\n[ "$1" = --python-seul ]\n[ "$2" = "$KIT/installateurs-linux" ]\n'
            'mkdir -p "$3/bin"\ncat >"$3/bin/python3" <<\'PYTHON\'\n'
            '#!/bin/sh\nprintf "%s\\n" "$@" >> "$TRACE"\nPYTHON\n'
            'chmod +x "$3/bin/python3"\n',
            encoding='utf-8',
        )
        result = subprocess.run(
            ['/bin/sh', ROOT/'scripts/dupliquer-kit-linux.sh', self.source],
            env={**os.environ, 'PATH': str(self.base)+':'+os.environ['PATH'],
                 'DISK': str(self.target), 'KIT': str(self.source),
                 'TMPDIR': str(temp), 'TRACE': str(trace)},
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
        )
        self.assertEqual(trace.read_text().splitlines(), [
            str(scripts/'pilot_kit.py'), 'duplicate', str(self.source),
            str(self.target/'SetupSurvie-Kit'), 'verified',
        ])
        self.assertEqual(list(temp.iterdir()), [])
        self.assertEqual(result.stderr, '')

    @unittest.skipUnless(sys.platform == 'linux', 'Lanceur de bureau Linux.')
    def test_linux_verify_launcher_also_checks_a_chosen_personal_backup(self):
        self.publish_manifest()
        tools = self.source/'installateurs-linux/tools/linux-offline-installers'
        tools.mkdir(parents=True)
        (tools/'python-archive.txt').touch()
        scripts = self.source/'app/scripts'
        scripts.mkdir()
        trace, temp, backup = self.base/'trace', self.base/'temp', self.base/'Sauvegarde 2026'
        temp.mkdir()
        driver = self.base/'python3'
        driver.write_text('#!/bin/sh\nexit 127\n', encoding='utf-8')
        driver.chmod(0o755)
        zenity = self.base/'zenity'
        zenity.write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '--question) printf "question\\n" >> "$TRACE";;\n'
            '--file-selection) printf "%s\\n" "$DISK";;\n'
            '--progress) cat >/dev/null;;\n'
            '--text-info) printf "resultat\\n" >> "$TRACE";;\n'
            '*) exit 1;;\nesac\n',
            encoding='utf-8',
        )
        zenity.chmod(0o755)
        (scripts/'installer-outils-linux-hors-ligne.sh').write_text(
            'set -e\nmkdir -p "$3/bin"\ncat >"$3/bin/python3" <<\'PYTHON\'\n'
            '#!/bin/sh\nprintf "%s\\n" "$@" >> "$TRACE"\nPYTHON\n'
            'chmod +x "$3/bin/python3"\n',
            encoding='utf-8',
        )
        subprocess.run(
            ['/bin/sh', ROOT/'scripts/dupliquer-kit-linux.sh', self.source, '--verify'],
            env={**os.environ, 'PATH': str(self.base)+':'+os.environ['PATH'],
                 'DISK': str(backup), 'TMPDIR': str(temp), 'TRACE': str(trace)},
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
        )
        self.assertEqual(trace.read_text().splitlines(), [
            'question', str(scripts/'pilot_kit.py'), 'verify-support', str(self.source),
            str(scripts/'pilot_backup.py'), 'verify', str(backup), '--kit', str(self.source), 'resultat',
        ])
        self.assertEqual(list(temp.iterdir()), [])

    def test_windows_installers_and_components_are_retained(self):
        packages = {}
        for name in sorted(windows_kit_installers.COMPONENTS):
            file = name + ('.msi' if name == 'wsl' else '.exe')
            record = self.add_file(f'installateurs-windows/{file}', name.encode(), add_to_manifest=False)
            packages[name] = {**record, 'file': file, 'id': name, 'url': f'https://example.invalid/{file}'}
        catalog = {'schema': 1, 'wsl': packages.pop('wsl'), 'installers': list(packages.values())}
        self.add_file(windows_kit_installers.CATALOG, json.dumps(catalog).encode())
        self.add_file('installateurs-windows/sxs/platform.cab', b'composant fixture', add_to_manifest=False)
        self.publish_manifest()
        kit_duplicate.duplicate(self.source, self.target)
        windows_kit_installers.prepare(self.target, verify_only=True)
        self.assertEqual((self.target / 'installateurs-windows/sxs/platform.cab').read_bytes(), b'composant fixture')
        self.assertEqual((self.target / 'manifest.json').read_bytes(), (self.source / 'manifest.json').read_bytes())

    def test_linux_tool_bundle_is_verified_and_duplicated_without_network(self):
        names = ['docker.tar.gz', 'docker-compose', linux_offline_tools.KIT_PYTHON]
        names += [prefix + 'nftables_test.deb' for prefix in ('', 'debian12/', 'ubuntu2204/')]
        entries = []
        folder = linux_offline_tools.KIT_FOLDER
        for name in names:
            record = self.add_file(f'{folder}/{linux_offline_tools.FOLDER}/{name}', name.encode(),
                                   add_to_manifest=False)
            entries.append(f"{record['sha256']} {record['bytes']} {name} https://example.invalid/tools")
        self.add_file(linux_offline_tools.CATALOG, '\n'.join(entries).encode())
        self.publish_manifest()
        with self.assertRaisesRegex(setup.SetupError, 'préparation des installateurs Linux'):
            kit_duplicate.duplicate(self.source, self.target)
        receipt = f'{folder}/{linux_offline_tools.RECEIPT}'
        self.add_file(receipt, (linux_offline_tools.KIT_PYTHON+'\n').encode(), add_to_manifest=False)
        with patch('linux_offline_tools.content.transfer', side_effect=AssertionError('Réseau interdit')):
            kit_duplicate.duplicate(self.source, self.target)
            linux_offline_tools.prepare_kit(self.target, verify_only=True)
            report = kit_duplicate.verify_support(self.target, report=lambda _line: None)
        self.assertIn('Linux : les installateurs présents sur le SSD sont vérifiés.', report)
        self.assertEqual((self.target/receipt).read_bytes(), (self.source/receipt).read_bytes())
        docker = self.target/folder/linux_offline_tools.FOLDER/'docker-compose'
        docker.write_bytes(b'x'*docker.stat().st_size)
        with self.assertRaisesRegex(setup.SetupError, 'absent ou modifié'):
            linux_offline_tools.prepare_kit(self.target, verify_only=True)

    def test_verify_support_reports_missing_tools_without_writing_and_rejects_damage(self):
        self.publish_manifest()
        files = {path.relative_to(self.source): path.read_bytes()
                 for path in self.source.rglob('*') if path.is_file()}
        with patch('content.transfer', side_effect=AssertionError('Réseau interdit')):
            report = kit_duplicate.verify_support(self.source, report=lambda _line: None)
        self.assertIn('Windows : aucun installateur embarqué', report)
        self.assertIn('Linux : aucun installateur embarqué', report)
        self.assertEqual({path.relative_to(self.source): path.read_bytes()
                          for path in self.source.rglob('*') if path.is_file()}, files)
        path = self.source/'payload/library/guides/exemple.txt'
        path.write_bytes(b'x'*path.stat().st_size)
        with self.assertRaisesRegex(setup.SetupError, 'Kit incomplet ou modifié'):
            kit_duplicate.verify_support(self.source, report=lambda _line: None)

    def test_same_size_altered_source_never_publishes_the_file_or_the_kit(self):
        self.publish_manifest()
        path = 'payload/library/guides/exemple.txt'
        (self.source / path).write_bytes(b'x' * (self.source / path).stat().st_size)
        with self.assertRaisesRegex(setup.SetupError, 'empreinte'):
            kit_duplicate.duplicate(self.source, self.target)
        self.assertFalse((self.target / path).exists())
        self.assertFalse((self.target / 'manifest.json').exists())

    def test_existing_destination_and_private_transfer_are_refused(self):
        self.publish_manifest()
        self.target.mkdir()
        unrelated = self.target / 'document.txt'
        unrelated.write_text('document existant')
        with self.assertRaisesRegex(setup.SetupError, 'déjà utilisé'):
            kit_duplicate.duplicate(self.source, self.target)
        self.assertEqual(unrelated.read_text(), 'document existant')
        self.manifest['kind'] = 'private transfer'
        self.publish_manifest()
        with self.assertRaisesRegex(setup.SetupError, 'kit public'):
            kit_duplicate.duplicate(self.source, self.base / 'Autre SSD')
