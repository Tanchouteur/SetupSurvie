"""Explicit context trials on already installed local models; never downloads one."""
import asyncio
import json
import time
import uuid
import httpx
from fastapi import HTTPException
from . import assistant_metrics,durable,engine,model_runtime,operations,store,translations

ACTIVE={}
RAM_RESERVE=4*1024**3
VIDEO_RESERVE=512*1024**2
REASONS={'paused':'Le moteur est en pause. L’essai attend une reprise volontaire.',
    'engine_unavailable':'Le moteur ne répond pas ou une commande est en cours.',
    'other_activity':'Une question ou une traduction a pris la priorité sur l’essai.',
    'hardware_unavailable':'Les mesures de mémoire du PC ne sont pas disponibles.',
    'ram_pressure':'La marge de mémoire vive est devenue insuffisante.',
    'video_pressure':'La marge de mémoire vidéo est devenue insuffisante.',
    'cold_unconfirmed':'Le déchargement du modèle n’a pas pu être confirmé.',
    'model_changed':'Le modèle a changé depuis le début des mesures.',
    'model_error':'Le moteur a interrompu cette mesure.',
    'incomplete_output':'Le modèle n’a pas terminé la réponse courte de vérification.',
    'unexpected_output':'La réponse du modèle dépasse le format de vérification.',
    'slow_response':'Le délai choisi pour le premier texte est dépassé à chaud.',
    'context_unconfirmed':'Le contexte réellement alloué n’a pas pu être confirmé.',
    'prompt_unmeasured':'Le moteur n’a pas renvoyé le nombre de tokens traités.',
    'prompt_coverage':'Le volume réellement traité ne permet pas de valider ce contexte.',
    'model_metadata_unavailable':'Le modèle local et ses limites n’ont pas pu être vérifiés.',
    'another_model_loaded':'Un autre modèle est chargé. Refaites l’essai lorsque le moteur est disponible.',
    'context_unsupported':'Ce modèle n’annonce pas le contexte minimal de cet essai.',
    'time_limit':'Le temps maximal de l’essai est atteint.',
    'timeout':'Le temps maximal de cette mesure est atteint.',
    'test_unavailable':'La mesure n’a pas pu se terminer. Les réglages sont conservés.',
    'user_cancelled':'Essai arrêté à votre demande.',
    'service_restarted':'Le service a redémarré. Relancez un nouvel essai explicitement.'}


class Abort(Exception):
    def __init__(self,reason,sample=None):super().__init__(reason);self.sample=sample


def running():return any(not task.done() for task in ACTIVE.values())


def competing_trial():
    # An optional module can be absent; if it is running, it is already loaded.
    import sys
    module=sys.modules.get(__package__+'.search_experiment')
    return module is not None and module.running()


def location():return store.ROOT/'calibration/latest.json'


def status():
    try:
        path=location()
        if path.stat().st_size>1_000_000:raise ValueError()
        report=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(report,dict) or report.get('schema')!=1:raise ValueError()
        task=ACTIVE.get(report.get('id'))
        if report.get('status')=='running' and (task is None or task.done()):report={**report,'status':'interrupted','reason':'service_restarted'}
        return {**report,'message':REASONS.get(report.get('reason'),'Essai en cours.' if report.get('status')=='running' else 'Mesures terminées ; examinez le rapport avant de changer le réglage.')}
    except (OSError,ValueError):return {'schema':1,'status':'not_started','trials':[],'recommendation':None}


def save(report):
    raw=json.dumps(report,ensure_ascii=False).encode('utf-8')
    if isinstance(report.get('id'),str) and len(report['id'])==32 and all(c in '0123456789abcdef' for c in report['id']):
        durable.write_bytes(location().with_name(report['id']+'.json'),raw,private=True)
    durable.write_bytes(location(),raw,private=True)


