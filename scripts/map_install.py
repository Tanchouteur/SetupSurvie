"""Prepare the default offline maps during installation, independently of AI."""
import hashlib
import io
import json
from pathlib import Path
import platform
import tarfile
import urllib.request
import zipfile

import content
import setup
from content_mirrors import network_open
from pilot import durable


# The pinned archive is hash-checked first; this only bounds decompression.
# go-pmtiles 1.31.2 for Linux x64 is 57.7 MB once extracted.
TOOL_LIMIT=150_000_000

def recipe():
    return json.loads((setup.ROOT/'deploy/map-catalog.json').read_text(encoding='utf-8'))


def installed(root, specification):
    manifest=content.destination(root,'library/maps/manifest.json')
    if not manifest.exists():return False
    records={m['id']:m for m in json.loads(manifest.read_text(encoding='utf-8'))['maps']}
    for wanted in specification['maps']:
        item=records.get(wanted['id'],{})
        if any(item.get(k)!=wanted.get(k) for k in ('bbox','maxzoom')):return False
        name=item.get('path','')
        if not name or Path(name).name!=name:return False
        path=content.destination(root,'library/maps/'+name)
        if not path.is_file() or path.stat().st_size!=item.get('bytes'):return False
        if setup.file_hash(path)!=item.get('sha256'):return False
        with path.open('rb') as stream:
            if stream.read(8)!=b'PMTiles\x03':return False
    return True


def tool(root, specification):
    config=specification['tool']
    system=platform.system();machine=platform.machine().lower()
    if machine not in ('amd64','x86_64') or system not in ('Windows','Linux'):
        raise setup.SetupError('Préparation des cartes : outil automatique disponible sur Windows/Linux x64.')
    windows=system=='Windows'
    url=config['windows_x86_64_url'] if windows else config['linux_x86_64_url']
    expected=config['windows_sha256'] if windows else config['sha256']
    folder=content.destination(root,'tools/pmtiles-'+config['version'])
    durable.mkdir(folder)
    archive=folder/('windows-x64.zip' if windows else 'linux-x64.tar.gz')
    if archive.exists() and setup.file_hash(archive)!=expected:
        raise setup.SetupError('Archive PMTiles modifiée, conservée pour examen : '+str(archive))
    if not archive.exists():
        print('Préparation de l’outil cartographique vérifié…',flush=True)
        request=urllib.request.Request(url,headers={'User-Agent':'SetupSurvie-offline-maps/0.1'})
        with network_open(request,timeout=60) as response:raw=response.read(50_000_001)
        if len(raw)>50_000_000 or hashlib.sha256(raw).hexdigest()!=expected:
            raise setup.SetupError('Empreinte de l’outil cartographique incorrecte ; aucun programme exécuté.')
        durable.write_bytes(archive,raw)
    raw=archive.read_bytes()
    if windows:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            binary=bundle.read('pmtiles.exe')
    else:
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as bundle:
            members=[m for m in bundle.getmembers() if m.isfile() and Path(m.name).name=='pmtiles']
            if len(members)!=1:raise setup.SetupError('Archive de l’outil cartographique ambiguë.')
            with bundle.extractfile(members[0]) as stream:binary=stream.read(TOOL_LIMIT+1)
    if len(binary)>TOOL_LIMIT:raise setup.SetupError('Outil cartographique trop volumineux.')
    target=folder/('pmtiles.exe' if windows else 'pmtiles')
    if not target.exists() or target.read_bytes()!=binary:durable.write_bytes(target,binary)
    target.chmod(0o755)
    return target


def geography_ready(root, options, *, require_places=False):
    directory=content.destination(root,'library/maps/geography')
    for manifest in sorted(directory.glob('*/manifest.json'),reverse=True):
        if manifest.is_symlink():continue
        value=json.loads(manifest.read_text(encoding='utf-8'))
        if not value.get('complete') or value.get('center')!=[options['lon'],options['lat']]:continue
        if value.get('radius_km',0)<options['radius_km'] or not value.get('terrain'):continue
        if require_places and not value.get('places_prepared',True):continue
        valid=True
        for item in value.get('files',[]):
            if Path(item['path']).name!=item['path']:valid=False;break
            path=content.destination(root,str(manifest.parent.relative_to(root)).replace('\\','/')+'/'+item['path'])
            if not path.is_file() or path.stat().st_size!=item['bytes'] or setup.file_hash(path)!=item['sha256']:valid=False;break
        if valid and any(i['path'].endswith('.hgt') for i in value.get('files',[])):return value
    return None


def ensure(root, *, offline=False):
    root=setup.safe_path(root);specification=recipe()
    ready=installed(root,specification)
    if not ready and not offline:
        import maps
        maps.prepare(root,tool(root,specification))
        ready=installed(root,specification)
        if not ready:raise setup.SetupError('Les cartes de base ne sont pas toutes vérifiées. Reprenez la préparation.')
    options=specification.get('geography')
    geography=geography_ready(root,options) if options else None
    if options and not geography and not offline:
        import geography_data
        geography_data.prepare(root,{**options,'places':False},progress=lambda message:print(message,flush=True))
        geography=geography_ready(root,options)
        if not geography:raise setup.SetupError('Relief et lieux locaux incomplets. Reprenez la préparation.')
    places=geography_ready(root,options,require_places=True) if options else None
    places_error=None
    if options and not places and not offline:
        import geography_data
        try:
            geography_data.prepare(root,options,progress=lambda message:print(message,flush=True))
            places=geography_ready(root,options,require_places=True)
        except (OSError,setup.SetupError,ValueError) as exc:
            places_error=str(exc)
            print('ATTENTION : fonds et relief conservés, mais adresses et lieux non préparés : '+places_error,flush=True)
    complete=ready and (not options or bool(geography))
    setup.write_json(root/'catalog/map-installation.json',{
        'status':'ready' if complete else 'missing',
        'basemap_status':'ready' if ready else 'missing',
        'geography_status':'ready' if geography else 'missing',
        'places_status':'ready' if places else 'missing','places_error':places_error,
        'required':[m['id'] for m in specification['maps']],
        'offline':offline,'routing_included':False,'elevation_included':bool(geography),
        'geography_options':options})
    print('Cartes de base vérifiées : Sud et Solliès-Ville.' if ready else
          'ATTENTION : ce kit ne contient pas les cartes de base. Elles restent à préparer avec Internet.',flush=True)
    if options:print('Relief local vérifié.' if geography else
                     'ATTENTION : relief local absent de ce kit.',flush=True)
    if options and not places:print('Adresses et points d’intérêt : préparation à reprendre avec prepare-maps.',flush=True)
    return complete
