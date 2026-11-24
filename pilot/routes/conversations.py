"""Routes du pilote — conversations, dossiers de conversation et questions à l’assistant."""
import asyncio
import time
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from .. import engine,library,operations,store,assistant_metrics
from .deps import SourceIdentifier,optional_feature,user

router=APIRouter()


class ConversationFolderName(BaseModel):
    name:str=Field(min_length=1,max_length=80)


class ConversationTitle(BaseModel):
    title:str=Field(min_length=1,max_length=80)


class ConversationFolderSelection(BaseModel):
    folder_id:str|None=Field(default=None,max_length=100)


@router.get('/api/conversation-folders')
async def conversation_folders(value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.folders,value['id'])


@router.post('/api/conversation-folders',status_code=201)
async def create_conversation_folder(body:ConversationFolderName,value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.save_folder,value['id'],body.name)


@router.patch('/api/conversation-folders/{identifier}')
async def rename_conversation_folder(identifier:str,body:ConversationFolderName,value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.save_folder,value['id'],body.name,identifier)


@router.delete('/api/conversation-folders/{identifier}')
async def delete_conversation_folder(identifier:str,value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.delete_folder,value['id'],identifier)


@router.patch('/api/conversations/{identifier}/title')
async def rename_conversation(identifier:str,body:ConversationTitle,value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.rename,value['id'],identifier,body.title)


@router.put('/api/conversations/{identifier}/folder')
async def move_conversation(identifier:str,body:ConversationFolderSelection,value=Depends(user)):
    with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.move,value['id'],identifier,body.folder_id)


@router.get('/api/conversations')
async def conversations(q:str=Query(default='',max_length=160),folder:str|None=Query(default=None,max_length=100),offset:int=Query(default=0,ge=0,le=100000),value=Depends(user)):
    # Legacy callers keep their original listing if the optional organizer fails.
    if q or folder is not None or offset:
        with optional_feature('conversation_organization') as module:return await asyncio.to_thread(module.listing,value['id'],q,folder,offset)
    with store.connect() as db:rows=db.execute('SELECT * FROM conversations WHERE user_id=? ORDER BY created DESC LIMIT 100',(value['id'],)).fetchall()
    return {'conversations':[dict(row) for row in rows]}


@router.get('/api/conversations/{identifier}')
async def conversation(identifier:str,value=Depends(user)):
    item=store.owned_conversation(identifier,value['id'])
    if not item:raise HTTPException(404,'Conversation introuvable.')
    with store.connect() as db:jobs=[dict(r) for r in db.execute("SELECT id,status,mode FROM jobs WHERE conversation_id=? AND status IN ('queued','running')",(identifier,))]
    with store.connect() as db:translated=[dict(r) for r in db.execute('SELECT id,title,source_id,status,created,mode FROM translations WHERE conversation_id=? ORDER BY created DESC',(identifier,))]
    with store.connect() as db:recent=[dict(r) for r in db.execute('SELECT id,mode,status,created FROM jobs WHERE conversation_id=? ORDER BY created DESC LIMIT 20',(identifier,))]
    measured=[r for r in recent if r['id'] in engine.MEASUREMENTS or assistant_metrics.path(r['id']).is_file()]
    return {**item,'messages':store.messages(identifier),'jobs':jobs,'source':store.conversation_source(identifier),'selected_sources':store.conversation_source_choices(identifier),'translations':[r['id'] for r in translated],'translation_items':translated,'measurement_jobs':measured,'summary_jobs':store.conversation_summaries(identifier)}


