#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo 'Usage : sudo ./scripts/install.sh --preparer-systeme DOSSIER [--content-pack LOT]…'
}
if [[ ${1:-} == --help ]]; then usage; exit 0; fi
if [[ $# -eq 0 || $EUID -ne 0 ]]; then usage >&2; exit 2; fi
source /etc/os-release
case "${ID:-}:${VERSION_ID:-}:$(uname -m)" in
    debian:13:x86_64|debian:12:x86_64|ubuntu:22.04:x86_64)
        if [[ ! -d /run/systemd/system ]]; then echo 'systemd doit être démarré.' >&2; exit 1; fi ;;
    *)
        echo 'Ce lanceur prend en charge Debian 12, Debian 13 et Ubuntu 22.04 x86-64.' >&2
        exit 1 ;;
esac

umask 022
base=$(realpath -m -- "$1")
shift
options=("$@")
while [[ $# -gt 0 ]]; do
    if [[ $# -lt 2 || $1 != --content-pack || ! "$2" =~ ^[a-z0-9_-]+$ ]]; then usage >&2; exit 2; fi
    shift 2
done
source_app=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
parent=$(dirname -- "$base")
if [[ "$base" == / || ! -d "$parent" || "$base" == "$source_app" || "$base/" == "$source_app/"* || "$source_app/" == "$base/"* ]]; then
    echo 'Choisissez un dossier dédié, distinct des sources, dans un répertoire existant.' >&2
    exit 1
fi
check="$parent"
while [[ "$check" != / ]]; do
    if [[ -n $(find "$check" -maxdepth 0 \( ! -uid 0 -o -perm /022 \) -print -quit) ]]; then
        echo 'Le dossier parent doit appartenir à root et être protégé en écriture.' >&2
        exit 1
    fi
    check=$(dirname -- "$check")
done

if [[ ! -e "$base" ]]; then
    stage=$(mktemp -d -- "$parent/.setupsurvie-installation.XXXXXXXX")
    mkdir "$stage/application"
    for name in assets deploy docs fixtures pilot portal scripts tests README.md; do
        cp -R --preserve=mode,timestamps -- "$source_app/$name" "$stage/application/"
    done
    cp --preserve=mode,timestamps -- "$source_app"/compose*.yaml "$stage/application/"
    find "$stage/application" -type f -perm /022 -exec chmod go-w -- {} +
    find "$stage/application" -type d -perm /022 -exec chmod go-w -- {} +
    printf 'SetupSurvie Linux installation\n' >"$stage/.installation-linux"
    mv -T --no-clobber -- "$stage" "$base"
    test ! -e "$stage"
fi
marker="$base/.installation-linux"
if [[ -n $(find "$base" -maxdepth 0 \( ! -uid 0 -o -perm /022 \) -print -quit) ]] ||
    [[ -L "$marker" || ! -f "$marker" ]] || ! grep -Fxq 'SetupSurvie Linux installation' "$marker"; then
    echo 'Dossier existant non reconnu. Choisissez un dossier neuf.' >&2
    exit 1
fi
if [[ -L "$base/install-linux.lock" ]]; then echo 'Verrou non valide.' >&2; exit 1; fi
exec 9>"$base/install-linux.lock"
if ! flock -n 9; then echo 'L’installation est déjà en cours.' >&2; exit 1; fi
application="$base/application"
tools="$base/outils-linux"
catalog="$application/deploy/linux-offline-installers.txt"
if [[ ! -e "$tools" && ! -L "$tools" ]]; then
    command -v curl >/dev/null || { echo 'curl et les certificats HTTPS sont requis pour la première préparation.' >&2; exit 1; }
    cache="$base/data/tools/linux-offline-installers"
    mkdir -p "$cache"
    while read -r expected size name url; do
        case "$name" in docker.tar.gz|docker-compose|python-3.13.tar.gz|*.deb) ;; *) continue;; esac
        file="$cache/$name"
        mkdir -p -- "$(dirname -- "$file")"
        if [[ -e "$file" ]]; then
            actual=$(sha256sum "$file")
            if [[ ${actual%% *} != "$expected" ]]; then echo "Empreinte incorrecte : $file" >&2; exit 1; fi
            continue
        fi
        printf 'Téléchargement de %s…\n' "$name"
        curl --fail --location --silent --show-error --retry 3 --proto '=https' --proto-redir '=https' \
            --connect-timeout 20 --max-time 900 --max-filesize "$size" --output "$file.part" -- "$url"
        actual=$(sha256sum "$file.part")
        if [[ ${actual%% *} != "$expected" ]]; then echo "Empreinte incorrecte : $name" >&2; exit 1; fi
        mv -- "$file.part" "$file"
    done <"$catalog"
    printf 'python-3.13.tar.gz\n' >"$cache/python-archive.txt"
    "$application/scripts/installer-outils-linux-hors-ligne.sh" "$base/data" "$tools"
fi
if [[ -L "$tools" || -L "$tools/bin/python3" || ! -x "$tools/bin/python3" ]] ||
    [[ -n $(find "$tools" \( ! -uid 0 -o \( ! -type l -perm /022 \) \) -print -quit) ]] ||
    ! cmp -s -- "$tools/.setupsurvie-restauration" "$catalog"; then
    echo 'Le dossier des outils ne correspond pas à cette installation.' >&2
    exit 1
fi
exec "$tools/bin/python3" "$application/scripts/linux_auto_install.py" "$base" "${options[@]}"
