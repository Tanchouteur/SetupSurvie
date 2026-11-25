#!/usr/bin/env python3
"""Read-only breakdown of the disk space used by an installation, for the portal.

The host controller runs it in a background thread: walking the search indexes
can take minutes. Only sizes and relative names leave this module, never
absolute paths or file contents.
"""
import fnmatch
import os
from pathlib import Path
import shutil
import stat
import threading
import time

import setup

SCHEMA = 1
REPORT = 'storage-report.json'
MAX_AGE = 24 * 3600
TOP = 10

CATEGORIES = {
    'library': 'Bibliothèque',
    'models': 'Assistant IA',
    'indexes': 'Index et caches de recherche',
    'profiles': 'Profils et réglages',
    'software': 'Logiciels et outils',
    'backups': 'Copies de sécurité',
    'temporary': 'Fichiers temporaires',
    'other': 'Autres fichiers',
}

# id: (category, label, rebuildable, explanation)
ITEMS = {
    'zim': ('library', 'Wikipédia et archives illustrées', False, 'Archives ZIM lues par Kiwix.'),
    'maps': ('library', 'Cartes et itinéraires', False, 'Fonds de carte PMTiles, géographie et calcul d’itinéraires.'),
    'videos': ('library', 'Vidéos', False, 'Vidéos locales et listes YouTube téléchargées.'),
    'guides': ('library', 'Guides et documents', False, 'Guides pratiques et documents ajoutés.'),
    'ebooks': ('library', 'Livres personnels', False, 'Ebooks privés de la famille.'),
    'library-other': ('library', 'Autres fichiers de la bibliothèque', False, ''),
    'catalog': ('library', 'Catalogue', True, 'Description des contenus, recalculée par l’installation.'),
    'models': ('models', 'Modèles d’IA', False, 'Modèles téléchargés pour l’assistant.'),
    'archive-index': ('indexes', 'Index de recherche des archives', True, 'Peut être recalculé, mais c’est long.'),
    'category-index': ('indexes', 'Index des catégories', True, 'Recalculé automatiquement.'),
    'search-cache': ('indexes', 'Caches de recherche', True, 'Peut être vidé sans perte.'),
    'video-db': ('indexes', 'Catalogue des vidéos des archives', True, 'Recalculé depuis les archives.'),
    'zim-videos': ('indexes', 'Vidéos extraites des archives', True, 'Copies prêtes à lire, extraites des archives ZIM.'),
    'webui-cache': ('indexes', 'Caches d’Open WebUI', True, 'Modèles de transcription et d’embeddings.'),
    'pilot-state': ('profiles', 'Profils, conversations et réglages du portail', False, 'Données personnelles à conserver.'),
    'webui': ('profiles', 'Open WebUI (comptes et conversations)', False, 'Données personnelles à conserver.'),
    'caddy': ('profiles', 'Certificats du réseau local', False, ''),
    'state-other': ('profiles', 'Autres données d’état', False, ''),
    'private': ('profiles', 'Réglages privés de l’installation', False, 'Clés et réglages ; à conserver.'),
    'application': ('software', 'Logiciel SetupSurvie', False, ''),
    'docker': ('software', 'Disque des conteneurs (Docker)', False, 'Images et volumes des services.'),
    'images': ('software', 'Images des conteneurs pour la copie hors ligne', False, ''),
    'tools': ('software', 'Outils embarqués', False, 'Python, Ollama, Docker Desktop, FFmpeg…'),
    'installers': ('software', 'Installateurs', False, 'Programmes d’installation gardés pour le hors-ligne.'),
    'maintenance': ('software', 'Outils de maintenance', False, 'Dépôt servant aux mises à jour.'),
    'restore-point': ('backups', 'Point de restauration', False, 'Copie complète scellée de l’installation.'),
    'old-installs': ('backups', 'Anciennes installations archivées', False, ''),
    'updates': ('backups', 'Sauvegardes des mises à jour', False, 'Permettent de revenir à la version précédente.'),
    'old-app': ('backups', 'Anciennes versions du logiciel', False, 'Gardées après une mise à jour interrompue.'),
    'cache': ('temporary', 'Cache', True, ''),
    'tmp': ('temporary', 'Fichiers temporaires', True, ''),
    'diagnostics': ('temporary', 'Diagnostics et journaux', False, 'Rapports utiles en cas de problème.'),
    'data-other': ('other', 'Autres fichiers des données', False, ''),
    'base-other': ('other', 'Autres fichiers du dossier d’installation', False, ''),
}

