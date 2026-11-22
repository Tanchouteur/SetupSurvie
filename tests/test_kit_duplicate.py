import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import kit_duplicate
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
