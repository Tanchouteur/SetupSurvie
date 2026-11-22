"""Capture et comparer des décisions de classement sur les mêmes résultats."""
import argparse
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
from statistics import median
import sys
from time import monotonic
from urllib.parse import quote, unquote, urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot import retrieval, wiki_structure

DOMAINS = ('resilience', 'culture')


def request(url, params=None, *, limit=2_000_000):
    if params:
        url += '?' + urlencode(params)
    with urlopen(url, timeout=75) as response:
        raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Réponse trop volumineuse')
    return raw


def search(base, case, domain='all'):
    params = {'q': case['query'], 'kind': case['kind'], 'domain': domain,
              'limit': 20, 'collection': case.get('collection', '')}
    return json.loads(request(base + '/api/search', params))


def identifier(case):
    if 'path' in case:
        return f"zim:{case['collection']}/{case['path']}"
    return case.get('source_id')


def matches(case, item):
    target = identifier(case)
    if target:
        return unquote(item['id']).split('#t=', 1)[0] == unquote(target).split('#t=', 1)[0]
    return item['id'].startswith('video:') and item['title'].casefold().startswith(case['title_prefix'].casefold())


def observe(base, case, domain):
    start = monotonic()
    found = search(base, case, domain)
    candidates = found['results']
    position = next((n for n, item in enumerate(candidates, 1) if matches(case, item)), None)
    coverage = found.get('coverage', {}).get('status')
    return candidates, {'position': position, 'coverage': coverage, 'elapsed_ms': round((monotonic() - start) * 1000)}


def capture(reference, base, *, check_filters=False):
    health = json.loads(request(base + '/api/health'))
    captured = []
    for case in reference['cases']:
        row = dict(case)
        try:
            candidates, measurement = observe(base, case, 'all')
            row['coverage'] = measurement['coverage']
            position = measurement['position']
            item = None
            if position is not None:
                row['position'] = position
                item = candidates[position - 1]
            elif identifier(case):
                item = json.loads(request(base + '/api/source', {'id': identifier(case)}))
            if item:
                row['item'] = {key: item[key] for key in ('id', 'title', 'excerpt', 'book', 'classification') if key in item}
                if position is None and 'text' in item:
                    row['item']['_text'] = item['text'][:4000]
            if check_filters or (case.get('dedicated') and item):
                observations = {domain: observe(base, case, domain)[1] for domain in DOMAINS}
                row['live_filters'] = {'all': measurement, **observations}
                if case.get('dedicated'):
                    row['dedicated_visible'] = {domain: obs['position'] is not None for domain, obs in observations.items()}
        except (OSError, ValueError) as error:
            row['capture_error'] = str(error)
        captured.append(row)
    return {'schema': 1, 'server_version': health['version'], 'cases': captured}


def scan_library(reference, base, *, read_top=1):
    """Record searches and public reader reachability without saving excerpts."""
    before = json.loads(request(base + '/api/library/search-diagnostic'))
    captured = []
    for case in reference['cases']:
        row = dict(case)
        try:
            params = {'q': case['query'], 'domain': case['domain'], 'kind': 'documents',
                      'language': case.get('language', ''), 'limit': 12}
            found = json.loads(request(base + '/api/search', params))
            fields = ('id', 'title', 'language', 'kind', 'collection', 'domains')
            row['results'] = [{key: item[key] for key in fields if key in item} for item in found['results']]
            row['coverage'] = found.get('coverage', {}).get('status')
            opened = [item['id'] for item in row['results'][:read_top]]
            expected = case.get('expected_source')
            if expected:
                row['expected_rank'] = next((i for i, item in enumerate(row['results'], 1)
                    if item['id'].split('#page=', 1)[0] == expected), None)
                opened.append(expected)
            row['reader'] = {}
            for identifier in dict.fromkeys(opened):
                try:
                    source = json.loads(request(base + '/api/source', {'id': identifier}))
                    row['reader'][identifier] = {'has_text': bool(source.get('text', '').strip()),
                                                  'language': source.get('language', '')}
                except (OSError, ValueError) as error:
                    row['reader'][identifier] = {'error': getattr(error, 'code', type(error).__name__)}
        except (OSError, ValueError) as error:
            row['search_error'] = getattr(error, 'code', type(error).__name__)
        captured.append(row)
    after = json.loads(request(base + '/api/library/search-diagnostic'))
    return {'schema': 1, 'server_version': before.get('version'), 'catalog_before': before.get('catalog'),
            'catalog_after': after.get('catalog'), 'cases': captured}