# Rules inside the data folder: relative pattern → item. A rule whose folder has
# deeper rules is descended; its unmatched entries stay with it.
DATA_RULES = (
    ('', 'data-other'),
    ('library', 'library-other'), ('library/zim', 'zim'), ('library/maps', 'maps'),
    ('library/video', 'videos'), ('library/videos', 'videos'), ('library/guides', 'guides'),
    ('library/ebooks', 'ebooks'), ('catalog', 'catalog'), ('models', 'models'),
    ('state', 'state-other'), ('state/pilot', 'pilot-state'),
    ('state/pilot/archive-index', 'archive-index'), ('state/pilot/category-index', 'category-index'),
    ('state/pilot/cache', 'search-cache'), ('state/pilot/index-cache', 'search-cache'),
    ('state/pilot/videos.db*', 'video-db'), ('state/pilot/videos-report.json', 'video-db'),
    ('state/pilot/zim-videos', 'zim-videos'),
    ('state/openwebui', 'webui'), ('state/openwebui/cache', 'webui-cache'), ('state/caddy', 'caddy'),
    ('docker', 'docker'), ('tools', 'tools'), ('installers', 'installers'),
    ('cache', 'cache'), ('tmp', 'tmp'), ('diagnostics', 'diagnostics'),
)

# Entries next to the application in a dedicated installation folder.
BASE_RULES = (
    ('', 'base-other'), ('application.*', 'old-app'), ('updates', 'updates'),
    ('maintenance*', 'maintenance'), ('images.tar*', 'images'),
)

RECOVERY_RULES = (('', 'old-installs'), ('point', 'restore-point'), ('point-verifie.json', 'restore-point'))


class Walker:
    """Sizes as allocated on disk, links never followed, hard links counted once."""

    def __init__(self):
        self.seen = set()
        self.items = {}

    def item(self, identifier, device):
        value = self.items.setdefault(identifier, {'bytes': 0, 'files': 0, 'unreadable': 0, 'devices': {}, 'top': {}})
        value['devices'].setdefault(device, 0)
        return value

    def size(self, entry):
        info = entry.stat(follow_symlinks=False)
        if os.name != 'nt' and info.st_nlink > 1:
            key = (info.st_dev, info.st_ino)
            if key in self.seen:
                return 0
            self.seen.add(key)
        return info.st_blocks * 512 if hasattr(info, 'st_blocks') else info.st_size

    def tree(self, path):
        """Return (bytes, files, unreadable) for a whole folder."""
        total = files = unreadable = 0
        stack = [path]
        while stack:
            folder = stack.pop()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        try:
                            if entry.is_symlink() or getattr(entry, 'is_junction', lambda: False)():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                total += self.size(entry)
                                files += 1
                        except OSError:
                            unreadable += 1
            except OSError:
                unreadable += 1
        return total, files, unreadable

    def add(self, identifier, device, entry, name, expand=False):
        """Count an entry; with expand, its direct children become the detail lines."""
        value = self.item(identifier, device)
        try:
            if entry.is_symlink() or getattr(entry, 'is_junction', lambda: False)():
                return
            if entry.is_dir(follow_symlinks=False):
                if expand:
                    try:
                        children = list(os.scandir(entry.path))
                    except OSError:
                        value['unreadable'] += 1
                        return
                    for child in children:
                        self.add(identifier, device, child, child.name + ('/' if _folder(child) else ''))
                    return
                size, files, unreadable = self.tree(entry.path)
            elif entry.is_file(follow_symlinks=False):
                size, files, unreadable = self.size(entry), 1, 0
            else:
                return
        except OSError:
            value['unreadable'] += 1
            return
        value['bytes'] += size
        value['files'] += files
        value['unreadable'] += unreadable
        value['devices'][device] += size
        value['top'][name] = value['top'].get(name, 0) + size

    def classify(self, root, rules, device, relative=''):
        """Walk root, attributing each entry to the most specific matching rule."""
        own = owner(rules, relative)
        self.item(own, device)
        try:
            entries = list(os.scandir(root))
        except OSError:
            self.item(own, device)['unreadable'] += 1
            return
        for entry in entries:
            child = (relative + '/' if relative else '') + entry.name
            exact = owner(rules, child, exact=True)
            deeper = any(pattern.startswith(child + '/') for pattern, _ in rules)
            folder = _folder(entry)
            if deeper and folder:
                self.classify(entry.path, rules, device, child)
            elif exact:
                # The detail lines list what is inside the item's folder.
                self.add(exact, device, entry, entry.name, expand=folder)
            else:
                self.add(own, device, entry, entry.name + ('/' if folder else ''))


