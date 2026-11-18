"""Site side of YouTube list downloads; the host controller does the work.

The pilot cannot write library/video (read-only mount) and the controller
accepts only small commands: the list is saved in the pilot state folder,
shared with the host, and only its identifier is sent.
"""
import time
import uuid

from fastapi import HTTPException

from . import durable,operations,store
from .youtube_list import REASONS,parse_list

MAX_TEXT=300_000
KEEP_LISTS=20
ACTIVE=('starting','planning','downloading','refreshing')
REFRESHED=None


def folder():return store.ROOT/'youtube-lists'


def check(text):
    entries,errors=parse_list(text)
    return {'videos':[{'line':item['line'],'id':item['id'],'theme':item['theme']} for item in entries],
            'refused':[{'line':item['line'],'text':item['text'][:200],'reason':item['reason'],'message':REASONS[item['reason']]} for item in errors]}


def save(text, *, prune=True):
    """Keep the list for the host; older lists are pruned (the host copies its own)."""
    directory=folder();durable.mkdir(directory)
    identifier=uuid.uuid4().hex
    # The pilot may run as root in its container while the host controller runs
    # as the installing user: the list holds public addresses and must stay readable.
    durable.write_bytes(directory/(identifier+'.txt'),text.encode('utf-8'),private=False)
    if prune:
        for old in sorted(directory.glob('*.txt'),key=lambda path:path.stat().st_mtime)[:-KEEP_LISTS]:old.unlink(missing_ok=True)
    return identifier


async def start(text,max_height):
    if len(text.encode('utf-8'))>MAX_TEXT:raise HTTPException(413,'Liste trop longue : la diviser en plusieurs fichiers.')
    summary=check(text)
    if not summary['videos']:raise HTTPException(400,'Aucune adresse de vidéo YouTube valide dans cette liste.')
    if max_height not in (360,480,720):raise HTTPException(400,'Qualité non valide.')
    await operations.library_command('youtube-download',{'list':save(text),'max_height':max_height})
    return {'accepted':True,**summary}


async def resume():
    await operations.library_command('youtube-download',{'resume':True})
    return {'accepted':True}


async def pause():
    state=await operations.library_command()
    if state.get('action')!='youtube-download' or state.get('phase') not in ACTIVE:raise HTTPException(409,'Aucun téléchargement YouTube en cours.')
    await operations.library_command('pause',{})
    return {'accepted':True}


async def refresh_inventory(job):
    """Once per finished job, without waiting for the periodic file check."""
    global REFRESHED
    if not job or job==REFRESHED:return
    REFRESHED=job
    from . import videos
    await videos.ensure_fresh(force=True)


async def status():
    try:state=await operations.library_command()
    except HTTPException as error:
        return {'available':False,'phase':'unknown','message':error.detail,'observed_at':time.time()}
    if state.get('action')!='youtube-download':
        busy=state.get('phase') in ACTIVE
        return {'available':True,'phase':'busy' if busy else 'idle','message':'Une autre préparation de la bibliothèque est en cours ; le téléchargement pourra commencer ensuite.' if busy else '',
                'observed_at':time.time()}
    progress=state.get('youtube') or {}
    if state.get('phase')=='completed':await refresh_inventory(state.get('id'))
    return {'available':True,'phase':state.get('phase'),'message':state.get('message',''),'pause_requested':bool(state.get('pause_requested')),
            'options':state.get('options',{}),'progress':{key:progress[key] for key in ('total','videos','done','current','counts','tools','items','remaining') if key in progress},
            'resumable':state.get('phase') in ('paused','interrupted','error'),'observed_at':time.time()}
