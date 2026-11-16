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
from zim_video_fixture import create

ROOT=Path(__file__).resolve().parents[1]


def run():
    image=json.loads((ROOT/'deploy/versions.json').read_text())['images']['kiwix'];checks=[]
    def check(value,label):
        if not value:raise AssertionError(label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='.kiwix-search-video-',dir=ROOT) as temporary:
        folder=Path(temporary);archive=folder/'video-fixture.zim';media=(ROOT/'tests/fixtures/video/solid-green.webm').read_bytes();create(archive,media=media)
        compose=folder/'compose.yaml';compose.write_text('services:\n  kiwix:\n    image: '+image+'\n    user: "0:0"\n    entrypoint: ["/usr/local/bin/kiwix-serve"]\n    volumes:\n      - '+json.dumps(str(folder)+':/data:ro')+'\n    command: ["--port=8080", "/data/video-fixture.zim"]\n')
        command=(['task-compose'] if shutil.which('task-compose') else ['docker','compose','--project-name','setupsurvie-video-'+uuid.uuid4().hex[:10]])+['-f',str(compose)]
        def get(path,range_header=None):
            request=('GET '+path+' HTTP/1.0\r\nHost: 127.0.0.1:8080\r\n'+('Range: '+range_header+'\r\n' if range_header else '')+'Connection: close\r\n\r\n').encode()
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
            body,headers=get('/content/video-fixture/media/clip.webm');check(body==media,'Native media path serves exactly the original WebM')
            check(bool(re.search(r'Content-Type:\s*video/webm',headers,re.I)),'Media MIME type is video/webm')
            body,headers=get('/content/video-fixture/media/clip.webm','bytes=3-16')
            check('206' in headers and body==media[3:17],'Kiwix serves an actual seek byte range')
            check(bool(re.search(r'Content-Range:\s*bytes 3-16/'+str(len(media)),headers,re.I)),'The range identifies the original media size')
            _,headers=get('/content/video-fixture/tracks/alias.vtt');check('302' in headers and '/tracks/en.vtt' in headers,'Subtitle alias redirects within the same archive')
            body,_=get('/content/video-fixture/tracks/en.vtt');check(b'Fictional 17 mm.' in body,'Canonical subtitle path keeps the expected text')
            body,_=get('/content/video-fixture/A/course.html');check(b'<video>' in body,'The source article remains independently readable')
            receipt={'passed':True,'kiwix_image':image,'archive_bytes':archive.stat().st_size,'media_bytes':len(media),'media_sha256':hashlib.sha256(media).hexdigest(),
                'checks':checks,'real_corpus':False,'real_model':False,'browser_decode':'separate_browser_recipe'}
        finally:subprocess.run([*command,'down','--volumes','--remove-orphans'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();receipt=run()
    if args.output:args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps(receipt,ensure_ascii=False))
