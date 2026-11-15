#!/usr/bin/env python3
"""Diagnostic HTTP séquentiel, sans IA, Windows/Linux (bibliothèque standard)."""
import argparse
import json
import math
import multiprocessing as mp
from pathlib import Path
import platform
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import runtime_resources

MAX_BYTES = 4 * 1024 * 1024
UNKNOWN = 'inconnu'


def scalars(value, fields):
    """Export only documented measurements, without arbitrary server payloads."""
    if not isinstance(value, dict):
        return {}
    result = {}
    for name in fields:
        item = value.get(name)
        if name not in value:
            continue
        if item is None or isinstance(item, bool) or isinstance(item, int):
            result[name] = item
        elif isinstance(item, float) and math.isfinite(item):
            result[name] = item
        elif isinstance(item, str):
            result[name] = item[:200]
    return result


def diagnostic_data(value):
    result = scalars(value, ('version', 'created'))
    for name, fields in (
        ('kiwix', ('state', 'elapsed_ms')),
        ('catalog', ('state', 'collections', 'age_seconds', 'http_status', 'elapsed_ms')),
        ('guides', ('indexed', 'status')),
        ('archive_index', ('phase', 'archives', 'completed', 'articles', 'workers', 'started')),
    ):
        if isinstance(value.get(name), dict):
            result[name] = scalars(value[name], fields)
    return result


def coverage_data(value):
    if not isinstance(value, dict):
        return UNKNOWN
    result = scalars(value, ('status', 'domain', 'collection', 'searched', 'failed',
        'not_searched', 'collections_selected', 'locally_indexed', 'native_incompatible',
        'without_fulltext', 'deadline_ms', 'deadline_exceeded', 'primary_requests',
        'request_limit', 'batch_limit', 'cache_hits', 'cache_ttl_seconds',
        'cache_disk_ttl_seconds', 'cache_generation', 'refinement_attempted',
        'refinement_failed', 'refinement_finished', 'refinement_not_searched',
        'title_searched', 'title_failed', 'title_not_searched', 'running'))
    for name, fields in (
        ('catalog', ('state', 'collections', 'age_seconds', 'http_status', 'elapsed_ms')),
        ('local_query', ('searched', 'failed', 'outdated')),
        ('local_index', ('phase', 'archives', 'completed', 'articles', 'workers')),
        ('concurrency', ('fulltext', 'titles', 'shared_across_requests')),
        ('processing', ('snapshots', 'selection_ms', 'selection_cpu_ms', 'metadata_evaluations', 'source_revision_checks', 'normalizations', 'normalization_hits', 'normalization_cache_bytes')),
        ('error_counts', ('timeout', 'invalid_response', 'http_error', 'connection_error')),
    ):
        if isinstance(value.get(name), dict):
            result[name] = scalars(value[name], fields)
    for name, maximum in (('trace', 40), ('errors', 12)):
        if not isinstance(value.get(name), list):
            continue
        rows = []
        for item in value[name][:maximum]:
            if not isinstance(item, dict):
                continue
            row = scalars(item, ('stage', 'pattern', 'language', 'elapsed_ms', 'outcome',
                'results', 'response_bytes', 'cached', 'http_status', 'reason'))
            if isinstance(item.get('collections'), list):
                row['collections'] = [book[:300] if isinstance(book, str) and not any(c in book for c in '/\\\x00') else UNKNOWN
                                      for book in item['collections'][:12]]
            rows.append(row)
        result[name] = rows
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def base_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or
            parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise argparse.ArgumentTypeError('URL HTTP(S) sans identifiants, requête ou fragment attendue.')
    return value.rstrip('/')


def local_resources():
    """Only the executing host/container, never inferred remote service resources."""
    return {'scope': 'machine ou conteneur exécutant le diagnostic',
            'platform': platform.system(), 'cpu_count': runtime_resources.cpu_count(),
            'available_memory_bytes': runtime_resources.available_memory() or UNKNOWN,
            'kiwix_cpu': UNKNOWN, 'kiwix_memory': UNKNOWN, 'disk_io': UNKNOWN,
            'gpu': UNKNOWN}


