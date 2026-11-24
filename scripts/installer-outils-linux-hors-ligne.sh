#!/usr/bin/env bash
# Run from the copied application. This bootstrap needs Bash and core utilities.
set -euo pipefail

python_only=no
if [[ ${1:-} == --python-seul ]]; then
    python_only=yes
    shift
fi
if [[ $# -ne 2 ]]; then
    echo 'Usage : installer-outils-linux-hors-ligne.sh [--python-seul] DOSSIER_DONNÉES NOUVEAU_DOSSIER_OUTILS' >&2
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

network_packages=()
if [[ "$python_only" == no && -r /etc/os-release ]]; then
    source /etc/os-release
    case "${ID:-}:${VERSION_ID:-}" in
        debian:13) prefix= ;;
        debian:12) prefix=debian12/ ;;
        ubuntu:22.04) prefix=ubuntu2204/ ;;
        *) prefix= ;;
    esac
    case "${ID:-}:${VERSION_ID:-}" in
        debian:13|debian:12|ubuntu:22.04)
            mapfile -t network_packages < <(awk -v p="$prefix" '
                index($3,p)==1 && substr($3,length(p)+1) ~ /^[[:alnum:]_+.-]+[.]deb$/ {print $3}
            ' "$catalog")
            ;;
    esac
fi
if [[ "$python_only" == yes ]]; then
    archives=("$python_archive")
else
    archives=(docker.tar.gz docker-compose "${python_archive}" "${network_packages[@]}")
fi
for name in "${archives[@]}"; do
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
mkdir -p "$stage/bin" "$stage/python"
if [[ "$python_only" == no ]]; then
    mkdir -p "$stage/docker-cli/cli-plugins"
    tar -xzf "$source_dir/docker.tar.gz" --no-same-owner --strip-components=1 -C "$stage/bin"
    install -m 755 -- "$source_dir/docker-compose" "$stage/docker-cli/cli-plugins/docker-compose"
fi
tar -xzf "$source_dir/$python_archive" --no-same-owner --strip-components=1 -C "$stage/python"
cat >"$stage/bin/python3" <<'PYTHON'
#!/usr/bin/env bash
set -euo pipefail
python_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../python" && pwd)"
exec "$python_root/bin/python3" "$@"
PYTHON
chmod 755 "$stage/bin/python3"
if [[ ${#network_packages[@]} -gt 0 ]] && ! PATH=/usr/sbin:/usr/bin:/sbin:/bin command -v nft >/dev/null; then
    mkdir "$stage/nftables"
    for name in "${network_packages[@]}"; do
        dpkg-deb --extract "$source_dir/$name" "$stage/nftables"
    done
    cat >"$stage/bin/nft" <<'NFT'
#!/usr/bin/env bash
set -euo pipefail
nft_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../nftables" && pwd)"
export LD_LIBRARY_PATH="$nft_root/usr/lib/x86_64-linux-gnu:$nft_root/lib/x86_64-linux-gnu"
for executable in "$nft_root/usr/sbin/nft" "$nft_root/sbin/nft"; do
    if [[ -x "$executable" ]]; then exec "$executable" "$@"; fi
done
echo 'Exécutable nftables absent.' >&2
exit 1
NFT
    chmod 755 "$stage/bin/nft"
    "$stage/bin/nft" --version
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
    python3 -m venv --without-pip "$stage/python-probe"
    "$stage/python-probe/bin/python" -c 'import encodings, ensurepip'
    python3 -c 'import shutil, sys; shutil.rmtree(sys.argv[1])' "$stage/python-probe"
    if [[ "$python_only" == no ]]; then
        docker --version
        docker compose version
    fi
)
# A root service must never load a file that another user can change.
find "$stage" \( -type f -o -type d \) -perm /022 -exec chmod go-w -- {} +
install -m 644 -- "$catalog" "$stage/.setupsurvie-restauration"
mv -T --no-clobber -- "$stage" "$target"
test ! -e "$stage"
printf 'Outils prêts dans %s. Chargez environnement.sh dans Bash.\n' "$target"
