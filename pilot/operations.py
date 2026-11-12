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
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=5) as client:
            response=await client.get(URL+'/status',headers={'Authorization':'Bearer '+TOKEN})
            response.raise_for_status();value=response.json()
    except (httpx.HTTPError,ValueError):
        value={'online':False,'paused':False,'models':[],'control_available':False,'gpus':[],'memory':{},'disk':{}}
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
    if action not in (None,'plan','download','pause','geography','routing'):raise HTTPException(400,'Action documentaire inconnue.')
    try:
        if not TOKEN:raise ValueError()
        async with httpx.AsyncClient(trust_env=False,timeout=8) as client:
            path=URL+'/library'+('/'+action if action else '')
            headers={'Authorization':'Bearer '+TOKEN}
            response=await client.post(path,json=body or {},headers=headers) if action else await client.get(path,headers=headers)
            if response.status_code in (400,409):raise HTTPException(response.status_code,response.json().get('detail','Vérifiez la sélection.'))
            response.raise_for_status();return response.json()
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'Le service de téléchargement ne répond pas. Relancez les services depuis le PC serveur ; la bibliothèque déjà installée reste disponible.')
