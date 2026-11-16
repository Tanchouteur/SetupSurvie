"""Explicit, bounded measurements on the installed library and selected local model.

No synthetic hardware stress, cache clearing, setting changes, model downloads or
forced unloads. Reports contain counters and fixed test labels, never source text.
"""
import asyncio
import json
import math
import re
import sqlite3
import sys
import time
import uuid

import httpx
from fastapi import HTTPException

from . import assistant_metrics,calibration,documentary,durable,engine,library,model_runtime,model_session,operations,store,translations

ACTIVE={}
REPORTS={}
INTERVAL=3
BASELINE=6
DEADLINE=3600
QUERIES=('faire du feu','panneau solaire batterie','révolution française')
QUESTION='Fais une courte synthèse des documents de la bibliothèque sur les techniques pour faire du feu. Cite uniquement les sources lues et distingue les informations manquantes.'
REASONS={**calibration.REASONS,'model_not_installed':'Le modèle choisi n’est pas installé localement.',
    'measurement_failed':'Une mesure a échoué. Les autres résultats sont conservés.',
    'completed':'Mesures terminées. Téléchargez le rapport pour l’analyse.',
    'completed_with_gaps':'Mesures terminées avec des étapes manquantes. Le rapport les indique.'}


def running():return any(not task.done() for task in ACTIVE.values())
def location():return store.ROOT/'performance/latest.json'


def save(report):
    durable.write_bytes(location(),json.dumps(report,ensure_ascii=False,allow_nan=False).encode(),private=True)


def load():
    if REPORTS:return next(iter(REPORTS.values()))
    try:
        if location().stat().st_size>16_000_000:raise ValueError()
        report=json.loads(location().read_text(encoding='utf-8'))
        if not isinstance(report,dict) or report.get('schema')!=1:raise ValueError()
        if report.get('status')=='running':
            report.update(status='interrupted',reason='service_restarted')
            recover_temporary_job()
        return report
    except (OSError,ValueError):return {'schema':1,'status':'not_started','steps':[],'samples':[]}


def status(full=False):
    report=load()
    value={k:v for k,v in report.items() if not k.startswith('_') and (full or k!='samples')}
    value['sample_count']=len(report.get('samples',[]))
    value['host_sample_count']=sum(bool(row.get('available')) for row in report.get('samples',[]))
    value['message']=REASONS.get(report.get('reason'),'Mesures en cours…' if report.get('status')=='running' else 'Aucun essai lancé.')
    return value


def competing():
    if engine.ACTIVE or translations.ACTIVE or calibration.running() or calibration.summary_activity():return True
    captions=sys.modules.get(__package__+'.captions')
    if captions and captions.running():return True
    module=sys.modules.get(__package__+'.search_experiment')
    return bool(module and module.running())


def number(value):return type(value) in (int,float) and 0<=value<=1e20 and math.isfinite(value)


