"""Authenticated local gateway for the first household pilot."""
import asyncio
import importlib
import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI,HTTPException,Request,Response
from starlette.responses import JSONResponse

from . import work_queue,youtube_pipeline
from . import engine,library,map_notebook,routing,store,translations,learning,profiles,calibration
from .routes.deps import TERRAIN_LOCK,COOKIE,MODEL_DOWNLOADS,DEGRADED,optional_feature,user,admin,public_user,profile_cookie,SourceIdentifier,WorkPause,CaptionResume  # noqa: F401 (noms historiques de ce module)
from .routes import status,profiles as profile_routes,library as library_routes,maps,conversations,videos,work,documents,admin as admin_routes
from .routes.status import health  # noqa: F401
from .routes.work import pause_work_queue  # noqa: F401

STARTUP_FEATURE_TIMEOUT=30


async def prepare_initial_index(app):
    async def index():
        try:
            await asyncio.to_thread(library.index_guides, automatic=True)
            DEGRADED.pop('index',None)
        except Exception:
            DEGRADED['index']=True
            logging.getLogger(__name__).warning('Indexation des guides indisponible au démarrage.')

    app.state.initial_index_task=asyncio.create_task(index())
    try:await asyncio.wait_for(asyncio.shield(app.state.initial_index_task),STARTUP_FEATURE_TIMEOUT)
    except asyncio.TimeoutError:
        if not app.state.initial_index_task.done():
            DEGRADED['index']=True
            logging.getLogger(__name__).warning('La préparation de l’index continue en arrière-plan.')



@asynccontextmanager
async def lifespan(app):
    store.init()
    work_queue.QUEUE.initialize()
    youtube_pipeline.initialize()
    await asyncio.to_thread(profiles.initialize)
    DEGRADED.clear()
    try:map_notebook.init()
    except Exception:DEGRADED['map_notebook']=True
    library.GUIDE_REFRESH_STOP.clear()
    await prepare_initial_index(app)
    try:
        with optional_feature('publications') as module:await asyncio.wait_for(module.recover(),STARTUP_FEATURE_TIMEOUT)
    except HTTPException:pass
    # Keep the video directory searchable without a manual inventory. The
    # check only lists names, sizes and dates; it never blocks startup.
    async def refresh_videos():
        try:
            with optional_feature('videos') as module:await module.ensure_fresh(force=True)
        except Exception:pass
    video_refresh=asyncio.create_task(refresh_videos())
    guide_watch=asyncio.create_task(library.watch_guides())
    youtube_watch=asyncio.create_task(youtube_pipeline.watch())
    yield
    await MODEL_DOWNLOADS.cancel()
    youtube_watch.cancel()
    await asyncio.gather(youtube_watch,return_exceptions=True)
    await youtube_pipeline.stop()
    video_refresh.cancel()
    library.GUIDE_REFRESH_STOP.set()
    guide_watch.cancel()
    await asyncio.gather(video_refresh,guide_watch,return_exceptions=True)
    try:
        with optional_feature('archive_videos') as module:await module.stop_all()
    except HTTPException:pass
    try:
        with optional_feature('caption_acquisition') as module:await module.stop_all()
    except HTTPException:pass
    try:
        with optional_feature('transcriptions') as module:await module.stop_all()
    except HTTPException:pass
    try:
        with optional_feature('translation_benchmark') as module:await module.pause(reason='service_restarted')
    except HTTPException:pass
    try:
        with optional_feature('captions') as module:await module.stop_all()
    except HTTPException:pass
    try:
        with optional_feature('videos') as module:await module.stop(reason='service_restarted')
    except HTTPException:pass
    try:
        with optional_feature('performance') as module:await module.cancel(reason='service_restarted')
    except HTTPException:pass
    try:
        with optional_feature('search_experiment') as module:await module.cancel(reason='service_restarted')
    except HTTPException:pass
    await calibration.cancel(reason='service_restarted')
    try:
        with optional_feature('summaries') as module:await module.stop_all()
    except HTTPException:pass
    for task in list(translations.ACTIVE.values()):task.cancel()
    if translations.ACTIVE:await asyncio.gather(*list(translations.ACTIVE.values()),return_exceptions=True)
    for task in list(engine.ACTIVE.values()):task.cancel()
    engine.PENDING.clear()
    if engine.ACTIVE:await asyncio.gather(*list(engine.ACTIVE.values()),return_exceptions=True)
    # Close the documentary cache after jobs stop creating new requests.
    await library.kiwix_queries.close()


VERSION='0.81.0'
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


for _module in (status,profile_routes,library_routes,maps,conversations,videos,work,documents,admin_routes):
    app.include_router(_module.router)
