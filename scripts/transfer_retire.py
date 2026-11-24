"""Retire the old Linux application and data after a successful local transfer."""
import json
import os
from pathlib import Path
import re
import shutil
import sys

import setup
import transfer
from delivery_paths import locked
from pilot import durable

ROLES = ('application', 'data')


def overlaps(first, second):
    return first.is_relative_to(second) or second.is_relative_to(first)


def mounted_paths():
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        field = line.split()[4]
        yield Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), field))


def docker_paths(source_project):
    host = os.environ.get('DOCKER_HOST')
    if not host:
        context = json.loads(setup.run(['docker', 'context', 'inspect'], capture=True))
        host = context[0]['Endpoints']['docker']['Host']
    if not host.startswith('unix:///'):
        raise setup.SetupError('Le retrait exige le moteur Docker local, via son socket Unix.')
    root = setup.run(['docker', 'info', '--format', '{{.DockerRootDir}}'], capture=True)
    if not Path(root).is_absolute():
        raise setup.SetupError('Stockage Docker impossible à identifier.')
    yield Path(root).resolve()
    ids = setup.run(['docker', 'ps', '-aq'], capture=True).split()
    if ids:
        for container in json.loads(setup.run(['docker', 'inspect', *ids], capture=True)):
            config = container['Config']
            if (config.get('Labels') or {}).get('com.docker.compose.project') == source_project:
                raise setup.SetupError('Des conteneurs de l’ancienne installation existent encore.')
            for mount in container.get('Mounts', []):
                if mount['Type'] == 'bind':
                    yield Path(mount['Source']).resolve()


def check_source_files(journal, paths):
    current = transfer.inventory(paths)
    expected = [record for record in journal['inventory']['files']
                if record['path'].split('/', 1)[0] in ROLES]
    if (not transfer.matches_frozen_inventory(current['files'], expected)
            or current['ollama_links'] != journal['inventory'].get('ollama_links', {})):
        raise setup.SetupError('L’ancienne installation a changé depuis la copie. Retrait refusé.')


def safe_directory(path, dest, private):
    if (not path.is_absolute() or path.resolve() != path or path == Path.home().resolve()
            or overlaps(path, dest) or overlaps(path, private) or len(path.parts) < 4):
        raise setup.SetupError('Dossier source ambigu ou commun aux deux installations.')


def different_filesystem(parent, dest):
    return parent.stat().st_dev != dest.stat().st_dev


def entry_identity(path):
    if path.is_symlink() or not path.is_dir():
        raise setup.SetupError('Un dossier prévu pour le retrait a changé.')
    stat = path.stat()
    return [stat.st_dev, stat.st_ino]


def check_destination(dest, app, config):
    if (Path(config['data_dir']).resolve() != dest/'data'
            or Path(config['app_dir']).resolve() != dest/'application'):
        raise setup.SetupError('Les réglages de la copie ne désignent pas ce disque.')
    transfer.validate_mounts(app, config, allow_ollama=True, app_root=dest/'application')
    health = app.request('http://127.0.0.1:8080/api/health', timeout=8)
    if not health.get('ok') or health.get('degraded_features'):
        raise setup.SetupError('Le portail de la copie doit fonctionner avant le retrait.')
    script = (dest/'application/scripts/transfer_document_probe.py').read_text(encoding='utf-8')
    probe = json.loads(app.compose(config, 'exec', '-T', 'pilot', 'python', '-c', script,
                                   capture=True, timeout=120))
    if probe.get('search') not in ('passed', 'not_tested_no_indexed_guide'):
        raise setup.SetupError('La recherche documentaire de la copie ne répond pas.')


