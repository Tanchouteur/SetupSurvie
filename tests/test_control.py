import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,control


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.app=setup.Installation(self.root/'private');self.c=self.app.init('linux',self.root/'data',cpu=True)
        self.server=control.Server(self.app,self.c,'compose',('127.0.0.1',0))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.base='http://127.0.0.1:'+str(self.server.server_port)

    def post(self,path,token=None,body=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        request=urllib.request.Request(self.base+path,data=json.dumps(body or {}).encode(),headers=headers)
        return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=3)

    def test_unauthorized_and_unknown_routes_never_execute(self):
        with patch.object(self.server,'change') as change:
            for token,path,code in [(None,'/start',401),('bad','/stop',401),(None,'/library/plan',401),(control.key(self.c),'/run',404)]:
                with self.assertRaises(urllib.error.HTTPError) as error:self.post(path,token,{'command':'anything'})
                self.assertEqual(error.exception.code,code)
            change.assert_not_called()

    def test_library_routes_are_authenticated_and_limited(self):
        with patch.object(self.server.library,'start') as start:
            with self.post('/library/plan',control.key(self.c),{'themes':['eau']}) as response:
                self.assertEqual(response.status,202)
            start.assert_called_once_with('plan',{'themes':['eau']})
        request=urllib.request.Request(self.base+'/library',headers={'Authorization':'Bearer '+control.key(self.c)})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=3) as response:
            value=json.load(response)
        self.assertEqual(value['phase'],'idle')
        self.assertTrue(any(t['id']=='energie' for t in value['themes']))

    def test_paused_start_requires_explicit_force(self):
        setup.write_json(self.app.work/'inference-paused.json',{'reason':'user_gaming'})
        with self.assertRaises(urllib.error.HTTPError) as error:self.post('/start',control.key(self.c))
        self.assertEqual(error.exception.code,409);self.assertIsNone(self.server.operation)
        with patch.object(self.server,'launch_worker') as launch:
            with self.post('/start',control.key(self.c),{'force':True}) as response:self.assertEqual(response.status,202)
            launch.assert_called_once_with('start',True)
        self.assertEqual(self.server.operation,'start')
        self.assertTrue((self.app.work/'inference-paused.json').exists())

    def test_native_start_does_not_override_pause(self):
        setup.write_json(self.app.work/'inference-paused.json',{'reason':'user_gaming'})
        with patch.object(setup,'os') as operating,patch.object(setup.subprocess,'Popen') as launch:
            operating.name='nt';self.app.start_native({**self.c,'target':'windows'})
            launch.assert_not_called()

    def test_slow_controller_stop_keeps_identity_and_refuses_duplicate(self):
        marker=self.app.work/'control-process.json';identity={'path':'owned','created':'1'}
        setup.write_json(marker,{'pid':123,'identity':identity})
        with patch.object(control.discovery,'identity',return_value=identity),patch.object(control.time,'sleep'):
            with self.assertRaises(setup.SetupError):control.stop(self.app)
        self.assertTrue(marker.exists())
        self.assertTrue((self.app.work/'control.stop').exists())

    def test_start_reloads_old_controller_but_keeps_current_one(self):
        from unittest.mock import MagicMock
        marker=self.app.work/'control-process.json';identity={'path':'owned','created':'1'}
        setup.write_json(marker,{'pid':123,'identity':identity,'version':'0.0.1'})
        with patch.object(control.discovery,'identity',return_value=identity),patch.object(control,'stop') as stop,patch.object(control.subprocess,'Popen',return_value=MagicMock(pid=123)) as launch:
            control.start(self.app,self.c)
            stop.assert_called_once_with(self.app)
            self.assertEqual(Path(launch.call_args.args[0][1]).name,'control.py')
            control.start(self.app,self.c)
            self.assertEqual(launch.call_count,1)


if __name__=='__main__':unittest.main()
