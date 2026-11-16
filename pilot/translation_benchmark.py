"""Voluntary 40-page PDF translation measurement, private and resumable.

Uses shared PDF extraction, chunks, inference and quality checks. Its source and
outputs never become documents, conversations or automatic publications.
"""
import asyncio
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import textwrap
import time
import uuid

import httpx
from fastapi import HTTPException
from . import calibration,document_text,durable,engine,operations,performance,store,translation_quality,translations

ACTIVE={}
REPORTS={}
PAGES=40
INTERVAL=5
DEADLINE=8*3600
REASONS={'completed':'Les 40 pages sont traduites. Téléchargez le rapport pour analyser les durées.',
    'user_cancelled':'Essai mis en pause. Les passages terminés restent conservés.',
    'service_restarted':'Essai interrompu par le redémarrage. Reprenez explicitement.',
    'paused':'Le moteur est en pause. Reprenez l’essai après son démarrage volontaire.',
    'engine_unavailable':'Le moteur est indisponible. Les passages terminés restent conservés.',
    'other_activity':'Une autre utilisation de l’IA est prioritaire. Reprenez l’essai plus tard.',
    'quality_blocked':'Un contrôle technique a refusé la traduction d’un passage. Le rapport conserve l’échec.',
    'translation_failed':'Un passage n’a pas pu être traduit. Les mesures et passages terminés restent conservés.',
    'time_limit':'Cette session atteint huit heures. Reprenez explicitement pour continuer.',
    'preparation_failed':'Le PDF d’essai n’a pas pu être préparé ou vérifié.',
    'fixture_changed':'Les fichiers d’essai ont changé. Les résultats sont conservés, mais la reprise est refusée.'}


def running():return any(not task.done() for task in ACTIVE.values())
def location():return store.ROOT/'translation-benchmark/latest.json'


def directory(identifier):
    if not isinstance(identifier,str) or not re.fullmatch('[a-f0-9]{32}',identifier):raise ValueError('Invalid benchmark identity')
    root=location().parent/identifier
    for part in (store.ROOT,location().parent,root):
        if part.exists() and part.is_symlink():raise ValueError('Benchmark links are not allowed')
    return root


def save(report):
    value={key:val for key,val in report.items() if not key.startswith('_')}
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
    durable.write_bytes(directory(report['id'])/'report.json',raw,private=True)
    durable.write_bytes(location(),raw,private=True)


def load():
    if REPORTS:return next(iter(REPORTS.values()))
    try:
        if location().stat().st_size>40_000_000:raise ValueError()
        report=json.loads(location().read_text())
        if report.get('schema')!=1 or report.get('protocol')!=1:raise ValueError()
        if report.get('status')=='running':
            report.update(status='paused',reason='service_restarted');save(report)
        return report
    except (OSError,ValueError):return {'schema':1,'status':'not_started','parts':[],'samples':[],'pages':PAGES,'pages_done':0}


def status(full=False):
    report=load()
    result={key:value for key,value in report.items() if not key.startswith('_') and (full or key not in ('samples','parts'))}
    result.update(sample_count=len(report.get('samples',[])),host_sample_count=sum(bool(s.get('available')) for s in report.get('samples',[])))
    result['message']=REASONS.get(report.get('reason'),'Traduction des pages en cours…' if report.get('status')=='running' else 'Aucun essai lancé.')
    if report.get('_session_start'):
        result['active_elapsed_ms']=report.get('active_elapsed_ms',0)+round((time.monotonic()-report['_session_start'])*1000)
    return result


def competing():
    if engine.ACTIVE or translations.ACTIVE or calibration.running() or calibration.summary_activity() or calibration.caption_activity() or performance.running():return True
    speech=sys.modules.get(__package__+'.transcriptions')
    if speech and speech.running():return True
    experiment=sys.modules.get(__package__+'.search_experiment')
    return bool(experiment and experiment.running())


async def guard():
    if competing():raise calibration.Abort('other_activity')
    state=await operations.status(fresh=True)
    if state.get('paused'):raise calibration.Abort('paused')
    if not state.get('online') or state.get('operation'):raise calibration.Abort('engine_unavailable')


