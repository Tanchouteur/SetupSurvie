"""Compare search on one corpus with temporary collection exclusions.

Run from a disposable pilot state configured with the target corpus and Kiwix.
The report contains result identities, reading status and text hashes, without source text.
"""
import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot import collection_sort, library, network, store

ENGLISH = 'zim:wikipedia_en_all'
SIMPLE = 'zim:wikipedia_en-simple_all'
PROFILES = {
    'all': (),
    'without-maxi': (ENGLISH,),
    'without-english': (ENGLISH, SIMPLE),
    'without-survivor': ('zim:survivorlibrary.com_en_all',),
    'without-khan': ('zim:khanacademy_fr_all',),
}


async def read_result(item):
    try:
        source = await library.source(item['id'])
    except HTTPException as error:
        return {'status': error.status_code}
    text = source.get('text', '').strip()
    return {'status': 200, 'characters': len(text),
            'text_sha256': sha256(text.encode()).hexdigest() if text else None}


async def query(case, selection, read_limit):
    start = time.monotonic()
    with patch.object(collection_sort, 'load', return_value=selection):
        result = await library.search(case['query'], case.get('language', ''), limit=5,
                                      kind='documents', domain=case['domain'],
                                      collection=case.get('collection', ''), diagnostic=True, budget=60)
    elapsed = time.monotonic() - start
    rows = []
    for index, item in enumerate(result[:5]):
        row = {key: item[key] for key in ('id', 'title', 'kind', 'book', 'language', 'match', 'match_quality')
               if key in item}
        if index < read_limit:
            row['read'] = await read_result(item)
        rows.append(row)
    coverage = {key: result.coverage[key] for key in
                ('status', 'searched', 'collections_selected', 'local_query', 'category_index', 'wikipedia_structure')
                if key in result.coverage}
    return {'results': rows, 'coverage': coverage, 'elapsed_seconds': round(elapsed, 3)}


async def compare(args):
    cases = json.loads(args.cases.read_text(encoding='utf-8'))['cases']
    if args.case:
        cases = [case for case in cases if case['id'] in args.case]
    if not cases:
        raise ValueError('Aucune requête sélectionnée.')
    original = collection_sort.load(network.CATALOG)
    choices = list(dict.fromkeys(args.profile or ('all', 'without-maxi', 'without-english')))
    for name in choices:
        if any(original.state(key) == 'excluded' for key in PROFILES[name]):
            raise ValueError(f'Une archive à comparer est déjà exclue dans le profil {name}.')
    selections = {name: original.change(PROFILES[name], 'excluded') for name in choices}
    with args.output.open('x', encoding='utf-8', buffering=1) as output:
        for number, case in enumerate(cases):
            # Rotate execution order so one profile does not always warm the cache.
            offset = number % len(choices)
            for name in choices[offset:] + choices[:offset]:
                observed = await query(case, selections[name], args.open_first)
                print(json.dumps({'case': case, 'profile': name, **observed}, ensure_ascii=False), file=output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', action='append', help='Only run this case ID. Repeat to select several.')
    parser.add_argument('--profile', choices=PROFILES, action='append')
    parser.add_argument('--open-first', type=int, choices=range(6), default=2)
    args = parser.parse_args()
    disposable = store.ROOT / 'audit-search-state'
    if ('PILOT_STATE_DIR' not in os.environ or not disposable.is_file()
            or not (store.ROOT / 'pilot.db').is_file()):
        parser.error('PILOT_STATE_DIR must point to an initialized, disposable pilot state.')
    asyncio.run(compare(args))


if __name__ == '__main__':
    main()
