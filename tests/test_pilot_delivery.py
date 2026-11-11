import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup
from pilot_kit import checked_entries
from pilot_backup import backup


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_kit_rejects_traversal_symlinks_and_altered_contents(self):
        kit=self.root/'kit';kit.mkdir();outside=self.root/'private.txt';outside.write_text('secret')
        entry={'path':'../private.txt','bytes':6,'sha256':setup.file_hash(outside)}
        with self.assertRaises(setup.SetupError):checked_entries(kit,{'files':[entry]})
        (kit/'linked').symlink_to(outside)
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

    def test_backup_refuses_in_place_or_existing_destination(self):
        app=setup.Installation(self.root/'private');c=app.init('linux',self.root/'data',cpu=True)
        with patch.object(app,'compose') as compose:
            for target in [self.root/'data/backup',self.root/'private/backup',self.root/'data']:
                with self.assertRaises(setup.SetupError):backup(app,c,target)
            compose.assert_not_called()


if __name__=='__main__':unittest.main()
