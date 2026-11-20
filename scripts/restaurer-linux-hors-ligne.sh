#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || $EUID -ne 0 ]]; then
    echo 'Sur la cible, lancez sudo restaurer-linux-hors-ligne.sh DOSSIER_DE_LA_COPIE.' >&2
    exit 2
fi
source /etc/os-release
if [[ "$(uname -m)" != x86_64 || "${ID:-}:${VERSION_ID:-}" != debian:13 || ! -d /run/systemd/system ]]; then
    echo 'La restauration automatique demande Debian 13 x86-64 avec systemd.' >&2
    exit 1
fi

base=$(realpath -e -- "$1")
application="$base/application"
if [[ "$(realpath -e -- "$(dirname -- "${BASH_SOURCE[0]}")/..")" != "$application" || ! -f "$base/transfer.json" ]]; then
    echo 'Ouvrez le lanceur depuis le dossier de la copie à restaurer.' >&2
    exit 1
fi
# System services execute from this directory after every reboot.
for dir in "$base" "$base/private"; do
    if [[ -L "$dir" || ! -d "$dir" ]]; then
        echo 'Dossier de restauration lié ou absent.' >&2
        exit 1
    fi
done
parent="$base"
while [[ "$parent" != / ]]; do
    if [[ -n $(find "$parent" -maxdepth 0 \( ! -uid 0 -o -perm /022 \) -print -quit) ]]; then
        echo 'Placez la copie dans un dossier système appartenant à root et protégé en écriture.' >&2
        exit 1
    fi
    parent=$(dirname -- "$parent")
done
if [[ -L "$base/restore-linux.lock" ]]; then
    echo 'Verrou de restauration non valide.' >&2
    exit 1
fi
exec 9>"$base/restore-linux.lock"
if ! flock -n 9; then
    echo 'Une restauration est déjà en cours dans ce dossier.' >&2
    exit 1
fi

tools="$base/outils-linux"
receipt="$tools/.setupsurvie-restauration"
if [[ -e "$tools" || -L "$tools" ]]; then
    if [[ -L "$tools" || -L "$receipt" || ! -f "$receipt" ]] ||
        [[ -n $(find "$tools" \( ! -uid 0 -o \( ! -type l -perm /022 \) \) -print -quit) ]] ||
        ! cmp -s -- "$receipt" "$application/deploy/linux-offline-installers.txt"; then
        echo 'Le dossier des outils existe déjà et ne correspond pas à cette restauration.' >&2
        exit 1
    fi
else
    "$application/scripts/installer-outils-linux-hors-ligne.sh" "$base/data" "$tools"
fi
source "$tools/environnement.sh"
exec "$tools/bin/python3" "$application/scripts/linux_offline_restore.py" "$base"
