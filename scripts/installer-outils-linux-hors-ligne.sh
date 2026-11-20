#!/usr/bin/env bash
# Run from the copied application. This bootstrap needs Bash and core utilities.
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo 'Usage : installer-outils-linux-hors-ligne.sh DOSSIER_DONNÉES NOUVEAU_DOSSIER_OUTILS' >&2
    exit 2
fi
if [[ "$(uname -s):$(uname -m)" != Linux:x86_64 ]]; then
    echo 'Ces installateurs sont destinés à Linux x86-64 avec glibc.' >&2
    exit 1
fi

source_dir="$1/tools/linux-offline-installers"
target="$2"
catalog="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../deploy" && pwd)/linux-offline-installers.txt"
if [[ -e "$target" || -L "$target" ]]; then
    echo 'Choisissez un nouveau dossier pour les outils. Le dossier existant est conservé.' >&2
    exit 1
fi
if [[ ! -f "$source_dir/python-archive.txt" || -L "$source_dir/python-archive.txt" ]]; then
    echo 'Installateurs hors ligne incomplets. Préparez-les sur la source avant la copie.' >&2
    exit 1
fi
IFS= read -r python_archive <"$source_dir/python-archive.txt"
if [[ ! "$python_archive" =~ ^python-3\.1[1-5]\.tar\.gz$ ]]; then
    echo 'Archive Python non reconnue.' >&2
    exit 1
fi

mapfile -t network_packages < <(awk '$3 ~ /^[[:alnum:]_+.-]+[.]deb$/ {print $3}' "$catalog")
for name in docker.tar.gz docker-compose "$python_archive" "${network_packages[@]}"; do
    expected=$(awk -v name="$name" '$3==name {print $1; exit}' "$catalog")
    file="$source_dir/$name"
    if [[ ! "$expected" =~ ^[0-9a-f]{64}$ || ! -f "$file" || -L "$file" ]]; then
        printf 'Installateur absent ou inconnu : %s\n' "$name" >&2
        exit 1
    fi
    actual=$(sha256sum -- "$file")
    if [[ ${actual%% *} != "$expected" ]]; then
        printf 'Empreinte incorrecte : %s. Aucun outil installé.\n' "$name" >&2
        exit 1
    fi
done

parent=$(dirname -- "$target")
stage=$(mktemp -d -- "$parent/.setupsurvie-outils.XXXXXXXX")
trap 'printf "Préparation interrompue. Dossier temporaire conservé : %s\n" "$stage" >&2' ERR
mkdir -p "$stage/bin" "$stage/python" "$stage/docker-cli/cli-plugins"
tar -xzf "$source_dir/docker.tar.gz" --no-same-owner --strip-components=1 -C "$stage/bin"
tar -xzf "$source_dir/$python_archive" --no-same-owner --strip-components=1 -C "$stage/python"
ln -s ../python/bin/python3 "$stage/bin/python3"
install -m 755 -- "$source_dir/docker-compose" "$stage/docker-cli/cli-plugins/docker-compose"
if [[ -r /etc/os-release ]] && ! command -v nft >/dev/null; then
    # These Debian packages remain inside the tools directory.
    source /etc/os-release
    if [[ "${ID:-}:${VERSION_ID:-}" == debian:13 ]]; then
        mkdir "$stage/nftables"
        for name in "${network_packages[@]}"; do
            dpkg-deb --extract "$source_dir/$name" "$stage/nftables"
        done
        cat >"$stage/bin/nft" <<'NFT'
#!/usr/bin/env bash
set -euo pipefail
nft_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../nftables" && pwd)"
export LD_LIBRARY_PATH="$nft_root/usr/lib/x86_64-linux-gnu"
exec "$nft_root/usr/sbin/nft" "$@"
NFT
        chmod 755 "$stage/bin/nft"
        "$stage/bin/nft" --version
    fi
fi
cat >"$stage/environnement.sh" <<'ENV'
# Charger dans Bash avant de démarrer Docker ou d'utiliser les lanceurs.
survie_tools_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$survie_tools_root/bin:$survie_tools_root/python/bin:$PATH"
export DOCKER_CONFIG="$survie_tools_root/docker-cli"
unset survie_tools_root
ENV
(
    source "$stage/environnement.sh"
    python3 --version
    docker --version
    docker compose version
)
mv -T --no-clobber -- "$stage" "$target"
test ! -e "$stage"
printf 'Outils prêts dans %s. Chargez environnement.sh dans Bash.\n' "$target"
