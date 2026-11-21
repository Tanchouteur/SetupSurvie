import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import setup
import windows_kit_installers as installers


class WindowsKitInstallerTests(unittest.TestCase):
    def setUp(self):
        fixture = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(fixture).resolve()
        self.catalog = self.root / installers.CATALOG
        self.catalog.parent.mkdir(parents=True)
        self.payloads = {}
        entries = {}
        for name in sorted(installers.COMPONENTS):
            file = name + ('.msi' if name == 'wsl' else '.exe')
            data = self.payloads[file] = (name + '-fixture').encode()
            entries[name] = {'id': name, 'file': file, 'url': 'https://example.invalid/' + file,
                             'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        self.recorded = {'schema': 1, 'wsl': entries.pop('wsl'), 'installers': list(entries.values())}
        self.publish_catalog()

    def publish_catalog(self):
        self.catalog.write_text(json.dumps(self.recorded), encoding='utf-8')
        setup.write_json(self.root / 'manifest.json', {
            'schema': 1, 'kind': 'SetupSurvie public pilot kit',
            'files': [{'path': installers.CATALOG, 'bytes': self.catalog.stat().st_size,
                       'sha256': setup.file_hash(self.catalog)}],
        })

    def test_prepare_resumes_partial_and_verify_uses_no_network(self):
        folder = self.root / installers.FOLDER
        folder.mkdir()
        partial = folder / 'wsl.msi.part'
        partial.write_bytes(self.payloads['wsl.msi'][:4])
        calls = []

        def respond(request, timeout):
            url = request.full_url
            data = self.payloads[url.rsplit('/', 1)[-1]]
            offset = int(request.get_header('Range').removeprefix('bytes=').removesuffix('-'))
            calls.append((url, offset))
            body = io.BytesIO(data[offset:])
            body.geturl = lambda: url
            body.status = 206
            body.headers = {'Content-Range': f'bytes {offset}-{len(data) - 1}/{len(data)}'}
            return body

        with patch('content_mirrors.network_open', side_effect=respond):
            installers.prepare(self.root)
        self.assertEqual(len(calls), 5)
        self.assertIn(('https://example.invalid/wsl.msi', 4), calls)
        self.assertFalse(partial.exists())
        for name, data in self.payloads.items():
            self.assertEqual((folder / name).read_bytes(), data)
        with patch('content.transfer') as transfer:
            installers.prepare(self.root, verify_only=True)
            transfer.assert_not_called()
        completed = subprocess.run([sys.executable, ROOT / 'scripts/pilot_kit.py', 'prepare-windows',
                                    self.root, '--verify-only'], capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_rejects_corrupt_installers_and_catalog_without_writing(self):
        folder = self.root / installers.FOLDER
        folder.mkdir()
        (folder / 'wsl.msi').write_bytes(b'incorrect')
        with self.assertRaisesRegex(setup.SetupError, r'absent ou modifié : wsl\.msi'):
            installers.prepare(self.root, verify_only=True)
        self.catalog.write_text('{}', encoding='utf-8')
        with patch('content.transfer') as transfer:
            with self.assertRaisesRegex(setup.SetupError, 'Kit incomplet ou modifié'):
                installers.prepare(self.root)
            transfer.assert_not_called()
        self.assertEqual((folder / 'wsl.msi').read_bytes(), b'incorrect')

    def test_rejects_a_catalog_with_missing_or_escaping_installers(self):
        self.recorded['wsl']['file'] = '../hors-du-kit.msi'
        self.publish_catalog()
        with self.assertRaisesRegex(setup.SetupError, 'Nom d’installateur'):
            installers.prepare(self.root, verify_only=True)
        self.recorded['installers'].pop()
        self.publish_catalog()
        with self.assertRaisesRegex(setup.SetupError, 'catalogue Windows est incomplet'):
            installers.prepare(self.root, verify_only=True)
