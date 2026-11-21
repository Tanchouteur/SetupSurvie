import errno
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, closing
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
import transfer
from delivery_paths import locked


@contextmanager
def no_services(app,config):
    yield


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.appdir=self.root/'Source é été'/'application';self.data=self.root/'Source é été'/'données';self.work=self.root/'Source é été'/'privé'
        for path in (self.appdir/'scripts',self.data/'state/pilot',self.data/'library/guides',self.work,self.data/'state/openwebui'):path.mkdir(parents=True)
        (self.appdir/'scripts/transfer.py').write_text('# fixture')
        (self.data/'library/guides/été.pdf').write_bytes(b'%PDF fixture')
        self.stamp=1700000000123456789
        os.utime(self.data/'library/guides/été.pdf',ns=(self.stamp,self.stamp))
        self.stamp=(self.data/'library/guides/été.pdf').stat().st_mtime_ns
        with closing(sqlite3.connect(self.data/'state/pilot/pilot.db')) as db:
            db.executescript("CREATE TABLE profiles(id TEXT PRIMARY KEY); INSERT INTO profiles VALUES ('marc-fixed-id'); CREATE TABLE favorites(profile TEXT REFERENCES profiles(id),doc TEXT); INSERT INTO favorites VALUES ('marc-fixed-id','doc:été'); CREATE TABLE archive_index(path TEXT,mtime INTEGER); INSERT INTO archive_index VALUES ('été.pdf',1700000000123456789);")
        with closing(sqlite3.connect(self.data/'state/openwebui/webui.db')) as db:db.execute('CREATE TABLE user(id TEXT PRIMARY KEY)');db.commit()
        self.config={'target':'windows','data_dir':str(self.data),'app_dir':str(self.appdir),'project':'survie-fixture','cpu':False,'secret':'secret-fixture-only','bind':'127.0.0.1','admin_email':'fixture@survie.local','admin_password':'fixture-only','chat_model':'fixture-model'}
        setup.write_json(self.work/'settings.json',self.config)
        setup.write_json(self.work/'inference-paused.json',{'reason':'gaming'})
        setup.write_json(self.data/'catalog.json',{'path':str(self.data/'library/guides/été.pdf')})
        self.app=setup.Installation(self.work);self.dest=self.root/'Nouveau SSD accentué'/'SetupSurvie'

    def copy(self,**kwargs):
        return transfer.transfer(self.app,self.dest,stop_context=no_services,export_images=False,**kwargs)

    def test_complete_relocation_keeps_ids_index_dates_pause_and_source(self):
        before=setup.file_hash(self.data/'state/pilot/pilot.db')
        self.copy();transfer.verify_copy(self.dest);journal=transfer.prepare(self.dest)
        transfer.verify_copy(self.dest)
        config=transfer.read(self.dest/'private/settings.json')
        self.assertEqual(config['data_dir'],(self.dest/'data').as_posix())
        self.assertEqual(config['app_dir'],(self.dest/'application').as_posix())
        self.assertFalse(config['inference_autostart'])
        self.assertEqual((self.dest/'data/library/guides/été.pdf').stat().st_mtime_ns,self.stamp)
        self.assertEqual(before,setup.file_hash(self.dest/'data/state/pilot/pilot.db'))
        self.assertEqual(before,setup.file_hash(self.data/'state/pilot/pilot.db'))
        self.assertTrue((self.work/'inference-paused.json').exists())
        self.assertTrue((self.dest/'private/inference-paused.json').exists())
        self.assertEqual(journal['phase'],'prepared')
        public=(self.dest/'Rapport-transfert.json').read_text()
        self.assertNotIn('secret-fixture-only',public);self.assertNotIn('marc-fixed-id',public)
        with self.assertRaises(setup.SetupError):transfer.guard(self.work)

    @unittest.skipIf(os.name=='nt','Manifestes Ollama dans le conteneur Linux')
    def test_ollama_v2_link_keeps_its_relative_blob_and_is_verified(self):
        blob=self.data/'models/blobs'/('sha256-'+'a'*64)
        link=self.data/'models/manifests-v2/ollama.com/library/model/tag'
        blob.parent.mkdir(parents=True);blob.write_bytes(b'manifest fixture')
        link.parent.mkdir(parents=True);link.symlink_to(os.path.relpath(blob,link.parent))
        self.copy()
        copied=self.dest/'data'/link.relative_to(self.data)
        self.assertEqual(os.readlink(copied),os.readlink(link))
        self.assertEqual(copied.read_bytes(),blob.read_bytes())
        transfer.verify_copy(self.dest)
        copied.unlink();copied.symlink_to(blob)
        with self.assertRaisesRegex(setup.SetupError,'externe'):
            transfer.verify_copy(self.dest)
        link.unlink();link.symlink_to(blob)
        with self.assertRaisesRegex(setup.SetupError,'externe'):
            transfer.inventory({'data':self.data})

    @unittest.skipIf(os.name == 'nt', 'Linux model store fixture')
    def test_smaller_target_uses_verified_compact_model_without_removing_any_model(self):
        import linux_host
        profile = linux_host.compact_cpu_profile()
        standard = setup.VERSIONS['default_model']
        config = {'cpu': True, 'chat_model': standard}
        standard_path = self.data / 'models/manifests/registry.ollama.ai/library/gpt-oss/20b'
        compact_path = self.data / 'models/manifests-v2/ollama.com/library/qwen3/1.7b-q4_K_M'
        blob = self.data / 'models/blobs' / ('sha256-' + 'c' * 64)
        standard_path.parent.mkdir(parents=True)
        standard_path.write_bytes(b'standard fixture')
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b'compact fixture')
        compact_path.parent.mkdir(parents=True)
        compact_path.symlink_to(os.path.relpath(blob, compact_path.parent))
        self.copy()
        inventory = transfer.verify_copy(self.dest)['inventory']
        with patch.object(linux_host, 'compact_cpu_profile', return_value=profile), \
                patch.object(linux_host, 'needs_compact_model', return_value=True):
            transfer.select_restored_cpu_model(config, {'files': []})
            self.assertEqual(config['chat_model'], standard)
            transfer.select_restored_cpu_model(config, inventory)
            self.assertEqual(config['chat_model'], profile['model'])
        for path in (standard_path, compact_path):
            self.assertEqual((self.dest / 'data' / path.relative_to(self.data)).read_bytes(), path.read_bytes())

    @unittest.skipIf(os.name=='nt','Permissions Unix')
    def test_copy_preserves_directory_permissions_under_private_destination(self):
        zim=self.data/'library/zim'
        zim.mkdir();zim.chmod(0o755)
        (zim/'test.zim').write_bytes(b'fixture')
        old=os.umask(0o077)
        try:self.copy()
        finally:os.umask(old)
        self.assertEqual((self.dest/'data/library/zim').stat().st_mode & 0o777,0o755)
        self.assertEqual(self.dest.stat().st_mode & 0o777,0o700)

    def test_youtube_venv_is_excluded_and_its_cache_required(self):
        venv=self.data/'tools/youtube/venv'
        venv.mkdir(parents=True);(venv/'pyvenv.cfg').write_text('fixture')
        with patch('youtube_tools.validate_wheels') as check:
            journal=self.copy()
        check.assert_called_once_with(self.data/'tools/youtube-wheels')
        self.assertIn('data/tools/youtube/venv',journal['inventory']['excluded'])
        self.assertFalse((self.dest/'data/tools/youtube/venv').exists())

    def test_process_death_resumes_published_files_without_recopy(self):
        # Kill only our disposable fixture process after a durable publication.
        script="""import sys,os
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import transfer,setup
from contextlib import contextmanager, closing
@contextmanager
def stopped(a,c):yield
real=transfer.copy_file
counter=0
def copy(*a,**kw):
 global counter
 result=real(*a,**kw);counter+=1
 if counter==2:os._exit(77)
 return result
transfer.copy_file=copy
transfer.transfer(setup.Installation(sys.argv[2]),Path(sys.argv[3]),stop_context=stopped,export_images=False)
"""
        process=subprocess.run([sys.executable,'-c',script,str(Path(transfer.__file__).parent),str(self.work),str(self.dest)],capture_output=True)
        self.assertEqual(process.returncode,77,process.stderr)
        target=self.dest/'application/scripts/transfer.py';timestamp=target.stat().st_mtime_ns
        self.copy();self.assertEqual(target.stat().st_mtime_ns,timestamp);transfer.verify_copy(self.dest)

    def test_disk_full_keeps_resume_and_blocks_start(self):
        original=transfer.copy_file;count=0
        def full(*args,**kwargs):
            nonlocal count
            count+=1
            if count==2:raise OSError(errno.ENOSPC,'fixture full')
            return original(*args,**kwargs)
        with patch.object(transfer,'copy_file',full),self.assertRaises(OSError):self.copy()
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'copying')
        with self.assertRaises(setup.SetupError):transfer.verify_copy(self.dest)
        self.copy();transfer.verify_copy(self.dest)

    def test_windows_can_resume_a_journal_that_inventory_included_a_data_lease(self):
        lease=self.data/'catalog/content.lock.lease'
        with locked(lease.with_name('content.lock')):
            with patch.object(transfer,'data_lease',return_value=False), \
                    self.assertRaises(PermissionError if os.name=='nt' else RuntimeError):
                if os.name=='nt':
                    self.copy()
                else:
                    original=transfer.database_check
                    def unavailable(path):
                        if path==lease:raise RuntimeError('fixture locked')
                        return original(path)
                    with patch.object(transfer,'database_check',side_effect=unavailable):
                        self.copy()
            journal=self.copy()
        self.assertIn('data/catalog/content.lock.lease',journal['inventory']['excluded'])
        self.assertFalse((self.dest/'data/catalog/content.lock.lease').exists())
        transfer.verify_copy(self.dest)

    def test_docker_disks_are_excluded_but_the_recovery_archive_and_template_are_copied(self):
        active=self.data/'docker/main/ext4.vhdx'
        history=self.data/'diagnostics/docker-recovery-2026-11-14/main/ext4.vhdx'
        template=self.data/'tools/DockerDesktop/resources/wsl/ext4.vhdx'
        for path in (active,history,template):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'fixture disk')
        items=transfer.inventory({'data':self.data},[active])
        self.assertIn('data/docker/main/ext4.vhdx',items['excluded'])
        self.assertIn('data/'+history.relative_to(self.data).as_posix(),[r['path'] for r in items['files']])
        self.assertIn('data/'+template.relative_to(self.data).as_posix(),[r['path'] for r in items['files']])
        with self.assertRaisesRegex(setup.SetupError,'non identifié'):
            transfer.inventory({'data':self.data})

    def test_report_distinguishes_moved_docker_data_from_backend_on_source(self):
        def disk(number):
            return {'known':True,'disk':number,'filesystem':'NTFS'}

        evidence={key:[{'path':f'private-{key}-path','physical_disk':disk(number)}]
                  for key,number in {'backend':1,'registration':1,'data_images':2,'wsl_system':2}.items()}
        host={'source':disk(1),'destination':disk(2),'docker_evidence':evidence,'observed_at':123}
        inventory={'files':[]}
        self.dest.mkdir(parents=True)
        transfer.export_report(self.dest,{'target':'windows','phase':'active','inventory':inventory,
                                         'host':{},'docker_last_check':host})
        report=transfer.read(self.dest/'Rapport-transfert.json')
        placement=report['storage']['docker_placement']
        self.assertEqual(placement,{'observed_at':123,'components':{
            'backend':'source','registration':'source','data_images':'destination','wsl_system':'destination',
        }})
        self.assertNotIn('private-backend-path',json.dumps(report))
        self.assertFalse(report['storage']['docker_moved'])
        host['destination']=disk(1)
        self.assertEqual(transfer.docker_placement(host)['components']['backend'],'same_disk')
        evidence['data_images']+=evidence['backend']
        self.assertEqual(transfer.docker_placement(host)['components']['data_images'],'multiple')
        self.assertEqual(transfer.docker_placement({})['components']['backend'],'unknown')

    def test_frozen_inventory_accepts_only_new_empty_wal_for_existing_base(self):
        base={'path':'data/state/pilot.db','bytes':4096}
        wal={'path':'data/state/pilot.db-wal','bytes':0}
        self.assertTrue(transfer.matches_frozen_inventory([base,wal],[base]))
        self.assertFalse(transfer.matches_frozen_inventory([base,{**wal,'bytes':32}],[base]))
        self.assertFalse(transfer.matches_frozen_inventory([base],[base,wal]))
        self.assertFalse(transfer.matches_frozen_inventory([base,{**wal,'path':'orphan-wal'}],[base]))

    def test_retries_return_after_source_is_unlocked_before_final_journal_write(self):
        self.copy()
        real_save=transfer.save
        def crash(dest,journal):
            if journal['phase']=='returned_to_source':raise OSError('fixture outage')
            real_save(dest,journal)
        with patch.object(transfer,'save',side_effect=crash),self.assertRaises(OSError):
            transfer.rollback(self.dest)
        self.assertFalse((self.work/'transfer-guard.json').exists())
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'returning_to_source')
        transfer.rollback(self.dest)
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'returned_to_source')

    def test_interrupted_image_export_keeps_attempt_and_reuses_only_verified_archive(self):
        self.dest.mkdir(parents=True)
        def export(_config,path):
            path.write_bytes(b'fixture Docker image')
            if exporter.call_count==1:
                raise OSError('fixture outage')
            setup.write_json(path.with_name(path.name+'.json'),{'sha256':setup.file_hash(path)})
        with patch.object(self.app,'export_images',side_effect=export) as exporter:
            with self.assertRaises(OSError):
                transfer.copy_images(self.app,self.config,self.dest,lambda *args,**kwargs:None)
            self.assertFalse((self.dest/'images.tar').exists())
            result=transfer.copy_images(self.app,self.config,self.dest,lambda *args,**kwargs:None)
            self.assertEqual(transfer.copy_images(self.app,self.config,self.dest,lambda *args,**kwargs:None),result)
        self.assertEqual(exporter.call_count,2)
        self.assertEqual(len(list(self.dest.glob('images-export-*.tar.pending'))),1)

    def test_partial_prefix_and_corruption(self):
        source=self.data/'large';source.write_bytes(b'0123456789'*100)
        target=self.root/'partial';partial=target.with_name(target.name+'.transfer-part');partial.write_bytes(b'0123456789')
        record={'bytes':source.stat().st_size,'mtime_ns':source.stat().st_mtime_ns}
        transfer.copy_file(source,target,record,lambda *args:None)
        self.assertEqual(target.read_bytes(),source.read_bytes())
        target.unlink();partial.write_bytes(b'bad')
        with self.assertRaises(setup.SetupError):transfer.copy_file(source,target,record,lambda *args:None)
        self.assertEqual(partial.read_bytes(),b'bad')

    def test_changed_source_refused(self):
        with patch.object(transfer,'copy_file',side_effect=OSError('fixture stop')),self.assertRaises(OSError):self.copy()
        (self.data/'new-manual-video.mp4').write_bytes(b'video')
        with self.assertRaisesRegex(setup.SetupError,'source a changé'):self.copy()

    def test_new_source_file_during_copy_prevents_publication(self):
        original=transfer.copy_file
        changed=False
        def mutate(*args,**kwargs):
            nonlocal changed
            digest=original(*args,**kwargs)
            if not changed:
                (self.data/'late-video.mp4').write_bytes(b'fixture late manual addition')
                changed=True
            return digest
        with patch.object(transfer,'copy_file',side_effect=mutate),self.assertRaisesRegex(setup.SetupError,'changé pendant'):
            self.copy()
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'copying')
        self.assertTrue((self.work/'transfer-guard.json').exists())

    def test_corruption_and_foreign_key_failure(self):
        self.copy();(self.dest/'data/library/guides/été.pdf').write_bytes(b'corrupt')
        with self.assertRaises(setup.SetupError):transfer.verify_copy(self.dest)
        with closing(sqlite3.connect(self.data/'state/pilot/pilot.db')) as db:db.execute("INSERT INTO favorites VALUES ('absent','doc')");db.commit()
        with self.assertRaises(setup.SetupError):transfer.database_check(self.data/'state/pilot/pilot.db')

    def test_existing_destination_overlap_symlink_and_ambiguous_names(self):
        self.dest.mkdir(parents=True)
        (self.dest/'precious').write_text('preserve')
        with self.assertRaises(setup.SetupError):self.copy()
        self.assertEqual((self.dest/'precious').read_text(),'preserve')
        with self.assertRaises(setup.SetupError):transfer.plan(self.app,self.data/'inside')
        if os.name!='nt':
            (self.data/'escape').symlink_to(self.root)
            with self.assertRaises(setup.SetupError):transfer.inventory(transfer.roots(self.app,self.config))

    def test_json_paths_only_and_adaptation_interruption(self):
        (self.data/'catalog').mkdir()
        path=self.data/'catalog/jobs.json'
        setup.write_json(path,{'source':str(self.data/'library/guides/été.pdf'),'text':'souvenir '+str(self.data)})
        self.copy()
        original=setup.write_json
        def fail(path,value,**kwargs):
            if Path(path).parts[-2:]==('private','settings.json'):raise OSError('fixture outage')
            return original(path,value,**kwargs)
        with patch.object(setup,'write_json',side_effect=fail),self.assertRaises(OSError):transfer.prepare(self.dest)
        transfer.prepare(self.dest);transfer.verify_copy(self.dest)
        value=transfer.read(self.dest/'data/catalog/jobs.json')
        self.assertEqual(value['source'],(self.dest/'data/library/guides/été.pdf').as_posix())
        self.assertEqual(value['text'],'souvenir '+str(self.data))

    def test_sqlite_wal_is_included(self):
        database=self.data/'state/pilot/wal.db'
        db=sqlite3.connect(database)
        try:
            db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE text(x)');db.execute("INSERT INTO text VALUES ('pending')");db.commit()
            self.copy();transfer.verify_copy(self.dest)
            with closing(sqlite3.connect(self.dest/'data/state/pilot/wal.db')) as target:self.assertEqual(target.execute('SELECT x FROM text').fetchone(),('pending',))
        finally:db.close()

    def test_crashed_wal_keeps_committed_data_without_open_source_connection(self):
        path=self.data/'state/pilot/crashed.db'
        script="import sqlite3,os,sys;db=sqlite3.connect(sys.argv[1]);db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE pending(x)');db.execute(\"INSERT INTO pending VALUES ('kept')\");db.commit();os._exit(0)"
        subprocess.run([sys.executable,'-c',script,str(path)],check=True)
        self.assertTrue(path.with_name('crashed.db-wal').exists())
        self.copy();transfer.verify_copy(self.dest)
        with closing(sqlite3.connect(self.dest/'data/state/pilot/crashed.db')) as db:
            self.assertEqual(db.execute('SELECT x FROM pending').fetchone(),('kept',))

    def test_compose_guard(self):
        setup.write_json(self.work/'transfer-guard.json',{'id':'fixture'})
        for verb in ('up','start','restart','run','exec'):
            with self.assertRaises(setup.SetupError):self.app.compose(self.config,verb)
        with patch.object(setup,'run',return_value='') as run:self.app.compose(self.config,'down');run.assert_called_once()



