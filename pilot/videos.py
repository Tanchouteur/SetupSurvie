"""Local media and caption index. No network, decoder, model or original writes."""
import asyncio
from contextlib import contextmanager
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time

from fastapi import HTTPException
from . import durable,retrieval,store,video_inventory as inventory

ROOT=Path(os.environ.get('VIDEO_DIR','/videos'))
ACTIVE=None
STOP=threading.Event()
LOCK=threading.Lock()
NOTICE='Sous-titres locaux : langue, sens et synchronisation non vérifiés. Le texte ne prouve pas que les gestes montrés ont été compris.'


@contextmanager
def connect():
    durable.mkdir(store.ROOT)
    path=store.ROOT/'videos.db';db=sqlite3.connect(path,timeout=10);db.row_factory=sqlite3.Row
    path.chmod(0o600)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.executescript('''CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY,path TEXT NOT NULL,revision TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS video_text USING fts5(id UNINDEXED,title,language UNINDEXED,track UNINDEXED,start_ms UNINDEXED,end_ms UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');''')
    try:
        with db:yield db
    finally:db.close()


def safe_file(relative):
    if not isinstance(relative,str) or not relative or '\\' in relative or any(p in ('','.','..') for p in relative.split('/')):
        raise HTTPException(400,'Chemin vidéo invalide.')
    path=ROOT/relative
    try:
        if any(inventory.is_link(p) for p in [ROOT,*[ROOT.joinpath(*Path(relative).parts[:n]) for n in range(1,len(Path(relative).parts)+1)]]):raise ValueError()
        if not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():raise ValueError()
        return path
    except (OSError,ValueError):raise HTTPException(404,'Ce fichier vidéo local n’est plus disponible.') from None


def identity(value):
    match=re.fullmatch(r'video:([a-f0-9]{64})(?:#t=(\d{1,10})(?:&track=\d{1,3})?)?',value)
    if not match:raise HTTPException(400,'Référence vidéo invalide.')
    return match[1],int(match[2] or 0)


def stat_revision(payload):
    entries=[payload['path'],payload['metadata']['path'],*[track['path'] for track in payload['tracks']]]
    values=[]
    for relative in entries:
        try:
            path=safe_file(relative);info=path.stat();values.append([relative,info.st_size,info.st_mtime_ns])
        except HTTPException:
            if relative==payload['metadata']['path'] and payload['metadata']['status']=='missing':values.append([relative,None]);continue
            return None
    return hashlib.sha256(json.dumps(values,ensure_ascii=False).encode()).hexdigest()


def row(identifier):
    key,position=identity(identifier)
    with connect() as db:value=db.execute('SELECT * FROM media WHERE id=?',(key,)).fetchone()
    if not value:raise HTTPException(404,'Vidéo introuvable. Actualisez l’index des vidéos depuis Collections.')
    payload=json.loads(value['payload'])
    if stat_revision(payload)!=value['revision']:raise HTTPException(409,'La vidéo ou ses sous-titres ont changé. Actualisez les vidéos avant de rouvrir ce résultat.')
    return dict(value),payload,position


def revision(identifier):
    try:return row(identifier)[0]['revision']
    except HTTPException:return None


def public(payload,revision):
    key=payload['inventory_id'];media=payload['media'];source=payload['source']
    declared=source.get('upload_date_declared') or ''
    date=declared[:4]+'-'+declared[4:6]+'-'+declared[6:] if re.fullmatch(r'\d{8}',declared) else ''
    return {'id':'video:'+key,'kind':'video','title':payload['title'][:400],'collection':source.get('channel') or payload['collection'],
        'language':media.get('language_declared') or '', 'duration_seconds':media.get('duration_seconds_declared'),
        'subtitle_status':payload['subtitle_status'],'video_revision':revision,'document_date':date,'edition':'',
        'collected_at':'','archive_date':'','provenance':source.get('channel') or 'Fichier vidéo local','licence':'Droits d’usage à vérifier.',
        'url':'/api/videos/media?id='+key,'images':[],'tracks':[
            {'id':index,'language':track['language_declared'] or '', 'origin':track['origin'],'status':track['technical_status'],
             'warnings':track['warnings'],'errors':track['errors'][:10],'url':'/api/videos/track?id='+key+'&track='+str(index)}
            for index,track in enumerate(payload['tracks'])],
        'video_notice':NOTICE,'audio_verified':False,'human_review':'not_performed'}


