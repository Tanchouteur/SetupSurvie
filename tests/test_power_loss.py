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
        crash_after_ready(code,[app.work,destination,self.ready],self.ready)
        self.assertFalse((destination/'backup.json').exists())
        complete=self.root/'complete'
        with patch.object(app,'compose'):backup(app,c,complete)
        checked_entries(complete,json.loads((complete/'backup.json').read_text(encoding='utf-8')))
