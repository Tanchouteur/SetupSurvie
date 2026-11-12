from collections import namedtuple
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import kit_audit,kit_maps,pilot_kit,setup


def record(root,relative,raw):
    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return {'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


class MapsKitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.kit=self.base/'kit';self.data=self.base/'data'
        self.kit.mkdir();self.data.mkdir();self.geo='a'*20
        self.images=[{'service':'routing','id':'sha256:'+'f'*64,'reference':'pinned'}]
        self.old={'schema':1,'kind':'SetupSurvie public pilot kit','files':[
            record(self.kit,'images.tar',b'old images'),record(self.kit,'payload/models/keep',b'unchanged model')]}
        self.old['files'].append(record(self.kit,'images.tar.json',json.dumps({'images':[],'sha256':setup.file_hash(self.kit/'images.tar')}).encode()))
        setup.write_json(self.kit/'manifest.json',self.old)
        entry=record(self.data,'library/maps/sollies-test.pmtiles',b'PMTiles\x03test')
        setup.write_json(self.data/'library/maps/manifest.json',{'maps':[{**entry,'path':'sollies-test.pmtiles','id':'sollies'}]})
        place=record(self.data,'library/maps/geography/'+self.geo+'/places.json',b'{"places":[]}')
        setup.write_json(self.data/'library/maps/geography'/self.geo/'manifest.json',{'complete':True,'files':[{**place,'path':'places.json'}]})
        record(self.data,'library/maps/geography/'+self.geo+'/unlisted-private.txt',b'do not export')
        record(self.data,'state/pilot/private.db',b'do not export')
        recipe=json.loads((setup.ROOT/'deploy/routing-engine.json').read_text())
        route=record(self.data,'library/maps/routing/current/foot/network.osrm.properties',b'graph fixture')
        setup.write_json(self.data/'library/maps/routing/current/manifest.json',{'complete':True,'image':recipe['image'],'profiles':recipe['profiles'],'files':[{**route,'path':'foot/network.osrm.properties'}]})
        usage=namedtuple('Usage','total used free')(590_000_000_000,100_000_000_000,490_000_000_000)
        mocked=patch.object(kit_maps.shutil,'disk_usage',return_value=usage);mocked.start();self.addCleanup(mocked.stop)

    def test_refresh_adds_english_wikipedia_and_downloaded_collections_to_old_kit(self):
        import content
        entries=[]
        for ident,name in [('wikipedia-en','wikipedia_en_all_maxi_2026-08.zim'),('new','sailing_en_all_2026-10.zim')]:
            raw=('tiny '+ident).encode()
            entry=record(self.data,'library/zim/'+name,raw)
            entries.append({**entry,'id':ident,'url':'https://download.kiwix.org/zim/other/'+name})
        setup.write_json(self.data/'catalog/downloaded-content.json',{'items':[entries[1]]})
        record(self.data,'library/guides/private-family.txt',b'private')
        with patch.object(content,'CATALOG',self.base/'unused'):
            # Default catalogue is frozen at import; patch the reader instead.
            original=content.catalog
            def catalog(path=None):return [entries[0]] if path is None else original(path)
            with patch.object(content,'catalog',side_effect=catalog):
                pilot_kit.refresh_library(self.kit,self.data)
        manifest=json.loads((self.kit/'manifest.json').read_text())
        self.assertTrue(manifest['english_wikipedia'])
        paths={i['path'] for i in manifest['files']}
        self.assertTrue(all('payload/'+i['path'] in paths for i in entries))
        self.assertNotIn('payload/library/guides/private-family.txt',paths)
        self.assertEqual((self.kit/'payload/models/keep').read_bytes(),b'unchanged model')
        target=self.kit/('payload/'+entries[1]['path']);target.unlink()
        (self.data/entries[1]['path']).write_bytes(b'corrupt')
        with patch.object(content,'catalog',side_effect=catalog):
            with self.assertRaises(setup.SetupError):pilot_kit.refresh_library(self.kit,self.data)
        self.assertFalse(target.exists())

    def save(self,path,images):path.write_bytes(b'new pinned images')

    def refresh(self,writer=None):return kit_maps.refresh(self.kit,self.data,[self.geo],True,self.images,writer or self.save)

    def test_adds_verified_maps_and_images_without_copying_models_or_private_files(self):
        before=(self.kit/'payload/models/keep').stat().st_ino
        result=self.refresh();manifest=json.loads((self.kit/'manifest.json').read_text())
        pilot_kit.checked_entries(self.kit,manifest)
        self.assertEqual((self.kit/'payload/models/keep').stat().st_ino,before)
        self.assertTrue(result['routing'])
        self.assertTrue((self.kit/'payload/library/maps/geography'/self.geo/'places.json').is_file())
        self.assertFalse(any('private' in f['path'] for f in manifest['files']))
        self.assertFalse((self.kit/'kit-building.json').exists())

    def test_repeat_reuses_image_archive(self):
        self.refresh()
        with patch.object(kit_maps.setup,'file_hash',wraps=setup.file_hash):
            def unexpected(*args):self.fail('Must reuse the verified archive')
            self.assertTrue(self.refresh(unexpected)['image_archive_reused'])

    def test_corrupt_source_or_invalid_selection_leaves_kit_unchanged(self):
        path=self.data/'library/maps/geography'/self.geo/'places.json';path.write_bytes(b'corrupt')
        with self.assertRaises(setup.SetupError):self.refresh()
        self.assertEqual(json.loads((self.kit/'manifest.json').read_text()),self.old)
        self.assertEqual((self.kit/'images.tar').read_bytes(),b'old images')
        with self.assertRaises(setup.SetupError):kit_maps.public_maps(self.data,['../private'],False)

    def test_publication_failure_restores_old_manifest_images_and_files(self):
        original=setup.write_json
        def fail(path,value,**kwargs):
            if path==self.kit/'manifest.json' and 'map_bundles' in value:raise OSError('power failure simulation')
            return original(path,value,**kwargs)
        with patch.object(setup,'write_json',side_effect=fail),self.assertRaises(OSError):self.refresh()
        self.assertEqual(json.loads((self.kit/'manifest.json').read_text()),self.old)
        self.assertEqual((self.kit/'images.tar').read_bytes(),b'old images')
        self.assertFalse((self.kit/'kit-building.json').exists())
        self.assertEqual(list(self.kit.glob('.maps-stage-*')),[])
        self.assertFalse((self.kit/'payload/library/maps/manifest.json').exists())

    def test_interrupted_publication_can_be_recovered(self):
        stage=self.kit/('.maps-stage-'+'b'*32);stage.mkdir()
        backup=stage/'previous/images.tar';backup.parent.mkdir();(self.kit/'images.tar').replace(backup)
        (self.kit/'images.tar').write_bytes(b'new image')
        setup.write_json(stage/'transaction.json',{'original':self.old,'files':[{'path':'images.tar','had_previous':True}]})
        setup.write_json(self.kit/'kit-building.json',{'kind':'SetupSurvie maps publication','staging':stage.name})
        kit_maps.recover(self.kit)
        self.assertEqual((self.kit/'images.tar').read_bytes(),b'old images')
        self.assertFalse(stage.exists());self.assertFalse((self.kit/'kit-building.json').exists())

    def test_unknown_destination_file_is_preserved(self):
        path=self.kit/'payload/library/maps/manifest.json';path.parent.mkdir(parents=True);path.write_bytes(b'user file')
        with self.assertRaises(setup.SetupError):self.refresh()
        self.assertEqual(path.read_bytes(),b'user file')

    def test_install_rejects_graph_without_offline_engine_before_copy(self):
        graph=record(self.kit,'payload/library/maps/routing/current/manifest.json',b'{}');self.old['files'].append(graph)
        setup.write_json(self.kit/'manifest.json',self.old)
        with self.assertRaisesRegex(setup.SetupError,'moteur hors ligne'):
            pilot_kit.install(self.kit,'windows',self.base/'install/data',self.base/'install/private')
        self.assertFalse((self.base/'install').exists())


class OfflineClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.files=[]
        def add(path,value):
            raw=value if isinstance(value,bytes) else json.dumps(value).encode()
            self.files.append(record(self.root,path,raw))
        self.add=add
        versions=json.loads((setup.ROOT/'deploy/versions.json').read_text())
        add('app/deploy/versions.json',versions);add('app/deploy/release.json',{'version':'0.1.14','data_schema':1})
        add('app/pilot/app.py',b"VERSION='0.1.14'\n");add('app/deploy/model-profiles.json',{'profiles':[{'model':'tiny:1'}]})
        add('app/deploy/discovery-packages.json',{'files':[]})
        blob=b'tiny model';digest=hashlib.sha256(blob).hexdigest()
        add('payload/models/blobs/sha256-'+digest,blob)
        add('payload/models/manifests/registry.ollama.ai/library/tiny/1',{'config':{'digest':'sha256:'+digest,'size':len(blob)},'layers':[]})
        cache='payload/state/openwebui/cache/'
        add(cache+'embedding-ready.json',versions['embedding']);add(cache+'whisper/ready.json',versions['speech'])
        for name in ('embedding/bge-m3/config.json','embedding/bge-m3/tokenizer.json','embedding/bge-m3/model.safetensors','whisper/faster-whisper-small/model.bin','whisper/faster-whisper-small/config.json','whisper/faster-whisper-small/tokenizer.json','tiktoken/cache'):
            add(cache+name,b'fixture')
        images=[];archive=io.BytesIO();entries=[]
        with tarfile.open(fileobj=archive,mode='w') as tar:
            for service,reference in versions['images'].items():
                raw=json.dumps({'image':service}).encode();digest=hashlib.sha256(raw).hexdigest();name=digest+'.json'
                info=tarfile.TarInfo(name);info.size=len(raw);tar.addfile(info,io.BytesIO(raw));entries.append({'Config':name,'Layers':[]})
                images.append({'service':service,'reference':reference,'id':'sha256:'+digest})
            raw=json.dumps(entries).encode();info=tarfile.TarInfo('manifest.json');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        add('images.tar',archive.getvalue());add('images.tar.json',{'images':images,'sha256':setup.file_hash(self.root/'images.tar')})
        for name in ('start-pilot.ps1','stop-pilot.ps1','create-shortcuts.ps1'):add('app/scripts/'+name,b'fixture')
        add('app/portal/branding/favicon.ico',b'icon')

    def manifest(self):return {'files':self.files}

    def test_complete_tiny_payload_has_offline_dependencies(self):
        pilot_kit.checked_entries(self.root,self.manifest())
        result=kit_audit.validate(self.root,self.manifest())
        self.assertEqual(result['models'],1);self.assertEqual(result['images'],4)

    def test_public_download_receipt_and_root_launchers_are_allowed(self):
        self.add('payload/catalog/downloaded-content.json', {'items': []})
        self.add('app/Installer-SetupSurvie.cmd', b'fixture')
        self.add('app/Mettre-a-jour-SetupSurvie.cmd', b'fixture')
        self.add('app/1-Preparer-le-PC.cmd', b'fixture')
        self.add('app/2-Installer-SetupSurvie.cmd', b'fixture')
        self.assertEqual(kit_audit.validate(self.root,self.manifest())['models'],1)
        self.add('payload/catalog/settings.json', {'secret': 'fixture'})
        with self.assertRaisesRegex(setup.SetupError,'personnel interdit'):
            kit_audit.validate(self.root,self.manifest())

    def test_pytorch_embedding_cache_is_supported_like_the_installer(self):
        old='payload/state/openwebui/cache/embedding/bge-m3/model.safetensors'
        new=old.replace('model.safetensors','pytorch_model.bin')
        (self.root/old).replace(self.root/new)
        for entry in self.files:
            if entry['path']==old:entry['path']=new
        self.assertEqual(kit_audit.validate(self.root,self.manifest())['models'],1)

    def test_missing_cache_rejected_even_if_other_files_hash_correctly(self):
        self.files=[f for f in self.files if not f['path'].endswith('/model.bin')]
        with self.assertRaisesRegex(setup.SetupError,'Dépendance'):kit_audit.validate(self.root,self.manifest())

    def test_private_database_and_stale_image_ids_rejected(self):
        self.add('payload/state/pilot/pilot.db',b'private fixture')
        with self.assertRaisesRegex(setup.SetupError,'personnel'):kit_audit.validate(self.root,self.manifest())
        self.files.pop()
        path=self.root/'images.tar.json';value=json.loads(path.read_text());value['images'][0]['id']='sha256:'+'0'*64;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(setup.SetupError,'ID'):kit_audit.validate(self.root,self.manifest())


if __name__=='__main__':unittest.main()
