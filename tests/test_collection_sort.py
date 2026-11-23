"""The catalogue sort is portable and prevents old plans from restoring a deleted ZIM."""
import json
import asyncio
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from pilot import archive_index, category_index, collection_sort, library, network, retrieval, store
import test_kiwix_select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import collection_tasks
import content
import content_retry
import setup


class CollectionSortTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.zims=self.root/'library/zim'
        self.zims.mkdir(parents=True)
        self.catalog=self.root/'catalog'
        self.state=self.root/'state/pilot'
        for module,name,value in [(store,'ROOT',self.state),(network,'CATALOG',self.catalog)]:
            setting=patch.object(module,name,value)
            setting.start()
            self.addCleanup(setting.stop)

    def test_exclusion_requires_a_fresh_preview_and_survives_an_old_download_plan(self):
        old=self.zims/'gutenberg_en_lcc-d_2025-12.zim'
        old.write_bytes(b'archive')
        new=self.zims/'gutenberg_en_lcc-d_2026-11.zim.part'
        excluded=collection_sort.archive(old.name)
        pending=collection_tasks.preview(self.root,{excluded})
        new.write_bytes(b'partial')
        with self.assertRaisesRegex(setup.SetupError,'sélection a changé'):
            collection_tasks.exclude(self.root,{excluded},pending['token'])
        self.assertTrue(old.is_file())
        updated=collection_tasks.preview(self.root,{excluded})
        self.assertEqual(updated['bytes'],len(b'archivepartial'))
        self.assertEqual(collection_tasks.exclude(self.root,{excluded},updated['token']),updated['bytes'])
        self.assertFalse(old.exists() or new.exists())
        item={'id':'later','path':'library/zim/gutenberg_en_lcc-d_2027-02.zim'}
        self.assertEqual(content_retry.remaining(self.root,[item]),[])
        with patch.object(content,'transfer',side_effect=AssertionError('Excluded transfer attempted')):
            self.assertEqual(content.download(self.root,[item]),[])

    def test_export_import_preserves_separate_states_across_editions(self):
        active=collection_sort.Sort()
        other=collection_sort.archive('ted_mul_history_2026-09.zim')
        excluded=collection_sort.archive('gutenberg_en_lcc-d_2026-09a.zim')
        collection_sort.save(self.catalog,active.change({other},'other').change({excluded},'excluded'))
        new_root=self.root/'fresh'
        collection_tasks.merge(new_root,collection_sort.read_file(self.catalog/collection_sort.FILENAME).as_json())
        imported=collection_sort.load(new_root/'catalog')
        self.assertEqual(imported.state(collection_sort.archive('ted_mul_history_2027-03.zim')),'other')
        self.assertEqual(imported.state(collection_sort.archive('gutenberg_en_lcc-d_2027-01.zim')),'excluded')
        self.assertFalse(imported.permits(other,'resilience'))
        self.assertTrue(imported.permits(other,'other'))
        self.assertTrue(imported.permits(other,'all'))
        self.assertFalse(imported.permits(excluded,'all'))


class PortableSelectionTests(unittest.TestCase):
    def test_an_imported_cultural_collection_can_be_downloaded_and_exclusion_blocks_its_new_edition(self):
        fixture=test_kiwix_select.KiwixSelectionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        saved=fixture.entry('fixture_livres_en_all',title='Romans',summary='')
        blocked=fixture.entry('appropedia_en_all',filename='appropedia_en_all_maxi_2027-04.zim')
        sorting=collection_sort.Sort(frozenset({collection_sort.archive(saved['filename'])}),
                                     frozenset({collection_sort.archive('appropedia_en_all_nopic_2026-02.zim')}))
        collection_sort.save(fixture.root/'catalog',sorting)
        plan=fixture.plan([saved,blocked])
        self.assertEqual([Path(item['path']).name for item in plan['items']],[saved['filename']])
        records={r['filename']:r for r in plan['candidates']}
        self.assertEqual(records[saved['filename']]['classification'],'other')
        self.assertEqual(records[blocked['filename']]['status'],'sort_excluded')


try:
    from libzim.writer import Creator
    from kiwix_search_smoke import Article
except ImportError:
    Creator=None


