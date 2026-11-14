"""Local household locations, offline address/POI search and HGT terrain tools."""
from contextlib import ExitStack
from functools import lru_cache
import json
import hashlib
import threading
import math
import mmap
from pathlib import Path
import struct
import time
import unicodedata
import uuid
import zlib

import httpx
from fastapi import HTTPException
from . import maps, store

CATEGORIES = {'water':'Points d’eau', 'food':'Alimentation', 'health':'Santé', 'shelter':'Abri', 'repair':'Réparation', 'communication':'Communications'}
NOTE = 'Lieux cartographiés non exhaustifs. Repères datés. Distance à vol d’oiseau, sans itinéraire ni garantie d’accès, d’ouverture ou de potabilité.'


def coordinates(lat, lon):
    if type(lat) not in (int,float) or type(lon) not in (int,float) or not math.isfinite(lat) or not math.isfinite(lon) or not -85 <= lat <= 85 or not -180 <= lon < 180:
        raise ValueError('Coordonnées non valides (latitude −85 à 85, longitude −180 à 180).')
    return float(lat), float(lon)


def load(key, default=None):
    with store.connect() as db:
        row = db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    return json.loads(row[0]) if row else default


def save(key, value):
    with store.connect() as db:
        db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,json.dumps(value,ensure_ascii=False)))


def settings():
    return {'home':load('home'), 'departure':load('departure'), 'categories':CATEGORIES}


def location():
    result = load('departure') or load('home')
    if not result:raise ValueError('Choisissez un domicile ou un point de départ dans Paramètres.')
    return {**result, 'note':'Point enregistré pour cet appareil ; ce n’est pas une position GPS en direct.'}


def set_location(target, candidate=None, lat=None, lon=None, label='Point choisi sur la carte'):
    if target not in ('home','departure'):raise ValueError('Emplacement inconnu.')
    if candidate:
        value = load('candidate:'+candidate)
        if not value or time.time()-value['created']>86400:raise ValueError('Résultat expiré. Relancez la recherche.')
        value={k:v for k,v in value.items() if k not in ('created','id')}
    else:
        lat,lon=coordinates(lat,lon)
        value={'lat':lat,'lon':lon,'label':label[:200], 'method':'map', 'source':'Position choisie manuellement, adresse non vérifiée'}
    value['saved_at']=time.time();save(target,value)
    return value


def offer(values):
    result=[]
    with store.connect() as db:
        db.execute("DELETE FROM settings WHERE key LIKE 'candidate:%' AND json_extract(value,'$.created')<?",(time.time()-86400,))
        db.execute("DELETE FROM settings WHERE key IN (SELECT key FROM settings WHERE key LIKE 'candidate:%' ORDER BY json_extract(value,'$.created') DESC LIMIT -1 OFFSET 200)")
        for value in values[:8]:
            identifier=uuid.uuid4().hex
            item={**value,'id':identifier,'created':time.time()}
            db.execute('INSERT INTO settings VALUES(?,?)',('candidate:'+identifier,json.dumps(item,ensure_ascii=False)))
            result.append(item)
    return result


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))


def datasets():
    root=maps.ROOT/'geography'
    if not root.exists() or root.is_symlink():return []
    result=[]
    for manifest in sorted(root.glob('*/manifest.json')):
        if manifest.is_symlink() or not manifest.resolve().is_relative_to(root.resolve()) or manifest.stat().st_size>200_000:continue
        try:
            value=json.loads(manifest.read_text(encoding='utf-8'))
            if not value.get('complete'):continue
            # Only publish complete, size-checked local bundles.
            for item in value['files']:
                path=manifest.parent/item['path']
                if Path(item['path']).name!=item['path'] or path.is_symlink() or not path.is_file() or path.stat().st_size!=item['bytes']:break
            else:
                result.append((manifest.parent,value))
        except (OSError,ValueError,KeyError,TypeError):continue
    return sorted(result,key=lambda pair:pair[1].get('created',''),reverse=True)


def status():
    return {'datasets':[{'id':root.name,**{k:value.get(k) for k in ('created','center','radius_km','places','addresses','terrain','attribution','bytes')},'places_prepared':value.get('places_prepared',True)} for root,value in datasets()], 'note':NOTE}


