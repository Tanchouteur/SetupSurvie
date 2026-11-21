"""Host-side collection changes; the portal sees the catalogue read-only."""
import json

import setup
from delivery_paths import destination, locked
from pilot import category_index, collection_sort

DEFAULT_SORT_PATH = 'deploy/collection-sort-default.json'


def validate_keys(body):
    values = body.get('keys')
    if not isinstance(values, list) or not 1 <= len(values) <= 500 or any(
        not isinstance(key, str) or not collection_sort.KEY.fullmatch(key) for key in values
    ):
        raise setup.SetupError('Sélection de collections non valide.')
    return set(values)


def catalog_directory(root):
    return destination(root, 'catalog')


def installation_default():
    return collection_sort.read_file(setup.ROOT / DEFAULT_SORT_PATH)


def seed(root, sorting):
    with locked(destination(root, 'catalog/content.lock')):
        path = destination(root, 'catalog/' + collection_sort.FILENAME)
        if not path.exists():
            collection_sort.save(path.parent, sorting)


def merge(root, value):
    if value is None:
        return
    sorting = collection_sort.parse(value)
    with locked(destination(root, 'catalog/content.lock')):
        current = collection_sort.load(catalog_directory(root))
        excluded = current.excluded | sorting.excluded
        collection_sort.save(catalog_directory(root), collection_sort.Sort((current.other | sorting.other) - excluded, excluded))


def move(root, body):
    keys = validate_keys(body)
    state = body.get('state')
    if state not in ('main', 'other'):
        raise setup.SetupError('Classement de destination non valide.')
    with locked(destination(root, 'catalog/content.lock')):
        current = collection_sort.load(catalog_directory(root))
        if current.excluded & keys:
            raise setup.SetupError('Les exclusions se gèrent séparément des collections conservées.')
        collection_sort.save(catalog_directory(root), current.change(keys, state))
    return {'updated': len(keys)}


def preview(root, keys):
    return collection_sort.deletion_preview(destination(root,'library/zim'),keys,
        video_dir=destination(root,'library/video'),video_db=destination(root,'state/pilot/videos.db'))


def exclude(root, keys, token):
    from pilot import archive_index
    import search_index_queue
    with locked(destination(root, 'catalog/content.lock')), locked(destination(root, 'catalog/publication.lock')), locked(destination(root, 'state/pilot/archive-index/operation.lock')):
        current = preview(root, keys)
        if not current['files'] or current['token'] != token:
            raise setup.SetupError('La sélection a changé. Affichez de nouveau les fichiers à supprimer.')
        folder = catalog_directory(root)
        # Record the exclusion first so a retry after an interrupted deletion cannot download the archive again.
        collection_sort.save(folder, collection_sort.load(folder).change(keys, 'excluded'))
        for item in current['files']:
            name = item['name']
            destination(root,name).unlink()
            if not name.startswith('library/zim/') or name.endswith('.part'):
                continue
            index_name = archive_index.index_name(name.removeprefix('library/zim/'))
            for folder_name in ('archive-index', category_index.DIRECTORY):
                for suffix in ('.sqlite', '.building', '.building-journal'):
                    destination(root, f'state/pilot/{folder_name}/' + index_name + suffix).unlink(missing_ok=True)
        if any(key.startswith('zim:') for key in keys):
            with search_index_queue.edit(root) as queue:
                for field in ('pending','completed'):
                    queue[field]={path:record for path,record in queue[field].items()
                                  if collection_sort.path_key(path) not in keys}
                if collection_sort.path_key(queue.get('last_problem','')) in keys:
                    queue['hold']=''
                    queue.pop('last_problem',None)
        receipt = destination(root, 'catalog/downloaded-content.json')
        if receipt.is_file():
            records = json.loads(receipt.read_text(encoding='utf-8'))
            if isinstance(records, dict) and isinstance(records.get('items'), list):
                records['items'] = [entry for entry in records['items'] if collection_sort.path_key(entry.get('path', '')) not in keys]
                setup.write_json(receipt, records)
    return current['bytes']
