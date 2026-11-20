"""Routes du pilote — résumés, traductions, termes de traduction et suivi des tâches."""
import asyncio
import json
from fastapi import APIRouter,Depends,HTTPException,Response,Query
from pydantic import BaseModel,Field
from .. import work_queue
from .. import engine,library,store,translations,assistant_metrics,startup_diagnostic
from .deps import CaptionResume,SourceIdentifier,admin,optional_feature,user
from .. import app as core  # VERSION est défini dans pilot/app.py

router=APIRouter()


class TranslationBenchmarkRequest(BaseModel):
    mode:str=Field(default='rapide',max_length=50)


@router.get('/api/admin/translation-benchmark')
async def get_translation_benchmark(value=Depends(admin)):
    with optional_feature('translation_benchmark') as module:return await asyncio.to_thread(module.status)


@router.get('/api/admin/translation-benchmark/report')
async def report_translation_benchmark(value=Depends(admin)):
    with optional_feature('translation_benchmark') as module:return await asyncio.to_thread(module.status,True)


@router.post('/api/admin/translation-benchmark/start',status_code=202)
async def start_translation_benchmark(body:TranslationBenchmarkRequest,value=Depends(admin)):
    async with startup_diagnostic.observe('translation_benchmark',body.mode,core.VERSION):
        with optional_feature('translation_benchmark') as module:return await module.start(body.mode,core.VERSION)


@router.post('/api/admin/translation-benchmark/pause')
async def pause_translation_benchmark(value=Depends(admin)):
    with optional_feature('translation_benchmark') as module:return await module.pause()


@router.post('/api/admin/translation-benchmark/resume',status_code=202)
async def resume_translation_benchmark(body:CaptionResume,value=Depends(admin)):
    with optional_feature('translation_benchmark') as module:return await module.resume(body.mode)


class SummaryRequest(BaseModel):
    question:str=Field(default='Fais une synthèse des informations utiles des documents choisis.',min_length=1,max_length=6000)
    conversation_id:str|None=Field(default=None,max_length=100)
    source_ids:list[SourceIdentifier]|None=Field(default=None,max_length=12)
    mode:str='rapide'


class SummaryResume(BaseModel):
    mode:str|None=Field(default=None,max_length=100)


@router.post('/api/summaries',status_code=202)
async def create_summary(body:SummaryRequest,value=Depends(user)):
    with optional_feature('summaries') as module:
        return await module.create(value['id'],body.question,body.mode,body.conversation_id,body.source_ids)


@router.get('/api/summaries/{identifier}')
async def summary_status(identifier:str,offset:int=Query(default=0,ge=0,le=100000),value=Depends(user)):
    with optional_feature('summaries') as module:return module.status(identifier,value['id'],offset)


@router.post('/api/summaries/{identifier}/pause')
async def pause_summary(identifier:str,value=Depends(user)):
    with optional_feature('summaries') as module:return await module.pause(identifier,value['id'])


@router.post('/api/summaries/{identifier}/resume',status_code=202)
async def resume_summary(identifier:str,body:SummaryResume,value=Depends(user)):
    with optional_feature('summaries') as module:return await module.resume(identifier,value['id'],body.mode)


@router.get('/api/summaries/{identifier}/export')
async def export_summary(identifier:str,value=Depends(user)):
    with optional_feature('summaries') as module:text=module.export(identifier,value['id'])
    return Response(text,media_type='text/markdown; charset=utf-8',headers={'Content-Disposition':'attachment; filename="synthese-et-notes.md"'})


