"""Live, non-inference account checks using disposable readers only."""
import asyncio
import base64
import json
import secrets
import time

import httpx

from . import accounts,store


async def main():
    admin=accounts.emergency_admin_token()
    created=[];checks=[]
    origin={'Origin':'http://127.0.0.1:8000'}
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',trust_env=False,timeout=60) as client:
        try:
            for _ in range(2):
                email='recette-'+secrets.token_hex(5)+'@survie.local';password=secrets.token_urlsafe(24)
                value=await accounts.native('/api/v1/auths/add',{'name':'Compte de recette temporaire','email':email,'password':password,'role':'user','profile_image_url':'/user.png'},admin)
                created.append({'id':value['id'],'email':email,'password':password})
            alice,bob=created
            response=await client.post('/api/auth/login',json={'email':alice['email'],'password':alice['password']});response.raise_for_status()
            old=client.cookies.get('survie_session')
            payload=json.loads(base64.urlsafe_b64decode(old.split('.')[1]+'==='))
            assert 30*86400-120 < payload['exp']-time.time() <= 30*86400+120
            assert 'Max-Age=2592000' in response.headers['set-cookie'];checks.append('cookie_et_jeton_30_jours')
            cid=store.new_id()
            with store.connect() as db:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(cid,alice['id'],'Conversation de recette',time.time()))
                db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(cid,'user','Message à préserver',time.time()))
            native_chat=await accounts.native('/api/v1/chats/new',{'chat':{'title':'Recette récupération','messages':[],'history':{'messages':{},'currentId':None}}},old)
            assert (await client.get('/api/admin/users')).status_code==403;checks.append('lecteur_sans_administration')
            bob_auth=await accounts.native('/api/v1/auths/signin',{'email':bob['email'],'password':bob['password']})
            assert (await client.get('/api/conversations/'+cid,headers={'Authorization':'Bearer '+bob_auth['token']})).status_code==404
            models=await accounts.native('/api/models',token=bob_auth['token'])
            assert all(any(m['id']=='survie-'+mode for m in models['data']) for mode in ('rapide','moyenne','approfondie'))
            checks.extend(['historique_isole','profils_openwebui_partages_aux_lecteurs'])
            response=await client.post('/api/auth/recovery-code',headers=origin);response.raise_for_status();code=response.json()['code']
            password=secrets.token_urlsafe(24)
            response=await client.post('/api/auth/recover',json={'email':alice['email'],'code':code,'new_password':password},headers=origin)
            response.raise_for_status();new_code=response.json()['code'];assert new_code!=code
            assert (await client.get('/api/auth/me',headers={'Authorization':'Bearer '+old})).status_code==401
            assert (await client.get('/api/conversations/'+cid)).json()['messages'][0]['content']=='Message à préserver'
            new=client.cookies.get('survie_session')
            assert (await accounts.native('/api/v1/chats/'+native_chat['id'],token=new))['id']==native_chat['id']
            checks.extend(['recuperation_code_sans_email','anciennes_sessions_invalidees','historiques_pilote_et_openwebui_preserves'])
            response=await client.post('/api/auth/recover',json={'email':alice['email'],'code':code,'new_password':password},headers=origin)
            assert response.status_code==400;checks.append('code_usage_unique')
            # Exercise the exact local fallback helper with a disposable reader.
            replacement=secrets.token_urlsafe(24);await accounts.reset_password(alice['email'],replacement)
            assert (await client.get('/api/auth/me')).status_code==401
            local_code=store.recovery_code(alice['id']);assert store.consume_code(alice['id'],local_code)
            checks.append('secours_local_sans_effacement')
            # Log in with the fallback password and explicitly sign out.
            response=await client.post('/api/auth/login',json={'email':alice['email'],'password':replacement},headers=origin);response.raise_for_status()
            credential=client.cookies.get('survie_session')
            response=await client.post('/api/auth/logout',headers=origin);response.raise_for_status()
            assert (await client.get('/api/auth/me',headers={'Authorization':'Bearer '+credential})).status_code==401;checks.append('deconnexion_effective')
        finally:
            # Disposable accounts only. Never touch the primary administrator.
            admin=accounts.emergency_admin_token()
            for account in created:
                with store.connect() as db:
                    ids=[r[0] for r in db.execute('SELECT id FROM conversations WHERE user_id=?',(account['id'],))]
                    for cid in ids:db.execute('DELETE FROM conversations WHERE id=?',(cid,))
                    db.execute('DELETE FROM recovery WHERE user_id=?',(account['id'],))
                response=await client.delete(accounts.WEBUI+'/api/v1/users/'+account['id'],headers={'Authorization':'Bearer '+admin})
                response.raise_for_status()
    result={'passed':True,'checks':checks,'inference':False,'real_windows_or_phone_test':False}
    (store.ROOT/'acceptance-accounts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':asyncio.run(main())