@unittest.skipUnless(Creator,'Optional libzim reader required')
class CategorySearchTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.zim=self.root/'wikipedia_fr_all_maxi_2026-11.zim'
        with Creator(self.zim).config_indexing(False,'fra') as creator:
            creator.add_metadata('Title','Wikipédia')
            creator.add_metadata('Language','fra')
            creator.add_item(Article('Conservation','Conservation des aliments','Conservation alimentaire fictive.'))
            creator.add_item(Article('Histoire','Histoire des arts','Musées et art ancien.'))
        self.state=self.root/'state'
        self.guide=self.root/'guides'
        self.guide.mkdir()
        env=patch.dict('os.environ',{'ZIM_DIR':str(self.root)})
        env.start()
        self.addCleanup(env.stop)
        for module,name,value in [(store,'ROOT',self.state),(network,'CATALOG',self.root/'catalog'),(library,'GUIDES',self.guide)]:
            p=patch.object(module,name,value)
            p.start()
            self.addCleanup(p.stop)
        store.init()

    def test_reference_fallback_uses_the_category_index_and_respects_collection_sort(self):
        prepared=category_index.prepare(self.root,self.state,reserve=0)
        self.assertEqual(prepared['phase'],'completed')
        self.assertGreater(prepared['bytes'],0)
        with patch.object(library,'search_archives',AsyncMock(return_value=([],{'status':'complete'}))) as native:
            practical = asyncio.run(library.search('conservation des aliments', kind='documents', domain='resilience'))
            self.assertEqual(practical[0]['title'], 'Conservation des aliments')
            self.assertTrue(practical[0]['reference_fallback'])
            self.assertEqual(practical[0]['domains'], ['culture'])
            self.assertEqual(native.call_args.kwargs['skip_native'], (self.zim.stem,))
            found = asyncio.run(library.search('conservation des aliments', kind='documents', domain='culture'))
            self.assertEqual(found[0]['title'], 'Conservation des aliments')
            self.assertEqual(found[0]['classification']['source_role'], 'reference')
            self.assertNotIn('reference_fallback', found[0])
            self.assertEqual(native.call_args.kwargs['skip_native'],(self.zim.stem,))
            self.assertEqual(found.coverage['category_index']['searched'],1)
            asyncio.run(library.search('conservation des aliments',kind='documents',domain='all'))
            self.assertEqual(native.call_args.kwargs['skip_native'],())
            catalog_dir = self.root / 'catalog'
            catalog_dir.mkdir(exist_ok=True)
            (catalog_dir / collection_sort.FILENAME).write_text(json.dumps(
                collection_sort.Sort().change([collection_sort.archive(self.zim.name)], 'other').as_json()
            ))
            self.assertFalse(asyncio.run(library.search('conservation des aliments', kind='documents', domain='resilience')))

    def test_valueless_html_attributes_are_read_as_empty(self):
        # ready.gov (22 Nov 2026): <span class> stopped the whole classification.
        from pilot.html_text import Text
        from pilot.illustrations import HTMLFigures
        reader=Text();reader.feed('<html lang><body><span class>Eau</span><img class src="a.png" alt></body></html>')
        self.assertIn('Eau',''.join(reader.parts))
        figures=HTMLFigures();figures.feed('<figure class><img class src="a.png" alt><figcaption class>Pompe</figcaption></figure>')
        self.assertEqual(figures.images[0]['src'],'a.png')

    def test_one_failing_archive_is_reported_and_the_others_continue(self):
        other=self.root/'guides_fr_2026-11.zim'
        other.write_bytes(self.zim.read_bytes())
        original=archive_index.build_archive
        def build(path,*args,**kwargs):
            if path==self.zim:raise AttributeError('fixture')
            return original(path,*args,**kwargs)
        with patch.object(archive_index,'build_archive',side_effect=build):
            report=category_index.prepare(self.root,self.state,reserve=0)
        self.assertEqual(report['phase'],'error')
        self.assertEqual(report['failures'],[{'archive':self.zim.name,'error':'AttributeError'}])
        self.assertEqual(report['completed'],1)

    def test_host_classification_reads_published_corrections_without_opening_pilot_db(self):
        # Windows reads of the WAL pilot.db broke the Docker pilot's SQLite calls (23 Nov 2026).
        from pilot import catalogue
        before,_=category_index.signature(self.zim,self.state)
        identifier=f'zim:{self.zim.stem}/Conservation'
        revision=catalogue.revision(identifier,self.guide,self.root)
        catalogue.save(identifier,{'domains':['resilience'],'document_type':'procedure','status':'reviewed'},
                       revision,self.guide,self.root)
        published=json.loads((self.state/category_index.CORRECTIONS).read_text())
        self.assertEqual(published['records'],{identifier:{'revision':revision,'domains':['resilience']}})
        with patch('sqlite3.connect',side_effect=AssertionError('pilot.db opened')):
            after,saved=category_index.signature(self.zim,self.state)
            self.assertEqual(len(category_index.ready_indexes(self.root,self.state)),0)
        self.assertNotEqual(before,after)
        self.assertEqual(saved,{'Conservation':['resilience']})
        catalogue.reset(identifier)
        self.assertEqual(json.loads((self.state/category_index.CORRECTIONS).read_text())['records'],{})
        self.assertEqual(category_index.signature(self.zim,self.state)[0],before)

    def test_correction_invalidates_then_rebuilds_the_category_index(self):
        from pilot import catalogue
        category_index.prepare(self.root,self.state,reserve=0)
        identifier=f'zim:{self.zim.stem}/Conservation'
        revision=catalogue.revision(identifier,self.guide,self.root)
        catalogue.save(identifier,{'domains':['resilience'],'document_type':'procedure','status':'reviewed'},
                       revision,self.guide,self.root)
        report,path=category_index.availability(self.root,self.state)
        self.assertEqual(report['phase'],'outdated')
        self.assertIsNone(path)
        category_index.prepare(self.root,self.state,reserve=0)
        _,path=category_index.availability(self.root,self.state)
        plan=retrieval.plan('conservation',['conservation'],{})
        self.assertTrue(archive_index.search(path.parent,plan,category='resilience',only_path=path))
        self.assertFalse(archive_index.search(path.parent,plan,category='culture',only_path=path))

    def test_return_to_main_fund_reuses_index_and_prepares_new_archive(self):
        other = self.root / 'guides_fr_2026-11.zim'
        with Creator(other).config_indexing(False, 'fra') as creator:
            creator.add_metadata('Title', 'Guides fictifs')
            creator.add_metadata('Language', 'fra')
            creator.add_item(Article('Potager', 'Potager', 'Semences pour le potager.'))
        catalog = self.root / 'catalog'
        main = collection_sort.Sort()
        other_key = collection_sort.archive(other.name)
        selection = main.change([other_key], 'other')
        collection_sort.save(catalog, selection)
        category_index.prepare(self.root, self.state, catalog=catalog, reserve=0)
        self.assertEqual(set(category_index.ready_indexes(self.root, self.state, selection)), {self.zim.stem})
        collection_sort.save(catalog, main)
        report, _ = category_index.availability(self.root, self.state, main)
        self.assertEqual((report['phase'], report['completed']), ('outdated', 1))
        category_index.prepare(self.root, self.state, catalog=catalog, reserve=0)
        indexes = category_index.ready_indexes(self.root, self.state, main)
        self.assertEqual(set(indexes), {self.zim.stem, other.stem})
        plan = retrieval.plan('potager', ['potager'], {})
        hits = archive_index.search(indexes[other.stem].parent, plan, category='resilience',
                                    index_paths=indexes.values())
        self.assertIn('Potager', [hit['title'] for hit in hits])
        self.assertEqual(set(hits.coverage['books']), set(indexes))
        self.assertEqual(set(category_index.ready_indexes(self.root, self.state, selection)), {self.zim.stem})
        self.assertEqual(category_index.ready_indexes(self.root, self.state, main), indexes)

    def test_parallel_resume_preserves_committed_cursor_and_search_results(self):
        other = self.root / 'parallel_fr_2026-11.zim'
        with Creator(other).config_indexing(False, 'fra') as creator:
            creator.add_metadata('Language', 'fra')
            for number in range(1600):
                creator.add_item(Article(f'Potager{number}', f'Potager {number}', 'Semences pour le potager.'))
        cancel = self.root / 'cancel'
        root = self.root / 'parallel'
        options = dict(force=True, categories=category_index.DOMAINS, reserve=0, workers=2)

        def checkpoint(done, total, counts):
            if done >= 1024:
                cancel.touch()

        with self.assertRaises(archive_index.Paused):
            archive_index.build_archive(other, root, cancel=cancel, progress=checkpoint, **options)
        self.assertFalse(list(root.glob('*.sqlite')))
        with archive_index.connect(next(root.glob('*.building')), True) as db:
            self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0], '1024')
        cancel.unlink()
        completed = archive_index.build_archive(other, root, cancel=cancel, **options)
        self.assertEqual(completed['articles'], 1600)
        plan = retrieval.plan('potager', ['potager'], {})
        hits = archive_index.search(root, plan, category='resilience', limit=1700)
        self.assertEqual(len({hit['id'] for hit in hits}), 1600)
