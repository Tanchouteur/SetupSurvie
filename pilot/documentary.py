"""Observed documentary work, independent of prose. No source passages persisted."""
import json
import sqlite3

STATES={'not_run','complete','partial','unavailable','unknown'}
SCOPES={'library','targeted','favorites','mixed','document'}
COUNTERS=('searches','results','sources_read','failed_reads','partial_reads')


def clean_sources(raw):
    try:
        if isinstance(raw,str):
            if len(raw)>40000:return []
            raw=json.loads(raw)
        if not isinstance(raw,list):return []
        result=[];seen=set();size=2
        for item in raw[:12]:
            if not isinstance(item,dict):continue
            identifier,title=item.get('id'),item.get('title')
            if not isinstance(identifier,str) or not identifier.startswith(('guide:','zim:','video:')) or len(identifier)>2000 or identifier in seen:continue
            if not isinstance(title,str) or not title.strip():continue
            candidate={'id':identifier,'title':title[:400]}
            try:(identifier+candidate['title']).encode('utf-8')
            except UnicodeError:continue
            encoded=len(json.dumps(candidate))+1
            if size+encoded>40000:continue
            result.append(candidate);seen.add(identifier);size+=encoded
        return result
    except (ValueError,TypeError):return []


def clean(raw):
    try:
        if isinstance(raw,str):
            if len(raw)>2048:return None
            raw=json.loads(raw)
        if not isinstance(raw,dict) or type(raw.get('schema')) is not int or raw['schema']!=1:return None
        if raw.get('status') not in STATES or raw.get('scope') not in SCOPES:return None
        if any(type(raw.get(key)) is not int or not 0<=raw[key]<=10000 for key in COUNTERS):return None
        return {key:raw[key] for key in ('schema','status','scope',*COUNTERS)}
    except (ValueError,TypeError):return None


class Evidence:
    def __init__(self):self.searches={};self.found=set();self.reads=set();self.failed=set();self.partial=set();self.consulted={}

    def record(self,name,arguments,value,*,key=None):
        if not isinstance(value,dict):return
        if not isinstance(arguments,dict):arguments={}
        if name=='search_library':
            key=key if key is not None else json.dumps(arguments,sort_keys=True,ensure_ascii=False)
            scope='favorites' if arguments.get('favorites_only') is True else 'targeted' if arguments.get('collection') else 'library'
            coverage=value.get('coverage') or {};status=coverage.get('status','unknown') if isinstance(coverage,dict) else 'unknown'
            if scope=='library' and isinstance(coverage,dict) and coverage.get('domain') not in (None,'','all'):scope='targeted'
            if value.get('error'):status='unavailable'
            if not isinstance(status,str) or status not in STATES:status='unknown'
            if scope=='favorites' and status=='unknown' and not value.get('error'):status='complete'
            self.searches[key]=(status,scope)
            results=value.get('results');results=results if isinstance(results,list) else []
            for item in results[:12]:
                if isinstance(item,dict) and isinstance(item.get('id'),str):self.found.add(item['id'])
        elif name=='read_source':
            identifier=str(arguments.get('id',''));offset=arguments.get('offset',0)
            offset=offset if type(offset) is int else 0;part=(identifier,offset)
            if value.get('error') or not isinstance(value.get('text'),str) or not value['text'].strip():self.failed.add(part)
            else:
                actual=value.get('id') if isinstance(value.get('id'),str) else identifier
                self.reads.add(actual);self.failed.discard(part)
                source=clean_sources([{'id':actual,'title':value.get('title')}])
                if source and (actual in self.consulted or len(self.consulted)<12):self.consulted[actual]=source[0]
                if value.get('partial_read') or value.get('more') or value.get('text_limit_reached'):self.partial.add(actual)

    def summary(self):
        states=[value[0] for value in self.searches.values()];scopes={value[1] for value in self.searches.values()}
        status='not_run' if not states else 'complete' if all(s=='complete' for s in states) else 'unavailable' if all(s=='unavailable' for s in states) and not self.found else 'unknown' if all(s=='unknown' for s in states) else 'partial'
        if self.failed and status in ('not_run','complete'):status='partial'
        return {'schema':1,'status':status,'scope':next(iter(scopes)) if len(scopes)==1 else 'mixed' if scopes else 'document',
                'searches':len(self.searches),'results':len(self.found),'sources_read':len(self.reads),
                'failed_reads':len({identifier for identifier,_ in self.failed}),'partial_reads':len(self.partial)}

    def view(self):return {**self.summary(),'consulted_sources':list(self.consulted.values())}


def save(identifier,summary,*,sources=None,message_id=None,db=None):
    from . import store
    value=clean(summary)
    if value is None:return False
    def write(connection):
        result=connection.execute('''INSERT INTO documentary_evidence(job_id,conversation_id,message_id,summary,sources)
          SELECT id,conversation_id,?,?,? FROM jobs WHERE id=? AND
          (? IS NULL OR EXISTS(SELECT 1 FROM messages WHERE id=? AND conversation_id=jobs.conversation_id AND role='assistant'))
          ON CONFLICT(job_id) DO UPDATE SET summary=excluded.summary,sources=excluded.sources,
          message_id=COALESCE(excluded.message_id,documentary_evidence.message_id)''',
          (message_id,json.dumps(value),json.dumps(clean_sources(sources)),identifier,message_id,message_id))
        return result.rowcount==1
    try:
        if db is not None:return write(db)
        with store.connect() as connection:return write(connection)
    except (OSError,sqlite3.Error):return False


def for_job(identifier):
    from . import store
    try:
        with store.connect() as db:row=db.execute('SELECT summary,sources FROM documentary_evidence WHERE job_id=?',(identifier,)).fetchone()
        value=clean(row['summary']) if row else None
        return {**value,'consulted_sources':clean_sources(row['sources'])} if value else None
    except (OSError,sqlite3.Error):return None


def for_messages(conversation):
    from . import store
    try:
        with store.connect() as db:rows=db.execute('SELECT message_id,summary,sources FROM documentary_evidence WHERE conversation_id=? AND message_id IS NOT NULL',(conversation,)).fetchall()
        return {row['message_id']:{**value,'consulted_sources':clean_sources(row['sources'])} for row in rows if (value:=clean(row['summary'])) is not None}
    except (OSError,sqlite3.Error):return {}
