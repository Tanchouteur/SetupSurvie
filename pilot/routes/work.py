"""Routes du pilote — file de travail et suivi des tâches de l’utilisateur."""
import asyncio
from typing import Literal
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from starlette.responses import JSONResponse
from .. import work_queue,youtube_pipeline
from .. import operations
from .deps import WorkPause,admin,optional_feature,user

router=APIRouter()


@router.get('/api/my-work')
async def my_work(value=Depends(user)):
    with optional_feature('document_workspace') as module:return await asyncio.to_thread(module.recent,value['id'])


@router.get('/api/document-work')
async def document_work(source_id:str=Query(min_length=1,max_length=2000,pattern=r'^(guide|zim):.+$'),value=Depends(user)):
    with optional_feature('document_workspace') as module:return await asyncio.to_thread(module.work,value['id'],source_id)


@router.get('/api/work-queue')
async def get_work_queue(value=Depends(user)):
    try:
        activity = await asyncio.wait_for(operations.activity(), timeout=1.5)
    except TimeoutError:
        activity = {'phase': 'unknown'}
    snapshot = work_queue.QUEUE.snapshot(value, activity)
    snapshot['preparations_available'] = activity.get('phase') != 'unknown'
    return JSONResponse(snapshot, headers={'Cache-Control': 'no-store'})


class WorkMoveStep(BaseModel):
    direction:Literal[-1,1]


class WorkMoveDrop(BaseModel):
    target:str=Field(min_length=1,max_length=128)
    after:bool


@router.post('/api/work-queue/pause')
async def pause_work_queue(body:WorkPause,value=Depends(admin)):
    work_queue.QUEUE.set_paused(body.paused)
    if body.paused:
        with optional_feature('videos') as module:
            if module.running() is not None and not module.STOP.is_set():
                module.request_stop('queue_paused')
        await youtube_pipeline.pause_active_download()
    return {'paused':body.paused}


@router.post('/api/work-queue/{identifier}/move')
async def move_work(identifier:str,body:WorkMoveStep|WorkMoveDrop,value=Depends(user)):
    if isinstance(body,WorkMoveDrop):
        work_queue.QUEUE.move(identifier,None,value,target=body.target,after=body.after)
    else:
        work_queue.QUEUE.move(identifier,body.direction,value)
    return {'accepted':True}


@router.post('/api/work-queue/{identifier}/retry',status_code=202)
async def retry_work(identifier:str,value=Depends(user)):
    await work_queue.retry(identifier,value)
    return {'accepted':True}


class WorkPausePreparation(BaseModel):
    operation_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')


@router.post('/api/work-queue/{identifier}/pause',status_code=202)
async def pause_queued_preparation(identifier:str,body:WorkPausePreparation,value=Depends(admin)):
    await work_queue.pause(identifier,body.operation_id)
    return {'accepted':True}
