"""The catalogue sort is portable and prevents old plans from restoring a deleted ZIM."""
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

    def test_search_queries_only_the_precomputed_category_and_global_search_uses_kiwix(self):
        prepared=category_index.prepare(self.root,self.state,reserve=0)
        self.assertEqual(prepared['phase'],'completed')
        self.assertGreater(prepared['bytes'],0)
        with patch.object(library,'search_archives',AsyncMock(return_value=([],{'status':'complete'}))) as native:
            found=asyncio.run(library.search('conservation des aliments',kind='documents',domain='resilience'))
            self.assertEqual(found[0]['title'],'Conservation des aliments')
            self.assertEqual(native.call_args.kwargs['skip_native'],(self.zim.stem,))
            self.assertEqual(found.coverage['category_index']['searched'],1)
            asyncio.run(library.search('conservation des aliments',kind='documents',domain='all'))
            self.assertEqual(native.call_args.kwargs['skip_native'],())

    def test_correction_invalidates_then_rebuilds_the_category_index(self):
        from pilot import catalogue
        category_index.prepare(self.root,self.state,reserve=0)
        identifier=f'zim:{self.zim.stem}/Conservation'
        revision=catalogue.revision(identifier,self.guide,self.root)
        catalogue.save(identifier,{'domains':['culture'],'document_type':'overview','status':'corrected'},
                       revision,self.guide,self.root)
        report,path=category_index.availability(self.root,self.state)
        self.assertEqual(report['phase'],'outdated')
        self.assertIsNone(path)
        category_index.prepare(self.root,self.state,reserve=0)
        _,path=category_index.availability(self.root,self.state)
        plan=retrieval.plan('conservation',['conservation'],{})
        self.assertFalse(archive_index.search(path.parent,plan,category='resilience',only_path=path))
        self.assertTrue(archive_index.search(path.parent,plan,category='culture',only_path=path))
