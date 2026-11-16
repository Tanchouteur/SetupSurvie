"""Single bounded provider request. No output except the private JSON protocol."""
from contextlib import redirect_stdout
import json
import sys
from . import provider_subtitles


def main():
    try:
        line=sys.stdin.read(16001)
        if len(line)>16000:raise ValueError('invalid_video_reference')
        command=json.loads(line)
        with redirect_stdout(sys.stderr):result=provider_subtitles.retrieve(command['id'],command.get('preferred',''),command.get('language',''),command.get('origin',''))
        value={'ok':True,'result':result}
    except Exception as error:
        allowed={'provider_tool_unavailable','provider_blocked','provider_captions_unavailable','provider_unreachable','provider_track_unavailable',
            'provider_response_too_large','invalid_video_reference','invalid_provider_cues','invalid_provider_timing','invalid_provider_language',
            'unexpected_provider_endpoint','provider_caption_too_large','no_provider_captions'}
        value={'ok':False,'reason':str(error) if isinstance(error,ValueError) and str(error) in allowed else 'provider_unreachable'}
    sys.stdout.write(json.dumps(value,ensure_ascii=False,allow_nan=False));sys.stdout.flush()


if __name__=='__main__':main()
