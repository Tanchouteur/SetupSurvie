"""Real pilot API and portal in Chromium for the YouTube list button.

The host controller is simulated (no download, no network); the list
parsing, endpoints, polling and interface are real.
Run: PLAYWRIGHT_WS=ws://host:port/ BROWSER_HOST=address python tests/browser_youtube_downloads.py
"""
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUTPUT=Path(os.environ.get('PLAYWRIGHT_OUTPUT','/tmp/youtube-button-browser'))
REPORT=[]
A,B='aaaaaaaaaaa','bbbbbbbbbbb'
LIST='[Eau]\nhttps://youtu.be/'+A+'\nhttps://www.youtube.com/playlist?list=PL1\nhttps://youtu.be/'+B+'\n'


def check(ok,label):
    if not ok:raise AssertionError(label)
    REPORT.append(label)


class Host:
    """Simulated controller: downloading for a few polls, then completed."""
    def __init__(self):self.state={'phase':'idle'};self.polls=0;self.commands=[]
    async def __call__(self,action=None,body=None):
        if action is None:
            self.polls+=1
            if self.state.get('phase')=='downloading' and self.polls>=4:
                self.state.update(phase='completed',message='Téléchargement terminé : 1 vidéo(s) ajoutée(s), 0 déjà présente(s), 1 non téléchargée(s).')
                self.state['youtube'].update(current=None,counts={'downloaded':1,'skipped':0,'error':1,'refused':1},
                    items=[{'line':2,'status':'downloaded','title':'Filtrer l’eau'},{'line':3,'status':'refused','message':'liste de lecture refusée'},{'line':4,'status':'error','message':'vidéo privée'}])
            return dict(self.state)
        self.commands.append((action,body))
        if action=='youtube-download':
            self.polls=0
            self.state={'phase':'downloading','action':'youtube-download','message':'Téléchargement des vidéos YouTube et de leurs sous-titres…','options':{'max_height':body.get('max_height',480),'videos':2},
                        'youtube':{'videos':2,'done':0,'current':{'index':1,'line':2},'counts':{'downloaded':0},'items':[]}}
        if action=='pause':self.state.update(phase='paused',message='Téléchargement YouTube en pause. « Reprendre » continue la liste.')
        return {'accepted':True}


def exercise(page,name,base,host):
    page.request.post(base+'/api/profiles/select',data={'id':'famille'},headers={'Origin':base})
    page.goto(base+'/nouveau/#/bibliotheque/collections')
    page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady")
    area=page.locator('#next-youtube');area.wait_for(state='attached')
    page.wait_for_function("()=>!document.getElementById('next-youtube').hidden")
    area.locator('summary').click()
    check(page.locator('#next-youtube-text').is_visible(),name+' : zone « Ajouter des vidéos depuis YouTube » visible pour Famille')
    page.fill('#next-youtube-text',LIST);page.click('#next-youtube-check')
    page.wait_for_function("()=>document.getElementById('next-youtube-message').textContent.includes('2 vidéo(s)')")
    check('liste de lecture' in page.locator('#next-youtube-refused').inner_text(),name+' : ligne refusée expliquée avant le téléchargement')
    page.select_option('#next-youtube-quality','720');page.click('#next-youtube-start')
    page.wait_for_function("()=>!document.getElementById('next-youtube-progress').hidden")
    check(host.commands[-1][0]=='youtube-download' and host.commands[-1][1]['max_height']==720 and len(host.commands[-1][1]['list'])==32,name+' : commande transmise au PC serveur avec la qualité et l’identifiant de la liste')
    check('vidéo 1 sur 2' in page.locator('#next-youtube-status').inner_text(),name+' : progression affichée pendant le téléchargement')
    check(page.locator('#next-youtube-pause').is_visible() and page.locator('#next-youtube-start').is_disabled(),name+' : pause proposée, nouveau lancement bloqué')
    page.screenshot(path=str(OUTPUT/(name+'-en-cours.png')),full_page=True)
    page.wait_for_function("()=>document.getElementById('next-youtube-status').textContent.includes('Téléchargement terminé')",timeout=20000)
    status=page.locator('#next-youtube-status').inner_text()
    check(status.count('ajoutée(s)')==1,name+' : totaux finaux affichés une seule fois')
    items=page.locator('#next-youtube-items').inner_text()
    check('Filtrer l’eau' in items and 'vidéo privée' in items,name+' : résultat ligne par ligne, avec la raison des échecs')
    area.screenshot(path=str(OUTPUT/(name+'-termine.png')))
    host.state={'phase':'downloading','action':'youtube-download','message':'…','options':{'max_height':480,'videos':2},'youtube':{'videos':2,'current':{'index':2},'counts':{}}};host.polls=-100
    page.wait_for_function("()=>!document.getElementById('next-youtube-pause').hidden")
    page.click('#next-youtube-pause')
    page.wait_for_function("()=>!document.getElementById('next-youtube-resume').hidden")
    check(host.commands[-1][0]=='pause' and 'en pause' in page.locator('#next-youtube-status').inner_text(),name+' : pause puis « Reprendre » proposé')
    page.click('#next-youtube-resume');page.wait_for_function("()=>document.getElementById('next-youtube-resume').hidden")
    check(host.commands[-1]==('youtube-download',{'resume':True}),name+' : reprise demandée au PC serveur')