async def guard(options,*,starting=False):
    state=await operations.status(fresh=True)
    if state.get('paused'):raise Abort('paused')
    if not state.get('online') or state.get('operation'):raise Abort('engine_unavailable')
    if engine.ACTIVE or translations.ACTIVE:raise Abort('other_activity')
    memory=state.get('memory',{});available=memory.get('available')
    if not isinstance(available,(int,float)) or type(memory.get('total')) is not int or memory['total']<=0 or not state.get('control_available'):
        raise Abort('hardware_unavailable',{'control_available':bool(state.get('control_available')),'ram_sample_available':isinstance(available,(int,float)),
            **{k:state[k] for k in ('control_error','control_http_status','control_elapsed_ms') if k in state}})
    gpus=state.get('gpus',[])
    sample={'ram_available':int(available),'video_available':min((int(g['total']-g['used']) for g in gpus),default=None)}
    if available<options['reserve_ram_bytes']:raise Abort('ram_pressure',sample)
    if any(g.get('total',0)-g.get('used',0)<options['reserve_video_bytes'] for g in gpus):raise Abort('video_pressure',sample)
    return sample


def prompt(context,target=None):
    # Bounded, synthetic material: no family documents or personal conversation.
    target=max(1024,min(int(target or (context-6144)*1.2),context*8,1_000_000))
    lines=[];size=0;number=0
    while size<target:
        line=f'Repère {number:06d} : matériel fictif, aucune consigne pratique.\n'
        lines.append(line);size+=len(line.encode('utf-8'));number+=1
    return ''.join(lines)+'\nFin du test synthétique. Réponds uniquement OK.'


