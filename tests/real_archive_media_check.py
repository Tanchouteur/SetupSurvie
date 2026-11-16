"""Opt-in PyAV range-read check; requires an existing tiny synthetic MP4.

No model, transcription or external network. Run in the isolated R7 environment.
"""
import argparse
from fractions import Fraction
import hashlib
import http.server
import json
from pathlib import Path
import re
import struct
import sys
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pilot.archive_media import RangeReader

OPTIONS={'format_whitelist':'mov,matroska,webm,avi,mpeg,mpegts,ogg,asf,flv','protocol_whitelist':''}


def run(video):
    import av
    original=video.read_bytes()
    if len(original)>2_000_000 or video.suffix.lower()!='.mp4':raise ValueError('Only an existing tiny synthetic MP4 is accepted.')
    padding=8*1024*1024;data=original+struct.pack('>I4s',padding+8,b'free')+bytes(padding)
    identity=str(uuid.uuid4());requests=[];secondary=[];current={'data':data}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            requests.append(self.path)
            if self.path=='/catalog/v2/entry/'+identity:
                body=('<entry><id>urn:uuid:'+identity+'</id><link type="text/html" href="/content/fixture"/></entry>').encode()
                self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
            if self.path!='/content/fixture/media/clip.mp4':self.send_error(404);return
            match=re.fullmatch(r'bytes=(\d+)-(\d+)',self.headers.get('Range',''))
            if not match:self.send_error(416);return
            first,last=map(int,match.groups());body=current['data'][first:last+1]
            self.send_response(206);self.send_header('Content-Range',f'bytes {first}-{last}/{len(current["data"])}')
            self.send_header('Content-Type','video/mp4');self.send_header('Content-Length',str(len(body)));self.send_header('ETag','"fixture"');self.end_headers();self.wfile.write(body)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    source={'endpoint':f'http://127.0.0.1:{server.server_port}','uuid':identity,'book':'fixture','path':'media/clip.mp4','size':len(data)}
    def deny(url,flags,options):secondary.append(url);raise OSError('secondary_reference_refused')
    def inspect(container):
        audio=container.streams.audio[0];container.seek(int(Fraction(58,1)/audio.time_base),stream=audio,backward=True,any_frame=False)
        frames=[]
        for frame in container.decode(audio):
            frames.append({'time':frame.time,'samples':frame.samples,'sample_rate':frame.sample_rate})
            if len(frames)==4:break
        return {'duration_ms':round(container.duration/1000),'audio_codec':audio.codec_context.name,'frames':frames}
    try:
        with av.open(str(video),mode='r') as container:expected=inspect(container)
        began=time.monotonic()
        with RangeReader(source) as reader:
            with av.open(reader,mode='r',options=dict(OPTIONS),io_open=deny) as container:observed=inspect(container)
            metrics=dict(reader.metrics)
        assert observed==expected,(observed,expected)
        assert 57<=observed['frames'][0]['time']<=58.1,observed
        assert metrics['media_bytes']<len(data)//2,metrics
        assert metrics['largest_range_bytes']<=256*1024,metrics
        assert not secondary,secondary
        current['data']=b'#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nhttps://external.invalid/audio.ts\n#EXT-X-ENDLIST\n'
        rejected=False;source['size']=len(current['data'])
        with RangeReader(source) as reader:
            try:
                with av.open(reader,mode='r',format='hls',options=dict(OPTIONS),io_open=deny):pass
            except av.error.FFmpegError:rejected=True
        assert rejected and not secondary,'Secondary protocol/playlist was not refused before I/O.'
        return {'passed':True,'av':av.__version__,'source_sha256':hashlib.sha256(original).hexdigest(),'original_bytes':len(original),'padded_bytes':len(data),
            'padding':'synthetic free MP4 atom, not actual high-bitrate footage','duration_ms':observed['duration_ms'],'audio_codec':observed['audio_codec'],
            'frames_after_seek':observed['frames'],'media_io':metrics,'elapsed_ms':round((time.monotonic()-began)*1000),'playlist_refused':rejected,
            'secondary_requests':len(secondary),'real_asr':False,'real_corpus':False,'simulated_kiwix_http':True}
    finally:server.shutdown();server.server_close();thread.join(5)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--video',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run(args.video);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
