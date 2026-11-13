"""The complete renderer is local, versioned and verified without npm at runtime."""
import hashlib
import json
from pathlib import Path
import unittest


class PDFAssetsTests(unittest.TestCase):
    def test_vendored_distribution_matches_verified_manifest(self):
        root=Path(__file__).resolve().parents[1]/'portal/vendor/pdfjs'
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['version'],'6.5.438')
        self.assertTrue(manifest['integrity'].startswith('sha512-'))
        listed={item['path'] for item in manifest['files']}
        self.assertTrue({'pdf.mjs','pdf.worker.mjs','pdf_viewer.mjs','pdf_viewer.css','LICENSE'}<=listed)
        for record in manifest['files']:
            with self.subTest(path=record['path']):
                path=root/record['path'];self.assertTrue(path.resolve().is_relative_to(root.resolve()))
                raw=path.read_bytes();self.assertEqual(len(raw),record['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),record['sha256'])
