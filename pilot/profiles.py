"""Local identity labels, freely selectable on the family network; no passwords.

Keep native user IDs when importing so existing portal histories stay attached.
The Open WebUI database is read-only and is never required for daily portal use.
"""
import hashlib
import sqlite3
import time
from urllib.parse import quote
from fastapi import HTTPException
from . import accounts,store

COOKIE='survie_profile'
DEFAULT='local-family'


def native_profiles():
    try:
        db=sqlite3.connect('file:'+accounts.DB_PATH+'?mode=ro',uri=True,timeout=2)
        db.row_factory=sqlite3.Row
        try:return [dict(row) for row in db.execute("SELECT id,name,email,role FROM user WHERE role IN ('admin','user') LIMIT 1000")]
        finally:db.close()
    except (sqlite3.Error,OSError):return []


def initialize():
    with store.connect() as db:
        db.execute('INSERT OR IGNORE INTO profiles VALUES(?,?,?,?,?,?)',(DEFAULT,'Famille','family@survie.local','admin','local',time.time()))
    sync()


def sync():
    native=native_profiles()
    with store.connect() as db:
        for item in native:
            if not all(isinstance(item.get(k),str) and item[k] for k in ('id','name','email','role')):continue
            email=item['email'].lower()
            if not email.isascii() or any(c in email for c in '\r\n'):continue
            # A local profile can already have an automatically created native account.
            if db.execute('SELECT 1 FROM profiles WHERE email=? AND id!=?',(email,item['id'])).fetchone():continue
            db.execute('INSERT INTO profiles VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=CASE WHEN profiles.origin IN (\'native\',\'recovered\') THEN excluded.name ELSE profiles.name END,email=excluded.email,role=CASE WHEN profiles.origin=\'recovered\' THEN excluded.role ELSE profiles.role END,origin=CASE WHEN profiles.origin=\'recovered\' THEN \'native\' ELSE profiles.origin END',
                       (item['id'],item['name'][:100],email,item['role'],'native',time.time()))
        # Recover portal identities even if Open WebUI has not started yet.
        ids={row[0] for table in ('conversations','jobs','translations') for row in db.execute('SELECT DISTINCT user_id FROM '+table)}
        for identifier in ids:
            if not identifier:continue
            suffix=hashlib.sha256(identifier.encode()).hexdigest()[:24]
            db.execute('INSERT OR IGNORE INTO profiles VALUES(?,?,?,?,?,?)',(identifier,'Profil conservé '+identifier[:8],'saved-'+suffix+'@survie.local','user','recovered',time.time()))


def public(row):return {k:row[k] for k in ('id','name','role')}


def current(identifier=None):
    with store.connect() as db:
        row=db.execute('SELECT * FROM profiles WHERE id=?',(identifier or DEFAULT,)).fetchone()
        if not row:row=db.execute('SELECT * FROM profiles WHERE id=?',(DEFAULT,)).fetchone()
    if row:return dict(row)
    # Also works in small fixtures or after a startup interrupted before profile import.
    initialize()
    return current(identifier)


def listing():
    sync()
    with store.connect() as db:return [public(row) for row in db.execute('SELECT * FROM profiles ORDER BY created,id')]


def selected(identifier):
    with store.connect() as db:row=db.execute('SELECT * FROM profiles WHERE id=?',(identifier,)).fetchone()
    if not row:raise HTTPException(404,'Profil introuvable. Actualisez la liste et choisissez un profil.')
    return dict(row)


def create(name):
    name=' '.join(name.split())
    if not name or len(name)>100:raise HTTPException(422,'Choisissez un prénom ou un nom de 1 à 100 caractères.')
    identifier='local-'+store.new_id()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT count(*) FROM profiles').fetchone()[0]>=1000:raise HTTPException(409,'La liste atteint 1 000 profils.')
        db.execute('INSERT INTO profiles VALUES(?,?,?,?,?,?)',(identifier,name,'profile-'+identifier[6:]+'@survie.local','user','local',time.time()))
    return selected(identifier)


def webui_headers(profile):
    return {'X-Survie-Email':profile['email'],'X-Survie-Name':quote(profile['name'],safe=''),'X-Survie-Role':profile['role']}
