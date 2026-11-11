import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from fastapi.testclient import TestClient
from pilot import app as gateway,library,maps,store


class OfflineMapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.raw=b'PMTiles\x03'+b'archive-bytes'*20
        (self.root/'test.pmtiles').write_bytes(self.raw)
        self.item={'id':'test','path':'test.pmtiles','bytes':len(self.raw),'sha256':'a'*64,
                   'title':'Test','bbox':[5,43,7,44],'center':[6,43.2],'maxzoom':13}
        self.write_manifest(self.item)
        for obj,name,value in [(maps,'ROOT',self.root),(store,'ROOT',self.root/'state'),
                               (library,'GUIDES',self.root/'guides'),(library,'books',AsyncMock(return_value=[]))]:
            patcher=patch.object(obj,name,value);patcher.start();self.addCleanup(patcher.stop)
    def write_manifest(self,item):
        (self.root/'manifest.json').write_text(json.dumps({'maps':[item]}))
    def test_range_reads_small_part_and_unknown_archive_is_rejected(self):
        with TestClient(gateway.app) as client:
            self.assertEqual(len(client.get('/api/maps').json()['maps']),1)
            response=client.get('/api/maps/test/archive',headers={'Range':'bytes=0-7'})
            self.assertEqual(response.status_code,206);self.assertEqual(response.content,b'PMTiles\x03')
            self.assertEqual(client.get('/api/maps/unknown/archive').status_code,404)
    def test_paths_partial_corrupt_and_symlink_are_not_published(self):
        for change in [{'path':'../secret.pmtiles'},{'path':'test.pmtiles.part'},{'bytes':len(self.raw)+1},{'sha256':'bad'}]:
            self.write_manifest({**self.item,**change});self.assertEqual(maps.available(),[])
        self.write_manifest(self.item)
        (self.root/'test.pmtiles').write_bytes(b'not-a-map'+b'x'*(len(self.raw)-9))
        self.assertEqual(maps.available(),[])
        (self.root/'test.pmtiles').unlink()
        try:(self.root/'test.pmtiles').symlink_to(self.root/'other')
        except OSError:self.skipTest('Liens non disponibles.')
        self.assertEqual(maps.available(),[])


if __name__=='__main__':unittest.main()
