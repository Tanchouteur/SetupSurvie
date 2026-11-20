# Installer SetupSurvie

Guide d’orientation mis à jour le 20 novembre 2026. Les procédures Windows et
les essais sur les appareils de Marc restent à valider sur place.

## Préparer le matériel

La [configuration cible évolutive](configuration-materielle-cible.md), ouverte le
16 novembre 2026, rassemble les choix provisoires de Louis et les observations
matérielles. Elle distingue la future cible des PC déjà utilisés et laisse le
processeur à déterminer après mesures. Ce n’est pas un minimum logiciel validé.

## Windows : installation et mise à jour (0.1.21)

Depuis le dépôt, lancer **`Installer-SetupSurvie.cmd`**. La préparation du PC puis
l’installation s’enchaînent. Les deux anciens lanceurs restent utilisables séparément. Le [guide Windows](deux-etapes-windows.md)
décrit les prérequis, les téléchargements vérifiés, le choix du disque, le kit
local et la reprise explicite après interruption. Ce parcours automatise la
préparation des composants manquants ; le pilote GPU et la confiance HTTPS sur
les téléphones restent des étapes accompagnées. Les essais Windows réels restent
à effectuer. Il ne remplace pas le parcours de mise à jour d’une installation existante.
Chaque nouvelle installation fournit aussi **Mettre à jour SetupSurvie** et son
lanceur Git, avec sauvegarde et récupération ; voir le
[guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

## Installer le kit hors ligne chez Marc

Le [guide Marc](pilote-marc.md) est la référence : prérequis, vérification du kit,
installation dans des dossiers vides, raccourcis, LAN, certificats et recette.
Le kit contient les services, modèles et contenus sélectionnés ; vérifier son
manifeste avant transfert. Les prérequis système doivent être installés séparément.

Pour actualiser les cartes et vérifier les dépendances du kit avant transfert,
suivre [Préparer et vérifier le kit hors ligne](preparer-kit-hors-ligne.md).

## Préparer les vidéos à la première installation

Depuis la 0.54.0, le serveur examine en arrière-plan les vidéos et les pistes
fournies dans les encyclopédies ZIM présentes à la fin de l’installation, y compris
depuis un kit hors ligne. Après publication de l’inventaire, le portail
rend les titres et les pistes exploitables recherchables. Le suivi se trouve dans
**Bibliothèque → Collections → Vidéos de la bibliothèque**. L’examen attend si
l’outil d’indexation manque, si le serveur est occupé ou si le mode jeu est actif.
Après une interruption, reprenez l’examen depuis le même écran.

Pour une installation en ligne, renseignez
[`deploy/youtube-installation.txt`](../../deploy/youtube-installation.txt) **avant**
de lancer l’installateur. Le dépôt fournit le fichier avec ses consignes et
aucune adresse présélectionnée. Le serveur télécharge les vidéos listées en 480p
et prépare automatiquement les sous-titres manquants, leur version française
et l’index de recherche. Consultez **File d’attente** pour suivre le travail ou
relancer une étape en erreur. Le portail est utilisable pendant ces opérations.
Le [guide YouTube](../utilisation/telecharger-videos-youtube.md) détaille le format,
les prérequis et les droits d’usage.

## Préparer une installation depuis le dépôt

### Installation automatique Linux

Depuis la 0.72.0, le lanceur accepte Debian 12, Debian 13 et Ubuntu 22.04
x86-64 avec systemd, Bash, curl et les certificats HTTPS. Lancer depuis le
dossier logiciel obtenu. L'artefact de qualification GitHub Actions contient
`SetupSurvie-linux-VERSION.tar.gz` et son fichier SHA-256. Après contrôle de
l'archive et extraction, ouvrir le dossier `SetupSurvie`.

```sh
sudo ./scripts/install.sh --preparer-systeme /srv/setup-survie --content-pack health --content-pack water
```

Le mode automatique prépare et vérifie Docker, Compose, Python et nftables,
puis installe SetupSurvie en mode CPU. Le dossier `/srv/setup-survie` est
créé avec un stockage Docker dédié, le code, les réglages privés, les données
et les installateurs destinés au transfert. Le lanceur utilise les ports de
SetupSurvie et active le routage IPv4. Après l'installation, accéder au
portail sur `http://127.0.0.1:8080`. Les services démarrent avec le système.
En cas d'interruption, relancer la même commande avec les mêmes lots.

Avec la 0.74.0, une première installation automatique prépare GPT-OSS 20B
et Qwen3 1,7B. Sur les machines qui détectent moins de 16 Gio de RAM,
le profil rapide et la traduction automatique des vidéos utilisent Qwen3
avec un contexte initial de 8 192 tokens. GPT-OSS 20B et les autres choix
restent accessibles dans la liste des modèles. Le réglage est enregistré
à la première initialisation. La copie hors ligne conserve tous les modèles
présents et peut adapter le profil rapide à la [mémoire de la cible](../exploitation/transfert-installation.md#restaurer-sur-une-autre-machine-linux-hors-ligne).

Pour utiliser une autre distribution ou un Docker déjà configuré, suivre
le parcours manuel ci-dessous.

### Installation manuelle

Ce parcours télécharge ses dépendances et n’équivaut pas à l’installation du kit.
Sous Windows : Python x64 3.11 à 3.15, Docker Desktop avec conteneurs Linux,
Ollama Windows et pilote NVIDIA adapté. Sous Linux : Python 3.11+, Docker avec
Compose et, pour le GPU, pilote NVIDIA et NVIDIA Container Toolkit configurés.
Les versions de référence figurent dans [versions.json](../../deploy/versions.json).
Les commandes ci-dessous sont le parcours manuel sur un système déjà préparé.
Le nouveau parcours Windows ci-dessus automatise les dépendances manquantes ;
les pilotes et le choix du disque Docker restent à vérifier par l’opérateur.

Depuis la racine du dépôt, sur Windows :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Lan -DataDir 'D:\SetupSurvie\donnees'
```

Sur un Linux préparé pour Docker et NVIDIA, choisir le disque de données :

```bash
./scripts/install.sh --lan --data-dir /DISQUE/SetupSurvie/donnees
```

Pour séparer les réglages privés du dépôt, ajouter
`--work-dir '/DISQUE/SetupSurvie/Réglages privés'`. Garder ce même dossier
lors de chaque relance. Les options `--content-pack` sont réservées à
l’installation en ligne. Les codes des lots sont listés par
`python3 scripts/content.py list`.

Depuis la 0.70.0, une installation Linux x86-64 en ligne conserve dans
`donnees/tools/linux-offline-installers/` les archives vérifiées de Docker
Engine, Compose, du même Python mineur (3.11 à 3.15) et des dépendances
réseau pour Debian 13. Depuis la 0.72.0, le lot contient aussi les paquets
résolus pour Debian 12 et Ubuntu 22.04. Le transfert emporte ces archives avec les données. Elles permettent de préparer les
outils sur une cible Linux glibc sans accès à Internet.
[Restaurer sur une autre machine Linux](../exploitation/transfert-installation.md#restaurer-sur-une-autre-machine-linux-hors-ligne)

Suivre le [guide de démarrage Linux](demarrage-linux.md) pour le service
systemd, Docker rootless et les prérequis GPU correspondants.

### Préparation initiale des guides longs (0.40.1)

Sur un fonds important, l’extraction initiale des PDF peut dépasser les 30 secondes
réservées au démarrage. Le portail conserve son dernier index et poursuit la
préparation en arrière-plan ; son état redevient normal dès la réussite. Une
erreur réelle reste signalée, sans afficher le contenu des documents. Les caches
d’extraction sont conservés pour les démarrages suivants.

Remplacer les chemins d’exemple par les destinations réelles. Les images et caches
nécessaires doivent être préparés avant de couper Internet ; la présence d’un
mode hors ligne ne prouve pas que tous les fichiers sont disponibles. Ne pas
relancer une installation pour mettre à jour une installation existante : suivre
le [guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

Le [guide initial du prototype](../historique/installation.md) conserve les
anciennes commandes et le test documentaire de démonstration. Ses descriptions
des fonctions absentes ne représentent plus l’état du pilote actuel.

## Réseau, données et essais

Le [guide Marc](pilote-marc.md) fait référence pour les accès par IP, QR code,
`survie.local`, les ports, le pare-feu et la confiance du certificat local.
La découverte mDNS doit être testée sur chaque client. Les API internes 11435 et
11436 ne doivent pas être exposées aux lecteurs.

Les comptes et données privées restent propres à chaque installation. Avant
transfert ou modification, suivre les [procédures d’exploitation](../exploitation/README.md).
Les résultats Linux sont dans les [bilans d’essais](../essais/README.md) ; ils ne
valident pas le matériel Windows de Marc. Le laboratoire Podman de Louis conserve
ses propres contrôles de montage et de capacité, décrits dans les bilans Linux.

## Disque de secours complet : protocole cible

Le [protocole de disque de secours et restauration hors ligne](../exploitation/disque-de-secours-hors-ligne.md) formalise la reconstruction sur un autre PC Windows ou Linux avec le seul disque externe, sans Internet ni disque source. Il couvre aussi les prérequis système, les données ajoutées après le kit et la documentation humaine autonome. Les cibles compatibles et les parcours intersystèmes restent à développer et qualifier ; le kit actuel ne satisfait pas encore cette promesse. Pour s’orienter dans une panne avec les fonctions présentes, commencer par le [manuel de secours](../exploitation/manuel-de-secours.md).
