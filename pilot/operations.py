"""Narrow authenticated bridge to the host controller."""
import json
import os
import time

import httpx
from fastapi import HTTPException

from . import engine,network

URL=os.environ.get('PILOT_CONTROL_URL','http://host.docker.internal:11436').rstrip('/')
TOKEN=os.environ.get('PILOT_CONTROL_TOKEN','')
CACHE={};UPDATED=0


def describe(value):
    if value.get('operation')=='start':return 'Démarrage de l’assistant en cours…'
    if value.get('operation')=='stop':return 'Arrêt de l’assistant et libération de la mémoire…'
    if value.get('online'):return 'Assistant prêt' if not value.get('models') else 'Assistant actif'
    if value.get('paused'):
        if value.get('reason') in ('user_gaming','gaming'):return 'Assistant en pause pour libérer la carte graphique — mode jeu'
        if value.get('reason')=='start_failed':return 'Le démarrage de l’assistant a échoué'
        return 'Assistant arrêté pour libérer la mémoire'
    return 'Le moteur de l’assistant est arrêté ou ne répond pas'


async def status(fresh=False):
    global CACHE,UPDATED
    if CACHE and not fresh and time.monotonic()-UPDATED<2:return CACHE
    problem='';upstream=None;started=time.monotonic()
    try:
        if not TOKEN:problem='not_configured';raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=5) as client:
            response=await client.get(URL+'/status',headers={'Authorization':'Bearer '+TOKEN})
            upstream=response.status_code;response.raise_for_status();value=response.json()
            if not isinstance(value,dict):raise ValueError()
    except (httpx.HTTPError,ValueError) as error:
        problem=problem or ('timeout' if isinstance(error,httpx.TimeoutException) else 'http_error' if isinstance(error,httpx.HTTPStatusError) else 'connection_error' if isinstance(error,httpx.HTTPError) else 'invalid_response')
        value={'online':False,'paused':False,'models':[],'models_available':False,'control_available':False,'gpus':[],'memory':{},'disk':{},
               'control_error':problem,'control_http_status':upstream,'control_elapsed_ms':round((time.monotonic()-started)*1000)}
        marker=network.CATALOG/'inference.json'
        if marker.is_file():
            try:
                saved=json.loads(marker.read_text());value.update(paused=saved.get('state')=='paused',reason=saved.get('reason',''))
            except (ValueError,OSError):pass
        if not value['paused']:
            try:
                async with httpx.AsyncClient(trust_env=False,timeout=1) as client:
                    response=await client.get(engine.OLLAMA+'/api/version');value['online']=response.is_success
            except httpx.HTTPError:pass
    value['message']=describe(value);CACHE=value;UPDATED=time.monotonic()
    return value


async def command(action,force=False):
    global UPDATED
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=8) as client:
            response=await client.post(URL+'/'+action,json={'force':force},headers={'Authorization':'Bearer '+TOKEN})
            if response.status_code==409:raise HTTPException(409,response.json().get('detail','Une commande est déjà en cours.'))
            response.raise_for_status()
        UPDATED=0
        return {'accepted':True}
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'Le service de commande ne répond pas. Utilisez le lanceur sur le PC serveur.')


async def library_command(action=None,body=None):
    if action not in (None,'plan','download','pause','geography','routing','index','index-prepare','index-settings','collection-move','collection-preview','collection-exclude','category-index','video-inventory','video-inventory-pause','youtube-download','youtube-download-pause'):raise HTTPException(400,'Action documentaire inconnue.')
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=8) as client:
            path=URL+'/library'+('/'+action if action else '')
            headers={'Authorization':'Bearer '+TOKEN}
            response=await client.post(path,json=body or {},headers=headers) if action else await client.get(path,headers=headers)
            if response.status_code in (400,409):raise HTTPException(response.status_code,response.json().get('detail','Vérifiez la sélection.'))
            response.raise_for_status();return response.json()
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'Le service de téléchargement ne répond pas. Relancez les services depuis le PC serveur ; la bibliothèque déjà installée reste disponible.')


async def youtube_result(identifier):
    """Fetch the host's retained result even after another library task starts."""
    try:
        if not TOKEN:
            return None
        async with httpx.AsyncClient(trust_env=False, timeout=8) as client:
            response = await client.get(URL+'/library/youtube/'+identifier, headers={'Authorization':'Bearer '+TOKEN})
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError):
        return None


async def activity():
    """Read-only filtered host activity; no profile content or raw diagnostics."""
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=8) as client:
            response=await client.get(URL+'/activity',headers={'Authorization':'Bearer '+TOKEN})
            response.raise_for_status();return response.json()
    except (httpx.HTTPError,ValueError):
        return {'phase':'unknown','source':None,'stale':True,'active':[],'commands':False,
                'control_available':False,'observed_at':time.time()}


async def performance():
    """Read host counters without starting any model or returning credentials."""
    try:
        if not TOKEN:return {'available':False,'reason':'not_configured'}
        async with httpx.AsyncClient(trust_env=False,timeout=6) as client:
            response=await client.get(URL+'/performance',headers={'Authorization':'Bearer '+TOKEN})
            if response.status_code==404:return {'available':False,'reason':'controller_update_required'}
            response.raise_for_status();value=response.json()
            if not isinstance(value,dict) or value.get('schema')!=1:raise ValueError()
            return {**value,'available':True}
    except (httpx.HTTPError,ValueError):return {'available':False,'reason':'controller_unavailable'}


async def update_request(action=None,body=None):
    """Update check and launch on the host; the portal never runs a command itself."""
    if action not in (None,'check','start'):raise HTTPException(400,'Action de mise à jour inconnue.')
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=8) as client:
            headers={'Authorization':'Bearer '+TOKEN}
            path=URL+'/update'+('/'+action if action else '')
            response=await client.post(path,json=body or {},headers=headers) if action else await client.get(path,headers=headers)
            if response.status_code==404:return {'supported':False,'reason':'controller_update_required'}
            if response.status_code==409:raise HTTPException(409,response.json().get('detail','Opération refusée.'))
            response.raise_for_status();value=response.json()
            if not isinstance(value,dict):raise ValueError()
            return value
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'Le service de commande ne répond pas. Utilisez le raccourci de mise à jour sur le PC serveur.')
