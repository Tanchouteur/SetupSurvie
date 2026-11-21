"""Prepare and verify the component installers for a disconnected Windows PC."""
import json
import re
import urllib.parse

import content
from delivery_paths import destination, locked
import setup

FOLDER = 'installateurs-windows'
CATALOG = 'app/deploy/windows-installers.json'
COMPONENTS = {'wsl', 'python', 'docker', 'git', 'ollama'}


def items(root):
    from pilot_kit import checked_entries

    if (root / 'kit-building.json').exists():
        raise setup.SetupError('Kit encore en préparation.')
    manifest = json.loads(destination(root, 'manifest.json').read_text(encoding='utf-8'))
    if (not isinstance(manifest, dict) or manifest.get('schema') != 1
            or manifest.get('kind') != 'SetupSurvie public pilot kit'
            or not isinstance(manifest.get('files'), list)):
        raise setup.SetupError('Choisissez un kit public SetupSurvie complet.')
    entry = [record for record in manifest['files']
             if isinstance(record, dict) and record.get('path') == CATALOG]
    if len(entry) != 1:
        raise setup.SetupError('Catalogue Windows absent ou dupliqué. Actualisez le logiciel du kit.')
    (_, catalog), = checked_entries(root, {'files': entry})
    recorded = json.loads(catalog.read_text(encoding='utf-8'))
    if (not isinstance(recorded, dict) or recorded.get('schema') != 1
            or not isinstance(recorded.get('installers'), list)):
        raise setup.SetupError('Catalogue des installateurs Windows non pris en charge.')
    packages = [recorded.get('wsl'), *recorded['installers']]
    if (len(packages) != len(COMPONENTS)
            or not all(isinstance(pkg, dict) and isinstance(pkg.get('id'), str) for pkg in packages)
            or {pkg['id'] for pkg in packages} != COMPONENTS):
        raise setup.SetupError('Le catalogue Windows est incomplet. Actualisez le logiciel du kit.')
    result = []
    names = set()
    for pkg in packages:
        name = pkg.get('file', '')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.(exe|msi)', name, re.ASCII):
            raise setup.SetupError('Nom d’installateur Windows non valide.')
        relative = f'{FOLDER}/{name}'
        destination(root, relative)
        if name.casefold() in names:
            raise setup.SetupError('Nom d’installateur Windows dupliqué.')
        names.add(name.casefold())
        address, size, digest = pkg.get('url'), pkg.get('bytes'), pkg.get('sha256')
        url = urllib.parse.urlsplit(address if isinstance(address, str) else '')
        if (url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment
                or type(size) is not int or not 0 < size <= 10_000_000_000
                or not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest)):
            raise setup.SetupError('URL, taille ou empreinte non valide dans le catalogue Windows. Actualisez le logiciel du kit.')
        result.append({'id': pkg['id'], 'path': relative, 'url': address,
                       'bytes': size, 'sha256': digest})
    return result


def check_file(path, item):
    if (not path.is_file() or path.stat().st_size != item['bytes']
            or setup.file_hash(path) != item['sha256']):
        raise setup.SetupError('Installateur Windows absent ou modifié : ' + path.name)


def prepare(root, *, verify_only=False):
    root = setup.safe_path(root)
    if not root.is_dir():
        raise setup.SetupError('Dossier du kit introuvable.')
    packages = items(root)
    if verify_only:
        for item in packages:
            check_file(destination(root, item['path']), item)
    else:
        with locked(destination(root, '.installateurs-windows.lock')):
            for item in packages:
                target = destination(root, item['path'])
                if not target.exists():
                    partial = destination(root, item['path'] + '.part')
                    copied = partial.stat().st_size if partial.is_file() else 0
                    content.check_capacity(root, max(0, item['bytes'] - copied), reserve=256 * 1024**2)
                content.transfer(root, item)
    print('Installateurs Windows vérifiés sur le kit.', flush=True)
