#!/usr/bin/env python3
"""Reconstitute map/routing services from the kit in disposable containers on the existing lab image cache.

No user state, model directory, GPU, published port, image pull or Internet route.
The cache is shared: this is not a clean-machine installation test.
Run pilot_kit.py verify first for the full payload hash audit.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

import kit_audit
import setup


def audit(kit,output):
    import linux_lab as lab
    lab.checked_mount();kit=setup.safe_path(kit);output=setup.safe_path(output)
    if not kit.is_relative_to(lab.MOUNT) or not output.is_relative_to(lab.MOUNT):
        raise setup.SetupError('Kit et rapport doivent rester sur le volume SSD dédié.')
    manifest=json.loads((kit/'manifest.json').read_text());closure=kit_audit.validate(kit,manifest)
    if not closure['routing'] or not closure['geography_zones']:raise setup.SetupError('Le kit ne contient pas de zone avec routage et géographie.')
    images=json.loads((kit/'images.tar.json').read_text())['images'];by_name={e['service']:e for e in images}
    if shutil.disk_usage(lab.MOUNT).free<(kit/'images.tar').stat().st_size*2+20_000_000_000:
        raise setup.SetupError('Marge insuffisante pour le stockage de recette isolé.')
    token=uuid.uuid4().hex[:12];base=lab.MOUNT/'tmp'/('offline-kit-'+token);base.mkdir(mode=0o700)
    runroot=Path('/run/user')/str(os.getuid())/'setupsurvie'
    (base/'tmp').mkdir();setup.write_json(base/'auth.json',{'auths':{}},private=True)
    env=os.environ.copy();env.update(TMPDIR=str(base/'tmp'),REGISTRY_AUTH_FILE=str(base/'auth.json'))
    prefix=['podman','--root',str(lab.MOUNT/'containers'),'--runroot',str(runroot/'storage'),
            '--tmpdir',str(runroot/'libpod'),'--events-backend=none']
    def engine(*args,check=True):
        return subprocess.run([*prefix,*map(str,args)],env=env,capture_output=True,text=True,check=check)
    names=[];network='offline-kit-'+token;network_created=False
    try:
        print('Import des images du kit dans le cache du laboratoire, sans registre…',flush=True)
        engine('load','-i',kit/'images.tar')
        for entry in images:
            value=json.loads(engine('image','inspect',entry['id']).stdout)[0]
            if setup.canonical_image_id(value['Id'])!=setup.canonical_image_id(entry['id']):raise setup.SetupError('Image importée différente du kit.')
        maps=base/'maps';shutil.copytree(kit/'payload/library/maps',maps)
        # Only map bundles are copied. Model files and real databases are not mounted.
        app=setup.Installation(base/'private')
        app.prepare({'data_dir':str(kit/'payload')},offline=True)
        engine('network','create','--internal',network);network_created=True
        for mode in ('foot','motorcycle','car'):
            name='audit-'+token+'-'+mode;names.append(name)
            engine('run','-d','--pull=never','--name',name,'--network',network,'--network-alias','router-'+mode,
                   '--security-opt=label=disable','--security-opt=no-new-privileges','--cap-drop=ALL','--cpus=1','--memory=2g',
                   '-v',str(maps/'routing/current'/mode)+':/data:ro',by_name['routing']['id'],
                   'osrm-routed','--algorithm','mld','--threads','1','/data/network.osrm')
        code='''import asyncio,json,time,urllib.request
from pilot import routing,geography,maps
async def main():
 result={'maps':len(maps.available()),'geography':geography.status()['datasets'],'routes':{}}
 assert result['maps']>=1 and result['geography']
 lon,lat=result['geography'][0]['center']
 result['elevation']=geography.elevation(lat,lon)['elevation_m']
 assert result['elevation'] is not None
 for mode in ('foot','motorcycle','car'):
  points=[]
  for x,y in [(lon,lat),(lon+.008,lat-.003)]:
   for attempt in range(30):
    try:
     with urllib.request.urlopen(routing.URLS[mode]+f'/nearest/v1/driving/{x},{y}?number=1',timeout=2) as response:value=json.load(response)
     break
    except OSError:
     if attempt==29:raise
     await asyncio.sleep(.2)
   point=value['waypoints'][0]['location'];points.append({'lon':point[0],'lat':point[1],'title':'Recette hors ligne'})
  route=await routing.calculate(points,mode,4 if mode=='foot' else 40)
  result['routes'][mode]={'distance_m':route['distance_m'],'duration_s':route['duration_s']}
 print(json.dumps(result,ensure_ascii=False))
asyncio.run(main())
'''
        print('Lecture des cartes, relief et trajets sur le réseau interne sans Internet…',flush=True)
        result=engine('run','--rm','--pull=never','--network',network,'--workdir','/srv','--cpus=1','--memory=2g',
                      '--security-opt=label=disable','--security-opt=no-new-privileges','--cap-drop=ALL',
                      '-v',str(kit/'app/pilot')+':/srv/pilot:ro','-v',str(maps)+':/maps:ro',
                      '--entrypoint','python',by_name['open-webui']['id'],'-c',code)
        results=json.loads(result.stdout.strip().splitlines()[-1])
        report={'passed':True,'offline_dependencies':closure,'map_test':results,'network':'internal, no Internet gateway',
                'image_store':'existing lab cache; not a clean installation','models_started':False,'real_user_state_mounted':False,'windows_installation_tested':False}
        setup.write_json(output,report)
        print('Recette hors ligne réussie ; aucun compte réel, modèle ou GPU utilisé.',flush=True)
        return report
    except subprocess.CalledProcessError as exc:
        print((exc.stderr or '')[-3000:],flush=True)
        raise setup.SetupError('Échec de la reconstitution hors ligne isolée.') from exc
    finally:
        for name in names:engine('rm','-f',name,check=False)
        if network_created:engine('network','rm',network,check=False)
        # Never remove images or runtime storage shared with the actual lab.
        engine('unshare','rm','-rf',base,check=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('kit');parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:audit(args.kit,args.output)
    except (setup.SetupError,OSError,ValueError,KeyError) as exc:print('ERREUR :',exc);raise SystemExit(1)
