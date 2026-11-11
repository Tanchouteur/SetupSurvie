#!/usr/bin/env python3
"""Isolated tool-use experiment with a deterministic, non-mutating calculation."""
import argparse
from fractions import Fraction
import json
import math
import re
import time

import linux_lab as lab

TOOL = {'type': 'function', 'function': {
    'name': 'divide_with_remainder',
    'description': 'Divise une quantité totale en unités complètes. Retourne le nombre entier d’unités et le reste exact. Utiliser pour les répartitions et les jours complets.',
    'parameters': {'type': 'object', 'properties': {'total': {'type': 'number'}, 'per_unit': {'type': 'number'}},
                   'required': ['total', 'per_unit'], 'additionalProperties': False}}}


def divide_with_remainder(total, per_unit):
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (total, per_unit)):
        raise ValueError('Deux nombres JSON sont requis')
    if any(abs(value) > 10**12 or not math.isfinite(value) for value in (total, per_unit)):
        raise ValueError('Quantités hors limites')
    total, per_unit = Fraction(str(total)), Fraction(str(per_unit))
    if total < 0 or per_unit <= 0 or max(abs(total), abs(per_unit)) > 10**12:
        raise ValueError('Quantités hors limites')
    count = total // per_unit
    remainder = total - count * per_unit
    return {'complete_units': count, 'remainder': float(remainder), 'exact_remainder': str(remainder)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', nargs='+', required=True)
    args = parser.parse_args()
    lab.require_inference()
    app, config = lab.configuration()
    folder = lab.MOUNT / 'results/evaluation/tools-v1'
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in args.models:
        lab.require_inference()
        path = folder / (re.sub(r'[^a-zA-Z0-9_-]', '_', model) + '.json')
        if path.exists():
            rows.append(json.loads(path.read_text())); continue
        mode = 'low' if model.startswith('gpt-oss') else False
        system = (lab.setup.ROOT / 'fixtures/evaluation/system.fr.txt').read_text()
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content':
            'Une réserve contient 600 litres. On utilise 18 litres par jour. Utilise obligatoirement l’outil fourni pour vérifier le calcul, puis réponds uniquement en JSON avec jours (entiers) et reste_litres.'}]
        trace, calls = [], []
        start = time.monotonic()
        final = ''
        error = None
        try:
            for step in range(4):
                request = {'model': model, 'messages': messages, 'tools': [TOOL], 'think': mode,
                           'stream': False, 'keep_alive': '10m',
                           'options': {'num_ctx': 8192, 'num_predict': 2048, 'temperature': 0, 'seed': 42}}
                result = app.request('http://127.0.0.1:11435/api/chat', request, timeout=600)
                trace.append(result)
                if result.get('error'):
                    raise RuntimeError(result['error'])
                message = result.get('message', {})
                messages.append(message)
                tool_calls = message.get('tool_calls') or []
                if not tool_calls:
                    final = message.get('content', ''); break
                for call in tool_calls:
                    function = call['function']
                    if function['name'] != TOOL['function']['name']:
                        raise RuntimeError('Le modèle demande un outil non déclaré')
                    arguments = function.get('arguments', {})
                    if isinstance(arguments, str):arguments = json.loads(arguments)
                    value = divide_with_remainder(**arguments)
                    calls.append({'name': function['name'], 'arguments': arguments, 'result': value})
                    reply = {'role': 'tool', 'tool_name': function['name'], 'content': json.dumps(value)}
                    if call.get('id'):reply['tool_call_id'] = call['id']
                    messages.append(reply)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        try:answer = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', final.strip()))
        except ValueError:answer = None
        passed = bool(calls) and answer == {'jours': 33, 'reste_litres': 6} and not error
        row = {'model': model, 'mode': mode, 'tool_schema': TOOL, 'calls': calls, 'trace': trace,
               'response': final, 'error': error, 'passed': passed, 'elapsed_seconds': time.monotonic() - start}
        lab.setup.write_json(path, row); rows.append(row)
        print('TOOL_RESULT', model, passed, round(row['elapsed_seconds'], 2), final, error, flush=True)
    lab.setup.write_json(folder / 'summary.json', rows)


if __name__ == '__main__':main()
