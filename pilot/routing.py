"""Bounded local OSRM adapter. Never falls back to an Internet routing service."""
import datetime
import base64
import hashlib
import hmac
import secrets
import time
import json
import math
import os
from pathlib import Path
import httpx
from fastapi import HTTPException
from . import geography, maps

URLS={mode:os.environ.get('ROUTING_'+mode.upper()+'_URL','http://router-'+mode+':5000').rstrip('/') for mode in ('foot','motorcycle','car')}
MODES={'foot':'À pied','motorcycle':'Moto','car':'Petite voiture'}
NOTE='Trajet préparé sur des données datées, sans navigation GPS. Vérifiez accès et état des voies sur place. Durée à vitesse moyenne constante, hors pauses, relief et conditions réelles.'


def manifest():
    root=maps.ROOT/'routing/current';path=root/'manifest.json'
    if not path.is_file() or path.is_symlink() or root.is_symlink() or path.stat().st_size>500_000:return None
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or not value.get('complete') or value.get('engine')!='OSRM' or not isinstance(value.get('build_id'),str) or not value['build_id']:return None
        bbox=value.get('bbox')
        if not isinstance(bbox,list) or len(bbox)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in bbox):return None
        if not (-180<=bbox[0]<bbox[2]<=180 and -90<=bbox[1]<bbox[3]<=90):return None
        if set(value['profiles'])!=set(MODES):return None
        for item in value['files']:
            relative=Path(item['path']);file=root/relative
            if relative.is_absolute() or len(relative.parts)!=2 or relative.parts[0] not in MODES or '..' in relative.parts or file.is_symlink() or not file.is_file() or file.stat().st_size!=item['bytes']:return None
        return value
    except (ValueError,KeyError,TypeError,OSError):return None


def status():
    value=manifest()
    return {'prepared':bool(value),'modes':MODES,'coverage':{k:value.get(k) for k in ('bbox','created','build_id','source','attribution')} if value else None,
            'note':'Données préparées ; le moteur sera vérifié lors du calcul.' if value else 'Préparez les routes et chemins depuis Données locales. Aucun calcul n’est envoyé sur Internet.'}


# Short-lived capabilities bind an access to its original point, profile and graph.
# A restart invalidates proposals; saved route snapshots remain independent.
_ACCESS_KEY=secrets.token_bytes(32)


class RoutingError(HTTPException):
    """Categorical internal error, serialized with a legacy string detail."""


def fail(status, code, message, **extra):
    raise RoutingError(status, {'code':code, 'message':message, **extra})


def access_token(payload):
    raw=base64.urlsafe_b64encode(json.dumps(payload, separators=(',',':')).encode()).decode()
    return raw+'.'+hmac.new(_ACCESS_KEY, raw.encode(), hashlib.sha256).hexdigest()


def read_access(token, original, mode, avoid_motorways, build_id):
    try:
        raw, signature=token.split('.')
        if not hmac.compare_digest(signature, hmac.new(_ACCESS_KEY, raw.encode(), hashlib.sha256).hexdigest()):raise ValueError()
        data=json.loads(base64.urlsafe_b64decode(raw))
        if (data['mode']!=mode or data['avoid']!=bool(avoid_motorways) or data['build']!=build_id
                or not 0<=time.time()-data['time']<=900
                or geography.distance(original['lat'],original['lon'],*data['origin'])>0.1):raise ValueError()
        geography.coordinates(*data['access'])
        if geography.distance(*data['origin'],*data['access'])>1000:raise ValueError()
        return data
    except (ValueError,KeyError,TypeError,OverflowError):
        fail(409,'access_expired','Cet accès a expiré ou le réseau a changé. Choisissez à nouveau un accès.')


