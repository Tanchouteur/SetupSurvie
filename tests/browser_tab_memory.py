"""Real portal in Chromium: each tab keeps its place; a second click resets it.

First click on another tab returns to its last screen (sub-page, typed search,
collection filter, scroll). A click on the tab already shown returns to its root.
No ZIM, model or network: empty fixture library, local Famille profile.
Run: python tests/browser_tab_memory.py (Playwright and Chromium required).
With a remote Playwright server: PLAYWRIGHT_WS=ws://host:port/ BROWSER_HOST=address
reachable from that browser (the API then listens on all interfaces).
"""
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = []


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    REPORT.append(label)


def exercise(page, base, name):
    page.request.post(base + '/api/profiles/select', data={'id': 'local-family'}, headers={'Origin': base})
    page.goto(base + '/#/appareil/reglages')
    page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady&&S.user&&S.user.role==='admin'")
    nav = lambda route: page.locator(f'#navigation [data-route="{route}"]').click()
    tab = lambda route: page.locator(f'.view:not([hidden]) .next-tabs [data-route="{route}"]').click()
    at = lambda hash: page.wait_for_function("h=>location.hash.split('?')[0]===h", arg=hash)

    page.locator('#settings-reglages [data-route="appareil/tests"]').click()
    at('#/appareil/tests')
    long_page = page.evaluate("()=>document.documentElement.scrollHeight-innerHeight") > 200
    if long_page:
        page.evaluate("()=>window.scrollTo(0,180)")
        page.wait_for_timeout(350)
    nav('bibliotheque')
    tab('bibliotheque/recherche')
    at('#/bibliotheque/recherche')
    page.locator('#library-query').fill('abri en hiver')

    nav('appareil')
    at('#/appareil/tests')
    check(page.locator('#settings-tests').is_visible(), name + ' : Mon appareil revient à la sous-page Tests')
    if long_page:
        page.wait_for_function("()=>Math.abs(scrollY-180)<5")
        check(True, name + ' : position dans la page retrouvée')

    nav('bibliotheque')
    at('#/bibliotheque/recherche')
    check(page.locator('#library-query').input_value() == 'abri en hiver', name + ' : mots tapés conservés dans Rechercher')
    tab('bibliotheque/recherche')
    page.wait_for_function("()=>document.querySelector('#library-query').value===''")
    check(True, name + ' : second clic sur Rechercher vide la recherche')

    tab('bibliotheque/collections')
    at('#/bibliotheque/collections')
    page.locator('#collection-filter').fill('wiki')
    page.wait_for_function("()=>location.hash.includes('resource=wiki')")
    nav('accueil')
    at('#/accueil')
    nav('bibliotheque')
    at('#/bibliotheque/collections')
    check(page.locator('#collection-filter').input_value() == 'wiki', name + ' : filtre des collections retrouvé')
    nav('bibliotheque')
    page.wait_for_function("()=>document.querySelector('#collection-filter').value===''&&!location.hash.includes('resource=')")
    check(True, name + ' : second clic sur Bibliothèque retire le filtre')
    tab('bibliotheque/recherche')
    check(page.locator('#library-query').input_value() == '', name + ' : la section repart de zéro, sous-onglets compris')

    nav('appareil')
    at('#/appareil/tests')
    tab('appareil/reglages')
    at('#/appareil/reglages')
    check(page.locator('#settings-reglages').is_visible() and page.locator('#settings-back').is_hidden(),
          name + ' : second clic sur Paramètres revient à la liste des rubriques')
    page.locator('#settings-reglages [data-route="appareil/tests"]').click()
    at('#/appareil/tests')
    tab('appareil/ensemble')
    at('#/appareil/ensemble')
    tab('appareil/reglages')
    at('#/appareil/tests')
    check(True, name + ' : premier clic sur Paramètres retrouve la sous-page')
    nav('appareil')
    at('#/appareil/ensemble')
    tab('appareil/reglages')
    at('#/appareil/reglages')
    check(True, name + ' : second clic sur Mon appareil remet toute la section à sa racine')

    nav('assistant')
    at('#/assistant')
    page.locator('#chat-input').fill('Brouillon à garder')
    nav('assistant')
    check(page.locator('#chat-input').input_value() == 'Brouillon à garder', name + ' : second clic sur Assistant garde le brouillon')
    page.go_back()
    check(page.evaluate('location.hash').startswith('#/'), name + ' : Précédent reste utilisable')


def main():
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from playwright.sync_api import sync_playwright
    from pilot import app as gateway, library, store
    temporary = Path(tempfile.mkdtemp())
    (temporary / 'guides').mkdir()
    for item in (patch.object(store, 'ROOT', temporary / 'state'), patch.object(library, 'GUIDES', temporary / 'guides'),
                 patch.object(library, 'books', AsyncMock(return_value=[]))):
        item.start()
    gateway.app.mount('/', StaticFiles(directory=str(ROOT / 'portal'), html=True), name='portal')
    remote = os.environ.get('PLAYWRIGHT_WS')
    host = os.environ.get('BROWSER_HOST', '127.0.0.1')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(gateway.app, host='0.0.0.0' if remote else '127.0.0.1', port=port, log_level='warning'))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(.05)
    base = f'http://{host}:{port}'
    errors = []
    with sync_playwright() as playwright:
        browser = (playwright.chromium.connect(remote, headers={'x-playwright-launch-options': json.dumps({'channel': 'chromium'})})
                   if remote else playwright.chromium.launch())
        for name, viewport in (('bureau', {'width': 1440, 'height': 950}), ('mobile', {'width': 390, 'height': 844})):
            context = browser.new_context(viewport=viewport)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            exercise(page, base, name)
            context.close()
        browser.close()
    server.should_exit = True
    check(not errors, 'Aucune erreur JavaScript : ' + '; '.join(errors))
    print('\n'.join(REPORT))


if __name__ == '__main__':
    main()
