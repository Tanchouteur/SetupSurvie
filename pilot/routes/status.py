"""Routes du pilote — statut, santé, réseau et moteur d’inférence."""
from fastapi import APIRouter,Depends,Request,Response
from pydantic import BaseModel
from .. import engine,inventory,library,network,operations,store
from .deps import DEGRADED,admin
from .. import app as core  # VERSION est défini dans pilot/app.py

router=APIRouter()


@router.get('/api/health')
async def health():return {'ok':True,'version':core.VERSION,'degraded_features':sorted(DEGRADED)}


@router.get('/api/assistant-context')
async def assistant_context():
    return {'system':engine.POLICY.read_text()+'\n'+engine.SYSTEM_APPENDIX,'profiles':list(engine.MODES.values()),
            'context_tokens':engine.PROFILE_CONFIG['context'],'output_tokens':engine.PROFILE_CONFIG['output_tokens'],
            'history_max_characters':7000,'source_excerpt_characters':3500,'tools':engine.TOOLS,
            'note':'Les messages de la conversation et les résultats d’outils s’ajoutent à cette consigne. Open WebUI ajoute son propre contexte natif.'}


@router.get('/api/status')
async def status():
    with store.connect() as db:guides=db.execute('SELECT count(*) FROM documents').fetchone()[0]
    return {'version':core.VERSION,'books':await library.books(),'guides':guides,
            'modes':[{'id':key,**value} for key,value in engine.MODES.items()]}


@router.get('/api/activity')
async def local_activity():return await operations.activity()


@router.get('/api/inventory')
async def local_inventory():return await inventory.inventory()


@router.get('/api/network')
async def network_status(request:Request):return network.status(request.url.hostname)


@router.get('/api/network/qr.svg')
async def network_qr(request:Request,kind:str='direct'):
    return Response(network.qr(network.status(request.url.hostname),kind),media_type='image/svg+xml',
                    headers={'Content-Security-Policy':"default-src 'none'; sandbox"})


@router.get('/api/inference')
async def inference_status():
    state=await operations.status()
    with store.connect() as db:
        counts={row['status']:row['n'] for row in db.execute("SELECT status,count(*) AS n FROM jobs WHERE status IN ('queued','running') GROUP BY status")}
    return {**state,'jobs':counts}


class StartEngine(BaseModel):force:bool=False


@router.post('/api/admin/inference/start')
async def start_engine(body:StartEngine,value=Depends(admin)):return await operations.command('start',body.force)


@router.post('/api/admin/inference/stop')
async def stop_engine(value=Depends(admin)):return await operations.command('stop')
