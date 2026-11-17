#!/usr/bin/env python3
"""Simulated yt-dlp for tests: no network. Behaviour per video id in FAKE_YTDLP.

Scenarios: ok (media, info.json, fr/en subtitles), nosubs, private, partial
(leaves a .part file and fails, then succeeds on the next call), empty.
Every call is appended to FAKE_YTDLP_CALLS for inspection.
"""
import json
import os
from pathlib import Path
import sys

args=sys.argv[1:]
if args==['--version']:print('2099.01.01-fake');raise SystemExit(0)
with open(os.environ['FAKE_YTDLP_CALLS'],'a',encoding='utf-8') as calls:calls.write(json.dumps(args)+'\n')
plan=json.loads(Path(os.environ['FAKE_YTDLP']).read_text(encoding='utf-8'))
folder=Path(args[args.index('-P')+1]);url=args[-1];identifier=url.rsplit('=',1)[-1]
scenario=plan.get(identifier,{'kind':'ok'})
title=scenario.get('title','Vidéo fictive '+identifier);channel=scenario.get('channel','Chaîne fictive')
stem=f'{title} [{identifier}]'
if scenario['kind']=='private':
    print('ERROR: [youtube] '+identifier+': Private video. Sign in if you\'ve been granted access to this video',file=sys.stderr);raise SystemExit(1)
if scenario['kind']=='partial':
    marker=folder/'.attempted'
    if not marker.exists():
        marker.write_text('1');(folder/(stem+'.mp4.part')).write_bytes(b'half')
        print('ERROR: unable to download video data: <urlopen error [Errno 104] Connection reset by peer>',file=sys.stderr);raise SystemExit(1)
    marker.unlink()
if scenario['kind']=='empty':raise SystemExit(0)
(folder/(stem+'.info.json')).write_text(json.dumps({'id':identifier,'title':title,'channel':channel,'extractor':'youtube','language':'fr','duration':12,'height':360,
    'description':'Description fictive.','webpage_url':url}),encoding='utf-8')
if scenario['kind']!='nosubs':
    (folder/(stem+'.fr.vtt')).write_text('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nFrotter le bâton fictif.\n',encoding='utf-8')
    (folder/(stem+'.en.vtt')).write_text('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nRub the imaginary stick.\n',encoding='utf-8')
(folder/(stem+'.mp4.part')).unlink(missing_ok=True)
(folder/(stem+'.mp4')).write_bytes(b'\x00\x00\x00\x18ftypmp42fake-media')
print('[download] 100% of 18.00B')
