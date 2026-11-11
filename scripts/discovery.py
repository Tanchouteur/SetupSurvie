#!/usr/bin/env python3
"""Advertise a friendly .local name from the real host, outside Docker's bridge."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import platform
import signal
import shutil
import socket
import subprocess
import sys
import time
import zipfile

import setup


def identity(pid):
    if os.name=='nt':return setup.Installation.native_identity(pid)
    try:
        process=Path('/proc')/str(pid)
        return {'path':str((process/'exe').resolve()),'created':(process/'stat').read_text().split(') ',1)[1].split()[19]}
    except (OSError,IndexError):return None


def prepare(app,wheelhouse=None):
    wheelhouse=Path(wheelhouse or os.environ.get('SURVIE_DISCOVERY_WHEELS',setup.ROOT/'vendor/discovery'))
    manifest=json.loads((setup.ROOT/'deploy/discovery-packages.json').read_text())
    abi='cp'+str(sys.version_info.major)+str(sys.version_info.minor)
    target=app.work/'discovery-libs'/abi
    marker=target/'ready.json'
    if marker.exists() and json.loads(marker.read_text())==manifest['packages']:return target
    if platform.machine().lower() not in ('x86_64','amd64'):raise setup.SetupError('Découverte automatique préparée pour les PC x64. Utilisez le QR code direct sur cet appareil.')
    selected=[]
    for item in manifest['files']:
        name=item['file']
        match=name.endswith('py3-none-any.whl') or (('-'+abi+'-'+abi+'-') in name and (name.endswith('win_amd64.whl') if os.name=='nt' else 'manylinux' in name and name.endswith('x86_64.whl')))
        if match:selected.append(item)
    if len(selected)!=2:raise setup.SetupError('Python 3.11 à 3.15 est requis pour le nom local automatique.')
    target.mkdir(parents=True,exist_ok=True)
    for item in selected:
        path=wheelhouse/item['file']
        if setup.file_hash(path)!=item['sha256']:raise setup.SetupError('Paquet de découverte absent ou altéré.')
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                if not (target/entry.filename).resolve().is_relative_to(target.resolve()) or (entry.external_attr>>16)&0o170000==0o120000:
                    raise setup.SetupError('Chemin de paquet non valide.')
            archive.extractall(target)
    setup.write_json(marker,manifest['packages'])
    return target


def local_ip(config):
    value=config.get('lan_host','')
    try:
        ipaddress.IPv4Address(value)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:sock.bind((value,0))
        return value
    except (ValueError,OSError):pass
    # UDP connect selects a route; it sends no packet and needs no Internet response.
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.connect(('192.0.2.1',9));return sock.getsockname()[0]
    except OSError:
        for result in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
            value=result[4][0]
            if not ipaddress.IPv4Address(value).is_loopback:return value
    raise setup.SetupError('Aucune adresse IPv4 du réseau local disponible.')


def network_status(app,c,address,ready,warning=''):
    host=c.get('discovery_name','survie')+'.local'
    value={'name':host,'ip':address,'ready':ready,'lan_enabled':c['bind']=='0.0.0.0','updated':time.time(),
           'http_url':f'http://{host}:8080/','https_url':f'https://{host}:8443/',
           'direct_url':f'http://{address}:8080/','direct_https_url':f'https://{address}:8443/',
           'warning':warning}
    setup.write_json(Path(c['data_dir'])/'catalog/network.json',value)


def native_avahi():
    return sys.platform.startswith('linux') and bool(shutil.which('avahi-publish')) and subprocess.run(['systemctl','is-active','--quiet','avahi-daemon'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0


def serve_avahi(app):
    c=app.load();stop_file=app.work/'discovery.stop'
    def quit_handler(*args):stop_file.touch()
    signal.signal(signal.SIGTERM,quit_handler);signal.signal(signal.SIGINT,quit_handler)
    address=c.get('lan_host','127.0.0.1')
    while not stop_file.exists():
        processes=[]
        try:
            address=local_ip(c);name=c.get('discovery_name','survie');host=name+'.local'
            commands=[['avahi-publish','-a','-R',host,address],
                      ['avahi-publish','-s','-H',host,'SetupSurvie '+name,'_http._tcp','8080','path=/']]
            for command in commands:processes.append(subprocess.Popen(command,stdin=subprocess.DEVNULL))
            for _ in range(2):
                time.sleep(1)
                if any(p.poll() is not None for p in processes):raise RuntimeError('Annonce interrompue.')
            network_status(app,c,address,True)
            last_check=time.monotonic()
            while not stop_file.exists():
                time.sleep(1)
                if any(p.poll() is not None for p in processes):raise RuntimeError('Annonce interrompue.')
                if time.monotonic()-last_check>=15:
                    last_check=time.monotonic()
                    if local_ip(c)!=address:break
                    network_status(app,c,address,True)
        except Exception:
            network_status(app,c,address,False,'Le nom local est momentanément indisponible. Nouvelle tentative automatique ; utilisez le QR code direct si le réseau est actif.')
            for _ in range(5):
                if stop_file.exists():break
                time.sleep(1)
        finally:
            for process in processes:
                if process.poll() is None:process.terminate()
            for process in processes:
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()


def serve(app):
    if native_avahi():return serve_avahi(app)
    c=app.load();sys.path.insert(0,str(prepare(app)))
    from zeroconf import IPVersion,ServiceInfo,Zeroconf
    stop_file=app.work/'discovery.stop'
    def quit_handler(*args):stop_file.touch()
    signal.signal(signal.SIGTERM,quit_handler)
    if hasattr(signal,'SIGINT'):signal.signal(signal.SIGINT,quit_handler)
    address=c.get('lan_host','127.0.0.1')
    while not stop_file.exists():
        zc=None;info=None
        try:
            address=local_ip(c);name=c.get('discovery_name','survie')
            zc=Zeroconf(interfaces=[address],ip_version=IPVersion.V4Only)
            info=ServiceInfo('_http._tcp.local.',f'SetupSurvie {name}._http._tcp.local.',
                addresses=[socket.inet_aton(address)],port=8080,
                properties={'path':'/','description':'Bibliothèque locale et assistant hors ligne'},server=name+'.local.')
            zc.register_service(info,allow_name_change=False)
            network_status(app,c,address,True)
            last_check=time.monotonic()
            while not stop_file.exists():
                time.sleep(1)
                if time.monotonic()-last_check>=15:
                    last_check=time.monotonic()
                    if local_ip(c)!=address:break
                    network_status(app,c,address,True)
        except Exception:
            network_status(app,c,address,False,'Le nom local est momentanément indisponible. Nouvelle tentative automatique ; le QR code direct reste utilisable si le réseau local est actif.')
            for _ in range(5):
                if stop_file.exists():break
                time.sleep(1)
        finally:
            if zc:
                if info:
                    try:zc.unregister_service(info)
                    except Exception:pass
                try:zc.close()
                except Exception:pass


def stop(app):
    marker=app.work/'discovery-process.json'
    if not marker.exists():return
    value=json.loads(marker.read_text())
    if not value.get('identity') or identity(value['pid'])!=value['identity']:marker.unlink();return
    (app.work/'discovery.stop').touch()
    for _ in range(30):
        if identity(value['pid'])!=value['identity']:break
        time.sleep(.1)
    else:
        if os.name=='nt':setup.run(['taskkill','/PID',str(value['pid']),'/T','/F'],capture=True)
        else:os.kill(value['pid'],signal.SIGTERM)
    marker.unlink(missing_ok=True)


def start(app,c,wheelhouse=None):
    if c['bind']!='0.0.0.0':stop(app);return
    marker=app.work/'discovery-process.json'
    if marker.exists():
        value=json.loads(marker.read_text())
        if value.get('identity') and identity(value['pid'])==value['identity']:return
    network_status(app,c,local_ip(c),False,'Le nom local n’est pas encore annoncé. Le QR code direct permet aussi de se connecter.')
    if not native_avahi():prepare(app,wheelhouse)
    (app.work/'discovery.stop').unlink(missing_ok=True)
    env=os.environ.copy()
    if wheelhouse:env['SURVIE_DISCOVERY_WHEELS']=str(wheelhouse)
    kwargs={'creationflags':subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    with (app.work/'discovery.log').open('ab') as log:
        process=subprocess.Popen([sys.executable,str(setup.ROOT/'scripts/discovery.py'),'serve','--work-dir',str(app.work)],
                                 stdin=subprocess.DEVNULL,stdout=log,stderr=log,env=env,**kwargs)
    setup.write_json(marker,{'pid':process.pid,'identity':identity(process.pid)},private=True)
    print('Annonce du nom local démarrée : '+c.get('discovery_name','survie')+'.local')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['start','stop','serve']);p.add_argument('--work-dir',required=True);p.add_argument('--wheels');args=p.parse_args();app=setup.Installation(args.work_dir)
    if args.action=='serve':serve(app)
    elif args.action=='stop':stop(app)
    else:start(app,app.load(),args.wheels)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError) as exc:raise SystemExit(str(exc))
