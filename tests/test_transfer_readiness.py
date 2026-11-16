"""Post-transfer OSRM readiness: no real graph, Docker or network."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import transfer_document_probe as probe


class TransferReadinessTests(unittest.TestCase):
    def test_no_prepared_routes_does_not_contact_a_router(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'MAPS_DIR':folder}):
            class Opener:
                def open(self,*args,**kwargs):raise AssertionError('No router should be queried')
            self.assertEqual(probe.probe_routing(Opener()),'not_prepared')

    def test_all_three_fixed_local_profiles_must_return_a_loaded_graph(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'MAPS_DIR':folder}):
            root=Path(folder)/'routing/current';root.mkdir(parents=True);(root/'manifest.json').write_text('{}')
            urls=[]
            class Opener:
                bad=False
                def open(self,url,timeout):
                    urls.append(url);self.timeout=timeout
                    value={'code':'NoSegment'} if self.bad and 'motorcycle' in url else {'code':'Ok','waypoints':[{'location':[6,43]}]}
                    return io.BytesIO(json.dumps(value).encode())
            opener=Opener();self.assertEqual(probe.probe_routing(opener),'passed');self.assertEqual(len(urls),3)
            self.assertEqual(opener.timeout,15);self.assertTrue(all(url.startswith('http://router-') for url in urls))
            opener.bad=True
            with self.assertRaises(ValueError):probe.probe_routing(opener)
