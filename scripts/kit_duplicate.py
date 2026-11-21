"""Duplicate a public installation kit without a source installation or network."""
import hashlib
import json
from pathlib import Path
import re
import shutil

from delivery_paths import destination, locked
import kit_audit
from pilot import durable
import setup
import transfer
import windows_kit_installers


MARKER = 'kit-building.json'
KIND = 'SetupSurvie public kit duplication'


def inventory(root):
    if destination(root, MARKER).exists():
        raise setup.SetupError('Le kit source est encore en préparation.')
    manifest = destination(root, 'manifest.json').read_bytes()
    catalog = json.loads(manifest)
    if (not isinstance(catalog, dict) or catalog.get('schema') != 1
            or catalog.get('kind') != 'SetupSurvie public pilot kit'
            or not isinstance(catalog.get('files'), list)):
        raise setup.SetupError('Choisissez un kit public SetupSurvie complet.')
    files = list(catalog['files'])
    seen = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str):
            raise setup.SetupError('Inventaire du kit non valide.')
        name = item['path']
        if (name.casefold() in seen or type(item.get('bytes')) is not int or item['bytes'] < 0
                or not isinstance(item.get('sha256'), str) or not re.fullmatch('[a-f0-9]{64}', item['sha256'])):
            raise setup.SetupError('Entrée de manifeste non valide ou dupliquée : ' + name)
        seen.add(name.casefold())
        source = destination(root, name)
        if not source.is_file() or source.stat().st_size != item['bytes']:
            raise setup.SetupError('Fichier absent ou incomplet dans le kit : ' + name)
    kit_audit.validate(root, catalog)
    tools = destination(root, windows_kit_installers.FOLDER)
    if tools.exists():
        installers = windows_kit_installers.items(root)
        for item in installers:
            path = destination(root, item['path'])
            if not path.is_file() or path.stat().st_size != item['bytes']:
                raise setup.SetupError('Terminez la préparation des installateurs Windows : ' + path.name)
        files.extend(installers)
        files.extend(windows_component_files(root))
    return manifest, files


def windows_component_files(root):
    base = windows_kit_installers.FOLDER + '/sxs'
    folder = destination(root, base)
    if not folder.exists():
        return []
    if not folder.is_dir():
        raise setup.SetupError('Dossier des composants Windows sxs non valide.')
    result = []
    names = set()
    for path in sorted(folder.rglob('*')):
        relative = path.relative_to(root).as_posix()
        destination(root, relative)
        if path.is_dir():
            continue
        if relative.casefold() in names:
            raise setup.SetupError('Deux paquets Windows portent le même nom : ' + path.name)
        names.add(relative.casefold())
        if path.suffix.lower() != '.cab' or not path.is_file():
            raise setup.SetupError('Le dossier sxs doit contenir uniquement des paquets CAB : ' + path.name)
        result.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': setup.file_hash(path)})
    return result


def duplicate(source, target):
    source, target = setup.safe_path(source), setup.safe_path(target)
    if source.is_relative_to(target) or target.is_relative_to(source):
        raise setup.SetupError('Choisissez un dossier de destination extérieur au kit source.')
    if not target.parent.is_dir():
        raise setup.SetupError('Le dossier parent de destination doit déjà exister.')
    with locked(target.parent / ('.' + target.name + '-kit-duplication.lock')):
        manifest, files = inventory(source)
        marker = destination(target, MARKER)
        identity = {'kind': KIND, 'manifest': hashlib.sha256(manifest).hexdigest(),
                    'files': [{k: item[k] for k in ('path', 'bytes', 'sha256')} for item in files]}
        if marker.is_file():
            if json.loads(marker.read_text(encoding='utf-8')) != identity:
                raise setup.SetupError('Ce dossier contient une autre préparation. Reprenez avec le kit initial.')
        else:
            if target.exists() and (not target.is_dir() or any(target.iterdir())):
                raise setup.SetupError('Le dossier de destination est déjà utilisé. Choisissez un dossier vide.')
            durable.mkdir(target)
            setup.write_json(marker, identity)
        copy_files(source, target, files)
        if destination(source, MARKER).exists() or destination(source, 'manifest.json').read_bytes() != manifest:
            raise setup.SetupError('Le kit source a changé pendant la duplication. Aucun kit publié.')
        durable.write_bytes(destination(target, 'manifest.json'), manifest)
        marker.unlink()
        durable.sync_directory(target)
    print('Second kit vérifié. Vous pouvez éjecter le support.', flush=True)


def copy_files(source, target, files):
    missing = 0
    for item in files:
        path = destination(target, item['path'])
        if not path.is_file():
            part = destination(target, item['path'] + '.transfer-part')
            missing += max(0, item['bytes'] - (part.stat().st_size if part.is_file() else 0))
    if shutil.disk_usage(target).free < missing + 256 * 1024**2:
        raise setup.SetupError('Place insuffisante pour copier le kit.')
    for number, item in enumerate(files, 1):
        origin, copy = destination(source, item['path']), destination(target, item['path'])
        if number == 1 or number == len(files) or number % 100 == 0:
            print(f'Copie du kit : {number}/{len(files)} fichiers.', flush=True)
        info = origin.stat()
        record = {**item, 'mtime_ns': info.st_mtime_ns}
        transfer.copy_file(origin, copy, record, file_progress(copy.name), expected_sha256=item['sha256'])


def file_progress(name):
    last = 0

    def progress(phase, copied, total):
        nonlocal last
        gib = copied // 1024**3
        if phase == 'Copie' and gib > last:
            last = gib
            print(f'{name} : {copied * 100 // total} %', flush=True)

    return progress
