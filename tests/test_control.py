import json
from pathlib import Path
import sys
import tempfile
import threading
import os
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup,control


class ControlTests(unittest.TestCase):
    def test_nonwindows_hardware_query_accepts_fractional_gpu_temperature(self):
        output = SimpleNamespace(returncode=0, stdout='NVIDIA GPU, 8192, 1024, 10, 46.73\n')
        with patch.object(control,'os',SimpleNamespace(name='posix')),patch.object(control.subprocess, 'run', return_value=output) as run:
            value = control.hardware(self.c)
        self.assertEqual(value['gpus'][0]['temperature'], 46.73)
        self.assertNotIn('creationflags',run.call_args.kwargs)

    def test_windows_hardware_never_starts_a_gpu_subprocess_even_if_driver_fails(self):
        import gpu_windows
        from unittest.mock import MagicMock
        for response in ([{'name':'native GPU','total':8,'used':2,'utilization':10,'temperature':47}],OSError('driver absent')):
            with patch.object(control,'os',SimpleNamespace(name='nt')),patch('ctypes.windll',MagicMock(),create=True),patch.object(gpu_windows,'query',side_effect=response if isinstance(response,Exception) else None,return_value=response),patch.object(control.subprocess,'run',side_effect=AssertionError('No helper executable')):
                value=control.hardware(self.c)
            self.assertEqual(value['gpus'],[] if isinstance(response,Exception) else response)

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
            for token,path,code in [(None,'/start',401),('bad','/stop',401),('bad-é','/start',401),
                                    (None,'/library/plan',401),(control.key(self.c),'/run',404)]:
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

    def test_performance_counters_are_authenticated_and_never_start_engine(self):
        import host_performance
        data={'schema':1,'source':'host_controller','cpu':{'percent':25},'disks':[]}
        with patch.object(host_performance,'snapshot',return_value=data),patch.object(control,'hardware',return_value={'memory':{'available':10},'gpus':[]}),patch.object(self.server,'change') as change:
            request=urllib.request.Request(self.base+'/performance')
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with self.assertRaises(urllib.error.HTTPError) as caught:opener.open(request,timeout=3)
            self.assertEqual(caught.exception.code,401)
            request.add_header('Authorization','Bearer '+control.key(self.c))
            with opener.open(request,timeout=3) as response:value=json.load(response)
            self.assertEqual(value['cpu']['percent'],25);self.assertEqual(value['memory']['available'],10)
            self.assertIn('memory_gpu_age_ms',value);change.assert_not_called()

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

    def test_engine_worker_keeps_a_bounded_failed_start_stage_without_logs(self):
        with patch.object(self.app,'compose',side_effect=setup.SetupError('PRIVATE PATH SECRET')):
            self.server.worker('start',False)
        saved=json.loads((self.app.work/'last-engine-diagnostic.json').read_text())
        self.assertEqual(saved['status'],'failed');self.assertEqual(saved['stage'],'service_command')
        self.assertEqual(saved['error_kind'],'SetupError');self.assertGreaterEqual(saved['elapsed_ms'],0)
        self.assertTrue((self.app.work/'inference-paused.json').exists());self.assertIsNone(self.server.operation)
        self.assertNotIn('PRIVATE',json.dumps(saved))
        with patch.object(control,'hardware',return_value={}),patch.object(self.app,'request',return_value={'version':'fixture','models':[]}):
            state=self.server.status()
        self.assertEqual(state['last_engine_action'],saved)

    def test_successful_start_records_completion_without_model_loading(self):
        with patch.object(self.app,'compose') as compose,patch.object(self.app,'request',return_value={'version':'0.40.16'}) as request:
            self.server.worker('start',False)
        saved=json.loads((self.app.work/'last-engine-diagnostic.json').read_text())
        self.assertEqual(saved['status'],'completed');self.assertEqual(saved['stage'],'completed')
        self.assertTrue(all('/api/version' in call.args[0] for call in request.call_args_list))
        compose.assert_called_once_with(self.c,'up','-d','--pull','never','ollama')

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