async def engine_request(mode, service, coords, params):
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=25,follow_redirects=False) as client:
            async with client.stream('GET',URLS[mode]+'/'+service+'/v1/driving/'+coords,params=params) as response:
                raw=bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw)>2_000_000:
                        fail(413,'route_too_large','Trajet trop détaillé. Choisissez des étapes plus proches.')
                try:data=json.loads(raw)
                except ValueError:fail(503,'invalid_response','Le moteur local a renvoyé une réponse illisible. Réessayez.')
                if not isinstance(data,dict):fail(503,'invalid_response','La réponse du moteur local est invalide.')
                if data.get('code')=='NoSegment':
                    fail(422,'no_access','Un point est trop éloigné des voies connues. Choisissez un accès proche.')
                if data.get('code')=='NoRoute':
                    fail(422,'no_route','Aucune liaison trouvée entre ces accès. Essayez un autre accès ou une zone plus large.')
                response.raise_for_status()
                if data.get('code')!='Ok':fail(503,'invalid_response','Le moteur local ne peut pas traiter ce calcul. Réessayez.')
                return data
    except httpx.TimeoutException:
        fail(504,'engine_timeout','Le calcul local prend trop de temps. Réessayez avec des étapes plus proches.')
    except httpx.HTTPError:
        fail(503,'engine_unavailable','Le moteur de calcul local ne répond pas. Réessayez ou vérifiez les services cartographiques dans Mon appareil.')


def check_build(data, value):
    if data.get('data_version')!=value['build_id']:
        fail(503,'stale_graph','Le moteur utilise une ancienne zone. Relancez les services cartographiques sur le PC serveur.')


async def accesses(lat, lon, mode='foot', avoid_motorways=True, near=None):
    if mode not in MODES:fail(400,'invalid_mode','Mode de déplacement inconnu.')
    lat,lon=geography.coordinates(lat,lon)
    value=manifest()
    if not value:fail(409,'not_prepared','Préparez le réseau de routes et chemins de cette zone.')
    west,south,east,north=value['bbox']
    if not west<=lon<=east or not south<=lat<=north:
        fail(422,'outside_coverage','Ce point est hors du réseau préparé. Préparez une zone plus large.')
    target=(lat,lon) if near is None else geography.coordinates(*near)
    if geography.distance(lat,lon,*target)>1000:
        fail(422,'access_too_far','Choisissez un accès à moins de 1 km du point d’origine.')
    params={'number':12,'radiuses':'1000' if near is None else '100','generate_hints':'true'}
    if mode!='foot' and avoid_motorways:params['exclude']='motorway'
    try:data=await engine_request(mode,'nearest',str(target[1])+','+str(target[0]),params)
    except HTTPException as exc:
        if isinstance(exc.detail,dict) and exc.detail['code']=='no_access':
            return {'candidates':[], 'build_id':value['build_id']}
        raise
    check_build(data,value)
    candidates=[];seen=set()
    try:
        for item in data['waypoints']:
            lon2,lat2=item['location'];geography.coordinates(lat2,lon2)
            offset=geography.distance(lat,lon,lat2,lon2)
            if offset>1000:continue
            nodes=tuple(sorted(n for n in item.get('nodes',[]) if n))
            key=nodes or (round(lat2,5),round(lon2,5))
            if key in seen or any(geography.distance(lat2,lon2,c['lat'],c['lon'])<20 for c in candidates):continue
            seen.add(key)
            payload={'origin':[lat,lon],'access':[lat2,lon2],'mode':mode,'avoid':bool(avoid_motorways),
                     'build':value['build_id'],'time':time.time(),'hint':str(item.get('hint',''))[:2048]}
            candidates.append({'lat':lat2,'lon':lon2,'label':str(item.get('name') or 'Voie sans nom')[:160],
                               'distance_m':round(offset,1),'token':access_token(payload)})
            if len(candidates)==3:break
    except (ValueError,KeyError,TypeError,IndexError):
        fail(503,'invalid_response','Les accès renvoyés par le moteur local ne sont pas valides.')
    return {'candidates':candidates,'build_id':value['build_id']}


