"""Routes du pilote — cartes, géographie, carnet de cartes et itinéraires."""
import asyncio
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Request,Response,Query
from pydantic import BaseModel,Field
from .. import operations,store,geography,map_notebook,routing
from .deps import TERRAIN_LOCK,admin,user

router=APIRouter()


class GeographyDownload(BaseModel):
    lat: float = Field(ge=-80, le=80, allow_inf_nan=False)
    lon: float = Field(ge=-180, lt=180, allow_inf_nan=False)
    radius_km: int = Field(default=10, ge=1, le=25, strict=True)
    terrain: bool = True


@router.get('/api/geography/addresses')
async def find_addresses(q: str = Query(min_length=3,max_length=200), online: bool = False, value=Depends(user)):
    if online and value['role']!='admin':raise HTTPException(403,'Recherche en ligne réservée à l’administrateur.')
    return await geography.addresses(q, online)


@router.get('/api/geography/status')
async def geography_status(value=Depends(user)):
    return await asyncio.to_thread(geography.status)


@router.post('/api/admin/library/geography',status_code=202)
async def download_geography(body: GeographyDownload,value=Depends(admin)):
    return await operations.library_command('geography',body.model_dump())


@router.post('/api/admin/library/routing',status_code=202)
async def download_routes(body: GeographyDownload,value=Depends(admin)):
    return await operations.library_command('routing',body.model_dump())


@router.get('/api/geography/nearby')
async def nearby_places(category: str, radius_km: float = Query(default=5,gt=0,le=25),
                        lat: float = Query(ge=-85,le=85,allow_inf_nan=False), lon: float = Query(ge=-180,lt=180,allow_inf_nan=False), value=Depends(user)):
    try:return await asyncio.to_thread(geography.nearby,category,radius_km,lat,lon)
    except ValueError as exc:raise HTTPException(400,str(exc))


@router.get('/api/geography/elevation')
async def point_elevation(lat: float = Query(ge=-85,le=85,allow_inf_nan=False), lon: float = Query(ge=-180,lt=180,allow_inf_nan=False),value=Depends(user)):
    return await asyncio.to_thread(geography.elevation,lat,lon)


@router.get('/api/geography/profile')
async def terrain_profile(lat1:float,lon1:float,lat2:float,lon2:float,value=Depends(user)):
    try:return await asyncio.to_thread(geography.profile,lat1,lon1,lat2,lon2)
    except ValueError as exc:raise HTTPException(400,str(exc))


@router.get('/api/geography/terrain/{z}/{x}/{y}.png')
async def terrain_tile(z:int,x:int,y:int,value=Depends(user)):
    async with TERRAIN_LOCK:
        raw=await asyncio.to_thread(geography.terrain_png,z,x,y)
    return Response(raw,media_type='image/png')


@router.get('/api/geography/shade/{z}/{x}/{y}.png')
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


@router.get('/api/map-notebook')
async def map_notebook_status(value=Depends(user)):
    return await asyncio.to_thread(map_notebook.overview)


@router.post('/api/admin/map-notebook/lists')
async def create_map_list(body:MapList,value=Depends(admin)):
    return map_notebook.save_list(body.title)


@router.post('/api/admin/map-notebook/lists/{identifier}')
async def update_map_list(identifier:str,body:MapList,value=Depends(admin)):
    return map_notebook.save_list(body.title,identifier)


@router.delete('/api/admin/map-notebook/lists/{identifier}')
async def delete_map_list(identifier:str,value=Depends(admin)):
    map_notebook.delete_list(identifier);return {'ok':True}


@router.post('/api/admin/map-notebook/points')
async def create_map_point(body:MapPoint,value=Depends(admin)):
    return map_notebook.save_point(body.model_dump())


@router.post('/api/admin/map-notebook/points/{identifier}')
async def update_map_point(identifier:str,body:MapPoint,value=Depends(admin)):
    return map_notebook.save_point(body.model_dump(),identifier)


@router.delete('/api/admin/map-notebook/points/{identifier}')
async def delete_map_point(identifier:str,value=Depends(admin)):
    map_notebook.delete_point(identifier);return {'ok':True}


@router.get('/api/routing')
async def routing_status(value=Depends(user)):
    return await asyncio.to_thread(routing.status)


class AccessRequest(BaseModel):
    lat: float = Field(ge=-85,le=85,allow_inf_nan=False)
    lon: float = Field(ge=-180,lt=180,allow_inf_nan=False)
    mode: Literal['foot','motorcycle','car'] = 'foot'
    avoid_motorways: bool = True
    near: list[float] | None = Field(default=None,min_length=2,max_length=2)


@router.post('/api/admin/map-notebook/accesses')
async def map_accesses(body:AccessRequest,value=Depends(admin)):
    if not store.limit('accesses:'+value['id'],maximum=30,period=60):raise HTTPException(429,'Attendez un instant avant de chercher un accès.')
    try:return await routing.accesses(body.lat,body.lon,body.mode,body.avoid_motorways,body.near)
    except ValueError as exc:raise HTTPException(422,str(exc))


@router.post('/api/admin/map-notebook/calculate')
async def calculate_route(body:RouteRequest,value=Depends(admin)):
    if not store.limit('routing:'+value['id'],maximum=12,period=60):raise HTTPException(429,'Attendez un instant avant de recalculer.')
    data=await routing.calculate([p.model_dump() for p in body.points],body.mode,body.speed_kmh,body.avoid_motorways)
    return map_notebook.draft(value['id'],data)


@router.post('/api/admin/map-notebook/routes')
async def save_map_route(body:SavedRoute,value=Depends(admin)):
    if not body.title.strip():raise HTTPException(400,'Donnez un nom au trajet.')
    return map_notebook.save_route(value['id'],body.draft_id,body.list_id,body.title)


@router.get('/api/map-notebook/routes/{identifier}')
async def saved_map_route(identifier:str,value=Depends(user)):
    return await asyncio.to_thread(map_notebook.route,identifier)


@router.delete('/api/admin/map-notebook/routes/{identifier}')
async def delete_map_route(identifier:str,value=Depends(admin)):
    map_notebook.delete_route(identifier);return {'ok':True}


@router.get('/api/map-notebook/lists/{identifier}/gpx')
async def map_list_gpx(identifier:str,value=Depends(user)):
    return Response(map_notebook.gpx(list_id=identifier),media_type='application/gpx+xml',headers={'Content-Disposition':'attachment; filename="points-setupsurvie.gpx"'})


@router.get('/api/map-notebook/routes/{identifier}/gpx')
async def map_route_gpx(identifier:str,value=Depends(user)):
    return Response(map_notebook.gpx(route_id=identifier),media_type='application/gpx+xml',headers={'Content-Disposition':'attachment; filename="trajet-setupsurvie.gpx"'})
