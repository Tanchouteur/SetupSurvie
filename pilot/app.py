"""Authenticated local gateway for the first household pilot."""
import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Literal
from urllib.parse import quote,urlparse

from fastapi import FastAPI,Depends,HTTPException,Request,Response,UploadFile,File,Form,Query
from pydantic import BaseModel,Field
from starlette.responses import FileResponse

from . import accounts,engine,inventory,library,maps,network,operations,store,geography,map_notebook,routing

TERRAIN_LOCK=asyncio.Semaphore(2)
COOKIE='survie_session'
SESSION_SECONDS=30*86400


@asynccontextmanager
async def lifespan(app):
    store.init()
    map_notebook.init()
    await asyncio.to_thread(library.index_guides)
    yield
    for task in list(engine.ACTIVE.values()):task.cancel()
    if engine.ACTIVE:await asyncio.gather(*list(engine.ACTIVE.values()),return_exceptions=True)


VERSION='0.1.12'
app=FastAPI(title='SetupSurvie',version=VERSION,lifespan=lifespan,docs_url=None,redoc_url=None)


@app.middleware('http')
async def origin_check(request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        expected=request.headers.get('host','')
        if origin and urlparse(origin).netloc!=expected:
            return Response('Origine non autorisée',status_code=403)
        if request.cookies.get(COOKIE) and not origin and not request.headers.get('authorization'):
            return Response('Origine requise',status_code=403)
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


def token(request):
    authorization=request.headers.get('authorization','')
    return authorization[7:] if authorization.startswith('Bearer ') else request.cookies.get(COOKIE)


async def user(request:Request):
    credential=token(request)
    if not credential:raise HTTPException(401,'Connectez-vous pour utiliser l’assistant.')
    with store.connect() as db:
        db.execute('DELETE FROM revoked WHERE expires<?',(time.time(),))
        if db.execute('SELECT 1 FROM revoked WHERE digest=?',(hashlib.sha256(credential.encode()).hexdigest(),)).fetchone():
            raise HTTPException(401,'Cette session a été fermée.')
    value=await accounts.native('/api/v1/auths/',token=credential)
    if value.get('role') not in ('admin','user'):raise HTTPException(403,'Ce compte attend l’accord d’un administrateur.')
    return value


async def admin(value=Depends(user)):
    if value['role']!='admin':raise HTTPException(403,'Accès réservé à l’administrateur.')
    return value


def public_user(value):
    with store.connect() as db:ready=db.execute('SELECT 1 FROM recovery WHERE user_id=? AND used=0',(value['id'],)).fetchone() is not None
    return {**{k:value.get(k) for k in ('id','name','email','role')},'recovery_ready':ready}


def cookie(response,request,credential):
    response.set_cookie(COOKIE,credential,max_age=SESSION_SECONDS,httponly=True,samesite='lax',
                        secure=request.headers.get('x-forwarded-proto',request.url.scheme)=='https',path='/')


class Login(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=1,max_length=200)


@app.get('/api/health')
async def health():return {'ok':True,'version':VERSION}


class LibrarySelection(BaseModel):
    themes:list[str]=Field(min_length=1,max_length=14)
    languages:list[str]=Field(default_factory=lambda:['fr','en'],min_length=1,max_length=2)
    max_add_gb:int=Field(default=10,ge=1,le=500)


class LibraryDownload(BaseModel):
    id:str=Field(pattern='^[a-f0-9]{32}$')


@app.get('/api/admin/library')
async def library_status(value=Depends(admin)):
    return await operations.library_command()


@app.post('/api/admin/library/plan',status_code=202)
async def library_plan(body:LibrarySelection,value=Depends(admin)):
    return await operations.library_command('plan',body.model_dump())


@app.post('/api/admin/library/download',status_code=202)
async def library_download(body:LibraryDownload,value=Depends(admin)):
    return await operations.library_command('download',body.model_dump())


@app.post('/api/admin/library/pause',status_code=202)
async def library_pause(value=Depends(admin)):
    return await operations.library_command('pause')


class LocationChoice(BaseModel):
    candidate: str | None = Field(default=None, pattern='^[a-f0-9]{32}$')
    lat: float | None = Field(default=None, ge=-85, le=85, allow_inf_nan=False)
    lon: float | None = Field(default=None, ge=-180, lt=180, allow_inf_nan=False)
    label: str = Field(default='Point choisi sur la carte', min_length=1, max_length=200)


class GeographyDownload(BaseModel):
    lat: float = Field(ge=-80, le=80, allow_inf_nan=False)
    lon: float = Field(ge=-180, lt=180, allow_inf_nan=False)
    radius_km: int = Field(default=10, ge=1, le=25, strict=True)
    terrain: bool = True


@app.get('/api/settings')
async def get_settings(value=Depends(user)):
    return geography.settings()


@app.post('/api/admin/settings/{target}')
async def set_settings(target: str, body: LocationChoice, value=Depends(admin)):
    try:return geography.set_location(target, **body.model_dump())
    except ValueError as exc:raise HTTPException(400, str(exc))


@app.delete('/api/admin/settings/{target}')
async def clear_settings(target: str, value=Depends(admin)):
    if target not in ('home','departure'):raise HTTPException(400,'Emplacement inconnu.')
    geography.save(target,None)
    return {'ok':True}


@app.get('/api/geography/addresses')
async def find_addresses(q: str = Query(min_length=3,max_length=200), online: bool = False, value=Depends(user)):
    if online and value['role']!='admin':raise HTTPException(403,'Recherche en ligne réservée à l’administrateur.')
    return await geography.addresses(q, online)


@app.get('/api/geography/status')
async def geography_status(value=Depends(user)):
    return await asyncio.to_thread(geography.status)


@app.post('/api/admin/library/geography',status_code=202)
async def download_geography(body: GeographyDownload,value=Depends(admin)):
    return await operations.library_command('geography',body.model_dump())


@app.post('/api/admin/library/routing',status_code=202)
async def download_routes(body: GeographyDownload,value=Depends(admin)):
    return await operations.library_command('routing',body.model_dump())


@app.get('/api/geography/nearby')
async def nearby_places(category: str, radius_km: float = Query(default=5,gt=0,le=25),
                        lat: float = Query(ge=-85,le=85,allow_inf_nan=False), lon: float = Query(ge=-180,lt=180,allow_inf_nan=False), value=Depends(user)):
    try:return await asyncio.to_thread(geography.nearby,category,radius_km,lat,lon)
    except ValueError as exc:raise HTTPException(400,str(exc))


@app.get('/api/geography/elevation')
async def point_elevation(lat: float = Query(ge=-85,le=85,allow_inf_nan=False), lon: float = Query(ge=-180,lt=180,allow_inf_nan=False),value=Depends(user)):
    return await asyncio.to_thread(geography.elevation,lat,lon)


@app.get('/api/geography/profile')
async def terrain_profile(lat1:float,lon1:float,lat2:float,lon2:float,value=Depends(user)):
    try:return await asyncio.to_thread(geography.profile,lat1,lon1,lat2,lon2)
    except ValueError as exc:raise HTTPException(400,str(exc))


@app.get('/api/geography/terrain/{z}/{x}/{y}.png')
async def terrain_tile(z:int,x:int,y:int,value=Depends(user)):
    async with TERRAIN_LOCK:
        raw=await asyncio.to_thread(geography.terrain_png,z,x,y)
    return Response(raw,media_type='image/png')


class MapList(BaseModel):
    title: str = Field(min_length=1,max_length=100)


class MapPoint(BaseModel):
    list_id: str = Field(pattern='^[a-f0-9]{32}$')
    title: str = Field(min_length=1,max_length=120)
    lat: float = Field(ge=-85,le=85,allow_inf_nan=False)
    lon: float = Field(ge=-180,lt=180,allow_inf_nan=False)
    kind: Literal['water','food','health','shelter','repair','communication','meeting','other'] = 'other'
    notes: str = Field(default='',max_length=2000)


class RoutePoint(BaseModel):
    lat: float = Field(ge=-85,le=85,allow_inf_nan=False)
    lon: float = Field(ge=-180,lt=180,allow_inf_nan=False)
    title: str = Field(default='Étape',max_length=120)


class RouteRequest(BaseModel):
    points: list[RoutePoint] = Field(min_length=2,max_length=8)
    mode: Literal['foot','motorcycle','car'] = 'foot'
    speed_kmh: float = Field(default=4,ge=0.5,le=130,allow_inf_nan=False)
    avoid_motorways: bool = True


class SavedRoute(BaseModel):
    draft_id: str = Field(pattern='^[a-f0-9]{32}$')
    list_id: str = Field(pattern='^[a-f0-9]{32}$')
    title: str = Field(min_length=1,max_length=120)


@app.get('/api/map-notebook')
async def map_notebook_status(value=Depends(user)):
    return await asyncio.to_thread(map_notebook.overview)


@app.post('/api/admin/map-notebook/lists')
async def create_map_list(body:MapList,value=Depends(admin)):
    return map_notebook.save_list(body.title)


@app.post('/api/admin/map-notebook/lists/{identifier}')
async def update_map_list(identifier:str,body:MapList,value=Depends(admin)):
    return map_notebook.save_list(body.title,identifier)


@app.delete('/api/admin/map-notebook/lists/{identifier}')
async def delete_map_list(identifier:str,value=Depends(admin)):
    map_notebook.delete_list(identifier);return {'ok':True}


@app.post('/api/admin/map-notebook/points')
async def create_map_point(body:MapPoint,value=Depends(admin)):
    return map_notebook.save_point(body.model_dump())


@app.post('/api/admin/map-notebook/points/{identifier}')
async def update_map_point(identifier:str,body:MapPoint,value=Depends(admin)):
    return map_notebook.save_point(body.model_dump(),identifier)


@app.delete('/api/admin/map-notebook/points/{identifier}')
async def delete_map_point(identifier:str,value=Depends(admin)):
    map_notebook.delete_point(identifier);return {'ok':True}


@app.get('/api/routing')
async def routing_status(value=Depends(user)):
    return await asyncio.to_thread(routing.status)


@app.post('/api/admin/map-notebook/calculate')
async def calculate_route(body:RouteRequest,value=Depends(admin)):
    if not store.limit('routing:'+value['id'],maximum=12,period=60):raise HTTPException(429,'Attendez un instant avant de recalculer.')
    data=await routing.calculate([p.model_dump() for p in body.points],body.mode,body.speed_kmh,body.avoid_motorways)
    return map_notebook.draft(value['id'],data)


@app.post('/api/admin/map-notebook/routes')
async def save_map_route(body:SavedRoute,value=Depends(admin)):
    if not body.title.strip():raise HTTPException(400,'Donnez un nom au trajet.')
    return map_notebook.save_route(value['id'],body.draft_id,body.list_id,body.title)


@app.get('/api/map-notebook/routes/{identifier}')
async def saved_map_route(identifier:str,value=Depends(user)):
    return await asyncio.to_thread(map_notebook.route,identifier)


@app.delete('/api/admin/map-notebook/routes/{identifier}')
async def delete_map_route(identifier:str,value=Depends(admin)):
    map_notebook.delete_route(identifier);return {'ok':True}


@app.get('/api/map-notebook/lists/{identifier}/gpx')
async def map_list_gpx(identifier:str,value=Depends(user)):
    return Response(map_notebook.gpx(list_id=identifier),media_type='application/gpx+xml',headers={'Content-Disposition':'attachment; filename="points-setupsurvie.gpx"'})


@app.get('/api/map-notebook/routes/{identifier}/gpx')
async def map_route_gpx(identifier:str,value=Depends(user)):
    return Response(map_notebook.gpx(route_id=identifier),media_type='application/gpx+xml',headers={'Content-Disposition':'attachment; filename="trajet-setupsurvie.gpx"'})


@app.get('/api/assistant-context')
async def assistant_context():
    return {'system':engine.POLICY.read_text()+'\n'+engine.SYSTEM_APPENDIX,'profiles':list(engine.MODES.values()),
            'context_tokens':engine.PROFILE_CONFIG['context'],'output_tokens':engine.PROFILE_CONFIG['output_tokens'],
            'history_max_characters':7000,'source_excerpt_characters':3500,'tools':engine.TOOLS,
            'note':'Les messages de la conversation et les résultats d’outils s’ajoutent à cette consigne. Open WebUI ajoute son propre contexte natif.'}


@app.get('/api/status')
async def status():
    with store.connect() as db:guides=db.execute('SELECT count(*) FROM documents').fetchone()[0]
    return {'version':VERSION,'books':await library.books(),'guides':guides,
            'modes':[{'id':key,**value} for key,value in engine.MODES.items()]}


@app.get('/api/inventory')
async def local_inventory():return await inventory.inventory()


@app.get('/api/network')
async def network_status(request:Request):return network.status(request.url.hostname)


@app.get('/api/network/qr.svg')
async def network_qr(request:Request,kind:str='direct'):
    return Response(network.qr(network.status(request.url.hostname),kind),media_type='image/svg+xml',
                    headers={'Content-Security-Policy':"default-src 'none'; sandbox"})


@app.get('/api/inference')
async def inference_status():
    state=await operations.status()
    with store.connect() as db:
        counts={row['status']:row['n'] for row in db.execute("SELECT status,count(*) AS n FROM jobs WHERE status IN ('queued','running') GROUP BY status")}
    return {**state,'jobs':counts}


class StartEngine(BaseModel):force:bool=False


@app.post('/api/admin/inference/start')
async def start_engine(body:StartEngine,value=Depends(admin)):return await operations.command('start',body.force)


@app.post('/api/admin/inference/stop')
async def stop_engine(value=Depends(admin)):return await operations.command('stop')


@app.post('/api/auth/login')
async def login(body:Login,request:Request,response:Response):
    key='login:'+hashlib.sha256(((request.client.host if request.client else '')+body.email.lower()).encode()).hexdigest()
    if not store.limit(key,maximum=20):raise HTTPException(429,'Trop de tentatives. Réessayez dans quinze minutes.')
    credentials=body.model_dump()
    credentials['email']=credentials['email'].strip().lower()
    if '@' not in credentials['email']:credentials['email']+='@survie.local'
    value=await accounts.native('/api/v1/auths/signin',credentials)
    if 'token' not in value:raise HTTPException(409,'Une protection supplémentaire est activée. Utilisez l’administration avancée.')
    cookie(response,request,value['token'])
    return public_user(value)


@app.get('/api/auth/me')
async def me(value=Depends(user)):return public_user(value)


@app.post('/api/auth/logout')
async def logout(request:Request,response:Response,value=Depends(user)):
    # Native signout revokes where supported; remove this browser's cookie in every case.
    try:await accounts.native('/api/v1/auths/signout',{},token(request))
    except HTTPException:pass
    with store.connect() as db:db.execute('INSERT OR REPLACE INTO revoked VALUES(?,?)',(hashlib.sha256(token(request).encode()).hexdigest(),time.time()+SESSION_SECONDS))
    response.delete_cookie(COOKIE,path='/')
    return {'ok':True}


@app.post('/api/auth/recovery-code')
async def recovery_code(value=Depends(user)):
    return {'code':await asyncio.to_thread(store.recovery_code,value['id'])}


class Reset(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    code:str=Field(min_length=10,max_length=160)
    new_password:str=Field(min_length=8,max_length=72)


@app.post('/api/auth/recover')
async def recover(body:Reset,request:Request,response:Response):
    if len(body.new_password.encode())>72:raise HTTPException(400,'Le mot de passe doit tenir dans 72 octets UTF-8. Essayez moins de caractères.')
    email=body.email.strip().lower()
    if '@' not in email:email+='@survie.local'
    # Both account and IP limits apply; a new source IP cannot bypass the account limit.
    for key in ('reset-email:'+email,'reset-ip:'+(request.client.host if request.client else 'local')):
        if not store.limit(key):raise HTTPException(429,'Trop de tentatives. Réessayez dans quinze minutes.')
    account=await asyncio.to_thread(accounts.native_account,email)
    if not account or not await asyncio.to_thread(store.consume_code,account['id'],body.code):
        raise HTTPException(400,'Code ou identifiant non valide.')
    await accounts.reset_password(email,body.new_password)
    with store.connect() as db:jobs=db.execute("SELECT id FROM jobs WHERE user_id=? AND status IN ('queued','running')",(account['id'],)).fetchall()
    for job in jobs:engine.cancel(job['id'])
    new_code=await asyncio.to_thread(store.recovery_code,account['id'])
    value=await accounts.native('/api/v1/auths/signin',{'email':email,'password':body.new_password})
    cookie(response,request,value['token'])
    return {'user':public_user(value),'code':new_code}


@app.get('/api/search')
async def search(q:str=Query(default='',max_length=200),language:str='',limit:int=Query(default=8,ge=1,le=20)):
    return {'results':await library.search(q.strip(),language,limit=limit) if q.strip() else []}


@app.get('/api/source')
async def source(id:str):return await library.source(id)


@app.get('/api/maps')
async def offline_maps():return {'maps':await asyncio.to_thread(maps.available)}


@app.get('/api/library/coverage')
async def library_coverage():return await asyncio.to_thread(library.index_report)


@app.get('/api/maps/{identifier}/archive')
async def map_archive(identifier:str):
    path=await asyncio.to_thread(maps.archive,identifier)
    return FileResponse(path,media_type='application/octet-stream',headers={'Cache-Control':'public, max-age=3600'})


@app.get('/api/media')
async def media(id:str):
    path=library.safe_zim_path(id)
    if path.split('/')[0] not in {b['book'] for b in await library.books()}:raise HTTPException(404,'Collection inconnue.')
    data,kind=await library.get('/content/'+quote(path,safe='/'),maximum=8_000_000)
    if not kind.startswith('image/'):raise HTTPException(400,'Ce contenu n’est pas une illustration.')
    return Response(data,media_type=kind,headers={'Content-Security-Policy':"sandbox; default-src 'none'"})


@app.get('/api/conversations')
async def conversations(value=Depends(user)):
    with store.connect() as db:rows=db.execute('SELECT * FROM conversations WHERE user_id=? ORDER BY created DESC LIMIT 100',(value['id'],)).fetchall()
    return {'conversations':[dict(row) for row in rows]}


@app.get('/api/conversations/{identifier}')
async def conversation(identifier:str,value=Depends(user)):
    item=store.owned_conversation(identifier,value['id'])
    if not item:raise HTTPException(404,'Conversation introuvable.')
    with store.connect() as db:jobs=[dict(r) for r in db.execute("SELECT id,status,mode FROM jobs WHERE conversation_id=? AND status IN ('queued','running')",(identifier,))]
    return {**item,'messages':store.messages(identifier),'jobs':jobs}


@app.delete('/api/conversations/{identifier}')
async def delete_conversation(identifier:str,value=Depends(user)):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():
            raise HTTPException(404,'Conversation introuvable.')
        jobs=db.execute('SELECT id,status FROM jobs WHERE conversation_id=?',(identifier,)).fetchall()
        if any(job['status'] in ('queued','running') for job in jobs):
            raise HTTPException(409,'Une réponse est en cours. Attendez sa fin ou annulez-la avant de supprimer cette conversation.')
        db.execute('DELETE FROM jobs WHERE conversation_id=?',(identifier,))
        db.execute('DELETE FROM conversations WHERE id=? AND user_id=?',(identifier,value['id']))
    for job in jobs:
        (store.ROOT/'traces'/(job['id']+'.json')).unlink(missing_ok=True)
    return {'ok':True}


class Question(BaseModel):
    message:str=Field(min_length=1,max_length=6000)
    mode:str='rapide'
    conversation_id:str|None=Field(default=None,max_length=100)
    source_id:str|None=Field(default=None,max_length=2000)


@app.post('/api/questions')
async def question(body:Question,value=Depends(user)):
    if body.mode not in engine.MODES:raise HTTPException(400,'Mode inconnu.')
    state=await operations.status()
    if not state.get('online') or state.get('operation'):
        raise HTTPException(503,state['message']+'. La bibliothèque reste disponible. Consultez « État de l’appareil » pour le redémarrage.')
    conversation_id=body.conversation_id
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if conversation_id and not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation_id,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=20:
            raise HTTPException(429,'La file d’attente est pleine. Réessayez après les demandes en cours.')
        if db.execute("SELECT count(*) FROM jobs WHERE user_id=? AND status IN ('queued','running')",(value['id'],)).fetchone()[0]>=2:
            raise HTTPException(429,'Vous avez déjà des questions en cours. Attendez ou annulez-en une.')
        if not conversation_id:
            conversation_id=store.new_id();db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation_id,value['id'],body.message[:80],time.time()))
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation_id,'user',body.message,time.time()))
        identifier=store.new_id();now=time.time()
        db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(identifier,value['id'],conversation_id,body.mode,'queued',now,now))
    engine.launch(identifier,value['id'],conversation_id,body.mode,body.source_id)
    return {'id':identifier,'conversation_id':conversation_id}