@router.delete('/api/conversations/{identifier}')
async def delete_conversation(identifier:str,value=Depends(user)):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():
            raise HTTPException(404,'Conversation introuvable.')
        if store.summary_active(db,identifier):raise HTTPException(409,'Mettez la synthèse longue en pause avant de supprimer cette conversation.')
        if db.execute("SELECT 1 FROM translations WHERE conversation_id=? AND status IN ('queued','running')",(identifier,)).fetchone():raise HTTPException(409,'Mettez la traduction en pause avant de supprimer cette conversation.')
        if db.execute("SELECT 1 FROM translations t JOIN settings s ON s.key='auto-translation:'||t.id WHERE t.conversation_id=? AND t.status='completed' AND EXISTS(SELECT 1 FROM translation_parts p WHERE p.translation_id=t.id AND p.status='done') AND NOT EXISTS(SELECT 1 FROM settings done WHERE done.key='published-translation:'||t.id)",(identifier,)).fetchone():
            raise HTTPException(409,'L’ajout d’une traduction terminée aux documents locaux reste à finaliser. Réessayez son ajout ou exportez-la avant de supprimer la conversation.')
        jobs=db.execute('SELECT id,status FROM jobs WHERE conversation_id=?',(identifier,)).fetchall()
        if any(job['status'] in ('queued','running') for job in jobs):
            raise HTTPException(409,'Une réponse est en cours. Attendez sa fin ou annulez-la avant de supprimer cette conversation.')
        db.execute('''DELETE FROM work_history WHERE id IN (
            SELECT id FROM jobs WHERE conversation_id=? UNION
            SELECT id FROM translations WHERE conversation_id=? UNION
            SELECT id FROM summary_jobs WHERE conversation_id=?
        )''',(identifier,identifier,identifier))
        db.execute('DELETE FROM jobs WHERE conversation_id=?',(identifier,))
        db.execute('DELETE FROM conversations WHERE id=? AND user_id=?',(identifier,value['id']))
    for job in jobs:
        (store.ROOT/'traces'/(job['id']+'.json')).unlink(missing_ok=True)
        assistant_metrics.path(job['id']).unlink(missing_ok=True)
    return {'ok':True}


class AssociatedSources(BaseModel):
    source_ids:list[SourceIdentifier]=Field(default_factory=list,max_length=12)


@router.post('/api/conversations',status_code=201)
async def new_document_conversation(body:AssociatedSources,value=Depends(user)):
    if not body.source_ids:raise HTTPException(400,'Choisissez au moins un document.')
    with optional_feature('associations') as module:
        choices,_=await module.resolve(body.source_ids)
        identifier=store.new_id()
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(identifier,value['id'],('Documents : '+choices[0]['title'])[:80],time.time()))
            if store.summary_active(db,identifier):raise HTTPException(409,'Mettez la synthèse longue en pause avant de modifier les documents.')
            module.save(db,identifier,choices)
    return {'conversation_id':identifier,'source':choices[0],'selected_sources':choices}


@router.put('/api/conversations/{identifier}/sources')
async def associate_sources(identifier:str,body:AssociatedSources,value=Depends(user)):
    if not store.owned_conversation(identifier,value['id']):raise HTTPException(404,'Conversation introuvable.')
    with optional_feature('associations') as module:
        choices,_=await module.resolve(body.source_ids,store.conversation_source_choices(identifier))
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
            if db.execute("SELECT 1 FROM jobs WHERE conversation_id=? AND status IN ('queued','running')",(identifier,)).fetchone():
                raise HTTPException(409,'Attendez la réponse en cours ou annulez-la avant de modifier les documents.')
            if store.summary_active(db,identifier):raise HTTPException(409,'Mettez la synthèse longue en pause avant de modifier les documents.')
            module.save(db,identifier,choices)
    return {'source':choices[0] if choices else None,'selected_sources':choices}


class Question(BaseModel):
    message:str=Field(min_length=1,max_length=6000)
    mode:str='rapide'
    domain:Literal['all','resilience','culture','other']=library.DEFAULT_SEARCH_DOMAIN
    conversation_id:str|None=Field(default=None,max_length=100)
    source_id:str|None=Field(default=None,max_length=2000)
    source_ids:list[SourceIdentifier]|None=Field(default=None,max_length=12)


