"""Optional pinned reader preparation. All runtime work stays local after preparation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import venv

import setup
from delivery_paths import locked,destination

VERSION='3.13.1'


def python(app):return app.work/'search-tools'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def ready(app):
    marker=app.work/'search-tools/reader-ready.json'
    try:
        state=json.loads(marker.read_text(encoding='utf-8'))
        return python(app).is_file() and isinstance(state,dict) and state.get('libzim')==VERSION
    except (OSError,ValueError):return False


def validate_cache(folder):
    try:manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):raise setup.SetupError('Empreintes des paquets d’indexation absentes ; préparez de nouveau l’outil.')
    if not isinstance(manifest,dict) or manifest.get('libzim')!=VERSION or not isinstance(manifest.get('files'),list):raise setup.SetupError('Version du paquet d’indexation non valide.')
    expected=set()
    for record in manifest['files']:
        if not isinstance(record,dict):raise setup.SetupError('Empreinte du paquet non valide.')
        name=record.get('path','')
        if not isinstance(name,str):raise setup.SetupError('Nom de paquet non valide.')
        path=folder/name
        if Path(name).name!=name or not name.startswith('libzim-'+VERSION+'-') or not name.endswith('.whl') or name in expected:raise setup.SetupError('Paquet d’indexation non valide.')
        expected.add(name)
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=record.get('bytes') or setup.file_hash(path)!=record.get('sha256'):raise setup.SetupError('Paquet d’indexation modifié ; installation refusée.')
    if not expected or {p.name for p in folder.glob('*.whl')}!=expected:raise setup.SetupError('Liste des paquets d’indexation non conforme.')
    return manifest


def prepare(app,config,*,offline=False,check=lambda:None,force=False):
    if ready(app) and not force:return True
    cache=Path(config['data_dir'])/'tools/search-index-wheels'
    bundled=setup.ROOT/'vendor/search-index'
    if offline and not any(path.is_dir() and list(path.glob('libzim-'+VERSION+'-*.whl')) for path in (cache,bundled)):
        return False
    with locked(destination(app.work,'search-tools-prepare.lock')):
        if ready(app) and not force:return True
        if force:(app.work/'search-tools/reader-ready.json').unlink(missing_ok=True)
        cache.mkdir(parents=True,exist_ok=True)
        trusted={}
        if offline and (cache/'manifest.json').is_file():trusted.update({r['path']:r for r in validate_cache(cache)['files']})
        if bundled.is_dir():
            bundle=validate_cache(bundled)
            for record in bundle['files']:
                source=bundled/record['path'];target=cache/source.name
                shutil.copyfile(source,target)
                if setup.file_hash(target)!=record['sha256']:raise setup.SetupError('Copie du paquet d’indexation non conforme.')
                trusted[source.name]=record
        if offline:
            setup.write_json(cache/'manifest.json',{'libzim':VERSION,'files':list(trusted.values())})
            validate_cache(cache)
        check();venv.EnvBuilder(with_pip=False).create(app.work/'search-tools')
        hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        subprocess.run([str(python(app)),'-m','ensurepip','--upgrade'],check=True,timeout=120,**hidden)
        if not offline:
            check();subprocess.run([str(python(app)),'-m','pip','download','--only-binary=:all:','--no-deps',
                '--dest',str(cache),'-r',str(setup.ROOT/'scripts/requirements-index.txt')],check=True,timeout=300,**hidden)
        records=[{'path':p.name,'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in cache.glob('*.whl') if not p.is_symlink()]
        if not offline:setup.write_json(cache/'manifest.json',{'libzim':VERSION,'files':records})
        validate_cache(cache)
        check();subprocess.run([str(python(app)),'-m','pip','install','--no-index','--find-links',str(cache),
            '-r',str(setup.ROOT/'scripts/requirements-index.txt')],check=True,timeout=300,**hidden)
        setup.write_json(app.work/'search-tools/reader-ready.json',{'libzim':VERSION},private=True)
        return True


def cache_target(app,config,target):
    """Download a pinned wheel for another kit target; never execute that wheel."""
    import re
    platform,separator,version=target.partition(':')
    if not separator or platform not in ('win_amd64','manylinux_2_28_x86_64') or not re.fullmatch(r'3\.(11|12|13|14)',version):
        raise setup.SetupError('Cible attendue : win_amd64:3.13 ou manylinux_2_28_x86_64:3.13, Python 3.11 à 3.14.')
    cache=Path(config['data_dir'])/'tools/search-index-wheels'
    with locked(destination(app.work,'search-tools-prepare.lock')):
        validate_cache(cache)
        hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        subprocess.run([str(python(app)),'-m','pip','download','--only-binary=:all:','--no-deps','--platform',platform,
            '--python-version',version,'--implementation','cp','--abi','cp'+version.replace('.',''),'--dest',str(cache),
            '-r',str(setup.ROOT/'scripts/requirements-index.txt')],check=True,timeout=300,**hidden)
        records=[{'path':p.name,'bytes':p.stat().st_size,'sha256':setup.file_hash(p)} for p in cache.glob('*.whl') if not p.is_symlink()]
        setup.write_json(cache/'manifest.json',{'libzim':VERSION,'files':records})
        validate_cache(cache)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-dir',required=True)
    parser.add_argument('--offline',action='store_true');parser.add_argument('--cache-target',action='append',default=[])
    args=parser.parse_args()
    if args.offline and args.cache_target:parser.error('La préparation de nouvelles cibles demande Internet.')
    app=setup.Installation(args.work_dir);config=app.load()
    if not prepare(app,config,offline=args.offline):raise setup.SetupError('Paquet compatible absent du kit.')
    for target in args.cache_target:cache_target(app,config,target)
