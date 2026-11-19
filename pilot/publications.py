"""Publish French passages as independent, labelled local HTML guides.

No private conversation text, account identity or reasoning trace is published.
The public file survives deletion of its originating conversation.
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import time
from urllib.parse import quote

from fastapi import HTTPException
from . import durable, library, store

LOCK=asyncio.Lock()
NOTICE='Traduction IA non vérifiée. Comparez les nombres, unités, tableaux et consignes avec le document original. Les illustrations ne sont pas traduites.'


def reserve(db, identifier, user_id, source, auto_publish=False):
    metadata={key:source.get(key,'') for key in ('document_date','edition','provenance','licence','collected_at','archive_date','source_revision','language')}
    db.execute('INSERT OR IGNORE INTO translation_publications(translation_id,user_id,source_id,title,source_meta,auto_publish) VALUES(?,?,?,?,?,?)',
               (identifier,user_id,source['id'],source['title'],json.dumps(metadata,ensure_ascii=False),int(auto_publish)))


def state(identifier):
    with store.connect() as db:
        row=db.execute('''SELECT published_path,published_at,error,auto_publish,source_meta,
            NOT EXISTS(SELECT 1 FROM settings WHERE key=?) AS pending
            FROM translation_publications WHERE translation_id=?''',('published-translation:'+identifier,identifier)).fetchone()
    if not row:return {'automatic':False,'source_id':None,'error':None}
    return {'automatic':bool(row['auto_publish']),'source_id':'guide:'+row['published_path'] if row['published_at'] else None,
            'partial':bool(row['published_at'] and json.loads(row['source_meta']).get('published_missing')),
            'pending':bool(row['auto_publish'] and row['pending']),
            'error':row['error']}


def mark_current(db,identifier,source_id,done):
    # A concurrent manual publication may have read an older partial snapshot.
    db.execute('''INSERT OR REPLACE INTO settings(key,value)
        SELECT ?,? WHERE (SELECT count(*) FROM translation_parts
        WHERE translation_id=? AND status='done')=?''',
        ('published-translation:'+identifier,source_id,identifier,done))


def _publish(identifier,user_id):
    with store.connect() as db:
        item=db.execute('SELECT * FROM translations WHERE id=? AND user_id=?',(identifier,user_id)).fetchone()
        if not item:raise HTTPException(404,'Traduction introuvable.')
        if item['status']!='completed':raise HTTPException(409,'Terminez la traduction avant de l’ajouter aux documents locaux.')
        reserve(db,identifier,user_id,{'id':item['source_id'],'title':item['title']})
        record=dict(db.execute('SELECT * FROM translation_publications WHERE translation_id=?',(identifier,)).fetchone())
        parts=[dict(row) for row in db.execute('SELECT * FROM translation_parts WHERE translation_id=? ORDER BY position',(identifier,))]
        reports={row['position']:json.loads(row['report']) for row in db.execute('SELECT position,report FROM translation_checks WHERE translation_id=?',(identifier,))}
    if any(part['status'] not in ('done','unreadable','deferred') for part in parts) or not any(part['status']=='done' for part in parts):
        raise HTTPException(409,'Aucun texte français à partager, ou traitement encore en cours.')
    if sum(len(part['translated']) for part in parts)>20_000_000:raise HTTPException(413,'La traduction est trop volumineuse pour un document partagé. Exportez le texte ou traduisez des plages plus courtes.')
    path='TRAD-'+identifier+'.fr.html'
    target=library.GUIDES/path
    source_meta=json.loads(record['source_meta'])
    from .translation_quality import VERSION, assess
    for part in parts:
        report=reports.get(part['position'])
        if part['status']!='done' or not report:continue
        language=report.get('source_language',source_meta.get('language'))
        check=assess(part['source_text'],part['translated'],source_language=language,english_grouping=True)
        errors={issue['code'] for issue in check['issues'] if issue['severity']=='error'}
        if report.get('version',0)<VERSION:
            # Older reports did not check references or copied short prose.
            errors.discard('references')
            if len(part['source_text'].strip())<100:errors.discard('unchanged')
        if report['status']=='blocked' or not part['translated'].strip() or errors:
            raise HTTPException(409,'Un passage enregistré présente une anomalie bloquante. Publication refusée ; le texte privé est conservé.')
    pages=defaultdict(list)
    for part in parts:pages[part['page']].append(part)
    unreadable=sum(part['status']=='unreadable' for part in parts)
    deferred=sum(part['status']=='deferred' for part in parts)
    missing=unreadable+deferred
    completeness=(f'Traduction partielle : {len(parts)-missing}/{len(parts)} passages disponibles. '
                  f'{deferred} non traduit(s), {unreadable} sans texte extractible. '
                  'Consultez l’original aux endroits indiqués.') if missing else ''

    title=('Traduction IA partielle — ' if missing else 'Traduction IA — ')+record['title']
    stamp=datetime.fromtimestamp(item['updated'],timezone.utc).date().isoformat()
    original_url='/index.html?document='+quote(record['source_id'],safe='')+'#library'
    models=', '.join(sorted({part['model'] for part in parts if part['model']}))
    digest=hashlib.sha256(json.dumps([(p['page'],p['source_text']) for p in parts],ensure_ascii=False).encode('utf-8')).hexdigest()
    head=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>
<style>body{{font:18px/1.65 system-ui,sans-serif;max-width:850px;margin:auto;padding:24px;color:#202b26;background:#faf9f4}}a{{color:#126344}}.notice{{border:2px solid #c28a2c;padding:16px;background:#fff6dc}}.part{{white-space:pre-wrap;overflow-wrap:anywhere}}section{{border-top:1px solid #ccd6cd;margin-top:32px}}@media print{{body{{background:white}}section{{break-before:page}}}}</style>
<h1>{escape(title)}</h1><p class="notice">{escape(NOTICE)}</p>
{f'<p class="notice">{escape(completeness)}</p>' if completeness else ''}
<p>Version française produite le {stamp}. Pages/sections {min(pages)} à {max(pages)}. Modèles : {escape(models)}.</p>
<p>Original : {escape(record['title'])}. Date : {escape(source_meta.get('document_date') or 'inconnue')}. Édition : {escape(source_meta.get('edition') or 'inconnue')}.</p>
<p><a href="{escape(original_url,quote=True)}">Consulter l’original dans la bibliothèque</a></p>
<p>Provenance de l’original : {escape(source_meta.get('provenance',''))}. Conditions d’utilisation déclarées pour l’original : {escape(source_meta.get('licence') or 'à vérifier')}.</p>
<p>Empreinte SHA-256 de l’instantané textuel utilisé : {digest}. Cette empreinte ne porte pas sur le fichier PDF.</p>'''
    sections=[]
    if reports:
        warnings=sum(report['status']=='warning' for report in reports.values())
        unchecked=sum(p['status']=='done' and p['position'] not in reports for p in parts)
        head+=f'<p class="notice">Contrôles automatiques limités : {warnings} passage(s) à relire, {unchecked} passage(s) sans contrôle enregistré. Ils ne valident pas le sens de la traduction ; aucune relecture humaine n’est attestée.</p>'
    for page,rows in pages.items():
        body=''
        for p in rows:
            if p['status']=='done':
                messages=reports.get(p['position'],{}).get('issues',[])
                if messages:body+='<p class="notice">À relire : '+escape(' '.join(i['message'] for i in messages))+'</p>'
                body+='<p class="part">'+escape(p['translated'])+'</p>'
            else:
                label='Passage non traduit' if p['status']=='deferred' else 'Texte non extractible'
                original=record['source_id']
                if original.lower().endswith('.pdf'):original+=f'#page={page}'
                href='/index.html?document='+quote(original,safe='')+'#library'
                body+=f'<p class="part">[{label} · passage {p["position"]+1}]</p><p><a href="{escape(href,quote=True)}">Consulter l’original</a></p>'
        sections.append(f'<section id="page={page}"><h2>Page/section {page}</h2>{body}</section>')
    payload=(head+'\n'.join(sections)+'</html>').encode('utf-8')
    digest=hashlib.sha256(payload).hexdigest()
    source_id='guide:'+path
    result={'source_id':source_id,'url':'/guides/'+quote(path),'title':title,'partial':bool(missing)}
    previous=source_meta.get('published_sha256')
    if target.is_symlink():
        raise HTTPException(409,'Le document publié a été modifié. Il est conservé.')
    if target.exists():
        actual=hashlib.sha256(target.read_bytes()).hexdigest()
        if actual not in (previous,source_meta.get('pending_sha256'),source_meta.get('pending_previous_sha256'),digest):
            raise HTTPException(409,'Le document publié a été modifié. Il est conservé.')
        if actual==previous and record['published_at'] and source_meta.get('published_missing',0)<=missing:
            with store.connect() as db:
                if db.execute('SELECT 1 FROM documents WHERE id=?',(source_id,)).fetchone():
                    db.execute('UPDATE translation_publications SET error=NULL WHERE translation_id=?',(identifier,))
                    mark_current(db,identifier,source_id,len(parts)-missing)
                    return result
    else:
        actual=None
    if actual!=digest:
        # Record the next digest before the atomic replacement. A restart can
        # recognize either file and retry without overwriting an external edit.
        if actual and actual!=previous:source_meta['pending_previous_sha256']=actual
        source_meta['pending_sha256']=digest
        with store.connect() as db:
            db.execute('UPDATE translation_publications SET source_meta=? WHERE translation_id=?',
                (json.dumps(source_meta,ensure_ascii=False),identifier))
        durable.write_bytes(target,payload)
    with store.connect() as db:
        db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET title=excluded.title,language=excluded.language,provenance=excluded.provenance,licence=excluded.licence',
                   (path,title,'fr',NOTICE+' Original : '+record['title'],'Droits de l’original à respecter ; aucune autorisation supplémentaire de redistribution.'))
        db.execute('INSERT INTO guide_dates VALUES(?,?,?,?) ON CONFLICT(path) DO NOTHING',(path,stamp,'Traduction IA non vérifiée',stamp))
    library.index_guides()
    with store.connect() as db:
        if not db.execute('SELECT 1 FROM documents WHERE id=?',('guide:'+path,)).fetchone():raise RuntimeError('Indexation du document non terminée.')
        source_meta.pop('pending_sha256',None)
        source_meta.pop('pending_previous_sha256',None)
        source_meta.update(published_sha256=digest,published_pages=sorted(pages),published_missing=missing)
        db.execute('UPDATE translation_publications SET published_path=?,source_meta=?,published_at=?,error=NULL WHERE translation_id=?',
            (path,json.dumps(source_meta,ensure_ascii=False),time.time(),identifier))
        mark_current(db,identifier,source_id,len(parts)-missing)
    return result


async def publish(identifier,user_id):
    async with LOCK:
        task=asyncio.create_task(asyncio.to_thread(_publish,identifier,user_id))
        try:return await asyncio.shield(task)
        except asyncio.CancelledError:
            # Cancelling to_thread does not stop its filesystem writes. Join it
            # before releasing LOCK or allowing the private work to be deleted.
            await asyncio.gather(task,return_exceptions=True)
            raise
        except Exception as exc:
            with store.connect() as db:db.execute('UPDATE translation_publications SET error=? WHERE translation_id=?',('Ajout aux documents locaux interrompu. La traduction privée est conservée ; réessayez.',identifier))
            raise


async def automatic(identifier,user_id):
    with store.connect() as db:
        intent=db.execute('SELECT value FROM settings WHERE key=?',('auto-translation:'+identifier,)).fetchone()
        if intent:reserve(db,identifier,user_id,json.loads(intent['value']),auto_publish=True)
    with store.connect() as db:
        ready=db.execute("SELECT 1 FROM translation_parts WHERE translation_id=? AND status='done' LIMIT 1",(identifier,)).fetchone()
        current=db.execute('SELECT 1 FROM settings WHERE key=?',('published-translation:'+identifier,)).fetchone()
    if ready and not current and state(identifier)['automatic']:
        try:await publish(identifier,user_id)
        except Exception:pass


async def recover():
    with store.connect() as db:
        rows=db.execute("SELECT t.id,t.user_id FROM translations t JOIN settings s ON s.key='auto-translation:'||t.id WHERE t.status='completed' AND EXISTS(SELECT 1 FROM translation_parts p WHERE p.translation_id=t.id AND p.status='done') AND NOT EXISTS(SELECT 1 FROM settings done WHERE done.key='published-translation:'||t.id)").fetchall()
    for row in rows:await automatic(row['id'],row['user_id'])
