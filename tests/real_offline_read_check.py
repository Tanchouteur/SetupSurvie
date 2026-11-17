#!/usr/bin/env python3
"""Exercise real local read APIs while the container has only loopback."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx


def isolated_network():
    interfaces=sorted(path.name for path in Path('/sys/class/net').iterdir())
    if interfaces!=['lo']:
        raise RuntimeError('network_interfaces_not_loopback_only')
    lines=Path('/proc/net/route').read_text().splitlines()
    routes=[]
    for line in lines[1:]:
        fields=line.split()
        if len(fields)<8:raise RuntimeError('invalid_proc_net_route')
        interface,destination,gateway=fields[:3]
        if interface!='lo' or destination=='00000000' or gateway!='00000000':
            raise RuntimeError('non_loopback_route_present')
        routes.append(interface)
    return {'interfaces':interfaces,'route_entries':len(routes)}


def check(condition,name,checks):
    if not condition:raise RuntimeError('check_failed:'+name)
    checks.append(name)


def start_server(env,port):
    return subprocess.Popen([sys.executable,'-m','uvicorn','pilot.app:app','--host','127.0.0.1',
                             '--port',str(port),'--no-access-log'],env=env,
                            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


async def wait_ready(client,process):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError('pilot_process_exited')
        try:
            response=await client.get('/api/health',timeout=1)
            if response.status_code==200:return response.json()
        except httpx.HTTPError:pass
        await asyncio.sleep(.1)
    raise RuntimeError('pilot_start_timeout')


async def exercise(base,checks):
    timeout=httpx.Timeout(8,connect=1)
    async with httpx.AsyncClient(base_url=base,timeout=timeout) as client:
        health=await wait_ready(client,server)
        check(health.get('ok') is True,'http_health',checks)
        origin={'Origin':base}

        response=await client.get('/api/search',params={'q':'praxidrome','language':'fr','domain':'all'})
        response.raise_for_status();guide_results=response.json()['results']
        guide=next((item for item in guide_results if item.get('id')=='guide:fixture.fr.txt'),None)
        check(guide is not None,'guide_search',checks)
        response=await client.get('/api/source',params={'id':'guide:fixture.fr.txt'})
        response.raise_for_status()
        check('praxidrome' in response.json().get('text',''),'guide_source_read',checks)

        response=await client.post('/api/admin/videos/index',headers=origin)
        response.raise_for_status()
        deadline=time.monotonic()+20;report=None
        while time.monotonic()<deadline:
            response=await client.get('/api/admin/videos/report')
            response.raise_for_status();report=response.json()
            if report.get('phase') in ('completed','failed','paused'):break
            await asyncio.sleep(.1)
        check(report is not None and report.get('phase')=='completed' and report.get('videos')==1 and report.get('tracks')==1,
              'video_index',checks)

        response=await client.get('/api/search',params={'q':'vibratille','language':'fr','domain':'all'})
        response.raise_for_status()
        video=next((item for item in response.json()['results'] if item.get('kind')=='video' and item.get('match')=='subtitle'),None)
        check(video is not None,'subtitle_search',checks)
        video_id=video['id'].split(':',1)[1].split('#',1)[0]
        response=await client.get('/api/source',params={'id':video['id']})
        response.raise_for_status()
        check('vibratille' in response.json().get('text',''),'subtitle_source_read',checks)
        async with client.stream('GET','/api/videos/media',params={'id':video_id}) as streamed:
            streamed.raise_for_status();body=b''.join([chunk async for chunk in streamed.aiter_bytes()])
            media_type=streamed.headers.get('content-type','')
        check(media_type.startswith('video/mp4') and body==MEDIA_BYTES,'synthetic_mp4_http_stream',checks)
        response=await client.get('/api/videos/track',params={'id':video_id,'track':0})
        response.raise_for_status()
        check('WEBVTT' in response.text and 'vibratille' in response.text,'french_vtt_read',checks)

        response=await client.put('/api/favorites',headers=origin,json={'source_id':'guide:fixture.fr.txt'})
        response.raise_for_status()
        response=await client.get('/api/favorites',params={'language':'fr'})
        response.raise_for_status()
        check(any(item.get('id')=='guide:fixture.fr.txt' for item in response.json()['results']),
              'favorite_saved',checks)
        response=await client.post('/api/conversations',headers=origin,json={'source_ids':['guide:fixture.fr.txt']})
        response.raise_for_status();conversation=response.json()['conversation_id']
        check(conversation and response.json().get('selected_sources'),'conversation_created',checks)
    return health['version'],conversation


def stop(process):
    if process is None:return
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=2)


MEDIA_BYTES=b'\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2'
server=None
REPORT={'status':'not_started','version':None,'checks':[]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-isolated',action='store_true',required=True,
                        help='refuse to run unless only loopback and no default route are present')
    args=parser.parse_args()
    del args
    checks=REPORT['checks'];network=isolated_network();version=None
    REPORT.update(status='running',network=network)
    with tempfile.TemporaryDirectory(prefix='setupsurvie-offline-read-') as temporary:
        root=Path(temporary);state=root/'state';guides=root/'guides';videos=root/'videos';zims=root/'zims'
        for directory in (state,guides,videos,zims):directory.mkdir()
        guide='''Un guide local de démonstration décrit le praxidrome, terme fictif réservé à cet essai.\n'''
        (guides/'fixture.fr.txt').write_text(guide,encoding='utf-8')
        (guides/'metadata.json').write_text(json.dumps([{'path':'fixture.fr.txt','title':'Guide local fictif','language':'fr'}]),encoding='utf-8')
        media_path=videos/'fixture.mp4';media_path.write_bytes(MEDIA_BYTES)
        (videos/'fixture.info.json').write_text(json.dumps({'title':'Vidéo synthétique','description':'Fixture locale','duration':2,'language':'en'}),encoding='utf-8')
        (videos/'fixture.fr.vtt').write_text('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nSegment fictif vibratille.\n',encoding='utf-8')
        env=os.environ.copy();env.update({'PILOT_STATE_DIR':str(state),'GUIDES_DIR':str(guides),'VIDEO_DIR':str(videos),
            'ZIM_DIR':str(zims),'KIWIX_URL':'http://127.0.0.1:9','OLLAMA_URL':'http://127.0.0.1:9',
            'WEBUI_URL':'http://127.0.0.1:9','WEBUI_DB_PATH':str(root/'absent-webui.db'),
            'PILOT_CONTROL_URL':'http://127.0.0.1:9','PYTHONDONTWRITEBYTECODE':'1'})
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        global server
        server=start_server(env,port)
        version,conversation=asyncio.run(exercise(base,checks))
        REPORT['version']=version
        stop(server);server=None
        server=start_server(env,port)
        async def verify_restart():
            async with httpx.AsyncClient(base_url=base,timeout=httpx.Timeout(5,connect=1)) as client:
                health=await wait_ready(client,server)
                favorite=await client.get('/api/favorites',params={'language':'fr'});favorite.raise_for_status()
                check(any(item.get('id')=='guide:fixture.fr.txt' for item in favorite.json()['results']),
                      'favorite_survives_restart',checks)
                saved=await client.get('/api/conversations/'+conversation);saved.raise_for_status();data=saved.json()
                check(any(item.get('id')=='guide:fixture.fr.txt' for item in data.get('selected_sources',[])),
                      'conversation_sources_survive_restart',checks)
                check(health.get('version')==version,'version_stable_after_restart',checks)
        asyncio.run(verify_restart())
        stop(server);server=None
    REPORT.update(status='passed',count=len(checks),limits=['synthetic guide, MP4 bytes and VTT only',
        'MP4 transport checked without decoding','no model generation or inference',
        'not a physical Internet-cut, Windows, Safari, or Marc-content validation'])
    print(json.dumps(REPORT,ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except Exception as error:
        stop(server)
        REPORT.update(status='failed',error=str(error)[:240],count=len(REPORT['checks']))
        print(json.dumps(REPORT,ensure_ascii=False))
        raise SystemExit(1)
    finally:stop(server)
