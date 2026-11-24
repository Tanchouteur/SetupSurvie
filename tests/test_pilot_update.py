import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from crash_harness import crash_after_ready

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
import pilot_update as update
import library_tasks
from delivery_paths import locked


class Services:
    def __init__(self,app,c,fail=False):self.app,self.c,self.fail=app,c,fail;self.starts=0;self.stops=0
    def stop(self):self.stops+=1
    def start(self):
        self.starts+=1
        if self.starts==1:
            # Simulate startup modifying the DB before a failed health check.
            (Path(self.c['data_dir'])/'state/pilot/pilot.db').write_bytes(b'migrated')
    def check(self,version):
        if self.fail and self.starts==1:raise setup.SetupError('Unhealthy new service')


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name).resolve()
        self.source=self.base/'source';self.root=self.base/'installed';self.data=self.base/'data';self.work=self.base/'private'
        self.source.mkdir();self.root.mkdir()
        for base,version in [(self.source,'0.1.2'),(self.root,'0.1.1')]:
            for name in ('scripts','pilot','portal','deploy'):(base/name).mkdir()
            for path in ('scripts/setup.py','scripts/pilot_update.py','compose.yaml','pilot/app.py','portal/index.html'):(base/path).write_text('version '+version)
            (base/'pilot/app.py').write_text("VERSION='"+version+"'\n")
            (base/'deploy/release.json').write_text(json.dumps({'version':version,'data_schema':1}))
            for name in ('versions.json','discovery-packages.json'):(base/'deploy'/name).write_text('{}')
        with patch.object(setup,'ROOT',self.source):
            self.package=self.base/'update.zip';self.digest=update.build(self.package)
        with patch.object(setup,'ROOT',self.root):
            self.app=setup.Installation(self.work);self.c=self.app.init('linux',self.data,cpu=True)
        self.c['app_dir']=str(self.root);setup.write_json(self.app.settings_path,self.c,private=True)
        for path,body in [('state/pilot/pilot.db',b'old-db'),('state/pilot/archive-index/text.sqlite',b'index-sentinel'),('state/openwebui/webui.db',b'accounts-and-history'),('models/blob',b'large-model-sentinel'),('library/zim/book.zim',b'archive-sentinel'),('state/openwebui/cache/file',b'cache-sentinel')]:
            target=self.data/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        (self.work/'inference-paused.json').write_text('{"reason":"user_gaming"}')
    def run_update(self,fail=False):
        service=Services(self.app,self.c,fail)
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'):
            result=update.apply(self.app,self.package,self.digest,service)
        return result,service
    def assert_static_data(self):
        self.assertEqual((self.data/'models/blob').read_bytes(),b'large-model-sentinel')
        self.assertEqual((self.data/'library/zim/book.zim').read_bytes(),b'archive-sentinel')
        self.assertEqual((self.data/'state/openwebui/webui.db').read_bytes(),b'accounts-and-history')
        self.assertEqual((self.data/'state/openwebui/cache/file').read_bytes(),b'cache-sentinel')
        self.assertEqual((self.data/'state/pilot/archive-index/text.sqlite').read_bytes(),b'index-sentinel')
        self.assertTrue((self.work/'inference-paused.json').exists())

    def test_snapshot_manifest_is_published_only_after_all_copies_are_synced(self):
        from pilot_backup import stopped_backup
        target = self.base/'partial-snapshot'
        with patch.object(update.durable, 'sync_file', side_effect=OSError('simulated write failure')):
            with self.assertRaisesRegex(OSError, 'simulated write failure'):
                stopped_backup(self.app, self.c, target, resume=False, services_stopped=True)
        self.assertFalse((target/'backup.json').exists())

    def test_pruning_keeps_two_complete_copies_and_preserves_unrecognized_folders(self):
        history = self.base/'updates'
        current, older, obsolete, unfinished = (history/(str(i)*32) for i in range(1, 5))
        for index, operation in enumerate((obsolete, older, current), 1):
            release = operation/'previous/deploy/release.json'
            release.parent.mkdir(parents=True)
            release.write_text('{}')
            manifest = operation/'snapshot/backup.json'
            manifest.parent.mkdir()
            manifest.write_text('{}')
            os.utime(manifest, (index, index))
        (unfinished/'new').mkdir(parents=True)
        manual = history/'manual-copy'
        manual.mkdir()
        discarded = history/('discarded-'+'5'*32)
        discarded.mkdir()

        update.prune_update_history(history, history/('9'*32))
        self.assertTrue(obsolete.is_dir())
        self.assertTrue(discarded.is_dir())
        update.prune_update_history(history, current)
        self.assertEqual(set(history.iterdir()), {current, older, unfinished, manual})

    def test_cleanup_between_updates_requires_a_complete_journal_and_healthy_installation(self):
        operation, _ = self.run_update()
        journal = self.work/'update.json'
        saved = json.loads(journal.read_text(encoding='utf-8'))
        with patch.object(setup, 'ROOT', self.root), patch.object(update, 'Services') as services, \
                patch.object(update, 'prune_update_history') as prune:
            setup.write_json(journal, {**saved, 'phase': 'switched'})
            with self.assertRaises(setup.SetupError):
                update.prune_completed_update(self.app)
            services.assert_not_called()
            setup.write_json(journal, saved)
            services.return_value.check.side_effect = setup.SetupError('unhealthy')
            with self.assertRaisesRegex(setup.SetupError, 'unhealthy'):
                update.prune_completed_update(self.app)
            prune.assert_not_called()
            services.return_value.check.side_effect = None
            update.prune_completed_update(self.app)
            prune.assert_called_once_with(operation.parent, operation)

    def test_windows_update_reconciles_only_prepared_routers(self):
        graph=self.data/'library/maps/routing/current/manifest.json'
        graph.parent.mkdir(parents=True)
        config={**self.c,'target':'windows'}
        routers=('router-foot','router-motorcycle','router-car')
        request=(config,'up','-d','--no-deps','--pull','never',*routers)
        with patch.object(self.app,'render'),patch.object(self.app,'compose') as compose, \
                patch('control.start'),patch('discovery.start'):
            update.Services(self.app,config).start()
            self.assertFalse(any(call.args[-3:]==routers for call in compose.call_args_list))
            graph.write_text('{}',encoding='utf-8')
            def start_service(*args,**kwargs):
                if args==request:
                    raise setup.SetupError('OSRM unavailable')
            compose.side_effect=start_service
            with patch('builtins.print') as report:
                update.Services(self.app,config).start()
            compose.assert_called_with(*request,timeout=90)
            self.assertIn('Routage local indisponible',report.call_args.args[0])
            self.assertTrue((self.work/'inference-paused.json').exists())
    def test_update_changes_code_and_preserves_accounts_models_and_pause(self):
        result,service=self.run_update()
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.2')
        self.assertTrue((result/'previous/portal/index.html').is_file());self.assert_static_data()
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'complete')
        self.assertFalse((self.work/'update.lock').exists())

    def test_resume_startup_keeps_data_created_after_the_update(self):
        self.run_update()
        journal=self.work/'update.json'
        state=json.loads(journal.read_text(encoding='utf-8'))
        state['phase']='switched'
        setup.write_json(journal,state)
        db=self.data/'state/pilot/pilot.db'
        db.write_bytes(b'new conversations')
        service=Services(self.app,self.c)
        with patch.object(setup,'ROOT',self.root),patch.object(update,'Services',return_value=service):
            update.resume_startup(self.app)
        self.assertEqual(json.loads(journal.read_text(encoding='utf-8'))['phase'],'complete')
        self.assertEqual(db.read_bytes(),b'new conversations')
        self.assertEqual((service.stops,service.starts),(0,0))

    def test_resume_startup_restores_application_between_renames_without_touching_data(self):
        operation,_=self.run_update()
        journal=self.work/'update.json'
        state=json.loads(journal.read_text(encoding='utf-8'))
        state['phase']='snapshot_ready'
        setup.write_json(journal,state)
        self.root.rename(operation/'new')
        db=self.data/'state/pilot/pilot.db'
        db.write_bytes(b'keep current data')
        with patch.object(setup,'ROOT',operation/'previous'):
            update.resume_startup(self.app)
        self.assertEqual(update.release_at(self.root)['version'],'0.1.1')
        self.assertEqual(json.loads(journal.read_text(encoding='utf-8'))['phase'],'rolled_back')
        self.assertEqual(db.read_bytes(),b'keep current data')

    def test_first_install_wrappers_do_not_break_legacy_update_allowlist(self):
        for name in ('Mettre-a-jour-SetupSurvie.cmd','Installer-SetupSurvie.cmd','1-Preparer-le-PC.cmd','2-Installer-SetupSurvie.cmd'):
            (self.source/name).write_text('first install fixture')
        (self.source/'scripts/install-windows.ps1').write_text('installer implementation fixture')
        with patch.object(setup,'ROOT',self.source):
            package=self.base/'with-installers.zip';digest=update.build(package)
        legacy_files=('README.md','AGENTS.md','compose.yaml','compose.linux.yaml','compose.gpu.yaml')
        with patch.object(update,'FILES',legacy_files):
            manifest=update.unpack(package,digest,self.base/'legacy-unpacked')
        names={entry['path'] for entry in manifest['files']}
        self.assertNotIn('Installer-SetupSurvie.cmd',names)
        self.assertNotIn('Mettre-a-jour-SetupSurvie.cmd',names)
        self.assertNotIn('1-Preparer-le-PC.cmd',names)
        self.assertIn('scripts/install-windows.ps1',names)
    def test_failed_health_restores_previous_code_and_database(self):
        with self.assertRaises(setup.SetupError):self.run_update(fail=True)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assert_static_data()
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'rolled_back')

    def test_snapshot_skips_rebuildable_category_index_and_rollback_keeps_it(self):
        index=self.data/'state/pilot/category-index/book.sqlite'
        index.parent.mkdir(parents=True);index.write_bytes(b'rebuildable-index')
        (index.parent/'progress.json').write_text('{"phase":"completed"}')
        videos=self.data/'state/pilot/videos.db';videos.write_bytes(b'video-index')
        (self.data/'state/pilot/videos.db-wal').write_bytes(b'video-log')
        # Saved by every backup since the collection sort exists; rollback must accept it.
        sort=self.data/'catalog/collection-sort.json'
        sort.parent.mkdir(parents=True,exist_ok=True);sort.write_text('{"schema":1}')
        with self.assertRaisesRegex(setup.SetupError,'Unhealthy'):self.run_update(fail=True)
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'rolled_back')
        operation=next(path for path in (self.root.parent/'updates').iterdir())
        report=json.loads((operation/'snapshot/backup.json').read_text(encoding='utf-8'))
        saved={entry['path'] for entry in report['files']}
        self.assertFalse(any('category-index' in path or 'videos.db' in path for path in saved))
        self.assertIn('data/state/pilot/archive-index/text.sqlite',saved)
        self.assertEqual(videos.read_bytes(),b'video-index')
        self.assertFalse((operation/'snapshot/data/state/pilot/category-index').exists())
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assertEqual(index.read_bytes(),b'rebuildable-index')
        self.assertTrue((index.parent/'progress.json').is_file())
        self.assert_static_data()

    def test_voluntary_rollback_preserves_recent_data_and_allows_updating_again(self):
        # Real package verification and filesystem swaps, simulated services only.
        with patch.object(setup,'ROOT',self.root):
            old_package=self.base/'old.zip';old_digest=update.build(old_package)
        self.run_update()
        recent=b'new conversations after successful update'
        (self.data/'state/pilot/pilot.db').write_bytes(recent)
        service=Services(self.app,self.c);service.starts=1
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'):
            operation=update.apply(self.app,old_package,old_digest,service,rollback=True)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),recent)
        self.assertEqual((operation/'snapshot/data/state/pilot/pilot.db').read_bytes(),recent)
        self.assert_static_data()
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'):
            update.apply(self.app,self.package,self.digest,service)
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),recent)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.2')

    def test_rollback_refuses_newer_or_identical_package_before_stopping(self):
        service=Services(self.app,self.c)
        with patch.object(setup,'ROOT',self.root),self.assertRaises(setup.SetupError):
            update.apply(self.app,self.package,self.digest,service,rollback=True)
        self.assertEqual(service.stops,0)
        self.run_update()
        with patch.object(setup,'ROOT',self.root),self.assertRaises(setup.SetupError):
            update.apply(self.app,self.package,self.digest,service,rollback=True)
        self.assertEqual(service.stops,0)

    def test_failed_voluntary_rollback_restores_recent_data_and_newer_code(self):
        with patch.object(setup,'ROOT',self.root):
            old_package=self.base/'old.zip';old_digest=update.build(old_package)
        self.run_update()
        recent=b'preserve this recent state on failed downgrade'
        (self.data/'state/pilot/pilot.db').write_bytes(recent)
        service=Services(self.app,self.c,fail=True)
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'),self.assertRaises(setup.SetupError):
            update.apply(self.app,old_package,old_digest,service,rollback=True)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.2')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),recent)
        self.assert_static_data()

    def test_active_cli_index_refuses_update_before_stop_or_incomplete_journal(self):
        service=Services(self.app,self.c);index=self.data/'state/pilot/archive-index'
        with locked(index/'operation.lock'),patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose') as compose:
            with self.assertRaisesRegex(setup.SetupError,'opération'):update.apply(self.app,self.package,self.digest,service)
            compose.assert_not_called()
        self.assertEqual(service.stops,0);self.assertFalse((self.work/'update.json').exists())
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1');self.assert_static_data()

    def test_windows_update_waits_for_video_pause_before_stopping_services(self):
        self.c['target']='windows'
        setup.write_json(self.app.settings_path,self.c,private=True)
        manager=library_tasks.Manager(self.app,self.c,'compose')
        job={'id':'a'*32,'action':'video-inventory','phase':'downloading'}
        manager.write(job)
        folder=manager.paths(job['id']);folder.mkdir()
        observed=[]
        def current(*_):
            if (folder/'cancel').exists():
                with self.assertRaises(setup.SetupError),locked(manager.directory/'operation.lock'):
                    pass
                observed.append('paused')
                return {**job,'phase':'paused'}
            return job
        with patch.object(library_tasks.Manager,'current',current),patch('pilot_backup.time.sleep'):
            _,service=self.run_update()
        self.assertEqual(observed,['paused'])
        self.assertEqual(service.stops,1)

    def test_windows_update_refuses_an_active_video_writer_before_stopping(self):
        service=Services(self.app,self.c)
        with locked(self.data/'state/pilot/zim-videos/operation.lock'),patch.object(setup,'ROOT',self.root):
            with self.assertRaisesRegex(setup.SetupError,'opération'):
                update.apply(self.app,self.package,self.digest,service)
        self.assertEqual(service.stops,0)
        self.assertFalse((self.work/'update.json').exists())

    def test_index_lease_survives_rollback_and_excludes_writers_through_all_transitions(self):
        index=self.data/'state/pilot/archive-index';lease=index/'operation.lock.lease';lease.write_bytes(b'lease inode sentinel')
        inode=lease.stat().st_ino;service=Services(self.app,self.c,True);events=[]
        def excluded(event):
            with self.assertRaises(setup.SetupError):
                with locked(index/'operation.lock'):pass
            events.append(event)
        start,stop,check=service.start,service.stop,service.check
        def starting():
            excluded('start');start()
            if service.starts==1:
                (index/'text.sqlite').write_bytes(b'changed during failed startup')
                (index/'new.sqlite').write_bytes(b'not in previous snapshot')
        service.start=starting
        service.stop=lambda:(excluded('stop'),stop())
        service.check=lambda version:(excluded('check'),check(version))
        copy=update.shutil.copyfile
        def copy_checked(source,target,*args,**kwargs):
            if Path(target)==index/'text.sqlite':excluded('restore')
            return copy(source,target,*args,**kwargs)
        with patch.object(setup,'ROOT',self.root),patch.object(self.app,'compose'),patch.object(update.shutil,'copyfile',side_effect=copy_checked):
            with self.assertRaisesRegex(setup.SetupError,'Unhealthy'):update.apply(self.app,self.package,self.digest,service)
        self.assertIn('restore',events);self.assertEqual(events.count('start'),2);self.assertEqual(events.count('stop'),2)
        self.assertEqual(lease.stat().st_ino,inode);self.assertEqual(lease.read_bytes(),b'lease inode sentinel')
        self.assertFalse((index/'new.sqlite').exists());self.assert_static_data()
        with locked(index/'operation.lock'):pass

    def test_manual_recovery_refuses_an_active_index_before_restoring_any_state(self):
        self.run_update();journal=self.work/'update.json';state=json.loads(journal.read_text());state['phase']='switched';setup.write_json(journal,state)
        service=Services(self.app,self.c);index=self.data/'state/pilot/archive-index'
        with locked(index/'operation.lock'),patch.object(setup,'ROOT',self.root):
            with self.assertRaisesRegex(setup.SetupError,'opération'):update.recover(self.app,journal,service)
        self.assertEqual(service.stops,0);self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.2')
        self.assertEqual(json.loads(journal.read_text())['phase'],'switched')
    def test_untrusted_archive_or_traversal_rejected_before_service_stop(self):
        with self.assertRaises(setup.SetupError):update.unpack(self.package,'0'*64,self.base/'staged')
        with zipfile.ZipFile(self.package,'a') as archive:archive.writestr('app/../../secret',b'bad')
        with self.assertRaises(setup.SetupError):update.unpack(self.package,setup.file_hash(self.package),self.base/'staged')
        self.assertFalse((self.base/'secret').exists())
    def test_dependency_change_rejected_without_stopping_service(self):
        (self.root/'deploy/versions.json').write_text('{"different":true}');service=Services(self.app,self.c)
        with patch.object(setup,'ROOT',self.root),self.assertRaises(setup.SetupError):update.apply(self.app,self.package,self.digest,service)
        self.assertEqual(service.stops,0);self.assert_static_data()
    def test_development_checkout_and_repeat_refused(self):
        (self.root/'.git').mkdir()
        with self.assertRaises(setup.SetupError),patch.object(setup,'ROOT',self.root):update.apply(self.app,self.package,self.digest)
        (self.root/'.git').rmdir();self.run_update()
        with self.assertRaises(setup.SetupError):self.run_update()
    def test_finished_update_recovery_never_reverts_new_user_data(self):
        self.run_update();(self.data/'state/pilot/pilot.db').write_bytes(b'new-conversation')
        with self.assertRaises(setup.SetupError):update.recover(self.app,self.work/'update.json',Services(self.app,self.c))
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'new-conversation')
    def test_power_cut_after_code_rename_is_recoverable_from_saved_copy(self):
        operation,service=self.run_update()
        j=json.loads((self.work/'update.json').read_text());j['phase']='switched'
        setup.write_json(self.work/'update.json',j,private=True)
        # Recovery after a power cut uses the script in updates/<id>/previous.
        with patch.object(setup,'ROOT',operation/'previous'):
            update.recover(self.app,self.work/'update.json',service)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assert_static_data()

    def assert_abrupt_cut_recovery(self, point):
        if point.startswith('rollback'):
            self.run_update()
            journal=json.loads((self.work/'update.json').read_text())
            journal['phase']='switched';setup.write_json(self.work/'update.json',journal,private=True)
        ready=self.base/'ready'
        code='''
from pathlib import Path
import time
import pilot_update as update
from pilot import durable
base=Path(sys.argv[2]).resolve();point=sys.argv[3];ready=Path(sys.argv[4])
root=base/'installed';work=base/'private';data=base/'data'
app=setup.Installation(work);config=app.load();setup.ROOT=root
app.compose=lambda *args,**kwargs:None
class Services:
    c=config
    def stop(self):pass
    def start(self):pass
    def check(self,version):pass
def stop_here():
    ready.touch();time.sleep(60)
original=durable.publish
def publish(source,target):
    original(source,target)
    source=Path(source);target=Path(target)
    if point=='between-renames' and source==root:stop_here()
    if point=='after-renames' and source.name=='new' and target==root:stop_here()
    if point=='rollback-rename' and source.name=='previous' and target==root:stop_here()
durable.publish=publish
copy=update.shutil.copyfile
def interrupted_copy(source,target,*args,**kwargs):
    if point=='rollback-copy' and Path(target)==data/'state/pilot/pilot.db':
        Path(target).write_bytes(b'torn fixture');stop_here()
    return copy(source,target,*args,**kwargs)
update.shutil.copyfile=interrupted_copy
if point.startswith('rollback'):
    update.recover(app,work/'update.json',Services())
else:
    package=base/'update.zip'
    update.apply(app,package,setup.file_hash(package),Services())
'''
        crash_after_ready(code,[self.base,point,ready],ready)
        with self.assertRaisesRegex(setup.SetupError,'interrompue'),patch.object(self.app,'compose') as compose:
            self.app.up(self.c)
        compose.assert_not_called()
        services=Services(self.app,self.c);services.starts=1
        with patch.object(setup,'ROOT',self.root):
            update.recover(self.app,self.work/'update.json',services)
        self.assertEqual((self.root/'portal/index.html').read_text(),'version 0.1.1')
        self.assertEqual((self.data/'state/pilot/pilot.db').read_bytes(),b'old-db')
        self.assertEqual(json.loads((self.work/'update.json').read_text())['phase'],'rolled_back')
        self.assert_static_data()

    def test_kill_between_application_directory_renames(self):
        self.assert_abrupt_cut_recovery('between-renames')

    def test_kill_after_new_application_directory_rename(self):
        self.assert_abrupt_cut_recovery('after-renames')

    def test_kill_during_rollback_directory_rename_then_repeat_recovery(self):
        self.assert_abrupt_cut_recovery('rollback-rename')

    def test_kill_during_rollback_database_copy_then_repeat_recovery(self):
        self.assert_abrupt_cut_recovery('rollback-copy')


class KiwixStartupTests(unittest.TestCase):
    def test_kiwix_start_period_covers_a_large_library_within_the_update_wait(self):
        import re
        text=(Path(__file__).resolve().parents[1]/'compose.yaml').read_text(encoding='utf-8')
        block=text.split('\n  kiwix:\n',1)[1].split('\n  pilot:\n',1)[0]
        seconds=int(re.search(r'start_period: (\d+)s',block).group(1))
        wait=int(re.search(r"'--wait-timeout','(\d+)'",(Path(update.__file__)).read_text(encoding='utf-8')).group(1))
        # 210 archives took about 100 s on Marc's PC; an update failed at 130 s.
        self.assertGreaterEqual(seconds,300)
        self.assertLess(seconds,wait)


if __name__=='__main__':unittest.main()