def numeric_metrics(value):
    """Allowlist: future metrics fields must not accidentally export user content."""
    if not isinstance(value,dict):return {}
    result={k:v for k,v in value.items() if k in ('total_ms','first_text_ms','requested_context','context','sources_found','sources_read','prepared_sources','selected_sources','continued_sources') and number(v)}
    if type(value.get('context_limited')) is bool:result['context_limited']=value['context_limited']
    for key in ('phases_ms','cache_hits'):
        result[key]={k:v for k,v in value.get(key,{}).items() if isinstance(k,str) and len(k)<=64 and number(v)}
    for key in ('status','failure'):
        if isinstance(value.get(key),str) and value[key].replace('_','').isalnum():result[key]=value[key][:64]
    result['model_calls']=[{k:v for k,v in call.items() if k in ('prompt_eval_count','prompt_eval_cached_count','eval_count','load_ms','prompt_eval_ms','eval_ms','total_ms') and number(v)} for call in value.get('model_calls',[])[:100]]
    result['model_preparations']=[{k:v for k,v in call.items() if (k=='duration_ms' and number(v)) or (k=='status' and v in ('failed','ready'))} for call in value.get('model_preparations',[])[:4]]
    result['model_retries']=[{k:v for k,v in call.items() if (k=='http_status' and number(v)) or
        (k=='stage' and v in ('chat','loading')) or (k=='reason' and v in ('transport','http_error','memory_error','empty_response','stream_interrupted','model_error','invalid_model_load'))}
        for call in value.get('model_retries',[])[:4]]
    result['budgets']=[]
    for entry in value.get('budgets',[])[:100]:
        budget={k:v for k,v in entry.items() if number(v)}
        if type(entry.get('fits')) is bool:budget['fits']=entry['fits']
        if all(number(entry.get(k)) for k in ('context','input_estimate','output','template_reserve')):
            remaining=entry['context']-entry['input_estimate']-entry['output']-entry['template_reserve']
            budget.update(remaining_estimate=max(0,remaining),overflow_estimate=max(0,-remaining))
        result['budgets'].append(budget)
    result['reading_packets']=[{k:v for k,v in entry.items() if k in ('framing_bytes','maximum_bytes','encoded_bytes','sources','omitted','failed') and number(v)}
                              for entry in value.get('reading_packets',[])[:100]]
    for key in ('runtime','runtime_after'):
        runtime=value.get(key,{})
        result[key]={k:runtime[k] for k in ('native_context','other_models','available','installed') if k in runtime}
        if isinstance(runtime.get('running'),dict):result[key]['running']={k:v for k,v in runtime['running'].items() if k in ('size','size_vram','context_length') and number(v)}
    evidence=documentary.clean(value.get('documentary'))
    if evidence:result['documentary']=evidence
    return result


async def ai_guard():
    if competing():raise calibration.Abort('other_activity')
    state=await operations.status(fresh=True)
    if state.get('paused'):raise calibration.Abort('paused')
    if not state.get('online') or state.get('operation'):raise calibration.Abort('engine_unavailable')


async def watch(awaitable,timeout,*,guard=False):
    task=asyncio.create_task(awaitable)
    try:
        async with asyncio.timeout(timeout):
            while not task.done():
                await asyncio.wait({task},timeout=1)
                if not task.done() and guard:await ai_guard()
            return await task
    finally:
        if not task.done():task.cancel()
        await asyncio.gather(task,return_exceptions=True)


async def samples(report,started):
    used=0;previous=None
    while True:
        before=time.monotonic()
        try:value=await operations.performance()
        except Exception:value={'available':False,'reason':'controller_unavailable'}
        step=report.get('current_step')
        measured=engine.MEASUREMENTS.get(report.get('_job'))
        # Correlate with the pilot's monotonic clock, not a remote wall clock.
        sample={'elapsed_ms':round((before-started)*1000),'request_ms':round((time.monotonic()-before)*1000),'step':step,
                'interval_since_previous_ms':round((before-previous)*1000) if previous is not None else None,
                'phase':measured.stage if measured else report.get('current_phase'),'competing_application_activity':competing(),**value}
        previous=before
        size=len(json.dumps(sample))
        if len(report['samples'])<1202 and used+size<12_000_000:
            report['samples'].append(sample);used+=size
        else:report['dropped_samples']=report.get('dropped_samples',0)+1
        await asyncio.sleep(max(.1,INTERVAL-(time.monotonic()-before)))


async def classical(row,report):
    start=time.monotonic();first=None
    async def update(rows):
        nonlocal first
        if rows and first is None:first=round((time.monotonic()-start)*1000)
    found=await watch(library.search(row['query'],limit=12,domain='all',diagnostic=True,on_update=update,budget=120),180)
    coverage=getattr(found,'coverage',{})
    if row['query']==QUERIES[0] and not report.get('_selected'):
        report['_selected']=list(dict.fromkeys(item['id'] for item in found if isinstance(item.get('id'),str)))[:3]
    row.update(results=len(found),first_result_ms=first,
               coverage={k:coverage[k] for k in ('status','searched','failed','not_searched','without_fulltext','deadline_exceeded','cache_hits','parallelism','processing',
                   'primary_requests','request_limit','refinement_attempted','refinement_failed','refinement_not_searched','title_searched','title_failed','title_not_searched',
                   'concurrency','local_query','cache_ttl_seconds','cache_disk_ttl_seconds','deadline_ms','error_counts') if k in coverage})
    row['native_calls']=[{k:v for k,v in call.items() if (k in ('elapsed_ms','results','response_bytes','http_status') and number(v)) or
        (k=='cached' and isinstance(v,bool)) or (k=='stage' and v in ('fulltext','title','refinement')) or
        (k=='outcome' and v in ('success','error')) or (k=='reason' and v in ('timeout','invalid_response','http_error','connection_error'))}
        for call in coverage.get('trace',[])[:40]]
    row['native_calls_limited']=len(row['native_calls'])>=40
    if first is None and found:row['first_result_ms']=round((time.monotonic()-start)*1000)


