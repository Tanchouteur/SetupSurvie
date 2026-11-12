"""Exercise the library controls on desktop/mobile, with simulated API jobs only."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get('PLAYWRIGHT_OUTPUT', '/tmp/library-browser'))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT/'portal')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(server.server_port)
    themes = [{'id':key, 'label':value['label']} for key, value in json.loads((ROOT/'deploy/kiwix-themes.json').read_text())['themes'].items()]
    report = []
    with sync_playwright() as playwright:
        for engine in ('chromium','webkit'):
            browser = getattr(playwright, engine).launch(headless=True, **({'args':['--disable-gpu','--disable-dev-shm-usage']} if engine=='chromium' else {}))
            state = {'phase':'idle','themes':themes,'available':True}
            role = ['admin']; requests = []; errors = []; external = []
            context = browser.new_context(viewport={'width':1366,'height':900})
            def route(request):
                url = urlsplit(request.request.url); path = url.path
                if url.netloc != urlsplit(base).netloc:
                    external.append(request.request.url); request.abort(); return
                if not path.startswith('/api/'):
                    request.continue_(); return
                requests.append(path)
                value = {}
                if path=='/api/auth/me':value={'id':'browser','name':'Test','email':'test','role':role[0],'recovery_ready':True}
                elif path=='/api/status':value={'version':'0.1.9','modes':[],'books':[],'guides':1}
                elif path=='/api/conversations':value={'conversations':[]}
                elif path=='/api/inference':value={'online':True,'control_available':True,'message':'Assistant prêt','models':[],'gpus':[],'memory':{},'disk':{},'jobs':{}}
                elif path=='/api/inventory':value={'books':[],'guides':[],'models':[],'note':'Inventaire simulé pour le test.'}
                elif path=='/api/admin/library':value=state
                elif path=='/api/admin/library/plan':
                    options=request.request.post_data_json
                    state.update(phase='planned',options=options,id='a'*32,message='Sélection prête.',plan={
                        'count':1,'remaining_download_bytes':20000000,'library_bytes':200000000000,
                        'missing_themes':['chasse'],'candidates':[
                            {'title':'Guide pratique de jardinage','themes':['agriculture'],'status':'selected','bytes':20000000,'fulltext_index':True}]})
                    value={'accepted':True}
                elif path=='/api/admin/library/download':
                    assert request.request.post_data_json['id']==state['id']
                    state.update(phase='downloading',message='Téléchargement et vérification des archives…',progress={'bytes':2000000,'total':20000000});value={'accepted':True}
                elif path=='/api/admin/library/pause':
                    state.update(phase='paused',message='Opération mise en pause.');value={'accepted':True}
                request.fulfill(status=200,content_type='application/json',body=json.dumps(value))
            context.route('**/*',route)
            page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base+'/#data');page.wait_for_selector('#content-themes input',state='attached')
            assert not page.locator('#content-manager').evaluate('e=>e.open')
            assert page.locator('#software-version').inner_text()=='Version d’essai 0.1.9'
            page.locator('#content-manager>summary').click()
            for width in (1366,768,390,320):
                page.set_viewport_size({'width':width,'height':900})
                assert page.locator('#content-themes input').count()==14
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(engine,width)
                assert page.locator('#content-plan').is_enabled()
                report.append({'engine':engine,'width':width,'no_overflow':True})
            page.locator('#content-themes input[value=chasse]').check()
            page.locator('#content-plan').click();page.wait_for_selector('#content-download:visible')
            assert 'Chasse' in page.locator('#content-gaps').inner_text()
            # Changing the choices requires a new plan rather than downloading old choices.
            page.locator('#content-budget').select_option('5');assert page.locator('#content-download').is_disabled()
            page.locator('#content-budget').select_option('10');assert page.locator('#content-download').is_enabled()
            page.locator('#content-download').click();page.wait_for_selector('#content-pause:visible')
            assert page.locator('#content-progress').is_visible()
            page.reload();page.wait_for_selector('#content-themes input',state='attached')
            page.locator('#content-manager>summary').click()
            page.wait_for_function("document.getElementById('content-fields').disabled")
            assert page.locator('#content-budget').is_disabled()
            page.locator('#content-pause').click();page.wait_for_function("document.getElementById('content-message').textContent.includes('pause')")
            assert page.locator('#content-download').is_enabled()
            page.locator('#content-results>summary').click()
            page.screenshot(path=str(OUTPUT/(engine+'-library-mobile.png')),full_page=True)
            state.update(phase='completed',message='Archives téléchargées et vérifiées.')
            page.locator('#content-refresh').click();page.wait_for_function("document.getElementById('content-message').textContent.includes('vérifiées')")
            assert page.locator('#content-download').is_hidden()
            role[0]='user';requests.clear();page.reload();page.wait_for_function("document.getElementById('account-label').textContent.includes('Test')")
            assert page.locator('#content-manager').is_hidden()
            assert '/api/admin/library' not in requests
            assert not errors,errors
            assert not external,external
            context.close();browser.close()
    server.shutdown();server.server_close()
    (OUTPUT/'browser-library.json').write_text(json.dumps({'passed':True,'layouts':report,'jobs_simulated':True,'physical_iphone':False},indent=2))
    print(json.dumps({'passed':True,'layouts':report}))


if __name__=='__main__':main()
