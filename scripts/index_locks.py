"""Index writer leases remain effective when a supervisor dies before its workers."""
from contextlib import contextmanager,ExitStack
import hashlib
from pathlib import Path
import re

import setup
from delivery_paths import locked


def worker(root,source):
    key=hashlib.sha256(Path(source).name.encode()).hexdigest()[:24]
    return Path(root)/('worker-'+key+'.lock')


def workers(root):
    result=[]
    for lease in Path(root).glob('worker-*.lock.lease'):
        if not re.fullmatch(r'worker-[a-f0-9]{24}\.lock\.lease',lease.name):
            raise setup.SetupError('Verrou d’indexation non identifiable ; conservez-le pour diagnostic.')
        result.append(lease.with_name(lease.name.removesuffix('.lease')))
    return result


def prepare(root,sources):
    # Register every lease before submitting any task. A delayed orphan must
    # encounter an existing lease held by maintenance, rather than create one
    # after the maintenance process has enumerated and frozen the writers.
    with ExitStack() as stack:
        for path in sorted(set(workers(root))|{worker(root,source) for source in sources}):
            stack.enter_context(locked(path))


@contextmanager
def stopped(root):
    with locked(Path(root)/'operation.lock'),ExitStack() as stack:
        for path in sorted(workers(root)):stack.enter_context(locked(path))
        yield
