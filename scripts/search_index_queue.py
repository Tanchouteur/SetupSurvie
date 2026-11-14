"""Durable verified-content queue. No inference, subprocess or network in producers."""
from contextlib import contextmanager
from datetime import datetime
import json
import hashlib
from pathlib import Path
import time
import re

import setup
from delivery_paths import destination,locked

class SourceChanged(setup.SetupError):pass


DEFAULTS={'enabled':True,'start_hour':0,'end_hour':0,'workers':0}


def read(root):
    path=destination(Path(root),'catalog/search-index-queue.json')
    if not path.exists():return {'schema':1,'settings':dict(DEFAULTS),'pending':{},'completed':{},'hold':''}
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict) or value.get('schema')!=1 or not isinstance(value.get('pending'),dict) or not isinstance(value.get('completed'),dict):
        raise setup.SetupError('File d’indexation illisible ; conservez les fichiers et relancez le diagnostic.')
    if not isinstance(value.get('settings',{}),dict):raise setup.SetupError('Réglages de préparation illisibles.')
    value['settings']={**DEFAULTS,**value.get('settings',{})}
    options=value['settings']
    if type(options['enabled']) is not bool or any(type(options[k]) is not int or not 0<=options[k]<=23 for k in ('start_hour','end_hour')) or type(options['workers']) is not int or not 0<=options['workers']<=16:raise setup.SetupError('Réglages de préparation non valides.')
    for relative,record in value['pending'].items():
        if not relative.startswith('library/zim/') or not relative.endswith('.zim') or not isinstance(record,dict) or not re.fullmatch('[a-f0-9]{64}',str(record.get('sha256',''))) or type(record.get('bytes')) is not int or type(record.get('mtime_ns')) is not int:raise setup.SetupError('Entrée de file d’indexation non valide.')
        destination(Path(root),relative)
    return value


@contextmanager
def edit(root):
    root=Path(root)
    with locked(destination(root,'catalog/search-index-queue.lock')):
        value=read(root);yield value
        setup.write_json(destination(root,'catalog/search-index-queue.json'),value,private=True)


def enqueue(root,item):
    relative=item.get('path','')
    if not relative.startswith('library/zim/') or not relative.endswith('.zim'):return
    target=destination(root,relative)
    if not target.is_file() or target.is_symlink():raise setup.SetupError('Archive vérifiée introuvable pour préparer sa recherche.')
    stat=target.stat()
    with edit(root) as value:
        completed=value['completed'].get(relative)
        if isinstance(completed,str) and completed==item['sha256']:return
        if isinstance(completed,dict) and (completed.get('sha256'),completed.get('bytes'),completed.get('mtime_ns'))==(item['sha256'],stat.st_size,stat.st_mtime_ns):
            key=hashlib.sha256(target.name.encode()).hexdigest()[:24]
            if completed.get('kind')=='kiwix_index' or (Path(root)/'state/pilot/archive-index'/(key+'.sqlite')).is_file():return
        if value.get('hold')=='source_changed' and value.get('last_problem')==relative:
            value['hold']='';value.pop('last_problem',None)
        previous=value['pending'].get(relative,{})
        if (previous.get('sha256'),previous.get('bytes'),previous.get('mtime_ns'))==(item['sha256'],stat.st_size,stat.st_mtime_ns):return
        value['pending'][relative]={'sha256':item['sha256'],'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'queued_at':time.time()}


def settings(root,body):
    if set(body)-set(DEFAULTS):raise setup.SetupError('Réglage d’indexation inconnu.')
    for name,value in body.items():
        if name=='enabled' and type(value) is not bool:raise setup.SetupError('Activation non valide.')
        if name in ('start_hour','end_hour') and (type(value) is not int or not 0<=value<=23):raise setup.SetupError('Heure entre 0 et 23 attendue.')
        if name=='workers' and (type(value) is not int or not 0<=value<=16):raise setup.SetupError('Choisissez automatique ou un à seize processus.')
    with edit(root) as value:value['settings'].update(body)


def in_window(options,now=None):
    hour=(now or datetime.now()).hour;start=options['start_hour'];end=options['end_hour']
    return start==end or (start<=hour<end if start<end else hour>=start or hour<end)


def hold(root,reason):
    with edit(root) as value:value['hold']=reason


def acknowledge(root,selection,report):
    done={r['archive']:r['status'] for r in report.get('results',[]) if r.get('status') in ('ready','kiwix_index')}
    with edit(root) as value:
        for relative,record in selection.items():
            path=destination(root,relative)
            if path.name not in done or value['pending'].get(relative)!=record or not path.is_file():continue
            stat=path.stat()
            if stat.st_size!=record['bytes'] or stat.st_mtime_ns!=record['mtime_ns']:
                value['hold']='source_changed';value['last_problem']=relative;continue
            value['completed'][relative]={**record,'kind':done[path.name]};value['pending'].pop(relative,None)
        value['last_run']={k:report.get(k) for k in ('phase','completed','articles','started','workers')}


def summary(root):
    value=read(root)
    return {'settings':value['settings'],'pending':len(value['pending']),'completed':len(value['completed']),
            'hold':value.get('hold',''),'last_run':value.get('last_run')}


def gaming(work):
    marker=Path(work)/'inference-paused.json'
    if not marker.exists():return False
    try:reason=json.loads(marker.read_text(encoding='utf-8')).get('reason','')
    except (OSError,ValueError):return True
    return reason in ('user_gaming','gaming','game','mode_jeu')


def validate_selection(root,selection):
    for relative,record in selection.items():
        path=destination(root,relative)
        stat=path.stat() if path.is_file() and not path.is_symlink() else None
        if stat is None or (stat.st_size,stat.st_mtime_ns)!=(record['bytes'],record['mtime_ns']):
            with edit(root) as value:value['hold']='source_changed';value['last_problem']=relative
            raise SourceChanged('Une archive a changé après vérification ; sa préparation automatique est suspendue.')
