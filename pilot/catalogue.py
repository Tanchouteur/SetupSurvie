"""Small human metadata overlay. Originals, search indexes and identifiers stay intact."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote

from fastapi import HTTPException
from . import retrieval, store

PREFIX='catalogue:v1:'
DOMAINS={'resilience','culture'}
TYPES={'unknown','overview','explanation','procedure','exercise','manual'}


def canonical(identifier):
    if not isinstance(identifier,str) or len(identifier)>2000 or not identifier.startswith(('guide:','zim:','collection:')):
        raise HTTPException(400,'Référence documentaire invalide.')
    kind,path=identifier.split(':',1)
    if kind=='guide':path=re.sub(r'#page=\d+$','',path)
    for _ in range(3):
        decoded=unquote(path)
        if decoded==path:break
        path=decoded
    if not path or path.startswith('/') or '\\' in path or re.search(r'%[0-9a-f]{2}|[\x00-\x1f]',path,re.I) or any(part in ('','.','..') for part in path.split('/')):
        raise HTTPException(400,'Référence documentaire invalide.')
    if kind=='collection' and '/' in path:raise HTTPException(400,'Référence de collection invalide.')
    return kind+':'+path


def revision(identifier,guides,zims):
    key=canonical(identifier);kind,path=key.split(':',1)
    root=Path(guides if kind=='guide' else zims)
    relative=path if kind=='guide' else path.split('/')[0]+'.zim'
    target=root/relative
    try:
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root.resolve()):return None
        stat=target.stat()
        return hashlib.sha256(('stat-v1:'+relative+':'+str(stat.st_size)+':'+str(stat.st_mtime_ns)).encode()).hexdigest()
    except OSError:return None


class Snapshot(dict):
    def __init__(self,*args,available=True,**kwargs):super().__init__(*args,**kwargs);self.available=available


def valid_record(key,value):
    if not isinstance(value,dict) or value.get('schema')!=1 or not re.fullmatch('[a-f0-9]{64}',str(value.get('revision',''))):return False
    try:
        if canonical(key)!=key:return False
    except HTTPException:return False
    if key.startswith('collection:'):
        return all(isinstance(value.get(k),str) and 0<len(value[k])<=n for k,n in [('family',80),('variant',120)])
    return isinstance(value.get('domains'),list) and len(value['domains'])<=2 and len(set(value['domains']))==len(value['domains']) and all(d in DOMAINS for d in value['domains']) and value.get('document_type') in TYPES and value.get('status') in ('corrected','reviewed')


def snapshot():
    result=Snapshot()
    try:
        with store.connect() as db:
            rows=db.execute('SELECT key,value FROM settings WHERE key LIKE ? LIMIT 10001',(PREFIX+'%',)).fetchall()
        if len(rows)>10000:return Snapshot(available=False)
        for row in rows:
            key=row['key'][len(PREFIX):]
            try:
                value=json.loads(row['value'])
                if valid_record(key,value):
                    fields=('schema','revision','family','variant') if key.startswith('collection:') else ('schema','revision','domains','document_type','status')
                    result[key]={name:value[name] for name in fields}
                else:result.available=False
            except (ValueError,TypeError):result.available=False
    except (OSError,sqlite3.DatabaseError):return Snapshot(available=False)
    return result


def classification(item,guides,zims,saved=None):
    saved=snapshot() if saved is None else saved
    try:key=canonical(item['id']);current=revision(key,guides,zims)
    except HTTPException:key='';current=None
    record=saved.get(key)
    automatic={'domains':retrieval.domains({**item,'_text':item.get('_text',item.get('text',''))}),'document_type':'exercise' if re.search(r'\b(quiz|qcm|questionnaire|exercices?|exercises?)\b',retrieval.normal(item.get('title',''))) else 'unknown',
               'method':'automatic','status':'unreviewed','revision':current,'has_correction':bool(record)}
    if record and current and record['revision']==current:
        return {**automatic,**{k:record[k] for k in ('domains','document_type','status')},'method':'human'}
    if record:automatic['status']='source_changed'
    return automatic


def annotate(items,guides,zims,saved=None):
    saved=snapshot() if saved is None else saved
    for item in items:
        info=classification(item,guides,zims,saved)
        item['classification']=info;item['domains']=info['domains']
    return saved.available


def save(identifier,values,expected,guides,zims):
    key=canonical(identifier);current=revision(key,guides,zims)
    if current is None:raise HTTPException(404,'Le fichier source n’est pas disponible pour ce classement.')
    if current!=expected:raise HTTPException(409,'Le fichier a changé. Rouvrez-le avant de modifier son classement.')
    record={'schema':1,'revision':current,**values}
    if not valid_record(key,record):raise HTTPException(400,'Classement documentaire invalide.')
    with store.connect() as db:
        exists=db.execute('SELECT 1 FROM settings WHERE key=?',(PREFIX+key,)).fetchone()
        if not exists and db.execute('SELECT count(*) FROM settings WHERE key LIKE ?',(PREFIX+'%',)).fetchone()[0]>=10000:
            raise HTTPException(409,'La limite de corrections est atteinte. Exportez les métadonnées avant leur entretien.')
        db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(PREFIX+key,json.dumps(record,ensure_ascii=False)))
    return record


def reset(identifier):
    key=canonical(identifier)
    with store.connect() as db:db.execute('DELETE FROM settings WHERE key=?',(PREFIX+key,))


def export():
    saved=snapshot()
    if not saved.available:raise HTTPException(503,'Certaines métadonnées ne sont pas lisibles. La recherche reste disponible ; conservez la sauvegarde avant réparation.')
    return {'schema':1,'kind':'SetupSurvie documentary metadata','notice':'Libellés et classements seulement. Aucune validation de sécurité du contenu.',
            'records':[{'id':key,**record} for key,record in sorted(saved.items())]}


def automatic_labels(stem,title):
    match=re.match(r'^(.*?)_([a-z]{2,3}(?:,[a-z]{2,3})?)_(.*?)(?:_(\d{4}-\d{2}))?$',stem)
    prefix=match[1] if match else stem
    families={'wikipedia':'Wikipédia','wikibooks':'Wikilivres','vikidia':'Vikidia','appropedia':'Appropedia','canadian-prepper':'Canadian Prepper'}
    family=families.get(prefix,title if not match or retrieval.normal(prefix)==retrieval.normal(title) else prefix.replace('-',' '))
    raw=match[3].replace('-',' ') if match else ''
    names={'all':'Collection complète','all maxi':'Collection complète illustrée','all nopic':'Collection complète sans images',
           'preppingfood':'Alimentation','preppinggear':'Équipement','preppingsurvival':'Préparation et autonomie',
           'survival':'Survie et autonomie','food':'Alimentation','energy':'Énergie','water':'Eau','shelter':'Abri',
           'diy':'Fabrication et réparation','gardening':'Jardinage','repair':'Réparation','medical':'Santé'}
    variant=names.get(raw)
    if variant is None:
        # Prefer the actual catalogue title when it distinguishes the editions.
        variant=title if retrieval.normal(title) not in (retrieval.normal(family),retrieval.normal(stem)) else raw or stem
    return {'family':family,'variant':variant,'archive_name':stem+'.zim'}


def collection_labels(stem,title,guides,zims,saved=None):
    saved=snapshot() if saved is None else saved
    automatic=automatic_labels(stem,title);key=canonical('collection:'+stem);current=revision(key,guides,zims);record=saved.get(key)
    active=bool(record and current and record['revision']==current)
    return {**automatic,**({k:record[k] for k in ('family','variant')} if active else {}),
            'automatic_labels':automatic,'labels_status':'corrected' if active else 'source_changed' if record else 'automatic',
            'labels_revision':current,'labels_corrected':bool(record)}


def matches_collection(book,selection,guides,zims,saved=None):
    if selection.startswith('group:'):
        labels=collection_labels(book['book'],book.get('title',''),guides,zims,saved)
        return selection[6:]==retrieval.normal(labels['family']).replace(' ','')
    return selection in retrieval.normal(book.get('book','')+' '+str(book.get('title',''))).replace(' ','')