def retire(dest, confirmation=None):
    if sys.platform != 'linux' or not shutil.rmtree.avoids_symlink_attacks:
        raise setup.SetupError('Ce retrait est disponible sur Linux.')
    dest = setup.safe_path(dest)
    with locked(dest/'operation.lock'):
        journal = transfer.read(dest/'transfer.json')
        identifier = journal.get('id', '')
        if (journal.get('kind') != transfer.KIND or journal.get('schema') != 1
                or journal.get('phase') != 'active' or journal.get('target') != 'linux'
                or journal.get('destination') != str(dest) or not re.fullmatch('[a-f0-9]{32}', identifier)
                or not journal.get('checks', {}).get('mounts')):
            raise setup.SetupError('Activez et vérifiez d’abord la copie Linux sur le nouveau disque.')
        if confirmation is not None and confirmation != identifier:
            raise setup.SetupError('Le code de confirmation ne correspond pas à ce transfert.')
        private = Path(journal['source']['private'])
        if not private.is_dir() or private.resolve() != private or overlaps(private, dest):
            raise setup.SetupError('Réglages privés de la source absents ou ambigus.')
        app = setup.Installation(dest/'private')
        with locked(private/'update.lock'), locked(private/'transfer.lock'), locked(app.work/'update.lock'):
            retire_locked(dest, journal, private, app, confirmation is not None)


def retire_locked(dest, journal, private, app, confirmed):
    identifier = journal['id']
    progress = journal.get('source_retirement')
    if progress and all(entry['stage'] == 'removed' for entry in progress.values()):
        if confirmed:transfer.export_report(dest, journal)
        print('Ancienne application et ancien dossier de données déjà supprimés.')
        return
    if transfer.read(private/'transfer-guard.json').get('id') != identifier:
        raise setup.SetupError('La source a été réactivée ou appartient à un autre transfert.')
    source = setup.Installation(private).load()
    paths = {role: Path(journal['source'][role]) for role in ROLES}
    if any(paths[role] != Path(source[key]).resolve()
           for role, key in zip(ROLES, ('app_dir', 'data_dir'))):
        raise setup.SetupError('Les chemins de l’ancienne installation ont changé.')
    retired = {role: path.with_name(f'.setupsurvie-retrait-{identifier}-{role}')
               for role, path in paths.items()}
    for path in (*paths.values(), *retired.values()):
        safe_directory(path, dest, private)
        if not different_filesystem(path.parent, dest):
            raise setup.SetupError('La copie doit être sur un autre système de fichiers.')
    if overlaps(paths['application'], paths['data']):
        raise setup.SetupError('Les répertoires source se chevauchent.')
    for protected in docker_paths(source['project']):
        if any(overlaps(path, protected) for path in (*paths.values(), *retired.values())):
            raise setup.SetupError('Un chemin de l’ancienne installation est utilisé par Docker.')
    for mount in mounted_paths():
        if any(mount.is_relative_to(path) for path in (*paths.values(), *retired.values())):
            raise setup.SetupError('Un système de fichiers est monté dans les dossiers à retirer.')
    check_destination(dest, app, app.load())
    if progress is None:
        check_source_files(journal, paths)
        if any(path.exists() for path in retired.values()):
            raise setup.SetupError('Un dossier de retrait existe déjà.')
        progress = {role: {'identity': entry_identity(paths[role]), 'stage': 'original'} for role in ROLES}
    for path in paths.values():
        print('Dossier concerné :', path)
    if not confirmed:
        print('Pour confirmer la suppression, relancez avec --confirm-id', identifier)
        return
    journal['source_retirement'] = progress
    transfer.save(dest, journal)
    for role, entry in progress.items():
        original, staging = paths[role], retired[role]
        if entry['stage'] == 'original':
            if original.exists() and not staging.exists():
                if entry_identity(original) != entry['identity']:
                    raise setup.SetupError('L’identité du dossier source a changé.')
                os.rename(original, staging)
                durable.sync_directory(staging.parent)
            if original.exists() or entry_identity(staging) != entry['identity']:
                raise setup.SetupError('L’identité du dossier à retirer a changé.')
            entry['stage'] = 'quarantined'
            transfer.save(dest, journal)
        if entry['stage'] == 'quarantined':
            if original.exists():
                raise setup.SetupError('Un nouveau dossier source est apparu pendant le retrait.')
            if staging.exists():
                if entry_identity(staging) != entry['identity']:
                    raise setup.SetupError('L’identité du dossier à retirer a changé.')
                shutil.rmtree(staging)
            durable.sync_directory(staging.parent)
            entry['stage'] = 'removed'
            transfer.save(dest, journal)
    transfer.export_report(dest, journal)
    print('Ancienne application et anciennes données supprimées. Les réglages et le moteur Docker sont conservés.')
