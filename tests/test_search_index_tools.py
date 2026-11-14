import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,search_index_tools as tools


class IndexToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.app=setup.Installation(self.root/'private');self.config=self.app.init('linux',self.root/'data',cpu=True)

    def test_offline_missing_wheel_never_attempts_a_download(self):
        with patch.object(tools.subprocess,'run') as run:
            self.assertFalse(tools.prepare(self.app,self.config,offline=True));run.assert_not_called()

    def test_modified_or_unlisted_wheel_is_rejected(self):
        folder=self.root/'wheels';folder.mkdir();wheel=folder/'libzim-3.13.1-fixture.whl';wheel.write_bytes(b'fixture')
        manifest={'libzim':tools.VERSION,'files':[{'path':wheel.name,'bytes':wheel.stat().st_size,'sha256':setup.file_hash(wheel)}]}
        setup.write_json(folder/'manifest.json',manifest);tools.validate_cache(folder)
        wheel.write_bytes(b'changed')
        with self.assertRaises(setup.SetupError):tools.validate_cache(folder)
        wheel.write_bytes(b'fixture');(folder/'unlisted.whl').write_bytes(b'other')
        with self.assertRaises(setup.SetupError):tools.validate_cache(folder)

    def test_wrong_version_marker_is_not_reported_ready(self):
        binary=tools.python(self.app);binary.parent.mkdir(parents=True);binary.touch()
        setup.write_json(self.app.work/'search-tools/reader-ready.json',{'libzim':'old'})
        self.assertFalse(tools.ready(self.app))
        marker=self.app.work/'search-tools/reader-ready.json'
        for value in [[],None,'invalid']:
            marker.write_text(json.dumps(value));self.assertFalse(tools.ready(self.app))

    def test_failed_reader_probe_after_install_does_not_publish_ready_marker(self):
        folder=Path(self.config['data_dir'])/'tools/search-index-wheels';folder.mkdir(parents=True)
        wheel=folder/'libzim-3.13.1-fixture.whl';wheel.write_bytes(b'fixture')
        setup.write_json(folder/'manifest.json',{'libzim':tools.VERSION,'files':[{'path':wheel.name,'bytes':wheel.stat().st_size,'sha256':setup.file_hash(wheel)}]})
        marker=self.app.work/'search-tools/reader-ready.json'
        report={'schema':1,'ok':False,'error':'reader_import'}
        with patch.object(tools.venv.EnvBuilder,'create'),patch.object(tools.subprocess,'run'),patch.object(tools,'verify',side_effect=tools.ReaderUnavailable(report)):
            with self.assertRaises(tools.ReaderUnavailable):tools.prepare(self.app,self.config,offline=True,force=True)
        self.assertFalse(marker.exists())
        valid={'schema':1,'ok':True,'libzim':tools.VERSION,'fts5':True}
        with patch.object(tools.venv.EnvBuilder,'create'),patch.object(tools.subprocess,'run'),patch.object(tools,'verify',return_value=valid):
            self.assertTrue(tools.prepare(self.app,self.config,offline=True,force=True))
        self.assertEqual(json.loads(marker.read_text())['probe'],valid)
