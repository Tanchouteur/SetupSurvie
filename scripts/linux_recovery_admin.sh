#!/usr/bin/env bash
# Graphical authorization enters here. The same entry point can resume a failed operation.
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
die() { printf '%s\n' "$*" >&2; exit 1; }
[[ $EUID == 0 ]] || die 'Autorisation administrateur nécessaire.'
source /etc/os-release
case "${ID:-}:${VERSION_ID:-}:$(uname -m)" in
    debian:12:x86_64|debian:13:x86_64|ubuntu:22.04:x86_64) ;;
    *) die 'Choisissez un PC Debian 12, Debian 13 ou Ubuntu 22.04 (64 bits).';;
esac
[[ -d /run/systemd/system ]] || die 'Le système doit avoir démarré normalement.'
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
action=${1:-}
case "$action:$#" in
    install:4)
        source_base=$(realpath -e -- "$2")
        dest=$3
        [[ $4 == yes || $4 == no ]] || die 'Choix du point de restauration invalide.'
        [[ -f "$source_base/transfer.json" ]] || die 'Ce support ne contient pas de copie SetupSurvie.'
        ;;
    point:2|restore:2) dest=$2; source_base=$2 ;;
    *) die 'Action inconnue.' ;;
esac
[[ "$dest" == /* && "$dest" != / && "$dest" != */ && "$dest" != *$'\n'* && "$dest" != *$'\r'* ]] ||
    die 'Choisissez un dossier d’installation dédié.'
base=$(realpath -m -- "$dest")
[[ "$base" == "$dest" ]] || die 'Le chemin doit désigner un dossier sans lien symbolique.'
parent=$(dirname -- "$base")
[[ -d "$parent" ]] || die 'Choisissez un disque déjà monté et un dossier parent existant.'
for directory in "$parent" "$base"; do
    while [[ "$directory" != / ]]; do
        if [[ -e "$directory" && ( ! -d "$directory" || -L "$directory" ||
                -n $(find "$directory" -maxdepth 0 \( ! -uid 0 -o -perm /022 \) -print -quit) ) ]]; then
            die 'Choisissez un dossier système protégé, par exemple /srv ou un disque monté par le système.'
        fi
        directory=$(dirname -- "$directory")
    done
done
if [[ "$action" == install && ( "$source_base/" == "$base/"* || "$base/" == "$source_base/"* ) ]]; then
    die 'Choisissez une destination distincte du dossier de secours.'
fi
if [[ "$action" == install && $(stat -c %d -- "$source_base") == $(stat -c %d -- "$parent") ]]; then
    die 'Choisissez un disque différent du SSD de secours.'
fi
recovery="$parent/.$(basename -- "$base")-secours"
[[ ! -L "$recovery" ]] || die 'Dossier de secours invalide.'
mkdir -p -- "$recovery"
[[ $(stat -c '%u:%a' -- "$recovery") == 0:700 ]] || die 'Dossier de secours déjà présent et non protégé.'
[[ ! -L "$recovery/lancement.lock" ]] || die 'Verrou de secours invalide.'
exec 9>"$recovery/lancement.lock"
flock -n 9 || die 'Une opération SetupSurvie est déjà en cours.'
runtime="$recovery/entretien"
if [[ ! -d "$runtime" ]]; then
    stage=$(mktemp -d -- "$recovery/.entretien.XXXXXXXX")
    application=$(dirname -- "$script_dir")
    if [[ -d "$application/application/scripts" ]]; then
        application="$application/application"
    fi
    [[ -f "$application/scripts/linux_recovery.py" ]] ||
        die 'Rouvrez le lanceur depuis le SSD de secours pour initialiser l’entretien.'
    # Keep the maintenance application separate. It must work if SetupSurvie cannot start.
    mkdir -- "$stage/application"
    for name in scripts pilot deploy; do
        cp -R --no-preserve=ownership -- "$application/$name" "$stage/application/"
    done
    cp -- "$application"/compose*.yaml "$stage/application/"
    chmod -R go-w -- "$stage/application"
    "$stage/application/scripts/installer-outils-linux-hors-ligne.sh" "$source_base/data" "$stage/outils-linux"
    mv -T -- "$stage" "$runtime"
    sync -f -- "$recovery"
fi
export PYTHONDONTWRITEBYTECODE=1
source "$runtime/outils-linux/environnement.sh"
exec "$runtime/outils-linux/bin/python3" "$runtime/application/scripts/linux_recovery.py" "$recovery" "$@"
