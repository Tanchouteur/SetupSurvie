#!/usr/bin/env python3
"""Real yt-dlp, Deno and FFmpeg on this OS, with a local HTTP video instead of YouTube.

Downloads only the pinned tools. Used by the Windows CI job; never needs a model.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import youtube_tools as tools
import youtube_videos as tool

VIDEO='aaaaaaaaaaa'


def check(condition,label):
    if not condition:raise SystemExit('ÉCHEC : '+label)
    print('OK :',label,flush=True)


def run(*args):return subprocess.run([str(item) for item in args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    temporary=Path(tempfile.mkdtemp(prefix='ss yt é '))
    server=None
    try:
        data=temporary/'données';data.mkdir()
        check(tools.prepare(data),'yt-dlp, Deno et FFmpeg préparés depuis les versions figées')
        state=tools.status(data);check(state['yt_dlp']==state['expected_yt_dlp'],'version de yt-dlp attendue : '+str(state['yt_dlp']))
        ffmpeg=tools.ffmpeg(data);probe=ffmpeg.with_name(ffmpeg.name.replace('ffmpeg','ffprobe'))
        verbose=run(tools.python(data),'-m','yt_dlp','-v','--simulate','--ignore-config','--ffmpeg-location',ffmpeg,'http://127.0.0.1:9/x')
        check('JS runtimes: deno-' in verbose.stderr,'yt-dlp détecte Deno');check('exe versions: ffmpeg' in verbose.stderr,'yt-dlp détecte FFmpeg')
        site=temporary/'site';site.mkdir()
        video,audio,merged=site/'v.mp4',site/'a.m4a',site/(VIDEO+'.mp4')
        for command in (['-f','lavfi','-i','testsrc=duration=2:size=320x240:rate=10','-c:v','mpeg4',video],['-f','lavfi','-i','sine=duration=2','-c:a','aac',audio],['-i',video,'-i',audio,'-c','copy','-map','0:v','-map','1:a',merged]):
            result=run(ffmpeg,'-hide_banner','-loglevel','error','-y',*command);check(result.returncode==0,'FFmpeg : '+(result.stderr[:200] or Path(str(command[-1])).name))
        streams=run(probe,'-v','error','-show_entries','stream=codec_type','-of','csv=p=0',merged).stdout.split()
        check(sorted(streams)==['audio','video'],'image et son assemblés sans réencodage')
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(site)));threading.Thread(target=server.serve_forever,daemon=True).start()
        entry={'id':VIDEO,'url':f'http://127.0.0.1:{server.server_port}/{VIDEO}.mp4','theme':'Thème é'}
        staging=data/'state/video-downloads/en-cours'/VIDEO;staging.mkdir(parents=True)
        args=tool.command([str(tools.python(data)),'-m','yt_dlp'],entry,staging,max_height=480,max_bytes=10_000_000,ffmpeg=ffmpeg)
        args[args.index('-f')+1]='b'
        code,output,paused=tool.execute(args);check(code==0 and not paused,'vrai yt-dlp : téléchargement local '+output[-200:].replace('\n',' ') if code else 'vrai yt-dlp : téléchargement local')
        media,sidecars=tool.finished_files(staging,VIDEO);check(media is not None and any(p.name.endswith('.info.json') for p in sidecars),'vidéo et .info.json terminés')
        library=data/'library/video';library.mkdir(parents=True)
        target,moved,info=tool.publish(media,sidecars,library,entry)
        check(target.is_file() and target.parent.name=='Thème é' and all(p.is_file() for p in moved),'fichiers rangés dans la bibliothèque')
        copy=temporary/'autre disque'/'données';shutil.copytree(data,copy,symlinks=True,ignore=shutil.ignore_patterns('site'));shutil.rmtree(tools.paths(copy)['venv'])
        def offline(*args,**kwargs):raise AssertionError('Accès réseau interdit après copie')
        check(tools.ensure(copy,opener=offline),'outils recréés hors ligne après copie vers un autre dossier')
        check(tools.status(copy)['ready'],'outils prêts après copie')
        print(json.dumps({'platform':sys.platform,'python':sys.version.split()[0],**tools.status(copy)},ensure_ascii=False))
    finally:
        if server:server.shutdown();server.server_close()
        shutil.rmtree(temporary,ignore_errors=True)


if __name__=='__main__':main()
