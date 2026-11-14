import json
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import setup
import content
import delivery_paths
from pilot import durable, store
from crash_harness import crash_after_ready


class PowerLossTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.ready = self.root / 'ready'

    def test_os_lease_releases_on_kill_and_blocks_other_writers_while_alive(self):
        lock = self.root / 'operation.lock'
        code = '''
from pathlib import Path
import time
from delivery_paths import locked
with locked(Path(sys.argv[2])):
    Path(sys.argv[3]).touch()
    time.sleep(60)
'''
        def active(process):
            with self.assertRaises(setup.SetupError):
                with content.locked(lock):pass
            self.assertTrue(delivery_paths.process_alive(process.pid))
        crash_after_ready(code, [lock, self.ready], self.ready, active)
        with content.locked(lock):
            with self.assertRaises(setup.SetupError):
                with delivery_paths.locked(lock):pass
        self.assertTrue(lock.with_name(lock.name + '.lease').exists())

    def test_identified_dead_legacy_lock_is_reclaimed_but_live_owner_is_preserved(self):
        lock = self.root / 'legacy.lock'
        code = '''
from pathlib import Path
import os,time,discovery
lock=Path(sys.argv[2]);lock.mkdir()
setup.write_json(lock/'owner.json',{'pid':os.getpid(),'identity':discovery.identity(os.getpid())})
Path(sys.argv[3]).touch()
time.sleep(60)
'''
        def active(process):
            with self.assertRaises(setup.SetupError):
                with delivery_paths.locked(lock):pass
        crash_after_ready(code, [lock, self.ready], self.ready, active)
        with delivery_paths.locked(lock):pass
        self.assertFalse(lock.exists())

    def test_atomic_state_is_complete_before_and_after_publication_crashes(self):
        target = self.root / 'settings.json'
        code = '''
from pathlib import Path
import time
from pilot import durable
original=durable.publish
def stop(source,target):
    if sys.argv[4]=='after':original(source,target)
    Path(sys.argv[3]).touch()
    time.sleep(60)
durable.publish=stop
setup.write_json(Path(sys.argv[2]),{'value':'nouveau réglage'},private=True)
'''
        for point, expected in [('before', 'old'), ('after', 'nouveau réglage')]:
            with self.subTest(point=point):
                setup.write_json(target, {'value': 'old'}, private=True)
                crash_after_ready(code, [target, self.ready, point], self.ready)
                self.assertEqual(json.loads(target.read_text(encoding='utf-8')), {'value': expected})
                setup.write_json(target, {'value': 'retry'}, private=True)
                self.assertEqual(json.loads(target.read_text()), {'value': 'retry'})
                if os.name != 'nt':self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_failed_sync_never_replaces_previous_settings(self):
        target = self.root / 'settings.json'
        setup.write_json(target, {'value': 'old'})
        with patch.object(durable.os, 'fsync', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):setup.write_json(target, {'value': 'new'})
        self.assertEqual(json.loads(target.read_text()), {'value': 'old'})

    def test_new_directory_entries_are_synced_before_state_publication(self):
        target=self.root/'new'/'nested'/'settings.json'
        events=[];publish=durable.publish
        sync_directory=durable.sync_directory
        def sync(path):
            events.append(Path(path));sync_directory(path)
        def checked_publish(source,destination):
            self.assertIn(self.root,events)
            self.assertIn(self.root/'new',events)
            publish(source,destination)
        with patch.object(durable,'sync_directory',side_effect=sync),patch.object(durable,'publish',side_effect=checked_publish):
            setup.write_json(target,{'complete':True})
        self.assertTrue(json.loads(target.read_text())['complete'])

    def test_sqlite_survives_kill_with_committed_messages_and_explicitly_paused_jobs(self):
        code = '''
from pathlib import Path
import time
from pilot import store
store.ROOT=Path(sys.argv[2]);store.init()
with store.connect() as db:
    assert db.execute('PRAGMA synchronous').fetchone()[0]==2
    db.execute("INSERT INTO conversations VALUES('c','u','fixture',0)")
    db.execute("INSERT INTO messages(conversation_id,role,content,created) VALUES('c','user','committed',0)")
    db.execute("INSERT INTO jobs VALUES('j','u','c','quick','running','partial','[]',NULL,0,0)")
    db.execute("INSERT INTO translations VALUES('t','u','c','s','fixture','quick','running',NULL,0,0)")
    db.execute("INSERT INTO translation_parts VALUES('t',0,1,'hello','bonjour','done','fixture')")
with store.connect() as db:
    db.execute("UPDATE messages SET content='not committed'")
    Path(sys.argv[3]).touch()
    time.sleep(60)
'''
        state = self.root / 'state'
        crash_after_ready(code, [state, self.ready], self.ready)
        with patch.object(store, 'ROOT', state):
            store.init()
            with store.connect() as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(db.execute('SELECT content FROM messages').fetchone()[0], 'committed')
                self.assertEqual(db.execute('SELECT status FROM jobs').fetchone()[0], 'interrupted')
                self.assertEqual(db.execute('SELECT status FROM translations').fetchone()[0], 'paused')
                self.assertEqual(db.execute('SELECT translated FROM translation_parts').fetchone()[0], 'bonjour')

    def test_pending_update_blocks_start_before_any_service_or_inference(self):
        app = setup.Installation(self.root / 'private')
        setup.write_json(app.work / 'update.json', {'phase': 'snapshot_ready'}, private=True)
        with patch.object(app, 'catalog') as catalog, patch.object(app, 'start_native') as native, patch.object(app, 'compose') as compose:
            with self.assertRaisesRegex(setup.SetupError, 'Recover'):app.up({})
            for raw in ('{torn','[]'):
                (app.work/'update.json').write_text(raw)
                with self.assertRaises(setup.SetupError):app.up({})
            catalog.assert_not_called();native.assert_not_called();compose.assert_not_called()

    def test_download_partial_resumes_after_real_process_kill_without_publishing_early(self):
        code='''
from pathlib import Path
import hashlib,time,content
root=Path(sys.argv[2]);raw=b'x'*(1024*1024);half=len(raw)//2
item={'path':'library/zim/fixture.zim','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'url':'https://example.org/fixture'}
class Response:
    status=206
    headers={'Content-Range':f'bytes 0-{len(raw)-1}/{len(raw)}'}
    first=True
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def geturl(self):return item['url']
    def read(self,count):
        if self.first:self.first=False;return raw[:half]
        Path(sys.argv[3]).touch();time.sleep(60)
with content.locked(root/'catalog/content.lock'):
    content.transfer(root,item,opener=lambda *args,**kwargs:Response())
'''
        crash_after_ready(code,[self.root,self.ready],self.ready)
        target=self.root/'library/zim/fixture.zim'
        partial=target.with_name(target.name+'.part')
        raw=b'x'*(1024*1024);half=len(raw)//2
        self.assertFalse(target.exists());self.assertEqual(partial.stat().st_size,half)
        item={'path':'library/zim/fixture.zim','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'url':'https://example.org/fixture'}
        class Response(io.BytesIO):
            status=206
            headers={'Content-Range':f'bytes {half}-{len(raw)-1}/{len(raw)}'}
            def geturl(self):return item['url']
        def opener(request,**kwargs):
            self.assertEqual(request.headers['Range'],f'bytes={half}-')
            return Response(raw[half:])
        with content.locked(self.root/'catalog/content.lock'):
            self.assertEqual(content.transfer(self.root,item,opener),'downloaded')
        self.assertEqual(target.read_bytes(),raw);self.assertFalse(partial.exists())

    def test_paused_start_reconciles_linux_docker_without_starting_inference(self):
        import control,discovery
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        setup.write_json(app.work/'inference-paused.json',{'reason':'gaming'},private=True)
        with patch.object(app,'catalog'),patch.object(control,'start'),patch.object(discovery,'start'),patch.object(app,'start_native') as native,patch.object(app,'compose') as compose:
            app.up(c)
        native.assert_not_called()
        self.assertEqual(compose.call_args_list[0].args[1:],('stop','ollama'))
        self.assertNotIn('ollama',compose.call_args_list[1].args[2:])
        self.assertTrue((app.work/'inference-paused.json').exists())

    def test_killed_backup_is_not_announced_complete_and_new_backup_can_run(self):
        from pilot_backup import backup
        from pilot_kit import checked_entries
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        (Path(c['data_dir'])/'state/pilot/pilot.db').write_bytes(b'fixture only')
        destination=self.root/'unfinished'
        code='''
from pathlib import Path
import time
from pilot_backup import backup
app=setup.Installation(sys.argv[2]);config=app.load();app.compose=lambda *args,**kwargs:None
original=setup.write_json
def write(path,value,**kwargs):
    if Path(path).name=='backup.json':
        Path(sys.argv[4]).touch();time.sleep(60)
    return original(path,value,**kwargs)
setup.write_json=write
backup(app,config,sys.argv[3])
'''
        index_lock=Path(c['data_dir'])/'state/pilot/archive-index/operation.lock'
        def index_excluded(process):
            with self.assertRaises(setup.SetupError):
                with delivery_paths.locked(index_lock):pass
        crash_after_ready(code,[app.work,destination,self.ready],self.ready,index_excluded)
        with delivery_paths.locked(index_lock):pass
        self.assertTrue(index_lock.with_name(index_lock.name+'.lease').exists())
        self.assertFalse((destination/'backup.json').exists())
        complete=self.root/'complete'
        with patch.object(app,'compose'):backup(app,c,complete)
        checked_entries(complete,json.loads((complete/'backup.json').read_text(encoding='utf-8')))

    def test_orphan_index_worker_blocks_snapshot_until_its_process_dies(self):
        from pilot_backup import backup
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        index=Path(c['data_dir'])/'state/pilot/archive-index';index.mkdir()
        (index/'published.sqlite').write_bytes(b'previous fixture index')
        code='''
from pathlib import Path
import time,index_archives
def extract(source,root,**options):
    Path(sys.argv[3]).touch();time.sleep(60)
index_archives.archive_index.build_archive=extract
index_archives.build_one(Path('fixture.zim'),Path(sys.argv[2]))
'''
        def active(process):
            # The supervisor's operation lease is free, but a real worker owns
            # its per-archive lease and still prevents maintenance.
            with delivery_paths.locked(index/'operation.lock'):pass
            with patch.object(app,'compose') as compose:
                with self.assertRaisesRegex(setup.SetupError,'opération'):backup(app,c,self.root/'blocked')
                compose.assert_not_called()
        crash_after_ready(code,[index,self.ready],self.ready,active)
        with patch.object(app,'compose'):backup(app,c,self.root/'complete')
        self.assertEqual((self.root/'complete/data/state/pilot/archive-index/published.sqlite').read_bytes(),b'previous fixture index')

    def graph(self,folder,body):
        file=folder/'foot/network.osrm';file.parent.mkdir(parents=True)
        file.write_bytes(body)
        setup.write_json(folder/'manifest.json',{'complete':True,'engine':'OSRM','files':[
            {'path':'foot/network.osrm','bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}]})

    def test_routing_graph_publication_survives_kills_before_and_after_directory_moves(self):
        import routing_prepare
        code='''
from pathlib import Path
import time,routing_prepare
from pilot import durable
root=Path(sys.argv[2]);point=sys.argv[3];ready=Path(sys.argv[4])
directory=root/'library/maps/routing';current=directory/'current';staging=directory/'.prepare-fixture'
original=durable.publish
def stop_here():ready.touch();time.sleep(60)
def publish(source,target):
    source=Path(source);target=Path(target)
    if point=='first' and source==staging:stop_here()
    original(source,target)
    if point=='between' and source==current:stop_here()
    if point=='after' and source==staging:stop_here()
durable.publish=publish
routing_prepare.publish_graph(staging,root)
'''
        for point,expected in [('between',b'old graph'),('after',b'new graph'),('first',b'new graph')]:
            with self.subTest(point=point):
                root=self.root/point;directory=root/'library/maps/routing'
                if point!='first':self.graph(directory/'current',b'old graph')
                self.graph(directory/'.prepare-fixture',b'new graph')
                crash_after_ready(code,[root,point,self.ready],self.ready)
                routing_prepare.recover_publication(root)
                self.assertEqual((directory/'current/foot/network.osrm').read_bytes(),expected)
                routing_prepare.recover_publication(root)
                self.assertEqual(json.loads((directory/'publication.json').read_text())['phase'],'complete')

    def test_routing_recovery_preserves_unverifiable_data_instead_of_resetting(self):
        import routing_prepare
        directory=self.root/'library/maps/routing'
        self.graph(directory/'current',b'expected')
        target=directory/'current/foot/network.osrm';target.write_bytes(b'torn')
        setup.write_json(directory/'publication.json',{'phase':'pending','previous':'previous-missing','staging':'.prepare-missing'})
        with self.assertRaises(setup.SetupError):routing_prepare.recover_publication(self.root)
        self.assertEqual(target.read_bytes(),b'torn')
