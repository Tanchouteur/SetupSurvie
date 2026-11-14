"""Authenticated local gateway for the first household pilot."""
import asyncio
from datetime import datetime,timezone
from contextlib import asynccontextmanager,contextmanager
import importlib
import logging
import json
import os
from pathlib import Path
import re
import time
from typing import Literal
from urllib.parse import quote,urlparse

from fastapi import FastAPI,Depends,HTTPException,Request,Response,UploadFile,File,Form,Query
from pydantic import BaseModel,Field
from starlette.responses import FileResponse,JSONResponse

from . import accounts,engine,inventory,library,maps,network,operations,store,geography,map_notebook,routing,translations,source_metadata,learning,profiles,catalogue,assistant_metrics,calibration

TERRAIN_LOCK=asyncio.Semaphore(2)
COOKIE='survie_session'


DEGRADED={}
STARTUP_FEATURE_TIMEOUT=30


@contextmanager
def optional_feature(name):
    try:
        module=importlib.import_module('.'+name,__package__)
        yield module
        DEGRADED.pop(name,None)
    except HTTPException:raise
    except Exception:
        DEGRADED[name]=True
        logging.getLogger(__name__).warning('Fonction optionnelle indisponible : %s',name)
        raise HTTPException(503,'Cette fonction est momentanément indisponible. Les autres documents et conversations restent accessibles.')


@asynccontextmanager
async def lifespan(app):
    store.init()
    await asyncio.to_thread(profiles.initialize)
    DEGRADED.clear()
    try:map_notebook.init()
    except Exception:DEGRADED['map_notebook']=True
    try:await asyncio.wait_for(asyncio.to_thread(library.index_guides),STARTUP_FEATURE_TIMEOUT)
    except Exception:
        DEGRADED['index']=True
        logging.getLogger(__name__).warning('Réindexation interrompue au démarrage ; dernier index conservé.')
    try:
        with optional_feature('publications') as module:await asyncio.wait_for(module.recover(),STARTUP_FEATURE_TIMEOUT)
    except HTTPException:pass
    yield
    await library.kiwix_queries.close()
    try:
        with optional_feature('search_experiment') as module:await module.cancel(reason='service_restarted')
    except HTTPException:pass
    await calibration.cancel(reason='service_restarted')
    for task in list(translations.ACTIVE.values()):task.cancel()
    if translations.ACTIVE:await asyncio.gather(*list(translations.ACTIVE.values()),return_exceptions=True)
    for task in list(engine.ACTIVE.values()):task.cancel()
    engine.PENDING.clear()
    if engine.ACTIVE:await asyncio.gather(*list(engine.ACTIVE.values()),return_exceptions=True)


VERSION='0.11.1'
app=FastAPI(title='SetupSurvie',version=VERSION,lifespan=lifespan,docs_url=None,redoc_url=None)


@app.exception_handler(routing.RoutingError)
async def routing_error_response(request:Request,exc:routing.RoutingError):
    # Keep detail a string for older tabs/API consumers; code is additive.
    return JSONResponse(status_code=exc.status_code,content={
        'detail':exc.detail['message'],'code':exc.detail['code']},headers=exc.headers)