def _folder(entry):
    try:
        return entry.is_dir(follow_symlinks=False) and not entry.is_symlink()
    except OSError:
        return False


def owner(rules, relative, exact=False):
    best, length = None, -1
    for pattern, identifier in rules:
        if exact:
            if fnmatch.fnmatchcase(relative, pattern) and pattern:
                best = identifier
        elif pattern == '' or relative == pattern or relative.startswith(pattern + '/'):
            if len(pattern) > length:
                best, length = identifier, len(pattern)
    return best


def device_of(path):
    try:
        return str(os.stat(path).st_dev)
    except OSError:
        return 'inconnu'


def disk_label(path):
    path = Path(path)
    if os.name == 'nt':
        return (path.drive or str(path)).upper()
    current = path
    while not current.is_mount() and current != current.parent:
        current = current.parent
    return str(current)


def recovery_folder(base):
    return base.parent / ('.' + base.name + '-secours')


def locations(app, config):
    """Roots to analyse, with the dedicated installation folder when there is one."""
    import transfer
    try:
        roots = transfer.roots(app, config)
    except setup.SetupError:
        roots = {'application': setup.safe_path(config.get('app_dir', setup.ROOT)),
                 'data': setup.safe_path(config['data_dir']), 'private': Path(app.work)}
    base = roots['application'].parent
    dedicated = roots['data'].parent == base and Path(roots['private']).parent == base
    return roots, (base if dedicated else None)


def scan(app, config, storage_root=None):
    started = time.monotonic()
    walker = Walker()
    roots, base = locations(app, config)
    data = roots['data']
    scanned = []
    if base is not None:
        known = {path.name: role for role, path in roots.items() if Path(path).parent == base}
        device = device_of(base)
        for entry in os.scandir(base):
            role = known.get(entry.name)
            if role == 'data':
                continue
            if role in ('application', 'private'):
                walker.add(role, device, entry, entry.name, expand=True)
            else:
                exact = owner(BASE_RULES, entry.name, exact=True) or 'base-other'
                walker.add(exact, device, entry, entry.name, expand=exact == 'updates')
        scanned.append(base)
    else:
        for role, identifier in (('application', 'application'), ('private', 'private'),
                                 ('updates-archive', 'updates'), ('maintenance-archive', 'maintenance')):
            path = roots.get(role)
            if path and Path(path).is_dir():
                walker.add(identifier, device_of(path), _Entry(Path(path)), Path(path).name, expand=True)
                scanned.append(Path(path))
    walker.classify(data, DATA_RULES, device_of(data))
    scanned.append(data)
    for disk in docker_disks():
        if not disk.is_relative_to(data):
            walker.add('docker', device_of(disk), _Entry(disk), disk.parent.name + '/' + disk.name)
            scanned.append(disk.parent)
    if roots.get('installers-cache'):
        cache = Path(roots['installers-cache'])
        walker.add('installers', device_of(cache), _Entry(cache), 'Cache Windows des installateurs')
        scanned.append(cache)
    recovery = recovery_folder(base or roots['application'].parent)
    if recovery.is_dir():
        device = device_of(recovery)
        walker.classify(recovery, RECOVERY_RULES, device)
        restore = walker.item('restore-point', device)
        if not restore['bytes']:
            # The sealed point is root-only: fall back on the size its manifest declares.
            declared = declared_size(recovery / 'point')
            if declared:
                restore.update(bytes=declared, estimated=True)
                restore['devices'][device] = declared
            elif not os.access(recovery, os.R_OK | os.X_OK):
                restore['unreadable'] += 1
        scanned.append(recovery)
    return build(walker, scanned, data, started, storage_root)