def page_text(number):
    # Fixed protocol, varied pages and paragraphs. No family documents, outside
    # copyright, practical recommendation, repeated padding or hidden instruction.
    topics=['the quiet village','the imaginary archive','a family exhibition','the painted garden',
        'the old theatre','a school story','the village library','the fictional workshop']
    paragraphs=[
        f'Page {number}. This fictional story describes {topics[(number-1)%len(topics)]}. It is a language exercise written for a software measurement. The people and places are invented. It does not provide instructions for real equipment or an actual emergency.',
        'The narrator visits a room where neighbours collect drawings, letters and descriptions of ordinary life. Each person explains what a favourite object means. The reader can compare these accounts without treating one memory as a complete history of the place.',
        'During the morning, a child describes the colours of an imaginary window. A visitor asks why the blue panel is different from the green panel. The teacher records both descriptions and keeps the questions beside the drawings for the next discussion.',
        'In the afternoon, the group reads a short tale about friendship and patience. They separate events described by the narrator from ideas suggested by the listeners. An unfinished sentence remains unfinished rather than being silently completed from an unrelated story.',
        'At the end of the meeting, the volunteers arrange the pages in a folder. The original wording remains available beside any later translation. Nobody claims that a translation or a drawing proves that the fictional scene took place outside the exercise.',
        f'The page marker is {number} and the invented reference is {1000+number}. These labels identify this part of the measurement. Do not change the two labels or invent additional measurements. The next page describes a different moment in the same fictional setting.'
    ]
    return '\n\n'.join(paragraphs)


def prepare(identifier):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
    root=directory(identifier);writer=PdfWriter()
    for number in range(1,PAGES+1):
        page=writer.add_blank_page(width=595,height=842)
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
        lines=[]
        for paragraph in page_text(number).split('\n\n'):lines.extend(textwrap.wrap(paragraph,94)+[''])
        commands=['BT /F1 10 Tf 42 795 Td 14 TL']
        for line in lines:
            escaped=line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            commands.append('('+escaped+') Tj T*')
        commands.append('ET');stream=DecodedStreamObject();stream.set_data('\n'.join(commands).encode('ascii'));page[NameObject('/Contents')]=stream
    output=io.BytesIO();writer.write(output);body=output.getvalue()
    durable.write_bytes(root/'source.pdf',body,private=True)
    parts=[];pages=document_text.pdf_texts(root/'source.pdf')
    for number,text in pages:
        if not text.strip():raise ValueError('Empty fixture page')
        for chunk in document_text.chunks(text):parts.append({'position':len(parts),'page':number,'source':chunk,'status':'pending','translated':None,'rejected':[]})
    if len(pages)!=PAGES:raise ValueError('Wrong fixture page count')
    raw=json.dumps(parts,ensure_ascii=False).encode();durable.write_bytes(root/'work.json',raw,private=True)
    return parts,{'pages':len(pages),'parts':len(parts),'bytes':len(body),'source_characters':sum(len(p['source']) for p in parts),
        'source_words':sum(len(p['source'].split()) for p in parts),'sha256':hashlib.sha256(body).hexdigest(),
        'text_sha256':hashlib.sha256(''.join(p['source'] for p in parts).encode()).hexdigest(),'kind':'generated_fictional_pdf','chunk_characters':2200}


def work(report):
    root=directory(report['id'])
    for name in ('work.json','source.pdf'):
        if (root/name).is_symlink():raise ValueError('Changed fixture')
    parts=json.loads((root/'work.json').read_text())
    if hashlib.sha256((root/'source.pdf').read_bytes()).hexdigest()!=report['fixture']['sha256'] or hashlib.sha256(''.join(p['source'] for p in parts).encode()).hexdigest()!=report['fixture']['text_sha256']:
        raise ValueError('Changed fixture')
    if len(parts)!=report['fixture']['parts'] or sum(len(p['source'].split()) for p in parts)!=report['fixture']['source_words']:raise ValueError('Changed fixture')
    return parts


def progress(report,parts):
    report.update(parts_done=sum(p['status']=='done' for p in parts),pages_done=sum(all(p['status']=='done' for p in parts if p['page']==n) for n in range(1,PAGES+1)),
        source_words_done=sum(len(p['source'].split()) for p in parts if p['status']=='done'),warnings=sum(p.get('quality',{}).get('status')=='warning' for p in parts))