@app.middleware('http')
async def origin_check(request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        expected=request.headers.get('host','')
        if origin and urlparse(origin).netloc!=expected:
            return Response('Origine non autorisée',status_code=403)
        if request.headers.get('sec-fetch-site')=='cross-site':return Response('Origine non autorisée',status_code=403)
        if (request.cookies.get(COOKIE) or request.cookies.get(profiles.COOKIE)) and not origin:
            return Response('Origine requise',status_code=403)
    response=await call_next(request)
    if not (request.url.path.startswith('/api/geography/shade/') and response.status_code in (200,304)):
        response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


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


@app.get('/api/health')
async def health():return {'ok':True,'version':VERSION,'degraded_features':sorted(DEGRADED)}


class LibrarySelection(BaseModel):
    themes:list[str]=Field(min_length=1,max_length=100)
    languages:list[str]=Field(default_factory=lambda:['fr','en'],min_length=1,max_length=2)
    max_add_gb:int=Field(default=0,ge=0)
    include_supplements:bool=False


class LibraryDownload(BaseModel):
    id:str=Field(pattern='^[a-f0-9]{32}$')


class IndexSettings(BaseModel):
    enabled:bool=True
    start_hour:int=Field(default=0,ge=0,le=23)
    end_hour:int=Field(default=0,ge=0,le=23)
    workers:int=Field(default=0,ge=0,le=16)


@app.post('/api/admin/library/index-settings')
async def set_index_settings(body:IndexSettings,value=Depends(admin)):
    return await operations.library_command('index-settings',body.model_dump())


@app.post('/api/admin/library/index/{action}')
async def index_archives(action:Literal['prepare','start','pause'],value=Depends(admin)):
    return await operations.library_command({'prepare':'index-prepare','start':'index','pause':'pause'}[action])


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


@app.get('/api/geography/shade/{z}/{x}/{y}.png')
async def terrain_shade_tile(z:int,x:int,y:int,request:Request,value=Depends(user)):
    if not 8<=z<=14 or not 0<=x<2**z or not 0<=y<2**z:raise HTTPException(404,'Tuile inconnue.')
    signature=await asyncio.to_thread(geography.terrain_signature)
    etag=geography.terrain_etag(signature,z,x,y)
    headers={'Cache-Control':'private, no-cache','ETag':etag,'Vary':'Cookie, X-Survie-Profile'}
    if request.headers.get('if-none-match')==etag:return Response(status_code=304,headers=headers)
    async with TERRAIN_LOCK:
        raw=await asyncio.to_thread(geography.terrain_shade_png,z,x,y,signature)
    return Response(raw,media_type='image/png',headers=headers)


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
    access_token: str | None = Field(default=None,max_length=6000)
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


class AccessRequest(BaseModel):
    lat: float = Field(ge=-85,le=85,allow_inf_nan=False)
    lon: float = Field(ge=-180,lt=180,allow_inf_nan=False)
    mode: Literal['foot','motorcycle','car'] = 'foot'
    avoid_motorways: bool = True
    near: list[float] | None = Field(default=None,min_length=2,max_length=2)


@app.post('/api/admin/map-notebook/accesses')
async def map_accesses(body:AccessRequest,value=Depends(admin)):
    if not store.limit('accesses:'+value['id'],maximum=30,period=60):raise HTTPException(429,'Attendez un instant avant de chercher un accès.')
    try:return await routing.accesses(body.lat,body.lon,body.mode,body.avoid_motorways,body.near)
    except ValueError as exc:raise HTTPException(422,str(exc))


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


@app.get('/api/activity')
async def local_activity():return await operations.activity()


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


class ProfileSelection(BaseModel):
    id:str=Field(min_length=1,max_length=200)


class ProfileCreation(BaseModel):
    name:str=Field(min_length=1,max_length=100)


@app.get('/api/profiles')
async def profile_list():return {'profiles':await asyncio.to_thread(profiles.listing)}


@app.get('/api/auth/me')
@app.get('/api/profiles/current')
async def me(value=Depends(user)):return public_user(value)


@app.post('/api/profiles/select')
async def select_profile(body:ProfileSelection,request:Request,response:Response):
    value=await asyncio.to_thread(profiles.selected,body.id)
    profile_cookie(response,request,value['id'])
    return public_user(value)


@app.post('/api/profiles',status_code=201)
async def create_profile(body:ProfileCreation,request:Request,response:Response):
    value=await asyncio.to_thread(profiles.create,body.name)
    profile_cookie(response,request,value['id'])
    return public_user(value)


@app.get('/api/profiles/webui-headers')
async def webui_profile(value=Depends(user)):
    return Response(status_code=200,headers=profiles.webui_headers(value))


@app.post('/api/auth/{action}')
async def retired_login(action:str):
    raise HTTPException(410,'Les mots de passe et codes de secours ont été remplacés par les profils. Rechargez la page puis choisissez votre profil.')


@app.get('/api/library/search-diagnostic')
async def search_diagnostic():
    async def server():
        started=time.monotonic()
        try:
            await asyncio.wait_for(library.get('/'),3)
            return {'state':'reachable','elapsed_ms':round((time.monotonic()-started)*1000)}
        except (TimeoutError,HTTPException):return {'state':'unavailable','elapsed_ms':round((time.monotonic()-started)*1000)}
        except Exception:return {'state':'unavailable','elapsed_ms':round((time.monotonic()-started)*1000)}
    catalog,access=await asyncio.gather(library.books(refresh=True),server())
    info=catalog.info() if isinstance(catalog,library.Catalog) else {'state':'live','collections':len(catalog)}
    report=await asyncio.to_thread(library.index_report)
    return {'version':VERSION,'created':time.time(),'kiwix':access,'catalog':info,
            'guides':{'indexed':report.get('indexed',0),'status':report.get('status')},
            'archive_index':library.archive_index.status(store.ROOT/'archive-index'),
            'notice':'Diagnostic sans IA. Mesure de préparation distincte des recherches suivantes.'}


@app.get('/api/search')
async def search(request:Request,q:str=Query(default='',max_length=200),language:str='',limit:int=Query(default=8,ge=1,le=20),favorites_only:bool=False,translations_only:bool=False,collection:str=Query(default='',max_length=160),domain:Literal['all','resilience','culture']='all',diagnostic:bool=False):
    owner=(await user(request))['id'] if favorites_only else None
    if favorites_only or translations_only:
        with optional_feature('favorites' if favorites_only else 'publications'):
            found=await library.search(q.strip(),language,limit=limit,favorite_user=owner,translations_only=translations_only,collection=collection,domain=domain,**({'diagnostic':True} if diagnostic else {})) if q.strip() else []
    else:
        found=await library.search(q.strip(),language,limit=limit,favorite_user=owner,translations_only=translations_only,collection=collection,domain=domain,**({'diagnostic':True} if diagnostic else {})) if q.strip() else []
    return {'results':found,**({'coverage':found.coverage} if isinstance(found,library.SearchResults) else {})}



class FavoriteRequest(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)


@app.get('/api/favorites')
async def favorite_list(language:str='',value=Depends(user)):
    with optional_feature('favorites') as module:return {'results':module.listing(value['id'],language)}


@app.put('/api/favorites')
async def favorite_add(body:FavoriteRequest,value=Depends(user)):
    with optional_feature('favorites') as module:
        await module.add(value['id'],body.source_id)
        return {'ok':True,'source_id':module.canonical(body.source_id)}


@app.delete('/api/favorites')
async def favorite_remove(source_id:str=Query(min_length=1,max_length=2000),value=Depends(user)):
    with optional_feature('favorites') as module:module.remove(value['id'],source_id)
    return {'ok':True}


@app.get('/api/library/translations')
async def shared_translations():
    with optional_feature('publications') as publications:
        with store.connect() as db:
            rows=db.execute("SELECT g.path,g.title,g.language FROM guide_meta g JOIN translation_publications p ON p.published_path=g.path WHERE p.published_at IS NOT NULL ORDER BY p.published_at DESC LIMIT 200").fetchall()
            return {'results':[{'id':'guide:'+row['path'],'title':row['title'],'language':row['language'],'kind':'guide','url':'/guides/'+quote(row['path']),'excerpt':publications.NOTICE,**library.guide_metadata(db,'guide:'+row['path'])} for row in rows]}


@app.get('/api/library/learning')
async def learning_paths():
    try:return learning.pathways()
    except (OSError,ValueError,KeyError):raise HTTPException(503,'Les parcours ne sont pas disponibles. La recherche documentaire reste accessible.')


@app.get('/api/source')
async def source(id:str):return await library.source(id)


class PracticalReference(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    source_revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    dossier_revision:int=Field(ge=0)
    sections:list[str]=Field(min_length=1,max_length=6)
    note:str=Field(min_length=1,max_length=700)
    locator:str=Field(min_length=1,max_length=200)
    reviewed:bool=False


@app.get('/api/library/dossiers')
async def practical_dossiers():
    with optional_feature('practical') as module:return await asyncio.to_thread(module.overview)


@app.get('/api/library/dossiers/{identifier}')
async def practical_dossier(identifier:str):
    with optional_feature('practical') as module:return await asyncio.to_thread(module.dossier,identifier)


@app.get('/api/library/dossiers/{identifier}/search')
async def practical_sources(identifier:str):
    with optional_feature('practical') as module:return await module.search(identifier)


@app.put('/api/admin/library/dossiers/{identifier}/references')
async def save_practical_reference(identifier:str,body:PracticalReference,value=Depends(admin)):
    with optional_feature('practical') as module:
        return await module.save(identifier,body.source_id,body.source_revision,body.dossier_revision,body.sections,body.note,body.locator,body.reviewed)


@app.delete('/api/admin/library/dossiers/{identifier}/references/{entry_id}')
async def remove_practical_reference(identifier:str,entry_id:str,revision:int=Query(ge=0),value=Depends(admin)):
    with optional_feature('practical') as module:return await asyncio.to_thread(module.remove,identifier,entry_id,revision)


@app.get('/api/admin/library/dossiers-export')
async def export_practical_dossiers(value=Depends(admin)):
    with optional_feature('practical') as module:return {'version':VERSION,**await asyncio.to_thread(module.export)}


class SourceClassification(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    domains:list[Literal['resilience','culture']]=Field(max_length=2)
    document_type:Literal['unknown','overview','explanation','procedure','exercise','manual']='unknown'
    reviewed:bool=False


class CollectionLabels(BaseModel):
    collection_id:str=Field(min_length=1,max_length=300)
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    family:str=Field(min_length=1,max_length=80)
    variant:str=Field(min_length=1,max_length=120)


@app.put('/api/admin/library/classification')
async def set_classification(body:SourceClassification,value=Depends(admin)):
    if not body.source_id.startswith(('guide:','zim:')):raise HTTPException(400,'Référence de document invalide.')
    with optional_feature('catalogue') as module:
        return await asyncio.to_thread(module.save,body.source_id,{'domains':body.domains,'document_type':body.document_type,'status':'reviewed' if body.reviewed else 'corrected'},body.revision,library.GUIDES,inventory.ZIMS)


@app.put('/api/admin/library/collection-labels')
async def set_collection_labels(body:CollectionLabels,value=Depends(admin)):
    with optional_feature('catalogue') as module:
        return await asyncio.to_thread(module.save,'collection:'+body.collection_id,{'family':body.family.strip(),'variant':body.variant.strip()},body.revision,library.GUIDES,inventory.ZIMS)


@app.delete('/api/admin/library/metadata')
async def reset_document_metadata(source_id:str=Query(min_length=1,max_length=2000),value=Depends(admin)):
    with optional_feature('catalogue') as module:await asyncio.to_thread(module.reset,source_id)
    return {'ok':True}


@app.get('/api/admin/library/metadata-export')
async def export_document_metadata(value=Depends(admin)):
    with optional_feature('catalogue') as module:return await asyncio.to_thread(module.export)


@app.get('/api/original')
async def original_pdf(id:str=Query(max_length=2000)):
    base=id.split('#page=')[0]
    if not base.startswith('guide:') or not base.lower().endswith('.pdf'):raise HTTPException(400,'Document PDF local requis.')
    await library.source(base)
    path=library.GUIDES/base.removeprefix('guide:')
    if any(p.is_symlink() for p in [path,*path.parents]) or not path.resolve().is_relative_to(library.GUIDES.resolve()) or not path.is_file():
        raise HTTPException(404,'Document original indisponible.')
    return FileResponse(path,media_type='application/pdf',headers={'Content-Disposition':'inline','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; frame-ancestors 'self'"})


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
    with store.connect() as db:translated=[dict(r) for r in db.execute('SELECT id,title,source_id,status,created,mode FROM translations WHERE conversation_id=? ORDER BY created DESC',(identifier,))]
    with store.connect() as db:recent=[dict(r) for r in db.execute('SELECT id,mode,status,created FROM jobs WHERE conversation_id=? ORDER BY created DESC LIMIT 20',(identifier,))]
    measured=[r for r in recent if r['id'] in engine.MEASUREMENTS or assistant_metrics.path(r['id']).is_file()]
    return {**item,'messages':store.messages(identifier),'jobs':jobs,'source':store.conversation_source(identifier),'translations':[r['id'] for r in translated],'translation_items':translated,'measurement_jobs':measured}


@app.delete('/api/conversations/{identifier}')
async def delete_conversation(identifier:str,value=Depends(user)):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():
            raise HTTPException(404,'Conversation introuvable.')
        if db.execute("SELECT 1 FROM translations WHERE conversation_id=? AND status IN ('queued','running')",(identifier,)).fetchone():raise HTTPException(409,'Mettez la traduction en pause avant de supprimer cette conversation.')
        if db.execute("SELECT 1 FROM translations t JOIN settings s ON s.key='auto-translation:'||t.id WHERE t.conversation_id=? AND t.status='completed' AND NOT EXISTS(SELECT 1 FROM settings done WHERE done.key='published-translation:'||t.id)",(identifier,)).fetchone():
            raise HTTPException(409,'L’ajout d’une traduction terminée aux documents locaux reste à finaliser. Réessayez son ajout ou exportez-la avant de supprimer la conversation.')
        jobs=db.execute('SELECT id,status FROM jobs WHERE conversation_id=?',(identifier,)).fetchall()
        if any(job['status'] in ('queued','running') for job in jobs):
            raise HTTPException(409,'Une réponse est en cours. Attendez sa fin ou annulez-la avant de supprimer cette conversation.')
        db.execute('DELETE FROM jobs WHERE conversation_id=?',(identifier,))
        db.execute('DELETE FROM conversations WHERE id=? AND user_id=?',(identifier,value['id']))
    for job in jobs:
        (store.ROOT/'traces'/(job['id']+'.json')).unlink(missing_ok=True)
        assistant_metrics.path(job['id']).unlink(missing_ok=True)
    return {'ok':True}


class Question(BaseModel):
    message:str=Field(min_length=1,max_length=6000)
    mode:str='rapide'
    domain:Literal['all','resilience','culture']='all'
    conversation_id:str|None=Field(default=None,max_length=100)
    source_id:str|None=Field(default=None,max_length=2000)


@app.post('/api/questions')
async def question(body:Question,value=Depends(user)):
    request_started=time.monotonic();reading_ms=0
    if body.mode not in engine.MODES:raise HTTPException(400,'Mode inconnu.')
    state=await operations.status()
    if not state.get('online') or state.get('operation'):
        raise HTTPException(503,state['message']+'. La bibliothèque reste disponible. Consultez « État de l’appareil » pour le redémarrage.')
    conversation_id=body.conversation_id
    if conversation_id and not store.owned_conversation(conversation_id,value['id']):raise HTTPException(404,'Conversation introuvable.')
    attached=store.conversation_source(conversation_id) if conversation_id else None
    source_id=body.source_id if 'source_id' in body.model_fields_set else (attached or {}).get('id')
    source=None
    if source_id:
        started=time.monotonic();source=await library.source(source_id);reading_ms=round((time.monotonic()-started)*1000)
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if conversation_id and not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation_id,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=20:
            raise HTTPException(429,'La file d’attente est pleine. Réessayez après les demandes en cours.')
        if db.execute("SELECT count(*) FROM jobs WHERE user_id=? AND status IN ('queued','running')",(value['id'],)).fetchone()[0]>=2:
            raise HTTPException(429,'Vous avez déjà des questions en cours. Attendez ou annulez-en une.')
        if not conversation_id:
            conversation_id=store.new_id();db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation_id,value['id'],body.message[:80],time.time()))
        store.set_conversation_source(db,conversation_id,source)
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation_id,'user',body.message,time.time()))
        identifier=store.new_id();now=time.time()
        db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(identifier,value['id'],conversation_id,body.mode,'queued',now,now))
    engine.PENDING[identifier]={'started':request_started,'preparation_ms':max(0,round((time.monotonic()-request_started)*1000)-reading_ms),'reading_ms':reading_ms,'source':source}
    engine.launch(identifier,value['id'],conversation_id,body.mode,source_id,domain=body.domain)
    return {'id':identifier,'conversation_id':conversation_id}


