"""Optional French Wikipedia pilot with an FTS index for each search category."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

from . import archive_index, durable

DIRECTORY = 'category-index'
DOMAINS = ('resilience', 'culture')
FORMAT = 1
PILOT_ARCHIVE = re.compile(r'wikipedia_fr_all(?:_(?:maxi|mini|nopic))?_\d{4}-\d{2}(?:-\d{2})?[a-z]?\.zim')


def source(zims):
    candidates = [p for p in Path(zims).glob('wikipedia_fr_all*.zim')
                  if PILOT_ARCHIVE.fullmatch(p.name) and not p.is_symlink()]
    return max(candidates, key=lambda p: ('_maxi_' in p.name, p.name), default=None)


def signature(path, state):
    info = path.stat()
    revision = hashlib.sha256(f'stat-v1:{path.name}:{info.st_size}:{info.st_mtime_ns}'.encode()).hexdigest()
    saved = {}
    database = Path(state)/'pilot.db'
    if database.is_file():
        with archive_index.connect(database, True) as db:
            prefix = f'catalogue:v1:zim:{path.stem}/'
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='settings'").fetchone():
                for key, value in db.execute('SELECT key,value FROM settings WHERE substr(key,1,?)=? ORDER BY key',(len(prefix),prefix)):
                    try:
                        record = json.loads(value)
                        domains = record.get('domains')
                        if record.get('revision') == revision and isinstance(domains,list) and all(d in DOMAINS for d in domains):
                            saved[key[len(prefix):]] = sorted(set(domains))
                    except (AttributeError,TypeError,ValueError):
                        continue
    payload = [FORMAT, path.name, info.st_size, info.st_mtime_ns, saved]
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(), saved


def read_status(state):
    root = Path(state)/DIRECTORY
    return archive_index.status(root)


def availability(zims, state):
    report = read_status(state)
    path = source(zims)
    if path is None:
        return {'phase':'unavailable'}, None
    if report['phase'] != 'completed':
        return {**report,'archive':path.name}, None
    try:
        fingerprint, _ = signature(path,state)
        index = Path(state)/DIRECTORY/(archive_index.index_name(path.name)+'.sqlite')
        if report.get('fingerprint') == fingerprint and index.is_file():
            return report, index
    except (OSError,sqlite3.Error):
        pass
    return {**report,'archive':path.name,'phase':'outdated'}, None


def prepare(zims, state, *, cancel=None, job_id=None, reserve=15_000_000_000):
    root = Path(state)/DIRECTORY
    path = source(zims)
    if path is None:
        raise FileNotFoundError('Aucune archive Wikipédia francophone compatible.')
    durable.mkdir(root)
    fingerprint, corrections = signature(path,state)
    previous, published = availability(zims,state)
    if published is not None:
        return previous
    elapsed_before=previous.get('elapsed_seconds',0) if previous.get('fingerprint')==fingerprint else 0
    started = time.monotonic()
    report = {'phase':'running','archive':path.name,'fingerprint':fingerprint,'job_id':job_id,'done':0,'total':None}
    def report_progress(done,total,counts):
        report.update(done=done,total=total,counts=counts,elapsed_seconds=round(elapsed_before+time.monotonic()-started,2))
        save()
    def save():
        durable.write_bytes(root/'progress.json',json.dumps(report).encode(),private=True)
    save()
    try:
        result = archive_index.build_archive(path,root,cancel=cancel,force=True,reserve=reserve,
            categories=DOMAINS,corrections=corrections,category_signature=fingerprint,progress=report_progress)
        if signature(path,state)[0] != fingerprint:
            report['phase'] = 'outdated'
        else:
            report.update(phase='completed',bytes=(root/(archive_index.index_name(path.name)+'.sqlite')).stat().st_size,
                          articles=result['articles'])
    except archive_index.Paused:
        report['phase'] = 'paused'
    except Exception:
        report['phase'] = 'error'
        raise
    finally:
        report['elapsed_seconds']=round(elapsed_before+time.monotonic()-started,2)
        save()
    return report
