"""Routes du pilote — vidéos, sous-titres, transcriptions, acquisitions et téléchargements YouTube."""
import asyncio
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Request,Response,Query
from pydantic import BaseModel,Field
from starlette.responses import FileResponse,JSONResponse
from .. import youtube_pipeline
from .. import operations
from .deps import CaptionResume,admin,optional_feature,user
from .. import app as core  # VERSION est défini dans pilot/app.py

router=APIRouter()


@router.get('/api/videos')
async def get_videos(offset:int=Query(default=0,ge=0,le=1000000),limit:int=Query(default=30,ge=1,le=100),q:str=Query(default='',max_length=160),grouped:bool=False,group:str=Query(default='',max_length=1000),origin:Literal['all','local']='all',value=Depends(user)):
    with optional_feature('videos') as module:
        # The background watcher checks freshness independently of catalogue reads.
        return await asyncio.to_thread(module.listing,offset,limit,q,grouped,group,origin)


@router.get('/api/zim-videos')
async def get_zim_videos(value=Depends(user)):
    with optional_feature('archive_videos') as module:return await module.status()


@router.post('/api/admin/zim-videos/start',status_code=202)
async def start_zim_videos(value=Depends(admin)):
    with optional_feature('archive_videos') as module:return await module.start()


@router.post('/api/admin/zim-videos/pause',status_code=202)
async def pause_zim_videos(value=Depends(admin)):
    return await operations.library_command('video-inventory-pause',{})


@router.get('/api/admin/zim-videos/report')
async def report_zim_videos(value=Depends(admin)):
    with optional_feature('archive_videos') as module:return {'version':core.VERSION,**await module.status()}


class YoutubeList(BaseModel):
    text:str=Field(min_length=1,max_length=300_000)
    max_height:int=480


@router.post('/api/admin/youtube-downloads/check')
async def check_youtube_list(body:YoutubeList,value=Depends(admin)):
    with optional_feature('youtube_downloads') as module:return module.check(body.text)


@router.post('/api/admin/youtube-downloads',status_code=202)
async def start_youtube_downloads(body:YoutubeList,value=Depends(admin)):
    return await youtube_pipeline.submit(body.text,body.max_height)


@router.post('/api/admin/youtube-downloads/resume',status_code=202)
async def resume_youtube_downloads(value=Depends(admin)):
    with optional_feature('youtube_downloads') as module:
        state=await operations.library_command()
        identifier=state.get('youtube_list')
        if identifier:
            await youtube_pipeline.retry(identifier)
            return {'accepted':True}
        return await module.resume()


@router.post('/api/admin/youtube-downloads/pause',status_code=202)
async def pause_youtube_downloads(value=Depends(admin)):
    with optional_feature('youtube_downloads') as module:return await module.pause()


@router.get('/api/admin/youtube-downloads')
async def youtube_downloads(value=Depends(admin)):
    with optional_feature('youtube_downloads') as module:return JSONResponse(await module.status(),headers={'Cache-Control':'no-store'})


@router.post('/api/admin/videos/index',status_code=202)
async def index_videos(value=Depends(admin)):
    with optional_feature('videos') as module:return await module.start()


@router.post('/api/admin/videos/stop')
async def stop_videos(value=Depends(admin)):
    with optional_feature('videos') as module:return await module.stop()


@router.get('/api/admin/videos/report')
async def report_videos(value=Depends(admin)):
    with optional_feature('videos') as module:result={'version':core.VERSION,**await asyncio.to_thread(module.status)}
    try:
        with optional_feature('captions') as module:result['subtitle_preparations']=await asyncio.to_thread(module.listing,None)
    except HTTPException:result['subtitle_preparations_unavailable']=True
    try:
        with optional_feature('transcriptions') as module:result['transcriptions']=await asyncio.to_thread(module.listing,None)
    except HTTPException:result['transcriptions_unavailable']=True
    try:
        with optional_feature('caption_acquisition') as module:result['subtitle_acquisitions']=await asyncio.to_thread(module.listing,None)
    except HTTPException:result['subtitle_acquisitions_unavailable']=True
    return result


class CaptionRequest(BaseModel):
    id:str=Field(min_length=1,max_length=2000,pattern=r'^video:[a-f0-9]{64}$')
    track:int=Field(ge=0,le=999)
    mode:str=Field(default='rapide',max_length=50)


class TranscriptionRequest(BaseModel):
    id:str=Field(min_length=1,max_length=2000,pattern=r'^video:[a-f0-9]{64}$')
    language:str=Field(default='',max_length=3,pattern=r'^(?:[a-z]{2,3})?$')
    mode:str=Field(default='rapide',max_length=50)
    translate_french:bool=True


class AcquisitionRequest(BaseModel):
    id:str=Field(min_length=1,max_length=2000,pattern=r'^video:[a-f0-9]{64}$')
    reference:str=Field(default='',max_length=2000)
    language:str=Field(default='',max_length=40,pattern=r'^(?:[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)?$')
    origin:str=Field(default='',pattern=r'^(?:provided|automatic)?$')
    mode:str=Field(default='rapide',max_length=50)
    translate_french:bool=True


