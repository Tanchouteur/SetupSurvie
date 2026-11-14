from collections import namedtuple
import shutil
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
from pilot_backup import backup,restore


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
        with patch.object(Path,'read_text',windows_read),patch.object(setup,'ROOT',setup.ROOT),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'verify'),patch.object(setup.Installation,'up') as up:
            restore(dest,kit,work,data)
        self.assertEqual(json.loads((work/'settings.json').read_text(encoding='utf-8'))['fixture_label'],'Réglages de Marc')
        self.assertEqual((work/'inference-paused.json').read_text(),'{"reason":"gaming"}')
        self.assertEqual((data/'catalog/downloaded-content.json').read_text(),receipt.read_text())
        self.assertTrue(up.called)

    def test_restore_rejects_overlapping_targets_before_hashing_or_copying(self):
        with patch('pilot_kit.checked_entries') as entries:
            for data,work in [(self.root/'data',self.root/'data'),(self.root/'data',self.root/'data/private')]:
                with self.assertRaisesRegex(setup.SetupError,'chevauchement'):
                    restore(self.root/'backup',self.root/'kit',work,data)
            entries.assert_not_called()

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

    def test_kit_installs_independent_application_and_retains_transport_copy(self):
        kit=self.root/'kit';application=kit/'app';(application/'scripts').mkdir(parents=True)
        original=application/'scripts/setup.py';original.write_text('transport copy')
        (application/'unlisted-private.txt').write_text('must not be copied')
        setup.write_json(kit/'manifest.json',{'files':[{'path':'app/scripts/setup.py','bytes':original.stat().st_size,'sha256':setup.file_hash(original)}]})
        work=self.root/'installed/private';data=self.root/'installed/data'
        with patch.object(setup,'ROOT',application),patch.object(setup.Installation,'import_images'),patch.object(setup.Installation,'doctor'),patch.object(setup.Installation,'prepare'),patch.object(setup.Installation,'up'),patch.object(setup.Installation,'verify'),patch.object(setup.Installation,'addresses'):
            install(kit,'linux',data,work)
        settings=json.loads((work/'settings.json').read_text())
        installed=self.root/'installed/application'
        self.assertEqual(settings['app_dir'],installed.as_posix())
        self.assertEqual((installed/'scripts/setup.py').read_text(),'transport copy')
        self.assertFalse((installed/'unlisted-private.txt').exists())
        (installed/'scripts/setup.py').write_text('new software')
        self.assertEqual(original.read_text(),'transport copy')
        checked_entries(kit,json.loads((kit/'manifest.json').read_text()))

    def test_windows_kit_configures_shortcuts_from_installed_copy(self):
        kit=self.root/'kit';application=kit/'app';(application/'scripts').mkdir(parents=True)
        script=application/'scripts/setup.py';script.write_text('software fixture')
        files=[script]
        for name in ('windows_background.py','update-windows.ps1','windows-common.ps1','startup-windows.ps1','stop-windows.ps1','register-startup-windows.ps1','content-monitor.ps1','windows_resume.py','register-windows-resume.ps1','start-without-inference.ps1'):
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
