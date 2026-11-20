"""The version shown by the API must match the published release."""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VersionConsistencyTests(unittest.TestCase):
    def test_api_version_matches_release(self):
        release = json.loads((ROOT / 'deploy/release.json').read_text())['version']
        tree = ast.parse((ROOT / 'pilot/app.py').read_text())
        api = next(node.value.value for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(getattr(target, 'id', None) == 'VERSION' for target in node.targets))
        self.assertEqual(api, release)
        self.assertRegex(release, r'^\d+\.\d+\.\d+$')

    def test_launchers_require_the_same_python(self):
        survie = (ROOT / 'scripts/survie.sh').read_text()
        self.assertIn('>= (3,11)', survie)
        self.assertIn('Python 3.11+', (ROOT / 'scripts/setup.py').read_text().splitlines()[1])


if __name__ == '__main__':
    unittest.main()