async def sample(report):
    total=sum(len(json.dumps(row)) for row in report['samples'])
    while True:
        started=time.monotonic()
        try:value=await operations.performance()
        except Exception:value={'available':False,'reason':'controller_unavailable'}
        row={'active_elapsed_ms':report.get('active_elapsed_ms',0)+round((time.monotonic()-report['_session_start'])*1000),
            'session':len(report['sessions']),'page':report.get('current_page'),'part':report.get('current_part'),**value}
        size=len(json.dumps(row))
        if len(report['samples'])<6000 and total+size<24_000_000:report['samples'].append(row);total+=size
        else:report['dropped_samples']=report.get('dropped_samples',0)+1
        await asyncio.sleep(max(.1,INTERVAL-(time.monotonic()-started)))


async def generate(text,mode,metrics):
    task=asyncio.create_task(translations.translate(text,mode,on_metrics=metrics))
    try:
        async with asyncio.timeout(900):
            while not task.done():
                await asyncio.wait({task},timeout=1)
                if not task.done():await guard()
            return await task
    finally:
        if not task.done():task.cancel()
        await asyncio.gather(task,return_exceptions=True)


async def run(report):
    report['_session_start']=time.monotonic();session={'started':time.time(),'mode':report['mode'],'model':report['model'],
        'requested_context':engine.context_size(report['model']),'output_tokens':engine.PROFILE_CONFIG['output_tokens']};report['sessions'].append(session)
    sampler=asyncio.create_task(sample(report));parts=None
    try:
        async with asyncio.timeout(DEADLINE):
            await guard()
            if not report.get('fixture'):
                started=time.monotonic();task=asyncio.create_task(asyncio.to_thread(prepare,report['id']))
                try:parts,fixture=await asyncio.shield(task)
                except asyncio.CancelledError:
                    await asyncio.shield(task);raise
                report.update(fixture=fixture,preparation_ms=round((time.monotonic()-started)*1000));save(report)
            else:
                try:parts=await asyncio.to_thread(work,report)
                except (ValueError,OSError):raise calibration.Abort('fixture_changed') from None
            progress(report,parts)
            for part in parts:
                if part['status']=='done':continue
                await guard()
                report.update(current_page=part['page'],current_part=part['position']+1);save(report)
                waiting=time.monotonic()
                async with engine.LOCK:
                    await guard()
                    row={'page':part['page'],'position':part['position'],'session':len(report['sessions']),'status':'running',
                        'source_words':len(part['source'].split()),'source_characters':len(part['source']),'queue_ms':round((time.monotonic()-waiting)*1000)}
                    report['parts'].append(row);started=time.monotonic()
                    def metrics(value):row['metrics']=performance.numeric_metrics(value)
                    try:
                        result,model=await generate(part['source'],report['mode'],metrics)
                        await guard()
                        checked=translation_quality.assess(part['source'],result)
                        row.update(quality={'version':checked['version'],'status':checked['status'],'issues':[{'code':issue['code'],'severity':issue['severity']} for issue in checked['issues']]},
                            output_characters=len(result),output_words=len(result.split()))
                        if checked['status']=='blocked':
                            part['rejected'].append({'candidate':result,'quality':checked});row['status']='blocked'
                            durable.write_bytes(directory(report['id'])/'work.json',json.dumps(parts,ensure_ascii=False).encode(),private=True)
                            raise calibration.Abort('quality_blocked')
                        part.update(status='done',translated=result,quality=checked,model=model)
                        durable.write_bytes(directory(report['id'])/'work.json',json.dumps(parts,ensure_ascii=False).encode(),private=True)
                        row['status']='done';progress(report,parts)
                    except asyncio.CancelledError:row.update(status='interrupted',reason='cancelled');raise
                    except calibration.Abort as error:
                        if row['status']=='running':row.update(status='interrupted',reason=str(error))
                        raise
                    except (ValueError,httpx.HTTPError,HTTPException,TimeoutError) as error:
                        row.update(status='failed',reason='timeout' if isinstance(error,TimeoutError) else 'translation_failed')
                        raise calibration.Abort('translation_failed') from None
                    except Exception:
                        row.update(status='failed',reason='translation_failed')
                        raise
                    finally:row['elapsed_ms']=round((time.monotonic()-started)*1000);save(report)
                await asyncio.sleep(0)
            report.update(status='completed',reason='completed')
    except asyncio.CancelledError:report.update(status='paused',reason=report.pop('_cancel_reason','user_cancelled'))
    except calibration.Abort as error:report.update(status='paused',reason=str(error))
    except TimeoutError:report.update(status='paused',reason='time_limit')
    except Exception:report.update(status='failed',reason='preparation_failed' if not report.get('fixture') else 'translation_failed')
    finally:
        sampler.cancel();await asyncio.gather(sampler,return_exceptions=True)
        session.update(finished=time.time(),elapsed_ms=round((time.monotonic()-report['_session_start'])*1000),status=report['status'],reason=report['reason'])
        report['active_elapsed_ms']=report.get('active_elapsed_ms',0)+session['elapsed_ms']
        report.pop('_session_start',None);report.pop('_cancel_reason',None)
        report.update(updated=time.time(),wall_elapsed_ms=round((time.time()-report['created'])*1000),current_page=None,current_part=None)
        if report.get('source_words_done') and report['active_elapsed_ms']>0:report['source_words_per_minute']=round(report['source_words_done']*60000/report['active_elapsed_ms'],2)
        if parts:
            report['page_timings']=[{'page':n,'complete':all(p['status']=='done' for p in parts if p['page']==n),
                'attempts':sum(row['page']==n for row in report['parts']),'elapsed_ms':sum(row.get('elapsed_ms',0)+row.get('queue_ms',0) for row in report['parts'] if row['page']==n)} for n in range(1,PAGES+1)]
        try:save(report)
        finally:ACTIVE.pop(report['id'],None);REPORTS.pop(report['id'],None)


