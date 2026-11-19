"""Real tiny ZIM and WebM, simulated host controller/Kiwix HTTP, never inference."""
import asyncio
import json
import shutil
import time
import uuid
from fastapi import Request,Response,HTTPException
from pilot import archive_videos,captions,durable,library,operations,videos,zim_video_inventory
from zim_video_fixture import create


def install(app,root,base):
    archives=root/'video-zim';archives.mkdir();archive_videos.ZIMS=archives
    original_command=operations.library_command;original_reader=library.KIWIX
    enabled=False;gate=None;task=None;hold=True;job='archive-video-browser-fixture';source=archives/'video-fixture.zim';cancel=root/'archive-video-cancel'
    def save(value):durable.write_bytes(archive_videos.directory()/'progress.json',json.dumps(value).encode(),private=True)
    async def worker():
        if gate:await gate.wait()
        value={'schema':1,'job_id':job,'phase':'running','archives':1,'completed':0,'results':[]}
        try:
            result=await asyncio.to_thread(zim_video_inventory.build,source,archive_videos.directory(),cancel=cancel,reserve=1_000_000)
            value.update(phase='completed',completed=1,results=[result],finished=time.time())
        except zim_video_inventory.Paused:value['phase']='paused'
        save(value)
    async def command(action=None,payload=None):
        nonlocal task,gate,job
        if not enabled:return await original_command(action,payload)
        if action is None:return {'id':job,'action':'video-inventory','phase':archive_videos.progress()['phase']}
        if action=='video-inventory':
            if task and not task.done():raise HTTPException(409,'Examen déjà en cours dans la fixture.')
            job=uuid.uuid4().hex;cancel.unlink(missing_ok=True);gate=asyncio.Event() if hold else None
            save({'schema':1,'job_id':job,'phase':'running','archives':1,'completed':0,'results':[]})
            task=asyncio.create_task(worker());return {'accepted':True}
        if action=='video-inventory-pause':
            cancel.touch()
            if gate:gate.set()
            if task:await task
            return {'accepted':True}
        return await original_command(action,payload)
    operations.library_command=command

    @app.post('/fixture/archive-videos')
    async def prepare(active:bool=True,wait:bool=True,without_tracks:bool=False):
        nonlocal enabled,hold,task,gate
        await archive_videos.stop_all();await captions.stop_all();await videos.stop()
        if task and not task.done():
            cancel.touch()
            if gate:gate.set()
            await task
        shutil.rmtree(archive_videos.directory(),ignore_errors=True);source.unlink(missing_ok=True)
        enabled=active;hold=wait
        if active:
            create(source,media=(base/'tests/fixtures/video/solid-green.webm').read_bytes(),
                   with_tracks=not without_tracks,extra=True)
            library.KIWIX='http://127.0.0.1:8769/fixture/archive-reader'
        else:library.KIWIX=original_reader
        videos.STOP.clear();await asyncio.to_thread(videos.scan)
        return {'ready':active,'native_archive':True,'simulated_host':True,'simulated_reader_http':True}

    @app.post('/fixture/archive-videos-release')
    async def release():
        if gate:gate.set()
        return {'released':True}

    @app.get('/fixture/archive-reader/content/{book}/{path:path}')
    def media(book:str,path:str,request:Request):
        from libzim.reader import Archive
        if not enabled or book!='video-fixture' or path!='media/clip.webm':raise HTTPException(404)
        data=bytes(Archive(source).get_entry_by_path(path).get_item().content);start=0;end=len(data)-1;status=200
        requested=request.headers.get('Range')
        if requested:
            import re
            match=re.fullmatch(r'bytes=(\d+)-(\d*)',requested)
            if not match:raise HTTPException(416)
            start=int(match[1]);end=min(end,int(match[2])) if match[2] else end
            if start>end:raise HTTPException(416)
            status=206
        headers={'Accept-Ranges':'bytes'}
        if status==206:headers['Content-Range']=f'bytes {start}-{end}/{len(data)}'
        return Response(data[start:end+1],status_code=status,headers=headers,media_type='video/webm')
