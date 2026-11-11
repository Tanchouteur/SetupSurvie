#!/usr/bin/env bash
# Enable local-name resolution without reconnecting Wi-Fi or changing IP addresses.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
    echo 'Cette correction du résolveur Linux nécessite sudo.' >&2
    exit 1
fi
interface="${1:-$(ip -4 route show default | awk '/dev/ {for(i=1;i<=NF;i++) if($i=="dev") {print $(i+1);exit}}')}"
if [[ -z "$interface" ]]; then echo 'Aucune interface réseau active.' >&2; exit 1; fi
connection_uuid="$(nmcli -g GENERAL.CON-UUID device show "$interface")"
if [[ -z "$connection_uuid" || "$connection_uuid" == -- ]]; then echo 'Connexion NetworkManager introuvable.' >&2; exit 1; fi
install -d -m 755 /etc/systemd/resolved.conf.d
config=/etc/systemd/resolved.conf.d/70-setupsurvie-mdns.conf
if [[ -e "$config" ]] && ! cmp -s "$config" <(printf '[Resolve]\nMulticastDNS=resolve\n'); then
    echo "Le fichier $config existe avec un autre contenu ; modification refusée." >&2
    exit 1
fi
printf '[Resolve]\nMulticastDNS=resolve\n' > "$config"
chmod 644 "$config"
nmcli connection modify "$connection_uuid" connection.mdns 1
systemctl restart systemd-resolved
resolvectl mdns "$interface" resolve
resolvectl flush-caches
# A resolver querying another mDNS responder on its own host can miss the
# locally published alias. Give the server a stable loopback alias as well.
if ! awk '$1 !~ /^#/ {for(i=2;i<=NF;i++) if($i=="survie.local") found=1} END {exit !found}' /etc/hosts; then
    printf '\n127.0.0.1 survie.local # SetupSurvie local access\n' >> /etc/hosts
fi
resolvectl flush-caches
echo 'Configuration appliquée ; vérification de survie.local. Le Wi-Fi et l’adresse IP restent en place.'
resolvectl query survie.local
