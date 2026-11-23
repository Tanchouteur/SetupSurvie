"""Resumable search indexes by space for the main collection."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

from . import archive_index, collection_sort, durable, retrieval

DIRECTORY = 'category-index'
DOMAINS = ('resilience', 'culture')
FORMAT = 1
PILOT_ARCHIVE = re.compile(r'wikipedia_fr_all(?:_(?:maxi|mini|nopic))?_\d{4}-\d{2}(?:-\d{2})?[a-z]?\.zim')


def sources(zims, sorting=None):
    sorting = sorting or collection_sort.Sort()
    paths = [path for path in Path(zims).glob('*.zim')
             if path.is_file() and not path.is_symlink()
             and sorting.state(collection_sort.archive(path.name)) == 'main']
    return sorted(paths, key=lambda path: (not bool(PILOT_ARCHIVE.fullmatch(path.name)),
                                           '_maxi_' not in path.name, path.name))


def signature(path, state):
    info = path.stat()
    revision = hashlib.sha256(f'stat-v1:{path.name}:{info.st_size}:{info.st_mtime_ns}'.encode()).hexdigest()
    saved = {}
    database = Path(state)/'pilot.db'
    if database.is_file():
        with archive_index.connect(database, True) as db:
            prefix = f'catalogue:v1:zim:{path.stem}/'
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='settings'").fetchone():
                for key, value in db.execute('SELECT key,value FROM settings WHERE key>=? AND key<? ORDER BY key',(prefix,prefix[:-1]+'0')):
                    try:
                        record = json.loads(value)
                        domains = record.get('domains')
                        if record.get('revision') == revision and isinstance(domains,list) and all(d in DOMAINS for d in domains):
                            saved[key[len(prefix):]] = sorted(set(domains))
                    except (AttributeError,TypeError,ValueError):
                        continue
    role = retrieval.source_role({'book': path.stem})
    format_version = FORMAT + 1 if role in retrieval.CULTURE_SOURCE_ROLES else FORMAT
    payload = [format_version, path.name, info.st_size, info.st_mtime_ns, saved]
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(), saved


def read_status(state):
    root = Path(state)/DIRECTORY
    return archive_index.status(root)


def _record(root, path):
    return root / (archive_index.index_name(path.name) + '.json')


def ready_indexes(zims, state, sorting=None):
    root = Path(state) / DIRECTORY
    legacy = read_status(state)
    ready = {}
    for path in sources(zims, sorting):
        index = root / (archive_index.index_name(path.name) + '.sqlite')
        if not index.is_file():
            continue
        try:
            record = _record(root, path)
            saved = json.loads(record.read_text(encoding='utf-8')) if record.is_file() else legacy
            if saved.get('archive') != path.name or saved.get('phase') != 'completed':
                continue
            fingerprint, _ = signature(path, state)
            if saved.get('fingerprint') == fingerprint:
                ready[path.stem] = index
        except (OSError, ValueError, AttributeError, sqlite3.Error):
            continue
    return ready


def availability(zims, state, sorting=None, *, indexes=None):
    paths = sources(zims, sorting)
    if not paths:
        return {'phase': 'unavailable', 'archives': 0, 'completed': 0}, None
    report = read_status(state)
    ready = ready_indexes(zims, state, sorting) if indexes is None else indexes
    report = {**report, 'archives': len(paths), 'completed': len(ready)}
    if len(ready) == len(paths) and report['phase'] != 'running':
        report['phase'] = 'completed'
    elif report['phase'] in ('completed', 'unavailable'):
        report['phase'] = 'outdated'
    return report, next(iter(ready.values()), None)


def compress_ready(root, paths, ready, report, failures, save, *, cancel=None, reserve=15_000_000_000, keep=None):
    """Convert indexes built before 0.88.0 to the compressed format (same results)."""
    for path in paths:
        if path.stem not in ready or (keep and not keep(path)):
            continue
        if cancel and Path(cancel).exists():
            raise archive_index.Paused()
        report.update(archive=path.name, step='compression', done=None, total=None)
        save()
        try:
            size = archive_index.compress(ready[path.stem], cancel=cancel, reserve=reserve)
        except archive_index.Paused:
            raise
        except (OSError, sqlite3.Error) as error:
            # The old index stays published and searchable.
            failures.append({'archive': path.name, 'step': 'compression', 'error': type(error).__name__})
            report['failures'] = failures
            save()
            if isinstance(error, archive_index.StorageReserve):
                break
            continue
        if size is None:
            continue
        record = _record(root, path)
        try:
            saved = json.loads(record.read_text(encoding='utf-8'))
            saved['bytes'] = size
            durable.write_bytes(record, json.dumps(saved).encode(), private=True)
        except (OSError, ValueError, TypeError):
            pass
        report['bytes'] = sum(index.stat().st_size for index in ready.values())
        save()
    report.pop('step', None)


def prepare(zims, state, *, cancel=None, job_id=None, reserve=15_000_000_000, workers=1, catalog=None):
    root = Path(state) / DIRECTORY
    durable.mkdir(root)
    sorting = collection_sort.load(catalog) if catalog is not None else None
    paths = sources(zims, sorting)
    ready = ready_indexes(zims, state, sorting)
    report = {'phase': 'running', 'job_id': job_id, 'archives': len(paths), 'completed': len(ready)}
    started = time.monotonic()
    previous = read_status(state)

    def save():
        report['elapsed_seconds'] = round(elapsed_before + time.monotonic() - started, 2)
        durable.write_bytes(root / 'progress.json', json.dumps(report).encode(), private=True)

    elapsed_before = previous.get('elapsed_seconds', 0) if previous.get('phase') in ('running', 'paused') else 0
    # Preserve a valid index published by the single-archive release.
    if previous.get('phase') == 'completed':
        for path in paths:
            if path.stem in ready and previous.get('archive') == path.name and not _record(root, path).exists():
                durable.write_bytes(_record(root, path), json.dumps(previous).encode(), private=True)

    class MovedFromMain(Exception):
        pass

    def in_main(path):
        return catalog is None or collection_sort.load(catalog).state(collection_sort.archive(path.name)) == 'main'

    def progress(done, total, counts):
        if not in_main(path):
            raise MovedFromMain()
        report.update(done=done, total=total, counts=counts)
        save()

    try:
        failures = []
        for path in paths:
            if cancel and Path(cancel).exists():
                raise archive_index.Paused()
            if path.stem in ready:
                continue
            if not in_main(path):
                continue
            fingerprint, corrections = signature(path, state)
            report.update(archive=path.name, fingerprint=fingerprint, done=0, total=None, counts={})
            save()
            try:
                result = archive_index.build_archive(path, root, cancel=cancel, force=True, reserve=reserve,
                    categories=DOMAINS, corrections=corrections, category_signature=fingerprint,
                    progress=progress, workers=workers)
            except MovedFromMain:
                continue
            except (archive_index.StorageReserve, archive_index.Paused):
                raise
            except Exception as error:
                # One unreadable archive is reported; the remaining archives still progress.
                failures.append({'archive': path.name, 'error': type(error).__name__})
                report['failures'] = failures
                save()
                continue
            if signature(path, state)[0] != fingerprint:
                continue
            index = root / (archive_index.index_name(path.name) + '.sqlite')
            record = {**report, 'phase': 'completed', 'bytes': index.stat().st_size,
                      'articles': result['articles']}
            durable.write_bytes(_record(root, path), json.dumps(record).encode(), private=True)
            ready[path.stem] = index
            report.update(completed=len(ready), bytes=sum(index.stat().st_size for index in ready.values()))
            save()
        compress_ready(root, paths, ready, report, failures, save, cancel=cancel, reserve=reserve, keep=in_main)
        current = sources(zims, collection_sort.load(catalog) if catalog is not None else sorting)
        complete = all(path.stem in ready for path in current)
        report['phase'] = 'completed' if complete else 'error' if failures else 'outdated'
    except archive_index.Paused:
        report['phase'] = 'paused'
    except Exception:
        report['phase'] = 'error'
        raise
    finally:
        save()
    return report