def _fetch(send, url, kind, timeout):
    """Disposable process: even DNS and trickling responses have an outer deadline."""
    started = time.monotonic()
    def emit(**value):
        send.send({**value, 'elapsed_ms': round((time.monotonic() - started) * 1000)})
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(url, headers={'Accept': 'text/event-stream' if kind == 'stream' else '*/*'})
        with opener.open(request, timeout=timeout) as response:
            emit(http_status=response.status, headers_ms=round((time.monotonic()-started)*1000))
            if kind == 'stream' and 'text/event-stream' not in response.headers.get('Content-Type', ''):
                raise ValueError('expected_sse')
            raw = bytearray()
            frame = bytearray()
            data_lines = []
            terminal = False
            def line_received(line):
                nonlocal terminal
                line = line.rstrip(b'\r')
                if line.startswith(b'data:'):
                    data_lines.append(line[5:].lstrip(b' '))
                elif not line and data_lines:
                    value = json.loads(b'\n'.join(data_lines))
                    data_lines.clear()
                    if not isinstance(value, dict) or value.get('state') not in ('working', 'results', 'done', 'error'):
                        raise ValueError('invalid_sse')
                    if value['state'] in ('results', 'done') and not isinstance(value.get('results'), list):
                        raise ValueError('invalid_results')
                    emit(event=value)
                    terminal = value['state'] in ('done', 'error')
            while True:
                chunk = response.read1(8192)
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > MAX_BYTES:
                    raise ValueError('response_too_large')
                if kind == 'stream':
                    frame.extend(chunk)
                    while b'\n' in frame:
                        line, _, rest = frame.partition(b'\n')
                        frame = bytearray(rest)
                        line_received(line)
                        if terminal:
                            break
                    if terminal:
                        break
            if kind == 'stream':
                if not terminal:
                    raise ValueError('incomplete_stream')
            elif kind == 'json':
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise ValueError('invalid_json_object')
                emit(data=diagnostic_data(value))
            elif kind == 'xml':
                tree = ET.fromstring(raw)
                if tree.tag != 'rss' or tree.find('channel') is None:
                    raise ValueError('invalid_search_xml')
                emit(result_count=len(tree.findall('./channel/item')))
            emit(finished=True, response_bytes=len(raw))
    except urllib.error.HTTPError as error:
        emit(error='http_error', http_status=error.code)
    except Exception as error:
        # No raw URLs, response bodies, provider messages or authentication details.
        reason = getattr(error, 'reason', error)
        category = ('read_or_connect_timeout' if isinstance(reason, (TimeoutError, socket.timeout)) else
                    'invalid_response' if isinstance(error, (ValueError, ET.ParseError)) else
                    'connection_or_read_error')
        emit(error=category, error_type=type(error).__name__)
    finally:
        send.close()


def measure(url, kind, timeout, total_deadline):
    record = {'status': 'running', 'first_results_ms': None, 'updates_received': 0,
              'coverage': UNKNOWN, 'result_count': 0}
    ctx = mp.get_context('spawn')
    receive, send = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_fetch, args=(send, url, kind, timeout), daemon=True)
    started = time.monotonic()
    deadline = min(total_deadline, started + timeout)
    process.start()
    send.close()
    def apply(message):
        event = message.pop('event', None)
        if event:
            if event['state'] == 'results':
                record['updates_received'] += 1
            if 'results' in event:
                record['result_count'] = len(event['results'])
                if event['results'] and record['first_results_ms'] is None:
                    record['first_results_ms'] = round((time.monotonic()-started)*1000)
                record['coverage'] = coverage_data(event.get('coverage'))
            if event['state'] == 'done':
                record['status'] = 'complete'
            elif event['state'] == 'error':
                record.update(status='error', error='server_stream_error')
        if message.get('result_count', 0) and record['first_results_ms'] is None:
            record['first_results_ms'] = round((time.monotonic()-started)*1000)
        record.update(message)
        if message.get('error'):
            record['status'] = 'error'
        if message.get('finished') and record['status'] == 'running':
            record['status'] = 'complete'
    try:
        while time.monotonic() < deadline:
            if receive.poll(min(.05, max(0, deadline-time.monotonic()))):
                try:
                    apply(receive.recv())
                except EOFError:
                    break
            elif not process.is_alive():
                break
        if record['status'] == 'running':
            record.update(status='timeout', error='client_deadline')
    except KeyboardInterrupt:
        record.update(status='cancelled', error='user_cancelled')
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
        receive.close()
    record['elapsed_ms'] = round((time.monotonic()-started)*1000)
    record.pop('finished', None)
    return record


