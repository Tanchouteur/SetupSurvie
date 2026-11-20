"""Design budget of the portal stylesheets: colours and sizes come from the tokens.

`portal/design/tokens.css` is the single source of colours. Older sheets still
hold raw values; these limits only go down. When a test fails, use a `var(--ds-…)`
token (with the old value as fallback if the page may load without tokens.css)
instead of a new raw colour or font size, then lower the limit when you remove some.
"""
import re
import unittest
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1] / 'portal'
HEX = re.compile(r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b(?![0-9a-fA-F])')
# Measured on 0.70.0 after mapping near-identical colours (ΔE ≤ 2) to tokens.
MAX_RAW_COLOURS = 239
MAX_FONT_SIZES = 81


def sheets():
    for path in sorted(PORTAL.rglob('*.css')):
        if 'vendor' in path.parts or 'cartes-hors-ligne' in path.parts or path.name == 'tokens.css':
            continue
        yield path, path.read_text(encoding='utf-8')


def raw_colours(text):
    text = re.sub(r'url\([^)]*\)|var\([^()]*\)', '', text)
    lines = (line for line in text.split('\n') if not line.lstrip().startswith('--'))
    return [match for line in lines for match in HEX.findall(line)]


class DesignBudgetTests(unittest.TestCase):
    def test_raw_colours_do_not_grow(self):
        found = sum(len(raw_colours(text)) for _, text in sheets())
        self.assertLessEqual(found, MAX_RAW_COLOURS, 'Utilisez une variable de design/tokens.css.')

    def test_font_sizes_do_not_grow(self):
        sizes = {re.sub(r'\s+', '', value) for _, text in sheets() for value in re.findall(r'font-size:\s*([^;}!]+)', text)}
        self.assertLessEqual(len(sizes), MAX_FONT_SIZES, 'Reprenez une taille déjà utilisée.')

    def test_new_shared_sheets_use_tokens_only(self):
        for name in ('core/core.css',):
            self.assertEqual(raw_colours((PORTAL / name).read_text()), [], name)

    def test_tokens_load_before_every_other_sheet(self):
        html = (PORTAL / 'index.html').read_text()
        sheets_in_order = re.findall(r'<link rel="stylesheet" href="([^"?]+)', html)
        self.assertEqual(sheets_in_order[0], '/design/tokens.css')


if __name__ == '__main__':
    unittest.main()
