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


def key(c):return hmac.new(c['secret'].encode(),b'SetupSurvie engine control v1',hashlib.sha256).hexdigest()


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
        result=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
        if result.returncode==0:
            for line in result.stdout.splitlines():
                name,total,used,load,temp=[p.strip() for p in line.split(',')]
                gpu.append({'name':name,'total':int(total)*1024**2,'used':int(used)*1024**2,'utilization':int(load),'temperature':int(temp)})
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    disk=shutil.disk_usage(c['data_dir'])
    return {'memory':memory,'gpus':gpu,'disk':{'total':disk.total,'used':disk.used,'free':disk.free}}


class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,app,c,backend,address=('0.0.0.0',11436)):
        self.app,self.config,self.backend=app,c,backend
        self.operation=None;self.operation_error=None;self.lock=threading.Lock();self.cache={};self.cache_time=0
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
        return {**value,'online':online,'paused':paused.exists(),'reason':reason,'models':models,
                'operation':operation,'error':error,'control_available':True}

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
        try:
            marker=app.work/'inference-paused.json'
            if action=='stop':
                setup.write_json(marker,{'reason':'user_pause'},private=True);publish(app,c,'paused','user_pause')
            elif marker.exists():marker.unlink()
            if self.backend=='lab':
                import linux_lab as lab
                lab.podman('start' if action=='start' else 'stop',lab.PREFIX+'ollama',capture=True)
            elif c['target']=='windows':
                if action=='start':app.start_native(c)
                else:app.stop_native(c)
            elif action=='start':app.compose(c,'up','-d','--pull','never','ollama')
            else:app.compose(c,'stop','ollama')
            if action=='start':
                for _ in range(45):
                    try:
                        app.request('http://127.0.0.1:11435/api/version',timeout=1);break
                    except (OSError,ValueError):time.sleep(1)
                else:raise setup.SetupError('Délai de démarrage dépassé.')
                publish(app,c,'online')
            setup.write_json(app.work/'last-engine-action.json',{'action':action,'forced':force,'time':time.time()},private=True)
        except Exception:
            with self.lock:self.operation_error='La commande a échoué. Consultez les diagnostics sur le PC serveur.'
            if action=='start':
                setup.write_json(app.work/'inference-paused.json',{'reason':'start_failed'},private=True);publish(app,c,'paused','start_failed')
        finally:
            with self.lock:self.operation=None


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,code,value):
        raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(code)
        self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def authorized(self):
        if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+key(self.server.config)):
            self.respond(401,{'detail':'Accès non autorisé.'});return False
        return True
    def do_GET(self):
        if not self.authorized():return
        if self.path!='/status':self.respond(404,{'detail':'Route inconnue.'});return
        self.respond(200,self.server.status())
    def do_POST(self):
        if not self.authorized():return
        if self.path not in ('/start','/stop'):self.respond(404,{'detail':'Commande inconnue.'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<=length<=1024:raise ValueError()
            body=json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body,dict):raise ValueError()
        except (ValueError,TypeError):self.respond(400,{'detail':'Requête non valide.'});return
        ok,error=self.server.change(self.path[1:],body.get('force') is True)
        self.respond(202 if ok else 409,{'accepted':ok,'detail':error})


def start(app,c,backend='compose'):
    marker=app.work/'control-process.json'
    if marker.exists():
        value=json.loads(marker.read_text())
        if value.get('identity') and discovery.identity(value['pid'])==value['identity']:return
    (app.work/'control.stop').unlink(missing_ok=True)
    kwargs={'creationflags':subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    with (app.work/'control.log').open('ab') as log:
        process=subprocess.Popen([sys.executable,str(setup.ROOT/'scripts/control.py'),'serve','--work-dir',str(app.work),'--backend',backend],stdin=subprocess.DEVNULL,stdout=log,stderr=log,**kwargs)
    setup.write_json(marker,{'pid':process.pid,'identity':discovery.identity(process.pid)},private=True)


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
    while not (app.work/'control.stop').exists():server.handle_request()
    server.server_close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['start','stop','serve']);p.add_argument('--work-dir',required=True);p.add_argument('--backend',choices=['compose','lab'],default='compose');a=p.parse_args();app=setup.Installation(a.work_dir)
    if a.action=='serve':serve(app,a.backend)
    elif a.action=='stop':stop(app)
    else:start(app,app.load(),a.backend)
