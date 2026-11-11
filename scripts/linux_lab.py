#!/usr/bin/env python3
"""Isolated, size-limited Podman lab for this Linux PC; no system reconfiguration."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import setup

BASE = Path('/var/mnt/data/AI/SetupSurvie')
IMAGE = BASE / 'storage.img'
# Decimal bytes, leaving room below the user's 600 GB ceiling for outer metadata.
CAPACITY = 590_000_000_000
MOUNT = Path('/run/media') / getpass.getuser() / 'SetupSurvie'
NAMES = ('pilot', 'open-webui', 'portal', 'kiwix', 'ollama')
PREFIX = 'setupsurvie-lab-'


def require_inference():
    checked_mount()
    if (MOUNT / 'private/inference-paused.json').exists():
        raise RuntimeError('Calcul IA suspendu (mode jeu). Reprise uniquement sur demande explicite : lab.sh resume-inference.')


def command(args, *, capture=False, env=None, check=True):
    return subprocess.run([str(x) for x in args], check=check, text=True,
                          capture_output=capture, env=env)


def loop_device():
    result = command(['losetup', '-j', IMAGE], capture=True)
    lines = result.stdout.strip().splitlines()
    if len(lines) > 1:
        raise RuntimeError('Plusieurs périphériques pour cette image : arrêt par précaution.')
    return lines[0].split(':', 1)[0] if lines else None


def checked_mount():
    """Fail closed: never silently write into the mountpoint on the system SSD."""
    if not IMAGE.is_file() or IMAGE.is_symlink() or IMAGE.stat().st_size != CAPACITY:
        raise RuntimeError('Image absente ou taille inattendue ; aucun téléchargement autorisé.')
    device = loop_device()
    result = command(['findmnt', '-rn', '-o', 'SOURCE,TARGET', '--mountpoint', MOUNT],
                     capture=True, check=False)
    if not device or result.returncode or result.stdout.strip() != f'{device} {MOUNT}':
        raise RuntimeError('Le volume dédié doit être monté : lancez mount.')
    backing = Path('/sys/class/block') / Path(device).name / 'loop/backing_file'
    if Path(backing.read_text().strip()).resolve() != IMAGE.resolve():
        raise RuntimeError('Le volume ne correspond pas au fichier du SSD de 4 To.')
    if os.stat(IMAGE).st_dev != os.stat('/var/mnt/data').st_dev:
        raise RuntimeError('Le fichier de stockage doit rester sur le SSD de 4 To.')


def mount():
    if not IMAGE.exists():
        if not os.path.ismount('/var/mnt/data'):
            raise RuntimeError('SSD de données non monté.')
        BASE.mkdir(mode=0o700, parents=True, exist_ok=True)
        IMAGE.touch(mode=0o600, exist_ok=False)
        command(['chattr', '+C', IMAGE])
        command(['truncate', '-s', str(CAPACITY), IMAGE])
        command(['mkfs.ext4', '-q', '-L', 'SetupSurvie', '-m', '0', '-T', 'largefile4',
                 '-E', f'root_owner={os.getuid()}:{os.getgid()},lazy_itable_init=1,lazy_journal_init=1', IMAGE])
    if IMAGE.stat().st_size != CAPACITY or IMAGE.is_symlink():
        raise RuntimeError('Image existante de taille inattendue ; aucune modification.')
    device = loop_device()
    if not device:
        result = command(['udisksctl', 'loop-setup', '--no-user-interaction', '--file', IMAGE], capture=True)
        match = re.search(r'/dev/loop\d+', result.stdout)
        if not match:
            raise RuntimeError('Périphérique loop introuvable.')
        device = match.group()
    if not os.path.ismount(MOUNT):
        command(['udisksctl', 'mount', '--no-user-interaction', '--block-device', device])
    checked_mount()
    for name in ('containers', 'tmp', 'private', 'logs', 'results', 'data', 'runtime'):
        (MOUNT / name).mkdir(exist_ok=True)
    (MOUNT / 'private').chmod(0o700)


def podman(*args, capture=False, check=True):
    checked_mount()
    if args and args[0] in ('start', 'restart', 'run'):
        values = [str(value) for value in args]
        if PREFIX + 'ollama' in values or any('/ollama:' in value for value in values):
            require_inference()
    env = os.environ.copy()
    env.update(TMPDIR=str(MOUNT / 'tmp'), REGISTRY_AUTH_FILE=str(MOUNT / 'private/auth.json'))
    runtime = Path('/run/user') / str(os.getuid()) / 'setupsurvie'
    return command(['podman', '--root', MOUNT / 'containers', '--runroot', runtime / 'storage',
                    '--tmpdir', runtime / 'libpod', '--events-backend=none', *args],
                   env=env, capture=capture, check=check)


def configuration():
    checked_mount()
    app = setup.Installation(MOUNT / 'private')
    c = app.init('linux', MOUNT / 'data')
    for name in ('portal', 'deploy', 'pilot'):
        shutil.copytree(setup.ROOT / name, MOUNT / 'runtime' / name, dirs_exist_ok=True)
    return app, c


def reference(name):
    value = setup.VERSIONS['images'][name]
    return 'docker.io/' + value if '/' not in value.split(':')[0] else value


def webui_env(c):
    # Application environment follows the existing Compose file, without adding a YAML dependency.
    env = {'OLLAMA_BASE_URL': 'http://ollama:11434', 'ENABLE_OPENAI_API': 'false',
           'ENABLE_WEB_SEARCH': 'false', 'ENABLE_IMAGE_GENERATION': 'false',
           'WEBUI_SECRET_KEY': c['secret'], 'WEBUI_ADMIN_EMAIL': c['admin_email'],
           'WEBUI_ADMIN_PASSWORD': c['admin_password'], 'WEBUI_ADMIN_NAME': 'Administration',
           'ENABLE_SIGNUP': 'false', 'DEFAULT_LOCALE': 'fr-FR', 'DEFAULT_MODELS': 'survie-rapide',
           'JWT_EXPIRES_IN': '30d',
           'ENABLE_TITLE_GENERATION': 'false', 'ENABLE_TAGS_GENERATION': 'false',
           'ENABLE_FOLLOW_UP_GENERATION': 'false', 'ENABLE_AUTOCOMPLETE_GENERATION': 'false',
           'ENABLE_SEARCH_QUERY_GENERATION': 'false', 'ENABLE_RETRIEVAL_QUERY_GENERATION': 'false',
           'ENABLE_CALENDAR': 'false', 'ENABLE_AUTOMATIONS': 'false',
           'DEFAULT_USER_ROLE': 'user', 'OFFLINE_MODE': 'true', 'HF_HUB_OFFLINE': '1',
           'AUDIO_STT_ENGINE': '',
           'WHISPER_MODEL': '/app/backend/data/cache/whisper/faster-whisper-small',
           'WHISPER_MODEL_AUTO_UPDATE': 'false', 'WHISPER_COMPUTE_TYPE': 'int8',
           'TIKTOKEN_CACHE_DIR': '/app/backend/data/cache/tiktoken', 'RAG_EMBEDDING_ENGINE': '',
           'RAG_EMBEDDING_MODEL': '/app/backend/data/cache/embedding/bge-m3',
           'RAG_EMBEDDING_MODEL_AUTO_UPDATE': 'false', 'RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE': 'false',
           'RAG_RERANKING_MODEL_AUTO_UPDATE': 'false', 'ENABLE_VERSION_UPDATE_CHECK': 'false',
           'ENABLE_PERSISTENT_CONFIG': 'false', 'VECTOR_DB': 'chroma'}
    env.update({key:'false' for key in ('USER_PERMISSIONS_FEATURES_CALENDAR','USER_PERMISSIONS_FEATURES_AUTOMATIONS','USER_PERMISSIONS_FEATURES_CODE_INTERPRETER','USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS')})
    return env


def run_container(name, image, args, env=None, *, detach=True,command_args=()):
    envpath = MOUNT / 'private' / f'{name}.env'
    envpath.write_text(''.join(f'{k}={v}\n' for k, v in (env or {}).items()))
    envpath.chmod(0o600)
    options = ['run', '--pull=never', '--name', PREFIX + name, '--label', 'project=setupsurvie-lab',
               '--security-opt=label=disable', '--log-driver=k8s-file', '--log-opt=max-size=10mb',
               f'--log-opt=path={MOUNT}/logs/{name}.log', '--env-file', envpath,
               '--pids-limit=1024']
    options += ['-d'] if detach else ['--rm']
    return podman(*options, *args, image,*command_args,capture=detach)


def up():
    _, c = configuration()
    tls_hosts=list(dict.fromkeys(['localhost',c.get('lan_host','localhost')]+([c.get('discovery_name','survie')+'.local'] if c['bind']=='0.0.0.0' else [])))
    if podman('network', 'exists', 'setupsurvie-lab', check=False).returncode:
        podman('network', 'create', 'setupsurvie-lab', capture=True)
    specifications = {
        'ollama': (['--device', 'nvidia.com/gpu=all', '--network', 'setupsurvie-lab',
                    '--network-alias', 'ollama', '-p', '127.0.0.1:11435:11434',
                    '-v', f'{MOUNT}/data/models:/root/.ollama/models', '--memory=22g', '--memory-swap=24g'],
                   {'OLLAMA_HOST': '0.0.0.0:11434', 'OLLAMA_NO_CLOUD': '1',
                    'OLLAMA_CONTEXT_LENGTH': '4096', 'OLLAMA_NUM_PARALLEL': '1',
                    'OLLAMA_MAX_LOADED_MODELS': '1'}),
        'open-webui': (['--network', 'setupsurvie-lab', '--network-alias', 'open-webui', '-p', f'{c["bind"]}:3000:8080',
                        '-v', f'{MOUNT}/data/state/openwebui:/app/backend/data', '--memory=8g'], webui_env(c)),
        'portal': (['--network', 'setupsurvie-lab', '-p', f'{c["bind"]}:8080:8080',
                    '-p', f'{c["bind"]}:8443:8443', '-p', f'{c["bind"]}:8444:8444', '-p', f'{c["bind"]}:8445:8445',
                    '-v', f'{MOUNT}/runtime/deploy/Caddyfile:/etc/caddy/Caddyfile:ro',
                    '-v', f'{MOUNT}/runtime/portal:/srv/portal:ro',
                    '-v', f'{MOUNT}/data/catalog:/srv/catalog:ro',
                    '-v', f'{MOUNT}/data/library/guides:/srv/guides:ro',
                    '-v', f'{MOUNT}/data/state/caddy:/data', '--memory=256m'],
                   {'TLS_FALLBACK_HOST':c.get('lan_host','localhost'),**{key:', '.join(f'https://{host}:{port}' for host in tls_hosts)
                    for key,port in [('TLS_PORTAL_ADDRESSES',8443),('TLS_WEBUI_ADDRESSES',8444),('TLS_KIWIX_ADDRESSES',8445)]}}),
        'kiwix': (['--network', 'setupsurvie-lab', '--network-alias', 'kiwix', '-p', f'{c["bind"]}:8081:8080',
                   '-v', f'{MOUNT}/runtime/deploy/kiwix-entrypoint.sh:/config/kiwix-entrypoint.sh:ro',
                   '-v', f'{MOUNT}/data/library/zim:/data:ro', '--memory=1g',
                   '--entrypoint', '/bin/sh'], {}),
        'pilot': (['--network', 'setupsurvie-lab', '--network-alias', 'pilot', '--workdir', '/srv',
                   '-v', f'{MOUNT}/runtime/pilot:/srv/pilot:ro',
                   '-v', f'{MOUNT}/runtime/deploy/assistant-system.fr.txt:/srv/system.fr.txt:ro',
                   '-v', f'{MOUNT}/runtime/deploy/model-profiles.json:/srv/model-profiles.json:ro',
                   '-v', f'{MOUNT}/data/state/pilot:/pilot-data',
                   '-v', f'{MOUNT}/data/state/openwebui:/webui-data:ro',
                   '-v', f'{MOUNT}/data/library/zim:/zim:ro',
                   '-v', f'{MOUNT}/data/models:/models:ro',
                   '-v', f'{MOUNT}/data/catalog:/catalog:ro',
                   '-v', f'{MOUNT}/data/library/guides:/guides', '--memory=2g'],
                  {'PILOT_STATE_DIR':'/pilot-data','WEBUI_DB_PATH':'/webui-data/webui.db',
                   'PILOT_CONTROL_URL':'http://host.containers.internal:11436','PILOT_CONTROL_TOKEN':setup.control_key(c),
                   'WEBUI_SECRET_KEY':c['secret'],'WEBUI_URL':'http://open-webui:8080',
                   'OLLAMA_URL':'http://ollama:11434','KIWIX_URL':'http://kiwix:8080',
                   'GUIDES_DIR':'/guides','ASSISTANT_POLICY':'/srv/system.fr.txt'}),
    }
    for name in ('ollama', 'kiwix', 'open-webui', 'pilot', 'portal'):
        if name == 'ollama' and (MOUNT / 'private/inference-paused.json').exists():
            print('Ollama reste arrêté : mode jeu actif.', flush=True)
            continue
        exists = podman('container', 'exists', PREFIX + name, check=False).returncode == 0
        if exists:
            podman('start', PREFIX + name, capture=True)
        else:
            args, env = specifications[name]
            if name == 'kiwix':
                # Supply an explicit command instead of the upstream image's CMD.
                envpath = MOUNT / 'private' / f'{name}.env'
                envpath.write_text('')
                envpath.chmod(0o600)
                podman('run', '-d', '--pull=never', '--name', PREFIX + name,
                       '--label', 'project=setupsurvie-lab', '--security-opt=label=disable',
                       '--log-driver=k8s-file', '--log-opt=max-size=10mb',
                       f'--log-opt=path={MOUNT}/logs/{name}.log', *args, reference(name),
                       '/config/kiwix-entrypoint.sh', capture=True)
            elif name == 'pilot':
                envpath=MOUNT/'private/pilot.env'
                envpath.write_text(''.join(f'{k}={v}\n' for k,v in env.items()));envpath.chmod(0o600)
                podman('run','-d','--pull=never','--name',PREFIX+name,'--label','project=setupsurvie-lab',
                       '--security-opt=label=disable','--log-driver=k8s-file','--log-opt=max-size=10mb',
                       f'--log-opt=path={MOUNT}/logs/pilot.log','--env-file',envpath,*args,
                       '--entrypoint','python',reference('open-webui'),'-m','uvicorn','pilot.app:app',
                       '--host','0.0.0.0','--port','8000',capture=True)
            else:
                run_container(name, reference(name), args, env)
        print(f'Démarré : {name}', flush=True)
    import control
    control.start(setup.Installation(MOUNT/'private'),c,'lab')
    if c['bind']=='0.0.0.0':
        import discovery
        try:discovery.start(setup.Installation(MOUNT/'private'),c,MOUNT/'tools/discovery-wheels')
        except (OSError,ValueError,setup.SetupError) as exc:print('Annonce du nom local indisponible :',exc)


def prepare():
    _, c = configuration()
    marker = MOUNT / 'data/state/openwebui/cache/embedding-ready.json'
    if marker.exists():
        if json.loads(marker.read_text()) != setup.VERSIONS['embedding']:
            raise RuntimeError('Révision embeddings différente ; réindexation nécessaire.')
        print('BGE-M3 déjà préparé.')
        return
    env = webui_env(c)
    env.update(HF_HUB_OFFLINE='0', OFFLINE_MODE='false', HF_HUB_DISABLE_XET='1')
    envpath = MOUNT / 'private/prepare.env'
    envpath.write_text(''.join(f'{k}={v}\n' for k, v in env.items()))
    envpath.chmod(0o600)
    podman('run', '--rm', '--pull=never', '--name', PREFIX + 'prepare',
           '--label', 'project=setupsurvie-lab', '--security-opt=label=disable',
           '--log-driver=none', '--memory=8g', '--env-file', envpath,
           '-v', f'{MOUNT}/data/state/openwebui:/app/backend/data',
           '--entrypoint', 'python', reference('open-webui'), '-c', setup.PREPARE_EMBEDDING)
    setup.write_json(marker, setup.VERSIONS['embedding'])


def down(remove=False):
    import control
    control.stop(setup.Installation(MOUNT/'private'))
    import discovery
    discovery.stop(setup.Installation(MOUNT/'private'))
    # Stop only this project's explicit background download, preserving its checkpoint.
    command(['systemctl', '--user', 'stop', 'setupsurvie-corpus.service'], capture=True, check=False)
    for name in (*NAMES, 'prepare', 'offline', 'speech-prepare', 'speech-offline'):
        if podman('container', 'exists', PREFIX + name, check=False).returncode == 0:
            podman('stop', '-t', '30', PREFIX + name, capture=True)
            if remove:
                podman('rm', PREFIX + name, capture=True)


def download_corpus():
    checked_mount()
    active = command(['systemctl', '--user', 'is-active', '--quiet', 'setupsurvie-corpus.service'],
                     capture=True, check=False)
    if active.returncode == 0:
        print('Téléchargement documentaire déjà en cours.')
        return
    command(['systemd-run', '--user', '--unit=setupsurvie-corpus', '--collect',
             '--description=SetupSurvie - corpus hors ligne',
             f'--property=WorkingDirectory={setup.ROOT}',
             f'--property=StandardOutput=append:{MOUNT}/logs/corpus-download.log',
             '--property=StandardError=inherit', '--property=Nice=10',
             sys.executable, str(setup.ROOT / 'scripts/lab_corpus.py')])
    print('Transfert lancé. Suivi : lab.sh jobs ; arrêt avec conservation : lab.sh down.')


def prepare_speech():
    configuration()
    speech = setup.VERSIONS['speech']
    marker = MOUNT / 'data/state/openwebui/cache/whisper/ready.json'
    if marker.exists() and json.loads(marker.read_text()) == speech:
        print('Dictée déjà préparée.')
        return
    code = """from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel
