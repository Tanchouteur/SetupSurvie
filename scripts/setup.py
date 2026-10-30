#!/usr/bin/env python3
"""SetupSurvie launcher. Python 3.10+, standard library only; never runs a shell."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = json.loads((ROOT / "deploy/versions.json").read_text(encoding="utf-8"))
PORTS = {"portal": 8080, "kiwix": 8081, "open-webui": 3000}
DIRECTORIES = ("library/zim", "library/guides", "catalog", "state/openwebui", "models")
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


class SetupError(RuntimeError):
    pass


def run(args, *, capture=False, env=None, timeout=None):
    try:
        result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env,
                                text=True, encoding="utf-8", errors="replace",
                                capture_output=capture, timeout=timeout, check=True)
        return result.stdout.strip() if capture else ""
    except FileNotFoundError as exc:
        raise SetupError(f"Programme introuvable : {args[0]}. Voir docs/14-installation.md.") from exc
    except subprocess.TimeoutExpired as exc:
        raise SetupError(f"Délai dépassé : {args[0]}. Voir les journaux.") from exc
    except subprocess.CalledProcessError as exc:
        # Do not print commands or environment: they can contain credentials.
        detail = (exc.stderr or "").strip() if capture else ""
        raise SetupError(f"Échec de {args[0]} (code {exc.returncode}). {detail}") from exc


def write_json(path, value, *, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if private and os.name != "nt":
        tmp.chmod(0o600)
    tmp.replace(path)


def safe_path(value):
    path = Path(value).expanduser().resolve()
    if any(c in str(path) for c in "\n\r\x00"):
        raise SetupError("Le chemin contient un caractère non pris en charge.")
    return path


class Installation:
    def __init__(self, work_dir=None):
        self.work = safe_path(work_dir or ROOT / ".local")
        self.settings_path = self.work / "settings.json"
        self.env_path = self.work / "compose.env"

    def load(self):
        if not self.settings_path.exists():
            raise SetupError("Installation non initialisée. Lancez d’abord install ou init.")
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def init(self, target, data_dir=None, lan=False, cpu=False):
        self.work.mkdir(parents=True, exist_ok=True)
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
                      "admin_password": secrets.token_urlsafe(24),
                      "chat_model": VERSIONS["default_model"]}
            write_json(self.settings_path, config, private=True)
            credentials = self.work / "identifiants.txt"
            credentials.write_text("Compte administrateur local Open WebUI\n"
                                   f"Identifiant : {config['admin_email']}\n"
                                   f"Mot de passe initial : {config['admin_password']}\n"
                                   "Ne pas diffuser ce fichier. Les comptes lecteurs se créent dans l’administration.\n",
                                   encoding="utf-8")
            if os.name != "nt":
                credentials.chmod(0o600)
        for name in DIRECTORIES:
            (Path(config["data_dir"]) / name).mkdir(parents=True, exist_ok=True)
        self.render(config)
        self.catalog(config)
        return config

    def render(self, c):
        values = {"DATA_DIR": c["data_dir"], "BIND_ADDRESS": c["bind"],
                  "OLLAMA_BASE_URL": "http://ollama:11434" if c["target"] == "linux" else "http://host.docker.internal:11435",
                  "WEBUI_SECRET_KEY": c["secret"], "WEBUI_ADMIN_EMAIL": c["admin_email"],
                  "WEBUI_ADMIN_PASSWORD": c["admin_password"], "CHAT_MODEL": c["chat_model"]}
        values.update({key: self.image_reference(c, service) for key, service in
                       (("WEBUI_IMAGE", "open-webui"), ("KIWIX_IMAGE", "kiwix"),
                        ("PORTAL_IMAGE", "portal"), ("OLLAMA_IMAGE", "ollama"))})
        lines = []
        for key, val in values.items():
            if any(ch in val for ch in "\r\n\x00"):
                raise SetupError(f"Valeur invalide pour {key}.")
            lines.append(key + "='" + val.replace("'", "\\'") + "'")
        self.env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if os.name != "nt":
            self.env_path.chmod(0o600)

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
        return base + list(args)

    def compose(self, c, *args, capture=False, timeout=None):
        return run(self.command(c, *args), capture=capture, timeout=timeout)

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
        if c["target"] != "windows":
            return
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
                    "OLLAMA_NO_CLOUD": "1", "OLLAMA_CONTEXT_LENGTH": "4096",
                    "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_MAX_LOADED_MODELS": "1"})
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
        marker = Path(c["data_dir"]) / "state/openwebui/cache/embedding-ready.json"
        if marker.exists():
            cached = json.loads(marker.read_text(encoding="utf-8"))
            if cached == VERSIONS["embedding"]:
                return
            raise SetupError("Le modèle de recherche a changé. Prévoir une réindexation avant la mise à jour.")
        if offline:
            raise SetupError("BGE-M3 n’est pas préparé. Lancez prepare une fois avec Internet.")
        print("Préparation du modèle multilingue BGE-M3 (plusieurs Go, CPU, une seule fois)…", flush=True)
        self.compose(c, "run", "--rm", "--no-deps", "-T", "--entrypoint", "python",
                     "-e", "HF_HUB_OFFLINE=0", "-e", "OFFLINE_MODE=false",
                     "open-webui", "-c", PREPARE_EMBEDDING)
        # The container may create root-owned directories on Linux. Write the marker through it.
        script = "from pathlib import Path; Path('/app/backend/data/cache/embedding-ready.json').write_text(" + repr(json.dumps(VERSIONS["embedding"])) + ")"
        self.compose(c, "run", "--rm", "--no-deps", "-T", "--entrypoint", "python", "open-webui", "-c", script)

    def up(self, c):
        self.catalog(c)
        self.start_native(c)
        self.compose(c, "up", "-d", "--pull", "never", "--wait", "--wait-timeout", "420")
        # Validate from the same network namespace as Open WebUI, not just from the host.
        script = "import os,urllib.request; print(urllib.request.urlopen(os.environ['OLLAMA_BASE_URL']+'/api/version',timeout=15).read().decode())"
        self.compose(c, "exec", "-T", "open-webui", "python", "-c", script)

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

    def verify(self, c, inference=False):
        failures = []
        for name, port, route in (("Portail", 8080, "/health"), ("Kiwix", 8081, "/"), ("Open WebUI", 3000, "/health")):
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f"http://127.0.0.1:{port}{route}", timeout=20) as response:
                    if response.status != 200:
                        raise SetupError(f"HTTP {response.status}")
                print(f"OK : {name}")
            except (OSError, SetupError) as error:
                failures.append(f"{name} : {error}")
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
                                       "think": False, "stream": False, "options": {"num_ctx": 4096, "num_predict": 128}}, timeout=600)
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
        report = {"automated_checks_passed": not failures, "failures": failures,
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
        run(['docker', 'image', 'load', '-i', source])
        for name in expected:
            entry = entries[name]
            actual = json.loads(run(['docker', 'image', 'inspect', entry['id']], capture=True))[0]
            if actual['Id'] != entry['id']:
                raise SetupError('ID d’image invalide après chargement.')
        # `docker save/load` need not retain RepoDigests. Local immutable IDs avoid a network lookup.
        c['local_images'] = {name: entries[name] for name in expected}
        write_json(self.settings_path, c, private=True)
        self.render(c)
        print('Images importées et identifiants locaux enregistrés. Aucun service démarré.')


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
        child.add_argument("--cpu", action="store_true", help="Linux : essai CPU explicite, sans réservation GPU")
        if command == "install":
            child.add_argument("--offline", action="store_true")
    for command in ("up", "down", "doctor", "catalog", "reload-library", "demo", "verify", "record", "prepare", "pull-model", "configure", "export-images", "import-images"):
        child = subs.add_parser(command)
        if command == "verify":
            child.add_argument("--inference", action="store_true")
        if command == "prepare":
            child.add_argument("--offline", action="store_true")
        if command == "pull-model":
            child.add_argument("model", nargs="?")
        if command == "configure":
            child.add_argument("--lan", action=argparse.BooleanOptionalAction, required=True)
        if command in {"export-images", "import-images"}:
            child.add_argument("destination")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    app = Installation(args.work_dir)
    if args.action in {"install", "init"}:
        c = app.init(args.target, args.data_dir, args.lan, args.cpu)
    else:
        c = app.load()
        app.render(c)
    if args.action == "init":
        print(f"Réglages conservés dans {app.work}. Identifiants dans identifiants.txt.")
    elif args.action == "install":
        app.doctor(c)
        app.demo(c)
        if not args.offline:
            app.compose(c, "pull")
        app.prepare(c, args.offline)
        app.up(c)
        if not args.offline:
            existing = app.request('http://127.0.0.1:11435/api/tags').get('models', [])
            if c['chat_model'] not in {model['name'] for model in existing}:
                app.pull_model(c, c["chat_model"])
            else:
                app.record(c)
        app.verify(c)
        print(f"Accueil : http://localhost:8080 — identifiants : {app.work / 'identifiants.txt'}")
    elif args.action == "configure":
        c["bind"] = "0.0.0.0" if args.lan else "127.0.0.1"
        write_json(app.settings_path, c, private=True)
        app.render(c)
        print("Réglage LAN enregistré. Lancez up pour l’appliquer.")
    elif args.action == "up":
        app.prepare(c, offline=True)
        app.up(c)
    elif args.action == "down":
        app.compose(c, "down")
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
    else:
        getattr(app, args.action)(c)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SetupError, OSError, ValueError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        raise SystemExit(1)
