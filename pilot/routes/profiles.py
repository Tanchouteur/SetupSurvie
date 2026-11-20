"""Routes du pilote — profils locaux, favoris, utilisateurs et retours."""
import asyncio
import time
from fastapi import APIRouter,Depends,HTTPException,Request,Response,Query
from pydantic import BaseModel,Field
from .. import store,profiles
from .deps import admin,optional_feature,profile_cookie,public_user,user

router=APIRouter()


class ProfileSelection(BaseModel):
    id:str=Field(min_length=1,max_length=200)


class ProfileCreation(BaseModel):
    name:str=Field(min_length=1,max_length=100)


@router.get('/api/profiles')
async def profile_list():return {'profiles':await asyncio.to_thread(profiles.listing)}


@router.get('/api/auth/me')
@router.get('/api/profiles/current')
async def me(value=Depends(user)):return public_user(value)


@router.post('/api/profiles/select')
async def select_profile(body:ProfileSelection,request:Request,response:Response):
    value=await asyncio.to_thread(profiles.selected,body.id)
    profile_cookie(response,request,value['id'])
    return public_user(value)


@router.post('/api/profiles',status_code=201)
async def create_profile(body:ProfileCreation,request:Request,response:Response):
    value=await asyncio.to_thread(profiles.create,body.name)
    profile_cookie(response,request,value['id'])
    return public_user(value)


@router.get('/api/profiles/webui-headers')
async def webui_profile(value=Depends(user)):
    return Response(status_code=200,headers=profiles.webui_headers(value))


@router.post('/api/auth/{action}')
async def retired_login(action:str):
    raise HTTPException(410,'Les mots de passe et codes de secours ont été remplacés par les profils. Rechargez la page puis choisissez votre profil.')


class FavoriteRequest(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)


@router.get('/api/favorites')
async def favorite_list(language:str='',value=Depends(user)):
    with optional_feature('favorites') as module:return {'results':module.listing(value['id'],language)}


@router.put('/api/favorites')
async def favorite_add(body:FavoriteRequest,value=Depends(user)):
    with optional_feature('favorites') as module:
        await module.add(value['id'],body.source_id)
        return {'ok':True,'source_id':module.canonical(body.source_id)}


@router.delete('/api/favorites')
async def favorite_remove(source_id:str=Query(min_length=1,max_length=2000),value=Depends(user)):
    with optional_feature('favorites') as module:module.remove(value['id'],source_id)
    return {'ok':True}


@router.get('/api/admin/users')
async def users(value=Depends(admin)):return {'users':await asyncio.to_thread(profiles.listing)}


@router.post('/api/admin/users')
async def add_user(body:ProfileCreation,value=Depends(admin)):
    return public_user(await asyncio.to_thread(profiles.create,body.name))


class Feedback(BaseModel):
    content:str=Field(min_length=3,max_length=4000)
    view:str=Field(default='',max_length=200)


@router.post('/api/feedback')
async def feedback(body:Feedback,request:Request,value=Depends(user)):
    if not store.limit('feedback:'+value['id'],maximum=10,period=3600):raise HTTPException(429,'Merci, vos retours sont déjà enregistrés. Réessayez plus tard.')
    with store.connect() as db:db.execute('INSERT INTO feedback VALUES(?,?,?,?,?)',(store.new_id(),value['id'],body.content,body.view,time.time()))
    return {'ok':True}


@router.get('/api/admin/feedback')
async def feedback_list(value=Depends(admin)):
    with store.connect() as db:return {'feedback':[dict(r) for r in db.execute('SELECT * FROM feedback ORDER BY created DESC LIMIT 500')]}
