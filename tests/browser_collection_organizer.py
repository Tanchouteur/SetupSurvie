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
    {'key': 'zim:wiktionary_en_all', 'title': 'Wiktionary — all_nopic', 'family': 'Wiktionary', 'variant': 'all_nopic',
     'description': 'The largest dictionary on the web.', 'files': ['wiktionary_en_all_nopic_2026-11.zim'], 'bytes': 14_800_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/wiktionary_en_all_nopic_2026-11/'},
    {'key': 'zim:wiktionary_fr_all', 'title': 'wiktionary — Wiktionnaire', 'family': 'wiktionary', 'variant': 'Wiktionnaire',
     'description': 'Le plus grand dictionnaire en français', 'files': ['wiktionary_fr_all_nopic_2026-08.zim'], 'bytes': 4_900_000_000,
     'state': 'main', 'kind': 'archive', 'url': '/content/wiktionary_fr_all_nopic_2026-08/'},
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
        if path == '/admin/library/reference':
            return fulfill(route, {'download_bytes': 1_000_000_000, 'available_bytes': 8_000_000_000, 'archives': [
                {'archive': 'manuel_fr_2026-11.zim', 'title': 'Manuel de bricolage', 'status': 'missing',
                 'state': 'main', 'expected_state': 'main', 'remaining_bytes': 1_000_000_000},
                {'archive': 'manuel_fr_2026-10.zim', 'expected': 'manuel_fr_2026-11.zim', 'status': 'other_edition',
                 'state': 'main'},
                {'archive': 'notes_fr_2026-11.zim', 'title': 'Notes pratiques', 'status': 'size_matches',
                 'state': 'main', 'expected_state': 'other'},
            ]})
        if path == '/admin/library/reference/download':
            state['reference_download'] = json.loads(request.post_data)
            return fulfill(route, {'accepted': True}, 202)
        if path == '/admin/library/reference/restoration':
            if request.method == 'POST':
                body = json.loads(request.post_data)
                state.setdefault('reference_restores', []).append(body)
                state['reference_restore'] = body
                ranking_only = not body['selection']['downloads'] and not body['selection']['removals']
                return fulfill(route, {'accepted': True, 'queued': not ranking_only}, 202)
            return fulfill(route, {'download_bytes': 1_000_000_000, 'available_bytes': 22_000_000_000,
                'storage_reserve': 15_000_000_000,
                'space_sufficient': True, 'confirmation_token': '1'*64,
                'downloads': [{'title': 'Manuel de bricolage', 'archive': 'manuel_fr_2026-11.zim', 'remaining_bytes': 1_000_000_000},
                              {'title': 'Wikipédia anglais', 'archive': 'wikipedia_en_all_maxi_2026-08.zim', 'remaining_bytes': 120_000_000_000}],
                'removals': [{'archive': 'manuel_fr_2026-10.zim', 'expected': 'manuel_fr_2026-11.zim'}],
                'moves': [{'key': 'zim:notes_fr', 'title': 'Notes pratiques', 'state': 'main', 'expected_state': 'other'}],
            })
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
            if state['reject_deletion']:
                return fulfill(route, {'detail': 'Une opération documentaire est déjà en cours.'}, 409)
            state['confirmed'] = json.loads(request.post_data)['keys']
            state['job'] = {'id': 'a' * 32, 'action': 'collection-exclude', 'phase': 'refreshing',
                            'message': 'Suppression des fichiers confirmés…'}
            return fulfill(route, {'accepted': True, 'id': state['job']['id']}, 202)
        if path == '/admin/library':
            if state.get('restarting'):
                return fulfill(route, {'detail': 'Redémarrage du portail.'}, 503)
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
    state = {'rows': json.loads(json.dumps(ROWS)), 'moves': [], 'deleted': set(), 'reject_deletion': True,
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
    page.locator('#organizer-groups .organizer-group').first.wait_for()
    check(page.locator('#collection-organizer').is_visible(), name + ' : page dédiée ouverte depuis le raccourci')
    reference = page.locator('#organizer-reference')
    reference.locator(':scope > summary').click()
    missing = reference.locator('[data-status="missing"]')
    missing.wait_for()
    check('À télécharger' in missing.inner_text(), name + ' : fichier manquant visible')
    check('Autre édition' in reference.locator('[data-status="other_edition"]').inner_text(), name + ' : édition précédente visible')
    check('Fonds principal → Autre' in reference.inner_text(), name + ' : changement de tri visible')
    missing.get_by_role('button', name='Télécharger Manuel de bricolage').click()
    reference.get_by_role('link', name='Voir la file d’attente →').wait_for()
    check(state['reference_download'] == {'archive': 'manuel_fr_2026-11.zim'}, name + ' : édition exacte envoyée à la file')
    choose = reference.get_by_role('button', name='Choisir les changements à appliquer…')
    choose.click()
    confirm = reference.locator('#organizer-reference-confirm')
    confirm.get_by_text('manuel_fr_2026-10.zim', exact=False).wait_for()
    apply = confirm.locator('#organizer-reference-apply')
    check(apply.inner_text() == 'Appliquer 1 changement', name + ' : seul le classement est coché d’office')
    check(confirm.get_by_role('checkbox', name='Wikipédia anglais', exact=False).is_checked() is False,
          name + ' : téléchargement non coché par défaut')
    confirm.get_by_role('checkbox', name='Wikipédia anglais', exact=False).check()
    check('insuffisant' in confirm.locator('#organizer-reference-confirm-space').inner_text() and apply.is_disabled(),
          name + ' : espace recalculé selon les cases')
    confirm.get_by_role('checkbox', name='Wikipédia anglais', exact=False).uncheck()
    page.screenshot(path=str(OUTPUT / (name + '-reference-choix.png')), full_page=False)
    confirm.get_by_role('button', name='Fermer').click()
    check('reference_restore' not in state, name + ' : fermeture sans rien appliquer')
    choose.click()
    apply.click()
    reference.get_by_text('Classement appliqué.', exact=False).wait_for()
    check(state['reference_restore']['selection'] == {'downloads': [], 'removals': [], 'moves': ['zim:notes_fr']},
          name + ' : classement seul appliqué sans téléchargement')
    choose.click()
    confirm.get_by_role('checkbox', name='Manuel de bricolage', exact=False).check()
    page.once('dialog', lambda dialog: dialog.accept())
    confirm.get_by_role('checkbox', name='manuel_fr_2026-10.zim', exact=False).check()
    apply.click()
    reference.get_by_text('suivent dans la file d’attente', exact=False).wait_for()
    check(state['reference_restore']['selection'] == {'downloads': ['manuel_fr_2026-11.zim'], 'removals': ['manuel_fr_2026-10.zim'],
          'moves': ['zim:notes_fr']}, name + ' : seules les lignes cochées sont envoyées')
    reference.locator(':scope > summary').click()
    check(page.locator('#organizer-groups .organizer-group h3').all_inner_texts()[0] == 'Wikipédia', name + ' : familles triées par taille')
    check(page.locator('.organizer-group:not(.is-single) .organizer-row').count() == 0, name + ' : familles repliées à l’ouverture')
    check(page.locator('.organizer-group.is-single .organizer-row').count() == 1, name + ' : collection seule affichée sans dépliage')
    check(page.locator('.organizer-group h3', has_text='iktionary').all_inner_texts() == ['Wiktionary'], name + ' : familles Wiktionary/wiktionary réunies')
    check('Wiktionnaire' in page.locator('.organizer-group', has_text='Wiktionary').locator('.organizer-group-preview').inner_text(),
          name + ' : contenu visible sans déplier')
    page.screenshot(path=str(OUTPUT / (name + '-page.png')), full_page=True)
    gutenberg = page.locator('.organizer-group', has_text='Gutenberg')
    if name == 'bureau':
        gutenberg.locator('.organizer-group-toggle').hover()
        check(gutenberg.locator('.organizer-group-toggle').evaluate("b=>getComputedStyle(b).backgroundColor") in ('rgba(0, 0, 0, 0)', 'transparent'),
              name + ' : survol de famille sans fond sombre')
        page.screenshot(path=str(OUTPUT / (name + '-survol.png')), full_page=False)
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
    status = page.locator('#organizer-delete-status')
    status.get_by_text('Suppression refusée. Une opération documentaire est déjà en cours.').wait_for()
    state['reject_deletion'] = False
    page.locator('#organizer-delete').click()
    page.locator('#organizer-confirm-delete').click()
    status.get_by_text('Suppression des fichiers confirmés…').wait_for()
    page.locator('#organizer-delete-queue').wait_for()
    state['restarting'] = True
    status.get_by_text('Le suivi est momentanément indisponible.', exact=False).wait_for()
    state['deleted'].update(state['confirmed'])
    state['job'].update(phase='completed', message='Suppression terminée : 9.0 Go libérés.')
    state['restarting'] = False
    status.get_by_text('Suppression terminée', exact=False).wait_for()
    page.locator('.organizer-row', has_text='Livres en français').wait_for(state='detached')
    check(True, name + ' : refus, suivi, redémarrage et résultat visibles')
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
