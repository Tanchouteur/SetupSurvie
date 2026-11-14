"""Small synthetic terrain and local OSRM contracts; no real maps or models."""
import asyncio
import concurrent.futures
import json
import math
import struct
import time
import unittest
import zlib
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pilot import app as gateway, geography, routing
import test_geography as terrain_fixtures
import test_map_notebook as routing_fixtures


def pixels(raw):
    chunks=[];offset=8
    while offset<len(raw):
        size=struct.unpack('>I',raw[offset:offset+4])[0]
        if raw[offset+4:offset+8]==b'IDAT':chunks.append(raw[offset+8:offset+8+size])
        offset+=size+12
    return zlib.decompress(b''.join(chunks))


class TerrainReliabilityTests(unittest.TestCase):
    setUp=terrain_fixtures.GeographyTests.setUp
    bundle=terrain_fixtures.GeographyTests.bundle
    def test_transparent_flat_and_missing_terrain_and_private_revalidation(self):
        folder=self.bundle();z=10;x=int((6.1+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(43.1)))/math.pi)/2*2**z)
        raw=geography.terrain_png(z,x,y)
        decoded=pixels(raw)
        self.assertTrue(all(decoded[j*1025+i*4+4]==0 for j in range(256) for i in range(256)))
        self.assertEqual(set(pixels(geography.terrain_png(z,0,0))),{0})
        gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'test','role':'admin'}
        self.addCleanup(gateway.app.dependency_overrides.clear)
        with TestClient(gateway.app) as client:
            url=f'/api/geography/terrain/{z}/{x}/{y}.png'
            first=client.get(url)
            self.assertEqual(first.headers['cache-control'],'private, no-cache')
            cached=client.get(url,headers={'If-None-Match':first.headers['etag']})
            self.assertEqual(cached.status_code,304)
            self.assertEqual(cached.content,b'')
            self.assertEqual(client.get('/api/settings').headers['cache-control'],'no-store')
            # Even equal-size content replacements must invalidate cached shade.
            path=folder/'N43E006.hgt'
            path.touch()
            newer=client.get(url,headers={'If-None-Match':first.headers['etag']})
            self.assertEqual(newer.status_code,200)
            self.assertNotEqual(first.headers['etag'],newer.headers['etag'])
            self.assertEqual(client.get('/api/geography/terrain/30/0/0.png').status_code,404)

    def test_shade_missing_border_no_false_cliff_and_coalesced_generation(self):
        class Heights:
            def __enter__(self):self.grids=True;return self
            def __exit__(self,*args):pass
            def sample(self,lat,lon):return None if lon<0 else lon*1000
        geography._terrain_png.cache_clear()
        with patch.object(geography,'Heights',Heights),patch.object(geography,'_height_samples',side_effect=lambda h,lats,lons:[[h.sample(lat,lon) for lon in lons] for lat in lats]):
            shade=pixels(geography.terrain_png(10,512,400,('synthetic-slope',)))
            alphas=[shade[j*1025+i*4+4] for j in range(256) for i in range(256)]
            self.assertTrue(any(alphas));self.assertLessEqual(max(alphas),64)
            missing=pixels(geography.terrain_png(10,511,400,('synthetic-slope',)))
            self.assertEqual(set(missing),{0})
        geography._terrain_png.cache_clear()
        original=geography._terrain_png
        with patch.object(geography,'_terrain_png',wraps=original) as calls,patch.object(geography,'Heights',Heights),patch.object(geography,'_height_samples',side_effect=lambda h,lats,lons:[[h.sample(lat,lon) for lon in lons] for lat in lats]):
            with concurrent.futures.ThreadPoolExecutor(4) as pool:
                results=list(pool.map(lambda _:geography.terrain_png(10,512,400,('concurrent',)),range(4)))
            self.assertEqual(len(set(results)),1)
            self.assertEqual(original.cache_info().misses,1)
            self.assertEqual(original.cache_info().hits,3)


