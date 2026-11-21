"""Routes du pilote — bibliothèque, recherche, sources, dossiers pratiques, classement et lecture de documents."""
import asyncio
from datetime import datetime,timezone
from pathlib import Path
import re
import time
from typing import Literal
from urllib.parse import quote
from fastapi import APIRouter,Depends,HTTPException,Request,Response,UploadFile,File,Form,Query
from pydantic import BaseModel,Field
from starlette.responses import FileResponse,JSONResponse,StreamingResponse
from .. import collection_sort,inventory,library,maps,network,operations,store,source_metadata,learning,catalogue,search_stream
from .deps import admin,optional_feature,user
from .. import app as core  # VERSION est défini dans pilot/app.py

router=APIRouter()


class LibrarySelection(BaseModel):
    themes:list[str]=Field(min_length=1,max_length=100)
    languages:list[str]=Field(default_factory=lambda:['fr','en'],min_length=1,max_length=2)
    max_add_gb:int=Field(default=0,ge=0)
    include_supplements:bool=False
    collection_sort:dict|None=None


class LibraryDownload(BaseModel):
    id:str=Field(pattern='^[a-f0-9]{32}$')


class IndexSettings(BaseModel):
    enabled:bool=True
    start_hour:int=Field(default=0,ge=0,le=23)
    end_hour:int=Field(default=0,ge=0,le=23)
    workers:int=Field(default=0,ge=0,le=16)


@router.post('/api/admin/library/index-settings')
async def set_index_settings(body:IndexSettings,value=Depends(admin)):
    return await operations.library_command('index-settings',body.model_dump())


@router.post('/api/admin/library/index/{action}')
async def index_archives(action:Literal['prepare','start','pause'],value=Depends(admin)):
    return await operations.library_command({'prepare':'index-prepare','start':'index','pause':'pause'}[action])


@router.get('/api/admin/library')
async def library_status(value=Depends(admin)):
    return await operations.library_command()


@router.post('/api/admin/library/plan',status_code=202)
async def library_plan(body:LibrarySelection,value=Depends(admin)):
    if body.collection_sort is not None:
        try:
            collection_sort.parse(body.collection_sort)
        except ValueError as exc:
            raise HTTPException(400,str(exc)) from exc
    return await operations.library_command('plan',body.model_dump(exclude_none=True))


@router.post('/api/admin/library/download',status_code=202)
async def library_download(body:LibraryDownload,value=Depends(admin)):
    return await operations.library_command('download',body.model_dump())


class CollectionBatch(BaseModel):
    keys:list[str]=Field(min_length=1,max_length=500)
    state:Literal['main','other']|None=None
    token:str|None=Field(default=None,pattern='^[a-f0-9]{64}$')


@router.get('/api/library/collection-sort')
async def library_collection_sort():
    return await asyncio.to_thread(inventory.sortable_collections)


@router.get('/api/admin/library/collection-sort/export')
async def export_collection_sort(value=Depends(admin)):
    sorting=await asyncio.to_thread(collection_sort.load,network.CATALOG)
    return JSONResponse(sorting.as_json(),headers={'Content-Disposition':'attachment; filename="SetupSurvie-tri.json"'})


@router.get('/api/admin/library/reference')
async def preview_library_reference(value=Depends(admin)):
    return await operations.library_command('reference-preview')


@router.get('/api/admin/library/reference/restoration')
async def preview_reference_restoration(value=Depends(admin)):
    return await operations.library_command('reference-preview', {'restore': True})


class ReferenceDownload(BaseModel):
    archive: str = Field(min_length=1, max_length=240)


class ReferenceRestoration(BaseModel):
    confirmation_token: str = Field(pattern='^[a-f0-9]{64}$')


@router.post('/api/admin/library/reference/restoration',status_code=202)
async def restore_library_reference(body:ReferenceRestoration,value=Depends(admin)):
    return await operations.library_command('download', {'reference_confirmation': body.confirmation_token})


@router.post('/api/admin/library/reference/download',status_code=202)
async def download_reference_archive(body:ReferenceDownload,value=Depends(admin)):
    return await operations.library_command('download', {'reference_archive': body.archive})


@router.post('/api/admin/library/collection-sort/{action}')
async def change_collection_sort(action:Literal['move','preview','exclude'],body:CollectionBatch,value=Depends(admin)):
    return await operations.library_command('collection-'+action,body.model_dump())


@router.get('/api/library/category-index')
async def category_index_status():
    report,_=await asyncio.to_thread(library.category_index.availability,inventory.ZIMS,store.ROOT,
                                     await asyncio.to_thread(library.collection_sort.load,library.network.CATALOG))
    return {key:report[key] for key in ('phase','archive','archives','completed','done','total','bytes','elapsed_seconds','counts') if key in report}


