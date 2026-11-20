#!/usr/bin/env python3
"""SetupSurvie launcher. Python 3.11+, standard library only; never runs a shell."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pilot import durable
VERSIONS = json.loads((ROOT / "deploy/versions.json").read_text(encoding="utf-8"))
PORTS = {"portal": 8080, "kiwix": 8081, "open-webui": 3000}
MANAGED_ENV={'DATA_DIR','BIND_ADDRESS','OLLAMA_BASE_URL','WEBUI_SECRET_KEY','WEBUI_ADMIN_EMAIL',
             'WEBUI_ADMIN_PASSWORD','CHAT_MODEL','WEBUI_IMAGE','KIWIX_IMAGE','PORTAL_IMAGE','OLLAMA_IMAGE',
             'TLS_PORTAL_ADDRESSES','TLS_WEBUI_ADDRESSES','TLS_KIWIX_ADDRESSES','TLS_FALLBACK_HOST','PILOT_CONTROL_TOKEN','ROUTING_IMAGE','HOST_GATEWAY'}
INITIAL_ZIM_VIDEO_REQUEST = 'initial-zim-video-inventory.json'
DIRECTORIES = ("library/zim", "library/video", "library/guides", "library/maps", "catalog", "state/openwebui", "state/pilot", "state/caddy", "models")
PREPARE_EMBEDDING = """
import os
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['TIKTOKEN_CACHE_DIR'] = '/app/backend/data/cache/tiktoken'
import tiktoken
for name in ('cl100k_base', 'o200k_base'):
    tiktoken.get_encoding(name)
from huggingface_hub import snapshot_download
snapshot_download(repo_id='BAAI/bge-m3', revision=REVISION,
    local_dir='/app/backend/data/cache/embedding/bge-m3',
    allow_patterns=['*.json', '*.txt', '*.model', '*.safetensors', 'pytorch_model.bin', '1_Pooling/*'])
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('/app/backend/data/cache/embedding/bge-m3',
    device='cpu', trust_remote_code=False, local_files_only=True)
assert m.encode(['test']).shape[1] == 1024
""".replace("REVISION", repr(VERSIONS["embedding"]["revision"]))
PREPARE_SPEECH = """
import os
os.environ['HF_HUB_OFFLINE']='0'
from huggingface_hub import snapshot_download
snapshot_download(repo_id=REPOSITORY,revision=REVISION,
 local_dir='/app/backend/data/cache/whisper/faster-whisper-small',
 allow_patterns=['*.json','*.txt','*.bin'])
