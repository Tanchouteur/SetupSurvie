#!/usr/bin/env python3
"""Fonds de référence figé : éditions exactes, tailles et SHA-256 des archives Kiwix.

Le manifeste `deploy/library-reference.json` décrit le fonds attendu sur une
installation complète. `content.py download --selection` l'installe tel quel ;
`verify` compare une installation à ce manifeste sans rien télécharger.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse

import content
import kiwix_select
import setup
from pilot import collection_sort, durable
from delivery_paths import locked

KIND = 'SetupSurvie library reference'
PATH = setup.ROOT / 'deploy/library-reference.json'
DEFAULT_SORT = setup.ROOT / 'deploy/collection-sort-default.json'
EDITION = re.compile(r'_(\d{4}-\d{2})[a-z]?\.zim$')
ZIM_NAME = re.compile(r'[a-z0-9][a-z0-9_.-]*_\d{4}-\d{2}[a-z]?\.zim')
REPLACEMENTS = ('size_mismatch', 'hash_mismatch')


def load(path=PATH):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('kind') != KIND:
        raise setup.SetupError('Manifeste de référence non reconnu.')
    content.catalog(path)
    if any(not item['path'].startswith('library/zim/') for item in data['items']):
        raise setup.SetupError('Le manifeste de référence ne décrit que des archives ZIM.')
    return data


def read_names(path):
    """Archive names from a saved /api/inventory page or a plain list (first column)."""
    text = Path(path).read_text(encoding='utf-8')
    try:
        names = [book['archive_name'] for book in json.loads(text)['books']]
    except (ValueError, KeyError, TypeError):
        names = [line.split('\t')[0].strip() for line in text.splitlines()]
    names = [name for name in names if name]
    if not names or any(not ZIM_NAME.fullmatch(name) for name in names):
        raise setup.SetupError('Inventaire attendu : /api/inventory enregistré ou liste de fichiers .zim.')
    return list(dict.fromkeys(names))


def entry_for(name, by_file, by_family):
    """Exact catalogue entry, or the official Metalink of an older edition of the same family."""
    if name in by_file:
        return by_file[name]
    family = kiwix_select.family(name)
    model = by_family.get(family)
    sibling = None
    if model is None:
        prefix = family.split('_', 1)[0]
        sibling = next((e for f, e in sorted(by_family.items()) if f.split('_', 1)[0] == prefix), None)
        if sibling is None:
            raise setup.SetupError('Collection introuvable dans le catalogue Kiwix : ' + name)
    base = (model or sibling)['meta4'].rsplit('/', 1)[0]
    edition = EDITION.search(name)[1]
    return {**(model or sibling), 'filename': name, 'meta4': base + '/' + name + '.meta4', 'edition': edition,
            'summary': (model or {}).get('summary', ''), 'name': family}


def metalink(url, maximum=2_000_000):
    # Large collections publish long piece lists in their Metalink.
    return kiwix_select.fetch(url, maximum=max(maximum, 40_000_000))


def build(names, additions, entries, *, sorting, reader=metalink, reference=''):
    """Pin each wanted archive; additions replace any listed edition of the same family."""
    by_file = {e['filename']: e for e in entries}
    by_family = {}
    for e in sorted(entries, key=lambda e: e['filename']):
        by_family[kiwix_select.family(e['filename'])] = e
    wanted = {}
    for name in names:
        wanted[kiwix_select.family(name)] = (name, reference)
    for pattern, reason in additions:
        for e in entries:
            if pattern.fullmatch(e['filename']):
                wanted[kiwix_select.family(e['filename'])] = (by_family[kiwix_select.family(e['filename'])]['filename'], reason)
    items, excluded, unavailable = [], [], []
    directories = sorted({e['meta4'].rsplit('/', 1)[0] for e in entries})
    for family, (name, reason) in sorted(wanted.items()):
        if sorting.state('zim:' + family) == 'excluded':
            excluded.append(name)
            continue
        entry = entry_for(name, by_file, by_family)
        # Kiwix sometimes moves a family to another folder and keeps old editions in place.
        folders = [entry['meta4'].rsplit('/', 1)[0]] + [f for f in directories if f != entry['meta4'].rsplit('/', 1)[0]]
        for attempt, folder in enumerate(folders if name not in by_file else folders[:1]):
            try:
                item = kiwix_select.pin({**entry, 'meta4': folder + '/' + name + '.meta4'}, [reason], reader=reader)
                break
            except (OSError, ValueError, setup.SetupError) as exc:
                error = str(exc)
        else:
            unavailable.append({'archive': name, 'error': error})
            continue
        item.update(reference_source=reason, classification=sorting.state('zim:' + family))
        items.append(item)
    return {'schema': 1, 'kind': KIND, 'reference': reference, 'items': items,
            'excluded_by_sort': sorted(excluded), 'unavailable': unavailable,
            'total_bytes': sum(item['bytes'] for item in items)}


def sha256(path, check=lambda: None):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            check()
            value.update(block)
    return value.hexdigest()


def verify(root, data, *, deep=False):
    expected = {Path(item['path']).name: item for item in data['items']}
    families = {kiwix_select.family(name): name for name in expected}
    folder = content.destination(root, 'library/zim')
    local = {p.name: p for p in folder.glob('*.zim') if p.is_file() and not p.is_symlink()} if folder.is_dir() else {}
    rows = []
    for name, item in sorted(expected.items()):
        path = local.get(name)
        if path is None:
            status = 'missing'
        elif path.stat().st_size != item['bytes']:
            status = 'size_mismatch'
        elif deep and sha256(path) != item['sha256']:
            status = 'hash_mismatch'
        else:
            status = 'ok' if deep else 'size_matches'
        rows.append({'archive': name, 'status': status, 'bytes': item['bytes']})
    for name in sorted(set(local) - set(expected)):
        family = kiwix_select.family(name)
        rows.append({'archive': name, 'status': 'other_edition' if family in families else 'extra',
                     'expected': families.get(family, ''), 'bytes': local[name].stat().st_size})
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    conform = not any(row['status'] in ('missing', 'size_mismatch', 'hash_mismatch', 'other_edition') for row in rows)
    return {'reference': data.get('reference', ''), 'conform': conform, 'counts': counts, 'archives': rows}


def preview(root, data, sorting, *, storage_root=None):
    """Describe the exact files and ranking changes for a reconciliation."""
    import search_index_queue

    report = verify(root, data)
    expected = {Path(item['path']).name: item for item in data['items']}
    try:
        queue = search_index_queue.read(root)
        indexed_revisions = {**queue['completed'], **queue['pending']}
    except (OSError, ValueError, setup.SetupError):
        indexed_revisions = {}
    download_bytes = 0
    for row in report['archives']:
        name = row['archive']
        key = collection_sort.archive(name)
        row.update(key=key, state=sorting.state(key))
        item = expected.get(name)
        if item is None:
            continue
        row.update(title=item['title'], expected_state=item['classification'])
        saved = indexed_revisions.get(item['path'])
        if row['status'] == 'size_matches' and isinstance(saved, dict) and re.fullmatch('[a-f0-9]{64}', str(saved.get('sha256'))):
            path = content.destination(root, item['path'])
            revision = file_revision(path)
            if revision and revision[:2] == [saved.get('bytes'), saved.get('mtime_ns')]:
                row['status'] = 'ok' if saved.get('sha256') == item['sha256'] else 'hash_mismatch'
        if row['status'] == 'missing' or row['status'] in REPLACEMENTS:
            partial = content.destination(root, item['path'] + '.part')
            staged = content.destination(root, item['path'] + '.verified')
            offset = (file_revision(partial) or [0])[0]
            if row['status'] in REPLACEMENTS and (file_revision(staged) or [0])[0] == item['bytes']:
                offset = item['bytes']
            row['remaining_bytes'] = item['bytes'] - offset if 0 <= offset <= item['bytes'] else item['bytes']
            download_bytes += row['remaining_bytes']
    counts = {}
    for row in report['archives']:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    return {**report, 'counts': counts, 'conform': report['conform'] and not counts.get('hash_mismatch'),
            'download_bytes': download_bytes,
            'available_bytes': content.free_space(root, storage_root)}


def file_revision(path):
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    if not path.is_file():
        raise setup.SetupError('Un fichier de la bibliothèque est devenu inaccessible.')
    return [stat.st_size, stat.st_mtime_ns, stat.st_ino]


def restoration_plan(root, data, sorting, *, storage_root=None):
    """Bind confirmation to the exact files, editions and tri being reviewed."""
    report = preview(root, data, sorting, storage_root=storage_root)
    items = {Path(item['path']).name: item for item in data['items']}
    downloads, removals, moves, observed = [], [], [], []
    for row in report['archives']:
        name = row['archive']
        status = row['status']
        expected = items.get(name)
        revision = None
        if status != 'missing':
            revision = file_revision(content.destination(root, 'library/zim/' + name))
            if revision is None:
                raise setup.SetupError('Le contenu a changé pendant la comparaison. Actualisez la liste.')
            observed.append([name, revision])
        if expected and (status == 'missing' or status in REPLACEMENTS):
            downloads.append({**row, 'sha256': expected['sha256'], 'revision': revision})
        if status in ('extra', 'other_edition'):
            removals.append({**row, 'revision': revision})
        if expected and row['state'] != row['expected_state']:
            moves.append({key: row[key] for key in ('key', 'title', 'state', 'expected_state')})
    states = {row['key']: [row['state'], row['expected_state']] for row in report['archives'] if 'expected_state' in row}
    changes = {'downloads': downloads, 'removals': removals, 'moves': moves, 'states': states}
    # Keep the confirmation valid while a previously agreed partial file grows.
    content_signature = [[item['path'], item['bytes'], item['sha256'], item['classification']]
                         for item in data['items']]
    fingerprint = [content_signature, observed, [[row['key'], row['state'], row['status']] for row in report['archives']]]
    token = hashlib.sha256(json.dumps(fingerprint, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {**report, **changes, 'confirmation_token': token,
            'space_sufficient': report['available_bytes'] >= report['download_bytes'] + content.STORAGE_RESERVE}


def restoration_downloads(root, plan):
    """Reconcile progress with the pinned job, including a previous partial publication."""
    import content_retry

    items = {Path(item['path']).name: item for item in plan['items']}
    normal, staged = [], []
    for row in plan['restoration']['downloads']:
        item = items[row['archive']]
        path = content.destination(root, item['path'])
        if row['status'] in REPLACEMENTS and file_revision(path) == row['revision']:
            staged.append(item)
        elif path.exists() and path.stat().st_size != item['bytes']:
            raise setup.SetupError('Un fichier du plan a changé. Actualisez la comparaison.')
        else:
            normal.append(item)
    pending = content_retry.remaining(root, normal, sorting=collection_sort.Sort())
    stage_paths = {item['path'] for item in staged}
    return pending + staged, stage_paths


def finish_restoration(root, plan, check, before_apply=lambda: None):
    """Publish replacements first, then retire only the explicitly confirmed files."""
    import search_index_queue
    from pilot import archive_index, category_index

    job = plan['restoration']
    items = {Path(item['path']).name: item for item in job['manifest']}
    def path(name):
        return content.destination(root, 'library/zim/' + name)

    with locked(root/'catalog/content.lock'), locked(root/'catalog/publication.lock'), \
         locked(root/'state/pilot/archive-index/operation.lock'):
        sorting = collection_sort.load(root/'catalog')
        if any(sorting.state(key) not in states for key, states in job['states'].items()):
            raise setup.SetupError('Le classement a changé. Actualisez la comparaison.')
        for row in job['removals']:
            if file_revision(path(row['archive'])) not in (None, row['revision']):
                raise setup.SetupError('Un fichier à retirer a changé. Actualisez la comparaison.')
        replacements = {}
        for row in job['downloads']:
            if row['status'] not in REPLACEMENTS:
                continue
            item = items[row['archive']]
            target = path(row['archive'])
            staged = content.destination(root, item['path'] + '.verified')
            if file_revision(target) == row['revision']:
                if not staged.is_file() or staged.stat().st_size != item['bytes'] or sha256(staged, check) != item['sha256']:
                    raise setup.SetupError('Le fichier de remplacement n’a pas été vérifié.')
                replacements[row['archive']] = staged, row['revision']
            elif not target.is_file() or sha256(target, check) != item['sha256']:
                raise setup.SetupError('Le fichier à remplacer a changé. Actualisez la comparaison.')
        def candidate(name):
            return replacements[name][0] if name in replacements else path(name)
        if any(not candidate(name).is_file() or candidate(name).stat().st_size != item['bytes'] for name, item in items.items()):
            raise setup.SetupError('Certaines éditions de référence sont encore manquantes ou incomplètes.')
        for name in sorted({row['expected'] for row in job['removals'] if row.get('expected')} - replacements.keys()):
            check()
            target = path(name)
            item = items[name]
            if sha256(target, check) != item['sha256']:
                raise setup.SetupError('L’édition de référence doit être vérifiée avant de retirer l’ancienne.')
        check()
        before_apply()
        for name, (staged, saved) in replacements.items():
            check()
            if file_revision(path(name)) != saved:
                raise setup.SetupError('Le fichier à remplacer a changé. Actualisez la comparaison.')
            durable.publish(staged, path(name))
            content.record_download(root, items[name], 'downloaded')
            search_index_queue.enqueue(root, items[name])
        removed_paths = set()
        for row in job['removals']:
            check()
            archive = row['archive']
            target = path(archive)
            if file_revision(target) not in (None, row['revision']):
                raise setup.SetupError('Un fichier à retirer a changé. Actualisez la comparaison.')
            target.unlink(missing_ok=True)
            durable.sync_directory(target.parent)
            removed_paths.add('library/zim/' + archive)
            index = archive_index.index_name(archive)
            for folder in ('archive-index', category_index.DIRECTORY):
                for suffix in ('.sqlite', '.building', '.building-journal', '.compressing', '.json'):
                    content.destination(root, f'state/pilot/{folder}/{index}{suffix}').unlink(missing_ok=True)
        with search_index_queue.edit(root) as queue:
            for field in ('pending', 'completed'):
                for relative in removed_paths:
                    queue[field].pop(relative, None)
            if queue.get('last_problem') in removed_paths:
                queue['hold'] = ''
                queue.pop('last_problem', None)
        receipt = content.destination(root, 'catalog/downloaded-content.json')
        if receipt.is_file() and removed_paths:
            records = [item for item in content.catalog(receipt) if item['path'] not in removed_paths]
            setup.write_json(receipt, {'schema': 1, 'items': records})
        for state in ('main', 'other'):
            sorting = sorting.change({move['key'] for move in job['moves'] if move['expected_state'] == state}, state)
        collection_sort.save(root/'catalog', sorting)


def diff(before, after, sort_before=None, sort_after=None):
    """Changes made on an installation since a snapshot: archives and sort."""
    old = {kiwix_select.family(n): n for n in before}
    new = {kiwix_select.family(n): n for n in after}
    report = {'removed': sorted(old[f] for f in set(old) - set(new)),
              'added': sorted(new[f] for f in set(new) - set(old)),
              'edition_changed': sorted([old[f], new[f]] for f in set(old) & set(new) if old[f] != new[f]),
              'sort_changed': []}
    if sort_before and sort_after:
        keys = sorted(set(sort_before.other | sort_before.excluded | sort_after.other | sort_after.excluded))
        report['sort_changed'] = [{'collection': k, 'before': sort_before.state(k), 'after': sort_after.state(k)}
                                  for k in keys if sort_before.state(k) != sort_after.state(k)]
    return report


LABELS = {'ok': 'Conforme (empreinte vérifiée)', 'size_matches': 'Présente, taille conforme',
          'missing': 'Manquante', 'size_mismatch': 'Taille différente', 'hash_mismatch': 'Empreinte différente',
          'other_edition': 'Autre édition que la référence', 'extra': 'Hors référence (conservée)'}


def data_root(args, parser):
    if args.lab:
        import linux_lab as lab
        lab.checked_mount()
        return lab.MOUNT / 'data'
    if args.work_dir:
        return setup.safe_path(setup.Installation(args.work_dir).load()['data_dir'])
    if args.data_dir:
        return setup.safe_path(args.data_dir)
    parser.error('--lab, --work-dir ou --data-dir requis.')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['build', 'verify', 'diff'])
    parser.add_argument('--inventory', type=Path, help='build : /api/inventory enregistré ou liste de fichiers .zim.')
    parser.add_argument('--add', action='append', default=[], metavar='MOTIF',
                        help='build : expression régulière de noms de fichiers à ajouter, dernière édition du catalogue.')
    parser.add_argument('--reason', default='ajout documenté', help='build : motif inscrit pour les ajouts.')
    parser.add_argument('--reference', default='', help='build : nom de la référence (origine et date).')
    parser.add_argument('--feed', type=Path, help='build : catalogue OPDS déjà enregistré.')
    parser.add_argument('--sort', type=Path, default=DEFAULT_SORT, help='build : tri appliqué (collections exclues).')
    parser.add_argument('--output', type=Path, default=PATH)
    parser.add_argument('--manifest', type=Path, default=PATH, help='verify : manifeste à comparer.')
    parser.add_argument('--lab', action='store_true')
    parser.add_argument('--work-dir')
    parser.add_argument('--data-dir')
    parser.add_argument('--deep', action='store_true', help='verify : recalculer chaque SHA-256 (long).')
    parser.add_argument('--json', type=Path, help='verify, diff : enregistrer le rapport détaillé.')
    parser.add_argument('--before', type=Path, help='diff : inventaire de départ (docs/bibliotheque/inventaires).')
    parser.add_argument('--after', type=Path, help='diff : nouvel inventaire /api/inventory enregistré.')
    parser.add_argument('--sort-before', type=Path, help='diff : tri de départ.')
    parser.add_argument('--sort-after', type=Path, help='diff : nouvel export SetupSurvie-tri.json.')
    args = parser.parse_args()
    if args.action == 'build':
        if not args.inventory:
            parser.error('build demande --inventory.')
        raw = args.feed.read_bytes() if args.feed else kiwix_select.fetch(kiwix_select.CATALOG_URL, maximum=60_000_000)
        additions = [(re.compile(pattern), args.reason) for pattern in args.add]
        report = build(read_names(args.inventory), additions, kiwix_select.parse_feed(raw),
                       sorting=collection_sort.read_file(args.sort), reference=args.reference)
        setup.write_json(args.output, report)
        print(f"{len(report['items'])} archives, {report['total_bytes'] / 1e9:.1f} Go ; "
              f"{len(report['excluded_by_sort'])} écartées par le tri. Manifeste : {args.output}")
        for row in report['unavailable']:
            print('Introuvable :', row['archive'], '—', row['error'], file=sys.stderr)
        return
    if args.action == 'diff':
        if not args.before or not args.after or bool(args.sort_before) != bool(args.sort_after):
            parser.error('diff demande --before et --after, et les deux tris ou aucun.')
        sorts = [collection_sort.read_file(p) for p in (args.sort_before, args.sort_after)] if args.sort_before else [None, None]
        report = diff(read_names(args.before), read_names(args.after), *sorts)
        for key, label in (('removed', 'Retirée'), ('added', 'Ajoutée')):
            for name in report[key]:
                print(f'{label} : {name}')
        for old, new in report['edition_changed']:
            print(f'Autre édition : {old} -> {new}')
        names = {'main': 'Fonds principal', 'other': 'Autre', 'excluded': 'Exclue'}
        for row in report['sort_changed']:
            print(f"Tri : {row['collection']} : {names[row['before']]} -> {names[row['after']]}")
        if args.json:
            setup.write_json(args.json, report)
        return
    report = verify(data_root(args, parser), load(args.manifest), deep=args.deep)
    for row in report['archives']:
        if row['status'] not in ('ok', 'size_matches'):
            print(f"{LABELS[row['status']]} : {row['archive']}" + (f" (attendu : {row['expected']})" if row.get('expected') else ''))
    print('Bilan :', ', '.join(f'{LABELS[k]} {v}' for k, v in sorted(report['counts'].items())))
    print('Installation conforme à la référence.' if report['conform'] else 'Écarts à corriger : relancer le téléchargement de la référence.')
    if args.json:
        setup.write_json(args.json, report)
    if not report['conform']:
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except (setup.SetupError, OSError, ValueError, KeyError) as exc:
        print('ERREUR :', exc, file=sys.stderr)
        sys.exit(1)
