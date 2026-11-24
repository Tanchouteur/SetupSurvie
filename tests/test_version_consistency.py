"""The version shown by the API must match the published release."""
import ast
import json
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
        self.assertIn(f'Version **{release}**', (ROOT / 'README.md').read_text())
        self.assertRegex(release, r'^\d+\.\d+\.\d+$')

    def test_launchers_require_the_same_python(self):
        for launcher in ('survie.sh', 'survie.ps1'):
            with self.subTest(launcher=launcher):
                source = (ROOT / 'scripts' / launcher).read_text(encoding='utf-8-sig')
                self.assertIn('sys.version_info >= (3,11)', source)
        self.assertIn('Python 3.11+', (ROOT / 'scripts/setup.py').read_text())


if __name__ == '__main__':
    unittest.main()
