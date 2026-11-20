# Résultats, défauts et reprises

## Jusqu'à la 0.71.0

| Défaut ou cas d'essai | Correction ou résultat observé |
| --- | --- |
| Le lanceur Linux refusait le dossier de réglages privé après la sous-commande. | Les deux positions de `--work-dir` sont acceptées. Les options incompatibles sont refusées avant création des dossiers. |
| La progression YouTube comptait les doublons. | La file compte les vidéos uniques et signale les lignes refusées à part. Deux vidéos présentes ont conservé leur SHA-256 lors du rejeu. |
| Le lot d'outils ne contenait pas le filtrage réseau du Debian minimal. | Ajout de nftables et de ses bibliothèques. Le démon utilise le lot et active le forwarding IPv4 sur la cible dédiée. |
| Le lien vers Python empêchait la recréation du venv ZIM. | Le lanceur appelle le vrai binaire Python et teste un environnement virtuel avant de publier les outils. |
| Un fichier Tcl/Tk du Python extrait gardait l'écriture de groupe. | Les droits d'écriture du groupe et des autres utilisateurs sont retirés. Le contrôle préalable des fichiers exécutés par systemd est conservé. |
| Conflit sur le port HTTPS pendant une mise à jour de la source. | Retour automatique vers la version précédente. Rejeu réussi en désactivant la page temporaire. Le conflit initial est encore ouvert. |
| Coupures injectées pendant l'installation et la copie. | Les partiels sont conservés, repris et vérifiés. Les échecs et le rejeu sont décrits dans les bilans de campagne. |

## Portabilité des outils 0.72.0

Debian 12.15 utilise glibc 2.36 et le noyau 6.1.0-56-amd64. Ubuntu 22.04.5
utilise glibc 2.35 et le noyau 5.15.0-1112-kvm. Les images minimales n'avaient
ni Docker ni nftables. Les binaires Docker, Compose et Python du lot démarrent
sur Debian 12. Le nftables de Debian 13 est refusé par glibc sur Debian 12,
car certaines bibliothèques exigent GLIBC_2.38.

La copie contient désormais des paquets réseau distincts obtenus depuis les
catalogues APT signés des deux distributions. Sur chaque cible hors ligne,
le script installe les outils dans un dossier dédié. Les contrôles ont
exécuté Docker 29.9.3, Compose 5.8.0, Python 3.15.2 et nftables 1.0.6
sur Debian 12 ou 1.0.2 sur Ubuntu 22.04. Chaque démon a démarré vide,
importé une image BusyBox depuis un fichier local et servi une page HTTP.
Le test de connexion TCP vers Internet a échoué avant activation.

La première tentative de démarrage de la VM Ubuntu lisait uniquement les
métadonnées SMBIOS. Le support NoCloud a été attaché en VirtIO avec une
configuration DHCP, puis le compte de recette et le réseau local ont été
disponibles. Ce défaut de préparation de la VM se situe avant SetupSurvie.

## Installation automatique 0.72.0, 20 novembre 2026

Les trois invités QEMU/KVM x86-64 partent d'images de distribution neuves. La
commande Python système a été masquée avant l'installation. Le lanceur a
préparé Docker et ses dépendances dans le dossier de SetupSurvie, sans
installer de démon global. Les lots sélectionnés étaient `health`, `water`
et `books-fr`, avec les cartes préparées par le lanceur.

Sur Debian 13.7, un arrêt forcé pendant le téléchargement de Wikilivres a
laissé 479 199 232 octets en attente. La modification des lots a été refusée.
La même commande a repris le téléchargement puis terminé l'installation. Le
service s'est relancé après redémarrage. Cet essai a commencé avec une version
de travail de la 0.72.0, avant l'ajout des paquets réseau pour les deux
distributions plus anciennes et du réglage d'écoute du contrôleur.

