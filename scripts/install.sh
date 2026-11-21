#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ ${1:-} == --preparer-systeme ]]; then
    shift
    exec "$SCRIPT_DIR/installer-systeme-linux.sh" "$@"
fi
exec "$SCRIPT_DIR/survie.sh" install --target linux "$@"