def local_addresses(query):
    words=normalize(query).split(); found=[]; seen=set()
    for point in (load('home'),load('departure')):
        if point and all(w in normalize(point['label']) for w in words):
            found.append({**point,'method':'saved'});seen.add((point['lat'],point['lon'],point['label']))
    for root,manifest in datasets():
        for item in json.loads((root/'places.json').read_text(encoding='utf-8'))['addresses']:
            key=(item['lat'],item['lon'],item['label'])
            if key not in seen and all(w in normalize(item['label']) for w in words):
                found.append({**item,'method':'offline','source':'OpenStreetMap · '+manifest['created']});seen.add(key)
                if len(found)>=8:return offer(found)
    return offer(found)


async def addresses(query, online=False):
    if not online:return {'results':local_addresses(query),'mode':'offline','note':'Uniquement les adresses et lieux téléchargés. Sinon, choisissez un point sur la carte ou saisissez ses coordonnées.'}
    if not store.limit('geocoding',maximum=1,period=1):raise HTTPException(429,'Attendez une seconde avant de relancer la recherche.')
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=12,follow_redirects=False) as client:
            response=await client.get('https://data.geopf.fr/geocodage/search',params={'q':query,'limit':5},headers={'User-Agent':'SetupSurvie/0.1.10'})
            response.raise_for_status()
            if len(response.content)>200_000:raise ValueError()
            values=[]
            for feature in response.json().get('features',[])[:5]:
                lon,lat=feature['geometry']['coordinates'];coordinates(lat,lon)
                props=feature['properties']
                values.append({'label':str(props['label'])[:300],'lat':lat,'lon':lon,'method':'online','source':'IGN Géoplateforme / BAN','precision':props.get('type','unknown')})
        return {'results':offer(values),'mode':'online','note':'Choisissez le résultat et vérifiez son emplacement. Un résultat peut désigner une rue ou une commune plutôt qu’un numéro.'}
    except (httpx.HTTPError,ValueError,KeyError,TypeError):raise HTTPException(503,'Recherche en ligne indisponible. Utilisez les données hors ligne ou choisissez un point.')


def distance(lat1,lon1,lat2,lon2):
    lat1,lon1=coordinates(lat1,lon1);lat2,lon2=coordinates(lat2,lon2)
    a,b=map(math.radians,(lat1,lat2));dl=math.radians(lon2-lon1)
    h=math.sin((b-a)/2)**2+math.cos(a)*math.cos(b)*math.sin(dl/2)**2
    return round(6371008.8*2*math.asin(min(1,math.sqrt(h))),1)


def nearby(category, radius_km=5, lat=None, lon=None):
    if category not in CATEGORIES:raise ValueError('Choisissez une catégorie proposée.')
    if type(radius_km) not in (int,float) or not 0<radius_km<=25:raise ValueError('Rayon entre 0 et 25 km.')
    if lat is None and lon is None:
        point=location();lat,lon=point['lat'],point['lon']
    lat,lon=coordinates(lat,lon);found=[];seen=set();coverage=[]
    for root,manifest in datasets():
        if not manifest.get('places_prepared',True):continue
        coverage.append({'center':manifest['center'],'radius_km':manifest['radius_km'],'created':manifest['created']})
        for item in json.loads((root/'places.json').read_text(encoding='utf-8'))['places']:
            if category not in item['categories'] or item['id'] in seen:continue
            seen.add(item['id']);meters=distance(lat,lon,item['lat'],item['lon'])
            if meters<=radius_km*1000:found.append({**item,'distance_m':meters,'edition':manifest['created'],'map_url':'/cartes.html?lat='+str(item['lat'])+'&lon='+str(item['lon'])})
    covered=any(distance(lat,lon,c['center'][1],c['center'][0])+radius_km*1000<=c['radius_km']*1000 for c in coverage)
    note=NOTE+(' Couverture locale partielle ou extérieure au rayon préparé : des lieux peuvent manquer.' if coverage and not covered else '')
    return {'origin':{'lat':lat,'lon':lon},'fully_covered':covered,'results':sorted(found,key=lambda p:p['distance_m'])[:12],'coverage':coverage,'note':note if coverage else 'Aucune donnée de lieux téléchargée. Ce résultat ne signifie pas qu’aucun lieu n’existe.'}


