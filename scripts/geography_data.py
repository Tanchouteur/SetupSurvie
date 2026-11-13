"""Prepare bounded offline OSM addresses/places and Mapzen terrain on the data disk."""
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import urllib.parse
import urllib.request
import urllib.error
import uuid

import content
import setup
from pilot import durable

ATTRIBUTION='© OpenStreetMap contributors · ODbL 1.0. Terrain: Mapzen; Europe: Copernicus EU-DEM; global: USGS SRTM/GMTED2010, NOAA ETOPO1.'
OVERPASS_SERVERS=('https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter',
                  'https://maps.mail.ru/osm/tools/overpass/api/interpreter')


def validate(body):
    lat,lon=body.get('lat'),body.get('lon');radius=body.get('radius_km',10)
    if type(lat) not in (int,float) or type(lon) not in (int,float) or not math.isfinite(lat) or not math.isfinite(lon) or not -80<=lat<=80 or not -180<=lon<180:
        raise setup.SetupError('Coordonnées de préparation non valides.')
    if type(radius) is not int or not 1<=radius<=25:raise setup.SetupError('Rayon de préparation entre 1 et 25 km.')
    if type(body.get('terrain',True)) is not bool:raise setup.SetupError('Choix de relief non valide.')
    if type(body.get('places',True)) is not bool:raise setup.SetupError('Choix de lieux non valide.')
    return {'lat':float(lat),'lon':float(lon),'radius_km':radius,'terrain':body.get('terrain',True),'places':body.get('places',True)}


def fetch(url, *, data=None, maximum=30_000_000, check=lambda:None):
    req=urllib.request.Request(url,data=data,headers={'User-Agent':'SetupSurvie offline preparation/0.1.10','Content-Type':'application/x-www-form-urlencoded'})
    # Fixed providers only; no redirects to arbitrary hosts.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):return None
    with urllib.request.build_opener(NoRedirect).open(req,timeout=100) as response:
        raw=bytearray()
        while True:
            check();chunk=response.read(262144)
            if not chunk:break
            raw.extend(chunk)
            if len(raw)>maximum:raise setup.SetupError('Réponse trop volumineuse ; réduisez la zone.')
    return bytes(raw)


def categories(tags):
    result=[];amenity=tags.get('amenity');natural=tags.get('natural');shop=tags.get('shop')
    if amenity in ('drinking_water','water_point','fountain') or natural in ('spring','water') or tags.get('man_made')=='water_well':result.append('water')
    if shop in ('supermarket','convenience','bakery','greengrocer','farm','butcher') or amenity=='marketplace':result.append('food')
    if amenity in ('pharmacy','hospital','clinic','doctors') or tags.get('healthcare'):result.append('health')
    if amenity=='shelter' or tags.get('tourism') in ('camp_site','alpine_hut','wilderness_hut'):result.append('shelter')
    if shop in ('hardware','doityourself','bicycle','car_repair'):result.append('repair')
    if amenity in ('telephone','post_office'):result.append('communication')
    return result


def fetch_overpass(query,*,maximum,check=lambda:None,reader=None):
    """Use fixed public providers, retaining the actual source in the bundle."""
    reader=reader or fetch
    for index,url in enumerate(OVERPASS_SERVERS):
        check()
        try:
            encoded=urllib.parse.urlencode({'data':query})
            if url.startswith('https://maps.mail.ru/'):
                return reader(url+'?'+encoded,maximum=maximum,check=check),url
            return reader(url,data=encoded.encode(),maximum=maximum,check=check),url
        except urllib.error.HTTPError as exc:
            if exc.code not in (429,500,502,503,504) or index==len(OVERPASS_SERVERS)-1:raise
        except (urllib.error.URLError,TimeoutError):
            if index==len(OVERPASS_SERVERS)-1:raise


def parse_places(value):
    if value.get('remark'):raise setup.SetupError('Extraction OSM incomplète ; réduisez la zone et réessayez.')
    places=[];addresses=[]
    elements=value.get('elements')
    if not isinstance(elements,list) or len(elements)>150000:raise setup.SetupError('Trop de lieux ; réduisez la zone.')
    for element in elements:
        tags=element.get('tags',{});point=element.get('center',element)
        lat,lon=point.get('lat'),point.get('lon')
        if type(lat) not in (int,float) or type(lon) not in (int,float) or not -85<=lat<=85 or not -180<=lon<180:continue
        identifier=str(element['type'])+'/'+str(element['id'])
        address=' '.join(str(tags.get(k,'')) for k in ('addr:housenumber','addr:street','addr:postcode','addr:city')).strip()
        label=str(tags.get('name') or address or tags.get('amenity') or tags.get('natural') or tags.get('shop') or 'Lieu cartographié')[:300]
        base={'id':identifier,'lat':lat,'lon':lon,'label':label}
        kinds=categories(tags)
        if kinds:
            places.append({**base,'categories':kinds,'address':address[:300],'tags':{k:tags[k] for k in ('amenity','natural','shop','drinking_water','access','opening_hours','phone','ele','tourism','healthcare') if k in tags}})
        if address or tags.get('place'):
            addresses.append({**base,'label':(address or label)[:300]})
    return {'places':places,'addresses':addresses}


