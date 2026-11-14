"""Real tiny ZIMs, resumable text index and publication; no downloaded corpus."""
import asyncio
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,AsyncMock

from pilot import archive_index,library,retrieval,store
try:
    from libzim.writer import Creator
    from kiwix_search_smoke import Article
    HAS_LIBZIM=True
except ImportError:HAS_LIBZIM=False


@unittest.skipUnless(HAS_LIBZIM,'Optional libzim reader required')
class ArchiveIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.zim=self.root/'manual_fr.zim';self.index=self.root/'state/archive-index'
        self.create()

    def create(self,extra=False):
        with Creator(self.zim).config_indexing(False,'fra') as c:
            for k,v in {'Title':'Guide fictif','Language':'fra','Name':'manual_fr'}.items():c.add_metadata(k,v)
            for i in range(140 if extra else 130):c.add_item(Article('Article_'+str(i),'Document '+str(i),'Fictional fixture.'))
            c.add_item(Article('Reparer_velo','Réparer un vélo','Une crevaison et la réparation de bicycle. Fixture sans procédure.'))

    def query(self,words='réparer un vélo'):
        plan=retrieval.plan(words,library.search_terms(words),library.SYNONYMS)
        return archive_index.search(self.index,plan)

    def test_real_missing_index_finds_body_text_and_links_without_reader_at_query_time(self):
        result=archive_index.build_archive(self.zim,self.index)
        self.assertEqual(result['status'],'ready');self.assertTrue(self.query())
        self.assertEqual(self.query()[0]['id'],'zim:manual_fr/Reparer_velo')
        body=self.query('crevaison');self.assertTrue(body);self.assertIn('/content/manual_fr/Reparer_velo',body[0]['url'])
        self.assertEqual(archive_index.build_archive(self.zim,self.index)['articles'],result['articles'])

    def test_interruption_resumes_from_committed_cursor_and_preserves_old_publication(self):
        archive_index.build_archive(self.zim,self.index);original=self.query()
        # Force replacement after the source changes, interrupt after the first batch.
        self.create(extra=True);calls=0
        def disk(path):
            nonlocal calls
            calls+=1
            if calls>90:raise archive_index.Paused()
            return type('Disk',(),{'free':5_000_000_000})()
        with patch.object(archive_index.shutil,'disk_usage',disk):
            with self.assertRaises(archive_index.Paused):archive_index.build_archive(self.zim,self.index)
        self.assertEqual(self.query(),original)
        building=next(self.index.glob('*.building'))
        with archive_index.connect(building) as db:self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0],'64')
        result=archive_index.build_archive(self.zim,self.index);self.assertEqual(result['articles'],141)
        self.assertTrue(self.query());self.assertFalse(list(self.index.glob('*.building')))

    def test_library_merges_local_index_even_when_kiwix_is_unavailable(self):
        archive_index.build_archive(self.zim,self.index)
        with patch.object(store,'ROOT',self.root/'state'),patch.object(library,'books',AsyncMock(return_value=library.Catalog(available=False))):
            store.init();found=asyncio.run(library.search('crevaison'))
        self.assertTrue(found);self.assertEqual(found[0]['match'],'local_index');self.assertEqual(found.coverage['status'],'unavailable')

    def test_cli_uses_multiple_worker_processes_and_reuses_published_index(self):
        zim_dir=self.root/'zim';zim_dir.mkdir();self.zim.rename(zim_dir/self.zim.name)
        result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/index_archives.py'),
            '--zim-dir',str(zim_dir),'--state-dir',str(self.root/'state'),'--workers','2','--reserve-bytes','1000000000'],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout);self.assertEqual(report['phase'],'completed');self.assertEqual(report['workers'],2)
        self.assertTrue(self.query())

    def test_automatic_queue_worker_publishes_real_index_and_acknowledges_only_selection(self):
        import hashlib
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        import setup,search_index_queue as queue,library_tasks as jobs
        data=self.root/'data';app=setup.Installation(self.root/'private');config=app.init('linux',data,cpu=True)
        target=data/'library/zim/manual_fr.zim';self.zim.rename(target)
        queue.enqueue(data,{'path':'library/zim/manual_fr.zim','sha256':setup.file_hash(target)})
        manager=jobs.Manager(app,config,'compose');job='c'*32;folder=manager.paths(job);folder.mkdir(parents=True);(folder/'ready').touch()
        manager.write({'id':job,'phase':'starting','action':'index','options':{'automatic':True,'selection':queue.read(data)['pending']}})
        real_popen=subprocess.Popen
        def fixture_popen(command,**kwargs):return real_popen([*command,'--reserve-bytes','1000000000','--workers','2'],**kwargs)
        with patch.object(manager,'check_storage',return_value=(data,None)),patch.object(manager,'index_python',return_value=Path(sys.executable)),patch.object(jobs.subprocess,'Popen',side_effect=fixture_popen):manager.run(job)
        self.assertEqual(manager.read()['phase'],'completed')
        self.assertEqual(queue.summary(data)['pending'],0)
        self.assertTrue(list((data/'state/pilot/archive-index').glob('*.sqlite')))
        self.assertIn('manual_fr.zim',archive_index.manifest(data/'state/pilot/archive-index'))

    def test_outdated_source_and_broken_database_are_reported_instead_of_silent_empty_results(self):
        archive_index.build_archive(self.zim,self.index)
        plan=retrieval.plan('crevaison',library.search_terms('crevaison'),library.SYNONYMS)
        self.assertTrue(archive_index.search(self.index,plan,source_dir=self.root))
        self.zim.rename(self.root/'removed.zim')
        found=archive_index.search(self.index,plan,source_dir=self.root)
        self.assertFalse(found);self.assertEqual(found.coverage['outdated'],1)
        next(self.index.glob('*.sqlite')).write_bytes(b'not a database')
        found=archive_index.search(self.index,plan)
        self.assertFalse(found);self.assertEqual(found.coverage['failed'],1)

    def test_incompatible_collection_is_not_returned(self):
        archive_index.build_archive(self.zim,self.index)
        plan=retrieval.plan('vélo',library.search_terms('vélo'),library.SYNONYMS,'wikipedia')
        self.assertEqual(archive_index.search(self.index,plan),[])