class _Entry:
    """Minimal os.DirEntry stand-in for a root folder."""

    def __init__(self, path):
        self.path, self.name = str(path), path.name

    def is_symlink(self):
        return Path(self.path).is_symlink()

    def is_dir(self, follow_symlinks=False):
        return Path(self.path).is_dir()

    def is_file(self, follow_symlinks=False):
        return Path(self.path).is_file()

    def stat(self, follow_symlinks=False):
        return os.stat(self.path, follow_symlinks=follow_symlinks)


DOCKER_SETTINGS = ('customWslDistroDir', 'diskImageLocation', 'dataFolder', 'wslDataRoot')
DOCKER_DISKS = ('docker_data.vhdx', 'disk/docker_data.vhdx', 'data/docker_data.vhdx', 'main/ext4.vhdx',
                'DockerDesktopWSL/disk/docker_data.vhdx', 'DockerDesktopWSL/main/ext4.vhdx')


def docker_disks():
    """Docker Desktop's WSL disks, wherever its settings put them (same lookup as transfer-host-check.ps1)."""
    if os.name != 'nt':
        return []
    roots = []
    if os.environ.get('LOCALAPPDATA'):
        roots.append(Path(os.environ['LOCALAPPDATA']) / 'Docker/wsl')
    if os.environ.get('APPDATA'):
        import transfer
        for name in ('settings-store.json', 'settings.json'):
            try:
                settings = transfer.read(Path(os.environ['APPDATA']) / 'Docker' / name)
            except (OSError, ValueError):
                continue
            if isinstance(settings, dict):
                # Docker writes "CustomWslDistroDir"; PowerShell reads keys case-insensitively, so do we.
                values = {str(key).casefold(): value for key, value in settings.items()}
                roots += [Path(values[key.casefold()]) for key in DOCKER_SETTINGS
                          if isinstance(values.get(key.casefold()), str) and values[key.casefold()]]
    found = []
    for root in roots:
        for relative in DOCKER_DISKS:
            path = root / relative
            try:
                if path.is_file() and not path.is_symlink() and path.resolve() not in found:
                    found.append(path.resolve())
            except OSError:
                continue
    return found


def declared_size(point):
    """Size recorded by the sealed point's manifest when the folder itself is unreadable."""
    import transfer
    try:
        value = transfer.read(point / 'transfer.json').get('bytes')
        return value if type(value) is int and value >= 0 else 0
    except (OSError, ValueError, AttributeError):
        return 0


def disks(paths, data, storage_root=None):
    result = {}
    data_device = device_of(data)
    # Measure the data folder first so its disk carries the data folder's free space.
    for path in [data, *paths]:
        device = device_of(path)
        if device in result:
            continue
        try:
            usage = shutil.disk_usage(path)
        except OSError:
            continue
        free = usage.free
        if storage_root is not None and device == data_device:
            try:
                import content
                free = min(free, content.free_space(Path(data), storage_root))
            except (OSError, setup.SetupError):
                pass
        result[device] = {'id': device, 'label': disk_label(path), 'total': usage.total,
                          'used': usage.used, 'free': free, 'data': device == data_device}
    return result


