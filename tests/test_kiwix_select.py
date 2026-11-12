from collections import namedtuple
import shutil
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import content
import kiwix_select as ks
import setup


class KiwixSelectionTests(unittest.TestCase):
    def setUp(self):
        # Tiny fixtures must not depend on the CI host having the production
        # 15 GB reserve. Capacity failure cases override this fixture explicitly.
        usage=namedtuple('Usage','total used free')(200_000_000_000,100_000_000_000,100_000_000_000)
        disk=patch.object(shutil,'disk_usage',return_value=usage);disk.start();self.addCleanup(disk.stop)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = b'illustrated zim sample'
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def entry(self, name='appropedia_en_all', **values):
        return {'name': name, 'title': 'Appropedia', 'summary': 'Sustainable techniques',
                'languages': ['eng'], 'edition': '2026-02-01', 'flavour': 'maxi',
                'tags': ['_pictures:yes', '_ftindex:yes'],
                'meta4': f'https://download.kiwix.org/zim/other/{name}_maxi_2026-02.zim.meta4',
                'filename': f'{name}_maxi_2026-02.zim', 'estimated_bytes': 1024, **values}

    def metalink(self, entry, **kwargs):
        return (f'<metalink xmlns="urn:ietf:params:xml:ns:metalink"><file name="{entry["filename"]}">'
                f'<size>{len(self.raw)}</size><hash type="sha-256">{self.digest}</hash></file></metalink>').encode()

    def plan(self, entries, requested=('autonomie',), **kwargs):
        by_url = {e['meta4']: e for e in entries}
        with patch.object(content, 'catalog', return_value=[]):
            return ks.select(entries, self.root, list(requested), reserve=0,
                             reader=lambda url, **kw: self.metalink(by_url[url]), **kwargs)

    def test_parse_official_feed_and_reject_incomplete_catalog(self):
        raw = b'''<feed xmlns="http://www.w3.org/2005/Atom"><totalResults>1</totalResults><entry>
        <name>appropedia_en_all</name><title>Appropedia</title><language>eng,fra</language>
        <updated>2026-02-01T00:00:00Z</updated><tags>_pictures:yes;_ftindex:yes</tags>
        <link type="application/x-zim" length="1024" href="https://download.kiwix.org/zim/other/appropedia_en_all_2026-02.zim.meta4"/>
        </entry></feed>'''
        entries = ks.parse_feed(raw)
        self.assertEqual(entries[0]['languages'], ['eng', 'fra'])
        self.assertEqual(entries[0]['filename'], 'appropedia_en_all_2026-02.zim')
        with self.assertRaises(setup.SetupError):
            ks.parse_feed(raw.replace(b'<totalResults>1', b'<totalResults>2'))

    def test_related_themes_merge_into_one_archive_with_exact_metalink_size(self):
        plan = self.plan([self.entry()], ['autonomie', 'agriculture', 'energie'])
        self.assertEqual(len(plan['items']), 1)
        item = plan['items'][0]
        self.assertEqual(set(item['topics']), {'autonomie', 'agriculture', 'energie'})
        self.assertEqual(item['bytes'], len(self.raw))  # OPDS size can be rounded.
        self.assertEqual(plan['remaining_download_bytes'], len(self.raw))
        self.assertTrue(item['commercial_review'])
        self.assertEqual(item['sha256'], self.digest)

    def test_existing_older_edition_is_kept_without_network(self):
        p = self.root / 'library/zim/appropedia_en_all_maxi_2025-01.zim'
        p.parent.mkdir(parents=True); p.write_bytes(self.raw)
        with patch.object(ks, 'pin', side_effect=AssertionError('No metadata request for installed family')):
            plan = self.plan([self.entry()])
        self.assertFalse(plan['items'])
        self.assertEqual(plan['candidates'][0]['status'], 'already_local')
        self.assertEqual(plan['local_inventory'][0]['status'], 'present_unverified')
        self.assertEqual(p.read_bytes(), self.raw)

    def test_newest_illustrated_variant_and_language_filter(self):
        older = self.entry(edition='2025-01-01')
        nopic = self.entry(flavour='nopic', tags=['_pictures:no'], filename='appropedia_en_all_nopic_2026-02.zim')
        unrelated = self.entry(name='appropedia_de_all', languages=['deu'])
        plan = self.plan([older, nopic, unrelated, self.entry()])
        self.assertEqual(len(plan['candidates']), 1)
        self.assertTrue(plan['items'][0]['pictures'])
        self.assertEqual(plan['items'][0]['edition'], '2026-02-01')
        self.assertEqual(ks.family('vikidia_en_all_nopic_2026-09a.zim'), ks.family('vikidia_en_all_maxi_2026-09.zim'))

    def test_game_false_positive_and_chasse_gap(self):
        game = self.entry(name='survivors_en_all', title='Vampire Survivors wiki', summary='A survival roguelite game')
        plan = self.plan([game], ['survie', 'chasse'])
        self.assertFalse(plan['items'])
        self.assertEqual(plan['missing_themes'], ['survie', 'chasse'])
        minecraft = self.entry(name='minecraft.wiki_en_all', title='Minecraft Wiki', summary='Construction and shelter')
        self.assertFalse(ks.matches(minecraft, ks.themes(), ['abri']))

    def test_wikimedia_extract_not_added_alongside_full_collection(self):
        full = self.entry(name='wikivoyage_en_all', title='Wikivoyage')
        extract = self.entry(name='wikivoyage_en_europe', title='Wikivoyage Europe', estimated_bytes=20)
        plan = self.plan([extract, full], ['orientation'])
        self.assertEqual(len(plan['items']), 1)
        self.assertIn('wikivoyage_en_all', plan['items'][0]['path'])
        self.assertEqual(plan['candidates'][1]['status'], 'covered_by_full_collection')
        # If the complete collection cannot fit, the smaller extract remains useful.
        full['estimated_bytes'] = 200_000_000_000
        plan = self.plan([extract, full], ['orientation'])
        self.assertIn('wikivoyage_en_europe', plan['items'][0]['path'])

    def test_obviously_oversize_collection_needs_no_metalink_request(self):
        with patch.object(ks, 'pin', side_effect=AssertionError('Huge archive should be excluded before Metalink')):
            plan = self.plan([self.entry(estimated_bytes=200_000_000_000)], max_add=10_000_000_000)
        self.assertFalse(plan['items'])
        self.assertEqual(plan['candidates'][0]['status'], 'budget_excluded')

    def test_budget_and_resume_use_only_remaining_bytes(self):
        entry = self.entry()
        plan = self.plan([entry], max_add=len(self.raw)-1)
        self.assertEqual(plan['candidates'][0]['status'], 'budget_excluded')
        partial = self.root / ('library/zim/' + entry['filename'] + '.part')
        partial.parent.mkdir(parents=True); partial.write_bytes(self.raw[:5])
        plan = self.plan([entry], max_add=len(self.raw)-5)
        self.assertEqual(plan['remaining_download_bytes'], len(self.raw)-5)
        self.assertEqual(partial.read_bytes(), self.raw[:5])

    def test_physical_reserve_and_document_budget_restrict_selection(self):
        from collections import namedtuple
        usage = namedtuple('Usage', 'total used free')(590, 570, 20)
        with patch.object(ks.shutil, 'disk_usage', return_value=usage):
            plan = self.plan([self.entry()], max_add=1000)
        self.assertEqual(plan['available_additional_bytes'], 20)
        self.assertFalse(plan['items'])
        p = self.root / 'library/guides/manual.txt'; p.parent.mkdir(parents=True); p.write_bytes(b'x'*10)
        plan = self.plan([self.entry()], budget=30)
        self.assertFalse(plan['items'])
        self.assertEqual(plan['library_bytes'], 10)

    def test_missing_or_wrong_metalink_never_selected(self):
        entry = self.entry()
        for raw in [self.metalink(entry).replace(self.digest.encode(), b'bad'),
                    self.metalink(entry).replace(entry['filename'].encode(), b'other.zim'), b'<broken']:
            with self.subTest(raw=raw), patch.object(content, 'catalog', return_value=[]):
                plan = ks.select([entry], self.root, ['autonomie'], reserve=0, reader=lambda *a, **k: raw)
                self.assertFalse(plan['items'])
                self.assertEqual(plan['candidates'][0]['status'], 'metadata_unavailable')

    def test_official_urls_only_and_symbolic_partial_refused(self):
        for url in ['http://download.kiwix.org/zim/other/a.zim',
                    'https://download.kiwix.org.attacker.net/zim/other/a.zim',
                    'https://download.kiwix.org/zim/../private.zim',
                    'https://user:pass@download.kiwix.org/zim/other/a.zim',
                    'https://download.kiwix.org:8080/zim/other/a.zim']:
            with self.assertRaises(setup.SetupError): ks.official_url(url)
        part = self.root / ('library/zim/' + self.entry()['filename'] + '.part'); part.parent.mkdir(parents=True)
        try: part.symlink_to(self.root / 'private')
        except OSError: self.skipTest('Liens symboliques non autorisés.')
        with self.assertRaises(setup.SetupError): self.plan([self.entry()])

    def test_archive_without_fulltext_index_is_explicit(self):
        plan = self.plan([self.entry(tags=['_pictures:yes', '_ftindex:no', '_videos:yes'])])
        self.assertFalse(plan['items'][0]['fulltext_index'])
        self.assertTrue(plan['items'][0]['videos'])

    def test_frozen_plan_is_consumed_by_existing_verified_downloader(self):
        plan = self.plan([self.entry()])
        path = self.root / 'selection.json'; path.write_text(json.dumps(plan))
        class Response(io.BytesIO):
            status = 200
            headers = {}
            def geturl(self): return 'https://download.kiwix.org/zim/other/a.zim'
        class Opener:
            def open(inner, *a, **k): return Response(self.raw)
        with patch.object(sys, 'argv', ['content.py', 'download', '--selection', str(path), '--data-dir', str(self.root), '--no-refresh']), \
             patch.object(content.urllib.request, 'build_opener', return_value=Opener()):
            content.main()
        target = self.root / plan['items'][0]['path']
        self.assertEqual(target.read_bytes(), self.raw)
        self.assertFalse(target.with_name(target.name + '.part').exists())

    def test_empty_plan_never_starts_network_or_services(self):
        plan = self.plan([], ['chasse'])
        path = self.root / 'selection.json'; path.write_text(json.dumps(plan))
        with patch.object(sys, 'argv', ['content.py', 'download', '--selection', str(path)]), \
             patch.object(content, 'download') as download:
            content.main(); download.assert_not_called()


if __name__ == '__main__': unittest.main()
