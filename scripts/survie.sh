#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10+ est requis. Voir docs/14-installation.md.' >&2
  exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || {
  echo 'Python 3.10+ est requis.' >&2; exit 1;
}
exec python3 "$SCRIPT_DIR/setup.py" "$@"
