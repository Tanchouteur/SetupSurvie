"""Inventory of files on disk, independent of a loaded language model."""
import json
import os
from pathlib import Path
import re

from . import collection_sort,network,library, store,catalogue

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


def collection_labels(stem,title):
    """Display grouping only; immutable archive identifiers and links stay intact."""
    return catalogue.automatic_labels(stem,title)


async def inventory():
    loaded = {book['book']: book for book in await library.books()}
    saved_labels=catalogue.snapshot()
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
        if not version:
            date=re.search(r'_(\d{4}-\d{2})$',stem)
            version=date[1] if date else ''
        ready = complete and bool(book)
        books.append({'id': stem, 'title': title, 'language': language,
                      'version': version, 'bytes': path.stat().st_size, 'ready': ready, 'sort_key': collection_sort.archive(path.name),**catalogue.collection_labels(stem,title,library.GUIDES,ZIMS,saved_labels),
                      'url': '/content/' + stem + '/',
                      # Kiwix identifier of the archive: the portal shows its own illustration.
                      'icon_id': (book.get('search_id') or '') if book else '',
                      'description': (book.get('description') if book and book.get('description') else '') or ('Articles encyclopédiques avec leurs illustrations.' if stem.startswith('wikipedia_') else 'Livres pédagogiques et guides pratiques.') if ready else ('Téléchargement incomplet.' if not complete else 'Archive présente, mais le service de lecture ne la propose pas actuellement.')})
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


def sortable_collections():
    from . import videos
    sorting=collection_sort.load(network.CATALOG)
    saved=catalogue.snapshot()
    _, cached=library.kiwix_catalog.snapshot(store.ROOT,library.KIWIX)
    books={book['book']:book for book in (cached or {}).get('items',[]) if isinstance(book,dict) and book.get('book')}
    titles={key:book.get('title') for key,book in books.items()}
    items={}
    for path,info in collection_sort.archive_files(ZIMS):
        key=collection_sort.archive(path.name)
        stem=path.name.removesuffix('.part').removesuffix('.zim')
        labels=catalogue.collection_labels(stem,titles.get(stem) or stem,library.GUIDES,ZIMS,saved)
        description=books.get(stem,{}).get('description')
        item=items.setdefault(key,{'key':key,'title':labels['family']+' — '+labels['variant'],
                                   'family':labels['family'],'variant':labels['variant'],
                                   'description':description[:300] if isinstance(description,str) else '',
                                   'files':[],'bytes':0,'state':sorting.state(key),'kind':'archive'})
        if path.name.endswith('.zim'):item.setdefault('url','/content/'+stem+'/')
        item['files'].append(path.name);item['bytes']+=info.st_size
    seen=set()
    for key,label,path,info in collection_sort.video_files(videos.ROOT,store.ROOT/'videos.db'):
        if (key,path) in seen:continue
        seen.add((key,path))
        item=items.setdefault(key,{'key':key,'title':label if label!='.' else 'Vidéos locales',
                                   'family':'Vidéos','variant':label if label!='.' else 'Vidéos locales',
                                   'description':'','files':[],'bytes':0,'state':sorting.state(key),'kind':'video','count':0})
        item['bytes']+=info.st_size
        if path.suffix.lower() not in ('.json','.srt','.vtt'):item['count']+=1
    return sorted(items.values(),key=lambda item:(-item['bytes'],item['title'].casefold()))
