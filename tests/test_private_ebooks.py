"""Private books in library/ebooks: indexed by the pilot, served read-only, never exported."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))


def service(text, name, following):
    return text.split(f'\n  {name}:\n', 1)[1].split(f'\n  {following}:\n', 1)[0]


class PrivateEbooksTests(unittest.TestCase):
    def test_compose_mounts_ebooks_read_only_under_the_guides(self):
        text = (ROOT / 'compose.yaml').read_text(encoding='utf-8')
        self.assertIn('${DATA_DIR}/library/ebooks:/guides/ebooks:ro', service(text, 'pilot', 'portal'))
        self.assertIn('${DATA_DIR}/library/ebooks:/srv/guides/ebooks:ro', service(text, 'portal', 'router-foot'))

    def test_linux_lab_mounts_ebooks_like_compose(self):
        text = (ROOT / 'scripts/linux_lab.py').read_text(encoding='utf-8')
        self.assertIn("/data/library/ebooks:/guides/ebooks:ro", text)
        self.assertIn("/data/library/ebooks:/srv/guides/ebooks:ro", text)

    def test_installation_creates_the_ebooks_folder(self):
        import setup
        self.assertIn('library/ebooks', setup.DIRECTORIES)

    def test_kit_export_skips_the_ebooks_mount_point(self):
        text = (ROOT / 'scripts/pilot_kit.py').read_text(encoding='utf-8')
        loop = text.split("for path in sorted((data/'library/guides').rglob('*')):", 1)[1].split('\n    if ', 1)[0]
        self.assertIn("!='ebooks'", loop)

    def test_guide_index_lists_books_in_the_ebooks_subfolder(self):
        from pilot import library
        with tempfile.TemporaryDirectory() as folder:
            guides = Path(folder)
            (guides / 'ebooks').mkdir()
            (guides / 'ebooks/livre.epub').write_bytes(b'epub')
            (guides / 'guide.fr.md').write_text('# Guide', encoding='utf-8')
            with patch.object(library, 'GUIDES', guides):
                names = [relative for _, relative in library.guide_files()]
        self.assertEqual(names, ['ebooks/livre.epub', 'guide.fr.md'])


if __name__ == '__main__':
    unittest.main()
