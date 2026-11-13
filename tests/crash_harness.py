"""Kill only our disposable child process, never the host or a real service."""
from pathlib import Path
import subprocess
import sys
import time


def crash_after_ready(code, arguments, ready, while_alive=None):
    ready = Path(ready)
    ready.unlink(missing_ok=True)
    repo = Path(__file__).resolve().parents[1]
    prefix = """import sys; sys.path.insert(0, sys.argv[1] + '/scripts'); import setup
def reject_external(*args, **kwargs):
    raise AssertionError('External service commands are forbidden in crash fixtures.')
setup.run = reject_external
"""
    process = subprocess.Popen([sys.executable, '-X', 'utf8', '-u', '-c', prefix + code,
                                str(repo), *map(str, arguments)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 15
        while not ready.exists():
            if process.poll() is not None:
                raise AssertionError(process.stderr.read().decode('utf-8', errors='replace'))
            if time.monotonic() > deadline:
                raise AssertionError('Child did not reach the crash point.')
            time.sleep(.01)
        if while_alive:
            while_alive(process)
        process.kill()
        process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        process.stderr.close()
