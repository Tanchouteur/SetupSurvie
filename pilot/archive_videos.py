"""Read prepared archive-video records without libzim or Internet."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import quote

from fastapi import HTTPException
import anyio
import httpx
from starlette.responses import StreamingResponse
from . import store,video_inventory,zim_video_inventory

ZIMS=Path(os.environ.get('ZIM_DIR','/zim'))
ACTIVE={}


def directory():return store.ROOT/'zim-videos'


def track_file(track):
    key=track.get('archive_cache')
    if not isinstance(key,str) or not re.fullmatch(r'[a-f0-9]{64}',key):raise HTTPException(400,'Référence de piste d’archive invalide.')
    path=directory()/'tracks'/(key+'.vtt')
    try:
        if any(video_inventory.is_link(parent) for parent in (store.ROOT,directory(),path.parent,path)):raise ValueError()
        video_inventory.regular(path)
        return path
    except (OSError,ValueError):raise HTTPException(404,'Cette piste préparée n’est plus disponible. Reprenez l’inventaire des vidéos des collections.') from None


def original_revision(payload):
    name=payload.get('archive','')
    if Path(name).name!=name or not name.endswith('.zim'):return None
    try:
        if video_inventory.is_link(ZIMS):return None
        info=video_inventory.regular(ZIMS/name);expected=payload['archive_revision']
        if info.st_size!=expected['bytes'] or info.st_mtime_ns!=expected['mtime_ns']:return None
        return hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
    except (OSError,ValueError,KeyError):return None


def items(errors=None):
    root=directory()
    if not root.is_dir() or video_inventory.is_link(root):return
    for path in sorted(root.glob('*.sqlite')):
        if not re.fullmatch('[a-f0-9]{24}\\.sqlite',path.name) or video_inventory.is_link(path):continue
        try:
            with zim_video_inventory.connect(path,True) as db:
                for row in db.execute('SELECT payload FROM video_items ORDER BY id'):
                    value=json.loads(row[0])
                    if original_revision(value):
                        for track in value['tracks']:
                            if track.get('archive_cache') and track['technical_status']=='passed':
                                try:
                                    checked=video_inventory.inspect_subtitle(track_file(track))
                                    if checked['technical_status']!='passed' or checked.get('text_utf8_sha256')!=track.get('text_utf8_sha256'):raise ValueError()
                                    track.update(revision=checked['revision'])
                                except (ValueError,HTTPException):
                                    track.update(technical_status='invalid',errors=['cache_piste_absent_ou_modifie'])
                                    if errors is not None:errors.append({'id':value['inventory_id'],'reason':'archive_track_cache_unavailable'})
                        usable=[track for track in value['tracks'] if track['technical_status']=='passed']
                        value['subtitle_status']='french_available' if any((t['language_declared'] or '').lower().startswith('fr') for t in usable) else 'source_only' if usable else 'invalid' if value['tracks'] else 'missing'
                        yield value
                    elif errors is not None:errors.append({'id':value.get('inventory_id',''),'reason':'archive_video_source_changed'})
        except (OSError,ValueError,zim_video_inventory.sqlite3.Error):
            if errors is not None:errors.append({'id':path.name,'reason':'archive_video_inventory_unreadable'})


def progress():
    path=directory()/'progress.json'
    try:
        if any(video_inventory.is_link(parent) for parent in (store.ROOT,directory(),path)) or video_inventory.regular(path).st_size>2_000_000:raise ValueError()
        value=json.loads(path.read_text())
        if not isinstance(value,dict) or value.get('schema')!=1:raise ValueError()
        return value
    except (OSError,ValueError):return {'schema':1,'phase':'not_started','archives':0,'completed':0,'results':[],'unexamined':[]}


def state():
    from . import videos
    value=progress();reader=videos.status()
    return {**value,'reader_ready':bool(value['phase'] in ('completed','partial') and value.get('job_id') and value['job_id']==reader.get('archive_inventory_job') and value.get('finished')==reader.get('archive_inventory_finished') and reader['phase']=='completed'),
        'reader_updating':value['phase'] in ('completed','partial') and (reader['phase']=='running' or any(not task.done() for task in ACTIVE.values())),'reader_status':reader['phase']}


async def status():
    """Distinguish a queued or failed host worker from the preceding inventory."""
    from . import operations
    value=await asyncio.to_thread(state)
    try:host=await operations.library_command()
    except HTTPException:return {**value,'control_notice':'Le suivi du PC serveur ne répond pas. Les inventaires déjà terminés restent disponibles.'}
    if host.get('action')!='video-inventory':return value
    value['host_job']={key:host[key] for key in ('id','phase') if key in host}
    same=host.get('id')==value.get('job_id')
    if same and value['phase'] in ('completed','partial'):return value
    phase=host.get('phase')
    if not same and phase in ('starting','downloading','running'):
        return {**value,'phase':'preparing','reader_ready':False,'reader_updating':False}
    if phase in ('error','interrupted','paused'):
        return {**value,'phase':'paused' if phase=='paused' else 'error','reader_ready':False,'reader_updating':False,
            'control_notice':'L’examen est en pause ou s’est interrompu. Vérifiez l’outil et l’espace libre, puis reprenez ; les anciens inventaires sont conservés.'}
    return value


def coverage():
    if not ZIMS.is_dir():return {'status':'not_available','archives':0,'examined':0}
    files=[path for path in ZIMS.glob('*.zim') if path.is_file() and not path.is_symlink()]
    if not files:return {'status':'not_available','archives':0,'examined':0}
    value=progress();ready={row['archive']:row for row in value.get('results',[]) if row.get('status') in ('completed','reused','partial')}
    examined=0
    for path in files:
        saved=ready.get(path.name,{}).get('revision',{})
        try:info=video_inventory.regular(path)
        except (OSError,ValueError):continue
        if info.st_size==saved.get('bytes') and info.st_mtime_ns==saved.get('mtime_ns'):examined+=1
    return {'status':'not_indexed' if value['phase']=='not_started' else 'complete' if value['phase']=='completed' and examined==len(files) else 'partial',
        'archives':len(files),'examined':examined,'scope':'explicit_html_media_and_checked_tracks'}


async def follow(job):
    from . import operations,videos
    observed=False
    try:
        for _ in range(21600):
            value=await asyncio.to_thread(progress)
            if value.get('job_id')==job:
                observed=True
                if value['phase'] in ('completed','partial'):
                    try:await videos.start()
                    except HTTPException:
                        if videos.ACTIVE:await asyncio.shield(videos.ACTIVE)
                        await videos.start()
                    if videos.ACTIVE:await asyncio.shield(videos.ACTIVE)
                    return
                if value['phase']=='paused':return
            elif observed:return
            try:
                host=await operations.library_command()
                if host.get('id')!=job or host.get('phase') in ('error','interrupted','paused'):return
            except HTTPException:pass
            await asyncio.sleep(5)
    except asyncio.CancelledError:raise
    except Exception:return  # Completed inventories remain available for explicit refresh.


async def start():
    from . import operations
    await operations.library_command('video-inventory',{})
    control=await operations.library_command();job=control.get('id')
    if job and job not in ACTIVE:
        task=asyncio.create_task(follow(job));ACTIVE[job]=task
        def done(task):
            if ACTIVE.get(job) is task:ACTIVE.pop(job,None)
        task.add_done_callback(done)
    return {'accepted':True,'job_id':job}


async def stop_all():
    tasks=list(ACTIVE.values())
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)


def audio_source(payload):
    """Build a private worker descriptor only from the configured local reader."""
    from . import archive_media,library
    if not original_revision(payload):raise HTTPException(409,'Cette archive a changé. Actualisez son inventaire vidéo avant la reconnaissance.')
    try:
        value={'endpoint':library.KIWIX,'book':payload['book'],'path':payload['path'],'size':payload['media']['size_bytes'],'uuid':payload['archive_revision']['uuid']}
        archive_media.urls(value)
        if len(json.dumps(value))>12000:raise ValueError()
        return value
    except (KeyError,ValueError):raise HTTPException(409,'La référence audio de cette vidéo doit être actualisée. Reprenez l’examen des collections.') from None


async def media_response(payload,range_header=None):
    from . import library
    path=payload['path'];book=payload['book']
    if not original_revision(payload):raise HTTPException(409,'Cette archive a changé. Actualisez son inventaire vidéo.')
    if not isinstance(path,str) or path.startswith('/') or '\\' in path or any(p in ('','.','..') for p in path.split('/')) or any(ord(c)<32 for c in path):raise HTTPException(400,'Chemin de média d’archive invalide.')
    if '/' in book or '\\' in book or book in ('','.','..'):raise HTTPException(400,'Référence de collection invalide.')
    if range_header and (len(range_header)>100 or not re.fullmatch(r'bytes=(?:\d+-\d*|-\d+)',range_header)):raise HTTPException(416,'Une seule plage vidéo est acceptée.')
    size=payload['media']['size_bytes'];requested=None
    if range_header:
        first,last=range_header[6:].split('-')
        start=int(first) if first else max(0,size-int(last));end=min(size-1,int(last)) if first and last else size-1
        if start>end or start>=size:raise HTTPException(416,'Cette plage dépasse la vidéo.',headers={'Content-Range':f'bytes */{size}'})
        requested=(start,end)
    client=httpx.AsyncClient(trust_env=False,timeout=httpx.Timeout(60,connect=5),follow_redirects=False)
    response=None
    try:
        request=client.build_request('GET',library.KIWIX+'/content/'+quote(book,safe='')+'/'+quote(path,safe='/'),headers={'Accept-Encoding':'identity',**({'Range':range_header} if range_header else {})})
        response=await client.send(request,stream=True)
        if response.status_code not in (200,206):
            code=response.status_code;await response.aclose();raise HTTPException(416 if code==416 else 503,'Le média ne répond pas dans cette collection. Ouvrez l’article d’origine ou réessayez le lecteur local.')
        if not original_revision(payload):await response.aclose();raise HTTPException(409,'L’archive a changé pendant l’ouverture de la vidéo.')
        expected=size
        if response.status_code==206:
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
            if not match or int(match[3])!=size or requested!=(int(match[1]),int(match[2])):raise ValueError()
            expected=int(match[2])-int(match[1])+1
        if response.headers.get('Content-Encoding','identity')!='identity' or int(response.headers.get('Content-Length',expected))!=expected:raise ValueError()
        mime=response.headers.get('Content-Type','').split(';')[0]
        if mime and not mime.startswith('video/') and mime!='application/octet-stream':raise ValueError()
    except HTTPException:
        if response is not None:await response.aclose()
        await client.aclose();raise
    except ValueError:
        if response is not None:await response.aclose()
        await client.aclose();raise HTTPException(503,'Le lecteur local a renvoyé un média différent de l’inventaire. Actualisez les collections avant de réessayer.') from None
    except httpx.HTTPError:
        await client.aclose();raise HTTPException(503,'Le lecteur local des collections ne répond pas. Les pistes déjà préparées restent consultables.') from None
    except BaseException:
        with anyio.CancelScope(shield=True):
            if response is not None:await response.aclose()
            await client.aclose()
        raise
    headers={key:response.headers[key] for key in ('Content-Range','Accept-Ranges') if key in response.headers}
    headers['Content-Length']=str(expected)
    headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    async def stream():
        checked=time.monotonic();remaining=expected
        try:
            async for chunk in response.aiter_raw(65536):
                if time.monotonic()-checked>1:
                    if not original_revision(payload):break
                    checked=time.monotonic()
                if len(chunk)>remaining:raise httpx.RemoteProtocolError('Le média dépasse la taille préparée.')
                remaining-=len(chunk);yield chunk
            if remaining:raise httpx.RemoteProtocolError('La lecture du média a été interrompue.')
        finally:await response.aclose();await client.aclose()
    class MediaStream(StreamingResponse):
        async def __call__(self,scope,receive,send):
            try:await super().__call__(scope,receive,send)
            finally:
                # Also close when the client leaves before iteration begins.
                with anyio.CancelScope(shield=True):
                    await response.aclose();await client.aclose()
    return MediaStream(stream(),status_code=response.status_code,media_type=payload['media']['mimetype'],headers=headers)
