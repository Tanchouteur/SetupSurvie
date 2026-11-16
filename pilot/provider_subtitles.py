"""YouTube caption selection and checked timing conversion.

No network call at import or from identity/normalization. The provider library
is optional and already included in the product's pinned Open WebUI image.
"""
import math
import re
from urllib.parse import parse_qs,urlsplit

ID=re.compile(r'[A-Za-z0-9_-]{11}')
LANG=re.compile(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*')


def video_id(value):
    if not isinstance(value,str):raise ValueError('invalid_video_reference')
    value=value.strip()
    if ID.fullmatch(value):return value
    if len(value)>2000:raise ValueError('invalid_video_reference')
    parsed=urlsplit(value)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError('invalid_video_reference')
    host=(parsed.hostname or '').lower();path=parsed.path.strip('/').split('/')
    if host in ('youtu.be','www.youtu.be') and len(path)==1:identifier=path[0]
    elif host in ('youtube.com','www.youtube.com','m.youtube.com'):
        if parsed.path=='/watch':
            values=parse_qs(parsed.query).get('v',[])
            if len(values)!=1:raise ValueError('invalid_video_reference')
            identifier=values[0]
        elif len(path)==2 and path[0] in ('shorts','embed','live'):identifier=path[1]
        else:raise ValueError('invalid_video_reference')
    else:raise ValueError('invalid_video_reference')
    if not ID.fullmatch(identifier):raise ValueError('invalid_video_reference')
    return identifier


def identity(payload,supplied=''):
    if supplied:return {'id':video_id(supplied),'basis':'user_reference'}
    source=payload.get('source') or {}
    if not isinstance(source,dict):raise ValueError('source_reference_required')
    extractor=str(source.get('extractor') or '').lower()
    if extractor in ('youtube','youtube:video') and ID.fullmatch(str(source.get('id') or '')):
        return {'id':source['id'],'basis':'source_metadata'}
    try:return {'id':video_id(source.get('url')),'basis':'source_url'}
    except ValueError:raise ValueError('source_reference_required') from None


def metadata(transcript):
    language=transcript.language_code
    if not isinstance(language,str) or not LANG.fullmatch(language):raise ValueError('invalid_provider_language')
    return {'language':language,'name':str(transcript.language)[:120],'origin':'automatic' if transcript.is_generated else 'provided'}


def choose(tracks,preferred=''):
    """Prefer an available French track, then the declared speech language.

    Human tracks take priority within the same language. No online machine
    translation is requested implicitly; another language can use our local model.
    """
    if not tracks:raise ValueError('no_provider_captions')
    preferred=preferred.lower().split('-')[0]
    def rank(track):
        language=metadata(track)['language'].lower().split('-')[0]
        return (0 if language=='fr' else 1 if language==preferred else 2 if language=='en' else 3,
                bool(track.is_generated),language)
    return sorted(tracks,key=rank)[0]


def checked_cues(rows):
    """Keep every word, make overlapping provider display intervals explicit.

    Rows sharing a start are joined. Other overlaps shorten display time only;
    the original provider payload stays private beside this normalized track.
    """
    if not isinstance(rows,list) or not rows or len(rows)>100000:raise ValueError('invalid_provider_cues')
    cues=[];characters=0;adjustments=[];previous=-1
    for position,row in enumerate(rows):
        if not isinstance(row,dict):raise ValueError('invalid_provider_cues')
        start,duration=row.get('start'),row.get('duration');text=row.get('text')
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in (start,duration)) or start<0 or duration<=0:raise ValueError('invalid_provider_timing')
        start_ms=round(start*1000);end_ms=round((start+duration)*1000)
        if not isinstance(text,str) or not text.strip() or '\x00' in text or len(text)>6000 or start_ms<previous or not start_ms<end_ms<=30*24*3600000:
            raise ValueError('invalid_provider_cues')
        characters+=len(text)
        if characters>5_000_000:raise ValueError('provider_caption_too_large')
        if cues and cues[-1]['start_ms']==start_ms:
            cues[-1]['text']+='\n'+text.strip();cues[-1]['end_ms']=max(cues[-1]['end_ms'],end_ms)
            if len(cues[-1]['text'])>6000:raise ValueError('provider_caption_too_large')
            adjustments.append({'position':position,'kind':'same_start_joined'})
        else:
            if cues and cues[-1]['end_ms']>start_ms:
                adjustments.append({'position':position-1,'kind':'display_end_clipped','original_end_ms':cues[-1]['end_ms'],'end_ms':start_ms})
                cues[-1]['end_ms']=start_ms
            cues.append({'start_ms':start_ms,'end_ms':end_ms,'text':text.strip()})
        previous=start_ms
    return cues,adjustments


