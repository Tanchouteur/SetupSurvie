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

## Défauts injectés et rejeu avec l'archive de distribution

Sur une quatrième VM de restauration Debian 12.15, un octet ajouté au
fichier `docker-compose` a déclenché le refus « Empreinte incorrecte :
docker-compose. Aucun outil installé. » Le rétablissement de ce fichier a
permis d'extraire les outils. Le fonds et le manifeste local du modèle étant
absents, le lanceur a de nouveau refusé d'activer la copie, cette fois en
indiquant le chemin du manifeste absent. Le stockage Docker dédié est resté
absent lors des deux tentatives et aucun dockerd n'a démarré.

Sur un autre Debian 13.7 vierge, l'archive Linux téléchargée depuis la CI a
été vérifiée à nouveau, puis extraite. Le lanceur s'est arrêté avant
l'initialisation avec « Port 8080 occupé ». Une fois le port libre, le même
lanceur a terminé l'installation. Le portail, la recherche, le PDF, la carte
et la collection Wikilivres ont passé les vérifications. Deux lignes
identiques configurées pour [Sintel](https://www.youtube.com/watch?v=eRsGyueVLvQ)
ont soumis une seule vidéo à la file automatique. Le MP4 de 49 150 125
octets a répondu en HTTP 206. La transcription anglaise a été publiée en
WebVTT et la recherche « traveling alone » a retrouvé le passage parlé.
La traduction française a échoué avec le modèle `gpt-oss:20b` sur cet
invité de 6 Gio sans swap. Ollama a signalé une allocation d'environ 9,7 Go
impossible à obtenir. La piste anglaise est restée disponible. La machine
minimale est donc qualifiée pour le téléchargement, la transcription et la
recherche de cette vidéo. La traduction automatique sur cette configuration
reste à valider.

## Correction 0.73.0 pour les installations avec peu de mémoire

La première installation automatique choisit le profil Qwen3 1,7B sans
réflexion lorsque la RAM détectée est inférieure à 16 Gio. Le réglage
enregistré se retrouve dans Compose et dans le profil rapide utilisé par la
traduction des sous-titres. Cette évolution du choix de modèle justifie le
passage à la version mineure 0.73.0.

Les tests simulés couvrent la sélection sur 6 et 32 Gio, la conservation du
modèle en cas de reprise, la configuration transmise au service et la
publication d'une piste française avec une réponse Ollama simulée.
L'essai de traduction réelle sur une VM de 6 Gio reste à rejouer avec le
nouveau modèle. L'adaptation d'une copie provenant d'une machine plus
puissante vers une cible moins dotée en RAM reste à qualifier. [Fiche du
modèle](https://ollama.com/library/qwen3:1.7b-q4_K_M)

Ces deux points ont été repris pendant la [confirmation sur deux SSD](#confirmation-sur-deux-ssd-physiques).

## Conservation des modèles et adaptation à la cible en 0.74.0

L'installation automatique prépare maintenant GPT-OSS 20B et Qwen3 1,7B.
Les profils GPT-OSS restent disponibles. Une restauration CPU peut affecter
le modèle compact déjà copié au profil rapide d'une machine à faible mémoire.
Cette nouvelle option de restauration justifie la version mineure 0.74.0.

Les scénarios simulés contrôlent le rejeu de la préparation et la présence
des deux manifestes sur la cible, y compris le lien relatif du manifeste Ollama
v2. La restauration et la traduction réelles avec ces deux modèles restent à
rejouer sur la VM de 6 Gio.

Sur la révision `b4b3026`, les onze tâches de la CI ont réussi. La tâche
Windows a exécuté 1 244 tests, vérifié les lanceurs PowerShell et recréé les
outils YouTube après copie sans accès réseau. L'archive Linux de cette
exécution a été téléchargée et son SHA-256 vérifié
(`6ec69669836df13880fa732dc5aaf63cbebc4691f6c2d4808413520277a3b497`).
Ces vérifications complètent la recette sur machine du dossier.
[Exécution GitHub Actions](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44820180459)

## Confirmation sur deux SSD physiques

La recette 0.76.0 s'est déroulée sur le PC Bazzite de Louis, dans deux invités
Debian 13 x86-64. Le disque système de l'invité source était sur le Crucial
CT4000P3PSSD8 de 4 To. Le support de copie et le disque système de
l'invité cible étaient sur le Samsung 990 PRO de 1 To. Le support était
présenté comme un disque virtio indépendant. L'image Debian correspondait au
SHA-256 indiqué plus haut pour Debian 13 Generic AMD64.

- L'archive Linux 0.76.0 du commit `0948298` était identique à l'archive
  reconstruite localement. SHA-256
  `ed907987b335e757f07234bec531c23f3252db0bb74891581381d5b3dc382288`.
  [Exécution GitHub Actions](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44878918985)
- L'installation depuis cette archive partait d'un invité sans Docker, Compose,
  nftables ni commande Python système. Les lots santé, eau et livres français
  ont été installés. Le rejeu du lanceur et le démarrage suivant ont réussi.
- La file a téléchargé et indexé automatiquement le film Blender *Sintel*.
  La recherche l'a retrouvé par son titre, le MP4 a répondu en HTTP 206 et
  la piste anglaise WebVTT était lisible. Une courte vidéo de recette avec
  deux sous-titres anglais contrôlait séparément la traduction.
- Le lanceur a vérifié 1 404 fichiers et 21 269 205 482 octets inventoriés.
  La copie complète, dont l'archive Docker, occupait 26 362 965 980 octets.
  SHA-256 du journal avant activation
  `c16955c055ebb8e618a219472ed209dcf3e6a309188581dc76bf5d1ed81d7412`.
- L'invité de restauration avait 6 Gio de RAM et aucun Docker, Compose,
  nftables ou Python utilisable globalement. Il a importé le dossier depuis
  le support monté en lecture seule. L'invité source a été arrêté et le
  support de transfert a été détaché avant activation. Le chemin source
  était absent et la sortie Internet était bloquée par QEMU. Le témoin TCP
  vers `1.1.1.1:443` échouait. Le lanceur a terminé en 2 min 24 s.
- Le démon Docker dédié a démarré avec les outils de la copie. Le portail,
  Open WebUI, le PDF de l'OMS, la carte PMTiles, l'article Wikilivres
  « Levain », *Sintel* et sa piste anglaise ont été lus sur la cible.
  Les empreintes Ollama de GPT-OSS 20B et Qwen3 1,7B étaient identiques
  entre les invités. La cible a choisi Qwen3 pour son profil rapide et
  GPT-OSS est resté disponible dans les profils.

### Reprise d'une traduction sur la cible

Avec 0.76.0, Qwen3 1,7B a recopié l'anglais pour la vidéo de recette.
Le contrôle qualité a arrêté le travail à 0 segment publié sur 2. La
piste anglaise est restée accessible. La correction 0.76.1 transmet la
consigne de traduction au modèle compact avec les segments. Cette
correction compatible justifie l'incrément de version de maintenance.
Le paquet logiciel a été appliqué sur la cible isolée avec le lanceur
de mise à jour existant.

La reprise du même travail a publié les deux segments. Le contrôle a
retrouvé la piste française par son texte, vérifié la valeur « 17 mm »
dans les deux segments et relu l'horodatage attendu. Le rejeu du lanceur
de restauration a réussi. Au redémarrage suivant, Docker et SetupSurvie
étaient actifs. La sortie WAN restait bloquée, le disque de support
était absent et la lecture de la vidéo, les pistes, le fonds documentaire
et les empreintes des deux modèles ont été vérifiés de nouveau.
[Relevés de la confirmation](preuves-ssd-0.76.tsv)

Cette campagne vérifie la traduction française du court document de
recette, et le téléchargement automatique, l'indexation et la piste
anglaise de *Sintel*. La restauration était destinée à un Debian déjà
installé. Les résultats de Debian 12 et Ubuntu 22.04 restent ceux de
la campagne 0.72.0. La campagne 0.76 a utilisé Bazzite comme hôte des VM.
