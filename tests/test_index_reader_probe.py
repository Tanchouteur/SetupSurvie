"""Isolated reader preflight, categorical failures, and no archive fan-out on failure."""
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import index_reader_probe as probe,index_archives,search_index_tools as tools,setup
import index_locks
from delivery_paths import locked
from pilot import archive_index,durable


class ReaderProbeTests(unittest.TestCase):
    def test_missing_reader_and_native_import_failure_have_no_raw_exception_details(self):
        with patch.object(probe.importlib.metadata,'version',side_effect=importlib.metadata.PackageNotFoundError('PRIVATE PATH')):
            result=probe.probe();self.assertEqual(result['error'],'reader_missing');self.assertNotIn('PRIVATE',json.dumps(result))
        original=__import__
        def failing(name,*args,**kwargs):
            if name=='libzim.reader':raise ImportError('PRIVATE DLL PATH')
            return original(name,*args,**kwargs)
        with patch.object(probe.importlib.metadata,'version',return_value=probe.VERSION),patch('builtins.__import__',side_effect=failing):
            result=probe.probe();self.assertEqual(result['error'],'reader_import');self.assertNotIn('PRIVATE',json.dumps(result))

    def test_reader_api_version_and_sqlite_are_checked(self):
        with patch.object(probe.importlib.metadata,'version',return_value='old'):
            self.assertEqual(probe.probe()['error'],'reader_version')
        reader=SimpleNamespace(Archive=type('Archive',(),{'has_fulltext_index':True,'_get_entry_by_id':object(),'get_metadata':object()}))
        original=__import__
        def fake(name,*args,**kwargs):return reader if name=='libzim.reader' else original(name,*args,**kwargs)
        with patch.object(probe.importlib.metadata,'version',return_value=probe.VERSION),patch('builtins.__import__',side_effect=fake):
            with patch.object(probe.sqlite3,'connect',side_effect=sqlite3.OperationalError('PRIVATE PATH')):
                self.assertEqual(probe.probe()['error'],'fts5_unavailable')
            self.assertTrue(probe.probe()['ok'])
            reader.Archive=type('BadArchive',(),{})
            self.assertEqual(probe.probe()['error'],'reader_api')

    def test_preflight_failure_keeps_previous_indexes_and_never_starts_workers(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);zim=root/'zim';zim.mkdir();state=root/'state';indexes=state/'archive-index';indexes.mkdir(parents=True)
            (indexes/'previous.sqlite').write_bytes(b'previous fixture index')
            durable.write_bytes(indexes/'manifest.json',b'{"schema":1,"archives":{"old.zim":{"status":"ready","archive":"old.zim"}}}')
            for i in range(135):(zim/('fixture'+str(i)+'.zim')).write_bytes(b'small fake archive')
            with patch.object(probe,'probe',return_value={'schema':1,'ok':False,'error':'reader_import'}),patch.object(index_archives,'ProcessPoolExecutor') as pool:
                report=index_archives.run(zim,state,job_id='a'*32);pool.assert_not_called()
            self.assertEqual(report['phase'],'partial');self.assertEqual(report['archives'],135);self.assertEqual(report['completed'],0)
            self.assertEqual(report['error_summary'],{'reader_import':1});self.assertEqual(report['results'],[])
            self.assertEqual((indexes/'previous.sqlite').read_bytes(),b'previous fixture index')
            self.assertIn('old.zim',archive_index.manifest(indexes))

    def test_archive_error_causes_do_not_copy_private_messages(self):
        import errno
        cases=[(archive_index.StorageReserve('PRIVATE'),'storage_reserve'),(archive_index.ArchiveChanged('PRIVATE'),'source_changed'),
               (PermissionError('PRIVATE'),'permission_denied'),(FileNotFoundError('PRIVATE'),'source_missing'),
               (OSError(errno.ENOSPC,'PRIVATE'),'storage_full'),(ImportError('PRIVATE'),'reader_import'),
               (sqlite3.OperationalError('PRIVATE'),'sqlite_error'),(setup.SetupError('PRIVATE'),'index_busy'),(RuntimeError('PRIVATE'),'archive_error')]
        for error,reason in cases:
            result=index_archives.error_record(Path('fixture.zim'),error);self.assertEqual(result['reason'],reason);self.assertNotIn('PRIVATE',json.dumps(result))

    def test_live_orphan_worker_refuses_a_new_pool_without_invalidating_reader(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);zims=root/'zim';zims.mkdir();(zims/'fixture.zim').write_bytes(b'fixture')
            index=root/'state/archive-index';index.mkdir(parents=True)
            (index/'previous.sqlite').write_bytes(b'published index')
            with locked(index_locks.worker(index,zims/'fixture.zim')),patch.object(probe,'probe',return_value={'schema':1,'ok':True}),patch.object(index_archives,'ProcessPoolExecutor') as pool:
                report=index_archives.run(zims,root/'state');pool.assert_not_called()
            self.assertTrue(report['reader_probe']['ok']);self.assertEqual(report['phase'],'partial')
            self.assertEqual(report['error_summary'],{'index_busy':1});self.assertEqual(report['completed'],0)
            self.assertEqual((index/'previous.sqlite').read_bytes(),b'published index')

    def test_registered_delayed_worker_cannot_start_inside_maintenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sources=[Path('first.zim'),Path('second.zim')]
            index_locks.prepare(root,sources)
            self.assertEqual(len(index_locks.workers(root)),2)
            with index_locks.stopped(root),patch.object(archive_index,'build_archive') as build:
                with self.assertRaises(setup.SetupError):index_archives.build_one(sources[0],root)
                build.assert_not_called()
            with patch.object(archive_index,'build_archive',return_value={'status':'ready'}) as build:
                self.assertEqual(index_archives.build_one(sources[0],root)['status'],'ready')
                build.assert_called_once()

    def test_isolated_verification_has_fixed_command_and_safe_failure_report(self):
        with tempfile.TemporaryDirectory() as folder:
            app=setup.Installation(Path(folder)/'private')
            for output,returncode in [({'schema':1,'ok':False,'error':'reader_import','raw':'PRIVATE'},1),({'schema':1,'ok':True,'libzim':tools.VERSION,'fts5':True},0)]:
                with patch.object(tools.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps(output),returncode=returncode)) as run:
                    if returncode:
                        with self.assertRaises(tools.ReaderUnavailable) as error:tools.verify(app)
                        self.assertNotIn('PRIVATE',str(error.exception.report))
                    else:self.assertTrue(tools.verify(app)['ok'])
                    command=run.call_args.args[0];self.assertEqual(command[1:4],['-I','-X','utf8']);self.assertTrue(command[-1].endswith('index_reader_probe.py'))
            with patch.object(tools.subprocess,'run',side_effect=tools.subprocess.TimeoutExpired(['fixture'],30)):
                with self.assertRaises(tools.ReaderUnavailable) as error:tools.verify(app)
                self.assertEqual(error.exception.report['error'],'probe_timeout')