def main():
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from playwright.sync_api import sync_playwright
    from pilot import app as gateway,profiles,store,youtube_downloads
    OUTPUT.mkdir(parents=True,exist_ok=True);temporary=Path(tempfile.mkdtemp());host=Host()
    patches=[patch.object(store,'ROOT',temporary/'state'),patch.object(youtube_downloads.operations,'library_command',host)]
    for item in patches:item.start()
    store.init()
    gateway.app.mount('/',StaticFiles(directory=str(ROOT/'portal'),html=True),name='portal')
    remote=os.environ.get('PLAYWRIGHT_WS');address=os.environ.get('BROWSER_HOST','127.0.0.1')
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(gateway.app,host='0.0.0.0' if remote else '127.0.0.1',port=port,log_level='warning'))
    threading.Thread(target=server.run,daemon=True).start();base=f'http://{address}:{port}'
    try:
        while not server.started:time.sleep(.05)
        child=profiles.create('Enfant')
        with sync_playwright() as playwright:
            browser=playwright.chromium.connect(remote,headers={'x-playwright-launch-options':json.dumps({'channel':'chromium'})}) if remote else playwright.chromium.launch()
            phone={k:v for k,v in playwright.devices['iPhone 13'].items() if k!='default_browser_type'}
            for name,options in [('ordinateur',{'viewport':{'width':1280,'height':900}}),('telephone',phone)]:
                page=browser.new_page(**options);errors=[];page.on('pageerror',lambda error:errors.append(error.message))
                try:
                    exercise(page,name,base,host);check(not errors,name+' : aucune erreur JavaScript')
                except Exception:
                    page.screenshot(path=str(OUTPUT/(name+'-echec.png')),full_page=True);print('Échec',name,errors);raise
                finally:page.close()
                host.state={'phase':'idle'}
            page=browser.new_page();page.request.post(base+'/api/profiles/select',data={'id':child['id']},headers={'Origin':base})
            page.goto(base+'/nouveau/#/bibliotheque/collections');page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady&&S.user")
            time.sleep(1)
            check(page.locator('#next-youtube').is_hidden(),'Profil Enfant : la zone YouTube n’est pas proposée')
            check(page.request.get(base+'/api/admin/youtube-downloads').status==403,'Profil Enfant : l’API refuse le téléchargement')
            page.close();browser.close()
    finally:
        server.should_exit=True
        for item in patches:item.stop()
        shutil.rmtree(temporary,ignore_errors=True)
        (OUTPUT/'report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2));print('\n'.join(REPORT))


if __name__=='__main__':main()
