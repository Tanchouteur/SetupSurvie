"""Pinned real Kiwix with one tiny generated ZIM; no model or external corpus."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pilot import archive_media
from zim_video_fixture import create

ROOT=Path(__file__).resolve().parents[1]


def run():
    image=json.loads((ROOT/'deploy/versions.json').read_text())['images']['kiwix'];checks=[]
    def check(value,label):
        if not value:raise AssertionError(label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='.kiwix-search-video-',dir=ROOT) as temporary:
        folder=Path(temporary);archive=folder/'filename-copy.zim';book=archive.stem;media=(ROOT/'tests/fixtures/video/solid-green.webm').read_bytes();create(archive,media=media)
        compose=folder/'compose.yaml';compose.write_text('services:\n  kiwix:\n    image: '+image+'\n    user: "0:0"\n    entrypoint: ["/usr/local/bin/kiwix-serve"]\n    volumes:\n      - '+json.dumps(str(folder)+':/data:ro')+'\n    command: '+json.dumps(['--port=8080','/data/'+archive.name])+'\n')
        command=(['task-compose'] if shutil.which('task-compose') else ['docker','compose','--project-name','setupsurvie-video-'+uuid.uuid4().hex[:10]])+['-f',str(compose)]
        def get(path,range_header=None,extra_headers=None):
            extras=''.join(key+': '+value+'\r\n' for key,value in (extra_headers or {}).items())
            request=('GET '+path+' HTTP/1.0\r\nHost: 127.0.0.1:8080\r\n'+('Range: '+range_header+'\r\n' if range_header else '')+extras+'Connection: close\r\n\r\n').encode()
            result=subprocess.run([*command,'exec','-T','kiwix','nc','-w','5','127.0.0.1','8080'],input=request,cwd=ROOT,capture_output=True,timeout=20)
            if result.returncode or b'\r\n\r\n' not in result.stdout:raise ValueError('Synthetic Kiwix HTTP request failed: '+result.stderr.decode(errors='replace')[-1000:])
            headers,body=result.stdout.split(b'\r\n\r\n',1);headers=headers.decode(errors='replace')
            return body,headers
        try:
            subprocess.run([*command,'up','-d'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
            for _ in range(50):
                try:
                    _,headers=get('/catalog/v2/entries?count=1')
                    if '200' in headers:break
                except ValueError:time.sleep(.1)
            else:raise AssertionError('Tiny Kiwix fixture did not become ready')
            body,headers=get('/content/'+book+'/media/clip.webm');check(body==media,'Native media path serves exactly the original WebM')
            check(bool(re.search(r'Content-Type:\s*video/webm',headers,re.I)),'Media MIME type is video/webm')
            body,headers=get('/content/'+book+'/media/clip.webm','bytes=3-16')
            check('206' in headers and body==media[3:17],'Kiwix serves an actual seek byte range')
            check(bool(re.search(r'Content-Range:\s*bytes 3-16/'+str(len(media)),headers,re.I)),'The range identifies the original media size')
            _,headers=get('/content/'+book+'/tracks/alias.vtt');check('302' in headers and '/tracks/en.vtt' in headers,'Subtitle alias redirects within the same archive')
            body,_=get('/content/'+book+'/tracks/en.vtt');check(b'Fictional 17 mm.' in body,'Canonical subtitle path keeps the expected text')
            body,_=get('/content/'+book+'/A/course.html');check(b'<video>' in body,'The source article remains independently readable')
            from libzim.reader import Archive
            identity=str(Archive(archive).uuid)
            entry,_=get('/catalog/v2/entry/'+identity)
            check(b'<name>video-fixture</name>' in entry and book!='video-fixture','A different filename remains usable independently of the embedded archive name')
            class KiwixTransport(httpx.BaseTransport):
                def handle_request(self,request):
                    body,raw=get(request.url.raw_path.decode('ascii'),request.headers.get('range'),
                        {key:request.headers[key] for key in ('Accept-Encoding','If-Range') if key in request.headers})
                    lines=raw.splitlines();headers={key.strip():value.strip() for line in lines[1:] if ':' in line for key,value in [line.split(':',1)]}
                    return httpx.Response(int(lines[0].split()[1]),headers=headers,stream=httpx.ByteStream(body))
            descriptor={'endpoint':'http://kiwix:8080','book':book,'path':'media/clip.webm','size':len(media),'uuid':identity}
            with patch.object(archive_media,'BLOCK',32),archive_media.RangeReader(descriptor,transport=KiwixTransport()) as reader:
                check(reader.read(7)==media[:7],'Product reader accepts the actual catalogue identity and first bytes')
                reader.seek(-14,2);check(reader.read(14)==media[-14:],'Product reader seeks with real ranges and consistent ETag')
                reader_metrics=dict(reader.metrics)
            receipt={'passed':True,'kiwix_image':image,'archive_bytes':archive.stat().st_size,'media_bytes':len(media),'media_sha256':hashlib.sha256(media).hexdigest(),
                'checks':checks,'real_corpus':False,'real_model':False,'browser_decode':'separate_browser_recipe','reader_metrics':reader_metrics,
                'transport':'HTTP bytes passed through nc inside the pinned service; no simulated responses'}
        finally:subprocess.run([*command,'down','--volumes','--remove-orphans'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();receipt=run()
    if args.output:args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps(receipt,ensure_ascii=False))