async def generation(row,report):
    async with engine.LOCK:
        await ai_guard()
        runtime=await model_runtime.describe(engine.OLLAMA,report['model'],fresh=True)
        if not runtime.get('available') or not runtime.get('installed'):raise calibration.Abort('model_not_installed')
        requested=engine.context_size(report['model'])
        context=min(requested,runtime['native_context']) if runtime.get('native_context') else requested
        measured=assistant_metrics.Measurement('performance',report['model'],report['mode'],requested)
        measured.value.update(context=context,context_limited=context<requested,runtime=runtime)
        try:
          async with httpx.AsyncClient(trust_env=False) as client:
            def notice(stage):report['current_phase']=stage
            session=model_session.Session(client,engine.OLLAMA,runtime,context,measured,notice,ai_guard)
            await session.prepare();measured.phase('model_preparation')
            last={};characters=0;thinking=0
            payload={'model':report['model'],'messages':[{'role':'user','content':'Essai de débit sans documents. Décris un village imaginaire en environ 150 mots, en français. Aucune instruction technique.'}],
                     'stream':True,'think':engine.MODES[report['mode']]['think'],'keep_alive':'5m',
                     'options':{'num_ctx':context,'num_predict':512,'temperature':0,'seed':0}}
            async for event in session.chat(payload):
                message=event.get('message',{});text=message.get('content','');characters+=len(text);thinking+=len(message.get('thinking',''))
                if text:measured.text();measured.phase('writing');report['current_phase']='writing'
                last=event
            measured.model_call(last)
            measured.value['runtime_after']=await model_runtime.describe(engine.OLLAMA,report['model'],fresh=True)
            row.update(answer_characters=characters,thinking_characters=thinking)
            if not last.get('done') or not characters:raise calibration.Abort('incomplete_output')
            measured.value['status']='done'
        finally:
            if measured.value['status']=='running':measured.value['status']='incomplete'
            row['metrics']=numeric_metrics(measured.live())


def cleanup(conversation,job):
    # Only the UUID pair created by this test. Published/user documents untouched.
    with store.connect() as db:
        db.execute('DELETE FROM jobs WHERE id=? AND conversation_id=?',(job,conversation))
        db.execute('DELETE FROM conversations WHERE id=?',(conversation,))
    for directory in ('assistant-metrics','traces'):(store.ROOT/directory/(job+'.json')).unlink(missing_ok=True)


def recover_temporary_job():
    marker=location().with_name('active-job.json')
    try:
        if marker.stat().st_size>1024:return
        value=json.loads(marker.read_text());conversation,job=value.get('conversation'),value.get('job')
        if not all(isinstance(identifier,str) and re.fullmatch(r'[0-9a-f-]{36}',identifier) for identifier in (conversation,job)):return
        with store.connect() as db:
            row=db.execute('SELECT c.title FROM conversations c JOIN jobs j ON j.conversation_id=c.id WHERE c.id=? AND j.id=?',(conversation,job)).fetchone()
        if row and row['title']=='Essai temporaire de performances':cleanup(conversation,job)
        marker.unlink(missing_ok=True)
    except (OSError,ValueError,sqlite3.Error):pass