async def trial(report,context,temperature,options):
    row={'context':context,'temperature':temperature,'status':'running','started':time.time()};report['trials'].append(row);save(report)
    measured=assistant_metrics.Measurement('calibration',report['model'],report['mode'],context)
    row['minimum_free']=await guard(options)
    async def generate():
        answer='';last={}
        async with asyncio.timeout(options['trial_timeout_seconds']),httpx.AsyncClient(trust_env=False,timeout=httpx.Timeout(60,connect=10)) as client:
            if temperature=='cold':
                response=await client.post(engine.OLLAMA+'/api/generate',json={'model':report['model'],'keep_alive':0,'stream':False})
                response.raise_for_status()
                response=await client.get(engine.OLLAMA+'/api/ps');response.raise_for_status()
                if any(m.get('name',m.get('model'))==report['model'] for m in response.json().get('models',[])):raise Abort('cold_unconfirmed')
            await guard(options)
            target=2048 if temperature=='probe' else int((context-3072)*.9/report['prompt_tokens_per_byte'])
            material=prompt(context,target);row['prompt_utf8_bytes']=len(material.encode('utf-8'))
            payload={'model':report['model'],'messages':[{'role':'user','content':material}],'think':engine.MODES[report['mode']]['think'],
                'stream':True,'keep_alive':'5m','options':{'num_ctx':context,'num_predict':1 if temperature=='probe' else 1024,'temperature':0}}
            async with client.stream('POST',engine.OLLAMA+'/api/chat',json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:continue
                    last=json.loads(line)
                    if last.get('error'):raise Abort('model_error')
                    text=last.get('message',{}).get('content','')
                    if text:measured.text();answer+=text
                    if len(answer)>4096:raise Abort('unexpected_output')
            measured.model_call(last)
        if not last.get('done') or (temperature!='probe' and (last.get('done_reason')!='stop' or answer.strip().strip('.')!='OK')):raise Abort('incomplete_output')
        if temperature=='warm' and (measured.first_text is None or measured.first_text>options['max_first_text_ms']):raise Abort('slow_response')
        runtime=await model_runtime.describe(engine.OLLAMA,report['model'],fresh=True)
        if runtime.get('digest')!=report['runtime']['digest']:raise Abort('model_changed')
        placement=runtime.get('running') or {}
        if not isinstance(placement.get('context_length'),int) or placement['context_length']<context:raise Abort('context_unconfirmed')
        if type(last.get('prompt_eval_count')) is not int or last['prompt_eval_count']<0 or (temperature in ('cold','probe') and not last['prompt_eval_count']):raise Abort('prompt_unmeasured')
        if temperature=='probe':
            ratio=last['prompt_eval_count']/row['prompt_utf8_bytes']
            if not .05<=ratio<=2:raise Abort('prompt_unmeasured')
            row['prompt_tokens_per_byte']=ratio
        if temperature=='cold' and not (int((context-3072)*.65)<=last['prompt_eval_count']<=context-1536):raise Abort('prompt_coverage')
        if placement.get('size_vram',0) and row['minimum_free']['video_available'] is None:raise Abort('hardware_unavailable')
        row.update(placement=placement,response_valid=None if temperature=='probe' else True)
    task=asyncio.create_task(generate())
    try:
        while not task.done():
            await asyncio.wait({task},timeout=1)
            snapshot=await guard(options)
            for key,value in snapshot.items():
                if value is not None:row['minimum_free'][key]=min(row['minimum_free'][key],value) if row['minimum_free'][key] is not None else value
        await task;row['status']='passed'
    finally:
        if not task.done():task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        row.update(duration_ms=round((time.monotonic()-measured.started)*1000),first_text_ms=measured.first_text,model_calls=measured.value['model_calls'])


async def release_model(report):
    try:
        state=await operations.status(fresh=True)
        if state.get('online') and not state.get('paused'):
            async with asyncio.timeout(5),httpx.AsyncClient(trust_env=False,timeout=3) as client:
                response=await client.get(engine.OLLAMA+'/api/ps');response.raise_for_status()
                loaded=next((m for m in response.json().get('models',[]) if m.get('name',m.get('model'))==report['model']),None)
                if loaded and loaded.get('digest')==report.get('runtime',{}).get('digest'):
                    response=await client.post(engine.OLLAMA+'/api/generate',json={'model':report['model'],'keep_alive':0,'stream':False});response.raise_for_status()
                    response=await client.get(engine.OLLAMA+'/api/ps');response.raise_for_status()
                    report['model_released']=not any(m.get('name',m.get('model'))==report['model'] for m in response.json().get('models',[]))
                    model_runtime.CACHE.pop((str(store.ROOT),engine.OLLAMA,report['model']),None)
    except Exception:report['model_released']=False


async def run(report,options):
    try:
        async with engine.LOCK,asyncio.timeout(3600):
            await guard(options)
            state=await operations.status(fresh=True)
            report['hardware']={'ram_total':state.get('memory',{}).get('total'),'gpus':[{'name':g.get('name'),'total':g.get('total')} for g in state.get('gpus',[])]}
            runtime=await model_runtime.describe(engine.OLLAMA,report['model'],fresh=True);report['runtime']=runtime
            if not runtime.get('available') or not runtime.get('installed') or not runtime.get('digest') or not runtime.get('native_context'):raise Abort('model_metadata_unavailable')
            if runtime.get('other_models'):raise Abort('another_model_loaded')
            candidates=[n for n in (16384,32768,65536) if n<=options['max_context'] and n<=runtime['native_context']]
            if not candidates:raise Abort('context_unsupported')
            await trial(report,candidates[0],'probe',options)
            report['prompt_tokens_per_byte']=report['trials'][-1]['prompt_tokens_per_byte']
            for context in candidates:
                try:
                    for temperature in ('cold','warm'):await trial(report,context,temperature,options)
                    report['recommendation']=context;save(report)
                except (Abort,TimeoutError,httpx.HTTPError,ValueError) as error:
                    reason=str(error) if isinstance(error,Abort) else 'timeout' if isinstance(error,TimeoutError) else 'model_error'
                    report['trials'][-1].update(status='failed',reason=reason)
                    if isinstance(error,Abort) and error.sample:report['trials'][-1]['failure_free']=error.sample
                    report['reason']=reason;break
            report['status']='completed'
    except Abort as error:report.update(status='interrupted',reason=str(error))
    except asyncio.CancelledError:report.update(status='cancelled',reason='user_cancelled')
    except TimeoutError:report.update(status='interrupted',reason='time_limit')
    except Exception:report.update(status='failed',reason='test_unavailable')
    finally:
        if report['trials'] and report['trials'][-1].get('status')=='running':report['trials'][-1].update(status='cancelled' if report['status']=='cancelled' else 'failed',reason=report.get('reason','test_unavailable'))
        # Do not unload a model that a newly queued conversation is about to use.
        if report['trials'] and not engine.ACTIVE and not translations.ACTIVE and not engine.LOCK.locked():
            async with engine.LOCK:await release_model(report)
        report['finished']=time.time()
        try:save(report)
        except OSError:pass
        ACTIVE.pop(report['id'],None)


async def start(mode,max_context=32768,*,reserve_ram_bytes=RAM_RESERVE,reserve_video_bytes=VIDEO_RESERVE,max_first_text_ms=90000,trial_timeout_seconds=600):
    if mode not in engine.MODES:raise HTTPException(400,'Mode inconnu.')
    if running() or competing_trial() or engine.LOCK.locked():raise HTTPException(409,'Une réponse ou un essai est déjà en cours.')
    options={'max_context':max_context,'reserve_ram_bytes':reserve_ram_bytes,'reserve_video_bytes':reserve_video_bytes,'max_first_text_ms':max_first_text_ms,'trial_timeout_seconds':trial_timeout_seconds}
    try:await guard(options,starting=True)
    except Abort as error:raise HTTPException(409,REASONS.get(str(error),REASONS['test_unavailable']))
    if running() or competing_trial() or engine.LOCK.locked():raise HTTPException(409,'Une autre demande vient de démarrer. Réessayez après sa fin.')
    identifier=uuid.uuid4().hex
    report={'schema':1,'kind':'SetupSurvie context calibration','id':identifier,'created':time.time(),'status':'running','mode':mode,
            'model':engine.MODES[mode]['model'],'settings':options,'trials':[],'recommendation':None,'previous_context':engine.context_size(engine.MODES[mode]['model'])}
    save(report);ACTIVE[identifier]=asyncio.create_task(run(report,options));return report


async def cancel(reason='user_cancelled'):
    identifiers=set(ACTIVE);tasks=list(ACTIVE.values())
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)
    for identifier,task in list(ACTIVE.items()):
        if task.done():ACTIVE.pop(identifier,None)
    report=status()
    if report.get('id') in identifiers:
        report.update(status='cancelled' if reason=='user_cancelled' else 'interrupted',reason=reason)
        save(report)
    return status()


