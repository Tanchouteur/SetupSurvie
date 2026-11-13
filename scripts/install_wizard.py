#!/usr/bin/env python3
"""Resumable first installation into an independent Windows application folder.

Never imports or executes Python from a supplied kit in this process.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

import setup
from pilot import durable
from delivery_paths import destination


WEB_PORTS = (3000, 8080, 8081, 8443, 8444, 8445)
HOST_PORTS = (11435, 11436)


def port_busy(port):
    with socket.socket() as connection:
        if os.name == 'nt':
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            connection.bind(('0.0.0.0', port))
        except OSError:
            return True
        return False


def check_installation_ports(work):
    """Fail before copies/downloads, allowing only services owned by a resumed setup."""
    busy = {port for port in (*WEB_PORTS, *HOST_PORTS) if port_busy(port)}
    if not busy:
        return
    app = setup.Installation(work)
    owned = set()
    if app.settings_path.is_file():
        config = app.load()
        if busy.intersection(WEB_PORTS):
            raw = app.compose(config, 'ps', '--format', 'json', capture=True)
            # Compose supports a JSON array or one JSON object per line.
            services = json.loads(raw) if raw.strip().startswith('[') else [json.loads(line) for line in raw.splitlines() if line.strip()]
            for service in services:
                if service.get('State') == 'running':
                    owned.update(int(p['PublishedPort']) for p in (service.get('Publishers') or []) if p.get('PublishedPort'))
        native = app.work/'native-ollama.json'
        if 11435 in busy and native.is_file() and app.native_owned(json.loads(native.read_text(encoding='utf-8'))):
            owned.add(11435)
        controller = app.work/'control-process.json'
        if 11436 in busy and controller.is_file():
            import discovery
            marker = json.loads(controller.read_text(encoding='utf-8'))
            if marker.get('identity') and discovery.identity(marker['pid']) == marker['identity']:
                owned.add(11436)
    conflict = sorted(busy-owned)
    if conflict:
        raise setup.SetupError('Une autre installation ou application utilise déjà les ports '+', '.join(map(str, conflict))+'. '
            'Si SetupSurvie fonctionne déjà, ouvrez http://localhost:8080 et utilisez sa procédure de mise à jour. '
            'Pour une nouvelle installation, arrêtez d’abord l’ancienne avec son raccourci Arrêter SetupSurvie. '
            'Aucun service existant arrêté et aucun téléchargement lancé.')


@contextmanager
def installation_lock(base):
    """OS lock released on process death; the empty lock file can safely remain."""
    path = destination(base, '.installation.lock')
    with path.open('a+b') as stream:
        # Windows forbids reading another process's locked byte before we can
        # report contention. Inspect the length without reading that byte.
        stream.seek(0, os.SEEK_END)
        if not stream.tell():
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise setup.SetupError('Une installation est déjà en cours dans ce dossier.')
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def source_records(kit):
    if kit:
        import kit_audit
        from pilot_kit import checked_entries
        manifest = json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
        print('Contrôle complet du kit, avant installation…', flush=True)
        entries = checked_entries(kit, manifest)
        kit_audit.validate(kit, manifest)
        return [(entry, path) for entry, path in entries
                if entry['path'].startswith(('app/', 'payload/'))], manifest
    from pilot_update import FOLDERS, FILES
    paths = [p for name in (*FOLDERS, 'vendor/discovery')
             for p in (setup.ROOT/name).rglob('*')
             if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    install_files = (*FILES, 'Installer-SetupSurvie.cmd', 'Mettre-a-jour-SetupSurvie.cmd', '1-Preparer-le-PC.cmd', '2-Installer-SetupSurvie.cmd')
    paths.extend(setup.ROOT/name for name in install_files if (setup.ROOT/name).is_file())
    return [({'path': 'app/'+p.relative_to(setup.ROOT).as_posix(),
              'bytes': p.stat().st_size, 'sha256': setup.file_hash(p)}, p) for p in sorted(paths)], None


def copy_checked(source, target, entry):
    if target.is_file() and target.stat().st_size == entry['bytes'] and setup.file_hash(target) == entry['sha256']:
        durable.sync_file(target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = destination(target.parent, target.name+'.installation-part')
    shutil.copyfile(source, partial)
    if partial.stat().st_size != entry['bytes'] or setup.file_hash(partial) != entry['sha256']:
        raise setup.SetupError('Copie interrompue ou source modifiée : '+entry['path'])
    durable.sync_file(partial)
    shutil.copymode(source, partial)
    durable.publish(partial,target)


def execute(arguments):
    result = subprocess.run([sys.executable, '-X', 'utf8', *map(str, arguments)], check=False)
    if result.returncode:
        raise setup.SetupError('Étape interrompue. Les fichiers copiés sont conservés ; reprenez avec --resume.')


def install(base, kit=None, *, resume=False, startup=True, lan_host=None, execute_step=execute):
    base = Path(base).expanduser().absolute()
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise setup.SetupError('Choisissez un dossier sans lien symbolique.')
    base = setup.safe_path(base)
    if base == Path(base.anchor) or base == setup.ROOT or base in setup.ROOT.parents or base.is_relative_to(setup.ROOT):
        raise setup.SetupError('Choisissez un dossier dédié hors du dépôt, pas la racine du disque.')
    kit = setup.safe_path(kit) if kit else None
    if kit and (kit == base or kit.is_relative_to(base) or base.is_relative_to(kit)):
        raise setup.SetupError('Le kit et l’installation doivent rester séparés.')
    durable.mkdir(base)
    with installation_lock(base):
        journal = destination(base, '.installation.json')
        state = json.loads(journal.read_text(encoding='utf-8')) if journal.exists() else None
        if state and state.get('status') not in ('copying', 'configuring', 'complete'):
            raise setup.SetupError('Journal d’installation non reconnu. Aucune donnée remplacée.')
        if state and state.get('status') == 'complete':
            raise setup.SetupError('Installation déjà terminée. Utilisez les raccourcis ou la mise à jour, pas une réinstallation.')
        if state and not resume:
            raise setup.SetupError('Installation interrompue détectée. Relancez avec --resume pour la reprendre explicitement.')
        if resume and not state:
            raise setup.SetupError('Aucune installation interrompue à reprendre dans ce dossier.')
        application = destination(base, 'application')
        data = destination(base, 'donnees')
        work = destination(base, 'prive')
        if not state and any(p.exists() and (not p.is_dir() or any(p.iterdir())) for p in (application, data, work)):
            raise setup.SetupError('Dossiers déjà occupés. Aucune donnée remplacée ; choisissez une nouvelle destination.')
        lan_host = setup.lan_host(lan_host) if lan_host else None
        options = {'base': str(base), 'kit': str(kit) if kit else None, 'startup': startup, 'lan_host': lan_host}
        if state and (state.get('schema') != 1 or state.get('options') != options):
            raise setup.SetupError('Reprise avec des options différentes refusée. Réutilisez le même dossier, kit et choix de démarrage.')
        check_installation_ports(work)
        records, manifest = source_records(kit)
        signature = hashlib.sha256(json.dumps([e for e, _ in records], sort_keys=True).encode()).hexdigest()
        if state and state.get('source') != signature:
            raise setup.SetupError('Le logiciel ou le kit source a changé depuis l’interruption. Reprenez avec la source initiale.')
        # Every destination is guarded, even for manifest-controlled paths.
        targets = [(entry, source, destination(application if entry['path'].startswith('app/') else data,
                    entry['path'].split('/', 1)[1])) for entry, source in records]
        copying = not state or state['status'] == 'copying'
        remaining = sum(e['bytes'] for e, _, target in targets if not target.is_file() or target.stat().st_size != e['bytes']) if copying else 0
        # Reserve room for Docker images, caches and a default model in online mode.
        reserve = 22_000_000_000 if kit or not copying else 60_000_000_000
        if shutil.disk_usage(base).free < remaining+reserve:
            raise setup.SetupError(f'Espace insuffisant : au moins {(remaining+reserve)/1e9:.1f} Go libres requis sur le disque de données. Vérifiez aussi le disque Docker.')
        if not state:
            state = {'schema': 1, 'options': options, 'source': signature, 'status': 'copying'}
            setup.write_json(journal, state, private=True)
        # Never recopy the initial payload after services have started: users may
        # already have added documents or changed metadata during a failed verify.
        if state['status'] == 'copying':
            for number, (entry, source, target) in enumerate(targets, 1):
                copy_checked(source, target, entry)
                if number % 100 == 0 or number == len(targets):
                    print(f'Copie contrôlée : {number}/{len(targets)} fichiers', flush=True)
            durable.sync_tree(application,sync_files=False)
            if data.exists():durable.sync_tree(data,sync_files=False)
            state['status'] = 'configuring'
            setup.write_json(journal, state, private=True)
        launcher = application/'scripts/setup.py'
        common = [launcher, '--work-dir', work]
        startup_option = [] if startup else ['--no-startup']
        network_options = ['--lan', '--lan-host', lan_host] if lan_host else []
        execute_step([*common, 'init', '--target', 'windows', '--data-dir', data, *network_options])
        # Required by the existing update path for both installation modes.
        config_path = work/'settings.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config['app_dir'] = application.as_posix()
        setup.write_json(config_path, config, private=True)
        if kit:
            execute_step([*common, 'import-images', kit/'images.tar'])
        # Existing install orchestration validates services and installs shortcuts;
        # it can be repeated after an interruption without resetting the account.
        arguments = [*common, 'install', '--target', 'windows', '--data-dir', data, *startup_option, *network_options]
        if kit:
            arguments.append('--offline')
        else:
            arguments.extend(['--content-pack', 'survival'])
        execute_step(arguments)
        if not kit:
            profiles = json.loads((setup.ROOT/'deploy/model-profiles.json').read_text())['profiles']
            for model in sorted({p['model'] for p in profiles if p.get('category') == 'recommended'} - {setup.VERSIONS['default_model']}):
                print('Préparation du modèle conseillé : '+model, flush=True)
                execute_step([*common, 'pull-model', model])
        state['status'] = 'complete'
        setup.write_json(journal, state, private=True)
        print('Installation terminée. Portail : http://localhost:8080\n'
              'Identifiants : '+str(work/'identifiants.txt')+'\n'
              'Pour les autres appareils : configurez le réseau privé avec le guide Windows.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-dir', required=True)
    parser.add_argument('--kit')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--check', action='store_true', help='Contrôler les conflits sans copie, installation ou téléchargement.')
    parser.add_argument('--no-startup', action='store_true')
    parser.add_argument('--lan-host', type=setup.lan_host)
    args = parser.parse_args()
    if os.name != 'nt':
        raise setup.SetupError('Ce lanceur concerne Windows. Utilisez scripts/install.sh sur Linux préparé.')
    if args.check:
        check_installation_ports(setup.safe_path(args.base_dir)/'prive')
        print('Ports disponibles ou appartenant à cette installation.')
        return
    install(args.base_dir, args.kit, resume=args.resume, startup=not args.no_startup, lan_host=args.lan_host)


if __name__ == '__main__':
    try:
        main()
    except (setup.SetupError, OSError, ValueError, KeyError) as exc:
        print('ERREUR :', exc, file=sys.stderr)
        sys.exit(1)
