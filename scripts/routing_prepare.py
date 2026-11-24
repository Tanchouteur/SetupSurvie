#!/usr/bin/env python3
"""Prepare local OSRM graphs on the target PC, never a public routing fallback."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET

import content
import geography_data
import setup
from pilot import durable


def verified_graph(folder):
    from pilot_kit import checked_entries
    try:
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        if not isinstance(manifest,dict) or manifest.get('complete') is not True or manifest.get('engine')!='OSRM' or not manifest.get('files'):return False
        checked_entries(folder,manifest)
        return True
    except (OSError,ValueError,setup.SetupError):return False


def recover_graph_publication(directory):
    journal=directory/'publication.json'
    if not journal.exists():return
    state=json.loads(journal.read_text(encoding='utf-8'))
    if not isinstance(state,dict):raise setup.SetupError('Journal de routage non reconnu ; données conservées.')
    if state.get('phase')=='complete':return
    if state.get('phase')!='pending':raise setup.SetupError('Journal de routage non reconnu ; données conservées.')
    for key,prefix in (('previous','previous-'),('staging','.prepare-')):
        name=state.get(key)
        if not isinstance(name,str) or not name.startswith(prefix) or Path(name).name!=name:
            raise setup.SetupError('Journal de routage non reconnu ; données conservées.')
    current=content.destination(directory,'current')
    previous=content.destination(directory,state['previous'])
    staging=content.destination(directory,state['staging'])
    if not verified_graph(current):
        candidate=previous if verified_graph(previous) else staging if verified_graph(staging) else None
        if candidate is None:raise setup.SetupError('Routage interrompu : aucune copie complète vérifiable. Données conservées pour récupération.')
        if current.exists():durable.publish(current,directory/('interrupted-'+uuid.uuid4().hex))
        durable.publish(candidate,current)
    state['phase']='complete';setup.write_json(journal,state)


def recover_publication(root):
    directory=content.destination(Path(root),'library/maps/routing')
    if not (directory/'publication.json').exists():return
    with content.locked(directory/'publication.lock'):
        recover_graph_publication(directory)


def publish_graph(staging,root):
    directory=content.destination(Path(root),'library/maps/routing')
    staging=Path(staging)
    if staging.parent.resolve()!=directory.resolve() or not staging.name.startswith('.prepare-'):
        raise setup.SetupError('Dossier de préparation du routage non reconnu.')
    with content.locked(directory/'publication.lock'):
        recover_graph_publication(directory)
        durable.sync_tree(staging)
        current=directory/'current';previous=directory/('previous-'+uuid.uuid4().hex)
        state={'phase':'pending','previous':previous.name,'staging':staging.name}
        setup.write_json(directory/'publication.json',state)
        try:
            if current.exists():durable.publish(current,previous)
            durable.publish(staging,current)
            state['phase']='complete';setup.write_json(directory/'publication.json',state)
        except BaseException:
            recover_graph_publication(directory)
            raise


def recipe():
    return json.loads((setup.ROOT/'deploy/routing-engine.json').read_text(encoding='utf-8'))


def build_user(backend,runner):
    if backend=='lab':return '0:0'
    result=runner(backend,'info','--format','{{json .SecurityOptions}}')
    try:options=json.loads(result.stdout)
    except (ValueError,AttributeError,TypeError):
        raise setup.SetupError('Mode Docker non vérifiable ; préparation du routage arrêtée.')
    if not isinstance(options,list):raise setup.SetupError('Mode Docker non vérifiable ; préparation du routage arrêtée.')
    if 'name=rootless' in options:return '0:0'
    return str(getattr(os,'getuid',lambda:1000)())+':'+str(getattr(os,'getgid',lambda:1000)())


def engine(backend,*args,check=True):
    if backend=='lab':
        import linux_lab as lab
        return lab.podman(*args,capture=True,check=check)
    try:
        return subprocess.run(['docker',*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',check=check,timeout=1800)
    except (OSError,subprocess.SubprocessError) as exc:
        raise setup.SetupError('Commande du moteur de routage indisponible ou échouée sur le PC serveur.') from exc


def start_services(app,config,backend):
    if backend=='lab':
        import linux_lab as lab
        lab.checked_mount()
        recover_publication(Path(config['data_dir']))
        root=Path(config['data_dir'])/'library/maps/routing/current'
        if not (root/'manifest.json').is_file():return
        if lab.podman('network','exists','setupsurvie-lab',check=False).returncode:
            lab.podman('network','create','setupsurvie-lab')
        for mode in recipe()['profiles']:
            name=lab.PREFIX+'router-'+mode
            if lab.podman('container','exists',name,check=False).returncode==0:
                lab.podman('rm','-f',name)
            lab.podman('run','-d','--pull=never','--name',name,'--label','project=setupsurvie-lab',
                '--network','setupsurvie-lab','--network-alias','router-'+mode,'--memory=2g','--cpus=1','--pids-limit=256',
                '--security-opt=label=disable','--security-opt=no-new-privileges','--cap-drop=ALL',
                '-v',str(root/mode)+':/data:ro',recipe()['image'],'osrm-routed','--algorithm','mld','--threads','1','/data/network.osrm')
    else:
        recover_publication(Path(config['data_dir']))
        app.render(config)
        app.compose(config,'up','-d','--pull','never','--no-deps','--force-recreate',*('router-'+mode for mode in recipe()['profiles']))


def stop_services(config,backend):
    # Called by the ordinary lab stop command; never touches Ollama.
    if backend!='lab':return
    import linux_lab as lab
    for mode in recipe()['profiles']:
        name=lab.PREFIX+'router-'+mode
        if lab.podman('container','exists',name,check=False).returncode==0:lab.podman('stop',name)


def build(root,source,bbox,*,backend='compose',storage_root=None,check=lambda:None,progress=lambda message:None,allow_download=False,runner=engine,source_url=None):
    root=setup.safe_path(root);source=Path(source)
    if source.is_symlink() or not source.is_file() or source.stat().st_size>50_000_000 or not (source.name.endswith('.osm.pbf') or source.suffix=='.osm'):
        raise setup.SetupError('Choisissez un extrait OSM de 50 Mo maximum (.osm ou .osm.pbf), sans lien symbolique.')
    if len(bbox)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in bbox):raise setup.SetupError('Zone non valide.')
    west,south,east,north=bbox
    if not -180<=west<east<180 or not -80<=south<north<=80:raise setup.SetupError('Zone non valide ou traversant le méridien 180°.')
    if east-west>2 or north-south>2:raise setup.SetupError('Préparez un extrait local de moins de deux degrés par axe.')
    config=recipe();directory=content.destination(root,'library/maps/routing');durable.mkdir(directory)
    staging=directory/('.prepare-'+uuid.uuid4().hex);durable.mkdir(staging)
    build_id=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        content.check_capacity(root,10_000_000_000,storage_root=storage_root);check()
        present=runner(backend,'image','inspect',config['image'],check=False).returncode==0
        if not present:
            if not allow_download:raise setup.SetupError('Image OSRM absente. Préparez son téléchargement sur le PC cible avec Internet.')
            progress('Téléchargement du moteur de calcul d’itinéraires (pas un modèle IA)…')
            runner(backend,'pull',config['image'])
        user=build_user(backend,runner)
        files=[];profiles=setup.ROOT/'deploy/routing'
        for mode in config['profiles']:
            check();progress('Préparation du réseau : '+mode+'…')
            folder=staging/mode;folder.mkdir();name='network.osm.pbf' if source.name.endswith('.osm.pbf') else 'network.osm'
            shutil.copyfile(source,folder/name)
            phases=[['osrm-extract','--threads','1','--data_version',build_id,'-p','/profiles/'+mode+'.lua','/data/'+name],
                    ['osrm-partition','--threads','1','/data/network.osrm'],
                    ['osrm-customize','--threads','1','/data/network.osrm']]
            for index,command in enumerate(phases):
                check();content.check_capacity(root,100_000_000,storage_root=storage_root)
                task='survie-routing-'+uuid.uuid4().hex
                stopped=threading.Event();errors=[]
                # Bind this phase's objects: a late watcher must not stop the next phase.
                def watch(stopped=stopped,errors=errors,task=task):
                    while not stopped.wait(1):
                        try:
                            check();content.check_capacity(root,100_000_000,storage_root=storage_root)
                            if sum(p.stat().st_size for p in staging.rglob('*') if p.is_file())>10_000_000_000:raise setup.SetupError('Préparation limitée à 10 Go.')
                        except Exception as exc:
                            errors.append(exc);runner(backend,'kill',task,check=False);return
                watcher=threading.Thread(target=watch,daemon=True);watcher.start()
                try:
                    # Rootless Podman/Docker map container UID 0 to the PC user. An
                    # explicit host UID instead maps to a subordinate user that
                    # cannot write these bind mounts (or traverse the SSD root).
                    runner(backend,'run','--rm','--pull=never','--name',task,'--network=none','--cpus=2','--memory=4g','--pids-limit=512',
                        '--cap-drop=ALL','--security-opt=no-new-privileges','--security-opt=label=disable',
                        '--user',user,
                        '-v',str(folder)+':/data','-v',str(profiles)+':/profiles:ro',config['image'],*command)
                except Exception:
                    if errors:raise errors[0]
                    raise
                finally:stopped.set();watcher.join(timeout=3)
                if errors:raise errors[0]
            (folder/name).unlink()
            output=list(folder.glob('network.osrm*'))
            if not output:raise setup.SetupError('Le moteur n’a pas créé de graphe exploitable.')
            for path in output:
                if path.is_symlink() or not path.is_file():raise setup.SetupError('Sortie de routage non valide.')
                # OSRM writes some indices mode 0600. Serving containers drop all
                # capabilities, so publish non-private OSM graph files readable.
                path.chmod(0o644)
                files.append({'path':mode+'/'+path.name,'bytes':path.stat().st_size,'sha256':setup.file_hash(path)})
        content.check_capacity(root,100_000_000,storage_root=storage_root);check()
        manifest={'complete':True,'engine':'OSRM','version':config['version'],'image':config['image'],'build_id':build_id,
                  'created':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),'bbox':bbox,'profiles':config['profiles'],
                  'source':{'name':source.name,'sha256':setup.file_hash(source)},'profile_sha256':{m:setup.file_hash(profiles/(m+'.lua')) for m in config['profiles']},
                  'files':files,'attribution':config['attribution']}
        if source_url:manifest['source']['url']=source_url
        setup.write_json(staging/'manifest.json',manifest)
        publish_graph(staging,root)
        return manifest
    finally:
        if staging.exists():shutil.rmtree(staging)


def prepare_area(root,options,*,backend,storage_root=None,check=lambda:None,progress=lambda message:None):
    options=geography_data.validate(options);lat,lon=options['lat'],options['lon'];radius=options['radius_km']
    dy=(radius+1)/110.5;dx=(radius+1)/(111.32*math.cos(math.radians(lat)));bbox=[lon-dx,lat-dy,lon+dx,lat+dy]
    if bbox[0]<-180 or bbox[2]>=180:raise setup.SetupError('Zone traversant le méridien 180° non prise en charge.')
    with content.locked(root/'catalog/content.lock'):
        content.check_capacity(root,10_000_000_000,storage_root=storage_root)
        progress('Téléchargement des voies et restrictions OpenStreetMap…')
        south,west,north,east=bbox[1],bbox[0],bbox[3],bbox[2]
        query=f'[out:xml][timeout:90][maxsize:134217728];way["highway"]({south},{west},{north},{east})->.roads;rel(bw.roads)["type"="restriction"]->.restrictions;(.roads;.restrictions;);(._;>>;);out body;'
        raw,endpoint=geography_data.fetch_overpass(query,maximum=50_000_000,check=check)
        document=ET.fromstring(raw)
        if document.tag!='osm' or document.find('remark') is not None or document.find('way') is None:raise setup.SetupError('Réseau incomplet ou vide. Réduisez la zone et réessayez.')
        directory=content.destination(root,'library/maps/routing');directory.mkdir(parents=True,exist_ok=True)
        source=directory/('source-'+uuid.uuid4().hex+'.osm')
        try:
            source.write_bytes(raw)
            return build(root,source,bbox,backend=backend,storage_root=storage_root,check=check,progress=progress,allow_download=True,source_url=endpoint)
        finally:source.unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-dir',required=True)
    parser.add_argument('--backend',choices=['compose','lab'],default='compose');parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--bbox',nargs=4,type=float,required=True);parser.add_argument('--allow-download',action='store_true')
    args=parser.parse_args();app=setup.Installation(args.work_dir);config=app.load();root=Path(config['data_dir']);scope=None
    if args.backend=='lab':
        import linux_lab as lab
        lab.checked_mount();scope=lab.MOUNT
        if root!=lab.MOUNT/'data':raise setup.SetupError('Données hors du volume du laboratoire.')
    with content.locked(root/'catalog/content.lock'):
        build(root,args.source,args.bbox,backend=args.backend,storage_root=scope,allow_download=args.allow_download,progress=print)
    start_services(app,config,args.backend)
    print('Réseau préparé ; le calcul local reste indépendant du GPS et d’Ollama.')


if __name__=='__main__':main()