class AccessReliabilityTests(unittest.IsolatedAsyncioTestCase):
    setUp=routing_fixtures.RoutingTests.setUp
    client=routing_fixtures.RoutingTests.client

    async def test_candidates_deduplicate_filter_and_bind_to_mode_graph_and_origin(self):
        data={'code':'Ok','data_version':'test-build','waypoints':[
            {'location':[6.002,43],'nodes':[1,2],'name':'Chemin proche','hint':'abc'},
            {'location':[6.002,43],'nodes':[2,1],'name':'Même chemin'},
            {'location':[6.005,43],'nodes':[3,4],'name':'Autre voie'},
            {'location':[6.1,43],'nodes':[5,6],'name':'Trop loin'}]}
        requests=[]
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(data,requests=requests)):
            result=await routing.accesses(43,6,'car')
        self.assertEqual(len(result['candidates']),2)
        self.assertEqual(requests[0].url.params['exclude'],'motorway')
        token=result['candidates'][0]['token']
        original=self.points[0]
        self.assertEqual(routing.read_access(token,original,'car',True,'test-build')['access'],[43,6.002])
        for value,mode,build,point in [(token,'foot','test-build',original),(token,'car','old',original),(token+'bad','car','test-build',original),(token,'car','test-build',self.points[1])]:
            with self.assertRaises(HTTPException) as error:routing.read_access(value,point,mode,True,build)
            self.assertEqual(error.exception.detail['code'],'access_expired')
        with patch.object(routing.time,'time',return_value=time.time()+901):
            with self.assertRaises(HTTPException):routing.read_access(token,original,'car',True,'test-build')

    async def test_confirmed_access_routes_on_network_and_keeps_original_and_connector(self):
        selected=[43,6.004]
        token=routing.access_token({'origin':[43,6],'access':selected,'mode':'foot','avoid':True,'build':'test-build','time':time.time(),'hint':'access-hint'})
        data={**self.data,'waypoints':[{'location':[6.004,43]},self.data['waypoints'][1]]}
        requests=[]
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(data,requests=requests)):
            result=await routing.calculate([{**self.points[0],'access_token':token},self.points[1]])
        self.assertEqual(result['points'][0]['lon'],6)
        self.assertEqual(result['points'][0]['snapped_lon'],6.004)
        self.assertTrue(result['points'][0]['access_selected'])
        self.assertFalse(result['connectors'][0]['verified'])
        self.assertGreater(result['connectors'][0]['distance_m'],300)
        self.assertEqual(result['distance_m'],8000)
        self.assertEqual(requests[0].url.params['radiuses'],'5;100')
        self.assertEqual(requests[0].url.params['hints'],'access-hint;')
        self.assertNotIn('access_token',json.dumps(result))
        self.assertNotIn('access-hint',json.dumps(result))

    async def test_engine_errors_are_actionable_without_fabricated_accesses(self):
        for data,status,code in [({'code':'NoSegment'},400,'no_access'),({'code':'NoRoute'},400,'no_route'),({'code':'Ok','data_version':'old'},200,'stale_graph'),([],200,'invalid_response')]:
            with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(data,status)):
                with self.assertRaises(HTTPException) as error:await routing.calculate(self.points)
                self.assertEqual(error.exception.detail['code'],code)
        for exc,code in [(httpx.ConnectError('private internal detail'),'engine_unavailable'),(httpx.ReadTimeout('internal url'),'engine_timeout')]:
            def handler(request):raise exc
            client=self.client_class(transport=httpx.MockTransport(handler))
            with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=client):
                with self.assertRaises(HTTPException) as error:await routing.calculate(self.points)
                self.assertEqual(error.exception.detail['code'],code)
                self.assertNotIn('internal',str(error.exception.detail))

    async def test_manual_access_and_coverage_bounds(self):
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient') as client:
            for lat,lon,near,code in [(48,2,None,'outside_coverage'),(43,6,[43.1,6],'access_too_far')]:
                with self.assertRaises(HTTPException) as error:await routing.accesses(lat,lon,near=near)
                self.assertEqual(error.exception.detail['code'],code)
            client.assert_not_called()
        data={'code':'NoSegment'}
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(data,400)):
            self.assertEqual((await routing.accesses(43,6))['candidates'],[])



class AccessExportTests(unittest.TestCase):
    setUp=routing_fixtures.NotebookTests.setUp

    def test_saved_accesses_and_gpx_never_join_unverified_connectors_to_track(self):
        from pilot import map_notebook as notebook
        import xml.etree.ElementTree as ET
        group=notebook.save_list('Fixture')['id']
        point={'title':'Lieu <test>','lat':43,'lon':6,'snapped_lat':43,'snapped_lon':6.003,'offset_m':244,'access_selected':True}
        data={'mode':'foot','distance_m':1000,'duration_s':900,'speed_kmh':4,'points':[point],
              'geometry':{'type':'LineString','coordinates':[[6.003,43],[6.01,43.01]]},
              'connectors':[{'verified':False,'distance_m':244,'geometry':{'type':'LineString','coordinates':[[6,43],[6.003,43]]}}],
              'note':'Liaisons non vérifiées, exclues du calcul.'}
        draft=notebook.draft('family',data)
        saved=notebook.save_route('family',draft['draft_id'],group,'Test')['id']
        with patch.object(routing.httpx,'AsyncClient',side_effect=AssertionError('No engine')):
            snapshot=notebook.route(saved);parsed=ET.fromstring(notebook.gpx(route_id=saved))
        self.assertEqual(snapshot['points'][0],point)
        self.assertEqual(snapshot['connectors'],data['connectors'])
        self.assertEqual(len(parsed.findall('.//{*}wpt')),2)
        self.assertEqual([float(p.attrib['lon']) for p in parsed.findall('.//{*}trkpt')],[6.003,6.01])
        self.assertIn('Lieu <test>',notebook.gpx(route_id=saved).decode().replace('&lt;','<').replace('&gt;','>'))

    def test_access_api_is_admin_only_and_rejects_nonfinite_or_oversized_requests(self):
        self.addCleanup(gateway.app.dependency_overrides.clear)
        gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'reader','role':'user'}
        with TestClient(gateway.app) as client:
            self.assertEqual(client.post('/api/admin/map-notebook/accesses',json={'lat':43,'lon':6}).status_code,403)
            gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'family','role':'admin'}
            with patch.object(routing,'accesses',side_effect=AssertionError('Rejected before engine')):
                for body in [{'lat':90,'lon':6},{'lat':43,'lon':6,'near':[1,2,3]},{'lat':43,'lon':6,'mode':'aircraft'}]:
                    self.assertEqual(client.post('/api/admin/map-notebook/accesses',json=body).status_code,422)