def source(identifier):
    stored,payload,position=row(identifier);result=public(payload,stored['revision']);result['id']=identifier
    key,_=identity(identifier)
    with connect() as db:
        # Favor a declared French track, then the source language. Never combine
        # translations into one alleged original transcript.
        candidates=[(i,t) for i,t in enumerate(payload['tracks']) if t['technical_status']=='passed']
        candidates.sort(key=lambda pair:(not (pair[1]['language_declared'] or '').startswith('fr'),pair[0]))
        requested=re.search(r'&track=(\d+)$',identifier)
        if requested:candidates=[pair for pair in candidates if pair[0]==int(requested[1])]
        if candidates:
            track=candidates[0][0]
            cues=db.execute('SELECT start_ms,end_ms,text,language FROM video_text WHERE id=? AND track=? AND end_ms>? ORDER BY CAST(start_ms AS INTEGER) LIMIT 80',(key,str(track),position)).fetchall()
        else:cues=[]
    text='\n'.join(f'[{int(c["start_ms"])//60000:02d}:{(int(c["start_ms"])//1000)%60:02d}] {c["text"]}' for c in cues)
    result.update(text=text[:100000],position_ms=position,text_truncated=bool(len(text)>100000 or cues and len(cues)>=80),preview=True,
                  transcription_available=bool(cues),language=cues[0]['language'] if cues else result['language'])
    if not text:result['text']=''
    return result


def search(plan,language='',limit=40):
    if not plan.words:return [],{'status':'not_run'}
    if not ROOT.is_dir():return [],{'status':'not_available'}
    if status()['phase']=='not_started':return [],{'status':'not_indexed'}
    with connect() as db:
        rows=db.execute("SELECT id,title,language,track,start_ms,end_ms,snippet(video_text,6,'','', '…',45) AS excerpt,text AS _text FROM video_text WHERE video_text MATCH ? AND (?='' OR language=? OR substr(language,1,2)=?) ORDER BY bm25(video_text) LIMIT ?",
                        (plan.fts(relaxed=True),language,language,language[:2],limit)).fetchall()
        result=[];stale=0
        for candidate in rows:
            try:stored,payload,_=row('video:'+candidate['id'])
            except HTTPException:stale+=1;continue
            data=public(payload,stored['revision']);start=int(candidate['start_ms'])
            data.update(id='video:'+candidate['id']+('#t='+str(start)+'&track='+candidate['track'] if candidate['track']!='metadata' else ''),
                        language=candidate['language'],excerpt=candidate['excerpt'],_text=candidate['_text'],
                        match='subtitle' if candidate['track']!='metadata' else 'title',position_ms=start,
                        transcription_origin=payload['tracks'][int(candidate['track'])]['origin'] if candidate['track']!='metadata' else 'metadata_only')
            if plan.collection and plan.collection not in retrieval.normal(data['collection']).replace(' ',''):continue
            result.append(data)
    return result,{'status':'partial' if stale else 'complete','stale_results':stale,'results':len(result),'scope':'indexed_local_titles_and_sidecars'}


def status():
    try:
        value=json.loads((store.ROOT/'videos-report.json').read_text())
        if value.get('phase')=='running' and (ACTIVE is None or ACTIVE.done()):value['phase']='interrupted'
        return value
    except (OSError,ValueError):return {'schema':1,'phase':'not_started','videos':0,'tracks':0,'errors':[]}


def listing(offset=0,limit=30,query=''):
    words=retrieval.normal(query).split()[:10]
    restriction=' WHERE id IN (SELECT id FROM video_text WHERE video_text MATCH ? AND track=\'metadata\')' if words else ''
    parameters=[' AND '.join('"'+word+'"' for word in words)] if words else []
    with connect() as db:
        total=db.execute('SELECT count(*) FROM media'+restriction,parameters).fetchone()[0]
        records=db.execute('SELECT * FROM media'+restriction+' ORDER BY id LIMIT ? OFFSET ?',(*parameters,limit,offset)).fetchall()
    items=[]
    for record in records:
        payload=json.loads(record['payload']);item=public(payload,record['revision'])
        item['available']=stat_revision(payload)==record['revision'];items.append(item)
    return {'status':status(),'total':total,'offset':offset,'videos':items}


