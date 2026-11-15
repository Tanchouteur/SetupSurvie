"""Durable numerical timings; no prompt, answer, source text or private reasoning."""
from contextlib import contextmanager
import json
import math
import re
import time
from . import durable,store


def path(identifier):
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,100}',identifier):raise ValueError('Identifiant de mesure invalide.')
    return store.ROOT/'assistant-metrics'/(identifier+'.json')


def read(identifier):
    try:
        target=path(identifier)
        if target.stat().st_size>1_000_000:return None
        value=json.loads(target.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or value.get('schema')!=1:return None
        if 'documentary' in value:
            from . import documentary
            observed=documentary.clean(value['documentary'])
            if observed is None:value.pop('documentary')
            else:value['documentary']=observed
        return value
    except (OSError,ValueError):return None


def estimate_tokens(messages,tools=()):
    # Conservative estimate, not a tokenizer. Template overhead is reserved
    # separately; actual prompt_eval_count is recorded after each model call.
    return math.ceil(len(json.dumps({'messages':messages,'tools':tools},ensure_ascii=False).encode('utf-8'))/2)


def budget(context,output,tools=()):
    reserve=2048
    tool_tokens=estimate_tokens([],tools)
    return {'context':context,'output':output,'template_reserve':reserve,'tool_estimate':tool_tokens,
            'message_bytes':max(0,(context-output-reserve-tool_tokens)*2),'estimation':'utf8_bytes_divided_by_2'}


class Measurement:
    def __init__(self,identifier,model,mode,context):
        self.identifier=identifier;self.started=time.monotonic();self.stage_started=self.started;self.stage='queue';self.first_text=None
        self.value={'schema':1,'kind':'SetupSurvie assistant measurements','created':time.time(),'model':model,'mode':mode,
                    'requested_context':context,'context':context,'status':'running','phases_ms':{},'model_calls':[],'budgets':[],
                    'sources_found':0,'sources_read':0,'cache_hits':{'search':0,'read':0}}

    def phase(self,name):
        now=time.monotonic();durations=self.value['phases_ms'];durations[self.stage]=durations.get(self.stage,0)+round((now-self.stage_started)*1000)
        self.stage=name;self.stage_started=now

    @contextmanager
    def during(self,name):
        previous=self.stage;self.phase(name)
        try:yield
        finally:self.phase(previous)

    def text(self):
        if self.first_text is None:self.first_text=round((time.monotonic()-self.started)*1000)

    def model_call(self,event):
        data={key:event[key] for key in ('prompt_eval_count','prompt_eval_cached_count','eval_count') if type(event.get(key)) is int and event[key]>=0}
        data.update({key.removesuffix('_duration')+'_ms':round(event[key]/1_000_000) for key in ('load_duration','prompt_eval_duration','eval_duration','total_duration') if type(event.get(key)) is int and event[key]>=0})
        if event.get('done_reason') in ('stop','length','unload','load'):data['done_reason']=event['done_reason']
        self.value['model_calls'].append(data)

    def finish(self,status):
        self.phase('finished');self.value.update(status=status,total_ms=round((time.monotonic()-self.started)*1000),first_text_ms=self.first_text)
        try:durable.write_bytes(path(self.identifier),json.dumps(self.value,ensure_ascii=False).encode('utf-8'),private=True)
        except OSError:pass
        return self.value

    def live(self):
        value={**self.value,'phases_ms':dict(self.value['phases_ms'])}
        value['phases_ms'][self.stage]=value['phases_ms'].get(self.stage,0)+round((time.monotonic()-self.stage_started)*1000)
        value.update(total_ms=round((time.monotonic()-self.started)*1000),first_text_ms=self.first_text)
        return value
