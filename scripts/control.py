#!/usr/bin/env python3
"""Authenticated host-side engine controls; fixed actions, no command execution API."""
import argparse
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

import discovery
import setup
import library_tasks
import library_monitor


def key(c):return hmac.new(c['secret'].encode(),b'SetupSurvie engine control v1',hashlib.sha256).hexdigest()


def clean_engine_diagnostic(value):
    if not isinstance(value,dict):return {}
    enums={'action':('start','stop'),'stage':('transfer_guard','service_command','waiting_for_api','completed'),
           'status':('running','completed','failed'),'target':('windows','linux'),
           'error_kind':('SetupError','OSError','ValueError','TimeoutExpired','CalledProcessError','PermissionError','other_error')}
    result={name:value[name] for name,allowed in enums.items() if value.get(name) in allowed}
    for name in ('created','finished','elapsed_ms'):
        if type(value.get(name)) in (int,float) and 0<=value[name]<10**13:result[name]=value[name]
    if type(value.get('forced')) is bool:result['forced']=value['forced']
    return result


def publish(app,c,state,reason=''):
    setup.write_json(Path(c['data_dir'])/'catalog/inference.json',{'state':state,'reason':reason,'updated':time.time()})


def hardware(c):
    memory={}
    if os.name=='nt':
        import ctypes
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in ('total','available','total_page','available_page','total_virtual','available_virtual','extended')]
        value=Memory();value.length=ctypes.sizeof(value)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):memory={'total':value.total,'used':value.total-value.available,'available':value.available}
    else:
        try:
            values={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
            memory={'total':values['MemTotal'],'available':values['MemAvailable'],'used':values['MemTotal']-values['MemAvailable']}
        except (OSError,ValueError,KeyError):pass
    gpu=[]
    try:
        if os.name=='nt':
            from gpu_windows import query
            gpu=query()
        else:
            result=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
            if result.returncode==0:
                for line in result.stdout.splitlines():
                    name,total,used,load,temp=[p.strip() for p in line.split(',')]
                    gpu.append({'name':name,'total':int(total)*1024**2,'used':int(used)*1024**2,'utilization':int(load),'temperature':float(temp)})
    except (OSError,ValueError,AttributeError,subprocess.TimeoutExpired):pass
    disk=shutil.disk_usage(c['data_dir'])
    return {'memory':memory,'gpus':gpu,'disk':{'total':disk.total,'used':disk.used,'free':disk.free}}


class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,app,c,backend,address=None):
        # Rootless Docker reaches the host loopback through rootlesskit, so the
        # token-protected controller need not listen on the local network.
        address=address or ('127.0.0.1' if c.get('docker_rootless') else '0.0.0.0',11436)
        self.app,self.config,self.backend=app,c,backend
        self.library=library_tasks.Manager(app,c,backend)
        self.operation=None;self.operation_error=None;self.lock=threading.Lock();self.cache={};self.cache_time=0
        self.activity_cache=None;self.activity_time=0
        self.performance_lock=threading.Lock()
        super().__init__(address,Handler)

    def status(self):
        with self.lock:
            if time.monotonic()-self.cache_time>3:
                self.cache=hardware(self.config);self.cache_time=time.monotonic()
            value=dict(self.cache);operation=self.operation;error=self.operation_error
        paused=self.app.work/'inference-paused.json'
        reason=''
        if paused.exists():
            try:reason=json.loads(paused.read_text()).get('reason','user_pause')
            except ValueError:reason='user_pause'
        online=False;models=[]
        try:
            version=self.app.request('http://127.0.0.1:11435/api/version',timeout=1)
            online=bool(version.get('version'))
            models=[{k:m.get(k) for k in ('name','size','size_vram','context_length')} for m in self.app.request('http://127.0.0.1:11435/api/ps',timeout=1).get('models',[])]
        except (OSError,ValueError):pass
        diagnostic={}
        try:
            path=self.app.work/'last-engine-diagnostic.json'
            if path.stat().st_size<=4096:
                saved=json.loads(path.read_text(encoding='utf-8'))
                diagnostic=clean_engine_diagnostic(saved)
        except (OSError,ValueError,TypeError):pass
        return {**value,'online':online,'paused':paused.exists(),'reason':reason,'models':models,
                'operation':operation,'error':error,'control_available':True,'last_engine_action':diagnostic}

    def activity(self):
        with self.lock:
            if self.activity_cache is None or time.monotonic()-self.activity_time>5:
                self.activity_cache=library_monitor.snapshot(self.config['data_dir'],self.app.work)
                self.activity_time=time.monotonic()
            return self.activity_cache

    def performance(self):
        import host_performance
        with self.performance_lock:
            value=host_performance.snapshot(self.config['data_dir'])
            with self.lock:
                if time.monotonic()-self.cache_time>3:
                    self.cache=hardware(self.config);self.cache_time=time.monotonic()
                resources=dict(self.cache)
                age=round((time.monotonic()-self.cache_time)*1000)
            value.update(memory=resources.get('memory',{}),gpus=resources.get('gpus',[]),
                         disk_capacity=resources.get('disk',{}),memory_gpu_age_ms=age)
            return value

    def change(self,action,force=False):
        with self.lock:
            if self.operation:return False,'Une commande est déjà en cours.'
            if action=='start' and (self.app.work/'inference-paused.json').exists() and not force:
                return False,'Le moteur est en pause. Utilisez explicitement « Forcer le démarrage » pour le reprendre.'
            self.operation=action;self.operation_error=None
        self.launch_worker(action,force)
        return True,None

    def launch_worker(self,action,force):
        threading.Thread(target=self.worker,args=(action,force),daemon=True).start()

    def worker(self,action,force):
        app,c=self.app,self.config
        started=time.monotonic();diagnostic={'action':action,'forced':bool(force),'created':time.time(),'stage':'transfer_guard','status':'running','target':c['target']}
        try:
            import transfer
            transfer.guard(app.work)
            marker=app.work/'inference-paused.json'
            if action=='stop':
                setup.write_json(marker,{'reason':'user_pause'},private=True);publish(app,c,'paused','user_pause')
            elif marker.exists():marker.unlink()
            diagnostic['stage']='service_command'
            if self.backend=='lab':
                import linux_lab as lab
                lab.podman('start' if action=='start' else 'stop',lab.PREFIX+'ollama',capture=True)
            elif c['target']=='windows':
                if action=='start':app.start_native(c)
                else:app.stop_native(c)
            elif action=='start':app.compose(c,'up','-d','--pull','never','ollama')
            else:app.compose(c,'stop','ollama')
            if action=='start':
                diagnostic['stage']='waiting_for_api'
                for _ in range(45):
                    try:
                        app.request('http://127.0.0.1:11435/api/version',timeout=1);break
                    except (OSError,ValueError):time.sleep(1)
                else:raise setup.SetupError('Délai de démarrage dépassé.')
                publish(app,c,'online')
            setup.write_json(app.work/'last-engine-action.json',{'action':action,'forced':force,'time':time.time()},private=True)
            diagnostic.update(status='completed',stage='completed')
        except Exception as error:
            diagnostic.update(status='failed',error_kind=type(error).__name__ if type(error).__name__ in ('SetupError','OSError','ValueError','TimeoutExpired','CalledProcessError','PermissionError') else 'other_error')
            with self.lock:self.operation_error='La commande a échoué. Consultez les diagnostics sur le PC serveur.'
            if action=='start':
                setup.write_json(app.work/'inference-paused.json',{'reason':'start_failed'},private=True);publish(app,c,'paused','start_failed')
        finally:
            diagnostic.update(elapsed_ms=round((time.monotonic()-started)*1000),finished=time.time())
            try:setup.write_json(app.work/'last-engine-diagnostic.json',clean_engine_diagnostic(diagnostic),private=True)
            except OSError:pass
            with self.lock:self.operation=None


