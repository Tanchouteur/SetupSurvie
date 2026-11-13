"""Durable publication of small state files; no promise about faulty hardware.

Windows supports file fsync, but Python cannot fsync a directory there. Keep
that limit explicit instead of claiming that a rename alone survives power loss.
"""
import os
from pathlib import Path
import tempfile


def sync_directory(path):
    if os.name == 'nt':
        return
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_file(path):
    with Path(path).open('rb+' if os.name == 'nt' else 'rb') as stream:
        os.fsync(stream.fileno())


def mkdir(path):
    """Persist each newly allocated directory entry, including its ancestors."""
    path = Path(path)
    missing = []
    parent = path
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    if not parent.is_dir():raise NotADirectoryError(str(parent))
    for directory in reversed(missing):
        try:directory.mkdir()
        except FileExistsError:
            if not directory.is_dir():raise
        sync_directory(directory.parent)


def publish(source, target):
    source, target = Path(source), Path(target)
    os.replace(source, target)
    sync_directory(target.parent)
    if source.parent != target.parent:
        sync_directory(source.parent)


def write_bytes(path, body, *, private=False):
    path = Path(path)
    mkdir(path.parent)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.pending', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            if os.name != 'nt':
                os.fchmod(stream.fileno(), 0o600 if private else 0o644)
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        publish(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sync_tree(root, *, sync_files=True):
    root = Path(root)
    directories = [root]
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Lien symbolique refusé pendant la synchronisation.')
        if path.is_file() and sync_files:
            sync_file(path)
        elif path.is_dir():
            directories.append(path)
    for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        sync_directory(path)
    sync_directory(root.parent)
