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
