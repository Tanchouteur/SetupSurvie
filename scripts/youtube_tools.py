#!/usr/bin/env python3
"""Outils du téléchargement YouTube : yt-dlp, Deno et FFmpeg, figés et vérifiés.

Préparés sans action de l’utilisateur par l’installation, le kit hors ligne,
la réactivation après transfert et, en dernier recours, au premier usage.

- Paquets Python (yt-dlp, Deno, dépendances) : versions de
  scripts/requirements-youtube.txt, mis en cache dans data/tools/youtube-wheels
  avec leurs empreintes, installés hors ligne dans data/tools/youtube/venv.
- FFmpeg (build LGPL) : archive figée dans deploy/youtube-tools.json, gardée
  dans data/tools/ffmpeg-archives et extraite dans data/tools/ffmpeg/<version>.

Un environnement Python copié sur un autre disque ou un autre PC peut ne plus
démarrer : il est alors recréé depuis le cache, sans Internet.
"""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import venv
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import setup
from delivery_paths import locked
from pilot import durable

MANIFEST=ROOT/'deploy/youtube-tools.json'
REQUIREMENTS=ROOT/'scripts/requirements-youtube.txt'
BUNDLED=ROOT/'vendor/youtube'
LINUX_PLATFORMS=('manylinux_2_28_x86_64','manylinux_2_27_x86_64','manylinux_2_17_x86_64','manylinux2014_x86_64')
HIDDEN={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}


def manifest():return json.loads(MANIFEST.read_text(encoding='utf-8'))


def pinned():
    """Exact « nom==version » lines of the requirements file."""
    values={}
    for line in REQUIREMENTS.read_text(encoding='utf-8').splitlines():
        line=line.split('#')[0].strip()
        if not line:continue
        name,separator,version=line.partition('==')
        if not separator:raise setup.SetupError('Version non figée dans requirements-youtube.txt : '+line)
        values[normal(name)]=version.strip()
    return values


def normal(name):return name.lower().replace('_','-').replace('.','-')


def host():return 'windows' if os.name=='nt' else 'linux'


def paths(data):
    data=Path(data);tools=data/'tools'
    version=manifest()['ffmpeg']['version']
    return {'wheels':tools/'youtube-wheels','archives':tools/'ffmpeg-archives','ffmpeg':tools/'ffmpeg'/version,
            'venv':tools/'youtube'/'venv','ready':tools/'youtube'/'ready.json'}


def python(data):
    folder=paths(data)['venv']
    return folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def ffmpeg(data):
    path=paths(data)['ffmpeg']/('ffmpeg.exe' if os.name=='nt' else 'ffmpeg')
    return path if path.is_file() else None


def deno(data):
    folder=paths(data)['venv']
    path=folder/('Scripts/deno.exe' if os.name=='nt' else 'bin/deno')
    return path if path.is_file() else None


def file_hash(path):
    digest=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()


# Python packages -----------------------------------------------------------

def wheel_name(path):
    """Distribution name and version of a wheel file name."""
    parts=Path(path).name.split('-')
    return normal(parts[0]),parts[1] if len(parts)>1 else ''


def validate_wheels(folder):
    """Every cached wheel is pinned and matches the recorded size and hash."""
    folder=Path(folder);path=folder/'manifest.json'
    if path.is_symlink() or not path.is_file():raise setup.SetupError('Cache des outils YouTube absent.')
    records=json.loads(path.read_text(encoding='utf-8')).get('files')
    if not isinstance(records,list) or not records:raise setup.SetupError('Cache des outils YouTube vide.')
    versions=pinned();listed=set()
    for record in records:
        name=record.get('path') if isinstance(record,dict) else None
        if not isinstance(name,str) or Path(name).name!=name or not name.endswith('.whl') or name in listed:raise setup.SetupError('Paquet des outils YouTube non valide.')
        distribution,version=wheel_name(name)
        if versions.get(distribution)!=version:raise setup.SetupError('Paquet non prévu dans le cache YouTube : '+name)
        wheel=folder/name
        if wheel.is_symlink() or not wheel.is_file() or wheel.stat().st_size!=record.get('bytes') or file_hash(wheel)!=record.get('sha256'):
            raise setup.SetupError('Paquet des outils YouTube modifié ; installation refusée : '+name)
        listed.add(name)
    if {p.name for p in folder.glob('*.whl')}!=listed:raise setup.SetupError('Liste des paquets YouTube non conforme.')
    return records


def record_wheels(folder):
    records=[{'path':p.name,'bytes':p.stat().st_size,'sha256':file_hash(p)} for p in sorted(Path(folder).glob('*.whl')) if not p.is_symlink()]
    setup.write_json(Path(folder)/'manifest.json',{'schema':1,'yt_dlp':manifest()['yt_dlp']['version'],'files':records})
    validate_wheels(folder)


