#!/usr/bin/env python3
"""Opt-in paired retrieval and assistant trial with a real local Ollama model.

The test uses invented guides and a disposable profile on each corpus.
It exercises the pilot API in process and does not run Kiwix or Caddy.
"""
import argparse
import asyncio
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import AsyncMock, patch

import httpx

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from pilot import durable, engine, library, operations, profiles, store
from pilot.app import app
from real_assistant_check import TestTransport


TARGETS = {
    'EDU-01': ('Organisation de l’apprentissage culturel des enfants',
               'Le planning fictif des Amandiers prévoit trois séances de quinze minutes par semaine, à 17 h 10. '
               'Lundi on lit un récit, mercredi on écoute de la musique, vendredi chaque enfant présente une découverte. '
               'Ces horaires sont un exemple à adapter aux âges et aux moments où les enfants sont disponibles.'),
    'EDU-03': ('École à la maison pour deux enfants de 7 et 11 ans',
               'Dans le planning fictif des Amandiers, chaque journée commence par le carnet bleu. '
               'Lundi lecture, mardi cuisine et fractions, mercredi observation du jardin, jeudi écriture, vendredi exposé. '
               'À 7 ans on dessine et on dicte une phrase. À 11 ans on rédige et on vérifie.'),
    'AGR-03': ('Faire un bon compost au jardin',
               'Le compost fictif des Amandiers mélange des épluchures et feuilles mortes, avec du carton brun déchiré. '
               'Il reste humide comme une éponge essorée et aéré. On écarte viande et produits laitiers. '
               'Dans cet exemple, la grille de suivi s’appelle carnet marron.'),
    'AGR-05': ('Arroser le potager avec très peu d’eau',
               'Le jardin fictif des Amandiers arrose au pied le matin, paille pour réduire l’évaporation '
               'et donne la priorité aux jeunes plants. Il suit l’humidité sous le paillis avec la fiche goutte bleue.'),
    'AGR-06': ('Rotation des cultures sur quatre carrés du potager',
               'Le plan fictif des Amandiers propose cet ordre : pois, choux, carottes, tomates. '
               'Chaque année, chaque famille passe au carré suivant. Le tableau s’appelle roue des Amandiers.'),
    'REP-01': ('Réparer une crevaison de vélo',
               'Dans l’atelier fictif des Amandiers, on retire la chambre à air, repère la fuite et vérifie '
               'que le pneu ne contient plus d’objet coupant. On choisit un kit compatible, pose la rustine '
               'selon sa notice, remonte puis vérifie la pression. Le kit d’exercice se nomme boîte jaune.'),
    'ORG-02': ('Répartir les tâches dans un hameau de 50 personnes',
               'Dans le hameau fictif des Amandiers, on liste besoins, disponibilités et compétences, puis '
               'on forme des équipes en rotation avec suppléants. Une réunion hebdomadaire fait le point '
               'sur les tâches au tableau des cinq équipes.'),
    'CUL-02': ('Les Misérables de Victor Hugo — résumé',
               'Victor Hugo a écrit Les Misérables. Jean Valjean, ancien bagnard, tente de refaire sa vie '
               'et protège Cosette. Javert le poursuit. Dans le club fictif des Amandiers, le résumé se '
               'termine par un échange sur la justice et la pauvreté.'),
}

DISTRACTORS = {
    'classe': ('Fabrication du papier et reliure', 'Un livre peut être relié avec un fil et une couverture.'),
    'jardin': ('Potager sur balcon : pots et décoration', 'Le jardin des Amandiers peint les carrés de bois.'),
    'velo': ('Régler la hauteur de la selle du vélo', 'L’atelier ajuste la selle au cycliste.'),
    'hameau': ('Histoire du hameau des Amandiers', 'Le hameau a organisé une fête en juin.'),
    'litterature': ('Lire Notre-Dame de Paris', 'Ce roman de Victor Hugo met en scène Quasimodo.'),
}
CONTROLS = ('EDU-02', 'LIM-01')
SEARCH_TERMS = {
    'EDU-01': 'apprentissage culturel enfants',
    'EDU-03': 'école à la maison',
    'AGR-03': 'compost jardin',
    'AGR-05': 'arroser potager',
    'AGR-06': 'rotation cultures',
    'REP-01': 'crevaison vélo',
    'ORG-02': 'hameau tâches',
    'CUL-02': 'les misérables victor hugo',
}
ENDPOINT = 'http://127.0.0.1:11434'
MODEL = 'gemma4:e4b'