@router.post('/api/admin/library/category-index',status_code=202)
async def prepare_category_index(value=Depends(admin)):
    return await operations.library_command('category-index')


@router.post('/api/admin/library/pause',status_code=202)
async def library_pause(value=Depends(admin)):
    return await operations.library_command('pause')


@router.get('/api/library/search-diagnostic')
async def search_diagnostic():
    async def server():
        started=time.monotonic()
        try:
            await asyncio.wait_for(library.get('/'),3)
            return {'state':'reachable','elapsed_ms':round((time.monotonic()-started)*1000)}
        except (TimeoutError,HTTPException):return {'state':'unavailable','elapsed_ms':round((time.monotonic()-started)*1000)}
        except Exception:return {'state':'unavailable','elapsed_ms':round((time.monotonic()-started)*1000)}
    catalog,access=await asyncio.gather(library.books(refresh=True),server())
    info=catalog.info() if isinstance(catalog,library.Catalog) else {'state':'live','collections':len(catalog)}
    report=await asyncio.to_thread(library.index_report)
    return {'version':core.VERSION,'created':time.time(),'kiwix':access,'catalog':info,
            'guides':{'indexed':report.get('indexed',0),'status':report.get('status')},
            'archive_index':library.archive_index.status(store.ROOT/'archive-index'),
            'notice':'Diagnostic sans IA. Mesure de préparation distincte des recherches suivantes.'}