def download_wheels(data,*,target=None,run=subprocess.run):
    """pip download of the pinned wheels, for this computer or another target.

    target: None (this Python), ('windows','3.13') or ('linux','3.13')."""
    folder=paths(data)['wheels'];durable.mkdir(folder)
    bootstrap(data,run=run)
    command=[str(python(data)),'-m','pip','download','--disable-pip-version-check','--only-binary=:all:','--no-deps','--dest',str(folder),'-r',str(REQUIREMENTS)]
    if target:
        system,version=target
        platforms=('win_amd64',) if system=='windows' else LINUX_PLATFORMS
        command+=[item for platform in platforms for item in ('--platform',platform)]
        command+=['--python-version',version,'--implementation','cp','--abi','cp'+version.replace('.','')]
    run(command,check=True,timeout=900,**HIDDEN)
    record_wheels(folder)


def bootstrap(data,*,fresh=False,run=subprocess.run):
    """An isolated environment with pip (ensurepip ships with Python, offline)."""
    folder=paths(data)['venv']
    if fresh:shutil.rmtree(folder,ignore_errors=True)
    if not fresh and python(data).is_file():
        try:
            if run([str(python(data)),'-m','pip','--version'],capture_output=True,timeout=120,**HIDDEN).returncode==0:return
        except (OSError,subprocess.SubprocessError):pass
        shutil.rmtree(folder,ignore_errors=True)
    venv.EnvBuilder(with_pip=False).create(folder)
    run([str(python(data)),'-m','ensurepip','--upgrade'],check=True,timeout=300,**HIDDEN)


def install_venv(data,*,run=subprocess.run):
    """Recreate the environment and install only from the verified cache."""
    wheels=paths(data)['wheels']
    validate_wheels(wheels)
    bootstrap(data,fresh=True,run=run)
    run([str(python(data)),'-m','pip','install','--disable-pip-version-check','--no-index','--find-links',str(wheels),'-r',str(REQUIREMENTS)],check=True,timeout=900,**HIDDEN)


def installed_version(data,*,run=subprocess.run):
    try:
        result=run([str(python(data)),'-m','yt_dlp','--version'],capture_output=True,text=True,timeout=60,**HIDDEN)
        return result.stdout.strip() if result.returncode==0 else None
    except (OSError,subprocess.SubprocessError):return None


# FFmpeg --------------------------------------------------------------------

def download_ffmpeg(data,system=None,*,opener=urllib.request.urlopen):
    entry=manifest()['ffmpeg'][system or host()]
    folder=paths(data)['archives'];durable.mkdir(folder)
    target=folder/entry['file']
    if target.is_file() and target.stat().st_size==entry['bytes'] and file_hash(target)==entry['sha256']:return target
    partial=target.with_name(target.name+'.part')
    with opener(entry['url'],timeout=60) as response,open(partial,'wb') as stream:shutil.copyfileobj(response,stream,1<<20)
    if partial.stat().st_size!=entry['bytes'] or file_hash(partial)!=entry['sha256']:
        partial.unlink(missing_ok=True);raise setup.SetupError('Archive FFmpeg non conforme à l’empreinte attendue ; rien n’est installé.')
    durable.publish(partial,target)
    return target


def bundled_ffmpeg(system=None):
    entry=manifest()['ffmpeg'][system or host()];path=BUNDLED/'ffmpeg'/entry['file']
    return path if path.is_file() else None


def extract_ffmpeg(data,archive,system=None):
    """Extract ffmpeg, ffprobe and the licence only, after checking the archive."""
    system=system or host();entry=manifest()['ffmpeg'][system]
    archive=Path(archive)
    if archive.stat().st_size!=entry['bytes'] or file_hash(archive)!=entry['sha256']:raise setup.SetupError('Archive FFmpeg modifiée ; installation refusée.')
    wanted={'ffmpeg.exe','ffprobe.exe','LICENSE.txt'} if system=='windows' else {'ffmpeg','ffprobe','LICENSE.txt'}
    target=paths(data)['ffmpeg'];staging=target.with_name(target.name+'.tmp')
    shutil.rmtree(staging,ignore_errors=True);durable.mkdir(staging)
    def keep(name):
        parts=PurePosixPath(name).parts
        return len(parts)>=2 and parts[-1] in wanted and (parts[-2]=='bin' or parts[-1]=='LICENSE.txt') and '..' not in parts
    found=set()
    if archive.name.endswith('.zip'):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if member.is_dir() or not keep(member.filename):continue
                with bundle.open(member) as source,open(staging/PurePosixPath(member.filename).name,'wb') as stream:shutil.copyfileobj(source,stream)
                found.add(PurePosixPath(member.filename).name)
    else:
        with tarfile.open(archive,'r:*') as bundle:
            for member in bundle.getmembers():
                if not member.isfile() or not keep(member.name):continue
                with bundle.extractfile(member) as source,open(staging/PurePosixPath(member.name).name,'wb') as stream:shutil.copyfileobj(source,stream)
                found.add(PurePosixPath(member.name).name)
    if found!=wanted:
        shutil.rmtree(staging,ignore_errors=True);raise setup.SetupError('Archive FFmpeg incomplète ; installation refusée.')
    if system!='windows':
        for name in ('ffmpeg','ffprobe'):(staging/name).chmod(0o755)
    shutil.rmtree(target,ignore_errors=True);durable.publish(staging,target)
    return target


