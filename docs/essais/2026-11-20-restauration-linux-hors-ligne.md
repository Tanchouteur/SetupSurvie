# Installation neuve et restauration Linux hors ligne — 20 novembre 2026

Recette demandée par Louis sur Bazzite. La source se trouve sur le SSD Crucial
de 4 To. Le support et le disque virtuel de la cible résident sur l'autre SSD,
le Samsung de 1 To. La cible est une VM Debian 13.7 x86-64 sur KVM, avec 6 Gio de
RAM, 4 vCPU et un disque virtuel de 150 Gio en allocation dynamique. Louis a
validé la simulation en VM pour la restauration.

## Nouveau départ et préparation

L'installation 0.69.6 a été supprimée, puis relancée depuis des dossiers de
réglages et de données absents et un moteur Docker sans images. Le lanceur
a terminé. La nouvelle exigence de Louis sur les installateurs a ensuite
conduit à la 0.70.0. Le dossier de cette première relance et le stockage
Docker ont été supprimés pour repartir une nouvelle fois de zéro avec la
version qui prépare les outils. Les clones, notes et applications hors
SetupSurvie ont été préservés.

La 0.70.0 est une évolution compatible. Elle télécharge, contrôle et conserve
des archives figées de Docker Engine, Compose et Python, ainsi que les
paquets réseau de Debian 13. L'archive Python correspond à la version mineure
de la source pour permettre de réutiliser les roues déjà préparées.
L'activation détecte le mode du Docker cible. Ce réglage peut changer quand
une source rootless est restaurée sur un démon système.

Le démarrage préliminaire du démon statique sur Debian minimal a trouvé
deux dépendances de l'environnement. L'absence de la commande `nft` empêchait
l'initialisation nftables. Le bootstrap a été complété avec cet outil et
ses bibliothèques dans le dossier des outils, puis le routage IPv4 a été
activé dans la VM. Docker 29.9.3 a alors créé un réseau depuis les seuls
fichiers locaux. Le préfixe et le stockage Docker préliminaires ont été retirés
de la cible. Le répertoire de la source Bazzite est absent dans l'invité.
QEMU refuse les connexions sortantes par `restrict=on`, avec une redirection
SSH limitée à la boucle locale de l'hôte. Une connexion TCP directe à une
adresse Internet a échoué depuis la VM.

La suite 0.70.0 a exécuté 1 226 tests, dont 7 ignorés, sans échec. Les cas
ciblés couvrent le choix de la version mineure et le refus d'un installateur
altéré avant toute extraction.

## Installation et copie réelles

La 0.70.0 termine l'installation en ligne sur Bazzite. Les 17 ressources
de départ et les 204 730 187 octets d'installateurs ont été revérifiés. Les
deux premières archives rejoignent la recherche. La liste YouTube de la
recette est soumise automatiquement et les deux pistes françaises
deviennent recherchables. Le compteur affiche 3 / 3 après traitement d'une
vidéo indisponible et écarte le doublon et l'adresse de liste de lecture.

La copie vers le Samsung est interrompue par SIGKILL avec 100 663 296 octets
dans un fichier partiel. La reprise termine avec 1 359 fichiers vérifiés et
une archive d'images Docker de 5 093 084 672 octets.

Pour élargir le fonds, l'archive iFixit française de 3 652 280 723 octets est
téléchargée, indexée, classée et parcourue par l'inventaire vidéo. Un retour
à la source a changé l'état du premier journal pendant sa lecture par la VM.
La préparation a refusé ce journal. La seconde copie a été faite une fois le
fonds stabilisé, et la source est restée arrêtée pendant la lecture du support.
Cette copie vérifiée compte 1 373 fichiers et 25 473 264 999 octets, avant
l'archive d'images.

## Défaut trouvé sur le Python de la copie

Le bootstrap 0.70.0 extrait Python et vérifie sa version, mais son lien
symbolique dans `bin` écrit un mauvais répertoire `home` dans
`pyvenv.cfg`. La restauration échoue lors de la reconstruction du lecteur
ZIM, avant démarrage du portail. La 0.70.1 remplace le lien par un lanceur qui
exécute le Python depuis son emplacement réel. Le bootstrap crée et teste
désormais un environnement virtuel avant de publier les outils.