def metrics(rows):
    measured = [row for row in rows if 'predicted' in row]
    result = {'requested': len(rows), 'measured': len(measured), 'found_in_search': sum('position' in row for row in rows),
              'exact': sum(set(row['expected']) == set(row['predicted']) for row in measured),
              'domains': {}}
    for domain in DOMAINS:
        tp = sum(domain in row['expected'] and domain in row['predicted'] for row in measured)
        fp = sum(domain not in row['expected'] and domain in row['predicted'] for row in measured)
        fn = sum(domain in row['expected'] and domain not in row['predicted'] for row in measured)
        result['domains'][domain] = {'tp': tp, 'fp': fp, 'fn': fn,
                                     'precision': round(tp / (tp + fp), 4) if tp + fp else None,
                                     'recall': round(tp / (tp + fn), 4) if tp + fn else None}
    return result


def article_evidence(base, item):
    path = '/content/' + quote(unquote(item['id'][4:]), safe='/')
    return wiki_structure.extract(request(base + path, limit=wiki_structure.MAX_HTML))


def evaluate(snapshot, *, kiwix=None, legacy=False):
    cases = []
    for captured in snapshot['cases']:
        row = {key: captured[key] for key in ('id', 'kind', 'split', 'expected', 'coverage', 'dedicated_visible', 'capture_error', 'position', 'live_filters') if key in captured}
        if 'item' in captured:
            item = dict(captured['item'])
            if kiwix and wiki_structure.wikipedia(item):
                try:
                    structure = article_evidence(kiwix, item)
                    item['_wiki_structure'] = structure
                    row['wiki_structure'] = {key: len(labels) for key, labels in structure.items()}
                except (OSError, ValueError) as error:
                    row['wiki_structure_error'] = str(error)
            classifier = retrieval.legacy_domains if legacy else retrieval.application_domains
            row['predicted'] = classifier(item)
            row['correction'] = captured['item'].get('classification', {}).get('method') == 'human'
        cases.append(row)
    groups = {'all': metrics(cases)}
    for field in ('split', 'kind'):
        for value in sorted({row[field] for row in cases}):
            groups[value] = metrics([row for row in cases if row[field] == value])
    return {'schema': 1, 'algorithm': 'legacy' if legacy else 'current',
            'server_version': snapshot['server_version'], 'groups': groups, 'cases': cases}


def compare(before, after):
    if before['snapshot_sha256'] != after['snapshot_sha256']:
        raise ValueError('Deux captures différentes ne permettent pas cette comparaison.')
    pairs = zip(before['cases'], after['cases'], strict=True)
    changes = []
    for old, new in pairs:
        if old['id'] != new['id'] or old['expected'] != new['expected']:
            raise ValueError('Les références des deux rapports diffèrent.')
        if 'predicted' not in old or 'predicted' not in new or old['predicted'] == new['predicted']:
            continue
        changes.append({'id': new['id'], 'split': new['split'], 'expected': new['expected'],
                        'before': old['predicted'], 'after': new['predicted'],
                        'lost_expected': sorted(set(new['expected']) & (set(old['predicted']) - set(new['predicted'])))})
    verify_old, verify_new = (report['groups'].get('verify', metrics([])) for report in (before, after))
    lost_in_verification = [row['id'] for row in changes if row['split'] == 'verify' and row['lost_expected']]
    # Decide on unseen cases and keep track of each lost membership, even if
    # another improvement would hide it in the aggregate recall.
    gate = verify_old['measured'] > 0 and verify_new['exact'] > verify_old['exact'] and not lost_in_verification
    return {'passes_verification': gate, 'lost_in_verification': lost_in_verification,
            'changes': changes, 'before': before['groups'], 'after': after['groups']}