def retrieve(identifier,preferred='',language='',origin=''):
    """Explicit Internet operation. Never loads a model or downloads a video.

    Failures have bounded reason codes; provider errors/URLs/cookies do not
    become public messages. The original rows are for a private job report.
    """
    import importlib.metadata
    identifier=video_id(identifier)
    if language and not LANG.fullmatch(language):raise ValueError('invalid_provider_language')
    if origin not in ('','provided','automatic'):raise ValueError('invalid_provider_origin')
    try:
        import requests
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:raise ValueError('provider_tool_unavailable') from None

    class PublicSession(requests.Session):
        def send(self,request,**kwargs):
            target=urlsplit(request.url);host=(target.hostname or '').lower()
            if target.scheme!='https' or not (host=='youtube.com' or host.endswith('.youtube.com')) or target.username or target.password or target.port not in (None,443):
                raise ValueError('unexpected_provider_endpoint')
            kwargs.update(timeout=(10,15),stream=True)
            response=super().send(request,**kwargs)
            try:
                chunks=[];size=0
                for chunk in response.iter_content(65536):
                    size+=len(chunk)
                    if size>20_000_000:raise ValueError('provider_response_too_large')
                    chunks.append(chunk)
                response._content=b''.join(chunks);response._content_consumed=True
                return response
            finally:response.close()

    try:
        with PublicSession() as session:
            session.trust_env=False;session.max_redirects=4
            transcripts=list(YouTubeTranscriptApi(http_client=session).list(identifier))
            if len(transcripts)>1000:raise ValueError('provider_response_too_large')
            descriptions=[metadata(track) for track in transcripts]
            if language:
                choices=[track for track in transcripts if track.language_code==language and (not origin or metadata(track)['origin']==origin)]
                if not choices:raise ValueError('provider_track_unavailable')
                selected=choose(choices,preferred)
            else:selected=choose(transcripts,preferred)
            raw=selected.fetch().to_raw_data();cues,adjustments=checked_cues(raw)
            return {'video_id':identifier,'provider':'youtube','tool_version':importlib.metadata.version('youtube-transcript-api'),
                'track':metadata(selected),'available_tracks':descriptions,'raw_provider_cues':raw,'cues':cues,'timing_adjustments':adjustments,
                'human_review':'not_performed','online_translation_requested':False}
    except Exception as error:
        reason=str(error) if isinstance(error,ValueError) and str(error) in (
            'invalid_provider_language','invalid_provider_origin','unexpected_provider_endpoint','provider_response_too_large',
            'provider_track_unavailable','no_provider_captions','invalid_provider_cues','invalid_provider_timing','provider_caption_too_large') else None
        if reason is None:
            name=type(error).__name__
            reason='provider_blocked' if name in ('RequestBlocked','IpBlocked','TooManyRequests') else 'provider_captions_unavailable' if name in (
                'TranscriptsDisabled','NoTranscriptFound','VideoUnavailable','VideoUnplayable','InvalidVideoId','AgeRestricted') else 'provider_unreachable'
        raise ValueError(reason) from None
