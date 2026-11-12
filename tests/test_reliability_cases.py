"""Prepare isolated evaluation inputs; no model call or automatic quality score."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_reliability_cases as recipe
from pilot import library,store


class ReliabilityCasesTests(unittest.TestCase):
    def test_only_fictional_sources_are_indexed_and_existing_folder_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=recipe.prepare(root/'campaign')
            with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',output/'guides'):
                store.init();self.assertEqual(library.index_guides(),7)
                with store.connect() as db:
                    texts=[r['text'] for r in db.execute('SELECT text FROM documents')]
                self.assertTrue(all('Document fictif' in text for text in texts))
                self.assertFalse(any('OMEGA-ABSENTE' in text for text in texts))
            cases=json.loads((recipe.ROOT/'fixtures/evaluation/reliability.json').read_text(encoding='utf-8'))
            self.assertEqual(len(cases['cases']),8)
            self.assertIn('non exécuté',(output/'RECETTE.md').read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):recipe.prepare(output)


if __name__=='__main__':unittest.main()