def prepare(root,options,*,storage_root=None,check=lambda:None,progress=lambda message:None,reader=fetch):
    options=validate(options);lat,lon,radius=options['lat'],options['lon'],options['radius_km']
    date=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    identifier=hashlib.sha256(json.dumps({**options,'date':date},sort_keys=True).encode()).hexdigest()[:20]
    directory=content.destination(root,'library/maps/geography');durable.mkdir(directory)
    final=directory/identifier
    if final.exists():
        manifest=json.loads((final/'manifest.json').read_text(encoding='utf-8'))
        for item in manifest['files']:
            if setup.file_hash(final/item['path'])!=item['sha256']:raise setup.SetupError('Données existantes altérées ; conservées pour examen.')
        return manifest
    # Stage on the data disk and publish the whole bundle only after validation.
    staging=directory/('.prepare-'+uuid.uuid4().hex);durable.mkdir(staging)
    try:
        with content.locked(root/'catalog/content.lock'):
            content.check_capacity(root,300_000_000,storage_root=storage_root)
            def guard():
                check();content.check_capacity(root,10_000_000,storage_root=storage_root)
            progress('Téléchargement des adresses et lieux OpenStreetMap…' if options['places'] else 'Préparation indépendante du relief…')
            area=f'(around:{radius*1000},{lat},{lon})'
            filters=['["addr:street"]','["place"]','["amenity"~"^(drinking_water|water_point|fountain|marketplace|pharmacy|hospital|clinic|doctors|shelter|telephone|post_office)$"]','["natural"~"^(spring|water)$"]','["man_made"="water_well"]','["shop"~"^(supermarket|convenience|bakery|greengrocer|farm|butcher|hardware|doityourself|bicycle|car_repair)$"]','["tourism"~"^(camp_site|alpine_hut|wilderness_hut)$"]','["healthcare"]']
            query='[out:json][timeout:75][maxsize:67108864];('+''.join('nwr'+f+area+';' for f in filters)+');out center tags;'
            if options['places']:
                raw,source=fetch_overpass(query,maximum=30_000_000,check=guard,reader=reader)
            else:
                raw=b'{"elements":[]}';source='local:empty-places-not-prepared'
            parsed=parse_places(json.loads(raw));setup.write_json(staging/'places.json',parsed)
            files=[{'path':'places.json','source':source,'source_sha256':hashlib.sha256(raw).hexdigest()}]
            if options['terrain']:
                dy=radius/110.5;dx=radius/(111.32*math.cos(math.radians(lat)))
                if lon-dx < -180 or lon+dx >= 180:raise setup.SetupError('Zone traversant le méridien 180° non prise en charge.')
                tiles=[(a,b) for a in range(math.floor(lat-dy),math.floor(lat+dy)+1) for b in range(math.floor(lon-dx),math.floor(lon+dx)+1)]
                if len(tiles)>9:raise setup.SetupError('Réduisez le rayon pour limiter le relief à neuf dalles.')
                for a,b in tiles:
                    guard();name=f'{"N" if a>=0 else "S"}{abs(a):02d}{"E" if b>=0 else "W"}{abs(b):03d}'
                    progress('Téléchargement du relief : '+name+'…')
                    url=f'https://elevation-tiles-prod.s3.amazonaws.com/skadi/{name[:3]}/{name}.hgt.gz'
                    compressed=reader(url,maximum=30_000_000,check=guard)
                    import io
                    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as archive:
                        grid=archive.read(3601*3601*2+1)
                    if len(grid) not in (1201*1201*2,3601*3601*2):raise setup.SetupError('Dalle de relief non valide.')
                    (staging/(name+'.hgt')).write_bytes(grid)
                    files.append({'path':name+'.hgt','source':url})
            attribution=setup.ROOT/'deploy/terrain-attribution.txt'
            shutil.copyfile(attribution,staging/'attribution.txt');files.append({'path':'attribution.txt','source':'https://github.com/tilezen/joerd/blob/master/docs/attribution.md'})
            for item in files:
                guard();path=staging/item['path'];item.update(bytes=path.stat().st_size,sha256=setup.file_hash(path))
            manifest={'schema':1,'complete':True,'created':date,'center':[lon,lat],'radius_km':radius,'terrain':options['terrain'],'places_prepared':options['places'],'places':len(parsed['places']),'addresses':len(parsed['addresses']),'files':files,'bytes':sum(f['bytes'] for f in files),'attribution':ATTRIBUTION,'integrity':'Empreintes calculées à la réception HTTPS ; pas des empreintes publiées par les fournisseurs.'}
            setup.write_json(staging/'manifest.json',manifest)
            check();durable.sync_tree(staging);durable.publish(staging,final)
            return manifest
    finally:
        if staging.exists():shutil.rmtree(staging)