from faster_whisper import WhisperModel
WhisperModel('/app/backend/data/cache/whisper/faster-whisper-small',device='cpu',compute_type='int8',local_files_only=True)
""".replace('REPOSITORY',repr(VERSIONS['speech']['repository'])).replace('REVISION',repr(VERSIONS['speech']['revision']))


class SetupError(RuntimeError):
    pass


def canonical_image_id(value):
    value=str(value).removeprefix('sha256:')
    if not re.fullmatch('[0-9a-f]{64}',value):raise SetupError('Identifiant d’image non valide.')
    return 'sha256:'+value


def run(args, *, capture=False, env=None, timeout=None):
    try:
        result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env,
                                text=True, encoding="utf-8", errors="replace",
                                capture_output=capture, timeout=timeout, check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        return result.stdout.strip() if capture else ""
    except FileNotFoundError as exc:
        raise SetupError(f"Programme introuvable : {args[0]}. Voir docs/installation/README.md.") from exc
    except subprocess.TimeoutExpired as exc:
        raise SetupError(f"Délai dépassé : {args[0]}. Voir les journaux.") from exc
    except subprocess.CalledProcessError as exc:
        # Do not print commands or environment: they can contain credentials.
        detail = (exc.stderr or "").strip() if capture else ""
        raise SetupError(f"Échec de {args[0]} (code {exc.returncode}). {detail}") from exc


def write_json(path, value, *, private=False):
    body = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode('utf-8')
    durable.write_bytes(path, body, private=private)


def prepare_youtube_tools(config,offline):
    """yt-dlp, Deno and FFmpeg for video lists; optional, never blocks setup."""
    try:
        import youtube_tools
        if youtube_tools.prepare(config['data_dir'],offline=offline):print('Outils de téléchargement des vidéos YouTube prêts.')
        else:print('Outils de téléchargement des vidéos YouTube : préparation terminée au premier téléchargement avec Internet.')
    except (OSError,ValueError,SetupError,subprocess.SubprocessError):
        print('Outils de téléchargement des vidéos YouTube non préparés ; ils le seront au premier téléchargement avec Internet. Les autres fonctions restent disponibles.')


def schedule_initial_videos(app, config, *, offline):
    """Leave durable requests for the existing host inventory and pilot queue."""
    from delivery_paths import destination
    from pilot.youtube_list import INSTALLATION_LIST, MAX_TEXT, parse_list

    data = Path(config['data_dir'])
    try:
        archives = destination(data, 'library/zim')
        if any(path.is_file() and not path.is_symlink() for path in archives.glob('*.zim')):
            write_json(app.work / INITIAL_ZIM_VIDEO_REQUEST, {'requested': True}, private=True)
            print('Inventaire vidéo des encyclopédies demandé en arrière-plan. Suivi dans Vidéos de la bibliothèque.')
    except (OSError, SetupError):
        print('Inventaire vidéo des encyclopédies à lancer depuis Vidéos de la bibliothèque.')

    if offline:
        return
    try:
        with (ROOT / 'deploy' / INSTALLATION_LIST).open('rb') as source:
            raw = source.read(MAX_TEXT + 1)
        if len(raw) > MAX_TEXT:
            raise ValueError('liste trop longue')
        text = raw.decode('utf-8-sig')
        entries, errors = parse_list(text)
        if entries:
            path = destination(data, 'state/pilot/' + INSTALLATION_LIST)
            durable.write_bytes(path, text.encode('utf-8'))
            print(f'{len(entries)} vidéo(s) YouTube demandée(s) en arrière-plan. Suivi dans File d’attente.')
        elif errors:
            print('La liste YouTube de l’installation ne contient aucune adresse de vidéo valide.')
    except (OSError, ValueError, SetupError):
        print('Liste YouTube de l’installation illisible ou trop longue. Ajoutez-la depuis la bibliothèque.')


def safe_path(value):
    path = Path(value).expanduser().resolve()
    if any(c in str(path) for c in "\n\r\x00"):
        raise SetupError("Le chemin contient un caractère non pris en charge.")
    return path


def lan_host(value):
    if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?',value):
        raise SetupError('Adresse IPv4 ou nom local non valide ; ne pas inclure de port ni de protocole.')
    return value


def control_key(c):return hmac.new(c['secret'].encode(),b'SetupSurvie engine control v1',hashlib.sha256).hexdigest()


class Installation:
    def __init__(self, work_dir=None):
        self.work = safe_path(work_dir or ROOT / ".local")
        self.settings_path = self.work / "settings.json"
        self.env_path = self.work / "compose.env"

    def load(self):
        if not self.settings_path.exists():
            raise SetupError("Installation non initialisée. Lancez d’abord install ou init.")
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def init(self, target, data_dir=None, lan=False, cpu=False, *, initial_chat_model=None):
        durable.mkdir(self.work)
        if os.name != "nt":
            self.work.chmod(0o700)
        if self.settings_path.exists():
            config = self.load()
            if config["target"] != target:
                raise SetupError("Cette installation appartient à un autre système. Utilisez un autre --work-dir.")
            if data_dir and safe_path(data_dir) != Path(config["data_dir"]):
                raise SetupError("Le dossier de données est déjà fixé. Déplacez-le avec une sauvegarde, pas une réinstallation.")
            if cpu != config["cpu"] or (lan and config["bind"] != "0.0.0.0"):
                raise SetupError("Options différentes de l’installation existante. Utilisez configure pour le LAN ; ne changez pas implicitement le mode GPU.")
        else:
            data = safe_path(data_dir or ROOT / "data")
            if data == ROOT or data in ROOT.parents:
                raise SetupError("Choisissez un sous-dossier dédié aux données, pas le dépôt ou son parent.")
            if data == self.work or self.work.is_relative_to(data / "library"):
                raise SetupError("Les réglages privés ne doivent pas être placés dans la bibliothèque publique.")
            config = {"schema": 1, "target": target, "data_dir": data.as_posix(),
                      "bind": "0.0.0.0" if lan else "127.0.0.1", "cpu": cpu,
                      "project": "survie-" + secrets.token_hex(4),
                      "secret": secrets.token_hex(32), "admin_email": "admin@survie.local",
                      "admin_password": secrets.token_urlsafe(32),
                      "chat_model": initial_chat_model or VERSIONS["default_model"]}
            write_json(self.settings_path, config, private=True)
            credentials = self.work / "identifiants.txt"
            durable.write_bytes(credentials,("SetupSurvie — profils locaux sans mot de passe\n"
                                   "Ouvrez l’accueil et choisissez un profil. Aucun code de secours n’est nécessaire.\n"
                                   "Les anciennes informations techniques restent dans les réglages privés.\n").encode('utf-8'),private=True)
        for name in DIRECTORIES:
            durable.mkdir(Path(config["data_dir"]) / name)
        self.render(config)
        self.catalog(config)
        return config

    def render(self, c):
        (Path(c['data_dir'])/'library/video').mkdir(parents=True,exist_ok=True)
        values = {"DATA_DIR": c["data_dir"], "BIND_ADDRESS": c["bind"],
                  "OLLAMA_BASE_URL": "http://ollama:11434" if c["target"] == "linux" else "http://host.docker.internal:11435",
                  "WEBUI_SECRET_KEY": c["secret"], "WEBUI_ADMIN_EMAIL": c["admin_email"],
                  "WEBUI_ADMIN_PASSWORD": c["admin_password"], "CHAT_MODEL": c["chat_model"]}
        values['PILOT_CONTROL_TOKEN']=control_key(c)
        # Rootless Docker: host-gateway is the internal bridge, not the host.
        values['HOST_GATEWAY']='10.0.2.2' if c.get('docker_rootless') else 'host-gateway'
        routing_recipe=json.loads((ROOT/'deploy/routing-engine.json').read_text(encoding='utf-8')) if (ROOT/'deploy/routing-engine.json').exists() else None
        if routing_recipe:
            entry=c.get('routing_image')
            if entry and entry['reference']!=routing_recipe['image']:raise SetupError('Le moteur de routage a changé. Préparez ses données explicitement avant mise à jour.')
            values['ROUTING_IMAGE']=entry['id'] if entry else routing_recipe['image']
        hosts=['localhost']
        values['TLS_FALLBACK_HOST']=c.get('lan_host','localhost')
        if c['bind']=='0.0.0.0':hosts.append(c.get('discovery_name','survie')+'.local')
        if c.get('lan_host') and c['lan_host']!='localhost':hosts.append(c['lan_host'])
        for key,port in [('TLS_PORTAL_ADDRESSES',8443),('TLS_WEBUI_ADDRESSES',8444),('TLS_KIWIX_ADDRESSES',8445)]:
            values[key]=', '.join('https://'+host+':'+str(port) for host in hosts)
        values.update({key: self.image_reference(c, service) for key, service in
                       (("WEBUI_IMAGE", "open-webui"), ("KIWIX_IMAGE", "kiwix"),
                        ("PORTAL_IMAGE", "portal"), ("OLLAMA_IMAGE", "ollama"))})
        lines = []
        for key, val in values.items():
            if any(ch in val for ch in "\r\n\x00"):
                raise SetupError(f"Valeur invalide pour {key}.")
            lines.append(key + "='" + val.replace("'", "\\'") + "'")
        durable.write_bytes(self.env_path, ("\n".join(lines) + "\n").encode('utf-8'), private=True)

    @staticmethod
    def image_reference(c, service):
        entry = c.get('local_images', {}).get(service)
        if entry:
            if entry['reference'] != VERSIONS['images'][service]:
                raise SetupError('Le kit importé ne correspond plus aux versions du dépôt.')
            return entry['id']
        return VERSIONS['images'][service]

    def command(self, c, *args):
        base = ["docker", "compose", "--project-name", c["project"],
                "--env-file", str(self.env_path), "-f", str(ROOT / "compose.yaml")]
        if c["target"] == "linux":
            base += ["-f", str(ROOT / "compose.linux.yaml")]
            if not c["cpu"]:
                base += ["-f", str(ROOT / "compose.gpu.yaml")]
        if (Path(c['data_dir'])/'library/maps/routing/current/manifest.json').is_file():
            if c["target"] == "windows":
                base += ["-f", str(ROOT / "deploy/compose.routing-windows.yaml")]
            base += ["--profile", "routing"]
        return base + list(args)

    def compose(self, c, *args, capture=False, timeout=None):
        if args and args[0] in ("up","start","restart","run","exec"):
            import transfer
            transfer.guard(self.work)
        return run(self.command(c, *args), capture=capture, timeout=timeout,env=self.environment())

    @staticmethod
    def environment():
        # Compose gives shell values precedence over --env-file. Keep installations isolated.
        return {key:value for key,value in os.environ.items() if key not in MANAGED_ENV}

    def catalog(self, c):
        root = Path(c["data_dir"]) / "library/guides"
        documents = []
        formats = {".pdf", ".html", ".txt", ".md", ".epub"}
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in formats:
                continue
            if not path.resolve().is_relative_to(root.resolve()):
                continue
            relative = path.relative_to(root).as_posix()
            lang = "fr" if ".fr." in path.name else "en" if ".en." in path.name else "other"
            documents.append({"title": path.stem.replace("_", " "), "path": relative,
                              "language": lang, "format": path.suffix[1:].upper(), "bytes": path.stat().st_size})
        write_json(Path(c["data_dir"]) / "catalog/guides.json", {"documents": documents})

    def demo(self, c):
        dest = Path(c["data_dir"]) / "library/guides"
        for source in (ROOT / "fixtures/guides").iterdir():
            target = dest / source.name
            if not target.exists():
                shutil.copyfile(source, target)
        self.catalog(c)

    def doctor(self, c):
        run(["docker", "compose", "version"], capture=True)
        os_type = run(["docker", "info", "--format", "{{.OSType}}"], capture=True, timeout=30)
        if os_type != "linux":
            raise SetupError("Docker doit utiliser les conteneurs Linux.")
        if c["target"] == "linux":
            import linux_host
            rootless=linux_host.docker_rootless()
            if bool(c.get('docker_rootless'))!=rootless:
                c['docker_rootless']=rootless;write_json(self.settings_path,c,private=True);self.render(c)
            if rootless:print(linux_host.ensure_host_loopback())
        self.compose(c, "config", "--quiet")
        free = shutil.disk_usage(c["data_dir"]).free / 1024**3
        print(f"Docker et Compose disponibles. Espace libre : {free:.1f} Gio.")
        if free < 20:
            raise SetupError("Moins de 20 Gio disponibles. Libérez de la place avant les téléchargements (40 Gio conseillés pour le petit essai).")
        if c["target"] == "linux" and not c["cpu"]:
            run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture=False, timeout=30)
            print("Le démarrage d’Ollama vérifiera aussi l’accès GPU depuis Docker (NVIDIA Container Toolkit requis).")
        if c["target"] == "windows" and not self.ollama_binary():
            raise SetupError("Installez Ollama pour Windows puis rouvrez PowerShell.")
        print("Les ports Web attendus sont 3000, 8080 et 8081 ; Ollama utilise un port distinct, 11435.")

    @staticmethod
    def ollama_binary():
        binary = shutil.which("ollama")
        if binary:
            return binary
        local = Path(os.environ.get("LOCALAPPDATA", ".")) / "Programs/Ollama/ollama.exe"
        return str(local) if local.is_file() else None

    @staticmethod
    def request(url, payload=None, timeout=15):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        # LAN/local API calls must not be redirected through an ambient HTTP proxy.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as response:
            return json.load(response)

    def start_native(self, c):
        import transfer
        transfer.guard(self.work)
        if c["target"] != "windows":
            return
        if (self.work/'inference-paused.json').exists():
            print('Moteur IA en pause ; les documents restent disponibles.');return
        if os.name != "nt":
            raise SetupError("Le serveur natif Windows doit être démarré sur Windows.")
        marker = self.work / "native-ollama.json"
        try:
            self.request("http://127.0.0.1:11435/api/version", timeout=2)
        except (OSError, ValueError):
            pass
        else:
            if not marker.exists() or not self.native_owned(json.loads(marker.read_text(encoding='utf-8'))):
                raise SetupError("Le port 11435 appartient déjà à un serveur non géré par cette installation.")
            return
        binary = self.ollama_binary()
        if not binary:
            raise SetupError("Ollama Windows introuvable.")
        env = os.environ.copy()
        env.update({"OLLAMA_HOST": "0.0.0.0:11435", "OLLAMA_MODELS": str(Path(c["data_dir"]) / "models"),
                    "OLLAMA_NO_CLOUD": "1", "OLLAMA_CONTEXT_LENGTH": "8192",
                    "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_KEEP_ALIVE": "-1"})
        log_path = self.work / "ollama.log"
        with log_path.open("ab") as output:
            process = subprocess.Popen([binary, "serve"], env=env, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=output,
                                       creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        write_json(marker, {"pid": process.pid, "binary": str(Path(binary).resolve()), "started_at": time.time(),
                            "identity": self.native_identity(process.pid)}, private=True)
        for _ in range(45):
            if process.poll() is not None:
                raise SetupError(f"Ollama s’est arrêté. Consultez {log_path}.")
            try:
                self.request("http://127.0.0.1:11435/api/version", timeout=2)
                return
            except (OSError, ValueError):
                time.sleep(1)
        raise SetupError(f"Ollama ne répond pas sur 11435. Consultez {log_path}.")

    @staticmethod
    def native_identity(pid):
        """Windows process creation time + executable path, to guard against PID reuse."""
        if os.name != 'nt':
            return None
        import ctypes
        from ctypes import wintypes
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        api.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        handle = api.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return None
        try:
            name = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(name))
            times = [wintypes.FILETIME() for _ in range(4)]
            if not api.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)) or not api.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
                return None
            return {'path': str(Path(name.value).resolve()).casefold(),
                    'created': (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime}
        finally:
            api.CloseHandle(handle)

    def native_owned(self, marker):
        actual = self.native_identity(marker['pid'])
        return bool(actual and actual == marker.get('identity') and
                    actual['path'] == str(Path(marker['binary']).resolve()).casefold())

    def stop_native(self, c):
        if c['target'] != 'windows':
            return
        marker_path = self.work / 'native-ollama.json'
        if marker_path.exists():
            marker = json.loads(marker_path.read_text(encoding='utf-8'))
            if self.native_owned(marker):
                run(['taskkill', '/PID', str(int(marker['pid'])), '/T', '/F'], capture=True)
                marker_path.unlink()
                print('Serveur Ollama dédié arrêté ; autres instances inchangées.')
            else:
                print('PID Ollama absent ou différent : aucun processus natif arrêté.')

    def prepare(self, c, offline):
        self.prepare_speech(c,offline)
        marker = Path(c["data_dir"]) / "state/openwebui/cache/embedding-ready.json"
        if marker.exists():
            cached = json.loads(marker.read_text(encoding="utf-8"))
            folder=marker.parent/'embedding/bge-m3'
            if cached == VERSIONS["embedding"] and (folder/'config.json').is_file() and (folder/'tokenizer.json').is_file() and any((folder/name).is_file() for name in ('model.safetensors','pytorch_model.bin')):
                return
            if cached != VERSIONS['embedding']:raise SetupError("Le modèle de recherche a changé. Prévoir une réindexation avant la mise à jour.")
        if offline:
            raise SetupError("BGE-M3 n’est pas préparé. Lancez prepare une fois avec Internet.")
        print("Préparation du modèle multilingue BGE-M3 (plusieurs Go, CPU, une seule fois)…", flush=True)
        self.compose(c, "run", "--rm", "--no-deps", "-T", "--entrypoint", "python",
                     "-e", "HF_HUB_OFFLINE=0", "-e", "OFFLINE_MODE=false",
                     "open-webui", "-c", PREPARE_EMBEDDING)
        # The container may create root-owned directories on Linux. Write the marker through it.
        script = "from pathlib import Path; Path('/app/backend/data/cache/embedding-ready.json').write_text(" + repr(json.dumps(VERSIONS["embedding"])) + ")"
        self.compose(c, "run", "--rm", "--no-deps", "-T", "--entrypoint", "python", "open-webui", "-c", script)

    def prepare_speech(self,c,offline):
        marker=Path(c['data_dir'])/'state/openwebui/cache/whisper/ready.json'
        folder=marker.parent/'faster-whisper-small'
        if marker.exists() and json.loads(marker.read_text())==VERSIONS['speech'] and all((folder/name).is_file() for name in ('model.bin','config.json','tokenizer.json')):return
        if offline:raise SetupError('Reconnaissance vocale non préparée. Lancez prepare avec Internet ou importez les caches du kit.')
        self.compose(c,'run','--rm','--no-deps','-T','--entrypoint','python','-e','HF_HUB_OFFLINE=0','-e','OFFLINE_MODE=false','open-webui','-c',PREPARE_SPEECH)
        script="from pathlib import Path; Path('/app/backend/data/cache/whisper/ready.json').write_text("+repr(json.dumps(VERSIONS['speech']))+")"
        self.compose(c,'run','--rm','--no-deps','-T','--entrypoint','python','open-webui','-c',script)

    def install_windows_shortcuts(self,c,*,startup=True):
        if c['target']!='windows':return
        import windows_update
        windows_update.install_launcher(self,c)
        import windows_autostart
        stable=windows_autostart.prepare(self,c) if startup else None
        shell=shutil.which('powershell.exe')
        if not shell:raise SetupError('PowerShell Windows est requis pour créer les raccourcis.')
        run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/create-shortcuts.ps1'),
             '-WorkDir',str(self.work),'-Startup' if startup else '-DisableStartup'],capture=True)
        if stable:
            run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(stable.with_name('register-startup-windows.ps1')),
                 '-WorkDir',str(self.work)],capture=True)
        elif not startup and c.get('app_dir'):
            registration=Path(c['app_dir']).parent/'maintenance/register-startup-windows.ps1'
            if registration.exists():run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(registration),'-WorkDir',str(self.work),'-Disable'],capture=True)
        print('Raccourcis Ouvrir / Arrêter / Mettre à jour créés'+(' ; démarrage à l’ouverture de session activé.' if startup else ' ; démarrage automatique désactivé.'))

    def up(self, c):
        import transfer
        transfer.guard(self.work)
        journal=self.work/'update.json'
        if journal.exists():
            try:state=json.loads(journal.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                raise SetupError('Journal de mise à jour illisible : conservez les données et les dossiers updates ; récupération nécessaire avant démarrage.')
            if not isinstance(state,dict) or state.get('phase') not in ('complete','rolled_back'):
                raise SetupError('Mise à jour interrompue : utilisez Mettre-a-jour-SetupSurvie.cmd -Recover ou pilot_update.py recover avant de démarrer.')
        import routing_prepare
        routing_prepare.recover_publication(Path(c['data_dir']))
        self.catalog(c)
        paused=(self.work/'inference-paused.json').exists() or c.get('inference_autostart') is False
        if paused and c['target']=='linux':
            # Docker may restart an old container before the host launcher runs.
            self.compose(c,'stop','ollama')
        import control
        control.start(self,c)
        if not paused:self.start_native(c)
        services=['open-webui','kiwix','pilot','portal'] if paused else []
        if paused and (Path(c['data_dir'])/'library/maps/routing/current/manifest.json').is_file():services += ['router-foot','router-motorcycle','router-car']
        self.compose(c, "up", "-d", "--pull", "never", "--wait", "--wait-timeout", "420",*services)
        # Validate from the same network namespace as Open WebUI, not just from the host.
        script = "import os,urllib.request; print(urllib.request.urlopen(os.environ['OLLAMA_BASE_URL']+'/api/version',timeout=15).read().decode())"
        if not paused:
            self.compose(c, "exec", "-T", "open-webui", "python", "-c", script)
            self.compose(c,'exec','-T','pilot','python','-m','pilot.configure')
        import discovery
        try:discovery.start(self,c)
        except (SetupError,OSError,ValueError) as exc:print('Nom local automatique indisponible :',str(exc),'Le site et l’accès direct restent disponibles.')

    def addresses(self,c):
        host=c.get('lan_host') or 'localhost'
        print('Sur le PC serveur : http://localhost:8080 ; Open WebUI : http://localhost:3000')
        if c['bind']=='0.0.0.0':
            print('Nom facile à retenir : http://'+c.get('discovery_name','survie')+'.local:8080')
            print(f'Sur le réseau local : https://{host}:8443 ; Open WebUI : https://{host}:8444 ; Kiwix : https://{host}:8445')
            print('Installer le certificat local sur chaque appareil pour HTTPS. Voir docs/installation/pilote-marc.md.')
        else:print('Accès limité au PC serveur. configure --lan --lan-host ADRESSE_IP pour ouvrir le réseau privé.')

    def certificate(self,c,destination):
        dest=safe_path(destination)
        if dest.exists():raise SetupError('Le certificat de destination existe déjà.')
        self.compose(c,'cp','portal:/data/caddy/pki/authorities/local/root.crt',str(dest))
        print('Certificat PUBLIC exporté :',dest)

    def pull_model(self, c, model):
        if ":cloud" in model.lower() or model.lower().endswith('-cloud') or not model or any(x.isspace() for x in model):
            raise SetupError("Utilisez un identifiant de modèle local sans espaces.")
        print(f"Préparation du modèle local {model}…", flush=True)
        result = self.request("http://127.0.0.1:11435/api/pull", {"model": model, "stream": False}, timeout=7200)
        if result.get('error'):
            raise SetupError(f"Ollama : {result['error']}")
        self.record(c)

    def record(self, c):
        versions = self.request("http://127.0.0.1:11435/api/version")
        tags = self.request("http://127.0.0.1:11435/api/tags")
        write_json(self.work / "manifest.json", {"recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "target": c["target"], "images": VERSIONS["images"], "embedding": VERSIONS["embedding"],
                   "ollama": versions, "models": [{key: m.get(key) for key in ("name", "digest", "size", "details")} for m in tags.get("models", [])]})

    def prepare_models(self, c, additional_models=()):
        existing = self.request('http://127.0.0.1:11435/api/tags').get('models', [])
        installed = {model['name'] for model in existing}
        required = dict.fromkeys((c['chat_model'], *additional_models))
        missing = [model for model in required if model not in installed]
        for model in missing:
            self.pull_model(c, model)
        if not missing:
            self.record(c)

    def verify(self, c, inference=False):
        paused=(self.work/'inference-paused.json').exists()
        if paused and inference:
            raise SetupError('Moteur en pause : le test IA est refusé. Levez explicitement la pause avant de demander une inférence.')
        failures = []
        try:
            state=self.request('http://127.0.0.1:8080/api/inference')
            if not state.get('control_available'):failures.append('Contrôleur du moteur inaccessible depuis le site ; vérifier le service hôte et le port interne 11436.')
            else:print('OK : site → contrôleur authentifié du moteur')
            self.request('http://127.0.0.1:8080/api/inventory')
            print('OK : inventaire local')
        except (OSError,ValueError) as error:failures.append('API du site : '+str(error))
        for name, port, route in (("Portail", 8080, "/health"), ("Kiwix", 8081, "/"), ("Open WebUI", 3000, "/health")):
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f"http://127.0.0.1:{port}{route}", timeout=20) as response:
                    if response.status != 200:
                        raise SetupError(f"HTTP {response.status}")
                print(f"OK : {name}")
            except (OSError, SetupError) as error:
                failures.append(f"{name} : {error}")
        if paused:
            print('Moteur en pause : contrôles Ollama différés, aucune inférence demandée.')
        else:
            try:
                self.compose(c, "exec", "-T", "open-webui", "python", "-c",
                             "import os,urllib.request; urllib.request.urlopen(os.environ['OLLAMA_BASE_URL']+'/api/tags',timeout=15)")
                print("OK : Open WebUI → Ollama")
            except SetupError as error:
                failures.append(str(error))
            try:
                tags = self.request("http://127.0.0.1:11435/api/tags")
                names = {m["name"] for m in tags.get("models", [])}
                if c["chat_model"] not in names:
                    failures.append("Modèle de dialogue absent : lancez pull-model.")
                if inference and c["chat_model"] in names:
                    result = self.request("http://127.0.0.1:11435/api/generate",
                                          {"model": c["chat_model"], "prompt": "Réponds en français : combien font deux plus deux ?",
                                           "think": "low" if c["chat_model"].startswith("gpt-oss") else True, "stream": False, "options": {"num_ctx": 8192, "num_predict": 512}}, timeout=600)
                    if not result.get("response", "").strip():
                        failures.append("Réponse IA vide.")
                    else:
                        print("Réponse de test :", result["response"])
                        write_json(self.work / "inference-test.json", result)
            except (OSError, ValueError) as error:
                failures.append(f"Ollama : {error}")
        try:
            self.compose(c, "exec", "-T", "open-webui", "python", "-c",
                         "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('/app/backend/data/cache/embedding/bge-m3',device='cpu',trust_remote_code=False,local_files_only=True); assert m.encode(['français','English']).shape==(2,1024)")
            print("OK : embeddings locaux BGE-M3")
        except SetupError as error:
            failures.append(f"Recherche documentaire : {error}")
        try:
            self.compose(c,'exec','-T','open-webui','python','-c',
                         "from faster_whisper import WhisperModel; WhisperModel('/app/backend/data/cache/whisper/faster-whisper-small',device='cpu',compute_type='int8',local_files_only=True)")
            print('OK : modèle de transcription audio chargé depuis les fichiers locaux, sur CPU')
        except SetupError as error:failures.append('Transcription audio locale : '+str(error))
        report = {"automated_checks_passed": not failures, "failures": failures, "inference_paused": paused, "ollama_checks_deferred": paused,
                  "manual_checks_pending": ["LAN depuis un téléphone", "question française sur guide anglais", "réseau Internet débranché", "redémarrage du PC", "restauration"]}
        write_json(self.work / "verification.json", report)
        if failures:
            raise SetupError("\n".join(failures))
        print("Contrôles automatiques réussis. Les essais LAN, documentaire et hors ligne restent à réaliser selon le guide.")

    def export_images(self, c, destination):
        dest = safe_path(destination)
        if dest.exists():
            raise SetupError("Le fichier de destination existe déjà.")
        names = ["open-webui", "kiwix", "portal"]
        if c["target"] == "linux":
            names.append("ollama")
        # Export by the immutable IDs, then restore names explicitly when loading.
        records = []
        for service in names:
            item = json.loads(run(["docker", "image", "inspect", self.image_reference(c, service)], capture=True))[0]
            records.append({"service": service, "id": item["Id"], "reference": VERSIONS['images'][service]})
        if (Path(c['data_dir'])/'library/maps/routing/current/manifest.json').is_file():
            reference=json.loads((ROOT/'deploy/routing-engine.json').read_text(encoding='utf-8'))['image']
            routing_entry=c.get('routing_image')
            item=json.loads(run(['docker','image','inspect',routing_entry['id'] if routing_entry else reference],capture=True))[0]
            records.append({'service':'routing','id':item['Id'],'reference':reference})
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(["docker", "image", "save", "-o", dest, *[r["id"] for r in records]])
        write_json(Path(str(dest) + ".json"), {"images": records, "sha256": file_hash(dest),
                   "notice": "Images seulement, architecture du PC exporteur ; modèles et données exclus."})
        print("Images exportées. Les modèles, caches et données restent à sauvegarder séparément.")

    def import_images(self, c, source):
        source = safe_path(source)
        manifest = json.loads(Path(str(source) + '.json').read_text(encoding='utf-8'))
        if file_hash(source) != manifest['sha256']:
            raise SetupError('Empreinte du kit invalide : ne pas importer cette archive.')
        expected = {'open-webui', 'kiwix', 'portal'}
        if c['target'] == 'linux':
            expected.add('ollama')
        entries = {entry['service']: entry for entry in manifest['images']}
        if not expected.issubset(entries):
            raise SetupError('Le kit ne contient pas toutes les images du système cible.')
        for name in expected:
            if entries[name]['reference'] != VERSIONS['images'][name]:
                raise SetupError('Le kit ne correspond pas aux versions de ce dépôt.')
        if 'routing' in entries:
            reference=json.loads((ROOT/'deploy/routing-engine.json').read_text(encoding='utf-8'))['image']
            if entries['routing']['reference']!=reference:raise SetupError('Le kit contient un moteur de routage différent.')
            expected.add('routing')
        run(['docker', 'image', 'load', '-i', source])
        for name in expected:
            entry = entries[name]
            actual = json.loads(run(['docker', 'image', 'inspect', entry['id']], capture=True))[0]
            actual_id=canonical_image_id(actual['Id'])
            if actual_id != canonical_image_id(entry['id']):
                raise SetupError('ID d’image invalide après chargement.')
            entries[name]={**entry,'id':actual_id}
        # `docker save/load` need not retain RepoDigests. Local immutable IDs avoid a network lookup.
        c['local_images'] = {name: entries[name] for name in expected if name!='routing'}
        if 'routing' in expected:c['routing_image']=entries['routing']
        write_json(self.settings_path, c, private=True)
        self.render(c)
        print('Images importées et profils locaux préparés. Aucun service démarré.')


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def parser():
    p = argparse.ArgumentParser(description="Installation et tests du prototype SetupSurvie")
    p.add_argument("--work-dir", help="Réglages privés (par défaut .local dans le dépôt)")
    subs = p.add_subparsers(dest="action", required=True)
    for command in ("init", "install"):
        child = subs.add_parser(command)
        child.add_argument("--target", choices=("windows", "linux"), required=True)
        child.add_argument("--data-dir")
        child.add_argument("--lan", action="store_true", help="Publier les ports Web sur toutes les interfaces")
        child.add_argument('--lan-host',type=lan_host)
        child.add_argument("--cpu", action="store_true", help="Linux : essai CPU explicite, sans réservation GPU")
        if command == "install":
            child.add_argument("--work-dir", default=argparse.SUPPRESS, help="Réglages privés (par défaut .local dans le dépôt)")
            child.add_argument("--offline", action="store_true")
            child.add_argument('--content-pack',action='append',default=[],help='Lot documentaire choisi dans scripts/content.py list ; répéter pour plusieurs lots.')
            child.add_argument('--startup',action=argparse.BooleanOptionalAction,default=True,help='Windows : démarrage à l’ouverture de session et raccourcis du Bureau ; Linux : service utilisateur systemd au démarrage du PC. --no-startup ne l’active pas.')
    for command in ("up", "down", "doctor", "catalog", "reload-library", "demo", "verify", "record", "prepare", "prepare-maps", "pull-model", "configure", "export-images", "import-images", "addresses", "certificate", "recover-account", "shortcuts"):
        child = subs.add_parser(command)
        if command == "shortcuts":
            child.add_argument("--no-startup",action="store_true")
        if command == "verify":
            child.add_argument("--inference", action="store_true")
        if command == "prepare":
            child.add_argument("--offline", action="store_true")
        if command == "pull-model":
            child.add_argument("model", nargs="?")
        if command == "configure":
            child.add_argument("--lan", action=argparse.BooleanOptionalAction, required=True)
            child.add_argument('--lan-host',type=lan_host,help='Adresse IP du PC serveur, à réserver dans le routeur')
            child.add_argument('--name',help='Nom local court, par exemple survie-marc ; lettres minuscules, chiffres, tirets')
        if command in {"export-images", "import-images"}:
            child.add_argument("destination")
        if command=='certificate':child.add_argument('destination')
        if command=='recover-account':
            child.add_argument('email')
            child.add_argument('--reset-password',action='store_true')
    return p


def main(argv=None, *, initial_chat_model=None, additional_models=()):
    args = parser().parse_args(argv)
    selected_content = []
    if args.action == "install":
        if args.offline and args.content_pack:
            raise SetupError('Choisir le kit hors ligne ou des téléchargements de lots en ligne.')
        if args.content_pack:
            import content
            items = content.catalog()
            packs = set(args.content_pack)
            unknown = packs - {item['pack'] for item in items}
            if unknown:
                raise SetupError('Lots inconnus : ' + ', '.join(sorted(unknown)))
            selected_content = [item for item in items if item['pack'] in packs]
    app = Installation(args.work_dir)
    if args.action in {"install", "init"}:
        c = app.init(args.target, args.data_dir, args.lan, args.cpu, initial_chat_model=initial_chat_model)
        if args.lan_host:
            if not args.lan:raise SetupError('--lan-host nécessite --lan.')
            c['lan_host']=args.lan_host;write_json(app.settings_path,c,private=True);app.render(c)
    else:
        c = app.load()
        app.render(c)
    if args.action == "init":
        print(f"Réglages conservés dans {app.work}. Accès par profil, sans mot de passe.")
    elif args.action == "install":
        app.doctor(c)
        if not args.offline:
            if c['target'] == 'linux':
                import linux_offline_tools
                if linux_offline_tools.prepare(c['data_dir']):
                    print('Installateurs hors ligne vérifiés : Docker, Compose, Python et paquets réseau Linux.')
                else:
                    print('Installateurs hors ligne indisponibles pour cette architecture ou version de Python.')
            app.compose(c, "pull")
        app.prepare(c, args.offline)
        import search_index_tools
        try:
            if not search_index_tools.prepare(app,c,offline=args.offline):print('Indexation complémentaire à préparer depuis les réglages ; bibliothèque disponible.')
        except (OSError,ValueError,SetupError,subprocess.SubprocessError) as error:
            print('Outil d’indexation non préparé ('+(str(error).strip()[:200] or type(error).__name__)+') ; réessayez dans les réglages. Les autres fonctions restent disponibles.')
        prepare_youtube_tools(c,args.offline)
        app.up(c)
        if not args.offline:
            app.prepare_models(c, additional_models)
        if selected_content:
            content.download(Path(c['data_dir']), selected_content, workers=2)
            app.catalog(c);app.compose(c,'restart','kiwix','pilot')
        import map_install
        map_install.ensure(Path(c['data_dir']),offline=args.offline)
        app.catalog(c)
        # Maps add their local guide after the initial service startup.
        app.compose(c,'exec','-T','pilot','python','-c',
                    'from pilot import library; library.index_guides()')
        app.verify(c)
        app.install_windows_shortcuts(c,startup=args.startup)
        if c['target']=='linux':
            import linux_host
            if args.startup:
                for line in linux_host.install_autostart(app,c):print(line)
            if not linux_host.controller_reachable(app,c):
                print('Attention : le portail ne joint pas le contrôleur local ; démarrage/arrêt de l’IA et indexation automatique indisponibles depuis le site. Voir docs/installation/README.md.')
            else:print('Contrôleur local joignable depuis le portail.')
        schedule_initial_videos(app, c, offline=args.offline)
        print("Accueil : http://localhost:8080 — choisissez un profil, sans mot de passe")
    elif args.action == "prepare-maps":
        import map_install
        map_install.ensure(Path(c['data_dir']))
        app.catalog(c)
        app.compose(c,'exec','-T','pilot','python','-c',
                    'from pilot import library; library.index_guides()')
    elif args.action == "shortcuts":
        app.install_windows_shortcuts(c,startup=not args.no_startup)
    elif args.action == "configure":
        if args.lan and not args.lan_host and not c.get('lan_host'):
            raise SetupError('Précisez --lan-host avec l’adresse IPv4 du PC serveur.')
        if args.name and not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',args.name):raise SetupError('Nom local non valide.')
        import discovery
        discovery.stop(app)
        c["bind"] = "0.0.0.0" if args.lan else "127.0.0.1"
        if args.lan_host:c['lan_host']=args.lan_host
        if args.name:c['discovery_name']=args.name
        write_json(app.settings_path, c, private=True)
        app.render(c)
        discovery.network_status(app,c,discovery.local_ip(c),False,'Relancez les services pour appliquer ce réglage réseau.')
        print("Réglage LAN enregistré. Lancez up pour l’appliquer.")
    elif args.action == "up":
        (app.work/"startup-paused.json").unlink(missing_ok=True)
        app.prepare(c, offline=True)
        app.up(c)
    elif args.action == "down":
        if c["target"]=="windows":write_json(app.work/"startup-paused.json",{"reason":"user_shutdown"},private=True)
        import discovery
        discovery.stop(app)
        import library_tasks
        library_tasks.shutdown(app,c)
        try:
            app.compose(c, "down")
        finally:
            # Even an unavailable Docker daemon must not leave the owned native
            # Ollama process running. Never stop Docker Desktop or other projects.
            app.stop_native(c)
        print("Services arrêtés, données conservées.")
    elif args.action == 'reload-library':
        app.catalog(c)
        app.compose(c, 'restart', 'kiwix')
    elif args.action == "prepare":
        app.prepare(c, args.offline)
    elif args.action == "pull-model":
        app.pull_model(c, args.model or c["chat_model"])
    elif args.action == "verify":
        app.verify(c, args.inference)
    elif args.action == "export-images":
        app.export_images(c, args.destination)
    elif args.action == "import-images":
        app.import_images(c, args.destination)
    elif args.action=='certificate':app.certificate(c,args.destination)
    elif args.action=='recover-account':
        action='reset-password' if args.reset_password else 'recovery-code'
        app.compose(c,'exec','pilot','python','-m','pilot.console',action,args.email)
    else:
        getattr(app, args.action)(c)
    return 0


if __name__ == "__main__":
    # Helper modules ``import setup``: share this module so their SetupError
    # is the one caught below, and errors stay short French messages.
    sys.modules.setdefault("setup", sys.modules[__name__])
    try:
        raise SystemExit(main())
    except (SetupError, OSError, ValueError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        raise SystemExit(1)