class Handler(BaseHTTPRequestHandler):
    MAX_POST_BYTES = 1024

    def log_message(self,*args):pass
    def respond(self,code,value):
        raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(code)
        self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def authorized(self):
        supplied = self.headers.get('Authorization', '').encode('latin-1')
        expected = ('Bearer ' + key(self.server.config)).encode('ascii')
        if not hmac.compare_digest(supplied, expected):
            if self.command == 'POST':
                self.discard_rejected_body()
            self.respond(401,{'detail':'Accès non autorisé.'});return False
        return True
    def discard_rejected_body(self):
        # Closing with a body still queued can reset the connection on Windows.
        # Drain only small requests and bound the total time spent on a refusal.
        try:
            remaining = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return
        if not 0 < remaining <= self.MAX_POST_BYTES:
            return
        deadline = time.monotonic() + 0.25
        previous_timeout = self.connection.gettimeout()
        try:
            while remaining:
                budget = deadline - time.monotonic()
                if budget <= 0:
                    break
                self.connection.settimeout(budget)
                chunk = self.rfile.read1(remaining)
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            pass
        finally:
            self.connection.settimeout(previous_timeout)
    def do_GET(self):
        if not self.authorized():return
        if self.path=='/performance':
            try:self.respond(200,self.server.performance())
            except (OSError,ValueError,RuntimeError):self.respond(503,{'detail':'Les mesures du PC ne sont pas disponibles.'})
            return
        if self.path=='/activity':
            self.respond(200,self.server.activity());return
        if self.path=='/library':
            try:self.respond(200,self.server.library.status())
            except (OSError,ValueError,RuntimeError,setup.SetupError):self.respond(503,{'detail':'Le suivi documentaire est indisponible sur le PC serveur.'})
            return
        if self.path!='/status':self.respond(404,{'detail':'Route inconnue.'});return
        self.respond(200,self.server.status())
    def do_POST(self):
        if not self.authorized():return
        if self.path not in ('/start','/stop','/library/plan','/library/download','/library/pause','/library/geography','/library/routing','/library/index','/library/index-prepare','/library/index-settings','/library/video-inventory','/library/video-inventory-pause'):
            self.discard_rejected_body()
            self.respond(404,{'detail':'Commande inconnue.'})
            return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<=length<=self.MAX_POST_BYTES:raise ValueError()
            body=json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body,dict):raise ValueError()
        except (ValueError,TypeError):self.respond(400,{'detail':'Requête non valide.'});return
        if self.path.startswith('/library/'):
            try:
                with self.server.lock:
                    if self.path=='/library/index-settings':
                        import search_index_queue
                        search_index_queue.settings(Path(self.server.config['data_dir']),body)
                    elif self.path=='/library/video-inventory-pause':
                        if self.server.library.current().get('action')!='video-inventory':raise setup.SetupError('Aucun inventaire des vidéos de collections n’est en cours.')
                        self.server.library.pause()
                    elif self.path=='/library/pause':self.server.library.pause()
                    else:self.server.library.start(self.path.rsplit('/',1)[-1],body)
                self.respond(202,{'accepted':True})
            except setup.SetupError as exc:self.respond(409,{'detail':str(exc)})
            except (OSError,ValueError,RuntimeError):self.respond(503,{'detail':'Vérifiez le disque de données et le service de téléchargement sur le PC serveur.'})
            return
        ok,error=self.server.change(self.path[1:],body.get('force') is True)
        self.respond(202 if ok else 409,{'accepted':ok,'detail':error})


