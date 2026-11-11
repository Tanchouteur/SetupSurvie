"""Inventory of files on disk, independent of a loaded language model."""
import json
import os
from pathlib import Path
import re

from . import library, store

ZIMS = Path(os.environ.get('ZIM_DIR', '/zim'))
MODELS = Path(os.environ.get('MODELS_DIR', '/models'))
LANGUAGES = {'fr': 'Français', 'fra': 'Français', 'en': 'Anglais', 'eng': 'Anglais'}


def local_file(path, root):
    return path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())


def model_inventory():
    result = []
    manifests = MODELS / 'manifests'
    for path in sorted(manifests.glob('*/*/*/*')):
        if not local_file(path, MODELS) or path.stat().st_size > 1_000_000:
            continue
        name = path.parent.name + ':' + path.name
        try:
            manifest = json.loads(path.read_text())
            layers = [manifest['config'], *manifest['layers']]
            ready = True
            size = 0
            for layer in layers:
                digest, length = layer['digest'], layer['size']
                if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest) or type(length) is not int or length < 0:
                    raise ValueError('Invalid manifest')
                blob = MODELS / 'blobs' / digest.replace(':', '-')
                ready = ready and local_file(blob, MODELS) and blob.stat().st_size == length
                size += length
            result.append({'name': name, 'bytes': size, 'ready': ready,
                           'description': 'Fichiers du modèle présents. Un modèle enregistré sur le disque n’occupe pas forcément la mémoire de la carte graphique.' if ready else 'Certains fichiers du modèle sont absents ou incomplets.'})
        except (ValueError, KeyError, TypeError, OSError):
            result.append({'name': name, 'bytes': None, 'ready': False,
                           'description': 'Les fichiers de ce modèle doivent être vérifiés.'})
    return result


async def inventory():
    loaded = {book['book']: book for book in await library.books()}
    books = []
    for path in sorted(ZIMS.glob('*')):
        if not (path.name.endswith('.zim') or path.name.endswith('.zim.part')) or not local_file(path, ZIMS):
            continue
        complete = path.name.endswith('.zim')
        stem = path.name.removesuffix('.part').removesuffix('.zim')
        book = loaded.get(stem)
        match = re.fullmatch(r'(wikipedia|wikibooks|vikidia|appropedia)_([a-z]+)_.*_(\d{4}-\d{2})', stem)
        title = book.get('title') if book else stem
        language = LANGUAGES.get(book.get('language'), book.get('language')) if book else ''
        version = ''
        if match:
            kind, lang, version = match.groups()
            language = LANGUAGES.get(lang, lang)
            title = {'wikipedia':'Wikipédia','wikibooks':'Wikilivres','vikidia':'Vikidia pour les enfants','appropedia':'Appropedia : techniques et autonomie'}[kind] + ' — ' + language
        ready = complete and bool(book)
        books.append({'id': stem, 'title': title, 'language': language,
                      'version': version, 'bytes': path.stat().st_size, 'ready': ready,
                      'url': '/content/' + stem + '/',
                      'description': ('Articles encyclopédiques avec leurs illustrations.' if stem.startswith('wikipedia_') else 'Livres pédagogiques et guides pratiques.') if ready else ('Téléchargement incomplet.' if not complete else 'Archive présente, mais le service de lecture ne la propose pas actuellement.')})
    guides = []
    with store.connect() as db:
        rows = db.execute('SELECT id,title,language FROM documents ORDER BY title').fetchall()
        metadata = {r['path']: dict(r) for r in db.execute('SELECT * FROM guide_meta')}
    for row in rows:
        relative = row['id'].removeprefix('guide:')
        path = library.GUIDES / relative
        ready = local_file(path, library.GUIDES)
        meta = metadata.get(relative, {})
        guides.append({**dict(row), 'language': LANGUAGES.get(row['language'], 'Langue non précisée'),
                       'bytes': path.stat().st_size if ready else None, 'ready': ready,
                       'description': meta.get('provenance') or 'Document consultable directement dans la bibliothèque.'})
    return {'books': books, 'guides': guides, 'models': model_inventory(),
            'note': 'L’inventaire vérifie la présence des fichiers et leur disponibilité pour la lecture. Il ne télécharge rien et ne lance aucun modèle. Les tailles des modèles incluent des fichiers qui peuvent être partagés entre plusieurs modèles.'}