snapshot_download(repo_id=REPO, revision=REV,
    local_dir='/app/backend/data/cache/whisper/faster-whisper-small',
    allow_patterns=['*.json','*.txt','model.bin'])
WhisperModel('/app/backend/data/cache/whisper/faster-whisper-small',
    device='cpu',compute_type='int8',local_files_only=True)
""".replace('REPO', repr(speech['repository'])).replace('REV', repr(speech['revision']))
    podman('run', '--rm', '--pull=never', '--name', PREFIX + 'speech-prepare',
           '--security-opt=label=disable', '--log-driver=none', '--memory=4g',
           '-e', 'HF_HUB_OFFLINE=0', '-e', 'HF_HUB_DISABLE_XET=1',
           '-v', f'{MOUNT}/data/state/openwebui:/app/backend/data',
           '--entrypoint', 'python', reference('open-webui'), '-c', code)
    setup.write_json(marker, speech)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('mount', 'pull', 'prepare', 'up', 'down', 'status',
                                         'pull-model', 'record', 'unmount', 'clean', 'prepare-speech',
                                         'download-corpus', 'jobs', 'pause-inference', 'resume-inference', 'network'))
    parser.add_argument('--erase-data', action='store_true', help='Supprime définitivement le volume et toutes ses données')
    parser.add_argument('--lan-host',type=setup.lan_host,help='network : adresse IPv4 du PC sur le réseau privé ; sans option, retour au PC seul')
    parser.add_argument('--name',help='network : nom local court, par exemple survie-marc')
    args = parser.parse_args()
    if args.action == 'mount':
        mount()
        configuration()
    elif args.action in ('unmount', 'clean'):
        if args.action == 'clean' and not args.erase_data:
            parser.error('clean exige --erase-data : cette action efface modèles, documents et comptes')
        if os.path.ismount(MOUNT):
            checked_mount()
            down(remove=True)
            command(['sync', '-f', MOUNT])
            command(['udisksctl', 'unmount', '--no-user-interaction', '-b', loop_device()])
        device = loop_device()
        if device:
            command(['udisksctl', 'loop-delete', '--no-user-interaction', '-b', device])
        if args.action == 'clean':
            if IMAGE.is_symlink() or IMAGE.stat().st_size != CAPACITY:
                raise RuntimeError('Image inattendue ; suppression refusée.')
            IMAGE.unlink()
            print('Volume supprimé. Code source conservé.')
    elif args.action == 'pull':
        configuration()
        for name in ('ollama', 'portal', 'kiwix', 'open-webui'):
            print(f'Téléchargement : {name}', flush=True)
            podman('pull', reference(name))
    elif args.action == 'prepare':
        prepare()
    elif args.action == 'prepare-speech':
        prepare_speech()
    elif args.action == 'download-corpus':
        download_corpus()
    elif args.action == 'pause-inference':
        checked_mount()
        setup.write_json(MOUNT / 'private/inference-paused.json', {'reason': 'user_gaming'}, private=True)
        setup.write_json(MOUNT/'data/catalog/inference.json',{'state':'paused','reason':'user_gaming'})
        podman('stop', '-t', '10', PREFIX + 'ollama', capture=True)
        print('Mode jeu actif : calcul IA arrêté et relance bloquée ; documents conservés.')
    elif args.action == 'resume-inference':
        checked_mount()
        (MOUNT / 'private/inference-paused.json').unlink(missing_ok=True)
        setup.write_json(MOUNT/'data/catalog/inference.json',{'state':'starting','reason':''})
        podman('start', PREFIX + 'ollama', capture=True)
        print('Calcul IA réactivé à la demande de l’utilisateur.')
    elif args.action == 'jobs':
        checked_mount()
        result = command(['systemctl', '--user', 'is-active', 'setupsurvie-corpus.service'],
                         capture=True, check=False)
        print('Transfert documentaire :', result.stdout.strip())
        progress = MOUNT / 'results/corpus-progress.json'
        if progress.exists():
            item = json.loads(progress.read_text())
            print(item.get('preparing'), f"{100 * item.get('downloaded_bytes', 0) / item.get('total_bytes', 1):.1f}%")
    elif args.action=='network':
        app,c=configuration()
        if args.name and not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',args.name):raise RuntimeError('Nom local non valide.')
        import discovery
        discovery.stop(app)
        c['bind']='0.0.0.0' if args.lan_host else '127.0.0.1'
        if args.name:c['discovery_name']=args.name
        if args.lan_host:c['lan_host']=args.lan_host
        else:c.pop('lan_host',None)
        setup.write_json(app.settings_path,c,private=True)
        app.render(c)
        for name in ('portal','kiwix','open-webui'):
            podman('stop',PREFIX+name,capture=True)
            podman('rm',PREFIX+name,capture=True)
        up()
        app.addresses(c)
    elif args.action == 'up':
        up()
    elif args.action == 'down':
        down()
    elif args.action == 'status':
        podman('ps', '-a', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}')
        command(['df', '-h', MOUNT])
        command(['du', '-h', IMAGE])
    else:
        app, c = configuration()
        if args.action == 'pull-model':
            app.pull_model(c, c['chat_model'])
        elif args.action == 'record':
            app.record(c)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError, setup.SetupError) as exc:
        print(f'ERREUR : {exc}', file=sys.stderr)
        sys.exit(1)
