"""Prepare verified Linux x86-64 installers for a later disconnected transfer."""
import json
import platform
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import content
import setup
from delivery_paths import destination, locked
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


KIT_FOLDER = 'installateurs-linux'
CATALOG = 'app/deploy/linux-offline-installers.txt'
KIT_PYTHON = 'python-3.13.tar.gz'
RECEIPT = f'{FOLDER}/python-archive.txt'


def kit_packages(root):
    from pilot_kit import checked_entries

    if (root/'kit-building.json').exists():
        raise setup.SetupError('Kit encore en préparation.')
    manifest = json.loads(destination(root, 'manifest.json').read_text(encoding='utf-8'))
    if (not isinstance(manifest, dict) or manifest.get('schema') != 1
            or manifest.get('kind') != 'SetupSurvie public pilot kit'
            or not isinstance(manifest.get('files'), list)):
        raise setup.SetupError('Choisissez un kit public SetupSurvie complet.')
    records = [record for record in manifest['files']
               if isinstance(record, dict) and record.get('path') == CATALOG]
    if len(records) != 1:
        raise setup.SetupError('Catalogue Linux absent ou dupliqué. Actualisez le logiciel du kit.')
    (_, catalog), = checked_entries(root, {'files': records})
    packages = {}
    for line in catalog.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        digest, size, name, url = line.split()
        address = urlsplit(url)
        size = int(size)
        if (not re.fullmatch(r'[0-9a-f]{64}', digest) or not 0 < size < 1_000_000_000
                or not re.fullmatch(r'(?:[a-z0-9]+/)?[A-Za-z0-9][A-Za-z0-9._+-]*', name)
                or address.scheme != 'https' or not address.hostname
                or address.username or address.password or address.fragment
                or name in packages):
            raise setup.SetupError('Catalogue d’installateurs Linux non valide.')
        packages[name] = {'id': name, 'path': f'{KIT_FOLDER}/{FOLDER}/{name}', 'url': url,
                          'bytes': size, 'sha256': digest}
    names = ['docker.tar.gz', 'docker-compose', KIT_PYTHON]
    for prefix in ('', 'debian12/', 'ubuntu2204/'):
        dependencies = [name for name in packages if name.startswith(prefix)
                        and '/' not in name[len(prefix):] and name.endswith('.deb')]
        if not any(name[len(prefix):].startswith('nftables_') for name in dependencies):
            raise setup.SetupError('Paquets nftables absents du catalogue Linux.')
        names.extend(dependencies)
    if not all(name in packages for name in names):
        raise setup.SetupError('Installateurs Linux absents du catalogue.')
    return [packages[name] for name in names]


def kit_items(root):
    packages = kit_packages(root)
    relative = f'{KIT_FOLDER}/{RECEIPT}'
    receipt = destination(root, relative)
    body = (KIT_PYTHON+'\n').encode('ascii')
    if not receipt.is_file() or receipt.stat().st_size != len(body) or receipt.read_bytes() != body:
        raise setup.SetupError('La préparation des installateurs Linux doit être terminée.')
    return [*packages, {'path': relative, 'bytes': len(body), 'sha256': setup.file_hash(receipt)}]


def prepare_kit(root, *, verify_only=False):
    root = setup.safe_path(root)
    if not verify_only:
        with locked(destination(root, '.installateurs-linux.lock')):
            for item in kit_packages(root):
                target = destination(root, item['path'])
                if not target.is_file():
                    partial = destination(root, item['path']+'.part')
                    staged = partial.stat().st_size if partial.is_file() else 0
                    content.check_capacity(root, max(0, item['bytes'] - staged), reserve=256 * 1024**2)
                content.transfer(root, item)
            durable.write_bytes(destination(root, f'{KIT_FOLDER}/{RECEIPT}'), (KIT_PYTHON+'\n').encode('ascii'))
    for item in kit_items(root):
        path = destination(root, item['path'])
        if (not path.is_file() or path.stat().st_size != item['bytes']
                or setup.file_hash(path) != item['sha256']):
            raise setup.SetupError('Installateur Linux absent ou modifié : '+path.name)
    print('Python, Docker, Compose et les paquets réseau Linux sont vérifiés sur le kit.', flush=True)
