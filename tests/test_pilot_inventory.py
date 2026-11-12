import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from pilot import inventory, library, store


class InventoryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('zim', 'models', 'guides', 'state'):
            (self.root / name).mkdir()
        for obj, name, value in ((inventory,'ZIMS',self.root/'zim'),(inventory,'MODELS',self.root/'models'),
                                  (library,'GUIDES',self.root/'guides'),(store,'ROOT',self.root/'state')):
            p = patch.object(obj, name, value); p.start(); self.addCleanup(p.stop)
        store.init()

    async def test_ready_requires_complete_archive_and_reader_registration(self):
        stem = 'wikipedia_fr_all_maxi_2026-05'
        (inventory.ZIMS / (stem+'.zim')).write_bytes(b'archive')
        (inventory.ZIMS / 'wikipedia_en_all_maxi_2026-08.zim.part').write_bytes(b'part')
        (inventory.ZIMS / 'ignored.zim.parts.json').write_text('{}')
        with patch.object(library,'books',AsyncMock(return_value=[])):
            data = await inventory.inventory()
        self.assertEqual(len(data['books']),2)
        self.assertFalse(any(b['ready'] for b in data['books']))
        with patch.object(library,'books',AsyncMock(return_value=[{'book':stem,'title':'Wikipedia','language':'fra'}])):
            data = await inventory.inventory()
        french = next(b for b in data['books'] if b['id']==stem)
        self.assertTrue(french['ready'])
        self.assertEqual(french['title'],'Wikipédia — Français')
        self.assertEqual(french['bytes'],7)
        self.assertEqual(french['version'],'2026-05')

    async def test_models_check_blob_presence_and_length_without_running_ollama(self):
        manifest = inventory.MODELS/'manifests/registry.ollama.ai/library/test/small'
        manifest.parent.mkdir(parents=True)
        digest = 'a'*64
        manifest.write_text(json.dumps({'config':{'digest':'sha256:'+digest,'size':3},'layers':[]}))
        self.assertFalse(inventory.model_inventory()[0]['ready'])
        blobs = inventory.MODELS/'blobs';blobs.mkdir()
        blob = blobs/('sha256-'+digest);blob.write_bytes(b'bad-size')
        self.assertFalse(inventory.model_inventory()[0]['ready'])
        blob.write_bytes(b'abc')
        self.assertTrue(inventory.model_inventory()[0]['ready'])
        manifest.write_text('{broken')
        self.assertFalse(inventory.model_inventory()[0]['ready'])

    async def test_guides_report_missing_files_and_symlinks_do_not_count(self):
        with store.connect() as db:
            db.execute('INSERT INTO documents VALUES(?,?,?,?,?)',('guide:missing.fr.txt','Absent','','fr','Texte'))
        try:
            (inventory.ZIMS/'outside.zim').symlink_to(self.root/'state/pilot.db')
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Création de lien non autorisée sur ce système.')
            raise
        with patch.object(library,'books',AsyncMock(return_value=[])):
            data = await inventory.inventory()
        self.assertEqual(data['books'],[])
        self.assertFalse(data['guides'][0]['ready'])
        self.assertIsNone(data['guides'][0]['bytes'])


if __name__ == '__main__':unittest.main()
