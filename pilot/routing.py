"""Bounded local OSRM adapter. Never falls back to an Internet routing service."""
import datetime
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
        if not value.get('complete') or value.get('engine')!='OSRM' or not value.get('build_id'):return None
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


async def calculate(points,mode='foot',speed_kmh=4,avoid_motorways=True):
    if mode not in MODES:raise HTTPException(400,'Mode de déplacement inconnu.')
    if type(speed_kmh) not in (int,float) or not math.isfinite(speed_kmh) or not (0.5<=speed_kmh<=12 if mode=='foot' else 5<=speed_kmh<=130):raise HTTPException(400,'Vitesse moyenne hors limites pour ce déplacement.')
    if not 2<=len(points)<=8:raise HTTPException(400,'Choisissez de 2 à 8 étapes.')
    value=manifest()
    if not value:raise HTTPException(409,'Réseau de routes et chemins non préparé. Les points et trajets enregistrés restent consultables.')
    normalized=[]
    for point in points:
        try:lat,lon=geography.coordinates(point['lat'],point['lon'])
        except (KeyError,ValueError):raise HTTPException(400,'Coordonnées d’étape non valides.')
        west,south,east,north=value['bbox']
        if not west<=lon<=east or not south<=lat<=north:raise HTTPException(422,'Une étape est hors de la zone préparée. Préparez une zone plus large ; aucun trajet à vol d’oiseau ne sera substitué.')
        normalized.append({'lat':lat,'lon':lon,'title':str(point.get('title','Étape'))[:120]})
    coords=';'.join(str(p['lon'])+','+str(p['lat']) for p in normalized)
    params={'overview':'full','geometries':'geojson','steps':'true','alternatives':'false','radiuses':';'.join(['100']*len(points)),'generate_hints':'false'}
    if mode!='foot' and avoid_motorways:params['exclude']='motorway'
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=25,follow_redirects=False) as client:
            async with client.stream('GET',URLS[mode]+'/route/v1/driving/'+coords,params=params) as response:
                raw=bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw)>2_000_000:raise HTTPException(413,'Trajet trop détaillé. Choisissez des étapes plus proches.')
                data=json.loads(raw)
                if data.get('code') in ('NoRoute','NoSegment'):raise HTTPException(422,'Aucun trajet praticable dans ce réseau pour ces étapes et ce mode. Choisissez un point plus proche d’une voie ou préparez une zone plus large.')
                response.raise_for_status()
        if data.get('code')!='Ok' or not data.get('routes'):raise ValueError()
        if data.get('data_version')!=value['build_id']:raise HTTPException(503,'Le moteur utilise une ancienne zone. Relancez les services cartographiques sur le PC serveur.')
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
            if offset>101:raise ValueError()
            snapped.append({**original,'snapped_lat':lat,'snapped_lon':lon,'offset_m':offset})
        segments=[]
        for leg in item.get('legs',[]):
            for step in leg.get('steps',[]):
                distance=step.get('distance',0)
                if type(distance) not in (int,float) or not math.isfinite(distance) or distance<0:raise ValueError()
                if distance>0:segments.append({'name':str(step.get('name') or 'Voie sans nom')[:160],'distance_m':round(distance,1)})
        return {'mode':mode,'mode_label':MODES[mode],'speed_kmh':speed_kmh,'distance_m':round(meters,1),'duration_s':round(meters/speed_kmh*3.6),'engine_duration_s':engine_duration,
                'points':snapped,'geometry':geometry,'segments':segments[:250],'avoid_motorways':bool(avoid_motorways),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'coverage':{k:value.get(k) for k in ('bbox','created','build_id','source')},'attribution':value.get('attribution'),'note':NOTE+' Les écarts entre les points choisis et les voies accrochées ne sont pas inclus dans les kilomètres.'}
    except HTTPException:raise
    except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError):raise HTTPException(503,'Le calcul local est indisponible ou sa réponse n’est pas valide. Aucun trajet n’a été inventé. Les trajets enregistrés restent consultables.')
