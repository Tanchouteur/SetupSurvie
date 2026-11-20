"""Read-only bounded view of web jobs and existing Windows library transfers.

Never open a database, hash an archive, acquire a job lease or change a worker.
Receipts describe prior verification, not current search/read availability.
"""
import json
import os
from pathlib import Path
import re
import time

import discovery
from delivery_paths import destination
from pilot import zim_video_inventory

MAX_JSON = 32 * 1024 * 1024
MAX_ITEMS = 20000


def read_json(path, default=None):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Linked state')
    try:
        with path.open('rb') as stream:
            data = stream.read(MAX_JSON + 1)
        if len(data) > MAX_JSON:
            raise ValueError('State too large')
        return json.loads(data.decode('utf-8-sig'))
    except FileNotFoundError:
        return default


def shared_size(path):
    """Read EOF via a shared Windows handle (directory sizes can lag writers)."""
    if os.name != 'nt':
        return path.stat().st_size
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x80000000, 7, None, 3, 0, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        length = ctypes.c_longlong()
        if not kernel.GetFileSizeEx(handle, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        return length.value
    finally:
        kernel.CloseHandle(handle)


def owner_status(owner):
    pid, saved = owner.get('pid'), owner.get('identity')
    if type(pid) is not int or pid <= 0 or not isinstance(saved, dict) or not saved:
        return None
    actual = discovery.identity(pid)
    # An inaccessible identity must not be mistaken for a stopped worker.
    if actual is None:
        from delivery_paths import process_alive
        return None if process_alive(pid) else False
    return actual == saved


def allowed_plan(path, root, work):
    original = Path(path).absolute()
    # Windows TEMP can use an 8.3 alias while root.resolve() uses its long name.
    # Reject linked components before canonicalising, then compare canonical roots.
    if any(part.is_symlink() for part in [original, *original.parents]):
        raise ValueError('Linked plan')
    path = original.resolve()
    if path.is_relative_to((root / 'catalog').resolve()):
        relative = path.relative_to(root.resolve()).as_posix()
        return destination(root, relative)
    try:
        parts = path.relative_to((work / 'library-web').resolve()).parts
    except ValueError:
        raise ValueError('External plan') from None
    if len(parts) != 2 or not re.fullmatch('[a-f0-9]{32}', parts[0]) or parts[1] != 'plan.json':
        raise ValueError('Invalid plan')
    return destination(work, 'library-web/' + '/'.join(parts))


def snapshot(root, work, *, now=None):
    now = time.time() if now is None else now
    root, work = Path(root).resolve(), Path(work).resolve()
    base = {'observed_at': now, 'phase': 'idle', 'source': None, 'active': [],
            'commands': False, 'stale': False}
    try:
        transfer = read_json(destination(root, 'diagnostics/bibliotheque-transfer.json'), {})
        direct = read_json(destination(root, 'diagnostics/content-transfer.json'), {})
        transfer_source = 'windows'
        if isinstance(direct, dict) and direct and (not transfer or owner_status(transfer) is not True):
            transfer = direct
            transfer_source = 'local'
        web = read_json(destination(work, 'library-web/state.json'), {})
        if not isinstance(transfer, dict) or not isinstance(web, dict):
            raise ValueError('Invalid state')
        # A verified independent worker takes precedence over a stale web record.
        transfer_alive = owner_status(transfer) if transfer else None
        web_alive = owner_status(web) if web else None
        # After a disk migration, a finished transfer can still name the old
        # disk. It is history, not an unknown current activity.
        transfer_plan=None
        if transfer:
            try:transfer_plan=allowed_plan(transfer['plan'],root,work)
            except (ValueError,KeyError,TypeError,OSError):
                if transfer_alive is True:raise
                transfer,transfer_alive={},None
        if web.get('action')=='index' and web_alive is not True and web.get('index_pid'):
            if owner_status({'pid':web['index_pid'],'identity':web.get('index_identity')}) is True:web_alive=True
        if transfer and (transfer_alive is True or not web.get('id') or web_alive is not True):
            owner, alive, source = transfer, transfer_alive, transfer_source
            plan_path = transfer_plan
            started = transfer.get('started', 0)
        elif web.get('id') and re.fullmatch('[a-f0-9]{32}', web['id']):
            owner, alive, source = web, web_alive, 'web'
            started = web.get('started_at', 0)
            if web.get('action') in ('geography', 'routing', 'plan','index','index-prepare','video-inventory','youtube-download','category-index','collection-exclude'):
                phase = web.get('phase', 'unknown')
                if phase in ('starting', 'planning', 'downloading', 'refreshing') and alive is False:
                    phase = 'interrupted'
                extra={}
                message=web.get('message') if isinstance(web.get('message'),str) else ''
                if web['action'] == 'video-inventory' and phase in ('completed', 'error'):
                    report = read_json(destination(root, 'state/pilot/zim-videos/progress.json'), {})
                    if (isinstance(report, dict) and report.get('job_id') == web['id']
                            and zim_video_inventory.partial_with_all_archives(report)
                            and (phase == 'completed' or message.startswith('L’opération a échoué.'))):
                        phase = 'partial'
                        message = zim_video_inventory.LIMITED_INVENTORY_MESSAGE
                        extra = {'archives': report['archives'], 'completed': report['archives']}
                if web['action']=='index':
                    progress=read_json(root/'state/pilot/archive-index/progress.json',{})
                    if isinstance(progress,dict):extra={key:progress.get(key,0) for key in ('archives','completed','articles') if type(progress.get(key,0)) is int}
                    if phase=='downloading':phase='indexing'
                elif web['action']=='index-prepare' and phase=='downloading':phase='index_preparation'
                elif web['action']=='category-index':
                    progress=read_json(root/'state/pilot/category-index/progress.json',{})
                    if isinstance(progress,dict) and (not progress.get('job_id') or progress.get('job_id')==web['id']):
                        counts=progress.get('counts') if isinstance(progress.get('counts'),dict) else {}
                        extra={'entries_done':progress.get('done'),'entries_total':progress.get('total'),
                               'resilience':counts.get('resilience'),'culture':counts.get('culture'),
                               'archives':progress.get('archives'),'completed':progress.get('completed')}
                        extra={key:value for key,value in extra.items() if type(value) is int and value>=0}
                    if phase=='downloading':phase='category_indexing'
                elif web['action']=='collection-exclude' and phase=='refreshing':phase='removing'
                elif web['action']=='youtube-download':
                    progress=read_json(destination(work,'library-web/'+web['id']+'/progress.json'),{})
                    counts=progress.get('counts') if isinstance(progress,dict) else None
                    if isinstance(counts,dict):extra={'videos':progress.get('videos',0),'downloaded':counts.get('downloaded',0),'skipped':counts.get('skipped',0),'errors':counts.get('error',0)}
                return {**base, 'source': source, 'phase': phase,
                        'kind': web['action'], 'operation_id': web['id'],
                        'pause_requested': (work/'library-web'/web['id']/'cancel').is_file(),
                        'automatic_pause': phase == 'paused' and (work/'library-web'/web['id']/'auto-pause').is_file(),
                        'worker_alive': alive,'index_progress':extra,'message':message[:400]}
            plan_path = allowed_plan(work / 'library-web' / web['id'] / 'plan.json', root, work)
        else:
            return base
        plan = read_json(plan_path, {})
        items = plan.get('items', [])
        if not isinstance(items, list) or len(items) > MAX_ITEMS:
            raise ValueError('Plan too large')
        selected = {}
        for item in items:
            if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                    or item['id'] in selected or type(item.get('bytes')) is not int or item['bytes'] <= 0
                    or not isinstance(item.get('path'), str)
                    or not item['path'].startswith(('library/zim/', 'library/guides/'))
                    or not re.fullmatch('[a-f0-9]{64}', item.get('sha256', ''))):
                raise ValueError('Invalid item')
            destination(root, item['path'])
            selected[item['id']] = item
        receipt = read_json(destination(root, 'catalog/downloaded-content.json'), {'items': []})
        records = receipt.get('items', [])
        if not isinstance(records, list) or len(records) > MAX_ITEMS:
            raise ValueError('Receipts too large')
        verified = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            item = selected.get(record.get('id'))
            if item and all(record.get(k) == item.get(k) for k in ('id', 'path', 'bytes', 'sha256')):
                verified.add(item['id'])
        progress_path = destination(root, 'catalog/content-progress.json')
        progress = read_json(progress_path, {})
        updated = progress_path.stat().st_mtime if progress_path.exists() else None
        fresh = updated is not None and updated >= float(started or 0)
        active = []
        if fresh and alive is True:
            entries = progress.get('active') or ([progress] if progress.get('id') else [])
            if not isinstance(entries, list):
                raise ValueError('Invalid progress')
            seen = set()
            for entry in entries[:3]:
                item = selected.get(entry.get('id')) if isinstance(entry, dict) else None
                if not item or item['id'] in verified or item['id'] in seen:
                    continue
                seen.add(item['id'])
                amount = entry.get('bytes', 0)
                if type(amount) is not int:
                    amount = 0
                try:
                    amount = shared_size(destination(root, item['path'] + '.part'))
                except OSError:
                    pass  # Keep the known observation, never invent a zero measurement.
                amount = max(0, min(amount, item['bytes']))
                active.append({'id': item['id'], 'title': str(item.get('title', item['id']))[:300],
                               'bytes': amount, 'total': item['bytes'],
                               'phase': 'verifying' if amount == item['bytes'] else 'downloading'})
        retry = read_json(destination(root, 'catalog/content-retry.json'), {})
        matching_retry = retry.get('pid') == owner.get('pid')
        paused = destination(root, 'catalog/content-supervisor.pause').exists()
        if source == 'web':
            paused = paused or destination(work, 'library-web/' + web['id'] + '/cancel').exists()
        if items and len(verified) == len(items):
            phase = 'refreshing' if source == 'web' and web.get('phase') == 'refreshing' else 'verified'
        elif alive is None:
            phase = 'unknown'
        elif alive is False:
            phase = 'paused' if paused or web.get('phase') == 'paused' and source == 'web' else 'interrupted'
        elif paused:
            phase = 'pausing'
        elif fresh and progress.get('status') == 'waiting_retry' and matching_retry:
            phase = 'waiting_retry'
        elif active:
            phase = 'verifying' if all(e['phase'] == 'verifying' for e in active) else 'downloading'
        else:
            phase = 'checking'
        failed = retry.get('failed', {}) if matching_retry else {}
        failed_count = sum(i in selected and i not in verified for i in failed) if isinstance(failed, dict) else 0
        return {**base, 'source': source, 'phase': phase, 'kind': 'download',
                'worker_alive': alive, 'progress_at': updated if fresh else None,
                'stale': not fresh or now - updated > 120, 'active': active,
                'total_count': len(items), 'verified_count': len(verified),
                'total_bytes': sum(i['bytes'] for i in items),
                'verified_bytes': sum(selected[i]['bytes'] for i in verified),
                'pending_errors': failed_count,
                'next_retry_at': retry.get('next_retry_at') if matching_retry and phase == 'waiting_retry' else None}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError):
        # Malformed or changing state fails locally; no private paths/log messages leak.
        return {**base, 'phase': 'unknown', 'stale': True}
