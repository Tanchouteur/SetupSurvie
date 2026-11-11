"""Path and operation-lock guards for installation and software updates.

Kept independent from the content downloader so its catalogue can evolve separately.
"""
from contextlib import contextmanager
import os
from pathlib import Path, PurePosixPath
import re
import setup


def destination(root,relative):
    if not isinstance(relative,str) or any(c in relative for c in '\\:\x00<>"|?*'):
        raise setup.SetupError('Chemin de contenu non valide.')
    parts=PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or any(not p or p in ('.','..') or p.endswith((' ','.')) or re.fullmatch(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',p) for p in relative.split('/')):
        raise setup.SetupError('Chemin de contenu non valide.')
    path=root.joinpath(*parts)
    for parent in [path,*path.parents]:
        if parent==root.parent:break
        if parent.is_symlink():raise setup.SetupError('Lien symbolique refusé : '+relative)
    if not path.resolve().is_relative_to(root.resolve()):raise setup.SetupError('Chemin externe refusé.')
    return path


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:path.mkdir()
    except FileExistsError:raise setup.SetupError('Une opération est en cours ou a été interrompue : '+str(path))
    owner=path/'owner.json'
    try:
        import discovery
        setup.write_json(owner,{'pid':os.getpid(),'identity':discovery.identity(os.getpid())},private=True)
        yield
    finally:
        owner.unlink(missing_ok=True);path.rmdir()