class AssociatedSource(BaseModel):
    source_id:str|None=Field(default=None,max_length=2000)


@app.put('/api/conversations/{identifier}/source')
async def associate_source(identifier:str,body:AssociatedSource,value=Depends(user)):
    if not store.owned_conversation(identifier,value['id']):raise HTTPException(404,'Conversation introuvable.')
    source=await library.source(body.source_id) if body.source_id else None
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
        store.set_conversation_source(db,identifier,source)
    return {'source':store.conversation_source(identifier)}


class TranslationRequest(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    conversation_id:str|None=Field(default=None,max_length=100)
    mode:str='rapide'
    first_page:int=Field(default=1,ge=1,le=1200)
    last_page:int|None=Field(default=None,ge=1,le=1200)


class TranslationResume(BaseModel):
    mode:str|None=None


@app.post('/api/translations',status_code=202)
async def translate_document(body:TranslationRequest,value=Depends(user)):
    return await translations.create(value['id'],body.source_id,body.conversation_id,body.mode,body.first_page,body.last_page)


@app.get('/api/translations/{identifier}')
async def translation_status(identifier:str,offset:int=Query(default=0,ge=0,le=100000),value=Depends(user)):
    return translations.status(identifier,value['id'],offset)


@app.post('/api/translations/{identifier}/pause')
async def pause_translation(identifier:str,value=Depends(user)):
    return await translations.pause(identifier,value['id'])


@app.post('/api/translations/{identifier}/resume',status_code=202)
async def resume_translation(identifier:str,body:TranslationResume,value=Depends(user)):
    return await translations.resume(identifier,value['id'],body.mode)


@app.get('/api/translations/{identifier}/export')
async def export_translation(identifier:str,value=Depends(user)):
    text=translations.export(identifier,value['id'])
    return Response(text,media_type='text/plain; charset=utf-8',headers={'Content-Disposition':'attachment; filename="traduction-fr.txt"'})


@app.post('/api/translations/{identifier}/publish')
async def publish_translation(identifier:str,value=Depends(user)):
    item=translations.owned(identifier,value['id'])
    try:source=await library.source(item['source_id'])
    except HTTPException:source={'id':item['source_id'],'title':item['title']}
    with optional_feature('publications') as module:
        with store.connect() as db:module.reserve(db,identifier,value['id'],source)
        return await module.publish(identifier,value['id'])


@app.get('/api/jobs/{identifier}')
async def job(identifier:str,value=Depends(user)):
    with store.connect() as db:row=db.execute('SELECT * FROM jobs WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone()
    if not row:raise HTTPException(404,'Demande introuvable.')
    live=engine.MEASUREMENTS.get(identifier)
    measured=live.live() if live else assistant_metrics.read(identifier)
    return {**dict(row),'sources':json.loads(row['sources']),'progress':engine.PROGRESS.get(identifier,{}),'measurements':measured}


@app.get('/api/jobs/{identifier}/measurements')
async def job_measurements(identifier:str,value=Depends(user)):
    found=await job(identifier,value)
    if not found['measurements']:raise HTTPException(404,'Mesures indisponibles pour cette ancienne réponse.')
    return {'version':VERSION,**found['measurements']}


@app.post('/api/jobs/{identifier}/cancel')
async def cancel(identifier:str,value=Depends(user)):
    await job(identifier,value);engine.cancel(identifier)
    return {'ok':True}


@app.post('/api/transcribe')
async def transcribe(request:Request,file:UploadFile=File(...),value=Depends(user)):
    content=await file.read(20_000_001)
    if len(content)>20_000_000:raise HTTPException(413,'Enregistrement trop long. Essayez une dictée plus courte.')
    credential=await accounts.profile_token(value)
    async with accounts.httpx.AsyncClient(trust_env=False,timeout=180) as client:
        result=await client.post(accounts.WEBUI+'/api/v1/audio/transcriptions',headers={'Authorization':'Bearer '+credential,**profiles.webui_headers(value)},
            files={'file':(Path(file.filename or 'dictee.webm').name,content,file.content_type or 'audio/webm')},data={'language':'fr'})
    if result.status_code!=200:raise HTTPException(503,'La dictée est indisponible. Vous pouvez écrire votre question.')
    return {'text':result.json().get('text','')}


@app.get('/api/admin/users')
async def users(value=Depends(admin)):return {'users':await asyncio.to_thread(profiles.listing)}


@app.post('/api/admin/users')
async def add_user(body:ProfileCreation,value=Depends(admin)):
    return public_user(await asyncio.to_thread(profiles.create,body.name))


@app.post('/api/admin/reindex')
async def reindex(value=Depends(admin)):return {'guides':await asyncio.to_thread(library.index_guides)}


@app.post('/api/admin/guides')
async def upload(file:UploadFile=File(...),title:str=Form(...),language:str=Form('fr'),provenance:str=Form(''),licence:str=Form(''),
                 document_date:str=Form('',max_length=10),edition:str=Form('',max_length=300),value=Depends(admin)):
    document_date=document_date.strip()
    if document_date and not source_metadata.date_value(document_date):raise HTTPException(422,'Date du document : indiquez une année, une année-mois ou une date AAAA-MM-JJ valide, ou laissez vide si elle est inconnue.')
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.txt','.md','.epub'):raise HTTPException(400,'Formats acceptés : PDF, texte, Markdown ou EPUB.')
    data=await file.read(20_000_001)
    if len(data)>20_000_000:raise HTTPException(413,'Ce fichier dépasse 20 Mo.')
    language=language if language in ('fr','en') else ''
    path=store.new_id()+'.'+(language or 'other')+suffix
    library.GUIDES.mkdir(parents=True,exist_ok=True)
    from .durable import write_bytes
    write_bytes(library.GUIDES/path,data)
    with store.connect() as db:
        db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',(path,title[:200],language,provenance[:1000],licence[:1000]))
        db.execute('INSERT INTO guide_dates VALUES(?,?,?,?)',(path,document_date,edition.strip(),datetime.now(timezone.utc).date().isoformat()))
    count=await asyncio.to_thread(library.index_guides)
    with store.connect() as db:
        indexed=db.execute('SELECT 1 FROM documents WHERE id=?',('guide:'+path,)).fetchone()
        if not indexed:
            db.execute('DELETE FROM guide_meta WHERE path=?',(path,))
            db.execute('DELETE FROM guide_dates WHERE path=?',(path,))
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


class ContextChoice(BaseModel):
    model:str=Field(max_length=100)
    tokens:Literal[8192,16384,32768,65536]


class CalibrationChoice(BaseModel):
    mode:str=Field(default='rapide',max_length=100)
    max_context:Literal[16384,32768,65536]=32768
    reserve_ram_gib:int=Field(default=4,ge=2,le=16)
    reserve_video_mib:int=Field(default=512,ge=256,le=4096)
    max_first_text_seconds:int=Field(default=90,ge=10,le=600)
    trial_timeout_seconds:int=Field(default=600,ge=30,le=900)


class CalibrationApply(BaseModel):
    id:str=Field(pattern=r'^[a-f0-9]{32}$')


class ContextModel(BaseModel):
    model:str=Field(max_length=100)


class SearchExperimentChoice(BaseModel):
    mode:str=Field(default='rapide',max_length=40)
    suite:Literal['verification','all']='verification'
    latency_budget_seconds:int=Field(default=15,ge=1,le=60)


class SearchExperimentReview(BaseModel):
    id:str=Field(pattern=r'^[a-f0-9]{32}$')
    case_id:str=Field(max_length=100)
    judgments:dict[str,Literal['useful','unrelated','uncertain']]=Field(max_length=12)


@app.get('/api/admin/search-experiment')
async def get_search_experiment(value=Depends(admin)):
    with optional_feature('search_experiment') as module:return {'version':VERSION,**module.status()}


@app.post('/api/admin/search-experiment/start',status_code=202)
async def start_search_experiment(body:SearchExperimentChoice,value=Depends(admin)):
    with optional_feature('search_experiment') as module:
        report=await module.start(body.mode,body.suite,body.latency_budget_seconds*1000)
        report['version']=VERSION;module.save(report);return report


@app.post('/api/admin/search-experiment/stop')
async def stop_search_experiment(value=Depends(admin)):
    with optional_feature('search_experiment') as module:return await module.cancel()


@app.post('/api/admin/search-experiment/review')
async def review_search_experiment(body:SearchExperimentReview,value=Depends(admin)):
    with optional_feature('search_experiment') as module:return module.review(body.id,body.case_id,body.judgments)


@app.get('/api/admin/assistant/calibration')
async def get_calibration(value=Depends(admin)):
    report=await asyncio.to_thread(calibration.status)
    model=report.get('model')
    if model in {p['model'] for p in engine.MODES.values()}:
        report['configured_context']=engine.context_size(model)
        with store.connect() as db:previous=db.execute('SELECT value FROM settings WHERE key=?',('context:previous:'+model,)).fetchone()
        report['can_rollback']=bool(previous and str(previous['value']) in ('8192','16384','32768','65536') and str(previous['value'])!=str(report['configured_context']))
    return {'version':VERSION,**report}


@app.post('/api/admin/assistant/calibration/start',status_code=202)
async def start_calibration(body:CalibrationChoice,value=Depends(admin)):
    return await calibration.start(body.mode,body.max_context,reserve_ram_bytes=body.reserve_ram_gib*1024**3,reserve_video_bytes=body.reserve_video_mib*1024**2,
        max_first_text_ms=body.max_first_text_seconds*1000,trial_timeout_seconds=body.trial_timeout_seconds)


@app.post('/api/admin/assistant/calibration/stop')
async def stop_calibration(value=Depends(admin)):return await calibration.cancel()


@app.post('/api/admin/assistant/calibration/apply')
async def apply_calibration(body:CalibrationApply,value=Depends(admin)):return await calibration.apply(body.id)


@app.post('/api/admin/assistant/context/rollback')
async def rollback_context(body:ContextModel,value=Depends(admin)):return await asyncio.to_thread(calibration.rollback,body.model)


@app.get('/api/admin/context')
async def get_context(value=Depends(admin)):
    models=list(dict.fromkeys(p['model'] for p in engine.MODES.values()))
    return {'models':[{'model':m,'tokens':engine.context_size(m)} for m in models]}


@app.post('/api/admin/context')
async def set_context(body:ContextChoice,value=Depends(admin)):
    if body.model not in {p['model'] for p in engine.MODES.values()}:raise HTTPException(400,'Modèle inconnu.')
    with store.connect() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('context:'+body.model,str(body.tokens)))
    return {'model':body.model,'tokens':body.tokens}