Après réinstallation des outils, la reprise de l'activation 0.70.0 a permis
de lire les trois collections, dont un article iFixit, un PDF, une carte
PMTiles, un MP4 et ses sous-titres. La recherche française retrouve le
passage de *Sintel*. La copie reste indépendante du support pendant ces essais.

Pour rejouer avec le correctif inclus dans la copie, la source Bazzite a été
mise à jour en 0.70.1 et les outils, le stockage Docker et l'installation
de la VM ont été retirés. La première mise à jour Bazzite a rencontré un
conflit sur le port HTTPS 8443 lors de la reprise par Docker. Le retour
automatique vers 0.70.0 a abouti. La relance avec l'option documentée
`SURVIE_MAINTENANCE_SITE=0` a appliqué 0.70.1.

## Rejeu final 0.70.1

La copie finale vers le Samsung compte 2 653 fichiers, soit 29 127 562 131
octets. Elle inclut les sauvegardes conservées par la mise à jour. L'archive
Docker ajoute 5 093 084 672 octets. Après copie dans la VM, le support est
démonté. Un exécutable Compose volontairement modifié est refusé avant
la création du dossier d'outils. Le fichier intact est remis en place.

Le bootstrap intégré à la copie installe Python 3.15.2, Docker 29.9.3,
Compose 5.8.0 et nftables 1.1.3. La commande Python système est masquée
pendant l'installation des outils et le lancement de l'activation.
Le démon Docker utilisé démarre sans image ni conteneur. Le programme
contrôle les 2 653 fichiers à leur nouvel emplacement, importe les images
localement et reconstruit les outils ZIM et YouTube depuis les roues copiées.

L'API 0.70.1 est saine après activation puis après redémarrage réel de la
VM. Le support reste démonté, la source est absente dans l'invité et le
témoin de connexion Internet reste inaccessible. Les contrôles vérifient
le contrôleur, Open WebUI, les trois collections Kiwix, la recherche et
l'ouverture d'un article iFixit, le PDF, la carte PMTiles, le MP4 et les
pistes anglaise et française de *Sintel*. Le modèle Ollama est présent sur
disque et le moteur reste arrêté sur la VM. La recette utilise des unités
systemd dédiées à la cible.

Bazzite est remis en service en 0.70.1. Une copie vérifiée est conservée
sur le Samsung dans `/var/home/louis/SetupSurvie-hors-ligne-20261120/secours-0701`.
La suite finale 0.70.1 exécute 1 226 tests, dont 7 ignorés, sans échec.
La recette couvre un Debian 13 déjà démarrable, en VM sur le second SSD,
avec Docker système. Le démarrage sur matériel vierge, les pilotes GPU
de la cible, l'inférence dans la VM et les autres distributions restent
hors de cette validation.

## Lanceur automatique 0.71.0

Le support généré expose `transferer-setupsurvie.sh --restaurer-hors-ligne`.
Sur une nouvelle Debian 13.7 x86-64, ce parcours extrait les outils vérifiés
de la copie, enregistre le démon Docker et l'application dans systemd,
importe les images et active les services. Le transfert vérifié compte
3 862 fichiers. La commande Python système est masquée pendant l'essai et le
support est démonté avant lancement. Le réseau WAN reste inaccessible.

Le premier passage a détecté une bibliothèque Tcl/Tk de l'archive Python
avec droit d'écriture de groupe. Le contrôle des fichiers destinés aux
services système a arrêté le lancement. Après correction du bootstrap,
les outils ont été extraits de nouveau depuis la copie et le lanceur a
repris sans changer les fichiers inventoriés. La seconde invocation sur
le même dossier a réussi sans réinstaller les outils ni les services.

Les deux unités systemd sont actives après redémarrage de la VM, avec
le support démonté. Santé 0.71.0, contrôleur, Open WebUI, les trois
collections Kiwix, article iFixit, PDF, PMTiles, MP4 et recherches dans les
sous-titres sont vérifiés avant et après le redémarrage. La suite finale
compte 1 232 tests, dont 7 ignorés, sans échec. Le lanceur automatique vise
Debian 13 déjà installé. Les pilotes GPU et les autres distributions
restent en dehors de cette recette.
