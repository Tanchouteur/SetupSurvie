"""Private user terminology, snapshotted per job; never automatic word replacement."""
import json
import re
import unicodedata

from fastapi import HTTPException
from . import store

VERSION=1
MAX_TERMS=40
CONTEXT_CHARS=600


def normalized(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text)).strip()


def validate(terms):
    if not isinstance(terms,list) or len(terms)>MAX_TERMS:raise HTTPException(400,'Conservez au maximum 40 mots ou expressions dans cette liste.')
    result=[];seen=set()
    for item in terms:
        if not isinstance(item,dict) or set(item)!={'source','french'}:raise HTTPException(400,'Chaque entrée doit contenir le terme original et sa traduction française.')
        row={}
        for key in ('source','french'):
            value=item[key]
            if not isinstance(value,str) or len(value)>100 or any(unicodedata.category(c).startswith('C') for c in value):raise HTTPException(400,'Chaque terme doit tenir sur une ligne de 100 caractères maximum.')
            row[key]=normalized(value)
            if not row[key] or not any(c.isalpha() for c in row[key]):raise HTTPException(400,'Indiquez un mot ou une expression dans les deux langues.')
        key=row['source'].casefold()
        if key in seen:raise HTTPException(400,'Un terme original apparaît plusieurs fois. Gardez une seule traduction par terme.')
        seen.add(key);result.append(row)
    return result


def profile(user_id):
    with store.connect() as db:row=db.execute('SELECT value FROM settings WHERE key=?',('translation-terms:'+user_id,)).fetchone()
    return {'version':VERSION,'terms':json.loads(row[0]) if row else [],'max_terms':MAX_TERMS}


def save(user_id,terms):
    terms=validate(terms)
    with store.connect() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('translation-terms:'+user_id,json.dumps(terms,ensure_ascii=False)))
    return profile(user_id)


def snapshot(db,identifier,user_id):
    row=db.execute('SELECT value FROM settings WHERE key=?',('translation-terms:'+user_id,)).fetchone()
    terms=json.loads(row[0]) if row else []
    db.execute('INSERT INTO translation_guidance VALUES(?,?,?)',(identifier,VERSION,json.dumps(terms,ensure_ascii=False)))


def terms(db,identifier):
    row=db.execute('SELECT version,terms FROM translation_guidance WHERE translation_id=?',(identifier,)).fetchone()
    return {'version':row['version'],'terms':json.loads(row['terms'])} if row else {'version':None,'terms':[]}


def contains(text,term):
    return bool(re.search(r'(?<!\w)'+re.escape(normalized(term))+r'(?!\w)',normalized(text),re.I))


def for_part(db,identifier,part):
    saved=terms(db,identifier)
    relevant=[row for row in saved['terms'] if contains(part['source_text'],row['source'])]
    previous=None
    if saved['version'] is not None:
        row=db.execute("SELECT position,source_text,translated FROM translation_parts WHERE translation_id=? AND position=? AND status='done'",(identifier,part['position']-1)).fetchone()
        if row:
            previous={'position':row['position'],'source_end':row['source_text'][-CONTEXT_CHARS:],'french_end':row['translated'][-CONTEXT_CHARS:]}
    return {'version':saved['version'],'terms':relevant,'previous':previous}


def assess(guidance,translated):
    return [{'code':'term_choice','severity':'warning',
        'message':'Le terme « '+row['source']+' » devait être rendu par « '+row['french']+' ». Cette forme n’a pas été repérée ; vérifiez le contexte et la traduction.'}
        for row in guidance['terms'] if not contains(translated,row['french'])]
