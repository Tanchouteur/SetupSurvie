import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import content
import library_reference as ref
import setup
from pilot import collection_sort

RAW = b'tiny zim fixture'
DIGEST = hashlib.sha256(RAW).hexdigest()


def entry(filename, folder='other', title='Fixture'):
    return {'name': ref.kiwix_select.family(filename), 'title': title, 'summary': 'Résumé', 'languages': ['fra'],
            'edition': '2026-11-01', 'flavour': '', 'tags': ['_videos:yes'],
            'meta4': f'https://download.kiwix.org/zim/{folder}/{filename}.meta4', 'filename': filename,
            'estimated_bytes': len(RAW)}


class LibraryReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.requested = []

    def reader(self, available):
        def read(url, maximum=0):
            self.requested.append(url)
            if url not in available:
                raise OSError('HTTP Error 404: Not Found')
            name = url.rsplit('/', 1)[-1].removesuffix('.meta4')
            return (f'<metalink xmlns="urn:ietf:params:xml:ns:metalink"><file name="{name}"><size>{len(RAW)}</size>'
                    f'<hash type="sha-256">{DIGEST}</hash></file></metalink>').encode()
        return read

    def build(self, names, additions=(), sorting=collection_sort.Sort(), available=None):
        entries = [entry('cest-pas-sorcier_fr_energie_2026-11.zim', 'videos'),
                   entry('cest-pas-sorcier_fr_medecine_2026-11.zim', 'videos'),
                   entry('gutenberg_fr_all_2026-11a.zim', 'books'),
                   entry('evageeks_en_all_maxi_2022-11.zim')]
        available = available or {e['meta4'] for e in entries} | {
            'https://download.kiwix.org/zim/gutenberg/gutenberg_fr_all_2026-01.zim.meta4',
            'https://download.kiwix.org/zim/videos/cest-pas-sorcier_fr_energie_2024-11.zim.meta4'}
        entries.append(entry('gutenberg_en_lcc-s_2026-11a.zim', 'gutenberg'))
        return ref.build(names, additions, entries, sorting=sorting, reader=self.reader(available), reference='essai')

    def test_old_edition_is_pinned_exactly_even_after_the_family_moved_folder(self):
        report = self.build(['gutenberg_fr_all_2026-01.zim'])
        self.assertEqual([i['path'] for i in report['items']], ['library/zim/gutenberg_fr_all_2026-01.zim'])
        self.assertEqual(report['items'][0]['url'], 'https://download.kiwix.org/zim/gutenberg/gutenberg_fr_all_2026-01.zim')
        self.assertEqual(report['items'][0]['sha256'], DIGEST)
        self.assertFalse(report['unavailable'])

    def test_additions_replace_older_edition_and_sort_exclusions_are_listed(self):
        sorting = collection_sort.Sort(frozenset({'zim:cest-pas-sorcier_fr_medecine'}), frozenset({'zim:evageeks_en_all'}))
        report = self.build(['cest-pas-sorcier_fr_energie_2024-11.zim', 'evageeks_en_all_maxi_2022-11.zim'],
                            [(re.compile(r'cest-pas-sorcier_fr_[a-z-]+_\d{4}-\d{2}\.zim'), 'vidéos')], sorting)
        paths = {i['path']: i for i in report['items']}
        self.assertEqual(set(paths), {'library/zim/cest-pas-sorcier_fr_energie_2026-11.zim',
                                      'library/zim/cest-pas-sorcier_fr_medecine_2026-11.zim'})
        self.assertEqual(paths['library/zim/cest-pas-sorcier_fr_medecine_2026-11.zim']['classification'], 'other')
        self.assertEqual(report['excluded_by_sort'], ['evageeks_en_all_maxi_2022-11.zim'])

    def test_missing_metalink_is_reported_without_inventing_an_item(self):
        report = self.build(['gutenberg_fr_all_2026-01.zim'], available={'https://example.invalid/none'})
        self.assertFalse(report['items'])
        self.assertEqual(report['unavailable'][0]['archive'], 'gutenberg_fr_all_2026-01.zim')

    def test_manifest_is_accepted_by_the_downloader_and_verify_reports_each_gap(self):
        report = self.build(['gutenberg_fr_all_2026-01.zim', 'cest-pas-sorcier_fr_energie_2024-11.zim'])
        manifest = self.root / 'reference.json'
        manifest.write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(len(content.catalog(manifest)), 2)
        data = ref.load(manifest)
        folder = self.root / 'data/library/zim'; folder.mkdir(parents=True)
        (folder / 'gutenberg_fr_all_2026-01.zim').write_bytes(RAW)
        (folder / 'cest-pas-sorcier_fr_energie_2023-01.zim').write_bytes(b'old')
        (folder / 'notes_fr_all_2026-01.zim').write_bytes(b'x')
        result = ref.verify(self.root / 'data', data, deep=True)
        status = {row['archive']: row['status'] for row in result['archives']}
        self.assertEqual(status['gutenberg_fr_all_2026-01.zim'], 'ok')
        self.assertEqual(status['cest-pas-sorcier_fr_energie_2024-11.zim'], 'missing')
        self.assertEqual(status['cest-pas-sorcier_fr_energie_2023-01.zim'], 'other_edition')
        self.assertEqual(status['notes_fr_all_2026-01.zim'], 'extra')
        self.assertFalse(result['conform'])
        (folder / 'gutenberg_fr_all_2026-01.zim').write_bytes(b'tiny zim fixturX')
        self.assertEqual({r['archive']: r['status'] for r in ref.verify(self.root / 'data', data, deep=True)['archives']}
                         ['gutenberg_fr_all_2026-01.zim'], 'hash_mismatch')

    def test_inventory_page_and_plain_list_are_read(self):
        page = self.root / 'inventory.json'
        page.write_text(json.dumps({'books': [{'archive_name': 'gutenberg_fr_all_2026-01.zim'}]}), encoding='utf-8')
        self.assertEqual(ref.read_names(page), ['gutenberg_fr_all_2026-01.zim'])
        plain = self.root / 'list.tsv'
        plain.write_text('gutenberg_fr_all_2026-01.zim\t12\n', encoding='utf-8')
        self.assertEqual(ref.read_names(plain), ['gutenberg_fr_all_2026-01.zim'])
        plain.write_text('../evil.zim\n', encoding='utf-8')
        with self.assertRaises(setup.SetupError):
            ref.read_names(plain)

    def test_shipped_reference_is_valid_and_respects_the_default_sort(self):
        data = ref.load()
        sorting = collection_sort.read_file(ref.DEFAULT_SORT)
        for item in data['items']:
            self.assertNotEqual(sorting.state(collection_sort.path_key(item['path'])), 'excluded', item['path'])
        self.assertFalse(data['unavailable'])
        names = {Path(i['path']).name for i in data['items']}
        self.assertTrue(any(n.startswith('cest-pas-sorcier_fr_medecine_') for n in names))
        self.assertTrue(any(n.startswith('mondial-tissus_fr_all_') for n in names))


if __name__ == '__main__':
    unittest.main()