def build(walker, scanned, data, started, storage_root=None):
    found = disks(scanned, data, storage_root)
    items = []
    for identifier, value in walker.items.items():
        category, label, rebuildable, note = ITEMS[identifier]
        if not value['bytes'] and not value['unreadable']:
            continue
        top = sorted(value['top'].items(), key=lambda pair: -pair[1])[:TOP]
        items.append({'id': identifier, 'category': category, 'label': label, 'note': note,
                      'rebuildable': rebuildable, 'bytes': value['bytes'], 'files': value['files'],
                      'unreadable': value['unreadable'], 'estimated': value.get('estimated', False),
                      'disks': {device: size for device, size in value['devices'].items() if size},
                      'top': [{'name': name, 'bytes': size} for name, size in top if size]})
    items.sort(key=lambda item: -item['bytes'])
    for disk in found.values():
        disk['setupsurvie'] = sum(size for item in items if item['category'] != 'backups'
                                  for device, size in item['disks'].items() if device == disk['id'])
        disk['backups'] = sum(size for item in items if item['category'] == 'backups'
                              for device, size in item['disks'].items() if device == disk['id'])
    categories = []
    for identifier, label in CATEGORIES.items():
        members = [item for item in items if item['category'] == identifier]
        if members:
            categories.append({'id': identifier, 'label': label, 'bytes': sum(i['bytes'] for i in members),
                               'rebuildable_bytes': sum(i['bytes'] for i in members if i['rebuildable'])})
    categories.sort(key=lambda category: -category['bytes'])
    ordered = sorted(found.values(), key=lambda disk: (not disk['data'], disk['label']))
    return {'schema': SCHEMA, 'scanned_at': time.time(), 'duration_ms': round((time.monotonic() - started) * 1000),
            'total': sum(item['bytes'] for item in items if item['category'] != 'backups'),
            'backups': sum(item['bytes'] for item in items if item['category'] == 'backups'),
            'rebuildable': sum(item['bytes'] for item in items if item['rebuildable']),
            'disks': ordered, 'categories': categories, 'items': items}


class Analyzer:
    """One background analysis at a time; the last report survives restarts."""

    def __init__(self, app, config, storage_root=None):
        self.app, self.config, self.storage_root = app, config, storage_root
        self.lock = threading.Lock()
        self.running = False
        self.error = None

    @property
    def path(self):
        return Path(self.app.work) / REPORT

    def read(self):
        try:
            import transfer
            value = transfer.read(self.path)
            return value if isinstance(value, dict) and value.get('schema') == SCHEMA else None
        except (OSError, ValueError):
            return None

    def start(self):
        import transfer
        transfer.guard(self.app.work)
        with self.lock:
            if self.running:
                return False
            self.running, self.error = True, None
        threading.Thread(target=self.run, daemon=True, name='storage-report').start()
        return True

    def run(self):
        try:
            report = scan(self.app, self.config, self.storage_root)
            setup.write_json(self.path, report, private=True)
        except (OSError, ValueError, setup.SetupError) as error:
            with self.lock:
                self.error = 'L’analyse du disque a échoué (' + type(error).__name__ + ').'
        finally:
            with self.lock:
                self.running = False

    def status(self):
        report = self.read()
        if (report is None or time.time() - report.get('scanned_at', 0) > MAX_AGE) and not self.error:
            try:
                self.start()
            except setup.SetupError:
                pass
        with self.lock:
            running, error = self.running, self.error
        roots, base = locations(self.app, self.config)
        paths = [roots['data'], roots['application']]
        recovery = recovery_folder(base or roots['application'].parent)
        if recovery.is_dir():
            paths.append(recovery)
        live = disks(paths, roots['data'], self.storage_root)
        if report:
            for disk in report.get('disks', []):
                if disk['id'] in live:
                    disk.update({key: live[disk['id']][key] for key in ('total', 'used', 'free')})
        return {'schema': SCHEMA, 'scanning': running, 'error': error, 'report': report,
                'disks': list(live.values()) if report is None else report['disks']}
