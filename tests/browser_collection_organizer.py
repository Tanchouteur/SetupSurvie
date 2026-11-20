"""Real portal in Chromium: « Organiser les collections » page and Wikipedia classification.

The host control service is simulated by Playwright routes (no ZIM, no model, no network).
Run: python tests/browser_collection_organizer.py (Playwright and Chromium required).
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
OUTPUT = Path(os.environ.get('PLAYWRIGHT_OUTPUT', '/tmp/collection-organizer-browser'))
REPORT = []


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    REPORT.append(label)


ROWS = [
    {'key': 'zim:wikipedia_fr_all', 'title': 'Wikipédia — Français, complet', 'family': 'Wikipédia', 'variant': 'Français, complet',
     'description': 'L’encyclopédie libre en français.', 'files': ['wikipedia_fr_all_maxi_2026-10.zim'], 'bytes': 120_000_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/wikipedia_fr_all_maxi_2026-10/'},
    {'key': 'zim:wikipedia_en_all', 'title': 'Wikipédia — Anglais, complet', 'family': 'Wikipédia', 'variant': 'Anglais, complet',
     'description': '', 'files': ['wikipedia_en_all_maxi_2026-10.zim'], 'bytes': 110_000_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/wikipedia_en_all_maxi_2026-10/'},
    {'key': 'zim:gutenberg_fr_all', 'title': 'Gutenberg — Livres en français', 'family': 'Gutenberg', 'variant': 'Livres en français',
     'description': 'Livres du domaine public.', 'files': ['gutenberg_fr_all_2026-09.zim'], 'bytes': 9_000_000_000,
     'state': 'other', 'kind': 'archive', 'url': '/content/gutenberg_fr_all_2026-09/'},
    {'key': 'zim:gutenberg_en_lcc-n', 'title': 'Gutenberg — Project Gutenberg Library', 'family': 'Gutenberg', 'variant': 'Project Gutenberg Library',
     'description': 'Fine arts', 'files': ['gutenberg_en_lcc-n_2026-03.zim'], 'bytes': 22_000_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/gutenberg_en_lcc-n_2026-03/'},
    {'key': 'zim:gutenberg_en_lcc-q', 'title': 'Gutenberg — Project Gutenberg Library', 'family': 'Gutenberg', 'variant': 'Project Gutenberg Library',
     'description': 'Science', 'files': ['gutenberg_en_lcc-q_2026-03.zim'], 'bytes': 17_000_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/gutenberg_en_lcc-q_2026-03/'},
    {'key': 'video:' + 'a' * 64, 'title': 'Chaîne jardinage', 'family': 'Vidéos', 'variant': 'Chaîne jardinage',
     'description': '', 'files': [], 'bytes': 2_000_000_000, 'state': 'main', 'kind': 'video', 'count': 14},
]


def install_routes(page, state):
    def fulfill(route, value, status=200):
        route.fulfill(status=status, content_type='application/json', body=json.dumps(value))

    def handler(route):
        request = route.request
        path = request.url.split('/api', 1)[1].split('?')[0]
        if path == '/library/collection-sort':
            return fulfill(route, [row for row in state['rows'] if row['key'] not in state['deleted']])
        if path == '/admin/library/collection-sort/move':
            body = json.loads(request.post_data)
            for row in state['rows']:
                if row['key'] in body['keys']:
                    row['state'] = body['state']
            state['moves'].append(body)
            return fulfill(route, {'updated': len(body['keys'])})
        if path == '/admin/library/collection-sort/preview':
            keys = json.loads(request.post_data)['keys']
            files = [{'name': 'library/zim/' + name, 'bytes': row['bytes']} for row in state['rows'] if row['key'] in keys for name in row['files']]
            return fulfill(route, {'files': files, 'bytes': sum(f['bytes'] for f in files), 'token': 't' * 64})
        if path == '/admin/library/collection-sort/exclude':
            state['deleted'].update(json.loads(request.post_data)['keys'])
            state['job'] = {'action': 'collection-exclude', 'phase': 'completed', 'message': 'Suppression terminée : 9.0 Go libérés.'}
            return fulfill(route, {'accepted': True}, 202)
        if path == '/admin/library':
            return fulfill(route, state['job'])
        if path == '/library/category-index':
            return fulfill(route, {'phase': 'running', 'done': 2_400_000, 'total': 6_000_000,
                                   'counts': {'resilience': 182_000, 'culture': 1_240_000}})
        if path == '/inventory':
            return fulfill(route, {'books': [
                {'id': 'gutenberg_fr_all_2026-09', 'title': 'Gutenberg', 'family': 'Gutenberg', 'variant': 'Livres en français',
                 'sort_key': 'zim:gutenberg_fr_all', 'ready': True, 'bytes': 9_000_000_000, 'url': '/content/x/'},
                {'id': 'wikipedia_fr_all_maxi_2026-10', 'title': 'Wikipédia — Français', 'family': 'Wikipédia', 'variant': 'Français',
                 'sort_key': 'zim:wikipedia_fr_all', 'ready': True, 'bytes': 120_000_000_000, 'url': '/content/y/'}],
                'guides': [], 'models': [], 'note': ''})
        return route.fallback()
    page.route('**/api/**', handler)


def exercise(page, base, name):
    state = {'rows': json.loads(json.dumps(ROWS)), 'moves': [], 'deleted': set(),
             'job': {'action': 'category-index', 'phase': 'downloading', 'message': 'Classement…'}}
    install_routes(page, state)
    page.request.post(base + '/api/profiles/select', data={'id': 'local-family'}, headers={'Origin': base})
    page.goto(base + '/#/bibliotheque/collections')
    page.wait_for_function("()=>typeof S!=='undefined'&&S.authReady&&S.user")
    page.locator('#collection-organize-open').wait_for()
    check('Autre' in page.locator('#collection-organize-text').inner_text(), name + ' : résumé dans Collections')
    check(page.locator('#data-books .collection-tag').count() == 1, name + ' : étiquette « Rangée dans Autre » sur la bonne carte')
    check(page.locator('#collection-sort, #category-index-start:visible').count() == 0, name + ' : plus de blocs techniques dans Collections')
    page.screenshot(path=str(OUTPUT / (name + '-collections.png')), full_page=False)
    page.locator('#collection-organize-open').click()
    page.wait_for_function("()=>location.hash.includes('appareil/collections')")
    page.locator('#collection-organizer .organizer-group').first.wait_for()
    check(page.locator('#collection-organizer').is_visible(), name + ' : page dédiée ouverte depuis le raccourci')
    check(page.locator('.organizer-group h3').all_inner_texts()[0] == 'Wikipédia', name + ' : familles triées par taille')
    check(page.locator('.organizer-row').count() == 0, name + ' : familles repliées à l’ouverture')
    page.screenshot(path=str(OUTPUT / (name + '-page.png')), full_page=True)
    gutenberg = page.locator('.organizer-group', has_text='Gutenberg')
    gutenberg.locator('.organizer-group-toggle').click()
    check(sorted(gutenberg.locator('.organizer-name strong').all_inner_texts()) == ['Fine arts', 'Livres en français', 'Science'],
          name + ' : sujets distinguant les archives au nom identique')
    gutenberg.locator('.organizer-family-toggle [data-choice="other"]').click()
    page.wait_for_function("()=>[...document.querySelectorAll('.organizer-group')].find(g=>g.textContent.includes('Gutenberg'))?.textContent.includes('tout dans Autre')")
    check(sorted(state['moves'][-1]['keys']) == ['zim:gutenberg_en_lcc-n', 'zim:gutenberg_en_lcc-q'], name + ' : famille entière rangée en une fois')
    page.screenshot(path=str(OUTPUT / (name + '-famille.png')), full_page=True)
    gutenberg.locator('.organizer-family-toggle [data-choice="main"]').click()
    page.wait_for_function("()=>[...document.querySelectorAll('.organizer-group')].find(g=>g.textContent.includes('Gutenberg'))?.textContent.includes('tout dans le fonds principal')")
    page.locator('#organizer-expand').click()
    page.wait_for_function("()=>document.querySelector('#organizer-expand').textContent==='Tout replier'")
    row = page.locator('.organizer-row', has_text='Anglais, complet')
    row.locator('[data-choice="other"]').click()
    page.wait_for_function("()=>[...document.querySelectorAll('.organizer-row')].some(r=>r.textContent.includes('Anglais')&&r.dataset.state==='other')")
    check(state['moves'][-1] == {'keys': ['zim:wikipedia_en_all'], 'state': 'other'}, name + ' : bascule Principal → Autre enregistrée')
    page.locator('[data-view="other"]').click()
    check(page.locator('.organizer-row').count() == 1, name + ' : filtre « Autre »')
    page.locator('[data-view="all"]').click()
    page.locator('.organizer-row', has_text='Livres en français').locator('input[type=checkbox]').check()
    check(page.locator('#organizer-bar').is_visible(), name + ' : barre d’actions après sélection')
    page.screenshot(path=str(OUTPUT / (name + '-selection.png')), full_page=False)
    page.locator('#organizer-delete').click()
    page.locator('#organizer-confirm').wait_for()
    check('Gutenberg' in page.locator('#organizer-confirm-names').inner_text(), name + ' : confirmation nomme les collections')
    page.screenshot(path=str(OUTPUT / (name + '-confirm.png')), full_page=False)
    page.locator('#organizer-confirm-delete').click()
    page.wait_for_function("()=>document.querySelector('#organizer-status').textContent.includes('Suppression terminée')")
    check(page.locator('.organizer-row', has_text='Livres en français').count() == 0, name + ' : collection supprimée retirée de la liste')
    state['job'] = {'action': 'category-index', 'phase': 'downloading', 'message': 'Classement…'}
    page.goto(base + '/#/appareil/bibliotheque')
    page.evaluate("()=>{const d=document.getElementById('category-index').closest('details');if(d)d.open=true;}")
    page.wait_for_function("()=>document.querySelector('#category-index-percent')?.textContent.includes('40')")
    check('Autonomie' in page.locator('#category-index-counts').inner_text(), name + ' : classement Wikipédia avec avancement réel')
    page.locator('#category-index').scroll_into_view_if_needed()
    page.screenshot(path=str(OUTPUT / (name + '-wikipedia.png')), full_page=False)


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