@router.get('/api/search')
async def search(request:Request,q:str=Query(default='',max_length=200),language:str='',limit:int=Query(default=8,ge=1,le=20),favorites_only:bool=False,translations_only:bool=False,collection:str=Query(default='',max_length=160),domain:Literal['all','resilience','culture','other']|None=None,diagnostic:bool=False,stream:bool=False,kind:Literal['all','documents','videos']='all'):
    if domain is None:
        domain = 'all' if favorites_only or translations_only else library.DEFAULT_SEARCH_DOMAIN
    owner=(await user(request))['id'] if favorites_only else None
    if stream:
        return StreamingResponse(search_stream.packets(q.strip(),language,limit=limit,favorite_user=owner,translations_only=translations_only,collection=collection,domain=domain,diagnostic=diagnostic,kind=kind),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    details={'budget':search_stream.BUDGET}
    if diagnostic:
        details['diagnostic']=True
    if favorites_only or translations_only:
        with optional_feature('favorites' if favorites_only else 'publications'):
            found=await library.search(q.strip(),language,limit=limit,favorite_user=owner,translations_only=translations_only,collection=collection,domain=domain,kind=kind,**details) if q.strip() or kind=='videos' else []
    else:
        found=await library.search(q.strip(),language,limit=limit,favorite_user=owner,translations_only=translations_only,collection=collection,domain=domain,kind=kind,**details) if q.strip() or kind=='videos' else []
    return {'results':found,**({'coverage':found.coverage} if isinstance(found,library.SearchResults) else {})}


@router.get('/api/library/translations')
async def shared_translations():
    with optional_feature('publications') as publications:
        with store.connect() as db:
            rows=db.execute("SELECT g.path,g.title,g.language FROM guide_meta g JOIN translation_publications p ON p.published_path=g.path WHERE p.published_at IS NOT NULL ORDER BY p.published_at DESC LIMIT 200").fetchall()
            return {'results':[{'id':'guide:'+row['path'],'title':row['title'],'language':row['language'],'kind':'guide','url':'/guides/'+quote(row['path']),'excerpt':publications.NOTICE,**library.guide_metadata(db,'guide:'+row['path'])} for row in rows]}


@router.get('/api/library/learning')
async def learning_paths():
    try:return learning.pathways()
    except (OSError,ValueError,KeyError):raise HTTPException(503,'Les parcours ne sont pas disponibles. La recherche documentaire reste accessible.')


@router.get('/api/source')
async def source(id:str):return await library.source(id)


@router.get('/api/library/french-reading')
async def french_reading(original_id:str=Query(min_length=1,max_length=2000)):
    with optional_feature('translation_reader') as module:return JSONResponse(await asyncio.to_thread(module.choices,original_id),headers={'Cache-Control':'no-store'})


@router.get('/api/library/french-page')
async def french_page(id:str=Query(min_length=1,max_length=2000),original_id:str=Query(min_length=1,max_length=2000),page:int=Query(default=1,ge=1,le=1200)):
    with optional_feature('translation_reader') as module:return JSONResponse(await asyncio.to_thread(module.page,id,original_id,page),headers={'Cache-Control':'no-store'})


class PracticalReference(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    source_revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    dossier_revision:int=Field(ge=0)
    sections:list[str]=Field(min_length=1,max_length=6)
    note:str=Field(min_length=1,max_length=700)
    locator:str=Field(min_length=1,max_length=200)
    reviewed:bool=False


@router.get('/api/library/dossiers')
async def practical_dossiers():
    with optional_feature('practical') as module:return await asyncio.to_thread(module.overview)


@router.get('/api/library/dossiers/{identifier}')
async def practical_dossier(identifier:str):
    with optional_feature('practical') as module:return await asyncio.to_thread(module.dossier,identifier)


@router.get('/api/library/dossiers/{identifier}/search')
async def practical_sources(identifier:str):
    with optional_feature('practical') as module:return await module.search(identifier)


@router.put('/api/admin/library/dossiers/{identifier}/references')
async def save_practical_reference(identifier:str,body:PracticalReference,value=Depends(admin)):
    with optional_feature('practical') as module:
        return await module.save(identifier,body.source_id,body.source_revision,body.dossier_revision,body.sections,body.note,body.locator,body.reviewed)


@router.delete('/api/admin/library/dossiers/{identifier}/references/{entry_id}')
async def remove_practical_reference(identifier:str,entry_id:str,revision:int=Query(ge=0),value=Depends(admin)):
    with optional_feature('practical') as module:return await asyncio.to_thread(module.remove,identifier,entry_id,revision)


@router.get('/api/admin/library/dossiers-export')
async def export_practical_dossiers(value=Depends(admin)):
    with optional_feature('practical') as module:return {'version':core.VERSION,**await asyncio.to_thread(module.export)}


class SourceClassification(BaseModel):
    source_id:str=Field(min_length=1,max_length=2000)
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    domains:list[Literal['resilience','culture']]=Field(max_length=2)
    document_type:Literal['unknown','overview','explanation','procedure','exercise','manual']='unknown'
    reviewed:bool=False


class CollectionLabels(BaseModel):
    collection_id:str=Field(min_length=1,max_length=300)
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    family:str=Field(min_length=1,max_length=80)
    variant:str=Field(min_length=1,max_length=120)


@router.put('/api/admin/library/classification')
async def set_classification(body:SourceClassification,value=Depends(admin)):
    if not body.source_id.startswith(('guide:','zim:','video:')):raise HTTPException(400,'Référence de document invalide.')
    with optional_feature('catalogue') as module:
        return await asyncio.to_thread(module.save,body.source_id,{'domains':body.domains,'document_type':body.document_type,'status':'reviewed' if body.reviewed else 'corrected'},body.revision,library.GUIDES,inventory.ZIMS)


@router.put('/api/admin/library/collection-labels')
async def set_collection_labels(body:CollectionLabels,value=Depends(admin)):
    with optional_feature('catalogue') as module:
        return await asyncio.to_thread(module.save,'collection:'+body.collection_id,{'family':body.family.strip(),'variant':body.variant.strip()},body.revision,library.GUIDES,inventory.ZIMS)


@router.delete('/api/admin/library/metadata')
async def reset_document_metadata(source_id:str=Query(min_length=1,max_length=2000),value=Depends(admin)):
    with optional_feature('catalogue') as module:await asyncio.to_thread(module.reset,source_id)
    return {'ok':True}


@router.get('/api/admin/library/metadata-export')
async def export_document_metadata(value=Depends(admin)):
    with optional_feature('catalogue') as module:return await asyncio.to_thread(module.export)


@router.get('/api/original')
async def original_pdf(id:str=Query(max_length=2000)):
    base=id.split('#page=')[0]
    if not base.startswith('guide:') or not base.lower().endswith('.pdf'):raise HTTPException(400,'Document PDF local requis.')
    await library.source(base)
    path=library.GUIDES/base.removeprefix('guide:')
    if any(p.is_symlink() for p in [path,*path.parents]) or not path.resolve().is_relative_to(library.GUIDES.resolve()) or not path.is_file():
        raise HTTPException(404,'Document original indisponible.')
    return FileResponse(path,media_type='application/pdf',headers={'Content-Disposition':'inline','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; frame-ancestors 'self'"})


@router.get('/api/maps')
async def offline_maps():return {'maps':await asyncio.to_thread(maps.available)}


@router.get('/api/library/coverage')
async def library_coverage():return await asyncio.to_thread(library.index_report)


@router.get('/api/maps/{identifier}/archive')
async def map_archive(identifier:str):
    path=await asyncio.to_thread(maps.archive,identifier)
    return FileResponse(path,media_type='application/octet-stream',headers={'Cache-Control':'public, max-age=3600'})


def illustration_revision(identifier,expected):
    current=catalogue.revision(identifier,library.GUIDES,inventory.ZIMS)
    if expected and current!=expected:raise HTTPException(409,'Le document a changé depuis cette réponse. Ouvrez son original actuel ; cette illustration n’est pas remplacée silencieusement.')
    return bool(expected and current==expected)


@router.get('/api/illustrations/document')
async def illustration_document(id:str=Query(max_length=2000),revision:str=Query(default='',pattern=r'^(?:[a-f0-9]{64})?$')):
    match=re.fullmatch(r'(guide:.+\.pdf)#page=([1-9]\d{0,3})',id,re.I)
    if not match or int(match[2])>1200:raise HTTPException(400,'Référence de page PDF non valide.')
    canonical=catalogue.canonical(match[1]);key=canonical.removeprefix('guide:')
    checked=await asyncio.to_thread(illustration_revision,canonical,revision)
    if not catalogue.revision(canonical,library.GUIDES,inventory.ZIMS):raise HTTPException(404,'Document original indisponible.')
    return {'url':'/guides/'+quote(key,safe='/'),'page':int(match[2]),'version_checked':checked}


@router.get('/api/media')
async def media(id:str,source_id:str=Query(default='',max_length=2000),revision:str=Query(default='',pattern=r'^(?:[a-f0-9]{64})?$')):
    path=library.safe_zim_path(id)
    if source_id:
        source=library.safe_zim_path(source_id)
        if source.split('/')[0]!=path.split('/')[0]:raise HTTPException(400,'L’illustration doit appartenir à l’archive de sa source.')
        await asyncio.to_thread(illustration_revision,source_id,revision)
    elif revision:raise HTTPException(400,'Indiquez la source de cette illustration.')
    if path.split('/')[0] not in {b['book'] for b in await library.books()}:raise HTTPException(404,'Collection inconnue.')
    data,kind=await library.get('/content/'+quote(path,safe='/'),maximum=8_000_000)
    if not kind.startswith('image/'):raise HTTPException(400,'Ce contenu n’est pas une illustration.')
    if source_id:await asyncio.to_thread(illustration_revision,source_id,revision)
    return Response(data,media_type=kind,headers={'Content-Security-Policy':"sandbox; default-src 'none'"})


@router.post('/api/admin/reindex')
async def reindex(value=Depends(admin)):return {'guides':await asyncio.to_thread(library.index_guides)}


@router.post('/api/admin/guides')
async def upload(file:UploadFile=File(...),title:str=Form(...),language:str=Form('fr'),provenance:str=Form(''),licence:str=Form(''),
                 document_date:str=Form('',max_length=10),edition:str=Form('',max_length=300),value=Depends(admin)):
    document_date=document_date.strip()
    if document_date and not source_metadata.date_value(document_date):raise HTTPException(422,'Date du document : indiquez une année, une année-mois ou une date AAAA-MM-JJ valide, ou laissez vide si elle est inconnue.')
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.txt','.md','.epub'):raise HTTPException(400,'Formats acceptés : PDF, texte, Markdown ou EPUB.')
    data=await file.read(20_000_001)
    if len(data)>20_000_000:raise HTTPException(413,'Ce fichier dépasse 20 Mo.')
    language=language if language in ('fr','en') else ''
    path=store.new_id()+'.'+(language or 'other')+suffix
    library.GUIDES.mkdir(parents=True,exist_ok=True)
    from ..durable import write_bytes
    write_bytes(library.GUIDES/path,data)
    with store.connect() as db:
        db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',(path,title[:200],language,provenance[:1000],licence[:1000]))
        db.execute('INSERT INTO guide_dates VALUES(?,?,?,?)',(path,document_date,edition.strip(),datetime.now(timezone.utc).date().isoformat()))
    count=await asyncio.to_thread(library.index_guides)
    with store.connect() as db:
        indexed=db.execute('SELECT 1 FROM documents WHERE id=?',('guide:'+path,)).fetchone()
        if not indexed:
            db.execute('DELETE FROM guide_meta WHERE path=?',(path,))
            db.execute('DELETE FROM guide_dates WHERE path=?',(path,))
    if not indexed:
        (library.GUIDES/path).unlink(missing_ok=True)
        raise HTTPException(400,'Le fichier n’a pas pu être lu. Vérifiez son format et son éventuelle protection par mot de passe.')
    return {'id':'guide:'+path,'guides':count}