def write_guides(folder, present):
    folder.mkdir()
    contents = {**DISTRACTORS, **(TARGETS if present else {})}
    metadata = []
    manifest = {}
    for key, (title, passage) in contents.items():
        filename = f'{key.lower()}.fr.txt'
        body = f'{title}\n\nDocument fictif de recette.\n\n{passage}\n'.encode()
        (folder / filename).write_bytes(body)
        manifest[filename] = hashlib.sha256(body).hexdigest()
        metadata.append({'path': filename, 'title': title, 'language': 'fr', 'document_date': '2026-11-17'})
    (folder / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
    return manifest


async def check(args):
    original = httpx.AsyncClient
    async with original(trust_env=False, timeout=8) as ollama:
        tags = (await ollama.get(f'{ENDPOINT}/api/tags')).raise_for_status().json()['models']
        version = (await ollama.get(f'{ENDPOINT}/api/version')).raise_for_status().json()['version']
        weights = next(row for row in tags if row['name'] == MODEL)

        async def availability():
            if args.pause_marker.exists():
                raise RuntimeError('Inference pause marker present.')
            loaded = (await ollama.get(f'{ENDPOINT}/api/ps')).raise_for_status().json()['models']
            if any(row['name'] != MODEL for row in loaded):
                return 'Another model is in use.'
            raw = await asyncio.to_thread(subprocess.check_output, [
                'nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits',
            ], text=True, timeout=8)
            free = int(raw.splitlines()[0])
            occupied = sum(row.get('size_vram', 0) for row in loaded) // 1024**2
            if free < 1536 or free + occupied < 9728:
                return 'Insufficient GPU reserve.'
            return None

        async def guard(*, fresh=False):
            unavailable = await availability()
            if unavailable:
                raise RuntimeError(unavailable)
            return {'online': True, 'paused': False}

        async def wait_for_gpu():
            deadline = time.monotonic() + args.gpu_wait_seconds
            unavailable = await availability()
            if unavailable:
                print(json.dumps({'phase': 'waiting_for_gpu', 'reason': unavailable}), flush=True)
            while unavailable and time.monotonic() < deadline:
                await asyncio.sleep(min(15, max(0, deadline - time.monotonic())))
                unavailable = await availability()
            if unavailable:
                raise RuntimeError(unavailable)

        if args.report.exists():
            raise FileExistsError(args.report)
        await wait_for_gpu()
        bank = json.loads((BASE / 'tests/evaluation/banque-questions-effondrement.json').read_text())
        questions = {row['id']: row for row in bank['questions']}
        report = {
            'version': app.version, 'commit': args.commit, 'bank': bank['version'],
            'model': MODEL, 'model_digest': weights['digest'], 'ollama': version,
            'mode': 'moyenne', 'context': 16384, 'output_limit': 2048, 'gpu_layers': 99,
            'corpora': {}, 'cases': [],
        }

        def save():
            durable.write_bytes(args.report, json.dumps(report, ensure_ascii=False, indent=2).encode(), private=True)

        transport = httpx.ASGITransport(app=app)
        async with original(transport=transport, base_url='http://pilot-test') as api:
            for condition in args.conditions:
                with tempfile.TemporaryDirectory(prefix='ss-document-coverage-') as workspace, ExitStack() as patches:
                    root = Path(workspace)
                    guides = root / 'guides'
                    report['corpora'][condition] = write_guides(guides, condition != 'absent')
                    patches.enter_context(patch.object(store, 'ROOT', root / 'state'))
                    patches.enter_context(patch.object(library, 'GUIDES', guides))
                    patches.enter_context(patch.object(library, 'books', AsyncMock(return_value=[])))
                    patches.enter_context(patch.object(engine, 'OLLAMA', ENDPOINT))
                    patches.enter_context(patch.object(engine, 'POLICY', BASE / 'deploy/assistant-system.fr.txt'))
                    patches.enter_context(patch.object(operations, 'status', guard))
                    patches.enter_context(patch.object(httpx, 'AsyncClient', side_effect=lambda **kwargs:
                        original(transport=TestTransport(2048, 99, 6), **kwargs)))
                    store.init()
                    profiles.initialize()
                    library.index_guides()
                    if condition == 'attached':
                        ids = args.attach
                    elif condition == 'present':
                        ids = [*TARGETS, *CONTROLS]
                    else:
                        ids = list(TARGETS)
                    for key in ids:
                        await wait_for_gpu()
                        question = questions[key]['question']
                        expected = f'guide:{key.lower()}.fr.txt' if key in TARGETS else None
                        found = (await api.get('/api/search', params={
                            'q': question, 'limit': 5, 'kind': 'documents',
                        })).raise_for_status().json()
                        short_search = None
                        if expected:
                            short_search = (await api.get('/api/search', params={
                                'q': SEARCH_TERMS[key], 'limit': 5, 'kind': 'documents',
                            })).raise_for_status().json()
                        payload = {'message': question, 'mode': 'moyenne'}
                        if condition == 'attached':
                            payload['source_id'] = expected
                        print(json.dumps({'case': key, 'condition': condition, 'phase': 'asking'}), flush=True)
                        started = time.monotonic()
                        identifier = (await api.post('/api/questions', json=payload)).raise_for_status().json()['id']
                        async with asyncio.timeout(210):
                            while True:
                                job = (await api.get(f'/api/jobs/{identifier}')).raise_for_status().json()
                                if job['status'] not in ('queued', 'running'):
                                    break
                                await asyncio.sleep(1)
                        trace = store.ROOT / 'traces' / f'{identifier}.json'
                        tools = json.loads(trace.read_text())['tools'] if trace.exists() else []
                        row = {
                            'case': key, 'question': question, 'condition': condition, 'expected': expected,
                            'search_top5': found, 'short_search_top5': short_search,
                            'status': job['status'], 'answer': job.get('answer'),
                            'elapsed_seconds': round(time.monotonic() - started, 2),
                            'error': job.get('error'), 'sources': job['sources'], 'tools': tools,
                            'measurements': job.get('measurements'),
                            'documentary': job.get('documentary'),
                        }
                        report['cases'].append(row)
                        save()
                        print(json.dumps({
                            'case': key, 'condition': condition, 'status': job['status'],
                            'search_hits': [item['id'] for item in found['results']],
                            'consulted': [item['id'] for item in
                                          (job.get('documentary') or {}).get('consulted_sources', [])],
                        }), flush=True)
                    await library.kiwix_queries.close()
        return bool(report['cases']) and all(row['status'] == 'done' for row in report['cases'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--pause-marker', type=Path, required=True)
    parser.add_argument('--attach', choices=tuple(TARGETS), nargs='*', default=[])
    parser.add_argument('--conditions', choices=('present', 'absent', 'attached'), nargs='+',
                        default=('present', 'absent', 'attached'))
    parser.add_argument('--gpu-wait-seconds', type=int, default=0)
    raise SystemExit(0 if asyncio.run(check(parser.parse_args())) else 2)
