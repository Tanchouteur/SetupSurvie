"""Opt-in R7 check: existing synthetic MP4 in a tiny ZIM to real ASR/French.

Native archive/index, simulated loopback Kiwix HTTP, actual prepared models.
Never run in CI or download a model. The full report is private.
"""
import argparse
import asyncio
from contextlib import AsyncExitStack
import hashlib
import http.server
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import httpx
from pilot import archive_videos,captions,durable,engine,library,operations,store,transcriptions,videos,zim_video_inventory
from real_assistant_check import TestTransport
from zim_video_fixture import create


async def check(args):
    from libzim.reader import Archive
    original=httpx.AsyncClient;started=time.monotonic();pause_marker=args.pause_marker or args.cache.parent/'private/inference-paused.json'
    async def guard(**kwargs):
        if pause_marker.exists():return {'online':True,'paused':True,'message':'Pause utilisateur conservée.'}
        async with original(trust_env=False,timeout=5) as client:
            response=await client.get('http://127.0.0.1:11434/api/ps');response.raise_for_status()
            if any(row.get('name',row.get('model'))!=args.model for row in response.json().get('models',[])):raise RuntimeError('Another Ollama model is active.')
        free=int((await asyncio.to_thread(subprocess.check_output,['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)).splitlines()[0])
        if free<1536:raise RuntimeError('GPU reserve unavailable.')
        return {'online':True,'paused':False,'message':'Test isolated, resources checked.'}
    initial=await guard()
    if initial['paused']:raise RuntimeError('User pause is active.')
    free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0])
    if free<8192+1536:raise RuntimeError('Initial GPU allocation unavailable.')
    if args.report.exists() or args.media.suffix.lower()!='.mp4' or args.media.stat().st_size>2_000_000:raise RuntimeError('New report and existing tiny synthetic MP4 required.')
    if shutil.disk_usage(args.cache).free<1_000_000_000:raise RuntimeError('Temporary storage reserve unavailable.')
    source_hash=hashlib.sha256(args.media.read_bytes()).hexdigest();config=transcriptions.model_config
    def prepared():return {**config(),'threads':4}
    with tempfile.TemporaryDirectory(prefix='ss-real-archive-audio-') as folder:
        root=Path(folder);archives=root/'zim';archives.mkdir();video=root/'video';video.mkdir();source=archives/'fixture.zim'
        create(source,media=args.media.read_bytes(),with_tracks=False,extension='mp4');native=Archive(source);identity=str(native.uuid);requests=[]
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                requests.append(self.path)
                if self.path=='/catalog/v2/entry/'+identity:
                    data=('<entry><id>urn:uuid:'+identity+'</id><link type="text/html" href="/content/fixture"/></entry>').encode()
                    self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
                if self.path!='/content/fixture/media/clip.mp4':self.send_error(404);return
                data=bytes(native.get_entry_by_path('media/clip.mp4').get_item().content);match=re.fullmatch(r'bytes=(\d+)-(\d+)',self.headers.get('Range',''))
                if not match:self.send_error(416);return
                first,last=map(int,match.groups());body=data[first:last+1]
                self.send_response(206);self.send_header('Content-Type','video/mp4');self.send_header('ETag','"'+identity+'"')
                self.send_header('Content-Range',f'bytes {first}-{last}/{len(data)}');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        mode={'id':'real-archive-audio','name':'Archive audio test','model':args.model,'think':False};endpoint=f'http://127.0.0.1:{server.server_port}'
        snapshot={'job':None}
        async def stop_jobs():
            await transcriptions.stop_all();await captions.stop_all();await videos.stop()
        async def preserve_failure():
            if args.report.exists():return
            result=transcriptions.status(snapshot['job'],True) if snapshot['job'] else None
            translated=captions.status(result['translation_job'],full=True) if result and result.get('translation_job') else None
            durable.write_bytes(args.report,json.dumps({'phase':'recipe_interrupted','transcription':result,'translation':translated},ensure_ascii=False,indent=2).encode(),private=True)
        try:
            async with AsyncExitStack() as stack:
                for change in (patch.object(store,'ROOT',root/'state'),patch.object(videos,'ROOT',video),patch.object(archive_videos,'ZIMS',archives),
                     patch.object(library,'KIWIX',endpoint),patch.object(transcriptions,'MODEL_ROOT',args.cache),patch.object(transcriptions,'model_config',prepared),
                     patch.dict(engine.MODES,{'real-archive-audio':mode}),patch.object(engine,'OLLAMA','http://127.0.0.1:11434'),
                     patch.object(engine,'PROFILE_CONFIG',{**engine.PROFILE_CONFIG,'context':16384,'output_tokens':4096}),
                     patch.object(operations,'status',guard),patch.object(httpx,'AsyncClient',side_effect=lambda **kw:original(transport=TestTransport(4096,24,6),**kw))):stack.enter_context(change)
                stack.push_async_callback(preserve_failure);stack.push_async_callback(stop_jobs)
                store.init();videos.STOP.clear();inventory=zim_video_inventory.build(source,archive_videos.directory(),reserve=1_000_000);videos.scan()
                digest=hashlib.sha256(source.read_bytes()).hexdigest();identifier=videos.listing()['videos'][0]['id']
                job=await transcriptions.create(identifier,'en',mode['id'],True);snapshot['job']=job['id']
                paused=None;before_unit=None
                for _ in range(1800):
                    value=transcriptions.status(job['id'],True)
                    if value['units_done']>=1 and value['status'] in ('queued','running'):
                        paused=await transcriptions.pause(job['id']);before_unit=transcriptions.status(job['id'],True)['units'][0];break
                    if value['status'] in ('error','paused','completed'):break
                    await asyncio.sleep(.1)
                if not paused:
                    durable.write_bytes(args.report,json.dumps({'phase':'before_pause','real_native_archive':True,'transcription':value},ensure_ascii=False,indent=2).encode(),private=True)
                    raise RuntimeError('Cannot validate the first-unit pause; inspect the private report.')
                await transcriptions.resume(job['id']);await transcriptions.ACTIVE[job['id']]
                result=transcriptions.status(job['id'],True);translation=None
                if result['translation_job']:
                    if task:=captions.ACTIVE.get(result['translation_job']):await task
                    translation=captions.status(result['translation_job'],full=True)
                if videos.ACTIVE:await videos.ACTIVE
                indexed=videos.source(identifier)
                search_word='';matched=[]
                for word in re.findall(r'[^\W\d_]{5,}',indexed['text'],flags=re.UNICODE):
                    plan=library.retrieval.plan(word,library.search_terms(word),library.SYNONYMS)
                    if not plan.words:continue
                    found,_=videos.search(plan,'fr')
                    if any(item['id'].startswith(identifier) and item.get('transcription_origin')=='local_translation' for item in found):search_word=word;matched=found;break
                checks={'native_inventory':inventory['video_resources']==1,'audio_completed':result['status']=='completed','three_units':result['units_done']==3,
                    'pause_kept_first_unit':bool(paused['units_done']>=1),'first_unit_unchanged':result['units'][0]==before_unit,
                    'french_completed':bool(translation and translation['status']=='completed'),'french_indexed':indexed.get('language')=='fr',
                    'both_tracks':{track['origin'] for track in indexed['tracks']}=={'local_transcription','local_translation'},
                    'archive_original_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==digest,'mp4_original_unchanged':hashlib.sha256(args.media.read_bytes()).hexdigest()==source_hash,
                    'no_media_extracted':not list(video.iterdir()),'range_metrics':all(unit.get('media_io',{}).get('source')=='kiwix_byte_ranges' for unit in result['units']),
                    'french_search_match':bool(matched)}
                report={'schema':1,'version':json.loads((ROOT/'deploy/release.json').read_text())['version'],'elapsed_ms':round((time.monotonic()-started)*1000),
                    'source_digest':hashlib.sha256(b''.join(path.read_bytes() for path in sorted((ROOT/'pilot').glob('*.py')))).hexdigest(),
                    'recipe_digest':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'synthetic_audio':True,'real_native_archive':True,'simulated_kiwix_http':True,
                    'real_recognition':True,'real_translation':True,'customer_validation':False,'source_sha256':source_hash,'archive_bytes':source.stat().st_size,
                    'transcription':result,'translation':translation,'paused':paused,'indexed_source':indexed,'checks':checks,'search_word':search_word,'http_requests':len(requests),'human_semantic_review':'required_separately'}
                durable.write_bytes(args.report,json.dumps(report,ensure_ascii=False,indent=2).encode(),private=True)
                print(json.dumps({'elapsed_ms':report['elapsed_ms'],'checks':checks,'error':result['error'],'translation_error':translation.get('error') if translation else None}),flush=True)
                if not all(checks.values()):raise RuntimeError('Inspect the private report; this run has gaps.')
        finally:
            server.shutdown();server.server_close();thread.join(5);del native


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--media',type=Path,required=True);parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--model',required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--pause-marker',type=Path)
    asyncio.run(check(parser.parse_args()))