@router.get('/api/admin/video-acquisitions')
async def list_video_acquisitions(value=Depends(admin)):
    with optional_feature('caption_acquisition') as module:return {'jobs':await asyncio.to_thread(module.listing)}


@router.post('/api/admin/video-acquisitions',status_code=202)
async def create_video_acquisition(body:AcquisitionRequest,value=Depends(admin)):
    with optional_feature('caption_acquisition') as module:return await module.create(body.id,body.reference,body.language,body.origin,body.mode,body.translate_french)


@router.get('/api/admin/video-acquisitions/{identifier}/report')
async def report_video_acquisition(identifier:str,value=Depends(admin)):
    with optional_feature('caption_acquisition') as module:return {'version':core.VERSION,**await asyncio.to_thread(module.status,identifier,True)}


@router.post('/api/admin/video-acquisitions/{identifier}/pause')
async def pause_video_acquisition(identifier:str,value=Depends(admin)):
    with optional_feature('caption_acquisition') as module:return await module.pause(identifier)


@router.post('/api/admin/video-acquisitions/{identifier}/resume',status_code=202)
async def resume_video_acquisition(identifier:str,value=Depends(admin)):
    with optional_feature('caption_acquisition') as module:return await module.resume(identifier)


@router.get('/api/admin/video-transcriptions')
async def list_video_transcriptions(video_id:str|None=Query(default=None,pattern=r'^video:[a-f0-9]{64}$'),value=Depends(admin)):
    with optional_feature('transcriptions') as module:
        runtime=await asyncio.to_thread(module.model_config)
        return {'jobs':await asyncio.to_thread(module.listing,video_id=video_id),'available':runtime['available'],'message':runtime.get('message','')}


@router.post('/api/admin/video-transcriptions',status_code=202)
async def create_video_transcription(body:TranscriptionRequest,value=Depends(admin)):
    with optional_feature('transcriptions') as module:return await module.create(body.id,body.language,body.mode,body.translate_french)


@router.get('/api/admin/video-transcriptions/{identifier}/report')
async def report_video_transcription(identifier:str,value=Depends(admin)):
    with optional_feature('transcriptions') as module:return {'version':core.VERSION,**await asyncio.to_thread(module.status,identifier,True)}


@router.post('/api/admin/video-transcriptions/{identifier}/pause')
async def pause_video_transcription(identifier:str,value=Depends(admin)):
    with optional_feature('transcriptions') as module:return await module.pause(identifier)


@router.post('/api/admin/video-transcriptions/{identifier}/resume',status_code=202)
async def resume_video_transcription(identifier:str,value=Depends(admin)):
    with optional_feature('transcriptions') as module:return await module.resume(identifier)


@router.get('/api/admin/video-captions')
async def list_video_captions(video_id:str|None=Query(default=None,pattern=r'^video:[a-f0-9]{64}$'),value=Depends(admin)):
    with optional_feature('captions') as module:return {'jobs':await asyncio.to_thread(module.listing,video_id=video_id)}


@router.post('/api/admin/video-captions',status_code=202)
async def create_video_captions(body:CaptionRequest,value=Depends(admin)):
    with optional_feature('captions') as module:return await module.create(body.id,body.track,body.mode)


@router.get('/api/admin/video-captions/{identifier}/report')
async def report_video_captions(identifier:str,value=Depends(admin)):
    with optional_feature('captions') as module:return {'version':core.VERSION,**await asyncio.to_thread(module.status,identifier,full=True)}


@router.post('/api/admin/video-captions/{identifier}/pause')
async def pause_video_captions(identifier:str,value=Depends(admin)):
    with optional_feature('captions') as module:return await module.pause(identifier)


@router.post('/api/admin/video-captions/{identifier}/resume',status_code=202)
async def resume_video_captions(identifier:str,body:CaptionResume,value=Depends(admin)):
    with optional_feature('captions') as module:return await module.resume(identifier,body.mode)


@router.get('/api/videos/media')
async def video_media(request:Request,id:str=Query(pattern=r'^[a-f0-9]{64}$')):
    with optional_feature('videos') as module:
        _,payload,_=await asyncio.to_thread(module.row,'video:'+id)
        if payload.get('provider')=='zim':
            with optional_feature('archive_videos') as archives:return await archives.media_response(payload,request.headers.get('range'))
        path=await asyncio.to_thread(module.safe_file,payload['path'])
        types={'.mp4':'video/mp4','.m4v':'video/mp4','.webm':'video/webm','.ogv':'video/ogg','.mov':'video/quicktime','.mkv':'video/x-matroska','.avi':'video/x-msvideo'}
        return FileResponse(path,media_type=types.get(path.suffix.lower(),'application/octet-stream'),content_disposition_type='inline')


@router.get('/api/videos/track')
async def video_track(id:str=Query(pattern=r'^[a-f0-9]{64}$'),track:int=Query(ge=0,le=999)):
    with optional_feature('videos') as module:
        text=await asyncio.to_thread(module.webvtt,id,track)
        return Response(text,media_type='text/vtt',headers={'Cache-Control':'no-store'})