async def calculate(points,mode='foot',speed_kmh=4,avoid_motorways=True):
    if mode not in MODES:raise HTTPException(400,'Mode de déplacement inconnu.')
    if type(speed_kmh) not in (int,float) or not math.isfinite(speed_kmh) or not (0.5<=speed_kmh<=12 if mode=='foot' else 5<=speed_kmh<=130):raise HTTPException(400,'Vitesse moyenne hors limites pour ce déplacement.')
    if not 2<=len(points)<=8:raise HTTPException(400,'Choisissez de 2 à 8 étapes.')
    value=manifest()
    if not value:fail(409,'not_prepared','Réseau de routes et chemins non préparé. Les trajets enregistrés restent consultables.')
    normalized=[]
    for point in points:
        try:lat,lon=geography.coordinates(point['lat'],point['lon'])
        except (KeyError,ValueError):raise HTTPException(400,'Coordonnées d’étape non valides.')
        west,south,east,north=value['bbox']
        if not west<=lon<=east or not south<=lat<=north:fail(422,'outside_coverage','Une étape est hors de la zone préparée. Préparez une zone plus large.')
        original={'lat':lat,'lon':lon,'title':str(point.get('title','Étape'))[:120]}
        access=read_access(point['access_token'],original,mode,avoid_motorways,value['build_id']) if point.get('access_token') else None
        normalized.append({**original,'access':access})
    targets=[p['access']['access'] if p['access'] else [p['lat'],p['lon']] for p in normalized]
    coords=';'.join(str(lon)+','+str(lat) for lat,lon in targets)
    params={'overview':'full','geometries':'geojson','steps':'true','alternatives':'false','radiuses':';'.join(['100']*len(points)),'generate_hints':'false'}
    if mode!='foot' and avoid_motorways:params['exclude']='motorway'
    if any(p['access'] for p in normalized):
        params['hints']=';'.join(p['access']['hint'] if p['access'] else '' for p in normalized)
        params['radiuses']=';'.join('5' if p['access'] else '100' for p in normalized)
    try:
        data=await engine_request(mode,'route',coords,params)
        check_build(data,value)
        item=data['routes'][0];meters=item['distance'];engine_duration=item['duration'];geometry=item['geometry']
        if type(meters) not in (int,float) or not math.isfinite(meters) or meters<0 or meters>5_000_000:raise ValueError()
        if type(engine_duration) not in (int,float) or not math.isfinite(engine_duration) or engine_duration<0:raise ValueError()
        if geometry.get('type')!='LineString' or not 2<=len(geometry['coordinates'])<=50000:raise ValueError()
        for position in geometry['coordinates']:
            if len(position)!=2:raise ValueError()
            geography.coordinates(position[1],position[0])
        waypoints=data['waypoints']
        if len(waypoints)!=len(points):raise ValueError()
        snapped=[]
        for original,waypoint in zip(normalized,waypoints):
            lon,lat=waypoint['location'];geography.coordinates(lat,lon)
            offset=geography.distance(original['lat'],original['lon'],lat,lon)
            target=original['access']['access'] if original['access'] else [original['lat'],original['lon']]
            if geography.distance(*target,lat,lon)>(6 if original['access'] else 101):raise ValueError()
            snapped.append({k:v for k,v in {**original,'snapped_lat':lat,'snapped_lon':lon,'offset_m':round(offset,1),'access_selected':bool(original['access'])}.items() if k!='access'})
        segments=[]
        for leg in item.get('legs',[]):
            for step in leg.get('steps',[]):
                distance=step.get('distance',0)
                if type(distance) not in (int,float) or not math.isfinite(distance) or distance<0:raise ValueError()
                if distance>0:segments.append({'name':str(step.get('name') or 'Voie sans nom')[:160],'distance_m':round(distance,1)})
        return {'mode':mode,'mode_label':MODES[mode],'speed_kmh':speed_kmh,'distance_m':round(meters,1),'duration_s':round(meters/speed_kmh*3.6),'engine_duration_s':engine_duration,
                'points':snapped,'connectors':[{'point_index':i,'distance_m':p['offset_m'],'verified':False,'geometry':{'type':'LineString','coordinates':[[p['lon'],p['lat']],[p['snapped_lon'],p['snapped_lat']]]}} for i,p in enumerate(snapped) if p['offset_m']>5],'geometry':geometry,'segments':segments[:250],'avoid_motorways':bool(avoid_motorways),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'coverage':{k:value.get(k) for k in ('bbox','created','build_id','source')},'attribution':value.get('attribution'),'note':NOTE+' Les écarts entre les points choisis et les voies accrochées ne sont pas inclus dans les kilomètres.'}
    except HTTPException:raise
    except (ValueError,KeyError,TypeError,IndexError,AttributeError):fail(503,'invalid_response','La réponse du moteur local n’est pas valide. Réessayez ; les trajets enregistrés restent consultables.')
