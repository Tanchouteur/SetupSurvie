"""Real pinned Caddy + tiny HTTP stubs; no Open WebUI image, accounts or inference.

Extract a temporary validation binary from the pinned image (not installed globally).
Verify header stripping/copying and cookie-selected identity through actual routes.
"""
import http.server
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]
IMAGE=json.loads((ROOT/'deploy/versions.json').read_text())['images']['portal']


def main():
    with tempfile.TemporaryDirectory(prefix='survie-proxy-') as folder:
        work=Path(folder);binary=work/'caddy';container='survie-profile-check-'+uuid.uuid4().hex[:12]
        subprocess.run(['docker','create','--name',container,IMAGE],check=True,stdout=subprocess.DEVNULL)
        try:subprocess.run(['docker','cp',container+':/usr/bin/caddy',str(binary)],check=True,stdout=subprocess.DEVNULL)
        finally:subprocess.run(['docker','rm',container],check=True,stdout=subprocess.DEVNULL)
        binary.chmod(0o700)
        env={**os.environ,'XDG_DATA_HOME':str(work/'data'),'XDG_CONFIG_HOME':str(work/'config')}
        adapted=subprocess.run([str(binary),'adapt','--adapter','caddyfile','--config',str(ROOT/'deploy/Caddyfile')],check=True,capture_output=True,text=True,env=env)
        config=json.loads(adapted.stdout)
        chosen=[s for s in config['apps']['http']['servers'].values() if ':3000' in s['listen']]
        assert len(chosen)==1
        seen=[]
        class Stub(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/api/profiles/webui-headers':
                    assert self.headers.get('X-Survie-Email') is None
                    assert self.headers.get('X-Survie-Role') is None
                    alice='survie_profile=alice' in self.headers.get('Cookie','')
                    identity=('alice@survie.local','Alice','user') if alice else ('family@survie.local','Famille','admin')
                    self.send_response(200)
                    for key,value in zip(('X-Survie-Email','X-Survie-Name','X-Survie-Role'),identity):self.send_header(key,value)
                    self.end_headers();return
                seen.append({k:self.headers.get(k) for k in ('X-Survie-Email','X-Survie-Name','X-Survie-Role')})
                body=json.dumps(seen[-1]).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
        backend=http.server.ThreadingHTTPServer(('127.0.0.1',0),Stub)
        thread=threading.Thread(target=backend.serve_forever,daemon=True);thread.start()
        with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        server=chosen[0];server['listen']=['127.0.0.1:'+str(port)]
        def rewrite(value):
            if isinstance(value,dict):
                if value.get('dial') in ('pilot:8000','open-webui:8080'):value['dial']='127.0.0.1:'+str(backend.server_port)
                for child in value.values():rewrite(child)
            elif isinstance(value,list):
                for child in value:rewrite(child)
        rewrite(server)
        config['apps']={'http':{'servers':{'fixture':server}}};config['admin']={'disabled':True}
        path=work/'proxy.json';path.write_text(json.dumps(config))
        with (work/'proxy.log').open('wb') as logs:
            process=subprocess.Popen([str(binary),'run','--config',str(path)],stdout=logs,stderr=logs,env=env)
            try:
                for _ in range(100):
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/',timeout=1):break
                    except OSError:
                        if process.poll() is not None:raise RuntimeError('Proxy fixture did not start')
                        time.sleep(.05)
                for cookie,email,role in [('', 'family@survie.local','admin'),('survie_profile=alice','alice@survie.local','user')]:
                    request=urllib.request.Request('http://127.0.0.1:'+str(port)+'/api/v1/auths/signin',headers={'Cookie':cookie,'X-Survie-Email':'forged@survie.local','X-Survie-Role':'admin','X-Survie-Name':'forged'})
                    with urllib.request.urlopen(request,timeout=3) as response:data=json.load(response)
                    assert data['X-Survie-Email']==email and data['X-Survie-Role']==role,data
                print('Pinned Caddy: valid routes, spoofed headers stripped, cookie-selected profile forwarded.')
            finally:
                process.terminate();process.wait(timeout=10);backend.shutdown();backend.server_close();thread.join(timeout=5)


if __name__=='__main__':main()
