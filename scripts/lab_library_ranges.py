"""Resumable range transfer from mirrors listed in Kiwix's official Metalink."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import threading
import time
import urllib.request

import linux_lab as lab

MIRRORS = ('https://ftp.fau.de/kiwix/zim/wikipedia/',
           'https://mirrors.dotsrc.org/kiwix/zim/wikipedia/',
           'https://ftp.nluug.nl/pub/kiwix/zim/wikipedia/')
CHUNK = 256 * 1024 * 1024


def download(partial, name, size, *, mirrors=None, status_path=None):
    lab.checked_mount()
    mirrors = mirrors or MIRRORS
    status_path = status_path or lab.MOUNT / 'data/catalog/kiwix.json'
    checkpoint = partial.with_suffix('.parts.json')
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state['name'] != name or state['size'] != size:
            raise RuntimeError('Le transfert existant appartient à une autre archive.')
    else:
        prefix = partial.stat().st_size if partial.exists() else 0
        if prefix >= size:
            if prefix == size:
                return  # Let the caller verify the completed sequential transfer.
            raise RuntimeError('Fichier partiel trop grand.')
        state = {'name': name, 'size': size, 'prefix': prefix, 'completed': []}
        lab.setup.write_json(checkpoint, state)
    fd = os.open(partial, os.O_RDWR | os.O_CREAT, 0o600)
    os.ftruncate(fd, size)
    lock = threading.Lock()
    ranges = [(i, offset, min(offset + CHUNK, size) - 1)
              for i, offset in enumerate(range(state['prefix'], size, CHUNK))]

    def transfer(item):
        index, start, end = item
        for attempt in range(6):
            url = mirrors[(index + attempt) % len(mirrors)] + name
            try:
                req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
                with urllib.request.urlopen(req, timeout=45) as response:
                    expected = f'bytes {start}-{end}/{size}'
                    if response.status != 206 or response.headers.get('Content-Range') != expected:
                        raise RuntimeError('Le miroir ne respecte pas la plage demandée.')
                    position = start
                    while position <= end:
                        block = response.read(min(1024 * 1024, end - position + 1))
                        if not block:
                            raise RuntimeError('Téléchargement interrompu.')
                        view = memoryview(block)
                        while view:
                            written = os.pwrite(fd, view, position)
                            position += written
                            view = view[written:]
                with lock:
                    # Make downloaded bytes durable before recording the range as complete.
                    os.fsync(fd)
                    state['completed'].append(index)
                    lab.setup.write_json(checkpoint, state)
                    done = state['prefix'] + sum(end_ - start_ + 1 for i, start_, end_ in ranges
                                                if i in state['completed'])
                    lab.setup.write_json(status_path,
                        {'preparing': name, 'archives': [], 'downloaded_bytes': done, 'total_bytes': size})
                    print(f'Wikipédia : {done / size:.1%}', flush=True)
                return
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(min(attempt + 1, 5))

    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(transfer, item) for item in ranges if item[0] not in state['completed']]
            for future in as_completed(futures):
                future.result()
    finally:
        os.close(fd)
