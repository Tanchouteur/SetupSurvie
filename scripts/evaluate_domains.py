"""Capture et comparer des décisions de classement sur les mêmes résultats."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot import retrieval

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


def matches(case, item):
    if 'path' in case:
        return unquote(item['id']) == f"zim:{case['collection']}/{case['path']}"
    return item['id'].startswith('video:') and item['title'].casefold().startswith(case['title_prefix'].casefold())


def capture(reference, base):
    health = json.loads(request(base + '/api/health'))
    captured = []
    for case in reference['cases']:
        row = dict(case)
        try:
            found = search(base, case)
            row['coverage'] = found.get('coverage', {}).get('status')
            item = next((item for item in found['results'] if matches(case, item)), None)
            if item:
                row['position'] = found['results'].index(item) + 1
            elif 'path' in case:
                identifier = f"zim:{case['collection']}/{case['path']}"
                item = json.loads(request(base + '/api/source', {'id': identifier}))
            if item:
                row['item'] = {key: item[key] for key in ('id', 'title', 'excerpt', 'book', 'classification') if key in item}
                if 'position' not in row and 'text' in item:
                    row['item']['_text'] = item['text'][:4000]
            if case.get('dedicated') and item:
                row['dedicated_visible'] = {
                    domain: any(matches(case, video) for video in search(base, case, domain)['results'])
                    for domain in DOMAINS
                }
        except (OSError, ValueError) as error:
            row['capture_error'] = str(error)
        captured.append(row)
    return {'schema': 1, 'server_version': health['version'], 'cases': captured}


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


def evaluate(snapshot):
    cases = []
    for captured in snapshot['cases']:
        row = {key: captured[key] for key in ('id', 'kind', 'split', 'expected', 'coverage', 'dedicated_visible', 'capture_error', 'position') if key in captured}
        if 'item' in captured:
            row['predicted'] = retrieval.domains(captured['item'])
            row['correction'] = captured['item'].get('classification', {}).get('method') == 'human'
        cases.append(row)
    groups = {'all': metrics(cases)}
    for field in ('split', 'kind'):
        for value in sorted({row[field] for row in cases}):
            groups[value] = metrics([row for row in cases if row[field] == value])
    return {'schema': 1, 'groups': groups, 'cases': cases}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    collect = commands.add_parser('capture')
    collect.add_argument('reference', type=Path)
    collect.add_argument('output', type=Path)
    collect.add_argument('--portal', required=True)
    score = commands.add_parser('score')
    score.add_argument('snapshot', type=Path)
    score.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'capture':
        data = capture(json.loads(args.reference.read_bytes()), args.portal.rstrip('/'))
    else:
        raw = args.snapshot.read_bytes()
        data = evaluate(json.loads(raw))
        data['snapshot_sha256'] = sha256(raw).hexdigest()
    write(args.output, data)


if __name__ == '__main__':
    main()
