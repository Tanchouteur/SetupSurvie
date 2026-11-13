"""Native account operations. Emergency tokens stay server-side and expire in one minute."""
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid

import httpx
from fastapi import HTTPException

WEBUI = os.environ.get('WEBUI_URL','http://open-webui:8080').rstrip('/')
DB_PATH = os.environ.get('WEBUI_DB_PATH','/webui-data/webui.db')
SECRET = os.environ.get('WEBUI_SECRET_KEY','')


async def native(path, payload=None, token=None):
    headers = {'Authorization':'Bearer '+token} if token else {}
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=30) as client:
            response = await client.request('POST' if payload is not None else 'GET',WEBUI+path,json=payload,headers=headers)
    except httpx.HTTPError:
        raise HTTPException(503,'Le service de connexion est momentanément indisponible.')
    if response.status_code >= 400:
        if response.status_code in (401,403):raise HTTPException(401,'Identifiant, mot de passe ou session non valide.')
        raise HTTPException(response.status_code,'Cette opération n’a pas pu être effectuée. Vérifiez les informations saisies.')
    return response.json()


def native_account(email):
    db = sqlite3.connect('file:'+DB_PATH+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    try:
        row=db.execute('SELECT a.id,a.email,a.session_stamp,a.mfa,u.role FROM auth a JOIN user u ON a.id=u.id WHERE lower(a.email)=? AND a.active=1',(email.lower(),)).fetchone()
        return dict(row) if row else None
    finally:db.close()


def emergency_admin_token():
    if not SECRET:raise HTTPException(503,'La récupération locale n’est pas configurée.')
    db=sqlite3.connect('file:'+DB_PATH+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    try:
        row=db.execute("SELECT a.id,a.session_stamp,a.mfa FROM auth a JOIN user u ON a.id=u.id WHERE u.role='admin' AND a.active=1 ORDER BY u.created_at LIMIT 1").fetchone()
    finally:db.close()
    if not row:raise HTTPException(503,'Aucun administrateur local disponible.')
    mfa=json.loads(row['mfa']) if isinstance(row['mfa'],str) else row['mfa']
    if mfa and mfa.get('secret'):
        raise HTTPException(409,'Une protection supplémentaire est activée. Utilisez le secours local de l’administrateur.')
    def encode(value):return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).rstrip(b'=')
    data=encode({'alg':'HS256','typ':'JWT'})+b'.'+encode({'id':row['id'],'session_stamp':row['session_stamp'],'auth_method':'password','iat':int(time.time()),'exp':int(time.time())+60,'jti':str(uuid.uuid4())})
    signature=base64.urlsafe_b64encode(hmac.new(SECRET.encode(),data,hashlib.sha256).digest()).rstrip(b'=')
    return (data+b'.'+signature).decode()


async def reset_password(email,password):
    account=native_account(email)
    if not account:raise HTTPException(400,'Code ou identifiant non valide.')
    await native('/api/v1/users/'+account['id']+'/update',{'password':password},emergency_admin_token())


async def profile_token(profile):
    """Short internal bridge to native sessions; no user password or token exposed."""
    from .profiles import webui_headers
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=30) as client:
            response=await client.post(WEBUI+'/api/v1/auths/signin',headers=webui_headers(profile),json={'email':profile['email'],'password':''})
            if response.status_code!=200:raise HTTPException(503,'L’assistant avancé est indisponible. Le portail reste utilisable.')
            value=response.json()
        if not isinstance(value.get('token'),str) or not value['token']:raise ValueError('Native profile unavailable')
        return value['token']
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'L’assistant avancé est indisponible. Le portail reste utilisable.')
