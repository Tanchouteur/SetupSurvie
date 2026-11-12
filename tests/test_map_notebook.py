import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pilot import app as gateway,library,map_notebook as notebook,maps,routing,store
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import routing_prepare
import setup


class NotebookTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for obj,name,value in [(store,'ROOT',self.root/'state'),(maps,'ROOT',self.root/'maps'),(library,'GUIDES',self.root/'guides'),(library,'books',AsyncMock(return_value=[]))]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        store.init();notebook.init()
    def sample_route(self):
        return {'mode':'foot','distance_m':8000,'duration_s':7200,'speed_kmh':4,'geometry':{'type':'LineString','coordinates':[[6,43],[6.1,43.1]]},'points':[{'title':'Départ','lat':43,'lon':6}],'note':'Données synthétiques, pas une carte réelle.'}
    def test_lists_points_route_snapshots_and_gpx_survive_without_engine(self):
        first=notebook.save_list('Eau');second=notebook.save_list('Repli')
        point={'list_id':first['id'],'title':'Source <test>','lat':43,'lon':6,'kind':'water','notes':'À vérifier & dater'}
        identifier=notebook.save_point(point)['id'];draft=notebook.draft('admin',self.sample_route())
        route=notebook.save_route('admin',draft['draft_id'],first['id'],'À pied')
        notebook.save_point({**point,'list_id':second['id'],'lat':43.2},identifier)
        notebook.delete_point(identifier)
        with patch.object(routing.httpx,'AsyncClient',side_effect=AssertionError('No network')):
            self.assertEqual(notebook.route(route['id'])['distance_m'],8000)
            self.assertNotIn('geometry',notebook.overview()['routes'][0])
            raw=notebook.gpx(route_id=route['id']);self.assertEqual(len(ET.fromstring(raw).findall('.//{*}trkpt')),2)
        with self.assertRaises(HTTPException) as error:notebook.delete_list(first['id'])
        self.assertEqual(error.exception.status_code,409)
        notebook.delete_route(route['id']);notebook.delete_list(first['id'])
        point['list_id']=second['id'];notebook.save_point(point)
        parsed=ET.fromstring(notebook.gpx(list_id=second['id']))
        self.assertEqual(parsed.find('.//{*}name').text,'Source <test>')
        self.assertEqual(parsed.find('.//{*}desc').text,'À vérifier & dater')
    def test_draft_cannot_be_forged_reused_or_saved_by_another_account(self):
        group=notebook.save_list('Test')['id'];draft=notebook.draft('alice',self.sample_route())
        with self.assertRaises(HTTPException):notebook.save_route('bob',draft['draft_id'],group,'Non')
        identifier=notebook.save_route('alice',draft['draft_id'],group,'Oui')['id']
        with self.assertRaises(HTTPException):notebook.save_route('alice',draft['draft_id'],group,'Doublon')
        self.assertEqual(notebook.route(identifier)['duration_s'],7200)
    def test_guests_and_readers_cannot_edit_but_readers_can_consult(self):
        self.addCleanup(gateway.app.dependency_overrides.clear)
        with TestClient(gateway.app) as client:
            self.assertEqual(client.get('/api/map-notebook').status_code,401)
            gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'reader','role':'user'}
            self.assertEqual(client.get('/api/map-notebook').status_code,200)
            for path in ('lists','points','calculate','routes'):
                self.assertEqual(client.post('/api/admin/map-notebook/'+path,json={}).status_code,403)
            gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'admin','role':'admin'}
            group=client.post('/api/admin/map-notebook/lists',json={'title':'Camp'}).json()['id']
            self.assertEqual(client.post('/api/admin/map-notebook/points',json={'list_id':group,'title':'Camp','lat':43,'lon':6}).status_code,200)
            self.assertEqual(client.post('/api/admin/map-notebook/points',json={'list_id':group,'title':'Bad','lat':200,'lon':6}).status_code,422)
            self.assertEqual(client.get('/api/map-notebook/lists/'+group+'/gpx').status_code,200)


class RoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.meta={'complete':True,'build_id':'test-build','created':'2026-11-12','bbox':[5,42,7,44],'source':{'name':'synthetic'},'attribution':'Test'}
        self.points=[{'lat':43,'lon':6,'title':'A'},{'lat':43.01,'lon':6.01,'title':'B'}]
        self.data={'code':'Ok','data_version':'test-build','waypoints':[{'location':[p['lon'],p['lat']]} for p in self.points],
                   'routes':[{'distance':8000,'duration':6000,'geometry':{'type':'LineString','coordinates':[[6,43],[6.01,43.01]]},'legs':[{'steps':[{'name':'Chemin test','distance':8000}]}]}]}
        self.client_class=httpx.AsyncClient
    def client(self,data,status=200,requests=None):
        def handler(request):
            if requests is not None:requests.append(request)
            return httpx.Response(status,json=data,request=request)
        return self.client_class(transport=httpx.MockTransport(handler),trust_env=False)
    async def test_real_road_kilometers_and_four_kmh_not_straight_line(self):
        requests=[]
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(self.data,requests=requests)):
            route=await routing.calculate(self.points,'foot',4)
        self.assertEqual(route['distance_m'],8000);self.assertEqual(route['duration_s'],7200)
        self.assertEqual(requests[0].url.host,'router-foot')
        self.assertEqual(requests[0].url.params['radiuses'],'100;100')
        self.assertEqual(route['geometry']['type'],'LineString')
    async def test_modes_choose_different_local_services_and_no_remote_fallback(self):
        for mode in ('car','motorcycle'):
            requests=[]
            with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(self.data,requests=requests)):
                result=await routing.calculate(self.points,mode,40)
            self.assertEqual(requests[0].url.host,'router-'+mode)
            self.assertEqual(requests[0].url.params['exclude'],'motorway');self.assertEqual(result['duration_s'],720)
        with patch.object(routing,'manifest',return_value=None),patch.object(routing.httpx,'AsyncClient') as client:
            with self.assertRaises(HTTPException) as error:await routing.calculate(self.points)
            self.assertEqual(error.exception.status_code,409);client.assert_not_called()
    async def test_missing_paths_old_graph_bad_response_and_outside_coverage_are_rejected(self):
        for data,status in [({'code':'NoRoute'},400),({'code':'NoSegment'},400),({**self.data,'data_version':'old'},200),({**self.data,'routes':[{'distance':float('inf')}]},200)]:
            with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient',return_value=self.client(data,status)):
                with self.assertRaises(HTTPException):await routing.calculate(self.points)
        with patch.object(routing,'manifest',return_value=self.meta),patch.object(routing.httpx,'AsyncClient') as client:
            with self.assertRaises(HTTPException):await routing.calculate([*self.points[:1],{'lat':48,'lon':2}])
            client.assert_not_called()
        for mode,speed in [('foot',0),('foot',40),('car',300)]:
            with self.assertRaises(HTTPException):await routing.calculate(self.points,mode,speed)


class RoutingPreparationTests(unittest.TestCase):
    def test_bounded_local_preparation_atomic_switch_and_no_model(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=Path(__file__).resolve().parents[1]/'fixtures/maps/routing-small.osm';calls=[]
            def runner(backend,*args,**kwargs):
                calls.append(args)
                if args[0]=='run':
                    mount=args[args.index('-v')+1];path=Path(mount.rsplit(':/data',1)[0])
                    if 'osrm-customize' in args:(path/'network.osrm.properties').write_bytes(b'synthetic graph')
                return SimpleNamespace(returncode=0)
            with patch.object(routing_prepare.content,'check_capacity'):
                first=routing_prepare.build(root,source,[6.09,43.09,6.12,43.12],runner=runner)
                second=routing_prepare.build(root,source,[6.09,43.09,6.12,43.12],runner=runner)
            self.assertNotEqual(first['build_id'],second['build_id'])
            self.assertEqual(len(list((root/'library/maps/routing').glob('previous-*'))),1)
            self.assertEqual({Path(f['path']).parts[0] for f in first['files']},{'foot','motorcycle','car'})
            self.assertFalse(any(args[0]=='pull' for args in calls))
            self.assertTrue(all('--network=none' in args and '--memory=4g' in args for args in calls if args[0]=='run'))
            current=(root/'library/maps/routing/current/manifest.json').read_bytes()
            with patch.object(routing_prepare.content,'check_capacity'),self.assertRaises(RuntimeError):
                routing_prepare.build(root,source,[6.09,43.09,6.12,43.12],runner=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('simulated failure')))
            self.assertEqual((root/'library/maps/routing/current/manifest.json').read_bytes(),current)
            self.assertEqual(list((root/'library/maps/routing').glob('.prepare-*')),[])


if __name__=='__main__':unittest.main()
