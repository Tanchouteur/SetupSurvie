"""Shared, human-reviewed reading dossiers. No generated procedural instructions."""
import asyncio
import json
import re
import uuid

from fastapi import HTTPException
from . import catalogue,inventory,learning,library,source_metadata,store

PREFIX='dossier:v1:'


def config():
    value=json.loads(learning.RULES.read_text(encoding='utf-8'))
    return value['practical_dossiers'],value['practical_sections']


def definition(identifier):
    dossiers,sections=config()
    item=next((d for d in dossiers if d['id']==identifier),None)
    if item is None:raise HTTPException(404,'Dossier introuvable.')
    return item,sections


def read(db,identifier):
    row=db.execute('SELECT value FROM settings WHERE key=?',(PREFIX+identifier,)).fetchone()
    if row is None:return {'schema':1,'revision':0,'evidence':[]}
    try:
        raw=row['value']
        if len(raw)>256000:raise ValueError()
        value=json.loads(raw)
        if value['schema']!=1 or type(value['revision']) is not int or not isinstance(value['evidence'],list) or len(value['evidence'])>24:raise ValueError()
        _,sections=definition(identifier);allowed={s['id'] for s in sections}
        records=[]
        for row in value['evidence']:
            if not re.fullmatch('[a-f0-9]{32}',row['id']) or not re.fullmatch('[a-f0-9]{64}',row['source_revision']):raise ValueError()
            if not row['source_id'].startswith(('guide:','zim:','video:')) or not row['sections'] or not set(row['sections'])<=allowed:raise ValueError()
            catalogue.canonical(row['source_id'])
            if any(not isinstance(row[k],str) or len(row[k])>limit for k,limit in [('note',700),('locator',200),('title',400)]):raise ValueError()
            records.append({**{k:row[k] for k in ('id','source_id','source_revision','sections','note','locator','title')},
                            'language':str(row.get('language',''))[:30],'provenance':str(row.get('provenance',''))[:300],
                            'is_ai_translation':bool(row.get('is_ai_translation')),**source_metadata.metadata(row)})
        return {'schema':1,'revision':value['revision'],'evidence':records}
    except (ValueError,KeyError,TypeError,HTTPException):raise HTTPException(503,'Les repères de ce dossier ne sont pas lisibles. Les documents restent accessibles ; conservez une sauvegarde avant réparation.')


def dossier(identifier):
    item,sections=definition(identifier)
    with store.connect() as db:saved=read(db,identifier)
    evidence=[]
    for row in saved['evidence']:
        current=catalogue.revision(row['source_id'],library.GUIDES,inventory.ZIMS)
        evidence.append({**row,'state':'reviewed' if current==row['source_revision'] else 'source_changed' if current else 'unavailable'})
    covered={section for row in evidence if row['state']=='reviewed' for section in row['sections']}
    return {**item,'revision':saved['revision'],'sections':[{**s,'has_reviewed_reference':s['id'] in covered} for s in sections],
            'evidence':evidence,'reviewed_sections':len(covered),'total_sections':len(sections),
            'notice':'Les repères renvoient à des passages examinés par la famille. Les autres points restent à documenter.'}


def overview():
    dossiers,_=config();result=[]
    for item in dossiers:
        try:
            detail=dossier(item['id']);result.append({**item,**{k:detail[k] for k in ('reviewed_sections','total_sections')}})
        except HTTPException:result.append({**item,'reviewed_sections':None,'total_sections':None,'state':'unavailable'})
    return {'dossiers':result,'notice':'Six objectifs pour organiser les documents et repérer les informations manquantes.'}


async def search(identifier):
    item,_=definition(identifier);found={};coverage=[]
    for query in item['queries']:
        try:
            result=await asyncio.wait_for(library.search(query,limit=6,domain='resilience'),timeout=20)
            info=getattr(result,'coverage',{})
            coverage.append({'query':query,'status':info.get('status','unknown'),'warning':info.get('warning','')[:2000]})
            for row in result[:6]:
                found.setdefault(row['id'],{k:row[k] for k in ('id','title','language','excerpt','kind','classification') if k in row})
        except Exception:coverage.append({'query':query,'status':'unavailable','warning':'Cette recherche n’a pas abouti. Cela ne prouve pas que le sujet est absent.'})
    return {'results':list(found.values())[:12],'coverage':coverage,
            'notice':'Résultats à ouvrir et examiner. Un titre ou une mention du sujet ne prouvent pas la présence d’une procédure.'}


async def save(identifier,source_id,expected_source,expected_dossier,sections,note,locator,reviewed):
    _,definition_sections=definition(identifier)
    if not reviewed or not sections or len(set(sections))!=len(sections) or not set(sections)<={s['id'] for s in definition_sections}:raise HTTPException(400,'Choisissez les points réellement examinés dans le document.')
    if not isinstance(note,str) or not note.strip() or len(note)>700 or not isinstance(locator,str) or not locator.strip() or len(locator)>200:raise HTTPException(400,'Ajoutez un bref repère et la page ou section où le retrouver.')
    if not source_id.startswith(('guide:','zim:','video:')):raise HTTPException(400,'Référence de document invalide.')
    catalogue.canonical(source_id)
    if catalogue.revision(source_id,library.GUIDES,inventory.ZIMS)!=expected_source:raise HTTPException(409,'Le fichier a changé ou est absent. Rouvrez le document avant d’ajouter ce repère.')
    source=await library.source(source_id)
    # Check again after network reading, without overwriting a newer family edit.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        saved=read(db,identifier)
        if saved['revision']!=expected_dossier:raise HTTPException(409,'Le dossier a été modifié dans un autre onglet. Rechargez-le avant d’enregistrer.')
        if catalogue.revision(source_id,library.GUIDES,inventory.ZIMS)!=expected_source:raise HTTPException(409,'Le fichier a changé pendant sa lecture. Rouvrez-le avant d’enregistrer.')
        prior=next((e for e in saved['evidence'] if e['source_id']==source_id and e['locator']==locator.strip()),None)
        if not prior and len(saved['evidence'])>=24:raise HTTPException(409,'Ce dossier contient déjà 24 repères. Retirez un ancien repère avant de poursuivre.')
        entry={'id':prior['id'] if prior else uuid.uuid4().hex,'source_id':source_id,'source_revision':expected_source,
               'title':str(source['title'])[:400],'language':source.get('language',''),'sections':sections,
               'note':note.strip(),'locator':locator.strip(),'provenance':str(source.get('provenance',''))[:300],
               'is_ai_translation':bool(source.get('is_ai_translation')),**source_metadata.metadata(source)}
        if prior:saved['evidence'].remove(prior)
        saved['evidence'].append(entry);saved['revision']+=1
        db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(PREFIX+identifier,json.dumps(saved,ensure_ascii=False)))
    return dossier(identifier)


def remove(identifier,entry_id,expected):
    definition(identifier)
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE');saved=read(db,identifier)
        if saved['revision']!=expected:raise HTTPException(409,'Le dossier a changé. Rechargez-le avant de retirer ce repère.')
        if not any(e['id']==entry_id for e in saved['evidence']):raise HTTPException(404,'Repère introuvable.')
        saved['evidence']=[e for e in saved['evidence'] if e['id']!=entry_id];saved['revision']+=1
        db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(PREFIX+identifier,json.dumps(saved,ensure_ascii=False)))
    return dossier(identifier)


def export():
    dossiers,_=config()
    return {'schema':1,'kind':'SetupSurvie practical reading dossiers','notice':'Repères humains communs et références seulement. Aucune validation de procédure.',
            'dossiers':[dossier(d['id']) for d in dossiers]}
