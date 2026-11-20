"""Dépendances communes des routes : profil courant, droits d’administration, fonctions optionnelles."""
import asyncio
from contextlib import contextmanager
import importlib
import logging
from typing import Annotated
from fastapi import Depends,HTTPException,Request
from pydantic import BaseModel,Field
from .. import model_downloads
from .. import engine,profiles


TERRAIN_LOCK=asyncio.Semaphore(2)


COOKIE='survie_session'


MODEL_DOWNLOADS=model_downloads.ModelDownloads(engine.OLLAMA,engine.PROFILE_CONFIG)


DEGRADED={}


@contextmanager
def optional_feature(name):
    try:
        module=importlib.import_module('.'+name,__package__.rpartition('.')[0])
        yield module
        DEGRADED.pop(name,None)
    except HTTPException:raise
    except Exception:
        DEGRADED[name]=True
        logging.getLogger('pilot.app').warning('Fonction optionnelle indisponible : %s',name)
        raise HTTPException(503,'Cette fonction est momentanément indisponible. Les autres documents et conversations restent accessibles.')


async def user(request:Request):
    value=await asyncio.to_thread(profiles.current,request.cookies.get(profiles.COOKIE))
    expected=request.headers.get('X-Survie-Profile')
    if expected and expected!=value['id']:raise HTTPException(409,'Le profil a changé dans un autre onglet. Rechargez la page.',headers={'X-Survie-Profile-Changed':'true'})
    return value


async def admin(value=Depends(user)):
    if value['role']!='admin':raise HTTPException(403,'Accès réservé à l’administrateur.')
    return value


def public_user(value):return profiles.public(value)


def profile_cookie(response,request,identifier):
    # Public identity label, not a credential: keep the choice usable on HTTP too.
    # A Secure choice set by HTTPS would prevent selecting a profile on HTTP later.
    response.set_cookie(profiles.COOKIE,identifier,max_age=10*365*86400,httponly=True,samesite='lax',path='/')
    # Old credentials are no longer used to identify a profile.
    response.delete_cookie(COOKIE,path='/')


SourceIdentifier=Annotated[str,Field(min_length=1,max_length=2000,pattern=r'^(guide|zim|video):.+$')]


class WorkPause(BaseModel):
    paused:bool


class CaptionResume(BaseModel):
    mode:str|None=Field(default=None,max_length=50)
