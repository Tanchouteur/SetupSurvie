from collections import namedtuple
from crash_harness import crash_after_ready
from contextlib import closing
import shutil
import sqlite3
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
from pilot_kit import checked_entries
from pilot_kit import install
from pilot_backup import backup,host_target,restore,restore_copy,start_restored
from delivery_paths import locked
import index_locks
from pilot import archive_index,collection_sort,retrieval


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        # Tiny fixtures must not depend on the CI host having the production
        # 15 GB reserve. Capacity failure cases override this fixture explicitly.
        usage=namedtuple('Usage','total used free')(200_000_000_000,100_000_000_000,100_000_000_000)
        disk=patch.object(shutil,'disk_usage',return_value=usage);disk.start();self.addCleanup(disk.stop)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        # Windows may expose TEMP through an 8.3 alias. The installer resolves
        # paths; compare canonical paths without weakening ownership checks.
        self.root=Path(self.temp.name).resolve()

    def test_kit_rejects_traversal_symlinks_and_altered_contents(self):
        kit=self.root/'kit';kit.mkdir();outside=self.root/'private.txt';outside.write_text('secret')
        entry={'path':'../private.txt','bytes':6,'sha256':setup.file_hash(outside)}
        with self.assertRaises(setup.SetupError):checked_entries(kit,{'files':[entry]})
        try:
            (kit/'linked').symlink_to(outside)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Création de lien non autorisée sur ce système.')
            raise
        with self.assertRaises(setup.SetupError):checked_entries(kit,{'files':[{**entry,'path':'linked'}]})
        file=kit/'data';file.write_text('valid');entry={'path':'data','bytes':5,'sha256':setup.file_hash(file)}
        self.assertEqual(len(checked_entries(kit,{'files':[entry]})),1)
        file.write_text('other')
        with self.assertRaises(setup.SetupError):checked_entries(kit,{'files':[entry]})

    def test_backup_stops_services_preserves_wal_and_restarts_on_error(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        state=Path(c['data_dir'])/'state/pilot'
        (state/'pilot.db').write_text('main')
        (state/'pilot.db-wal').write_text('last committed pages')
        secret=Path(c['data_dir'])/'state/openwebui/cache/model';secret.parent.mkdir(parents=True);secret.write_text('cache omitted')
        dest=self.root/'backup'
        with patch.object(app,'compose') as compose:
            backup(app,c,dest)
        self.assertEqual(compose.call_args_list[0].args[1:],('stop','portal','pilot','open-webui'))
        self.assertEqual(compose.call_args_list[-1].args[1:],('start','open-webui','pilot','portal'))
        self.assertEqual((dest/'data/state/pilot/pilot.db-wal').read_text(),'last committed pages')
        self.assertFalse((dest/'data/state/openwebui/cache').exists())
        checked_entries(dest,json.loads((dest/'backup.json').read_text()))
        with patch.object(app,'compose') as compose,patch('pilot_backup.shutil.copyfile',side_effect=OSError('full')):
            with self.assertRaises(OSError):backup(app,c,self.root/'failed')
            self.assertEqual(compose.call_args_list[-1].args[1:],('start','open-webui','pilot','portal'))

    def test_backup_and_restore_preserve_pause_and_download_receipt_over_kit_defaults(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        c['fixture_label']='Réglages de Marc';setup.write_json(app.settings_path,c,private=True)
        (app.work/'inference-paused.json').write_text('{"reason":"gaming"}')
        receipt=Path(c['data_dir'])/'catalog/downloaded-content.json'
        receipt.write_text('{"schema":1,"items":[],"fixture":"added since kit"}')
        dest=self.root/'backup'
        with patch.object(app,'compose'):backup(app,c,dest)
        kit=self.root/'kit';records=[]
        for name,raw in [('app/scripts/setup.py',b'# fixture'),('payload/catalog/downloaded-content.json',b'{"schema":1,"items":[]}')]:
            path=kit/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            records.append({'path':name,'bytes':len(raw),'sha256':setup.file_hash(path)})
        setup.write_json(kit/'manifest.json',{'files':records})
        work=self.root/'restored/private';data=self.root/'restored/data'
        read_text=Path.read_text
        def windows_read(path,encoding=None,errors=None):
            return read_text(path,encoding=encoding or 'cp1252',errors=errors)
        with patch('pilot_backup.host_target',return_value='linux'),patch.object(Path,'read_text',windows_read),patch.object(setup,'ROOT',setup.ROOT),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'verify'),patch.object(setup.Installation,'up') as up:
            restore(dest,kit,work,data)
        self.assertEqual(json.loads((work/'settings.json').read_text(encoding='utf-8'))['fixture_label'],'Réglages de Marc')
        self.assertEqual((work/'inference-paused.json').read_text(),'{"reason":"gaming"}')
        self.assertEqual((data/'catalog/downloaded-content.json').read_text(),receipt.read_text())
        self.assertTrue(up.called)

    def cross_system_fixture(self, root, source_target):
        app = setup.Installation(root/'source/private')
        config = app.init(source_target, root/'source/data', cpu=source_target == 'linux')
        config.update(lan_host='192.168.1.9', bind='0.0.0.0', docker_rootless=True,
                      routing_image={'id': 'obsolete'}, local_images={'portal': {}},
                      app_dir=str(setup.ROOT))
        setup.write_json(app.settings_path, config, private=True)
        data = Path(config['data_dir'])
        with closing(sqlite3.connect(data/'state/pilot/conversations.sqlite3')) as db:
            db.execute('CREATE TABLE conversation (id TEXT PRIMARY KEY, titre TEXT)')
            db.execute('INSERT INTO conversation VALUES (?, ?)', ('profil-fixe', 'Échange de test'))
            db.commit()
        paths = {
            'state/caddy/host.crt': b'ancien certificat',
            'library/guides/guide.fr.md': b'guide personnel',
        }
        for name, body in paths.items():
            path = data/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        snapshot = root/'snapshot'
        with patch.object(app,'compose'):
            backup(app, config, snapshot)
        kit = root/'kit'
        files = {
            'app/deploy/release.json': (setup.ROOT/'deploy/release.json').read_bytes(),
            'app/deploy/versions.json': (setup.ROOT/'deploy/versions.json').read_bytes(),
            'payload/library/guides/guide.fr.md': b'guide public',
            'payload/library/guides/kit.fr.md': b'autre guide public',
        }
        records = []
        for name, body in files.items():
            path = kit/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            records.append({'path': name, 'bytes': len(body), 'sha256': setup.file_hash(path)})
        setup.write_json(kit/'manifest.json', {'files': records})
        return snapshot, kit, config

    def test_restore_between_systems_recreates_host_settings_and_preserves_private_files(self):
        for source, target in [('windows', 'linux'), ('linux', 'windows'), ('linux', 'linux'), ('windows', 'windows')]:
            with self.subTest(source=source, target=target):
                root = self.root/f'{source}-{target}'
                snapshot, kit, config = self.cross_system_fixture(root, source)
                original_files = {path.relative_to(snapshot): setup.file_hash(path)
                                  for path in snapshot.rglob('*') if path.is_file()}
                work, data = root/'target/private', root/'target/data'
                with patch('pilot_backup.host_target', return_value=target), patch('kit_audit.validate') as audit, \
                     patch('pilot_backup.socket.socket') as socket, patch.object(setup,'run',return_value='linux'), \
                     patch.object(setup.Installation, 'doctor') as doctor, \
                     patch.object(setup.Installation, 'import_images') as images, \
                     patch.object(setup.Installation, 'prepare') as prepare, \
                     patch.object(setup.Installation, 'up'), patch.object(setup.Installation, 'verify'):
                    socket.return_value.__enter__.return_value.connect_ex.return_value = 1
                    restore(snapshot, kit, work, data, target=target)
                audit.assert_called_once()
                doctor.assert_called_once()
                self.assertEqual(images.call_args.args[1], kit/'images.tar')
                self.assertIs(prepare.call_args.args[1], True)
                settings = json.loads((work/'settings.json').read_text(encoding='utf-8'))
                self.assertEqual((settings['target'], settings['cpu']), (target, target == 'linux'))
                self.assertEqual(settings['secret'], config['secret'])
                self.assertEqual(settings['bind'], '127.0.0.1')
                self.assertEqual(settings['app_dir'], (root/'target/application').as_posix())
                self.assertNotEqual(settings['project'], config['project'])
                self.assertFalse({'lan_host', 'docker_rootless', 'local_images', 'routing_image'} & settings.keys())
                self.assertTrue((work/'inference-paused.json').is_file())
                self.assertFalse((data/'state/caddy/host.crt').exists())
                self.assertEqual((data/'library/guides/guide.fr.md').read_bytes(), b'guide personnel')
                self.assertEqual((data/'library/guides/kit.fr.md').read_bytes(), b'autre guide public')
                with closing(sqlite3.connect(data/'state/pilot/conversations.sqlite3')) as db:
                    self.assertEqual(db.execute('SELECT * FROM conversation').fetchall(),
                                     [('profil-fixe', 'Échange de test')])
                self.assertEqual({path.relative_to(snapshot): setup.file_hash(path)
                                  for path in snapshot.rglob('*') if path.is_file()}, original_files)

    def test_cross_system_restore_checks_version_host_and_space_before_writing(self):
        snapshot, kit, _ = self.cross_system_fixture(self.root, 'windows')
        work, data = self.root/'target/private', self.root/'target/data'
        report_path = snapshot/'backup.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        self.assertEqual(report['installation']['version'], json.loads((kit/'app/deploy/release.json').read_text())['version'])
        with patch('pilot_backup.host_target', return_value='linux'), patch('kit_audit.validate'):
            with self.assertRaisesRegex(setup.SetupError, 'système demandé'):
                restore(snapshot, kit, work, data, target='windows')
            with self.assertRaisesRegex(setup.SetupError, 'autre système'):
                restore(snapshot, kit, work, data)
            with patch.object(shutil, 'disk_usage', return_value=namedtuple('Usage', 'total used free')(1, 1, 0)):
                with self.assertRaisesRegex(setup.SetupError, 'Espace insuffisant'):
                    restore(snapshot, kit, work, data, target='linux')
            report['installation']['open_webui'] = 'ancienne version'
            setup.write_json(report_path, report, private=True)
            with self.assertRaisesRegex(setup.SetupError, 'Kit incompatible'):
                restore(snapshot, kit, work, data, target='linux')
            del report['installation']
            setup.write_json(report_path, report, private=True)
            with self.assertRaisesRegex(setup.SetupError, 'Version de sauvegarde inconnue'):
                restore(snapshot, kit, work, data, target='linux')
        self.assertFalse(work.parent.exists())

    def test_cross_system_restore_rejects_case_conflict_between_kit_and_snapshot(self):
        snapshot, kit, _ = self.cross_system_fixture(self.root, 'linux')
        report_path = kit/'manifest.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        entry = next(e for e in report['files'] if e['path'].endswith('/guide.fr.md'))
        new_name = entry['path'].replace('/guides/', '/Guides/')
        path = kit/new_name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            (kit/entry['path']).rename(path)
        entry['path'] = new_name
        # Drop the other kit guide for this case so the conflict spans the two inputs.
        report['files'] = [record for record in report['files'] if not record['path'].endswith('/kit.fr.md')]
        setup.write_json(report_path, report)
        work, data = self.root/'target/private', self.root/'target/data'
        with patch('pilot_backup.host_target', return_value='windows'), patch('kit_audit.validate'):
            with self.assertRaisesRegex(setup.SetupError, 'Conflit de noms'):
                restore(snapshot, kit, work, data, target='windows')
        self.assertFalse(work.parent.exists())

    def test_cross_system_restore_refuses_a_bad_destination_copy_before_activation(self):
        snapshot, kit, _ = self.cross_system_fixture(self.root, 'windows')
        work, data = self.root/'target/private', self.root/'target/data'
        copyfile = shutil.copyfile

        def faulty_copy(source, destination):
            copyfile(source, destination)
            if destination.name == 'guide.fr.md':
                destination.write_bytes(b'X'*destination.stat().st_size)

        with patch('pilot_backup.host_target', return_value='linux'), patch('kit_audit.validate'), \
             patch('pilot_backup.portable_restore_preflight'), patch.object(shutil, 'copyfile', side_effect=faulty_copy), \
             patch.object(setup.Installation, 'up') as up:
            with self.assertRaisesRegex(setup.SetupError, 'Copie non conforme'):
                restore(snapshot, kit, work, data, target='linux')
        up.assert_not_called()
        self.assertFalse((work/'settings.json').exists())
        self.assertEqual((snapshot/'data/library/guides/guide.fr.md').read_bytes(), b'guide personnel')

    def test_interrupted_restore_resumes_copy_or_activation_without_changing_original(self):
        fixture = """
import time
from pathlib import Path
from unittest.mock import patch
import kit_audit
import pilot_backup

snapshot, kit, work, data, ready = map(Path, sys.argv[2:7])
phase = sys.argv[7]
target = pilot_backup.host_target()
original_copy = pilot_backup.restore_copy

def wait_for_cut():
    ready.touch()
    while True:
        time.sleep(1)

def copy(entry, source, destination, *, verify):
    if phase == 'copying' and destination.name == 'guide.fr.md':
        destination.parent.mkdir(parents=True, exist_ok=True)
        from pilot import durable
        durable.write_bytes(destination, b'partial')
        wait_for_cut()
    original_copy(entry, source, destination, verify=verify)

def start(config):
    if phase == 'activating':
        from pilot import durable
        durable.write_bytes(data / 'library/guides/guide.fr.md', b'written after activation')
        wait_for_cut()

with patch.object(kit_audit, 'validate'), patch.object(pilot_backup, 'portable_restore_preflight'), patch.object(pilot_backup, 'restore_copy', copy), patch.object(setup.Installation, 'doctor'), patch.object(setup.Installation, 'import_images'), patch.object(setup.Installation, 'prepare'), patch.object(setup.Installation, 'up', side_effect=start):
    pilot_backup.restore(snapshot, kit, work, data, target=target)
"""
        target = host_target()
        if target is None:
            self.skipTest('Restauration portable disponible sous Windows et Linux')
        for phase in ('copying', 'activating'):
            with self.subTest(phase=phase):
                root = self.root/phase
                snapshot, kit, _ = self.cross_system_fixture(root, target)
                work, data = root/'target/private', root/'target/data'
                ready = root/'ready'
                journal = work.parent/'restauration.json'
                crash_after_ready(fixture, [snapshot, kit, work, data, ready, phase], ready)
                before = json.loads(journal.read_text(encoding='utf-8'))
                self.assertEqual(before['phase'], phase)
                with patch('kit_audit.validate'), patch('pilot_backup.portable_restore_preflight') as preflight, \
                     patch('pilot_backup.restore_copy', wraps=restore_copy) as copy, \
                     patch.object(setup.Installation, 'doctor'), patch.object(setup.Installation, 'import_images') as images, \
                     patch.object(setup.Installation, 'prepare'), patch.object(setup.Installation, 'up') as up, \
                     patch.object(setup.Installation, 'verify'):
                    with self.assertRaisesRegex(setup.SetupError, 'nouveau dossier'):
                        restore(snapshot, kit, work, data, target=target)
                    manifest = kit/'manifest.json'
                    original_manifest = manifest.read_bytes()
                    manifest.write_bytes(original_manifest + b'\n')
                    with self.assertRaisesRegex(setup.SetupError, 'un autre kit'):
                        restore(snapshot, kit, work, data, target=target, resume=True)
                    manifest.write_bytes(original_manifest)
                    restore(snapshot, kit, work, data, target=target, resume=True)
                    up.assert_called_once()
                    self.assertEqual(up.call_args.args[0]['project'], before['project'])
                    self.assertEqual(preflight.call_args.kwargs['activating'], phase == 'activating')
                    if phase == 'copying':
                        copied = {call.args[2].name for call in copy.call_args_list}
                        self.assertIn('guide.fr.md', copied)
                        self.assertNotIn('conversations.sqlite3', copied)
                        images.assert_called_once()
                    else:
                        copy.assert_not_called()
                        images.assert_not_called()
                expected = b'guide personnel' if phase == 'copying' else b'written after activation'
                self.assertEqual((data/'library/guides/guide.fr.md').read_bytes(), expected)
                self.assertEqual((snapshot/'data/library/guides/guide.fr.md').read_bytes(), b'guide personnel')
                self.assertEqual(json.loads(journal.read_text(encoding='utf-8'))['phase'], 'complete')
                with self.assertRaisesRegex(setup.SetupError, 'déjà terminée'):
                    restore(snapshot, kit, work, data, target=target, resume=True)

    def test_restored_launcher_reopens_after_transport_is_removed(self):
        target = host_target()
        if target is None:
            self.skipTest('Restauration portable disponible sous Windows et Linux')
        snapshot, kit, _ = self.cross_system_fixture(self.root, target)
        extension = {'linux': 'desktop', 'windows': 'cmd'}[target]
        name = 'Ouvrir-SetupSurvie.'+extension
        relative = 'app/scripts/restored-launchers/'+name
        script = kit/relative
        script.parent.mkdir(parents=True)
        script.write_bytes((setup.ROOT/'scripts/restored-launchers'/name).read_bytes())
        manifest = json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
        manifest['files'].append({'path': relative, 'bytes': script.stat().st_size, 'sha256': setup.file_hash(script)})
        setup.write_json(kit/'manifest.json', manifest)
        base = self.root/'target'
        work, data = base/'private', base/'data'
        with patch('kit_audit.validate'), patch('pilot_backup.portable_restore_preflight'), \
             patch.object(setup.Installation, 'doctor'), patch.object(setup.Installation, 'import_images'), \
             patch.object(setup.Installation, 'prepare'), patch.object(setup.Installation, 'up'), \
             patch.object(setup.Installation, 'verify'):
            restore(snapshot, kit, work, data, target=target)
        self.assertEqual((base/name).read_bytes(), script.read_bytes())
        if target == 'linux':
            self.assertTrue((base/name).stat().st_mode & 0o100)
        kit.rename(self.root/'kit-ejected')
        snapshot.rename(self.root/'snapshot-ejected')
        with patch.object(setup, 'ROOT', base/'application'), \
             patch.object(setup.Installation, 'up') as up, patch.object(setup.Installation, 'verify') as verify:
            start_restored(base)
            config = setup.Installation(work).load()
            up.assert_called_once_with(config)
            verify.assert_called_once_with(config)
            journal = json.loads((base/'restauration.json').read_text(encoding='utf-8'))
            journal['phase'] = 'activating'
            setup.write_json(base/'restauration.json', journal, private=True)
            up.reset_mock()
            with self.assertRaisesRegex(setup.SetupError, 'doit être terminée'):
                start_restored(base)
            up.assert_not_called()
        self.assertTrue((work/'inference-paused.json').is_file())

    def test_restore_rejects_overlapping_targets_before_hashing_or_copying(self):
        with patch('pilot_kit.checked_entries') as entries:
            for data,work in [(self.root/'data',self.root/'data'),(self.root/'data',self.root/'data/private')]:
                with self.assertRaisesRegex(setup.SetupError,'chevauchement'):
                    restore(self.root/'backup',self.root/'kit',work,data)
            entries.assert_not_called()

    def test_backup_refuses_a_cli_index_owner_before_stopping_services(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        index=Path(c['data_dir'])/'state/pilot/archive-index';index.mkdir()
        (index/'previous.sqlite').write_bytes(b'published index')
        for owner in (index/'operation.lock',index_locks.worker(index,Path('fixture.zim'))):
            with self.subTest(owner=owner.name),locked(owner),patch.object(app,'compose') as compose:
                with self.assertRaisesRegex(setup.SetupError,'opération'):backup(app,c,self.root/'snapshot')
                compose.assert_not_called()
        self.assertFalse((self.root/'snapshot').exists())
        self.assertEqual((index/'previous.sqlite').read_bytes(),b'published index')

    def test_snapshot_excludes_index_writers_and_restores_a_searchable_index(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        index=Path(c['data_dir'])/'state/pilot/archive-index';index.mkdir()
        with archive_index.connect(index/'fixture.sqlite') as db:
            db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
            db.execute('INSERT INTO metadata VALUES(?,?)',('source',json.dumps({'book':'fixture','title':'Fixture','fingerprint':'1:fixture:1:1'})))
            db.execute('CREATE VIRTUAL TABLE articles USING fts5(path UNINDEXED,title,text,language UNINDEXED)')
            db.execute('INSERT INTO articles VALUES(?,?,?,?)',('Bicycle','Vélo fictif','Une crevaison fictive, sans procédure.','fr'));db.commit()
        original=shutil.copyfile;copied=[]
        def copy(source,target,*args,**kwargs):
            if str(source).endswith('fixture.sqlite'):
                with self.assertRaises(setup.SetupError):
                    with locked(index/'operation.lock'):pass
                copied.append('index')
            return original(source,target,*args,**kwargs)
        snapshot=self.root/'snapshot'
        with patch.object(app,'compose'),patch('pilot_backup.shutil.copyfile',side_effect=copy):backup(app,c,snapshot)
        self.assertEqual(copied,['index'])
        self.assertFalse(list(snapshot.rglob('*.lease')))
        # Older snapshots can contain lease files. They are verified as inputs,
        # but ownership must never be restored from them.
        old=snapshot/'data/state/pilot/archive-index/operation.lock.lease';old.write_bytes(b'old lease')
        report=json.loads((snapshot/'backup.json').read_text());report['files'].append({'path':old.relative_to(snapshot).as_posix(),'bytes':old.stat().st_size,'sha256':setup.file_hash(old)})
        setup.write_json(snapshot/'backup.json',report)
        kit=self.root/'kit';script=kit/'app/scripts/setup.py';script.parent.mkdir(parents=True);script.write_bytes(b'# fixture')
        setup.write_json(kit/'manifest.json',{'files':[{'path':'app/scripts/setup.py','bytes':script.stat().st_size,'sha256':setup.file_hash(script)}]})
        work=self.root/'restored/private';data=self.root/'restored/data'
        with patch('pilot_backup.host_target',return_value='linux'),patch.object(setup,'ROOT',setup.ROOT),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'up'),patch.object(setup.Installation,'verify'):
            restore(snapshot,kit,work,data)
        restored=data/'state/pilot/archive-index'
        found=archive_index.search(restored,retrieval.plan('crevaison',['crevaison'],{}))
        self.assertEqual(found[0]['id'],'zim:fixture/Bicycle')
        self.assertFalse((restored/'operation.lock.lease').exists())
        with locked(restored/'operation.lock'):pass

    def test_backup_attempts_service_recovery_after_partial_stop_failure(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        with patch.object(app,'compose',side_effect=[setup.SetupError('stop failure'),None]) as compose:
            with self.assertRaisesRegex(setup.SetupError,'stop failure'):backup(app,c,self.root/'backup')
        self.assertEqual(compose.call_args_list[-1].args[1:],('start','open-webui','pilot','portal'))
        self.assertFalse((self.root/'backup/backup.json').exists())

    def test_backup_refuses_active_background_work_or_transfer_before_stopping_services(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        state=app.work/'library-web/state.json'
        setup.write_json(state,{'phase':'downloading'})
        with patch.object(app,'compose') as compose:
            with self.assertRaisesRegex(setup.SetupError,'pause'):backup(app,c,self.root/'backup')
            compose.assert_not_called()
            setup.write_json(state,{'phase':'paused'})
            lock=Path(c['data_dir'])/'catalog/content.lock';lock.mkdir()
            with self.assertRaisesRegex(setup.SetupError,'opération'):backup(app,c,self.root/'backup')
            compose.assert_not_called()

    def test_manifest_rejects_duplicate_case_aliases_and_windows_reserved_paths(self):
        kit=self.root/'kit';kit.mkdir();path=kit/'valid';path.write_bytes(b'fixture')
        good={'path':'valid','bytes':path.stat().st_size,'sha256':setup.file_hash(path)}
        for records in [[good,good],[good,{**good,'path':'VALID'}],[{**good,'path':'C:private'}],[{**good,'path':'con.txt'}],[{**good,'path':'./valid'}],[{**good,'bytes':True}]]:
            with self.subTest(records=records),self.assertRaises(setup.SetupError):checked_entries(kit,{'files':records})

    def test_restore_requires_settings_verified_by_manifest_before_copying(self):
        source=self.root/'backup';kit=self.root/'kit'
        setup.write_json(source/'backup.json',{'files':[]})
        setup.write_json(source/'private/settings.json',{'unlisted':'must not be trusted'})
        setup.write_json(kit/'manifest.json',{'files':[]})
        with self.assertRaisesRegex(setup.SetupError,'manifeste'):
            restore(source,kit,self.root/'restored/private',self.root/'restored/data')
        self.assertFalse((self.root/'restored').exists())

    def test_backup_refuses_job_start_lock_without_stopping_services(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        lock=app.work/'library-web/operation.lock';lock.mkdir(parents=True)
        with patch.object(app,'compose') as compose:
            with self.assertRaisesRegex(setup.SetupError,'opération'):backup(app,c,self.root/'backup')
            compose.assert_not_called()

    def test_cli_publication_excludes_backup_until_catalog_and_restart_finish(self):
        import content
        from types import SimpleNamespace
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        root=Path(c['data_dir']);args=SimpleNamespace(no_refresh=False,lab=False,jobs=2)
        def attempt_backup(*unused):
            with self.assertRaisesRegex(setup.SetupError,'opération'):
                backup(app,c,self.root/'backup')
            compose.assert_not_called()
        with patch.object(content,'download'),patch.object(content,'check_capacity'),patch.object(content,'install_templates',side_effect=attempt_backup),patch.object(app,'catalog',side_effect=attempt_backup),patch.object(app,'compose',side_effect=attempt_backup) as compose:
            # The restart itself must also remain inside the exclusion window.
            def restart(*unused):
                with self.assertRaisesRegex(setup.SetupError,'opération'):
                    backup(app,c,self.root/'backup')
            compose.side_effect=restart
            content.download_and_refresh(args,app,c,root,[],None,None)
        self.assertFalse((root/'catalog/publication.lock').exists())
        self.assertFalse((self.root/'backup').exists())

    @unittest.skipIf(os.name=='nt','Noms réservés créés seulement sur POSIX.')
    def test_backup_never_marks_nonportable_guide_paths_as_restorable(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        guides=Path(c['data_dir'])/'library/guides'
        for names in [('con.txt',),('Guide.txt','guide.txt')]:
            for name in names:(guides/name).write_bytes(b'fixture')
            dest=self.root/('backup-'+names[0])
            with patch.object(app,'compose'),self.assertRaises(setup.SetupError):backup(app,c,dest)
            self.assertFalse((dest/'backup.json').exists())
            for name in names:(guides/name).unlink()

    def test_backup_refuses_in_place_or_existing_destination(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        with patch.object(app,'compose') as compose:
            for target in [self.root/'data/backup',self.root/'private/backup',self.root/'data']:
                with self.assertRaises(setup.SetupError):backup(app,c,target)
            compose.assert_not_called()

    def test_linux_graphical_kit_creates_a_local_launcher_and_keeps_inference_paused(self):
        from pilot_kit import start_installed
        _, kit, _ = self.cross_system_fixture(self.root, 'linux')
        name = 'Ouvrir-SetupSurvie.desktop'
        relative = 'app/scripts/restored-launchers/'+name
        template = kit/relative
        template.parent.mkdir(parents=True)
        template.write_bytes((setup.ROOT/'scripts/restored-launchers'/name).read_bytes())
        manifest = json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
        manifest['files'].append({'path': relative, 'bytes': template.stat().st_size, 'sha256': setup.file_hash(template)})
        setup.write_json(kit/'manifest.json', manifest)
        base = self.root/'installée'; work, data = base/'private', base/'data'
        with patch.object(setup,'ROOT',kit/'app'), patch('kit_audit.validate'), \
             patch('pilot_backup.portable_restore_preflight'), patch.object(setup.Installation,'import_images'), \
             patch.object(setup.Installation,'doctor'), patch.object(setup.Installation,'prepare') as prepare, \
             patch.object(setup.Installation,'up'), patch.object(setup.Installation,'verify'), \
             patch.object(setup.Installation,'addresses'):
            install(kit,'linux',data,work,cpu=True,graphical=True)
            self.assertTrue(prepare.call_args.kwargs['offline'])
        self.assertEqual((base/name).read_bytes(), template.read_bytes())
        self.assertTrue((work/'inference-paused.json').is_file())
        self.assertEqual((data/'library/guides/guide.fr.md').read_bytes(), b'guide public')
        kit.rename(self.root/'kit-retiré')
        with patch.object(setup,'ROOT',base/'application'), \
             patch.object(setup.Installation,'up') as up, patch.object(setup.Installation,'verify') as verify:
            start_installed(base)
        self.assertTrue(up.call_args.args[0]['kit_linux_graphical'])
        self.assertTrue(up.call_args.args[0]['cpu'])
        verify.assert_called_once_with(up.call_args.args[0])

    def test_kit_installs_independent_application_and_retains_transport_copy(self):
        kit=self.root/'kit';application=kit/'app';(application/'scripts').mkdir(parents=True)
        original=application/'scripts/setup.py';original.write_text('transport copy')
        (application/'unlisted-private.txt').write_text('must not be copied')
        preset=application/'deploy/collection-sort-default.json'
        setup.write_json(preset,collection_sort.Sort(excluded=frozenset({'zim:wiktionary_en_all'})).as_json())
        excluded=kit/'payload/library/zim/wiktionary_en_all_2026-10.zim'
        excluded.parent.mkdir(parents=True)
        excluded.write_bytes(b'excluded archive fixture')
        files=(original,preset,excluded)
        setup.write_json(kit/'manifest.json',{'files':[{'path':p.relative_to(kit).as_posix(),
            'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in files]})
        work=self.root/'installed/private';data=self.root/'installed/data'
        with patch.object(setup,'ROOT',application),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'doctor'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'up'),patch.object(setup.Installation,'verify'),patch.object(setup.Installation,'addresses'):
            install(kit,'linux',data,work,cpu=True)
        settings=json.loads((work/'settings.json').read_text())
        installed=self.root/'installed/application'
        self.assertEqual(settings['app_dir'],installed.as_posix())
        self.assertTrue(settings['cpu'])
        self.assertEqual((installed/'scripts/setup.py').read_text(),'transport copy')
        self.assertFalse((installed/'unlisted-private.txt').exists())
        self.assertFalse((data/'library/zim'/excluded.name).exists())
        self.assertEqual(collection_sort.load(data/'catalog').state('zim:wiktionary_en_all'),'excluded')
        (installed/'scripts/setup.py').write_text('new software')
        self.assertEqual(original.read_text(),'transport copy')
        checked_entries(kit,json.loads((kit/'manifest.json').read_text()))

    def test_windows_kit_configures_shortcuts_from_installed_copy(self):
        kit=self.root/'kit';application=kit/'app';(application/'scripts').mkdir(parents=True)
        script=application/'scripts/setup.py';script.write_text('software fixture')
        files=[script]
        for name in ('windows_background.py','update-windows.ps1','windows-common.ps1','transfer-windows.ps1','startup-windows.ps1','stop-windows.ps1','register-startup-windows.ps1','content-monitor.ps1','windows_resume.py','register-windows-resume.ps1','start-without-inference.ps1'):
            target=application/'scripts'/name
            target.write_text('# tiny updater fixture')
            files.append(target)
        setup.write_json(kit/'manifest.json',{'files':[{'path':'app/'+p.relative_to(application).as_posix(),'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in files]})
        work=self.root/'installed/private';data=self.root/'installed/data'
        with patch.object(setup,'ROOT',application),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'doctor'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'up'),patch.object(setup.Installation,'verify'),patch.object(setup.Installation,'addresses'),patch.object(setup.shutil,'which',return_value='powershell.exe'),patch.object(setup,'run') as shortcuts:
            install(kit,'windows',data,work)
        command=next(call.args[0] for call in shortcuts.call_args_list if any(str(arg).endswith('create-shortcuts.ps1') for arg in call.args[0]))
        self.assertIn(str(work.parent/'application/scripts/create-shortcuts.ps1'),command)
        self.assertEqual(command[-1],'-Startup')
        self.assertNotIn(str(application/'scripts/create-shortcuts.ps1'),command)
        self.assertTrue((work.parent/'Mettre-a-jour-SetupSurvie.cmd').is_file())


if __name__=='__main__':unittest.main()