def run(args, probe=measure):
    started = time.monotonic()
    deadline = started + args.max_seconds
    report = {'schema': 1, 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'status': 'running', 'query': args.query, 'book': args.book,
              'collection': args.collection, 'language': args.language,
              'endpoints': {'portal': args.portal, 'kiwix': args.kiwix},
              'limits': {'request_seconds': args.timeout, 'total_seconds': args.max_seconds,
                         'response_bytes': MAX_BYTES, 'repeats': args.repeats, 'parallel_requests': 1},
              'resources': local_resources() if args.local_resources else UNKNOWN,
              'server_resources': UNKNOWN, 'steps': [],
              'notice': 'GET seulement ; caches non effacés. Les services peuvent remplir leurs caches. Sans IA.'}
    def step(name, url, kind, **metadata):
        if time.monotonic() >= deadline or report['status'] == 'cancelled':
            return False
        print(name, flush=True)
        result = probe(url, kind, args.timeout, deadline)
        report['steps'].append({'name': name, **metadata, **result})
        if result['status'] == 'cancelled':
            report['status'] = 'cancelled'
        return report['status'] != 'cancelled'
    try:
        # Same preparatory diagnostic as the existing portal check; no index start.
        step('portal_diagnostic', args.portal + '/api/library/search-diagnostic', 'json')
        for repeat in range(args.repeats):
            if report['status'] == 'cancelled' or time.monotonic() >= deadline:
                break
            label = 'initial_cache_unknown' if repeat == 0 else 'warm_repetition'
            if not step('kiwix_access', args.kiwix + '/', 'access', repeat=repeat, cache_state=label):
                break
            native = urllib.parse.urlencode({'books.name': args.book, 'pattern': args.query,
                                             'format': 'xml', 'pageLength': 5})
            if not step('kiwix_search', args.kiwix + '/search?' + native, 'xml', repeat=repeat, cache_state=label):
                break
            params = urllib.parse.urlencode({'q': args.query, 'collection': args.collection,
                                             'language': args.language, 'limit': 5,
                                             'diagnostic': 'true', 'stream': 'true'})
            if not step('portal_search', args.portal + '/api/search?' + params, 'stream', repeat=repeat, cache_state=label):
                break
    except KeyboardInterrupt:
        report['status'] = 'cancelled'
    if report['status'] != 'cancelled':
        report['status'] = 'budget_exhausted' if time.monotonic() >= deadline else 'measured'
    report['elapsed_ms'] = round((time.monotonic()-started)*1000)
    return report


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--portal', type=base_url, default='http://127.0.0.1:8080')
    p.add_argument('--kiwix', type=base_url, default='http://127.0.0.1:8081')
    p.add_argument('--query', required=True)
    p.add_argument('--book', required=True, help='Identifiant exact Kiwix, une seule archive.')
    p.add_argument('--collection', required=True, help='Même identifiant complet que --book ; pas de famille de collections.')
    p.add_argument('--language', default='')
    p.add_argument('--repeats', type=int, choices=range(1, 4), default=2)
    p.add_argument('--timeout', type=float, default=90)
    p.add_argument('--max-seconds', type=float, default=300)
    p.add_argument('--local-resources', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    return p


def main():
    p = parser()
    args = p.parse_args()
    if (not 0 < args.timeout <= 120 or not 0 < args.max_seconds <= 900 or
            not args.query.strip() or len(args.query) > 200 or
            args.collection != args.book or not re.search(r'[a-zA-Z0-9]', args.book) or
            any(c in args.book for c in ',;\r\n') or len(args.collection) > 160):
        p.error('--collection doit être identique à --book ; une archive ; délai 0–120 s, total 0–900 s.')
    # Reserve output before making requests; never overwrite an existing report.
    with args.output.open('x', encoding='utf-8') as output:
        report = run(args)
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    failures = any(s['status'] != 'complete' for s in report['steps'])
    return 130 if report['status'] == 'cancelled' else 1 if failures or report['status'] != 'measured' else 0


if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