@app.get('/api/jobs/{identifier}')
async def job(identifier:str,value=Depends(user)):
    with store.connect() as db:row=db.execute('SELECT * FROM jobs WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone()
    if not row:raise HTTPException(404,'Demande introuvable.')
    return {**dict(row),'sources':json.loads(row['sources'])}


@app.post('/api/jobs/{identifier}/cancel')
async def cancel(identifier:str,value=Depends(user)):
    await job(identifier,value);engine.cancel(identifier)
    return {'ok':True}


@app.post('/api/transcribe')
async def transcribe(request:Request,file:UploadFile=File(...),value=Depends(user)):
    content=await file.read(20_000_001)
    if len(content)>20_000_000:raise HTTPException(413,'Enregistrement trop long. Essayez une dictée plus courte.')
    async with accounts.httpx.AsyncClient(trust_env=False,timeout=180) as client:
        result=await client.post(accounts.WEBUI+'/api/v1/audio/transcriptions',headers={'Authorization':'Bearer '+token(request)},
            files={'file':(Path(file.filename or 'dictee.webm').name,content,file.content_type or 'audio/webm')},data={'language':'fr'})
    if result.status_code!=200:raise HTTPException(503,'La dictée est indisponible. Vous pouvez écrire votre question.')
    return {'text':result.json().get('text','')}


@app.get('/api/admin/users')
async def users(value=Depends(admin)):
    import sqlite3
    db=sqlite3.connect('file:'+accounts.DB_PATH+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:return {'users':[dict(r) for r in db.execute('SELECT id,name,email,role FROM user ORDER BY created_at')]}
    finally:db.close()


class AddUser(Login):
    name:str=Field(min_length=1,max_length=100)
    password:str=Field(min_length=8,max_length=72)


@app.post('/api/admin/users')
async def add_user(body:AddUser,request:Request,value=Depends(admin)):
    if len(body.password.encode())>72:raise HTTPException(400,'Le mot de passe doit tenir dans 72 octets UTF-8.')
    details=body.model_dump();details['email']=details['email'].strip().lower()
    if '@' not in details['email']:details['email']+='@survie.local'
    result=await accounts.native('/api/v1/auths/add',{**details,'role':'user','profile_image_url':'/user.png'},token(request))
    return {k:result.get(k) for k in ('id','name','email','role')}


class Password(BaseModel):password:str=Field(min_length=8,max_length=72)


@app.post('/api/admin/users/{identifier}/password')
async def change_user_password(identifier:str,body:Password,request:Request,value=Depends(admin)):
    if len(body.password.encode())>72:raise HTTPException(400,'Le mot de passe doit tenir dans 72 octets UTF-8.')
    await accounts.native('/api/v1/users/'+identifier+'/update',body.model_dump(),token(request))
    return {'ok':True}


@app.post('/api/admin/reindex')
async def reindex(value=Depends(admin)):return {'guides':await asyncio.to_thread(library.index_guides)}


@app.post('/api/admin/guides')
async def upload(file:UploadFile=File(...),title:str=Form(...),language:str=Form('fr'),provenance:str=Form(''),licence:str=Form(''),value=Depends(admin)):
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.txt','.md','.epub'):raise HTTPException(400,'Formats acceptés : PDF, texte, Markdown ou EPUB.')
    data=await file.read(20_000_001)
    if len(data)>20_000_000:raise HTTPException(413,'Ce fichier dépasse 20 Mo.')
    language=language if language in ('fr','en') else ''
    path=store.new_id()+'.'+(language or 'other')+suffix
    library.GUIDES.mkdir(parents=True,exist_ok=True)
    (library.GUIDES/path).write_bytes(data)
    with store.connect() as db:db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',(path,title[:200],language,provenance[:1000],licence[:1000]))
    count=await asyncio.to_thread(library.index_guides)
    with store.connect() as db:
        indexed=db.execute('SELECT 1 FROM documents WHERE id=?',('guide:'+path,)).fetchone()
        if not indexed:db.execute('DELETE FROM guide_meta WHERE path=?',(path,))
    if not indexed:
        (library.GUIDES/path).unlink(missing_ok=True)
        raise HTTPException(400,'Le fichier n’a pas pu être lu. Vérifiez son format et son éventuelle protection par mot de passe.')
    return {'id':'guide:'+path,'guides':count}


class Feedback(BaseModel):
    content:str=Field(min_length=3,max_length=4000)
    view:str=Field(default='',max_length=200)


@app.post('/api/feedback')
async def feedback(body:Feedback,request:Request,value=Depends(user)):
    if not store.limit('feedback:'+value['id'],maximum=10,period=3600):raise HTTPException(429,'Merci, vos retours sont déjà enregistrés. Réessayez plus tard.')
    with store.connect() as db:db.execute('INSERT INTO feedback VALUES(?,?,?,?,?)',(store.new_id(),value['id'],body.content,body.view,time.time()))
    return {'ok':True}


@app.get('/api/admin/feedback')
async def feedback_list(value=Depends(admin)):
    with store.connect() as db:return {'feedback':[dict(r) for r in db.execute('SELECT * FROM feedback ORDER BY created DESC LIMIT 500')]}