def start(app,c,backend='compose'):
    import transfer
    transfer.guard(app.work)
    marker=app.work/'control-process.json'
    version=json.loads((setup.ROOT/'deploy/release.json').read_text())['version']
    if marker.exists():
        value=json.loads(marker.read_text())
        if value.get('identity') and discovery.identity(value['pid'])==value['identity']:
            if value.get('version')==version:return
            # Reload an older controller when deploying software, without
            # touching Ollama. Detached library jobs continue independently.
            stop(app)
    (app.work/'control.stop').unlink(missing_ok=True)
    kwargs={'creationflags':subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    with (app.work/'control.log').open('ab') as log:
        process=subprocess.Popen([sys.executable,str(setup.ROOT/'scripts/control.py'),'serve','--work-dir',str(app.work),'--backend',backend],stdin=subprocess.DEVNULL,stdout=log,stderr=log,**kwargs)
    setup.write_json(marker,{'pid':process.pid,'identity':discovery.identity(process.pid),'version':version},private=True)


def stop(app):
    marker=app.work/'control-process.json'
    if not marker.exists():return
    value=json.loads(marker.read_text())
    if not value.get('identity') or discovery.identity(value['pid'])!=value['identity']:marker.unlink();return
    (app.work/'control.stop').touch()
    for _ in range(100):
        if discovery.identity(value['pid'])!=value['identity']:break
        time.sleep(.1)
    else:raise setup.SetupError('Le contrôleur ne s’est pas arrêté ; son identité est conservée pour éviter un doublon.')
    marker.unlink(missing_ok=True)


def serve(app,backend):
    server=Server(app,app.load(),backend);server.timeout=.5
    last_index=0
    while not (app.work/'control.stop').exists():
        server.handle_request()
        if time.monotonic()-last_index>=5:
            last_index=time.monotonic()
            try:server.library.auto_index()
            except (OSError,ValueError,setup.SetupError):pass
    server.server_close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['start','stop','serve']);p.add_argument('--work-dir',required=True);p.add_argument('--backend',choices=['compose','lab'],default='compose');a=p.parse_args();app=setup.Installation(a.work_dir)
    if a.action=='serve':serve(app,a.backend)
    elif a.action=='stop':stop(app)
    else:start(app,app.load(),a.backend)