def tile_name(lat,lon):
    lat,lon=math.floor(lat),math.floor(lon)
    return f'{"N" if lat>=0 else "S"}{abs(lat):02d}{"E" if lon>=0 else "W"}{abs(lon):03d}.hgt'


class Heights:
    def __enter__(self):
        self.stack=ExitStack();self.grids={};self.sources=[]
        for root,value in datasets():
            for item in value['files']:
                if not item['path'].endswith('.hgt') or item['path'] in self.grids:continue
                path=root/item['path'];n=math.isqrt(item['bytes']//2)
                if n not in (1201,3601) or n*n*2!=item['bytes']:continue
                stream=self.stack.enter_context(path.open('rb'))
                grid=self.stack.enter_context(mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ))
                self.grids[path.name]=(grid,n)
            self.sources.append(value['created'])
        return self
    def __exit__(self,*args):return self.stack.__exit__(*args)
    def sample(self,lat,lon):
        pair=self.grids.get(tile_name(lat,lon))
        if pair is None:return None
        grid,n=pair;fx=(lon-math.floor(lon))*(n-1);fy=(1-(lat-math.floor(lat)))*(n-1)
        x=min(n-2,math.floor(fx));y=min(n-2,math.floor(fy));dx=fx-x;dy=fy-y
        a,b=struct.unpack_from('>hh',grid,2*(y*n+x));c,d=struct.unpack_from('>hh',grid,2*((y+1)*n+x))
        if -32768 in (a,b,c,d):return None
        return round((a*(1-dx)+b*dx)*(1-dy)+(c*(1-dx)+d*dx)*dy,2)


def _height_samples(heights, latitudes, longitudes):
    # Resolve horizontal interpolation once for all rows; avoid 66,564 complete
    # coordinate lookups and rounded public elevation calls for every tile.
    columns=[]
    for lon in longitudes:
        lon=((lon+180)%360)-180;east=math.floor(lon)
        columns.append((east,lon-east))
    rows=[]
    for lat in latitudes:
        north=math.floor(lat);row=[];prepared={}
        for east,fraction in columns:
            if east not in prepared:
                pair=heights.grids.get(tile_name(lat,east+.5))
                if pair:
                    grid,n=pair;fy=(1-(lat-north))*(n-1);y=min(n-2,math.floor(fy))
                    prepared[east]=(grid,n,y,fy-y)
                else:prepared[east]=None
            pair=prepared[east]
            if pair is None:row.append(None);continue
            grid,n,y,dy=pair;fx=fraction*(n-1);x=min(n-2,math.floor(fx));dx=fx-x
            a,b=struct.unpack_from('>hh',grid,2*(y*n+x));c,d=struct.unpack_from('>hh',grid,2*((y+1)*n+x))
            row.append(None if -32768 in (a,b,c,d) else (a*(1-dx)+b*dx)*(1-dy)+(c*(1-dx)+d*dx)*dy)
        rows.append(row)
    return rows


def elevation(lat,lon):
    lat,lon=coordinates(lat,lon)
    with Heights() as heights:
        return {'lat':lat,'lon':lon,'elevation_m':heights.sample(lat,lon),'source':'Mapzen Terrain Tiles / Skadi','editions':heights.sources,'note':'Altitude approximative du terrain ; pas la hauteur des bâtiments. Valeur absente si la zone n’est pas préparée.'}


def profile(lat1,lon1,lat2,lon2):
    meters=distance(lat1,lon1,lat2,lon2)
    if abs(lon2-lon1)>180:raise ValueError('Profil traversant le méridien 180° non pris en charge.')
    if meters>50000:raise ValueError('Profil limité à 50 km à vol d’oiseau.')
    with Heights() as heights:
        points=[{'distance_m':round(meters*i/40),'elevation_m':heights.sample(lat1+(lat2-lat1)*i/40,lon1+(lon2-lon1)*i/40)} for i in range(41)]
    return {'distance_m':meters,'points':points,'note':'Coupe du terrain en ligne droite, pas un chemin praticable ni un itinéraire. Altitudes approximatives.'}