# Orchestration --------------------------------------------------------------

def adopt_bundled(data):
    """Copy the kit's verified caches into the data folder (offline install)."""
    wheels=BUNDLED/'wheels'
    if wheels.is_dir() and (wheels/'manifest.json').is_file():
        validate_wheels(wheels)
        target=paths(data)['wheels'];durable.mkdir(target)
        for path in wheels.iterdir():
            if path.is_file() and not path.is_symlink():shutil.copyfile(path,target/path.name)
        validate_wheels(target)
    archive=bundled_ffmpeg()
    if archive:
        folder=paths(data)['archives'];durable.mkdir(folder)
        if not (folder/archive.name).is_file():shutil.copyfile(archive,folder/archive.name)


def status(data,*,run=subprocess.run):
    version=installed_version(data,run=run)
    expected=manifest()['yt_dlp']['version']
    return {'yt_dlp':version,'expected_yt_dlp':expected,'deno':bool(deno(data)),'ffmpeg':bool(ffmpeg(data)),
            'ready':bool(version) and bool(deno(data)) and bool(ffmpeg(data))}


def prepare(data,*,offline=False,force=False,run=subprocess.run,opener=urllib.request.urlopen,log=print):
    """Make yt-dlp, Deno and FFmpeg usable; True when all three are ready.

    Offline: only the data folder caches and the kit. Online: missing pinned
    files are downloaded and verified first. Never touches the system."""
    data=Path(data);tools=data/'tools';durable.mkdir(tools)
    with locked(tools/'youtube-prepare.lock'):
        if not force and status(data,run=run)['ready']:return True
        try:adopt_bundled(data)
        except setup.SetupError as error:log('Kit : '+str(error))
        wheels=paths(data)['wheels']
        try:validate_wheels(wheels);cached=True
        except (setup.SetupError,OSError,ValueError):cached=False
        if not cached and not offline:download_wheels(data,run=run);cached=True
        if cached and (force or not installed_version(data,run=run) or not deno(data)):install_venv(data,run=run)
        if force or not ffmpeg(data):
            entry=manifest()['ffmpeg'][host()];archive=paths(data)['archives']/entry['file']
            if not archive.is_file() and not offline:archive=download_ffmpeg(data,opener=opener)
            if archive.is_file():extract_ffmpeg(data,archive)
        state=status(data,run=run)
        if state['yt_dlp']:setup.write_json(paths(data)['ready'],{**state,'offline':offline})
        return state['ready']


def cache_target(data,system,python_version='3.13',*,run=subprocess.run,opener=urllib.request.urlopen):
    """Download the pinned files for another computer of the kit (never run)."""
    if system not in ('windows','linux'):raise setup.SetupError('Cible attendue : windows ou linux.')
    with locked(Path(data)/'tools'/'youtube-prepare.lock'):
        download_wheels(data,target=(system,python_version),run=run)
        download_ffmpeg(data,system,opener=opener)


def ensure(data,*,log=print,run=subprocess.run,opener=urllib.request.urlopen):
    """Before a download: repair from the caches, then online if needed."""
    if status(data,run=run)['ready']:return True
    log('Préparation des outils de téléchargement (yt-dlp, Deno, FFmpeg)…')
    try:
        if prepare(data,offline=True,run=run,opener=opener,log=log):return True
    except (setup.SetupError,OSError,ValueError,subprocess.SubprocessError):pass
    return prepare(data,offline=False,force=True,run=run,opener=opener,log=log)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data-dir',required=True)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--cache-target',action='append',default=[],help='windows:3.13 ou linux:3.13, pour le kit')
    args=parser.parse_args()
    data=setup.safe_path(args.data_dir)
    ok=prepare(data,offline=args.offline)
    for target in args.cache_target:
        system,_,version=target.partition(':');cache_target(data,system,version or '3.13')
    print('Outils YouTube prêts.' if ok else 'Outils YouTube incomplets ; ils seront préparés au premier téléchargement avec Internet.')