Debian 12.15 et Ubuntu 22.04.5 Minimal ont terminé avec le code d'installation
du commit `c2e5a031e466a40b89be450dec3e465c85da4e97`. Le second lancement
avec les mêmes options a réussi sur les deux cibles. Après un redémarrage
confirmé par le changement de l'identifiant de boot, les deux services
étaient actifs. Le portail, Open WebUI, le contrôleur, la recherche
documentaire, un PDF de l'OMS et une carte PMTiles étaient disponibles.
Le port 11436 du contrôleur écoutait sur la passerelle du réseau Docker.
Les tests intégrés ont également chargé les modèles locaux d'embeddings et
de transcription. La campagne vidéo de Bazzite est décrite dans le bilan
d'installation. La sélection utilisée ici ne contenait pas de liste YouTube.

### Traçabilité du logiciel et des images

- Suite locale du 20 novembre : 1 237 tests exécutés, dont 7 ignorés, aucun
  échec.
- [Exécution GitHub Actions du commit qualifié](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44811954591).
  L'artefact `logiciel-et-empreinte` a été téléchargé et vérifié par
  `sha256sum -c`. SHA-256 de `SetupSurvie-linux-0.72.0.tar.gz` :
  `9552372c3d255a0cad2c0bdd6c7cbbd9aff108108b5ad0c6261c54254e8373b1`.
- [Debian 13 Generic AMD64](https://cloud.debian.org/images/cloud/trixie/latest/) :
  `8909a284450ae3167a63d5b3671ebd4fa1e178a8c6521770c1d5e0f6450288cc`.
- [Debian 12 Generic AMD64](https://cloud.debian.org/images/cloud/bookworm/latest/) :
  `335105aff6e335a561940ce25227449fce5a80c2b0c52004f617ce2f68db19dc`.
- [Ubuntu 22.04 Minimal AMD64](https://cloud-images.ubuntu.com/minimal/releases/jammy/release/) :
  `dac74360a7d0fa6b848d08134e31c0da0615467ffd712575aae65c825882411b`.

## Restauration 0.72.0 sans Internet, 20 novembre 2026

La VM Debian 13 source se trouvait sur le Samsung de 1 To. La copie vérifiée
a été déplacée sur le Crucial de 4 To avant sa présentation aux invités.
Elle occupait 24 626 510 281 octets. Le manifeste source comptait 1 341
fichiers et l'archive Docker regroupait les quatre images du serveur.
SHA-256 du journal de la copie avant activation :
`2123f6fa6f0f8c61b91fcdc10e99af1c83b057aed6df37558423b0abf0064be6`.

La restauration s'est faite dans trois VM distinctes, créées à partir des
images de distribution neuves. Le chemin source était absent. Le réseau
QEMU bloquait la sortie Internet dès le démarrage et le témoin TCP vers
`1.1.1.1:443` échouait avant et après activation. Le dossier de la copie a
été importé depuis un partage en lecture seule, puis démonté avant l'appel
à `transferer-setupsurvie.sh --restaurer-hors-ligne`. Le journal est
passé à `active` sur les trois cibles. Les services utilisaient Docker
29.9.3, Compose 5.8.0, Python 3.13.18 et le nftables de leur distribution.
Les outils de téléchargement et de traitement YouTube étaient disponibles
localement à l'activation.

| Cible | nftables | Lancement et rejeu | Après redémarrage |
| --- | --- | --- | --- |
| Debian 13.7 | 1.1.3 | Réussis | Services actifs, contenus et article « Levain » accessibles |
| Debian 12.15 | 1.0.6 | Réussis | Services actifs, contenus et article « Levain » accessibles |
| Ubuntu 22.04.5 Minimal | 1.0.2 | Réussis | Services actifs, contenus et article « Levain » accessibles |

Après chaque redémarrage, le portail répondait en 0.72.0 sans fonctionnalité
dégradée. Les vérifications ont couvert le contrôleur limité à la passerelle
Docker, Open WebUI, un PDF de l'OMS, la lecture partielle de la carte PMTiles,
la recherche « eau assainissement », puis la recherche et l'ouverture de
« Levain » dans Kiwix. La restauration avec MP4 et pistes VTT reste attestée
par l'essai 0.71.0 effectué sous Debian 13 avec une sélection plus volumineuse.