def launch(report):
    REPORTS[report['id']]=report;ACTIVE[report['id']]=asyncio.create_task(run(report))


async def start(mode,version):
    if mode not in engine.MODES:raise HTTPException(400,'Choisissez un mode IA connu.')
    if running() or competing() or engine.LOCK.locked():raise HTTPException(409,'Une autre utilisation de l’IA est en cours. Attendez sa fin.')
    try:await guard()
    except calibration.Abort as error:raise HTTPException(409,REASONS[str(error)]) from None
    report={'schema':1,'protocol':1,'kind':'SetupSurvie 40-page translation diagnostic','id':uuid.uuid4().hex,'version':version,
        'created':time.time(),'status':'running','mode':mode,'model':engine.MODES[mode]['model'],'pages':PAGES,'pages_done':0,'parts_done':0,
        'parts':[],'samples':[],'sessions':[],'active_elapsed_ms':0,'source_words_done':0,
        'settings':{'maximum_session_seconds':DEADLINE,'sample_interval_seconds':INTERVAL,'context':engine.context_size(engine.MODES[mode]['model']),
            'output_tokens':engine.PROFILE_CONFIG['output_tokens'],'model_unloaded':False,'cache_cleared':False,'published':False},
        'limitations':['fictional_pdf_not_a_real_manual','no_semantic_fidelity_certificate','no_images_or_ocr','whole_host_counters','initial_cache_state_unknown','sampling_can_miss_peaks']}
    save(report);launch(report);return status()


async def pause(reason='user_cancelled'):
    tasks=list(ACTIVE.values())
    for report in REPORTS.values():report['_cancel_reason']=reason
    for task in tasks:task.cancel()
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)
    for identifier,report in list(REPORTS.items()):
        if identifier in ACTIVE and ACTIVE[identifier].done():
            report.update(status='paused',reason=reason);save(report);ACTIVE.pop(identifier,None);REPORTS.pop(identifier,None)
    return status()


async def resume(mode=None):
    report=load()
    if report.get('status') not in ('paused','failed'):raise HTTPException(409,'Cet essai est déjà actif, terminé ou absent.')
    mode=mode or report['mode']
    if mode not in engine.MODES:raise HTTPException(400,'Mode IA inconnu.')
    if running() or competing() or engine.LOCK.locked():raise HTTPException(409,'Une autre utilisation de l’IA est en cours.')
    try:await guard()
    except calibration.Abort as error:raise HTTPException(409,REASONS[str(error)]) from None
    report.update(status='running',mode=mode,model=engine.MODES[mode]['model']);report.pop('reason',None)
    save(report);launch(report);return status()