class TranslationRequest(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    conversation_id:str|None=Field(default=None,max_length=100)
    mode:str='rapide'
    first_page:int=Field(default=1,ge=1,le=1200)
    last_page:int|None=Field(default=None,ge=1,le=1200)


class TranslationResume(BaseModel):
    mode:str|None=None


class TranslationTerm(BaseModel):
    source:str=Field(min_length=1,max_length=100)
    french:str=Field(min_length=1,max_length=100)


class TranslationTermsRequest(BaseModel):
    terms:list[TranslationTerm]=Field(max_length=40)


@router.get('/api/translation-terms')
async def get_translation_terms(value=Depends(user)):
    from .. import translation_terms
    return await asyncio.to_thread(translation_terms.profile,value['id'])


@router.put('/api/translation-terms')
async def save_translation_terms(body:TranslationTermsRequest,value=Depends(user)):
    from .. import translation_terms
    return await asyncio.to_thread(translation_terms.save,value['id'],[row.model_dump() for row in body.terms])


@router.post('/api/translations',status_code=202)
async def translate_document(body:TranslationRequest,value=Depends(user)):
    return await translations.create(value['id'],body.source_id,body.conversation_id,body.mode,body.first_page,body.last_page)


@router.get('/api/translations/{identifier}')
async def translation_status(identifier:str,offset:int=Query(default=0,ge=0,le=100000),value=Depends(user)):
    return translations.status(identifier,value['id'],offset)


@router.post('/api/translations/{identifier}/pause')
async def pause_translation(identifier:str,value=Depends(user)):
    return await translations.pause(identifier,value['id'])


@router.post('/api/translations/{identifier}/resume',status_code=202)
async def resume_translation(identifier:str,body:TranslationResume,value=Depends(user)):
    return await translations.resume(identifier,value['id'],body.mode)


@router.post('/api/translations/{identifier}/stop')
async def stop_translation(identifier:str,value=Depends(user)):
    return await translations.stop(identifier,value['id'])


@router.delete('/api/translations/{identifier}')
async def delete_translation(identifier:str,value=Depends(user)):
    return await translations.delete(identifier,value['id'])


@router.get('/api/translations/{identifier}/export')
async def export_translation(identifier:str,value=Depends(user)):
    text=translations.export(identifier,value['id'])
    return Response(text,media_type='text/plain; charset=utf-8',headers={'Content-Disposition':'attachment; filename="traduction-fr.txt"'})


@router.post('/api/translations/{identifier}/publish')
async def publish_translation(identifier:str,value=Depends(user)):
    item=translations.owned(identifier,value['id'])
    try:source=await library.source(item['source_id'])
    except HTTPException:source={'id':item['source_id'],'title':item['title']}
    with optional_feature('publications') as module:
        with store.connect() as db:module.reserve(db,identifier,value['id'],source)
        return await module.publish(identifier,value['id'])


@router.get('/api/jobs/{identifier}')
async def job(identifier:str,value=Depends(user)):
    with store.connect() as db:row=db.execute('SELECT * FROM jobs WHERE id=? AND user_id=?',(identifier,value['id'])).fetchone()
    if not row:raise HTTPException(404,'Demande introuvable.')
    live=engine.MEASUREMENTS.get(identifier)
    measured=live.live() if live else assistant_metrics.read(identifier)
    from .. import documentary
    observed=engine.DOCUMENTARY.get(identifier)
    evidence=observed.view() if observed else documentary.for_job(identifier) or documentary.clean((measured or {}).get('documentary'))
    queued=work_queue.queue_fields(identifier,row['status'],'chat')
    return {**dict(row),'sources':json.loads(row['sources']),'progress':engine.PROGRESS.get(identifier,{}),'measurements':measured,
            **queued,**({'documentary':evidence} if evidence else {})}


@router.get('/api/jobs/{identifier}/measurements')
async def job_measurements(identifier:str,value=Depends(user)):
    found=await job(identifier,value)
    if not found['measurements']:raise HTTPException(404,'Mesures indisponibles pour cette ancienne réponse.')
    return {'version':core.VERSION,**found['measurements']}


@router.post('/api/jobs/{identifier}/cancel')
async def cancel(identifier:str,value=Depends(user)):
    await job(identifier,value);engine.cancel(identifier)
    return {'ok':True}