async def documentary_trial(row,report,user):
    await ai_guard()
    conversation,job=store.new_id(),store.new_id();now=time.time();report['_job']=job
    marker=location().with_name('active-job.json')
    durable.write_bytes(marker,json.dumps({'conversation':conversation,'job':job}).encode(),private=True)
    with store.connect() as db:
        db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,user,'Essai temporaire de performances',now))
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user',QUESTION,now))
        db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',(job,user,conversation,report['mode'],'queued',now,now))
    try:
        choices=report.get('_selected') if row['kind']=='selected_documentary' else None
        await watch(engine.run(job,user,conversation,report['mode'],domain='all',source_ids=choices),900,guard=True)
        row['metrics']=numeric_metrics(assistant_metrics.read(job))
        with store.connect() as db:state=db.execute('SELECT status FROM jobs WHERE id=?',(job,)).fetchone()
        if state:row['response_status']=state['status']
        row['reading_performed']=row['metrics'].get('documentary',{}).get('sources_read',0)>0
        if not row['reading_performed']:row['coverage_limit']='no_sources_read'
        if not state or state['status']!='done':raise calibration.Abort('incomplete_output')
    finally:
        if 'metrics' not in row:row['metrics']=numeric_metrics(assistant_metrics.read(job))
        report.pop('_job',None);cleanup(conversation,job);marker.unlink(missing_ok=True)


def interpretation(report):
    observations=[]
    for row in report['steps']:
        if row['kind'] not in ('generation','documentary','selected_documentary'):continue
        phases=row.get('metrics',{}).get('phases_ms',{})
        measured={key:value for key,value in phases.items() if number(value) and key not in ('finished',)}
        if measured:observations.append({'step':row['id'],'fact':'dominant_measured_phase','phase':max(measured,key=measured.get),'duration_ms':max(measured.values())})
        for index,call in enumerate(row.get('metrics',{}).get('model_calls',[])):
            count,duration=call.get('eval_count'),call.get('eval_ms')
            if number(count) and number(duration) and duration>0:
                observations.append({'step':row['id'],'fact':'model_output_throughput','call':index,'tokens_per_second':round(1000*count/duration,2)})
    resources=[sample for sample in report['samples'] if sample.get('available')]
    for row in report['steps']:
        selected=[sample for sample in resources if sample.get('step')==row['id']]
        cores=[s.get('cpu',{}).get('max_core_percent') for s in selected];cores=[v for v in cores if number(v)]
        disks=[d for s in selected for d in s.get('disks',[]) if d.get('data_disk')]
        busy=[d['busy_percent'] for d in disks if number(d.get('busy_percent'))]
        if cores and max(cores)>=90:observations.append({'step':row['id'],'fact':'busy_cpu_core_observed','max_percent':max(cores),'conclusion':'possible_cpu_pressure_not_proven'})
        if busy and max(busy)>=90:observations.append({'step':row['id'],'fact':'busy_library_disk_observed','max_percent':max(busy),'conclusion':'possible_io_pressure_not_proven'})
    return {'observations':observations,'causal_conclusion':'needs_analysis',
            'limitations':['whole_host_counters_include_other_activities','initial_cache_state_unknown','no_forced_cold_model','sampling_can_miss_peaks',
                          'capacity_occupied_is_not_proof_of_bottleneck','disk_counters_may_include_multiple_mounts','paging_counters_not_available_on_all_platforms','no_automatic_hardware_purchase_recommendation']}


