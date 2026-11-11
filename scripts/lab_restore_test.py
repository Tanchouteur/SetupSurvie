#!/usr/bin/env python3
"""Restore account/history snapshots into separate containers; never run inference."""
import json
from pathlib import Path
import secrets
import shutil
import sys
import time
import urllib.error
import urllib.request

import linux_lab as lab
from lab_api import WebUI
from pilot_backup import backup


def main():
    from pilot import store
    app,c=lab.configuration();api=WebUI();suffix=secrets.token_hex(4)
    email='recette-restauration-'+suffix+'@survie.local';password=secrets.token_urlsafe(24)
    account=api.request('/api/v1/auths/add',{'name':'Recette restauration temporaire','email':email,'password':password,'role':'user','profile_image_url':'/user.png'})
    store.ROOT=lab.MOUNT/'data/state/pilot';cid=store.new_id()
    with store.connect() as db:
        db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(cid,account['id'],'Recette restauration',time.time()))
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(cid,'user','Message de contrôle restauré',time.time()))
    code=store.recovery_code(account['id'])
    snapshot=lab.MOUNT/'backups'/('recette-'+suffix);restored=lab.MOUNT/'tmp'/('restauration-'+suffix)
    ui='restore-ui-'+suffix;pilot='restore-pilot-'+suffix;created=[]
    try:
        def compose(config,*args,**kwargs):
            if args[0] not in ('stop','start'):raise RuntimeError('Commande non prévue par cette recette.')
            for name in args[1:]:lab.podman(args[0],lab.PREFIX+name,capture=True)
        app.compose=compose
        backup(app,c,snapshot)
        restored.mkdir(mode=0o700)
        shutil.copytree(snapshot/'data',restored/'data')
        data=restored/'data';original=lab.MOUNT/'data'
        env=lab.webui_env(c)
        lab.run_container(ui,lab.reference('open-webui'),['--network','setupsurvie-lab','--network-alias',ui,
            '-v',str(data/'state/openwebui')+':/app/backend/data',
            '-v',str(original/'state/openwebui/cache')+':/app/backend/data/cache:ro','--memory=3g'],env)
        created.append(ui)
        lab.run_container(pilot,lab.reference('open-webui'),['--network','setupsurvie-lab','--workdir','/srv',
            '-p','127.0.0.1:18080:8000','-v',str(lab.MOUNT/'runtime/pilot')+':/srv/pilot:ro',
            '-v',str(lab.MOUNT/'runtime/deploy/model-profiles.json')+':/srv/model-profiles.json:ro',
            '-v',str(lab.MOUNT/'runtime/deploy/assistant-system.fr.txt')+':/srv/system.fr.txt:ro',
            '-v',str(data/'state/pilot')+':/pilot-data','-v',str(data/'state/openwebui')+':/webui-data:ro',
            '-v',str(data/'library/guides')+':/guides','--entrypoint','python','--memory=1g'],
            {'PILOT_STATE_DIR':'/pilot-data','WEBUI_DB_PATH':'/webui-data/webui.db','WEBUI_SECRET_KEY':c['secret'],
             'WEBUI_URL':'http://'+ui+':8080','KIWIX_URL':'http://kiwix:8080','GUIDES_DIR':'/guides'},
            command_args=['-m','uvicorn','pilot.app:app','--host','0.0.0.0','--port','8000'])
        created.append(pilot)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def request(path,payload=None,token=None):
            headers={'Content-Type':'application/json'}
            if token:headers['Authorization']='Bearer '+token
            req=urllib.request.Request('http://127.0.0.1:18080/api'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
            with opener.open(req,timeout=10) as response:
                data=json.load(response);cookie=response.headers.get('Set-Cookie','')
                if cookie:data['_cookie']=cookie.split(';')[0].split('=',1)[1]
                return data
        for _ in range(120):
            try:login=request('/auth/login',{'email':email,'password':password});break
            except (OSError,ValueError):time.sleep(1)
        else:raise RuntimeError('Le service restauré n’est pas prêt.')
        assert request('/conversations/'+cid,token=login['_cookie'])['messages'][0]['content']=='Message de contrôle restauré'
        recovered=request('/auth/recover',{'email':email,'code':code,'new_password':secrets.token_urlsafe(24)})
        assert recovered['code']!=code
        assert request('/conversations/'+cid,token=recovered['_cookie'])['messages'][0]['content']=='Message de contrôle restauré'
        try:request('/auth/me',token=login['_cookie']);raise RuntimeError('Ancienne session encore valide.')
        except urllib.error.HTTPError as exc:assert exc.code==401
        report={'passed':True,'checks':['snapshot_services_arretes','restauration_conteneurs_distincts','authentification_compte_restaure','historique_restaure','code_secours_restaure','ancienne_session_invalidee'],'inference':False,'windows_test':False}
        lab.setup.write_json(lab.MOUNT/'results/restore-rehearsal.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        for name in reversed(created):
            lab.podman('rm','-f',lab.PREFIX+name,capture=True,check=False)
            (lab.MOUNT/'private'/(name+'.env')).unlink(missing_ok=True)
        # The temporary reader belongs to this test; never delete another account.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req=urllib.request.Request('http://127.0.0.1:3000/api/v1/users/'+account['id'],method='DELETE',headers={'Authorization':'Bearer '+api.token})
        for _ in range(90):
            try:
                with opener.open(req,timeout=5):pass
                break
            except OSError:time.sleep(1)
        with store.connect() as db:
            db.execute('DELETE FROM conversations WHERE id=?',(cid,));db.execute('DELETE FROM recovery WHERE user_id=?',(account['id'],))
        for path in [snapshot,restored]:
            if path.exists():shutil.rmtree(path)


if __name__=='__main__':main()