def scan():
    with LOCK:
        report={'schema':1,'phase':'running','started':time.time(),'videos':0,'tracks':0,'errors':[]}
        last_saved=time.monotonic()
        def save():durable.write_bytes(store.ROOT/'videos-report.json',json.dumps(report,ensure_ascii=False).encode(),private=True)
        save()
        try:
            if not ROOT.is_dir() or inventory.is_link(ROOT):raise ValueError('video_directory_unavailable')
            found=inventory.inventory(ROOT,cancelled=STOP.is_set)
            with connect() as db:
                db.execute('DELETE FROM media');db.execute('DELETE FROM video_text')
                for item in found['videos']:
                    if STOP.is_set():raise InterruptedError()
                    key=item['inventory_id'];version=stat_revision(item)
                    if not version:report['errors'].append({'id':key,'reason':'source_changed'});continue
                    db.execute('INSERT INTO media VALUES(?,?,?,?)',(key,item['path'],version,json.dumps(item,ensure_ascii=False)))
                    language=item['media']['language_declared'] or ''
                    db.execute('INSERT INTO video_text VALUES(?,?,?,?,?,?,?)',(key,item['title'],language,'metadata',0,0,(item['description'] or '')[:100000]))
                    for index,track in enumerate(item['tracks']):
                        if track['technical_status']!='passed':continue
                        parsed=inventory.inspect_subtitle(safe_file(track['path']),item['media']['duration_seconds_declared'],include_cues=True)
                        if parsed['technical_status']!='passed' or parsed['revision']!=track['revision']:raise ValueError('subtitle_changed')
                        for cue in parsed['cues']:
                            db.execute('INSERT INTO video_text VALUES(?,?,?,?,?,?,?)',(key,item['title'],track['language_declared'] or '',str(index),cue['start_ms'],cue['end_ms'],cue['text']))
                        report['tracks']+=1
                    report['videos']+=1
                    if time.monotonic()-last_saved>2:
                        save();last_saved=time.monotonic()
                if STOP.is_set():raise InterruptedError()
            report.update(phase='completed',skipped=found['skipped'],inventory_errors=found['errors'],unexamined=found['unexamined'],limitations=found['limitations'],
                          per_video=[{'id':'video:'+item['inventory_id'],'path':item['path'],'title':item['title'],'subtitle_status':item['subtitle_status'],
                                      'media':item['media'],'source':{key:item['source'].get(key) for key in ('id','extractor','channel','upload_date_declared')},
                                      'revision':stat_revision(item),'same_source_paths':item['same_source_paths'],
                                      'tracks':[{key:track[key] for key in ('language_declared','origin','technical_status','errors','warnings')} for track in item['tracks']],
                                      'validation':item['validation'],'next_action':item['next_action']} for item in found['videos']])
        except InterruptedError:report['phase']='paused'
        except Exception:report.update(phase='failed',error='L’inventaire n’a pas abouti ; l’ancien index reste conservé.')
        report['finished']=time.time();save()
        return report


async def start():
    global ACTIVE
    if ACTIVE is not None and not ACTIVE.done():raise HTTPException(409,'Un inventaire vidéo est déjà en cours.')
    STOP.clear()
    # Publish running before handing work to a thread: a fast poll must not
    # mistake the preceding completed report for the newly requested inventory.
    durable.write_bytes(store.ROOT/'videos-report.json',json.dumps({'schema':1,'phase':'running','started':time.time(),'videos':0,'tracks':0,'errors':[]}).encode(),private=True)
    ACTIVE=asyncio.create_task(asyncio.to_thread(scan));return {'accepted':True}


async def stop():
    STOP.set()
    if ACTIVE is not None:await asyncio.shield(ACTIVE)
    return status()


def webvtt(key,index):
    stored,payload,_=row('video:'+key)
    if not 0<=index<len(payload['tracks']):raise HTTPException(404,'Piste introuvable.')
    track=payload['tracks'][index]
    if track['technical_status']!='passed':raise HTTPException(422,'Cette piste ne passe pas les contrôles techniques. Consultez son rapport.')
    parsed=inventory.inspect_subtitle(safe_file(track['path']),payload['media']['duration_seconds_declared'],include_cues=True)
    if parsed['technical_status']!='passed' or parsed['revision']!=track['revision']:raise HTTPException(409,'Cette piste a changé ; actualisez les vidéos.')
    def stamp(ms):return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'
    return 'WEBVTT\n\n'+'\n\n'.join(stamp(c['start_ms'])+' --> '+stamp(c['end_ms'])+'\n'+html.escape(c['text'],quote=False) for c in parsed['cues'])+'\n'