async def apply(identifier):
    report=status();context=report.get('recommendation')
    if running() or report.get('id')!=identifier or report.get('status')!='completed' or context not in (16384,32768,65536):raise HTTPException(409,'Aucun contexte terminé et mesuré à appliquer.')
    if not all(any(t.get('context')==context and t.get('temperature')==temperature and t.get('status')=='passed' for t in report['trials']) for temperature in ('cold','warm')):raise HTTPException(409,'Mesures incomplètes.')
    model=report['model'];runtime=await model_runtime.describe(engine.OLLAMA,model,fresh=True)
    if not runtime.get('digest') or runtime.get('digest')!=report['runtime'].get('digest'):raise HTTPException(409,'Le modèle a changé. Refaites l’essai avant d’appliquer ce résultat.')
    state=await operations.status(fresh=True)
    hardware={'ram_total':state.get('memory',{}).get('total'),'gpus':[{'name':g.get('name'),'total':g.get('total')} for g in state.get('gpus',[])]}
    if hardware!=report.get('hardware'):raise HTTPException(409,'Le matériel observé a changé. Refaites l’essai sur ce PC.')
    if not runtime.get('native_context') or context>runtime['native_context']:raise HTTPException(409,'Le modèle n’annonce plus ce contexte.')
    if running() or status().get('id')!=identifier:raise HTTPException(409,'Un autre essai a commencé. Attendez sa fin avant de choisir un résultat.')
    previous=engine.context_size(model)
    with store.connect() as db:
        records=[('context:'+model,str(context)),('context:tested:'+model,json.dumps({'context':context,'digest':runtime['digest'],'calibration':identifier}))]
        if previous!=context:records.append(('context:previous:'+model,str(previous)))
        for key,value in records:
            db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))
    return {'model':model,'tokens':context,'previous':previous}


def rollback(model):
    if model not in {p['model'] for p in engine.MODES.values()}:raise HTTPException(400,'Modèle inconnu.')
    with store.connect() as db:
        row=db.execute('SELECT value FROM settings WHERE key=?',('context:previous:'+model,)).fetchone()
        try:previous=int(row['value']) if row else None
        except (ValueError,TypeError):previous=None
        if previous not in (8192,16384,32768,65536):raise HTTPException(409,'Aucun réglage précédent conservé.')
        db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('context:'+model,str(previous)))
    return {'model':model,'tokens':previous}
