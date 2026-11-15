"""Small manifest checks only; no real notice, network or inference in CI."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from real_radio_check import scenario


class DocumentaryScenarioTests(unittest.TestCase):
    def test_case_manifest_is_bound_to_actual_local_document_and_detects_a_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'fixture.fr.txt';source.write_text('Fictional local text.')
            manifest=root/'cases.json';data={'documents':[{'path':source.name,'title':'Fixture','language':'fr','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}],'cases':[{'name':'case','question':'Question fictive ?','review_reference':'Aucune validation de contenu réel.'}]}
            manifest.write_text(json.dumps(data));documents,cases=scenario(manifest)
            self.assertEqual(documents[0][0],source.resolve());self.assertEqual(cases[0][0],'case')
            source.write_text('Changed fixture.')
            with self.assertRaises(ValueError):scenario(manifest)

    def test_parent_path_cannot_add_an_unrelated_file_to_the_model_context(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest=Path(directory)/'cases.json'
            manifest.write_text(json.dumps({'documents':[{'path':'../outside.txt','sha256':'a'*64}],'cases':[]}))
            with self.assertRaises(ValueError):scenario(manifest)
