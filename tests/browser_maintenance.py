"""Real portal in Chromium: update entry, confirmation, tracking and maintenance mode.

The host controller and the status file are simulated by Playwright routes; no
update, Git, Docker or network access happens. Run: python tests/browser_maintenance.py
(Playwright and Chromium required). With a remote Playwright server:
PLAYWRIGHT_WS=ws://host:port/ BROWSER_HOST=address reachable from that browser.
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
OUTPUT = Path(os.environ.get('PLAYWRIGHT_OUTPUT', '/tmp/maintenance-browser'))
REPORT = []


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    REPORT.append(label)


def install_routes(page, state):
    def fulfill(route, value, status=200, headers=None):
        route.fulfill(status=status, content_type='application/json', body=json.dumps(value), headers=headers or {})

    def api(route):
        request = route.request
        path = request.url.split('/api', 1)[1].split('?')[0]
        if path == '/maintenance/update':
            return fulfill(route, state['update'])
        if path == '/maintenance/update/check':
            state['checks'] += 1
            return fulfill(route, {'accepted': True}, 202)
        if path == '/maintenance/update/start':
            state['started'].append(json.loads(request.post_data))
            state['status'] = dict(state['next'])
            return fulfill(route, {'accepted': True, 'id': state['next']['id']}, 202)
        if path == '/work-queue' and state.get('queue'):
            return fulfill(route, state['queue'])
        return route.fallback()

    def catalog(route):
        if state['offline']:
            return route.abort('connectionrefused')
        if state['status'] is None:
            return route.fulfill(status=404, body='')
        headers = {'X-SetupSurvie-Maintenance': '1'} if state['maintenance_page'] else {}
        return fulfill(route, state['status'], headers=headers)
    page.route('**/api/**', api)
    page.route('**/catalog/maintenance.json', catalog)


def status(phase, title, **values):
    now = time.time()
    return {'schema': 1, 'id': 'f' * 32, 'kind': 'update', 'state': 'running', 'phase': phase, 'title': title,
            'detail': '', 'current': None, 'total': None, 'unavailable': False, 'installed': '0.67.4',
            'available': '0.68.0', 'rolled_back': False, 'started': now - 95, 'updated': now,
            'steps': [{'phase': 'git', 'title': 'Récupération de la version disponible', 'at': now - 90}],
            'lines': ['[10:00:01] Récupération de la version disponible'], **values}


def exercise(page, base, name):
    now = time.time()
    state = {'checks': 0, 'started': [], 'offline': False, 'maintenance_page': False, 'status': None,
             'update': {'supported': True, 'installed': '0.67.4', 'available': '0.68.0', 'update_available': True,
                        'changes': ['Suivre les mises à jour depuis le portail', 'Afficher la copie complète'],
                        'checked_at': now - 300, 'error': '', 'checking': False, 'running': False,
                        'transfer_in_progress': False},
             'queue': {'jobs': [{'id': 'j', 'status': 'running', 'title': 'Indexation'}], 'running': True, 'paused': False},
             'next': status('git', 'Récupération de la version disponible')}
    install_routes(page, state)
    page.request.post(base + '/api/profiles/select', data={'id': 'local-family'}, headers={'Origin': base})
    page.goto(base + '/#/bibliotheque/collections')
    page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady&&S.user")
    entry = page.locator('.update-nav-mobile' if name == 'mobile' else '#main-navigation > .update-nav')
    entry.wait_for()
    check(entry.locator('.update-nav-dot').is_visible(), name + ' : pastille quand une version est disponible')
    if name == 'bureau':
        entry.hover()
        preview = entry.locator('.update-nav-preview')
        preview.wait_for()
        text = preview.inner_text()
        check('Nouvelle version 0.68.0' in text and 'Dernière vérification' in text and 'il y a 5 min' in text,
              name + ' : survol avec version et date de dernière vérification')
        page.screenshot(path=str(OUTPUT / (name + '-survol.png')))
        preview.get_by_text('Vérifier maintenant').click()
        page.wait_for_function("()=>true")
        page.wait_for_timeout(300)
        check(state['checks'] == 1, name + ' : actualisation depuis le survol')
        preview.get_by_text('Mettre à jour…').click()
    else:
        entry.locator('.update-nav-button').click()
    dialog = page.locator('#update-dialog')
    dialog.wait_for()
    page.locator('.update-dialog-queue').wait_for()
    check('0.67.4 → nouvelle version 0.68.0' in dialog.inner_text(), name + ' : confirmation avec les deux versions')
    check(dialog.locator('.update-dialog-changes li').count() == 2, name + ' : changements listés')
    check('indisponible' in dialog.locator('.update-dialog-warning').inner_text(), name + ' : indisponibilité annoncée')
    check('mise en pause' in page.locator('.update-dialog-queue').inner_text(), name + ' : file active signalée')
    page.screenshot(path=str(OUTPUT / (name + '-confirmation.png')))
    dialog.get_by_text('Lancer la mise à jour').click()
    page.locator('#maintenance-home').wait_for()
    check(state['started'] == [{'confirmed': True, 'pause_queue': True}], name + ' : lancement confirmé avec pause de la file')
    check(page.evaluate("()=>location.hash").startswith('#/accueil'), name + ' : suivi ouvert sur l’accueil')
    check('Récupération de la version disponible' in page.locator('#maintenance-home').inner_text(), name + ' : étape affichée')
    page.screenshot(path=str(OUTPUT / (name + '-preparation.png')), full_page=True)

    page.evaluate("()=>{location.hash='#/bibliotheque/recherche'}")
    page.locator('#maintenance-banner').wait_for()
    check(page.locator('#view-library').is_visible(), name + ' : site utilisable pendant la préparation')

    steps = state['next']['steps'] + [{'phase': 'backup', 'title': 'Sauvegarde des données', 'at': now}]
    state['status'] = status('backup', 'Sauvegarde des données', unavailable=True, current=120, total=480,
                             detail='120 fichiers sur 480 sauvegardés', steps=steps)
    page.wait_for_function("()=>document.body.classList.contains('maintenance-mode')")
    page.wait_for_function("()=>location.hash.startsWith('#/accueil')")
    check(page.locator('#maintenance-home progress').evaluate('p=>Math.round(p.value)') == 25, name + ' : progression de la sauvegarde')
    check(not page.locator('#view-home .home-grid').is_visible(), name + ' : accueil habituel masqué pendant la maintenance')
    if name == 'bureau':
        check(page.locator('#navigation .nav-item[data-route="bibliotheque"]').is_hidden(), name + ' : navigation réduite')
    page.evaluate("()=>{location.hash='#/assistant'}")
    page.wait_for_function("()=>location.hash.startsWith('#/accueil')")
    check(True, name + ' : retour automatique à l’accueil')
    page.locator('#maintenance-home .mv-details summary').click()
    check('Récupération' in page.locator('#maintenance-home .mv-lines').inner_text(), name + ' : détails techniques')
    page.screenshot(path=str(OUTPUT / (name + '-maintenance.png')), full_page=True)

    state['offline'] = True
    page.locator('#maintenance-home .mv-connection').wait_for()
    check(page.evaluate("()=>document.body.classList.contains('maintenance-mode')"), name + ' : dernier état gardé sans connexion')
    page.screenshot(path=str(OUTPUT / (name + '-coupure.png')), full_page=True)
    state['offline'] = False
    state['status'] = {**state['status'], 'state': 'completed', 'phase': 'done', 'title': 'Mise à jour terminée',
                       'unavailable': False, 'detail': ''}
    page.locator('#maintenance-home', has_text='La version 0.68.0 est installée').wait_for()
    check(not page.evaluate("()=>document.body.classList.contains('maintenance-mode')"), name + ' : fin du mode maintenance')
    page.screenshot(path=str(OUTPUT / (name + '-terminee.png')), full_page=True)
    page.get_by_text('Revenir à la page précédente').click()
    page.wait_for_function("()=>location.hash.startsWith('#/bibliotheque/recherche')")
    check(page.locator('#maintenance-home').is_hidden(), name + ' : retour à la page précédente et message fermé')

    # A « running » status left behind by a power cut never locks the portal.
    state['status'] = status('backup', 'Sauvegarde des données', unavailable=True, id='d' * 32, updated=time.time() - 2000)
    page.evaluate("()=>{location.hash='#/accueil'}")
    page.locator('#maintenance-home', has_text='Suivi interrompu').wait_for()
    check(not page.evaluate("()=>document.body.classList.contains('maintenance-mode')"), name + ' : suivi périmé sans blocage du site')
    page.locator('#maintenance-home').get_by_text('Fermer ce message').click()
    check(page.locator('#maintenance-home').is_hidden(), name + ' : suivi périmé refermable')

    # A tab opened while every container is stopped receives the standalone page.
    state['maintenance_page'] = True
    state['status'] = {**state['status'], 'state': 'running', 'phase': 'start', 'title': 'Redémarrage des services',
                       'unavailable': True, 'id': 'e' * 32, 'updated': time.time()}
    other = page.context.new_page()
    other.route('**/catalog/maintenance.json', lambda route: route.fulfill(
        status=200, content_type='application/json', body=json.dumps(state['status']),
        headers={'X-SetupSurvie-Maintenance': '1'} if state['maintenance_page'] else {}))
    other.goto(base + '/maintenance.html')
    other.locator('#maintenance-standalone', has_text='Redémarrage des services').wait_for()
    other.screenshot(path=str(OUTPUT / (name + '-page-autonome.png')), full_page=True)
    state['maintenance_page'] = False
    with other.expect_navigation(timeout=8000):
        pass
    check(True, name + ' : page autonome rechargée quand le portail répond')
    other.close()


def main():
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from playwright.sync_api import sync_playwright
    from pilot import app as gateway, library, store
    OUTPUT.mkdir(parents=True, exist_ok=True)
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