async def run(report,user):
    start=time.monotonic();sampler=asyncio.create_task(samples(report,start))
    try:
        async with asyncio.timeout(DEADLINE):
            report['current_step']='baseline';report['current_phase']='idle';await asyncio.sleep(BASELINE)
            for query in QUERIES:
                for repeat in (1,2):
                    row={'id':'search-'+str(len(report['steps'])+1),'kind':'classical','query':query,'repeat':repeat,'cache_state':'initial_unknown' if repeat==1 else 'repeat_without_clearing'}
                    await step(row,report,classical(row,report),180)
            ai_reason=None
            try:await ai_guard()
            except calibration.Abort as error:ai_reason=str(error)
            if not ai_reason:
                runtime=await model_runtime.describe(engine.OLLAMA,report['model'],fresh=True)
                if not runtime.get('available') or not runtime.get('installed'):ai_reason='model_not_installed'
                report['initial_model']={k:runtime.get(k) for k in ('version','native_context','running','other_models','installed','available')}
            for kind in ('generation','documentary'):
                for repeat in (1,2):
                    row={'id':kind+'-'+str(repeat),'kind':kind,'repeat':repeat,'cache_state':'initial_unknown' if repeat==1 else 'repeat_without_clearing'}
                    if ai_reason:row.update(status='not_run',reason=ai_reason);report['steps'].append(row);continue
                    call=generation(row,report) if kind=='generation' else documentary_trial(row,report,user)
                    await step(row,report,call,600 if kind=='generation' else 920,guard=True)
                    if row.get('reason') in ('paused','engine_unavailable','other_activity','model_not_installed'):ai_reason=row['reason']
            row={'id':'selected-documentary','kind':'selected_documentary','repeat':1,'selected_count':len(report.get('_selected',[]))}
            if ai_reason or not report.get('_selected'):
                row.update(status='not_run',reason=ai_reason or 'no_search_candidates');report['steps'].append(row)
            else:await step(row,report,documentary_trial(row,report,user),920,guard=True)
            gaps=any(row.get('status')!='completed' or row.get('coverage_limit') for row in report['steps'])
            report.update(status='completed',reason='completed_with_gaps' if gaps else 'completed')
    except asyncio.CancelledError:report.update(status='cancelled',reason=report.pop('_cancel_reason','user_cancelled'))
    except TimeoutError:report.update(status='interrupted',reason='time_limit')
    except Exception:report.update(status='failed',reason='measurement_failed')
    finally:
        sampler.cancel();await asyncio.gather(sampler,return_exceptions=True)
        for key in list(report):
            if key.startswith('_'):report.pop(key,None)
        for row in report['steps']:
            if row.get('status')=='running':row.update(status='interrupted',reason=report.get('reason','measurement_failed'))
        report.update(finished=time.time(),elapsed_ms=round((time.monotonic()-start)*1000),current_step=None,current_phase=None)
        report['analysis']=interpretation(report)
        try:save(report)
        finally:ACTIVE.pop(report['id'],None);REPORTS.pop(report['id'],None)


async def step(row,report,call,timeout,guard=False):
    started=time.monotonic();row.update(status='running',started_ms=round((started-report['_monotonic'])*1000))
    report['steps'].append(row);report['current_step']=row['id'];report['current_phase']=row['kind']
    try:await watch(call,timeout,guard=guard);row['status']='completed'
    except calibration.Abort as error:row.update(status='failed',reason=str(error))
    except model_session.Failure as error:row.update(status='failed',reason=error.kind)
    except TimeoutError:row.update(status='failed',reason='timeout')
    except (httpx.HTTPError,ValueError,OSError):row.update(status='failed',reason='measurement_failed')
    finally:
        row['elapsed_ms']=round((time.monotonic()-started)*1000)
        save({k:v for k,v in report.items() if not k.startswith('_')})


async def start(mode,user,version):
    if mode not in engine.MODES:raise HTTPException(400,'Mode inconnu.')
    if running() or competing() or engine.LOCK.locked():raise HTTPException(409,'Une réponse ou un essai est déjà en cours. Attendez sa fin.')
    recover_temporary_job()
    report={'schema':1,'kind':'SetupSurvie performance diagnostic','protocol':1,'version':version,'id':uuid.uuid4().hex,'created':time.time(),
            'status':'running','mode':mode,'planned_steps':11,'model':engine.MODES[mode]['model'],'think':engine.MODES[mode]['think'],'configured_context':engine.context_size(engine.MODES[mode]['model']),
            'settings':{'maximum_seconds':DEADLINE,'sample_interval_seconds':INTERVAL,'search_budget_seconds':120,'generation_output_tokens':512,
                        'documentary_output_tokens':engine.PROFILE_CONFIG['output_tokens'],'cache_cleared':False,'model_unloaded':False},'steps':[],'samples':[]}
    save(report);report['_monotonic']=time.monotonic();REPORTS[report['id']]=report
    ACTIVE[report['id']]=asyncio.create_task(run(report,user));return status()


async def cancel(reason='user_cancelled'):
    tasks=list(ACTIVE.values())
    for report in REPORTS.values():report['_cancel_reason']=reason
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)
    # A task cancelled before its first scheduling does not execute its finally.
    for identifier,report in list(REPORTS.items()):
        if identifier in ACTIVE and ACTIVE[identifier].done():
            report={k:v for k,v in report.items() if not k.startswith('_')}
            report.update(status='cancelled',reason=reason,finished=time.time());save(report)
            ACTIVE.pop(identifier,None);REPORTS.pop(identifier,None)
    return status()
