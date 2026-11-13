import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from pilot import app as gateway, geography, library, maps, store
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import geography_data
import setup


class GeographyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for obj,key,value in [(store,'ROOT',self.root/'state'),(maps,'ROOT',self.root/'maps'),(library,'GUIDES',self.root/'guides'),(library,'books',AsyncMock(return_value=[]))]:
            p=patch.object(obj,key,value);p.start();self.addCleanup(p.stop)
        store.init()
    def bundle(self):
        folder=maps.ROOT/'geography'/'test';folder.mkdir(parents=True)
        places={'places':[{'id':'node/1','label':'Source test','lat':43.1,'lon':6.1,'categories':['water']}],
                'addresses':[{'id':'node/2','label':'12 Rue des Écoles 83000 Test','lat':43.1,'lon':6.1}]}
        (folder/'places.json').write_text(json.dumps(places))
        (folder/'N43E006.hgt').write_bytes(struct.pack('>h',123)*1201**2)
        manifest={'complete':True,'created':'2026-11-12','center':[6.1,43.1],'radius_km':5,'terrain':True,'places':1,'addresses':1,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.iterdir()]}
        (folder/'manifest.json').write_text(json.dumps(manifest));return folder
    def test_offline_lookup_confirmation_and_departure_preserve_home(self):
        self.bundle()
        with patch.object(geography.httpx,'AsyncClient',side_effect=AssertionError('No Internet')):
            result=geography.local_addresses('12 rue ecoles')
        self.assertEqual(len(result),1)
        home=geography.set_location('home',candidate=result[0]['id'])
        geography.set_location('departure',lat=43.2,lon=6.2,label='Camp')
        self.assertEqual(geography.settings()['home'],home)
        self.assertEqual(geography.location()['label'],'Camp')
        geography.save('departure',None);self.assertEqual(geography.location()['label'],home['label'])
        with self.assertRaises(ValueError):geography.set_location('home',candidate='f'*32)
        with self.assertRaises(ValueError):geography.set_location('home',lat=float('nan'),lon=0)
    def test_places_missing_coverage_elevation_profile_and_png_offline(self):
        self.assertIsNone(geography.elevation(43.1,6.1)['elevation_m'])
        self.assertIn('Aucune donnée',geography.nearby('water',lat=43.1,lon=6.1)['note'])
        self.bundle();geography.set_location('home',lat=43.1,lon=6.1)
        self.assertEqual(geography.nearby('water')['results'][0]['distance_m'],0)
        self.assertEqual(geography.elevation(43.1,6.1)['elevation_m'],123)
        self.assertEqual(len(geography.profile(43.1,6.1,43.11,6.11)['points']),41)
        with self.assertRaises(ValueError):geography.profile(43,6,46,6)
        self.assertAlmostEqual(geography.distance(0,0,0,1),111195.1,delta=1)
        import math
        z=10;x=int((6.1+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(43.1)))/math.pi)/2*2**z)
        self.assertTrue(geography.terrain_png(z,x,y).startswith(b'\x89PNG'))
    def test_terrain_interpolation_and_missing_samples(self):
        folder=self.bundle();path=folder/'N43E006.hgt'
        with path.open('r+b') as stream:
            for x,y,value in [(600,600,100),(601,600,200),(600,601,300),(601,601,400)]:
                stream.seek(2*(y*1201+x));stream.write(struct.pack('>h',value))
        lat=44-600.5/1200;lon=6+600.5/1200
        self.assertEqual(geography.elevation(lat,lon)['elevation_m'],250)
        with path.open('r+b') as stream:
            stream.seek(2*(600*1201+600));stream.write(struct.pack('>h',-32768))
        self.assertIsNone(geography.elevation(lat,lon)['elevation_m'])

    def test_no_data_is_published_from_partial_symlink_or_bad_size(self):
        folder=self.bundle();self.assertEqual(len(geography.datasets()),1)
        (folder/'places.json').write_text('{}');self.assertEqual(geography.datasets(),[])
    def test_online_candidates_are_from_provider_and_failures_are_clear(self):
        response=AsyncMock();response.get=AsyncMock(return_value=__import__('httpx').Response(200,json={'features':[{'geometry':{'coordinates':[6.1,43.1]},'properties':{'label':'Rue test','type':'street'}}]},request=__import__('httpx').Request('GET','https://data.geopf.fr/geocodage/search')))
        async_client=AsyncMock();async_client.__aenter__.return_value=response
        import asyncio
        with patch.object(geography.httpx,'AsyncClient',return_value=async_client):
            data=asyncio.run(geography.addresses('Rue test',True))
        point=geography.set_location('home',candidate=data['results'][0]['id'])
        self.assertEqual(point['precision'],'street');self.assertEqual(point['method'],'online')
    def test_api_protects_address_and_mutations(self):
        gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'reader','role':'user'}
        self.addCleanup(gateway.app.dependency_overrides.clear)
        with TestClient(gateway.app) as client:
            self.assertEqual(client.post('/api/admin/settings/home',json={'lat':43,'lon':6}).status_code,403)
            self.assertEqual(client.get('/api/geography/addresses?q=test&online=true').status_code,403)
            gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'admin','role':'admin'}
            self.assertEqual(client.post('/api/admin/settings/home',json={'lat':43,'lon':6}).status_code,200)
            self.assertEqual(client.post('/api/admin/settings/home',json={'candidate':'a'*32}).status_code,400)
            self.assertEqual(client.post('/api/admin/settings/home',json={'lat':123,'lon':6}).status_code,422)
            self.assertEqual(client.get('/api/settings').json()['home']['lat'],43)
            gateway.app.dependency_overrides.clear()
            self.assertEqual(client.get('/api/settings').status_code,200)
    def test_assistant_executes_geo_tool_calls_without_network_or_model(self):
        import asyncio
        from contextlib import asynccontextmanager
        from pilot import engine
        self.bundle();geography.set_location('home',lat=43.1,lon=6.1)
        policy=self.root/'policy.txt';policy.write_text('Assistant local de test')
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('geo','reader','Test',time.time()))
            db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',('geo','user','Trouve un point d’eau proche',time.time()))
            db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('geo-job','reader','geo','rapide','queued',time.time(),time.time()))
        payloads=[]
        class Response:
            def raise_for_status(self):pass
            async def aiter_lines(self):
                if len(payloads)==1:
                    message={'tool_calls':[{'function':{'name':'get_location','arguments':{}}},{'function':{'name':'search_nearby','arguments':{'category':'water','radius_km':1}}}]}
                else:message={'content':'Source test : repère cartographié à vérifier sur place.'}
                yield json.dumps({'message':message,'done_reason':'stop'})
        class Client:
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            @asynccontextmanager
            async def stream(self,*args,**kwargs):
                payloads.append(json.loads(json.dumps(kwargs['json'])))
                yield Response()
        with patch.object(engine.httpx,'AsyncClient',return_value=Client()),patch.object(engine,'POLICY',policy):
            asyncio.run(engine.run('geo-job','reader','geo','rapide'))
        trace=json.loads((store.ROOT/'traces/geo-job.json').read_text())
        self.assertEqual([t['tool'] for t in trace['tools']],['get_location','search_nearby'])
        self.assertEqual(trace['tools'][1]['result']['results'][0]['label'],'Source test')
        with store.connect() as db:self.assertEqual(db.execute('SELECT status FROM jobs WHERE id=?',('geo-job',)).fetchone()[0],'done')

    def test_preparation_checks_capacity_and_publishes_atomic_verified_bundle(self):
        root=self.root/'data';root.mkdir()
        raw=json.dumps({'elements':[{'type':'node','id':1,'lat':43.1,'lon':6.1,'tags':{'natural':'spring','name':'Source','addr:street':'Rue test','addr:housenumber':'12'}}]}).encode()
        calls=[]
        def reader(url,**kwargs):
            calls.append(url);kwargs['check']()
            return gzip.compress(struct.pack('>h',321)*1201**2) if url.endswith('.gz') else raw
        with patch.object(geography_data.content,'check_capacity') as capacity:
            manifest=geography_data.prepare(root,{'lat':43.1,'lon':6.1,'radius_km':1},reader=reader)
            self.assertTrue(capacity.called)
        self.assertEqual(manifest['places'],1);self.assertTrue(manifest['terrain'])
        for item in manifest['files']:
            path=next((root/'library/maps/geography').glob('*/'+item['path']))
            self.assertEqual(setup.file_hash(path),item['sha256'])
        self.assertTrue(any('overpass' in c for c in calls));self.assertTrue(any('skadi' in c for c in calls))
        for body in ({'lat':float('nan'),'lon':6},{'lat':43,'lon':6,'radius_km':True},{'lat':43,'lon':6,'radius_km':26}):
            with self.assertRaises(setup.SetupError):geography_data.validate(body)
        with self.assertRaises(setup.SetupError):geography_data.parse_places({'elements':[],'remark':'timeout'})
    def test_failed_preparation_preserves_existing_data(self):
        root=self.root/'data';root.mkdir();existing=root/'library/maps/geography/existing';existing.mkdir(parents=True);(existing/'keep').write_text('user data')
        with patch.object(geography_data.content,'check_capacity'),self.assertRaises(ValueError):
            geography_data.prepare(root,{'lat':43.1,'lon':6.1,'radius_km':1},reader=lambda *a,**k:b'not json')
        self.assertEqual((existing/'keep').read_text(),'user data')
        self.assertEqual(list(existing.parent.glob('.prepare-*')),[])

    def test_overpass_uses_fixed_backup_only_for_transient_failures(self):
        import urllib.error
        calls=[]
        def reader(url,**kwargs):
            calls.append(url)
            if len(calls)==1:raise urllib.error.HTTPError(url,502,'temporary',{},None)
            return b'<osm />'
        raw,source=geography_data.fetch_overpass('query',maximum=100,reader=reader)
        self.assertEqual(raw,b'<osm />')
        self.assertEqual(calls,list(geography_data.OVERPASS_SERVERS))
        self.assertEqual(source,geography_data.OVERPASS_SERVERS[1])
        calls.clear()
        def invalid(url,**kwargs):
            calls.append(url);raise urllib.error.HTTPError(url,400,'bad query',{},None)
        with self.assertRaises(urllib.error.HTTPError):geography_data.fetch_overpass('bad query',maximum=100,reader=invalid)
        self.assertEqual(len(calls),1)
        calls.clear()
        def oversized(url,**kwargs):
            calls.append(url);raise setup.SetupError('response too large')
        with self.assertRaises(setup.SetupError):geography_data.fetch_overpass('large query',maximum=100,reader=oversized)
        self.assertEqual(len(calls),1)


if __name__=='__main__':unittest.main()
