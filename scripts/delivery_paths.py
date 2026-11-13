"""Path and operation-lock guards for installation and software updates.

Kept independent from the content downloader so its catalogue can evolve separately.
"""
from contextlib import contextmanager
import os
import json
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
    """An OS lease survives as a file; the OS releases ownership on process death.

    Never unlink the lease file: another process could still hold its inode.
    Old directory locks are reclaimed only when their owner is demonstrably gone.
    """
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    lease=path.with_name(path.name+'.lease')
    if path.is_symlink() or lease.is_symlink():raise setup.SetupError('Lien de verrou refusé.')
    with lease.open('a+b') as stream:
        if os.name!='nt':os.fchmod(stream.fileno(),0o600)
        if os.fstat(stream.fileno()).st_size==0:
            stream.write(b'\0');stream.flush()
        stream.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            raise setup.SetupError('Une opération est en cours : '+str(path)) from exc
        try:
            reclaim_legacy_lock(path)
            yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def process_alive(pid):
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return ctypes.get_last_error()!=87  # Access denied is not proof of death.
        try:
            code=wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):return True
            return code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    except PermissionError:return True
    return True


def reclaim_legacy_lock(path):
    if not path.exists():return
    owner=path/'owner.json'
    try:
        if owner.is_symlink():raise ValueError()
        value=json.loads(owner.read_text(encoding='utf-8'))
        pid=value['pid']
        if type(pid) is not int or not 0<pid<=0x7fffffff or not value.get('identity'):raise ValueError()
        import discovery
        identity=discovery.identity(pid)
        if process_alive(pid) and (identity is None or identity==value['identity']):
            raise setup.SetupError('Une opération est en cours : '+str(path))
        if set(p.name for p in path.iterdir())!={'owner.json'}:raise ValueError()
    except (OSError,ValueError,KeyError,TypeError):
        raise setup.SetupError('Une opération précédente a laissé un verrou non identifiable, conservé : '+str(path))
    owner.unlink();path.rmdir()
