"""Real pilot API and portal in Chromium: « Vidéos uniquement » and assistant links.

Tiny fixture videos only (one small WebM copied twice), no model or network.
Run: python tests/browser_video_search.py (Playwright and Chromium required).
With a remote Playwright server: PLAYWRIGHT_WS=ws://host:port/ BROWSER_HOST=address
reachable from that browser (the API then listens on all interfaces).
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
from unittest.mock import AsyncMock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUTPUT=Path(os.environ.get('PLAYWRIGHT_OUTPUT','/tmp/video-search-browser'))
REPORT=[]


def check(ok,label):
    if not ok:raise AssertionError(label)
    REPORT.append(label)


def fixtures(temporary):
    media=temporary/'video';guides=temporary/'guides'
    for folder in (media/'youtube'/'feu',guides):folder.mkdir(parents=True)
    clip=(ROOT/'tests/fixtures/video/solid-green.webm').read_bytes()
    (media/'youtube'/'feu'/'Allumer un feu [abc].webm').write_bytes(clip)
    (media/'youtube'/'feu'/'Allumer un feu [abc].info.json').write_text(json.dumps({'title':'Allumer un feu sans allumettes','language':'fr','duration':12,'channel':'Chaîne fictive','id':'abc','extractor':'Youtube','description':'Démonstration fictive.'}))
    (media/'Bouillir.webm').write_bytes(clip)
    (guides/'feu.fr.txt').write_text('Allumer un feu : guide fictif.')
    return media,guides


def exercise(page,name,base,videos,video_requests):
    page.request.post(base+'/api/profiles/select',data={'id':'browser'},headers={'Origin':base})
    page.goto(base+'/#/bibliotheque/recherche')
    page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady")
    kind=page.locator('#search-kind');check(kind.is_visible(),name+' : menu « Documents et vidéos » visible')
    kind.select_option('videos')
    page.wait_for_function("()=>document.querySelectorAll('#search-results .result').length===2")
    titles=page.locator('#search-results .result h3').all_inner_texts()
    check(titles==['Allumer un feu sans allumettes','Bouillir'],name+' : recherche vide en mode vidéos = toutes les vidéos, par titre')
    check('kind=videos' in page.url,name+' : choix conservé dans l’adresse')
    check('vidéo(s) trouvée(s)' in page.locator('#search-message').inner_text(),name+' : message adapté aux vidéos')
    page.screenshot(path=str(OUTPUT/(name+'-videos.png')),full_page=True)
    page.fill('#library-query','allumer');page.locator('#library-search button[type=submit]').click()
    page.wait_for_function("()=>document.querySelectorAll('#search-results .result').length===1")
    check(page.locator('#search-results .result h3').inner_text()=='Allumer un feu sans allumettes',name+' : mot-clé limité aux vidéos')
    kind.select_option('documents')
    page.wait_for_function("()=>document.querySelector('#search-results .result .result-meta')?.textContent.startsWith('Guide')")
    check(page.locator('#search-results .result',has_text='Vidéo ·').count()==0,name+' : « Documents uniquement » exclut les vidéos')
    found=page.request.get(base+'/api/search?q=allumer&kind=videos').json()['results'][0]
    page.goto(base+video_requests.open_url(found['id']))
    page.locator('#reader video').wait_for()
    check(page.locator('#reader').get_by_text('Allumer un feu sans allumettes').count()>=1,name+' : le lien donné par l’assistant ouvre le lecteur de la vidéo')
    page.screenshot(path=str(OUTPUT/(name+'-lecteur.png')),full_page=True)


def main():
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from playwright.sync_api import sync_playwright
    from pilot import app as gateway,library,store,video_requests,videos
    OUTPUT.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp());media,guides=fixtures(temporary)
    patches=[patch.object(store,'ROOT',temporary/'state'),patch.object(videos,'ROOT',media),patch.object(library,'GUIDES',guides),patch.object(library,'books',AsyncMock(return_value=[]))]
    for item in patches:item.start()
    gateway.app.mount('/',StaticFiles(directory=str(ROOT/'portal'),html=True),name='portal')
    remote=os.environ.get('PLAYWRIGHT_WS');host=os.environ.get('BROWSER_HOST','127.0.0.1')
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(gateway.app,host='0.0.0.0' if remote else '127.0.0.1',port=port,log_level='warning'))
    threading.Thread(target=server.run,daemon=True).start()
    base=f'http://{host}:{port}'
    try:
        while not server.started:time.sleep(.05)
        # The inventory starts by itself with the service: no click needed.
        for _ in range(100):
            if videos.status()['phase']=='completed':break
            time.sleep(.1)
        check(videos.status()['phase']=='completed' and videos.status()['videos']==2,'Répertoire des vidéos créé automatiquement au démarrage du service')
        with sync_playwright() as playwright:
            browser=playwright.chromium.connect(remote,headers={'x-playwright-launch-options':json.dumps({'channel':'chromium'})}) if remote else playwright.chromium.launch()
            phone={k:v for k,v in playwright.devices['iPhone 13'].items() if k!='default_browser_type'}
            for name,options in [('ordinateur',{'viewport':{'width':1280,'height':900}}),('telephone',phone)]:
                page=browser.new_page(**options);errors=[];page.on('pageerror',lambda error:errors.append(error.message))
                try:
                    exercise(page,name,base,videos,video_requests)
                    check(not errors,name+' : aucune erreur JavaScript')
                except Exception:
                    page.screenshot(path=str(OUTPUT/(name+'-echec.png')),full_page=True)
                    print('Échec',name,page.url,repr(page.locator('#search-message').inner_text()) if page.locator('#search-message').count() else '',errors)
                    raise
                finally:page.close()
            browser.close()
    finally:
        server.should_exit=True
        for item in patches:item.stop()
        shutil.rmtree(temporary,ignore_errors=True)
        (OUTPUT/'report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
        print('\n'.join(REPORT))


if __name__=='__main__':main()
