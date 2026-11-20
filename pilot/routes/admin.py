"""Routes du pilote — administration et maintenance : réglages, mise à jour, performance, calibrage, contexte et modèles."""
import asyncio
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from .. import engine,operations,store,geography,calibration,startup_diagnostic
from .deps import MODEL_DOWNLOADS,WorkPause,admin,optional_feature,user
from .work import pause_work_queue
from .. import app as core  # VERSION est défini dans pilot/app.py

router=APIRouter()


class LocationChoice(BaseModel):
    candidate: str | None = Field(default=None, pattern='^[a-f0-9]{32}$')
    lat: float | None = Field(default=None, ge=-85, le=85, allow_inf_nan=False)
    lon: float | None = Field(default=None, ge=-180, lt=180, allow_inf_nan=False)
    label: str = Field(default='Point choisi sur la carte', min_length=1, max_length=200)


@router.get('/api/settings')
async def get_settings(value=Depends(user)):
    return geography.settings()


@router.post('/api/admin/settings/{target}')
async def set_settings(target: str, body: LocationChoice, value=Depends(admin)):
    try:return geography.set_location(target, **body.model_dump())
    except ValueError as exc:raise HTTPException(400, str(exc))


@router.delete('/api/admin/settings/{target}')
async def clear_settings(target: str, value=Depends(admin)):
    if target not in ('home','departure'):raise HTTPException(400,'Emplacement inconnu.')
    geography.save(target,None)
    return {'ok':True}


class UpdateStart(BaseModel):
    confirmed:Literal[True]
    pause_queue:bool=False


@router.get('/api/maintenance/update')
async def update_status(value=Depends(admin)):
    return await operations.update_request()


@router.post('/api/maintenance/update/check',status_code=202)
async def update_check(value=Depends(admin)):
    return await operations.update_request('check')


@router.post('/api/maintenance/update/start',status_code=202)
async def update_start(body:UpdateStart,value=Depends(admin)):
    if body.pause_queue:
        # The updater waits for running work to stop; it refuses an active, unpaused queue.
        await pause_work_queue(WorkPause(paused=True),value)
    return await operations.update_request('start',{'confirmed':True})


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


class PerformanceChoice(BaseModel):
    mode:str=Field(default='rapide',max_length=100)


@router.get('/api/admin/performance')
async def get_performance(value=Depends(admin)):
    with optional_feature('performance') as module:return module.status()


@router.get('/api/admin/performance/report')
async def get_performance_report(value=Depends(admin)):
    with optional_feature('performance') as module:return module.status(full=True)


@router.post('/api/admin/performance/start',status_code=202)
async def start_performance(body:PerformanceChoice,value=Depends(admin)):
    async with startup_diagnostic.observe('performance',body.mode,core.VERSION):
        with optional_feature('performance') as module:return await module.start(body.mode,value['id'],core.VERSION)


@router.post('/api/admin/performance/stop')
async def stop_performance(value=Depends(admin)):
    with optional_feature('performance') as module:return await module.cancel()


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


@router.get('/api/admin/search-experiment')
async def get_search_experiment(value=Depends(admin)):
    with optional_feature('search_experiment') as module:return {'version':core.VERSION,**module.status()}


@router.post('/api/admin/search-experiment/start',status_code=202)
async def start_search_experiment(body:SearchExperimentChoice,value=Depends(admin)):
    async with startup_diagnostic.observe('search_experiment',body.mode,core.VERSION):
        with optional_feature('search_experiment') as module:
            report=await module.start(body.mode,body.suite,body.latency_budget_seconds*1000)
            report['version']=core.VERSION;module.save(report);return report


@router.post('/api/admin/search-experiment/stop')
async def stop_search_experiment(value=Depends(admin)):
    with optional_feature('search_experiment') as module:return await module.cancel()


@router.post('/api/admin/search-experiment/review')
async def review_search_experiment(body:SearchExperimentReview,value=Depends(admin)):
    with optional_feature('search_experiment') as module:return module.review(body.id,body.case_id,body.judgments)


@router.get('/api/admin/assistant/calibration')
async def get_calibration(value=Depends(admin)):
    report=await asyncio.to_thread(calibration.status)
    model=report.get('model')
    if model in {p['model'] for p in engine.MODES.values()}:
        report['configured_context']=engine.context_size(model)
        with store.connect() as db:previous=db.execute('SELECT value FROM settings WHERE key=?',('context:previous:'+model,)).fetchone()
        report['can_rollback']=bool(previous and str(previous['value']) in ('8192','16384','32768','65536') and str(previous['value'])!=str(report['configured_context']))
    return {'version':core.VERSION,**report}


@router.get('/api/admin/assistant/startup-report')
async def get_startup_report(mode:str|None=None,value=Depends(admin)):
    return await startup_diagnostic.report(core.VERSION,mode)


@router.post('/api/admin/assistant/calibration/start',status_code=202)
async def start_calibration(body:CalibrationChoice,value=Depends(admin)):
    async with startup_diagnostic.observe('calibration',body.mode,core.VERSION):
        return await calibration.start(body.mode,body.max_context,reserve_ram_bytes=body.reserve_ram_gib*1024**3,reserve_video_bytes=body.reserve_video_mib*1024**2,
            max_first_text_ms=body.max_first_text_seconds*1000,trial_timeout_seconds=body.trial_timeout_seconds)


@router.post('/api/admin/assistant/calibration/stop')
async def stop_calibration(value=Depends(admin)):return await calibration.cancel()


@router.post('/api/admin/assistant/calibration/apply')
async def apply_calibration(body:CalibrationApply,value=Depends(admin)):return await calibration.apply(body.id)


@router.post('/api/admin/assistant/context/rollback')
async def rollback_context(body:ContextModel,value=Depends(admin)):return await asyncio.to_thread(calibration.rollback,body.model)


@router.get('/api/admin/context')
async def get_context(value=Depends(admin)):
    models=list(dict.fromkeys(p['model'] for p in engine.MODES.values()))
    return {'models':[{'model':m,'tokens':engine.context_size(m)} for m in models]}


@router.post('/api/admin/context')
async def set_context(body:ContextChoice,value=Depends(admin)):
    if body.model not in {p['model'] for p in engine.MODES.values()}:raise HTTPException(400,'Modèle inconnu.')
    with store.connect() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('context:'+body.model,str(body.tokens)))
    return {'model':body.model,'tokens':body.tokens}


class ModelDownloadChoice(BaseModel):
    model: str = Field(min_length=1, max_length=150)


@router.get('/api/admin/models')
async def list_models(value=Depends(admin)):
    return await MODEL_DOWNLOADS.status()


@router.post('/api/admin/models/download',status_code=202)
async def download_model(body:ModelDownloadChoice,value=Depends(admin)):
    return await MODEL_DOWNLOADS.start(body.model)


class ModelDownloadCancellation(BaseModel):
    id: str = Field(pattern=r'^[a-f0-9]{32}$')


@router.post('/api/admin/models/cancel')
async def cancel_model_download(body:ModelDownloadCancellation,value=Depends(admin)):
    return await MODEL_DOWNLOADS.cancel(body.id)
