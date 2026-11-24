"""Private child process for bounded audio decoding/transcription, CPU by default.

JSON lines on stdin/stdout. The parent owns the process and can terminate it on
pause. Local files or configured Kiwix portions, preinstalled model, no download.
"""
from contextlib import contextmanager,redirect_stdout
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import sys
import time

RATE=16000
MODEL=None
MODEL_KEY=None


def local(path):
    path=Path(path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():raise ValueError('local_file_required')
    return path


def command_source(command):
    if 'archive' in command:
        if 'path' in command or not isinstance(command['archive'],dict):raise ValueError('invalid_media_reference')
        return command['archive']
    return command['path']


@contextmanager
def opened_media(source):
    import av
    if not isinstance(source,dict):
        with av.open(str(local(source)),mode='r') as container:yield container,{'source':'local_file','read_bytes_measured':False}
        return
    from .archive_media import ArchiveMediaError,DECODE_OPTIONS,RangeReader
    with RangeReader(source) as reader:
        def deny(url,flags,options):reader.fail('archive_secondary_reference_refused')
        try:
            # File-like input is supplied by our bounded reader. Refuse nested
            # protocols and playlists rather than delegate their I/O to FFmpeg.
            with av.open(reader,mode='r',options=dict(DECODE_OPTIONS),io_open=deny) as container:yield container,reader.metrics
        finally:
            if reader.failure:raise ArchiveMediaError(reader.failure)


def probe(path):
    with opened_media(path) as (container,media_io):
        streams=list(container.streams.audio)
        if not streams:return {'audio_present':False,'duration_ms':round(container.duration/1000) if container.duration else None,'media_io':dict(media_io)}
        stream=streams[0]
        duration=float(stream.duration*stream.time_base) if stream.duration is not None and stream.time_base else None
        offset=float(stream.start_time*stream.time_base) if stream.start_time is not None and stream.time_base else 0
        length=container.duration/1_000_000 if container.duration else None
        if duration is not None:length=max(length or 0,duration+max(0,offset))
        return {'audio_present':True,'duration_ms':round(length*1000) if length and math.isfinite(length) and length>0 else None,
            'audio_codec':stream.codec_context.name,'audio_start_ms':round(offset*1000),'sample_rate':stream.codec_context.sample_rate,
            'channels':stream.codec_context.channels,'media_io':dict(media_io)}


def decode_window(path,start_ms,end_ms):
    """Seek/decode one short interval, preserving the original media timeline."""
    import av
    import numpy as np
    if not 0<=start_ms<end_ms or end_ms-start_ms>64000:raise ValueError('invalid_window')
    size=math.ceil((end_ms-start_ms)*RATE/1000);audio=np.zeros(size,dtype=np.float32)
    decoded=0;frames=0;last_end=0;eof=True;timing_unknown=False
    with opened_media(path) as (container,media_io):
        if not container.streams.audio:raise ValueError('no_audio_stream')
        stream=container.streams.audio[0]
        # Seek in the audio stream: a sparse video keyframe can otherwise return
        # us to the beginning of a long film for every successive audio unit.
        if start_ms:
            if stream.time_base:container.seek(int(Fraction(max(0,start_ms-1000),1000)/stream.time_base),stream=stream,backward=True,any_frame=False)
            else:container.seek(max(0,start_ms-1000)*1000,backward=True,any_frame=False)
        resampler=av.AudioResampler(format='fltp',layout='mono',rate=RATE)
        for frame in container.decode(stream):
            frames+=1
            frame_time=float(frame.time) if frame.time is not None else None
            if frame_time is not None and frame_time*1000>=end_ms:
                eof=False;break
            for converted in resampler.resample(frame):
                when=float(converted.time) if converted.time is not None else frame_time
                if when is None:timing_unknown=True;continue
                values=converted.to_ndarray().reshape(-1).astype(np.float32)
                index=round(when*RATE-start_ms*RATE/1000);left=max(0,index);right=min(size,index+len(values))
                if right>left:
                    audio[left:right]=values[left-index:right-index];decoded+=right-left
                    last_end=max(last_end,round((when+len(values)/RATE)*1000))
        # Resamplers may buffer the final samples. Do not drop them at EOF.
        if eof:
            for converted in resampler.resample(None):
                if converted.time is None:timing_unknown=True;continue
                when=float(converted.time);values=converted.to_ndarray().reshape(-1).astype(np.float32)
                index=round(when*RATE-start_ms*RATE/1000);left=max(0,index);right=min(size,index+len(values))
                if right>left:
                    audio[left:right]=values[left-index:right-index];decoded+=right-left;last_end=max(last_end,round((when+len(values)/RATE)*1000))
    return audio,{'decoded_samples':decoded,'audio_frames':frames,'eof':eof,'last_decoded_ms':last_end,'timing_unknown':timing_unknown,'media_io':dict(media_io)}


def aligned_cues(segments,window_start,start,end):
    """Keep word midpoints in this unit. Adjacent units have overlapping context.

    Recognition timestamps are estimates, never a synchronization certificate.
    Word boundaries are clipped to this unit, so its published cues cannot overlap
    those of the next unit. Raw segment times stay in the private result.
    """
    cues=[];raw=[];warnings=[]
    for segment in segments:
        raw.append({'start_ms':round(segment.start*1000)+window_start,'end_ms':round(segment.end*1000)+window_start,
            'avg_logprob':float(segment.avg_logprob),'no_speech_probability':float(segment.no_speech_prob),
            'compression_ratio':float(segment.compression_ratio)})
        words=getattr(segment,'words',None)
        if words:
            selected=[]
            for word in words:
                left=round(word.start*1000)+window_start;right=round(word.end*1000)+window_start
                if start<=(left+right)/2<end and right>left:selected.append((max(start,left),min(end,right),word.word))
            if not selected:continue
            # Whisper may group words separated by a long silence into one
            # segment. Keep short readable cues instead of a 50-second subtitle.
            groups=[];group=[]
            for current in selected:
                if group and (current[0]-group[-1][1]>1200 or current[1]-group[0][0]>7000 or sum(len(w[2]) for w in group)+len(current[2])>110):
                    groups.append(group);group=[]
                group.append(current)
            if group:groups.append(group)
            for group in groups:
                text=''.join(word[2] for word in group).strip();left=group[0][0];right=group[-1][1]
                if not text or right<=left:continue
                add_cue(cues,warnings,left,right,text)
            continue
        else:
            warnings.append('word_timestamps_unavailable')
            left=round(segment.start*1000)+window_start;right=round(segment.end*1000)+window_start
            if not start<=(left+right)/2<end:continue
            left,right=max(start,left),min(end,right);text=segment.text.strip()
        if not text or right<=left:continue
        add_cue(cues,warnings,left,right,text)
    return cues,raw,sorted(set(warnings))


def add_cue(cues,warnings,left,right,text):
    """Retain overlapping ASR output as an anomaly, with a playable timeline.

    The unit check refuses overlapping cues; without this the same unit would
    fail at every resume. The later cue starts when the previous one ends, or
    joins it when nothing of its own time remains.
    """
    if cues and left<cues[-1]['end_ms']:
        warnings.append('recognition_overlap');left=cues[-1]['end_ms']
        if right<=left:
            cues[-1]['text']=(cues[-1]['text']+' '+text)[:6000];return
    cues.append({'start_ms':left,'end_ms':right,'text':text})


def transcribe(command):
    global MODEL,MODEL_KEY
    from faster_whisper import WhisperModel
    start,end=command['start_ms'],command['end_ms'];model_path=Path(command['model_path'])
    if not model_path.is_absolute() or model_path.is_symlink() or not model_path.is_dir():raise ValueError('local_model_required')
    for name in ('model.bin','config.json','tokenizer.json'):local(model_path/name)
    threads=int(command.get('threads',2))
    if not 1<=threads<=32:raise ValueError('invalid_threads')
    language=command.get('language') or None
    if language is not None and (not isinstance(language,str) or not language.isalpha() or not 2<=len(language)<=3):raise ValueError('invalid_language')
    window_start=max(0,start-2000);window_end=end+2000
    began=time.monotonic();samples,decode=decode_window(command_source(command),window_start,window_end)
    decode_ms=round((time.monotonic()-began)*1000)
    if decode['timing_unknown']:raise ValueError('audio_timestamps_unavailable')
    if not decode['decoded_samples']:return {**decode,'cues':[],'language':language,'decode_ms':decode_ms,'model_loaded':False,'warnings':['no_audio_decoded_in_window']}
    key=str(model_path),threads;loading=time.monotonic();loaded=MODEL_KEY!=key
    if loaded:
        MODEL=WhisperModel(str(model_path),device='cpu',compute_type='int8',cpu_threads=threads,num_workers=1,local_files_only=True)
        MODEL_KEY=key
    load_ms=round((time.monotonic()-loading)*1000)
    began=time.monotonic()
    segments,info=MODEL.transcribe(samples,language=language,task='transcribe',word_timestamps=True,vad_filter=True,
        condition_on_previous_text=False,beam_size=5,temperature=0)
    actual_end=min(end,decode['last_decoded_ms']) if decode['eof'] else end
    cues,raw,warnings=aligned_cues(segments,window_start,start,actual_end)
    return {**decode,'cues':cues,'raw_segments':raw,'language':info.language,'language_probability':float(info.language_probability),
        'decode_ms':decode_ms,'load_ms':load_ms,'recognition_ms':round((time.monotonic()-began)*1000),'model_loaded':loaded,
        'device':'cpu','compute_type':'int8','threads':threads,'warnings':warnings,'alignment':'word_midpoints_with_2s_context'}


def dispatch(command):
    if command.get('action')=='probe':return probe(command_source(command))
    if command.get('action')=='transcribe':return transcribe(command)
    raise ValueError('unknown_action')


def main():
    for line in sys.stdin:
        try:
            if len(line)>16000:raise ValueError('command_too_large')
            command=json.loads(line)
            # Model libraries may print initialization details; reserve stdout
            # for the bounded protocol and keep provider output out of the UI.
            with redirect_stdout(sys.stderr):result=dispatch(command)
            value={'ok':True,'result':result}
        except Exception as error:
            reason=str(error) if isinstance(error,ValueError) and str(error) in ('local_file_required','no_audio_stream','audio_timestamps_unavailable','local_model_required','invalid_window',
                'archive_reader_unavailable','archive_edition_unavailable','archive_media_range_unavailable','archive_media_redirect_refused','archive_media_response_invalid','archive_secondary_reference_refused') else 'audio_processing_failed'
            value={'ok':False,'reason':reason}
        sys.stdout.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');sys.stdout.flush()


if __name__=='__main__':main()
