#!/usr/bin/env python3
"""Reproducible bounded local evaluations; no model is used to grade itself."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request

import linux_lab as lab

FIXTURES = lab.setup.ROOT / 'fixtures/evaluation'


def grade(case, result):
    text = result.get('response', '').strip()
    if result.get('error'):
        return {'passed': False, 'reason': 'execution_error'}
    if result.get('done_reason') == 'length' or not result.get('done'):
        return {'passed': False, 'reason': 'budget_or_incomplete'}
    if any(word in text for word in case.get('forbidden', [])):
        return {'passed': False, 'reason': 'forbidden_output'}
    normalized = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    try:
        answer = json.loads(normalized)
    except (ValueError, TypeError):
        return {'passed': False, 'reason': 'invalid_json'}
    expected = case['expected']
    passed = isinstance(answer, dict) and all(k in answer and answer[k] == v for k, v in expected.items())
    return {'passed': passed, 'reason': 'expected_fields' if passed else 'wrong_fields', 'parsed': answer}


def resources():
    with open('/proc/meminfo') as stream:
        memory = {k: int(v.split()[0]) for k, v in (line.split(':', 1) for line in stream)
                  if k in ('MemAvailable', 'SwapFree')}
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                           '--format=csv,noheader,nounits'], capture_output=True, text=True).stdout.strip()
    return {'time': time.time(), 'memory_kib': memory, 'gpu': gpu}


def generate(payload, output, deadline=600):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request('http://127.0.0.1:11435/api/generate',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    stop = threading.Event()
    samples = []

    def monitor():
        while not stop.is_set():
            samples.append(resources())
            stop.wait(2)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    start = time.monotonic()
    text, thinking, final, first = '', '', {}, None
    error = None
    try:
        with opener.open(request, timeout=min(deadline, 180)) as response:
            for line in response:
                event = json.loads(line)
                if event.get('error'):
                    raise RuntimeError(event['error'])
                if event.get('response') and first is None:
                    first = time.monotonic() - start
                text += event.get('response', '')
                thinking += event.get('thinking', '')
                if event.get('done'):
                    final = event
                if time.monotonic() - start > deadline:
                    raise TimeoutError('Budget de temps écoulé')
                if len(thinking) and len(thinking) % 500 < 30:
                    lab.setup.write_json(output.with_suffix('.partial.json'),
                        {'response': text, 'thinking': thinking, 'elapsed_seconds': time.monotonic() - start})
    except Exception as exc:
        # Never retain an authorization header or credentials; this is the local Ollama API.
        error = f'{type(exc).__name__}: {exc}'
    finally:
        stop.set(); thread.join(timeout=5)
    result = {**final, 'response': text, 'thinking': thinking}
    if error:
        result['error'] = error
    duration = result.get('eval_duration', 0) / 1e9
    return {'result': result, 'first_text_seconds': first, 'elapsed_seconds': time.monotonic() - start,
            'generation_tokens_per_second': result.get('eval_count', 0) / duration if duration else None,
            'resource_samples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', nargs='*')
    parser.add_argument('--cases', nargs='*', default=['reserve', 'harness'])
    parser.add_argument('--contexts', type=int, nargs='+', default=[8192])
    parser.add_argument('--run', default='screening-v1')
    parser.add_argument('--deadline', type=int, default=600)
    parser.add_argument('--repetitions', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--max-tokens', type=int, choices=[512, 1024, 2048, 4096, 8192], default=2048)
    parser.add_argument('--retry-errors', action='store_true')
    parser.add_argument('--modes', nargs='*', choices=['off', 'on', 'low', 'high'])
    parser.add_argument('--real-documents', action='store_true')
    parser.add_argument('--context-probe', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.run):
        parser.error('Nom de campagne invalide')
    if any(c not in (4096, 8192, 16384, 32768) for c in args.contexts):
        parser.error('Contexte non prévu par le protocole')
    if args.max_tokens >= min(args.contexts):
        parser.error('La sortie doit laisser de la place à la question et aux documents')
    lab.require_inference()
    app, config = lab.configuration()
    output = lab.MOUNT / 'results/evaluation' / args.run
    output.mkdir(parents=True, exist_ok=True)
    models = json.loads((FIXTURES / 'models.json').read_text())
    if args.models:
        models = [m for m in models if m['model'] in args.models]
    if args.modes:
        allowed = [{'off': False, 'on': True}.get(m, m) for m in args.modes]
        models = [{**m, 'modes': [mode for mode in m['modes'] if mode in allowed]} for m in models]
        models = [m for m in models if m['modes']]
    cases = [c for c in json.loads((FIXTURES / 'cases.json').read_text()) if c['id'] in args.cases]
    sources = lab.MOUNT / 'data/research/sources'
    if args.real_documents:
        cases.extend([
            {'id': 'real_english_ohm', 'category': 'real_document_multilingual',
             'prompt': "D'après le manuel anglais ci-dessous, dans son exemple du moteur de résistance 1 ohm branché à 12 V, quel courant circule et le fil donné pour 10 A convient-il ? Réponds uniquement en JSON avec courant_A, fil_utilisable (booléen) et source (identifiant du document).\n" + (sources / 'BOOK-EN-OHM.txt').read_text(),
             'expected': {'courant_A': 12, 'fil_utilisable': False, 'source': 'BOOK-EN-OHM'}},
            {'id': 'real_energy_unit', 'category': 'real_document',
             'prompt': "D'après le document, à combien de mégajoules correspond 1 kWh ? Réponds uniquement en JSON avec megajoules et source (identifiant du document).\n" + (sources / 'WIKI-FR-KWH.txt').read_text(),
             'expected': {'megajoules': 3.6, 'source': 'WIKI-FR-KWH'}}])
    if args.context_probe:
        text = (sources / 'WIKI-FR-FOOD.txt').read_text()
        filler = (text * (20000 // len(text) + 1))[:20000]
        needle = '\n[FICHE-CONTROLE] Le code de contrôle de cette fiche est ARDOISE-4729. [/FICHE-CONTROLE]\n'
        cases.append({'id': 'context_middle', 'category': 'context_stress',
            'prompt': 'Retrouve uniquement le code de contrôle indiqué dans la fiche au milieu des documents. Réponds en JSON avec code.\n' + filler[:10000] + needle + filler[10000:],
            'expected': {'code': 'ARDOISE-4729'}})
    system = (FIXTURES / 'system.fr.txt').read_text()
    tags = {m['name']: m for m in app.request('http://127.0.0.1:11435/api/tags')['models']}
    matrix = {'models': models, 'cases': cases, 'system': system, 'contexts': args.contexts,
              'repetitions': args.repetitions, 'output_tokens': args.max_tokens, 'temperature': 0, 'seed': 42}
    matrix['sha256'] = hashlib.sha256(json.dumps(matrix, sort_keys=True).encode()).hexdigest()
    manifest = output / 'protocol.json'
    if manifest.exists() and json.loads(manifest.read_text())['sha256'] != matrix['sha256']:
        raise RuntimeError('Campagne existante avec un autre protocole : choisir un autre nom')
    lab.setup.write_json(manifest, matrix)
    rows = []
    for candidate in models:
        model = candidate['model']
        if model not in tags:
            print('NOT_INSTALLED', model, flush=True)
            continue
        for context in args.contexts:
            for mode in candidate['modes']:
                for case in cases:
                    for repetition in range(args.repetitions):
                        key = re.sub(r'[^a-zA-Z0-9_-]', '_', f'{model}-{mode}-{context}-{case["id"]}-{repetition}')
                        path = output / (key + '.json')
                        if path.exists():
                            row = json.loads(path.read_text())
                            if args.retry_errors and row['result'].get('error'):
                                excluded = output / 'previous-errors'
                                excluded.mkdir(exist_ok=True)
                                path.rename(excluded / (str(time.time_ns()) + '-' + path.name))
                            else:
                                rows.append(row)
                                continue
                        state = resources()
                        if state['memory_kib']['MemAvailable'] < 2_500_000:
                            raise RuntimeError('Marge RAM trop faible ; campagne arrêtée sans perdre les résultats')
                        payload = {'model': model, 'system': system, 'prompt': case['prompt'], 'think': mode,
                                   'stream': True, 'keep_alive': '10m',
                                   'options': {'num_ctx': context, 'num_predict': args.max_tokens, 'temperature': 0, 'seed': 42}}
                        print('RUN', model, mode, context, case['id'], repetition, flush=True)
                        lab.require_inference()
                        engine_log = lab.MOUNT / 'logs/ollama.log'
                        log_offset = engine_log.stat().st_size if engine_log.exists() else 0
                        run = generate(payload, path, args.deadline)
                        row = {'model': model, 'digest': tags[model]['digest'], 'mode': mode, 'context': context,
                               'case': case['id'], 'repetition': repetition, 'request': payload, **run}
                        row['grade'] = grade(case, row['result'])
                        if engine_log.exists():
                            with engine_log.open('rb') as stream:
                                stream.seek(min(log_offset, engine_log.stat().st_size))
                                excerpt = stream.read().decode(errors='replace')
                            row['input_truncation_warnings'] = [line for line in excerpt.splitlines()
                                if 'truncating input prompt' in line]
                        row['placement'] = app.request('http://127.0.0.1:11435/api/ps')
                        lab.setup.write_json(path, row)
                        rows.append(row)
                        lab.setup.write_json(output / 'summary.json', rows)
                        print('RESULT', row['grade'], 'seconds', round(row['elapsed_seconds'], 2), flush=True)
    lab.setup.write_json(output / 'summary.json', rows)


if __name__ == '__main__':
    main()
