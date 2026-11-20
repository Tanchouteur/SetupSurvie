"""Prepare verified Linux x86-64 installers for a later disconnected transfer."""
import platform
import sys
from pathlib import Path

import content
import setup
from delivery_paths import locked
from pilot import durable

FOLDER = 'tools/linux-offline-installers'


def prepare(data):
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        return False
    python_archive = f'python-{sys.version_info.major}.{sys.version_info.minor}.tar.gz'
    catalog = setup.ROOT / 'deploy/linux-offline-installers.txt'
    packages = {}
    for line in catalog.read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#'):
            digest, size, name, url = line.split()
            packages[name] = {'id': name, 'path': f'{FOLDER}/{name}',
                              'url': url, 'bytes': int(size), 'sha256': digest}
    if python_archive not in packages:
        return False
    parts = ['docker.tar.gz', 'docker-compose', python_archive]
    parts.extend(name for name in packages if name.endswith('.deb'))
    data = Path(data)
    with locked(content.destination(data, f'{FOLDER}/download.lock')):
        for name in parts:
            item = packages[name]
            target = content.destination(data, item['path'])
            if not target.is_file():
                content.check_capacity(data, item['bytes'])
            content.transfer(data, item)
        receipt = content.destination(data, f'{FOLDER}/python-archive.txt')
        durable.write_bytes(receipt, (python_archive + '\n').encode('ascii'))
    return True
