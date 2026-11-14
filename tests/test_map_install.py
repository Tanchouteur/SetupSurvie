"""Map installation boundaries: no false completion, no implicit offline downloads."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock,patch
import urllib.error
import zipfile
from datetime import date

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import map_install
import maps as preparation
import search_index_tools
import setup


class MapInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def test_offline_missing_maps_are_reported_without_downloading(self):
        with patch.object(map_install,'tool') as fetch:
            self.assertFalse(map_install.ensure(self.root,offline=True))
        fetch.assert_not_called()
        self.assertEqual(json.loads((self.root/'catalog/map-installation.json').read_text())['status'],'missing')

    def test_verified_existing_maps_need_no_network_and_corruption_is_detected(self):
        spec={'maps':[{'id':'test','bbox':[1,2,3,4],'maxzoom':13}]}
        folder=self.root/'library/maps';folder.mkdir(parents=True)
        raw=b'PMTiles\x03'+b'valid-fixture'
        (folder/'test.pmtiles').write_bytes(raw)
        record={**spec['maps'][0],'path':'test.pmtiles','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        setup.write_json(folder/'manifest.json',{'maps':[record]})
        with patch.object(map_install,'recipe',return_value=spec),patch.object(map_install,'tool') as tool:
            self.assertTrue(map_install.ensure(self.root));tool.assert_not_called()
        (folder/'test.pmtiles').write_bytes(raw[:-1]+b'!')
        self.assertFalse(map_install.installed(self.root,spec))

    def test_windows_binary_is_derived_from_the_checked_archive(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('pmtiles.exe',b'checked-executable')
        raw=stream.getvalue();spec={'tool':{'version':'test','windows_x86_64_url':'https://example.org/tool.zip','windows_sha256':hashlib.sha256(raw).hexdigest()}}
        response=MagicMock();response.__enter__.return_value.read.return_value=raw
        with patch.object(map_install.platform,'system',return_value='Windows'),patch.object(map_install.platform,'machine',return_value='AMD64'),patch.object(map_install,'network_open',return_value=response):
            target=map_install.tool(self.root,spec)
            self.assertEqual(target.read_bytes(),b'checked-executable')
            target.write_bytes(b'altered-cache')
            self.assertEqual(map_install.tool(self.root,spec).read_bytes(),b'checked-executable')
            spec['tool']['windows_sha256']='0'*64
            with self.assertRaisesRegex(setup.SetupError,'modifiée'):map_install.tool(self.root,spec)

    def test_expired_daily_source_uses_recent_official_build_with_actual_date(self):
        spec={'source':'https://build.protomaps.com/20260101.pmtiles','edition':'2026-01-01'}
        response=MagicMock();response.__enter__.return_value.status=206
        response.__enter__.return_value.headers={'Content-Range':'bytes 0-126/1000'}
        response.__enter__.return_value.read.return_value=b'PMTiles\x03'
        def opener(request,timeout):
            if request.full_url==spec['source']:raise urllib.error.HTTPError(request.full_url,404,'expired',{},None)
            return response
        resolved=preparation.resolve_source(spec,opener=opener,today=date(2026,11,13))
        self.assertEqual(resolved['edition'],'2026-11-13')
        self.assertEqual(resolved['source'],'https://build.protomaps.com/20261113.pmtiles')

    def test_incomplete_extraction_is_preserved_for_a_safe_new_attempt(self):
        partial=self.root/'library/maps/test.pmtiles.part';partial.parent.mkdir(parents=True);partial.write_bytes(b'incomplete')
        preparation.preserve_partial(self.root,partial)
        self.assertFalse(partial.exists())
        saved=list((self.root/'diagnostics/maps-partials').iterdir())
        self.assertEqual([p.read_bytes() for p in saved],[b'incomplete'])

    def test_default_install_requires_maps_before_reporting_success(self):
        app=MagicMock();config={'data_dir':str(self.root),'chat_model':'already-present','target':'windows'}
        app.init.return_value=config;app.request.return_value={'models':[{'name':'already-present'}]}
        with patch.object(search_index_tools,'prepare',return_value=True),patch.object(setup,'Installation',return_value=app),patch.object(map_install,'ensure',side_effect=setup.SetupError('map failure')) as ensure:
            with self.assertRaisesRegex(setup.SetupError,'map failure'):
                setup.main(['--work-dir',str(self.root/'work'),'install','--target','windows'])
        ensure.assert_called_once_with(self.root,offline=False)
        app.verify.assert_not_called();app.install_windows_shortcuts.assert_not_called()

    def test_offline_install_never_silently_switches_to_online_map_preparation(self):
        app=MagicMock();app.init.return_value={'data_dir':str(self.root),'target':'windows'}
        with patch.object(search_index_tools,'prepare',return_value=True),patch.object(setup,'Installation',return_value=app),patch.object(map_install,'ensure',return_value=False) as ensure:
            setup.main(['--work-dir',str(self.root/'work'),'install','--target','windows','--offline'])
        ensure.assert_called_once_with(self.root,offline=True)

    def test_poi_failure_keeps_verified_relief_and_is_explicit_in_the_report(self):
        import geography_data
        spec={'maps':[],'geography':{'lat':43.18,'lon':6.04,'radius_km':25,'terrain':True}}
        def ready(root,options,**kwargs):return None if kwargs.get('require_places') else {'terrain':True}
        with patch.object(map_install,'recipe',return_value=spec),patch.object(map_install,'installed',return_value=True),patch.object(map_install,'geography_ready',side_effect=ready),patch.object(geography_data,'prepare',side_effect=TimeoutError('provider unavailable')):
            self.assertTrue(map_install.ensure(self.root))
        report=json.loads((self.root/'catalog/map-installation.json').read_text())
        self.assertTrue(report['elevation_included'])
        self.assertEqual(report['places_status'],'missing')
        self.assertIn('provider unavailable',report['places_error'])


if __name__=='__main__':unittest.main()
