#!/usr/bin/env python3
"""Small repeatable smoke benchmark; raw answers remain local on the data SSD."""
import argparse
import json
import statistics
import subprocess
import threading
import time
import urllib.request

import linux_lab as lab


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model')
    parser.add_argument('--repetitions', type=int, choices=range(1, 11), default=3)
    parser.add_argument('--output', default='benchmark.json')
    args = parser.parse_args()
    if '/' in args.output or '\\' in args.output or not args.output.endswith('.json'):
        parser.error('--output doit être un nom de fichier .json')
    lab.require_inference()
    app, config = lab.configuration()
    model = args.model or config['chat_model']
    output = lab.MOUNT / 'results' / args.output
    app.record(config)
    cases = [
        ('addition', 'Réponds en français en une phrase : combien font deux plus deux ?'),
        ('reserve', 'Une réserve contient 600 litres. On utilise 18 litres par jour. '
         'Combien de jours complets et combien de litres restent ensuite ? Réponds brièvement en français.'),
        ('document', 'Réponds brièvement en français, uniquement à partir du document [1] ci-dessous. '
         'Cite [1]. Quel est le volume intérieur de la boîte ALPHA ? Peut-on en déduire sa charge maximale ?\n'
         '[1]\n' + (lab.MOUNT / 'data/library/guides/box.en.txt').read_text()),
    ]
    # Unload first, to distinguish the initial load from subsequent requests.
    app.request('http://127.0.0.1:11435/api/generate', {'model': model, 'keep_alive': 0}, timeout=120)
    rows, samples = [], []
    stop = threading.Event()

    def monitor():
        while not stop.is_set():
            value = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                                    '--format=csv,noheader,nounits'], capture_output=True, text=True)
            with open('/proc/meminfo') as stream:
                memory = {line.split(':')[0]: line.split(':')[1].strip() for line in stream
                          if line.startswith(('MemAvailable:', 'SwapFree:'))}
            samples.append({'time': time.time(), 'gpu': value.stdout.strip(), 'host_memory': memory})
            stop.wait(1)

    worker = threading.Thread(target=monitor, daemon=True)
    worker.start()
    try:
        for name, prompt in cases:
            for repetition in range(args.repetitions):
                payload = {'model': model, 'prompt': prompt, 'think': False, 'stream': True,
                           'keep_alive': '10m', 'options': {'num_ctx': 4096, 'num_predict': 256,
                                                          'temperature': 0, 'seed': 42}}
                started = time.monotonic()
                first, answer, final = None, '', {}
                req = urllib.request.Request('http://127.0.0.1:11435/api/generate',
                    data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(req, timeout=900) as response:
                    for line in response:
                        event = json.loads(line)
                        if event.get('error'):
                            raise RuntimeError(event['error'])
                        if event.get('response') and first is None:
                            first = time.monotonic() - started
                        answer += event.get('response', '')
                        if event.get('done'):
                            final = event
                if not final or not answer.strip():
                    raise RuntimeError('Génération incomplète ou vide.')
                elapsed = time.monotonic() - started
                duration = final.get('eval_duration', 0) / 1e9
                row = {'case': name, 'repetition': repetition, 'cold': not rows,
                       'first_token_seconds': first, 'wall_seconds': elapsed,
                       'tokens_per_second': final.get('eval_count', 0) / duration if duration else None,
                       'response': answer, 'final': final, 'request': payload,
                       'placement': app.request('http://127.0.0.1:11435/api/ps')}
                rows.append(row)
                lab.setup.write_json(output, {'runs': rows, 'gpu_samples': samples})
                print(json.dumps({k: row[k] for k in ('case', 'repetition', 'first_token_seconds',
                                                     'wall_seconds', 'tokens_per_second', 'response')}, ensure_ascii=False), flush=True)
    finally:
        stop.set()
        worker.join(timeout=5)
        lab.setup.write_json(output, {'runs': rows, 'gpu_samples': samples})
    warm = [r['tokens_per_second'] for r in rows if not r['cold']]
    if warm:
        print(f'Médiane génération à chaud : {statistics.median(warm):.2f} tokens/s')


if __name__ == '__main__':
    main()
