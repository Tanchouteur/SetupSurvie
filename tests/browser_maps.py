"""Exercise real offline map rendering while blocking every external request."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

URL=os.environ.get('PLAYWRIGHT_BASE_URL','http://127.0.0.1:8080')
OUTPUT=Path(os.environ.get('PLAYWRIGHT_OUTPUT','/output'))


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    allowed=urlsplit(URL).netloc;external=[];errors=[];responses=[];layouts=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1280,'height':800})
        def route(request):
            url=request.request.url
            if urlsplit(url).netloc==allowed or url.startswith(('blob:','data:')):request.continue_()
            else:external.append(url);request.abort()
        context.route('**/*',route)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='warning' and 'Error' in m.text else None)
        page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}) if '/api/maps/' in r.url or '/fonts/' in r.url else None)
        page.goto(URL+'/#library')
        page.locator('a[href="/cartes.html"]').click()
        page.wait_for_function("document.getElementById('status').textContent.includes('Fonctionne sans Internet')")
        page.wait_for_function("document.getElementById('map').dataset.ready === 'true'")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUTPUT/'maps-desktop.png'))
        assert any('/archive' in r['url'] and r['status']==206 for r in responses),responses
        assert any('/fonts/' in r['url'] and r['status']==200 for r in responses),responses
        image=Image.open(OUTPUT/'maps-desktop.png').convert('RGB')
        colors=image.crop((200,200,1000,650)).getcolors(1_000_000)
        assert colors and len(colors)>30,'La carte semble vide.'
        for width in (320,390,768):
            page.set_viewport_size({'width':width,'height':750});page.wait_for_timeout(250)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
            assert page.locator('#area').is_visible()
            layouts.append({'width':width,'no_horizontal_overflow':True})
        page.locator('#area').select_option('sud');page.wait_for_timeout(4000)
        assert 'PACA' in page.locator('#status').inner_text()
        page.screenshot(path=str(OUTPUT/'maps-mobile.png'))
        assert not external,external
        assert not errors,errors
        (OUTPUT/'maps-browser.json').write_text(json.dumps({'passed':True,'engine':'Chromium software rendering','physical_device':False,'layouts':layouts,'responses':responses,'external':external,'errors':errors},indent=2))
        browser.close()
    print('Carte réelle, lecture partielle HTTP, polices locales et trois largeurs : OK ; aucune requête extérieure.')


if __name__=='__main__':main()