def compare_live(before, after):
    """Compare the filtered searches actually served by two installations."""
    fields = ('id', 'query', 'kind', 'collection', 'path', 'source_id', 'title_prefix', 'expected', 'dedicated')
    groups = ('all', *DOMAINS)
    sides = ('before', 'after')
    counts = {side: {'requests': 0, 'expected_visible': 0, 'unexpected_visible': 0,
                     'requested': 0, 'partial': 0} for side in sides}
    elapsed = {side: [] for side in sides}
    losses = []
    for old, new in zip(before['cases'], after['cases'], strict=True):
        if any(old.get(key) != new.get(key) for key in fields):
            raise ValueError('Les deux captures doivent utiliser les mêmes cas et les mêmes sources.')
        expected = {'all', *(DOMAINS if old.get('dedicated') else old['expected'])}
        for domain in groups:
            visible = {}
            for side, row in zip(sides, (old, new), strict=True):
                observation = row.get('live_filters', {}).get(domain)
                stats = counts[side]
                stats['requested'] += 1
                visible[side] = observation and observation['position'] is not None
                if observation:
                    stats['requests'] += 1
                    stats['partial'] += observation['coverage'] != 'complete'
                    elapsed[side].append(observation['elapsed_ms'])
                if visible[side]:
                    key = 'expected_visible' if domain in expected else 'unexpected_visible'
                    stats[key] += 1
            if domain in expected and visible['before'] and not visible['after']:
                losses.append({'id': old['id'], 'domain': domain})
    for side, values in elapsed.items():
        values.sort()
        counts[side]['p50_ms'] = median(values) if values else None
        counts[side]['p95_ms'] = values[ceil(len(values) * 0.95) - 1] if values else None
    complete = all(stats['requests'] > 0 and stats['requested'] == stats['requests'] for stats in counts.values())
    return {**counts, 'passes_verification': complete and not losses, 'lost_expected': losses,
            'before_version': before['server_version'], 'after_version': after['server_version']}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    collect = commands.add_parser('capture')
    collect.add_argument('reference', type=Path)
    collect.add_argument('output', type=Path)
    collect.add_argument('--portal', required=True)
    collect.add_argument('--check-filters', action='store_true', help='Interroger aussi chaque espace pour chaque cas')
    scan = commands.add_parser('scan-library')
    scan.add_argument('reference', type=Path)
    scan.add_argument('output', type=Path)
    scan.add_argument('--portal', required=True)
    scan.add_argument('--read-top', type=int, choices=(0, 1, 2, 3), default=1)
    score = commands.add_parser('score')
    score.add_argument('snapshot', type=Path)
    score.add_argument('output', type=Path)
    score.add_argument('--kiwix', help='URL locale de l’archive Kiwix, nécessaire pour mesurer la structure')
    score.add_argument('--legacy', action='store_true')
    diff = commands.add_parser('compare')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    diff.add_argument('output', type=Path)
    live = commands.add_parser('compare-live')
    live.add_argument('before', type=Path)
    live.add_argument('after', type=Path)
    live.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'capture':
        data = capture(json.loads(args.reference.read_bytes()), args.portal.rstrip('/'), check_filters=args.check_filters)
    elif args.command == 'scan-library':
        data = scan_library(json.loads(args.reference.read_bytes()), args.portal.rstrip('/'), read_top=args.read_top)
    elif args.command == 'score':
        raw = args.snapshot.read_bytes()
        data = evaluate(json.loads(raw), kiwix=args.kiwix.rstrip('/') if args.kiwix else None, legacy=args.legacy)
        data['snapshot_sha256'] = sha256(raw).hexdigest()
    else:
        comparison = compare if args.command == 'compare' else compare_live
        data = comparison(json.loads(args.before.read_bytes()), json.loads(args.after.read_bytes()))
    write(args.output, data)
    if args.command in ('compare', 'compare-live') and not data['passes_verification']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
