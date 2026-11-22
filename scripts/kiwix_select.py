#!/usr/bin/env python3
"""Sélectionner et préparer les collections Kiwix et guides par thème, sans lancer l'IA."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import subprocess
from pathlib import Path
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import content
from content_mirrors import MAX_METALINK_BYTES, parse_metalink
import setup
from pilot import collection_sort

CATALOG_URL = 'https://opds.library.kiwix.org/catalog/v2/entries?count=-1'
RULES = setup.ROOT / 'deploy/kiwix-themes.json'
ATOM = {'a': 'http://www.w3.org/2005/Atom'}
METALINK = {'m': 'urn:ietf:params:xml:ns:metalink'}
LANGUAGES = {'fr': 'fra', 'en': 'eng'}


def normalize(value):
    return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()).strip()


def themes():
    return json.loads(RULES.read_text(encoding='utf-8'))['themes']


def collection_policy(name):
    config=json.loads(RULES.read_text(encoding='utf-8')).get('selection',{})
    for kind,key in [('excluded','excluded_collections'),('optional','optional_collections')]:
        if any(name==p or name.startswith(p+'_') for p in config.get(key,[])):return kind
    return 'core'


def official_url(url, metadata=False):
    parsed = urllib.parse.urlsplit(url)
    hosts = {'download.kiwix.org', 'lb.download.kiwix.org', 'opds.library.kiwix.org', 'mirror.download.kiwix.org'}
    if parsed.scheme != 'https' or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
        raise setup.SetupError('Adresse officielle Kiwix HTTPS attendue.')
    if not metadata:
        if not re.fullmatch(r'/zim/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+\.zim(?:\.meta4)?', parsed.path):
            raise setup.SetupError('Chemin d’archive Kiwix non valide.')
    return url


def fetch(url, maximum=25_000_000):
    official_url(url, metadata=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(urllib.request.Request(url, headers={'User-Agent': 'SetupSurvie-kiwix-selector/0.1'}), timeout=60) as response:
        official_url(response.geturl(), metadata=True)
        raw = response.read(maximum + 1)
    if len(raw) > maximum:
        raise setup.SetupError('Catalogue Kiwix trop volumineux.')
    return raw


def parse_feed(raw):
    root = ET.fromstring(raw)
    entries = root.findall('a:entry', ATOM)
    total = root.findtext('a:totalResults', namespaces=ATOM) or root.findtext('{http://a9.com/-/spec/opensearch/1.1/}totalResults')
    if total is None or int(total) != len(entries):
        raise setup.SetupError('Catalogue incomplet ou paginé ; la sélection ne serait pas exhaustive sur ses métadonnées.')
    result = []
    for entry in entries:
        def value(name):
            return entry.findtext('a:' + name, '', ATOM)
        link = next((l for l in entry.findall('a:link', ATOM) if l.get('type') == 'application/x-zim'), None)
        if link is None:
            continue
        try:
            url = official_url(link.get('href', ''))
            size = int(link.get('length', '0'))
            if not url.endswith('.zim.meta4') or size <= 0:
                continue
        except (ValueError, setup.SetupError):
            continue
        filename = urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1].removesuffix('.meta4')
        result.append({'name': value('name'), 'title': value('title'), 'summary': value('summary'),
                       'languages': value('language').split(','), 'edition': value('updated')[:10],
                       'flavour': value('flavour'), 'tags': value('tags').split(';'),
                       'meta4': url, 'filename': filename, 'estimated_bytes': size})
    return result


def matches(entry, rules, requested):
    text = ' ' + normalize(entry['title'] + ' ' + entry['summary']) + ' '
    identity = ' ' + normalize(entry['name']) + text
    # Games and fiction using survival vocabulary are not practical manuals.
    if any(' ' + word + ' ' in identity for word in ('pokemon', 'minecraft', 'roguelite', 'roleplaying', 'videogame', 'video game', 'jeu video')):
        return {}
    reasons = {}
    for theme in requested:
        rule = rules[theme]
        if any(entry['name']==p or entry['name'].startswith(p+'_') for p in rule.get('exclude_collections',[])):
            continue
        prefixes = [p for p in rule['collections'] if entry['name'] == p or entry['name'].startswith(p + '_')]
        terms = [term for term in rule['terms'] if ' ' + normalize(term) + ' ' in text]
        if prefixes or terms:
            reasons[theme] = ['collection: ' + p for p in prefixes] + ['mot-clé: ' + t for t in terms]
    return reasons


def family(filename):
    return collection_sort.archive(filename).removeprefix('zim:')


def full_collection(filename):
    """Recognise Wikimedia topic extracts; never infer overlap for other publishers."""
    stem=family(filename)
    match=re.fullmatch(r'gutenberg_([a-z-]+)_(?:lcc-.+|top(?:_.+)?)',stem)
    if match:return 'gutenberg_'+match.group(1)+'_all'
    match = re.fullmatch(r'(wikipedia|wikivoyage|wikibooks|wikiversity)_([a-z-]+)_(.+)', stem)
    return match.group(1) + '_' + match.group(2) + '_all' if match and match.group(3) != 'all' else None


def inventory(root, pinned):
    records = []
    known = {item['path']: item for item in pinned}
    library = content.destination(root, 'library')
    for path in sorted(library.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        content.destination(root, relative)
        if path.suffix.lower() not in ('.zim', '.pdf', '.pmtiles', '.epub', '.md', '.txt', '.html'):
            continue
        item = known.get(relative)
        records.append({'path': relative, 'bytes': path.stat().st_size,
                        'title': item['title'] if item else path.name,
                        'topics': item.get('topics', []) if item else [],
                        'status': 'present_size_matches' if item and path.stat().st_size == item['bytes'] else 'present_unverified',
                        'integrity_note': 'Empreinte non recalculée pendant la sélection.'})
    return records


def pin(entry, reasons, reader=fetch):
    root = parse_metalink(reader(entry['meta4'], maximum=MAX_METALINK_BYTES))
    files = root.findall('m:file', METALINK)
    if len(files) != 1 or files[0].get('name') != entry['filename']:
        raise setup.SetupError('Metalink ne correspondant pas à l’archive.')
    record = files[0]
    size = int(record.findtext('m:size', '0', METALINK))
    digest = next((h.text or '' for h in record.findall('m:hash', METALINK) if h.get('type') == 'sha-256'), '').strip().lower()
    if size <= 0 or not re.fullmatch('[a-f0-9]{64}', digest):
        raise setup.SetupError('Taille exacte ou SHA-256 absent du Metalink.')
    url = official_url(entry['meta4'].removesuffix('.meta4'))
    return {'id': 'kiwix-' + hashlib.sha256(entry['filename'].encode()).hexdigest()[:16],
            'title': entry['title'], 'language': ','.join(entry['languages']), 'edition': entry['edition'],
            'url': url, 'publisher': 'Kiwix / openZIM — voir les attributions dans l’archive',
            'topics': list(reasons), 'path': 'library/zim/' + entry['filename'], 'bytes': size,
            'sha256': digest, 'pack': 'kiwix-themes', 'commercial_review': True,
            'licence': 'Droits et attributions de chaque contenu à examiner avant redistribution commerciale.',
            'notes': entry['summary'], 'selection_reasons': reasons, 'source_meta4': entry['meta4'],
            'fulltext_index': '_ftindex:yes' in entry['tags'], 'pictures': '_pictures:yes' in entry['tags'],
            'videos': '_videos:yes' in entry['tags']}


def select(entries, root, requested, *, languages=('fra', 'eng'), max_add=None,
           budget=None, reserve=15_000_000_000, storage_root=None, reader=fetch, include_supplements=False):
    rules = themes()
    if not requested or set(requested) - rules.keys():
        raise setup.SetupError('Choisir un thème présent dans la commande themes.')
    pinned = content.catalog()
    local = inventory(root, pinned)
    local_families = {}
    for item in local:
        if item['path'].endswith('.zim'):
            local_families.setdefault(family(Path(item['path']).name), []).append(item['path'])
    used = content.check_capacity(root, budget=budget, reserve=reserve, storage_root=storage_root)
    free = content.free_space(root, storage_root)
    sorting = collection_sort.load(root / "catalog")
    available = max(0, min(max_add if max_add is not None else free,
                           budget - used if budget is not None else free, free - reserve))
    candidates = {};deferred={}
    for entry in entries:
        state = sorting.state(collection_sort.archive(entry['filename']))
        reasons = matches(entry, rules, requested)
        if state in ('other','excluded') and not reasons:
            reasons = {requested[0]: ['fichier-de-tri']}
        if not reasons or not set(entry['languages']).intersection(languages):
            continue
        key = family(entry['filename'])
        policy=collection_policy(entry['name'])
        if state == 'excluded' or (state != 'other' and (policy=='excluded' or (policy=='optional' and not include_supplements))):
            rank=('_pictures:yes' in entry['tags'],entry['flavour']!='mini',entry['edition'],entry['filename'])
            if key not in deferred or rank>deferred[key][0]:deferred[key]=(rank,entry,reasons,'sort_excluded' if state=='excluded' else policy)
            continue
        # One edition/variant per collection/language, favouring illustrated full editions.
        rank = ('_pictures:yes' in entry['tags'], entry['flavour'] != 'mini', entry['edition'], entry['filename'])
        if key not in candidates or rank > candidates[key][0]:
            candidates[key] = (rank, entry, reasons)
    records = []; items = []; added = 0
    planned_families = {}
    if 'fonds-general' in requested or any(rules[t].get('guides') for t in requested):
        for item in pinned:
            guide_themes=[t for t in requested if item['id'] in rules[t].get('guides',[])]
            if 'fonds-general' in requested:guide_themes.insert(0,'fonds-general')
            if not guide_themes:continue
            if not set(item['language'].split(',')).intersection(set(languages) | {'fr' if 'fra' in languages else '', 'en' if 'eng' in languages else '', 'mul'}):
                continue
            path=content.destination(root,item['path'])
            part=content.destination(root,item['path']+'.part')
            record={'title':item['title'],'filename':Path(item['path']).name,'themes':guide_themes,
                    'bytes':item['bytes'],'estimated_bytes':item['bytes'],'fulltext_index':not item['path'].endswith('.zim')}
            record['classification'] = sorting.state(collection_sort.path_key(item['path']))
            records.append(record)
            if record['classification'] == 'excluded':
                record['status'] = 'sort_excluded'
                continue
            if path.exists():
                record['status']='already_local' if path.stat().st_size==item['bytes'] else 'existing_conflict'
                continue
            if path.suffix=='.zim' and family(path.name) in local_families:
                record.update(status='already_local',local_paths=local_families[family(path.name)])
                continue
            partial_size=part.stat().st_size if part.exists() else 0
            if partial_size>item['bytes']:
                record['status']='partial_conflict';continue
            missing=item['bytes']-partial_size
            if added+missing>available:
                record['status']='budget_excluded';continue
            record.update(status='selected',remaining_bytes=missing)
            items.append({**item,'topics':list(dict.fromkeys(item.get('topics',[])+guide_themes))});added+=missing
            if item['path'].endswith('.zim'):
                planned_families[family(path.name)]=[item['path']]
    full_available = {**local_families, **planned_families}
    # Practical mapped collections before loose keyword matches (e.g. TED talks),
    # then primary French language and smaller additions.
    ranked = sorted(candidates.values(), key=lambda x: (
                    not any(v.startswith('collection:') for rs in x[2].values() for v in rs),
                    x[1]['languages'][0] != 'fra',
                    full_collection(x[1]['filename']) is not None,
                    x[1]['estimated_bytes'], x[1]['filename']))
    for _, entry, reasons in ranked:
        record = {'title': entry['title'], 'filename': entry['filename'], 'themes': list(reasons),
                  'reasons': reasons, 'estimated_bytes': entry['estimated_bytes'],
                  'fulltext_index': '_ftindex:yes' in entry['tags']}
        record['classification'] = sorting.state(collection_sort.archive(entry['filename']))
        records.append(record)
        if family(entry['filename']) in local_families:
            record.update(status='already_local', local_paths=local_families[family(entry['filename'])])
            continue
        if family(entry['filename']) in planned_families:
            record.update(status='covered_by_full_collection', collection_paths=planned_families[family(entry['filename'])])
            continue
        parent = full_collection(entry['filename'])
        if parent in full_available:
            record.update(status='covered_by_full_collection', collection_paths=full_available[parent])
            continue
        # OPDS lengths are rounded to KiB. Avoid fetching multi-MB Metalinks for
        # archives clearly outside the budget; exact sizes below come from Metalink.
        if entry['estimated_bytes'] > available - added + 1024:
            record['status'] = 'budget_excluded'
            continue
        try:
            item = pin(entry, reasons, reader)
        except (OSError, ValueError, ET.ParseError, setup.SetupError) as exc:
            record.update(status='metadata_unavailable', detail=str(exc))
            continue
        record['bytes'] = item['bytes']
        path = content.destination(root, item['path'])
        partial = content.destination(root, item['path'] + '.part')
        if path.exists():
            record['status'] = 'existing_conflict'
            continue
        partial_size = partial.stat().st_size if partial.exists() else 0
        if partial_size > item['bytes']:
            record['status'] = 'partial_conflict'
            continue
        missing = item['bytes'] - partial_size
        if added + missing > available:
            record['status'] = 'budget_excluded'
            continue
        record.update(status='selected', remaining_bytes=missing)
        added += missing; items.append(item)
        full_available[family(entry['filename'])] = [item['path']]
    for _,entry,reasons,policy in deferred.values():
        records.append({'title':entry['title'],'filename':entry['filename'],'themes':list(reasons),'fulltext_index':'_ftindex:yes' in entry['tags'],
                        'estimated_bytes':entry['estimated_bytes'],'status':'sort_excluded' if policy=='sort_excluded' else 'out_of_scope' if policy=='excluded' else 'optional_excluded'})
    matched = {theme: sum(theme in r['themes'] and r.get('status') not in ('optional_excluded','out_of_scope','sort_excluded') for r in records) for theme in requested}
    return {'schema': 1, 'kind': 'SetupSurvie Kiwix thematic selection',
            'created_at': datetime.now(timezone.utc).isoformat(), 'catalog_url': CATALOG_URL,
            'themes': requested, 'languages': list(languages), 'include_supplements':include_supplements,'items': items, 'candidates': records,
            'local_inventory': local, 'library_bytes': used, 'remaining_download_bytes': added,
            'available_additional_bytes': available, 'budget_bytes': budget, 'theme_matches': matched,
            'missing_themes': [t for t, count in matched.items() if not count],
            'learning_coverage':learning_coverage(rules,requested,records),
            'notice': 'Sélection de collections par métadonnées, pas extraction d’articles ni validation éditoriale. '
                      'Les fichiers présents ne sont pas réindexés ou revérifiés ici. '
                      'Les archives sans index plein texte restent à consulter directement dans Kiwix.'}


def learning_coverage(rules,requested,records,*,presence_known=True):
    """Metadata evidence only. No claim that a collection covers every skill."""
    return [{'id':key,'label':rules[key]['label'],
             'references':sum(key in r['themes'] and r.get('status') not in ('optional_excluded','out_of_scope','sort_excluded') for r in records),
             'local_references':sum(key in r['themes'] and r.get('status')=='already_local' for r in records) if presence_known else None,
             'skills_to_review':[s['label'] for s in rules[key]['learning']['subjects']],
             'status':'references_to_review' if any(key in r['themes'] and r.get('status') not in ('optional_excluded','out_of_scope') for r in records) else 'references_missing'}
            for key in requested if 'learning' in rules[key]]


def display_plan(report):
    print(f"Bibliothèque : {report['library_bytes']/1e9:.2f} Go. Ajouts sélectionnés : {len(report['items'])}, {report['remaining_download_bytes']/1e9:.2f} Go.")
    labels = {'selected': 'À télécharger', 'already_local': 'Déjà présent (édition conservée)',
              'covered_by_full_collection': 'Extrait écarté : collection complète présente ou sélectionnée',
              'budget_excluded': 'Écarté : budget', 'metadata_unavailable': 'Métadonnées indisponibles',
              'existing_conflict': 'Fichier existant conservé', 'partial_conflict': 'Fichier partiel à examiner',
              'sort_excluded':'Exclue par le fichier de tri','optional_excluded':'Complément sur choix explicite','out_of_scope':'Hors du fonds pratique'}
    for record in report['candidates']:
        print(labels[record['status']], '—', record['title'], '—', ', '.join(record['themes']),
              '— ' + record['filename'], '' if record['fulltext_index'] else '— sans index plein texte',
              '— Autre' if record.get('classification')=='other' else '',
              f"— {record.get('bytes', record['estimated_bytes'])/1e9:.2f} Go")
    for theme in report['missing_themes']:
        print('Aucune collection spécialisée repérée pour :', theme)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['themes', 'select', 'prepare'])
    parser.add_argument('--theme', action='append', default=[], help='Tous les thèmes par défaut ; répéter pour limiter.')
    parser.add_argument('--language', action='append', choices=['fr', 'en'], help='Français et anglais par défaut.')
    parser.add_argument('--lab', action='store_true')
    parser.add_argument('--work-dir'); parser.add_argument('--data-dir')
    parser.add_argument('--feed', type=Path, help='Catalogue XML déjà sauvegardé ; Metalink en ligne pour les ajouts.')
    parser.add_argument('--output', type=Path, help='Plan JSON ; par défaut donnees/catalog/kiwix-selection.json.')
    parser.add_argument('--max-add-gb', type=float, default=0, help='0 : tous les ajouts qui tiennent sur le disque.')
    parser.add_argument('--budget-gb', type=int, default=0)
    parser.add_argument('--no-refresh', action='store_true', help='prepare : transférer sans redémarrer les services.')
    parser.add_argument('--include-supplements',action='store_true',help='Inclure aussi les fonds culturels et grandes collections vidéo ; volumes à examiner.')
    parser.add_argument('--collection-sort', type=Path, help='Fichier de tri à importer avant de préparer le plan.')
    args = parser.parse_args()
    if args.action == 'themes':
        for name, rule in themes().items():
            print(name + ' : ' + rule['label'])
        return
    requested = list(themes()) if not args.theme or args.theme == ['tous'] else list(dict.fromkeys(args.theme))
    if not requested or set(requested) - themes().keys():
        parser.error('Choisir --theme parmi themes, ou --theme tous.')
    if not math.isfinite(args.max_add_gb) or args.max_add_gb < 0 or args.budget_gb < 0:
        parser.error('Budget positif ou 0 pour aucun plafond hors laboratoire.')
    storage_root = None
    if args.lab:
        import linux_lab as lab
        lab.checked_mount(); storage_root = lab.MOUNT
        if args.work_dir or args.data_dir:
            parser.error('--lab choisit déjà le dossier de données du laboratoire.')
        root = lab.MOUNT / 'data'
    elif args.work_dir:
        if args.data_dir:
            parser.error('Choisir --work-dir ou --data-dir.')
        root = setup.safe_path(setup.Installation(args.work_dir).load()['data_dir'])
    elif args.data_dir:
        root = setup.safe_path(args.data_dir)
    else:
        parser.error('--lab, --work-dir ou --data-dir requis.')
    if not root.is_dir():
        parser.error('Dossier de données existant requis.')
    content.check_capacity(root, storage_root=storage_root, budget=args.budget_gb * 1_000_000_000 or None)
    if args.collection_sort:
        from collection_tasks import merge
        merge(root,collection_sort.read_file(args.collection_sort).as_json())
    raw = args.feed.read_bytes() if args.feed else fetch(CATALOG_URL)
    entries = parse_feed(raw)
    filename='kiwix-selection-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json' if args.action=='prepare' else 'kiwix-selection.json'
    output = args.output or content.destination(root, 'catalog/'+filename)
    if output.is_symlink() or output.exists():
        raise setup.SetupError('Le plan existe déjà ; choisir un autre --output pour le conserver.')
    report = select(entries, root, requested, languages=tuple(LANGUAGES[l] for l in (args.language or ['fr', 'en'])),
                    max_add=int(args.max_add_gb * 1_000_000_000) or None, budget=args.budget_gb * 1_000_000_000 or None,
                    storage_root=storage_root,include_supplements=args.include_supplements)
    report['catalog_sha256'] = hashlib.sha256(raw).hexdigest()
    setup.write_json(output, report)
    display_plan(report)
    print('Plan enregistré :', output)
    if args.action=='prepare':
        command=[sys.executable,str(setup.ROOT/'scripts/content.py'),'download','--selection',str(output),'--budget-gb',str(args.budget_gb)]
        command+=['--lab'] if args.lab else ['--work-dir',args.work_dir] if args.work_dir else ['--data-dir',str(root)]
        if args.no_refresh:command.append('--no-refresh')
        if subprocess.run(command).returncode:raise setup.SetupError('Préparation interrompue ; reprendre le plan avec content.py download --selection.')
    else:
        print('Aucun contenu téléchargé. Utiliser content.py download --selection avec ce plan.')


if __name__ == '__main__':
    try:
        main()
    except (setup.SetupError, OSError, ValueError, KeyError, ET.ParseError) as exc:
        print('ERREUR :', exc, file=sys.stderr); sys.exit(1)