# Raster shade, rather than raster-dem: MapLibre's DEM decoder ignores alpha.
# Missing elevations must never be interpreted as sea level or opaque pixels.
_TERRAIN_LOCKS = [threading.Lock() for _ in range(16)]


def terrain_signature():
    return tuple((str(root), (root/'manifest.json').stat().st_mtime_ns,
                  tuple((item['path'], (root/item['path']).stat().st_mtime_ns, item['bytes'])
                        for item in value['files'] if item['path'].endswith('.hgt')))
                 for root, value in datasets())


def terrain_etag(signature, z, x, y):
    return '"'+hashlib.sha256(repr(('shade-v1', signature, z, x, y)).encode()).hexdigest()+'"'


def terrain_shade_png(z, x, y, signature=None):
    if not 8 <= z <= 14 or not 0 <= x < 2**z or not 0 <= y < 2**z:
        raise HTTPException(404, 'Tuile inconnue.')
    signature = terrain_signature() if signature is None else signature
    # Coalesce identical concurrent requests without serializing unrelated tiles.
    with _TERRAIN_LOCKS[hash((z, x, y)) % len(_TERRAIN_LOCKS)]:
        return _terrain_shade_png(z, x, y, signature)


def _png(rows, size=256):
    def chunk(kind, body):
        return struct.pack('>I', len(body))+kind+body+struct.pack('>I', zlib.crc32(kind+body))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
            +chunk(b'IDAT', zlib.compress(b''.join(rows), 3))+chunk(b'IEND', b''))


@lru_cache(maxsize=128)
def _terrain_shade_png(z, x, y, signature):
    size=256
    # One pixel of real neighbouring elevation on each side avoids tile seams.
    longitudes=[(x+(i+.5)/size)/2**z*360-180 for i in range(-1, size+1)]
    latitudes=[math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+(j+.5)/size)/2**z))))
               for j in range(-1, size+1)]
    with Heights() as heights:
        samples=_height_samples(heights,latitudes,longitudes) if heights.grids else []
    rows=[]
    for j in range(size):
        row=bytearray([0])
        resolution=40075016.686*math.cos(math.radians(latitudes[j+1]))/(size*2**z)
        for i in range(size):
            if not samples:
                row.extend((0,0,0,0));continue
            a,b,c,d,center=(samples[j+1][i], samples[j+1][i+2], samples[j][i+1], samples[j+2][i+1], samples[j+1][i+1])
            if None in (a,b,c,d,center):
                row.extend((0,0,0,0));continue
            dx=(b-a)/(2*resolution);dy=(d-c)/(2*resolution)
            # Northwest illumination. Flat terrain is transparent, slopes subtle.
            light=(dx+dy)/(math.sqrt(2)*math.sqrt(1+dx*dx+dy*dy))
            alpha=min(64, round(abs(light)*90))
            row.extend((255,255,255,alpha) if light>0 else (53,57,44,alpha))
        rows.append(row)
    # Empty/missing tiles are valid transparent raster tiles, cached as well.
    return _png(rows)


# Legacy DEM endpoint remains compatible with already-open older map readers.
def terrain_png(z,x,y):
    signature=tuple((str(root), (root/'manifest.json').stat().st_mtime_ns) for root,_ in datasets())
    return _terrain_png(z,x,y,signature)


@lru_cache(maxsize=32)
def _terrain_png(z,x,y,signature):
    if not 0<=z<=14 or not 0<=x<2**z or not 0<=y<2**z:raise HTTPException(404,'Tuile inconnue.')
    size=256;rows=[];present=False
    with Heights() as heights:
        if not heights.grids:raise HTTPException(404,'Relief non téléchargé.')
        longitudes=[(x+(i+.5)/size)/2**z*360-180 for i in range(size)]
        for j in range(size):
            lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+(j+.5)/size)/2**z))))
            row=bytearray([0])
            for lon in longitudes:
                height=heights.sample(lat,min(lon,179.999999));present|=height is not None
                v=round(((height or 0)+32768)*256);row.extend(((v>>16)&255,(v>>8)&255,v&255,255 if height is not None else 0))
            rows.append(row)
    if not present:raise HTTPException(404,'Zone sans altitude préparée.')
    def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