@router.post('/api/questions')
async def question(body:Question,value=Depends(user)):
    request_started=time.monotonic();reading_ms=0
    if body.mode not in engine.MODES:raise HTTPException(400,'Mode inconnu.')
    state=await operations.status()
    if not state.get('online') or state.get('operation') or state.get('paused'):
        raise HTTPException(503,state['message']+'. La bibliothèque reste disponible. Consultez « État de l’appareil » pour le redémarrage.')
    conversation_id=body.conversation_id
    if conversation_id and not store.owned_conversation(conversation_id,value['id']):raise HTTPException(404,'Conversation introuvable.')
    attached=store.conversation_source_choices(conversation_id) if conversation_id else []
    if 'source_ids' in body.model_fields_set:
        if body.source_ids is None or 'source_id' in body.model_fields_set:raise HTTPException(400,'Utilisez une seule sélection de documents.')
        identifiers=body.source_ids
    elif 'source_id' in body.model_fields_set and not (body.source_id and len(attached)>1 and attached[0]['id']==body.source_id):
        identifiers=[body.source_id] if body.source_id else []
    else:identifiers=[item['id'] for item in attached]
    source=None;loaded={}
    if identifiers and ('source_ids' in body.model_fields_set or len(identifiers)>1):
        with optional_feature('associations') as module:
            started=time.monotonic();choices,loaded=await module.resolve(identifiers,attached);reading_ms=round((time.monotonic()-started)*1000)
    elif identifiers:
        started=time.monotonic();source=await library.source(identifiers[0]);reading_ms=round((time.monotonic()-started)*1000);choices=[source]
    else:choices=[]
    identifiers=[item['id'] for item in choices];source_id=identifiers[0] if identifiers else None
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if conversation_id and not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation_id,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
        if conversation_id and store.summary_active(db,conversation_id):raise HTTPException(409,'La synthèse longue est en cours. Mettez-la en pause avant de poser une autre question ici.')
        if conversation_id and db.execute("SELECT 1 FROM jobs WHERE conversation_id=? AND status IN ('queued','running')",(conversation_id,)).fetchone():
            raise HTTPException(409,'Une réponse est déjà en cours dans cette conversation. Attendez sa fin ou annulez-la.')
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=20:
            raise HTTPException(429,'La file d’attente est pleine. Réessayez après les demandes en cours.')
        if db.execute("SELECT count(*) FROM jobs WHERE user_id=? AND status IN ('queued','running')",(value['id'],)).fetchone()[0]>=2:
            raise HTTPException(429,'Vous avez déjà des questions en cours. Attendez ou annulez-en une.')
        if not conversation_id:
            conversation_id=store.new_id();db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation_id,value['id'],body.message[:80],time.time()))
        if not db.execute('SELECT 1 FROM messages WHERE conversation_id=?',(conversation_id,)).fetchone():
            db.execute("UPDATE conversations SET title=? WHERE id=? AND NOT EXISTS(SELECT 1 FROM settings WHERE key='conversation-title:'||?)",(body.message[:80],conversation_id,conversation_id))
        try:store.set_conversation_source_choices(db,conversation_id,choices)
        except store.AssociationUnavailable as error:raise HTTPException(503,str(error)) from None
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation_id,'user',body.message,time.time()))
        identifier=store.new_id();now=time.time()
        db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(identifier,value['id'],conversation_id,body.mode,'queued',now,now))
    engine.PENDING[identifier]={'started':request_started,'preparation_ms':max(0,round((time.monotonic()-request_started)*1000)-reading_ms),'reading_ms':reading_ms,'source':source,'sources':loaded}
    engine.launch(identifier,value['id'],conversation_id,body.mode,source_id,domain=body.domain,**({'source_ids':identifiers} if len(identifiers)>1 else {}))
    return {'id':identifier,'conversation_id':conversation_id}


class AssociatedSource(BaseModel):
    source_id:str|None=Field(default=None,max_length=2000)


@router.put('/api/conversations/{identifier}/source')
async def associate_source(identifier:str,body:AssociatedSource,value=Depends(user)):
    if not store.owned_conversation(identifier,value['id']):raise HTTPException(404,'Conversation introuvable.')
    source=await library.source(body.source_id) if body.source_id else None
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone():raise HTTPException(404,'Conversation introuvable.')
        if db.execute("SELECT 1 FROM jobs WHERE conversation_id=? AND status IN ('queued','running')",(identifier,)).fetchone():
            raise HTTPException(409,'Attendez la réponse en cours ou annulez-la avant de modifier les documents.')
        if store.summary_active(db,identifier):raise HTTPException(409,'Mettez la synthèse longue en pause avant de modifier les documents.')
        store.set_conversation_source(db,identifier,source)
    return {'source':store.conversation_source(identifier)}