class ActivationTests(unittest.TestCase):
    setUp=TransferTests.setUp
    copy=TransferTests.copy
    def prepared(self):
        self.config['target']='linux';setup.write_json(self.work/'settings.json',self.config)
        (self.appdir/'scripts/transfer_document_probe.py').write_text('print("fixture")')
        self.copy()
        (self.dest/'images.tar').write_bytes(b'tiny-image-fixture')
        setup.write_json(self.dest/'images.tar.json',{'sha256':setup.file_hash(self.dest/'images.tar')})
        journal=transfer.read(self.dest/'transfer.json')
        journal['images_sha256']=setup.file_hash(self.dest/'images.tar')
        journal['images_manifest_sha256']=setup.file_hash(self.dest/'images.tar.json')
        transfer.save(self.dest,journal);transfer.prepare(self.dest)

    @unittest.skipUnless(sys.platform=='linux','Retrait sur Linux')
    def test_retirement_is_explicit_resumable_and_preserves_docker_and_private_state(self):
        import transfer_retire
        self.prepared()
        journal=transfer.read(self.dest/'transfer.json')
        journal['phase']='active';journal['checks']['mounts']=True
        transfer.save(self.dest,journal)
        docker=self.appdir.parent/'docker';docker.mkdir()
        (docker/'state').write_text('conserver')
        checks=(
            patch.object(transfer_retire,'docker_paths',return_value=[docker]),
            patch.object(transfer_retire,'mounted_paths',return_value=[]),
            patch.object(transfer_retire,'check_destination'),
            patch.object(transfer_retire,'different_filesystem',return_value=True),
        )
        from contextlib import ExitStack
        with ExitStack() as stack:
            for check in checks:stack.enter_context(check)
            transfer_retire.retire(self.dest)
            self.assertTrue(self.appdir.is_dir())
            self.assertNotIn('source_retirement', transfer.read(self.dest/'transfer.json'))
            with self.assertRaises(setup.SetupError):transfer_retire.retire(self.dest,'wrong')
            with patch.object(transfer_retire.shutil,'rmtree',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):transfer_retire.retire(self.dest,journal['id'])
            self.assertFalse(self.appdir.exists())
            with self.assertRaisesRegex(setup.SetupError,'retrait'):transfer.rollback(self.dest)
            transfer_retire.retire(self.dest,journal['id'])
        self.assertFalse(self.data.exists())
        self.assertTrue((self.work/'transfer-guard.json').is_file())
        self.assertTrue((docker/'state').is_file())
        self.assertTrue((self.dest/'data/state/pilot/pilot.db').is_file())
        report=transfer.read(self.dest/'Rapport-transfert.json')
        self.assertEqual(report['source_retirement'],{'application':'removed','data':'removed'})

    def test_activation_fences_source_and_checks_mounts_documents(self):
        if os.name=='nt':self.skipTest('Linux runtime fixture')
        self.prepared()
        def run(command,**kwargs):return 'linux' if 'info' in command else ''
        with patch.object(setup,'ROOT',self.dest/'application'),patch.object(setup,'run',side_effect=run),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'up') as up,patch.object(setup.Installation,'compose',return_value='{"search":"passed","open_document":"passed"}'),patch.object(transfer,'validate_mounts') as mounts:
            transfer.activate(self.dest)
        self.assertFalse((self.dest/'private/transfer-guard.json').exists())
        self.assertTrue((self.work/'transfer-guard.json').exists())
        config=up.call_args.args[0];self.assertFalse(config['inference_autostart'])
        self.assertTrue(transfer.read(self.dest/'transfer.json')['checks']['mounts'])
        mounts.assert_called_once()

    @unittest.skipIf(os.name == 'nt', 'Linux runtime fixture')
    def test_activation_from_other_machine_selects_a_copied_compact_model(self):
        import linux_host
        self.config.update(cpu=True, chat_model=setup.VERSIONS['default_model'])
        profile = linux_host.compact_cpu_profile()
        for model in (self.config['chat_model'], profile['model']):
            name, tag = model.split(':', 1)
            manifest = self.data / 'models/manifests/registry.ollama.ai/library' / name / tag
            manifest.parent.mkdir(parents=True)
            manifest.write_text(model)
        self.prepared()
        self.work.rename(self.work.with_name('source retirée de la VM cible'))
        with patch.object(setup, 'ROOT', self.dest / 'application'), \
                patch.object(setup, 'run', return_value='linux'), \
                patch.object(setup.Installation, 'import_images'), \
                patch.object(setup.Installation, 'up') as up, \
                patch.object(setup.Installation, 'compose', return_value='{}'), \
                patch.object(transfer, 'validate_mounts'), \
                patch.object(linux_host, 'compact_cpu_profile', return_value=profile), \
                patch.object(linux_host, 'needs_compact_model', return_value=True):
            transfer.activate(self.dest)
        self.assertEqual(up.call_args.args[0]['chat_model'], profile['model'])
        self.assertFalse(up.call_args.args[0]['inference_autostart'])
        self.assertEqual(transfer.read(self.dest / 'transfer.json')['phase'], 'active')

    def test_activation_failure_stays_fenced_then_resumes(self):
        if os.name=='nt':self.skipTest('Linux runtime fixture')
        self.prepared()
        def run(command,**kwargs):return 'linux' if 'info' in command else ''
        with patch.object(setup,'ROOT',self.dest/'application'),patch.object(setup,'run',side_effect=run),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'up',side_effect=setup.SetupError('fixture failure')),patch.object(setup.Installation,'compose',return_value=''),patch('control.stop'),patch('discovery.stop'):
            with self.assertRaises(setup.SetupError):transfer.activate(self.dest)
        self.assertTrue((self.dest/'private/transfer-guard.json').exists())
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'activating')
        with patch.object(setup,'ROOT',self.dest/'application'),patch.object(setup,'run',side_effect=run),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'up'),patch.object(setup.Installation,'compose',return_value='{"search":"passed","open_document":"passed"}'),patch.object(transfer,'validate_mounts'),patch('control.stop'),patch('discovery.stop'):
            transfer.activate(self.dest)
        self.assertEqual(transfer.read(self.dest/'transfer.json')['phase'],'active')

    def test_destination_can_move_before_activation(self):
        self.prepared()
        other=self.root/'Encore un autre emplacement accentué'
        self.dest.rename(other);self.dest=other
        transfer.prepare(other);transfer.verify_copy(other)
        self.assertEqual(transfer.read(other/'private/settings.json')['data_dir'],(other/'data').as_posix())

    def test_partial_rollback_needs_no_destination_runtime(self):
        with patch.object(transfer,'copy_file',side_effect=OSError('interruption')),self.assertRaises(OSError):self.copy()
        with patch.object(setup,'run') as run:transfer.rollback(self.dest)
        run.assert_not_called()
        self.assertFalse((self.work/'transfer-guard.json').exists())

    def test_trampoline_uses_copied_portable_python(self):
        self.prepared()
        portable=self.dest/'data/tools/Python312/python.exe'
        portable.parent.mkdir(parents=True);portable.write_bytes(b'fixture-only')
        command=transfer.local_runtime(self.dest)
        self.assertEqual(command[0],str(portable))
        self.assertIn(str(self.dest/'application/scripts/transfer.py'),command)

    def test_external_mounts_are_refused(self):
        fake=setup.Installation(self.work)
        container={'Mounts':[{'Type':'bind','Source':'/unrelated/file'}],'State':{'Health':{'Status':'healthy'}}}
        with patch.object(fake,'compose',return_value='container-fixture'),patch.object(setup,'run',return_value=json.dumps([container])):
            with self.assertRaises(setup.SetupError):transfer.validate_mounts(fake,self.config)


    def test_routing_services_without_docker_healthcheck_are_validated_as_running(self):
        routes=self.data/'library/maps/routing/current';routes.mkdir(parents=True);(routes/'manifest.json').write_text('{}')
        containers=[]
        for service in ('open-webui','kiwix','pilot','portal','router-foot','router-motorcycle','router-car'):
            state={'Running':True}
            if not service.startswith('router-'):state['Health']={'Status':'healthy'}
            containers.append({'Config':{'Labels':{'com.docker.compose.service':service}},
                'Mounts':[{'Type':'bind','Source':str(self.data)}],'State':state})
        with patch.object(self.app,'compose',return_value=' '.join('container-'+str(i) for i in range(7))),patch.object(setup,'run',side_effect=lambda *a,**kw:json.dumps(containers)):
            transfer.validate_mounts(self.app,self.config)
            containers[-1]['State']['Running']=False
            with self.assertRaises(setup.SetupError):transfer.validate_mounts(self.app,self.config)

    def test_video_jobs_generated_tracks_and_speech_cache_are_preserved_together(self):
        state=self.data/'state/pilot';job='audio-fixture-id';track=state/'video-transcriptions'/job/'source.vtt';track.parent.mkdir(parents=True)
        track.write_text('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nDo not open.\n')
        with closing(sqlite3.connect(state/'video-transcriptions.db')) as db:
            db.execute('CREATE TABLE jobs(id TEXT PRIMARY KEY,status TEXT,progress_ms INTEGER)')
            db.execute('INSERT INTO jobs VALUES(?,?,?)',(job,'paused',60000));db.commit()
        french=state/'video-captions'/'translation-fixture-id'/'fr.vtt';french.parent.mkdir(parents=True);french.write_text('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nNe pas ouvrir.\n')
        acquired=state/'video-acquisition'/'provider-fixture-id'/'source.vtt';acquired.parent.mkdir(parents=True);acquired.write_bytes(track.read_bytes())
        provider=acquired.with_name('provider.json');provider.write_text('{"provider":"youtube","human_review":"not_performed"}')
        with closing(sqlite3.connect(state/'video-acquisition.db')) as db:
            db.execute('CREATE TABLE jobs(id TEXT PRIMARY KEY,status TEXT)');db.execute('INSERT INTO jobs VALUES(?,?)',('provider-fixture-id','completed'));db.commit()
        cache=self.data/'state/openwebui/cache/whisper/faster-whisper-small';cache.mkdir(parents=True);(cache/'model.bin').write_bytes(b'tiny-model-fixture-no-inference')
        self.copy();transfer.prepare(self.dest);transfer.verify_copy(self.dest)
        for original in (track,french,acquired,provider,cache/'model.bin'):
            copied=self.dest/'data'/original.relative_to(self.data)
            self.assertEqual(original.read_bytes(),copied.read_bytes())
        with closing(sqlite3.connect(self.dest/'data/state/pilot/video-transcriptions.db')) as db:
            self.assertEqual(db.execute('SELECT * FROM jobs').fetchone(),(job,'paused',60000))
        with closing(sqlite3.connect(self.dest/'data/state/pilot/video-acquisition.db')) as db:
            self.assertEqual(db.execute('SELECT * FROM jobs').fetchone(),('provider-fixture-id','completed'))

    def test_source_rollback_is_refused_during_another_source_operation(self):
        self.copy()
        with transfer.locked(self.work/'update.lock'):
            with self.assertRaises(setup.SetupError):transfer.rollback(self.dest)
        self.assertTrue((self.work/'transfer-guard.json').exists())


if __name__=="__main__":unittest.main()
