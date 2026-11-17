# Installer SetupSurvie

Guide d’orientation mis à jour le 12 novembre 2026. Les procédures Windows et
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

## Préparer une installation depuis le dépôt

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

### Linux : démarrage automatique et Docker rootless (0.39.0)

Premier essai d’installation Linux de zéro sur Bazzite le 17 novembre 2026 ;
voir le [bilan](../essais/2026-11-17-installation-neuve-bazzite.md).

- **Démarrage avec le PC.** Sous Linux, l’installation crée et démarre le
  service utilisateur systemd `setupsurvie-<projet>.service`
  (`~/.config/systemd/user/`). Il lance `survie.sh up` au démarrage : services
  Web, contrôleur local, annonce `survie.local` et indexation automatique. Ces
  processus ne dépendent plus du terminal de l’installation. Sans session
  ouverte, il faut le « linger » de l’utilisateur : l’installation l’active si
  le système le permet, sinon elle affiche `sudo loginctl enable-linger UTILISATEUR`.
  `--no-startup` n’installe pas ce service. Le retirer :
  `systemctl --user disable --now setupsurvie-<projet>.service`, puis supprimer
  le fichier du service.
- **Docker rootless** (cas des systèmes immuables comme Bazzite) : détecté
  automatiquement. Les conteneurs joignent alors le contrôleur par la boucle
  locale de l’hôte (`10.0.2.2`) et le contrôleur n’écoute que sur `127.0.0.1`.
  Cela exige `DOCKERD_ROOTLESS_ROOTLESSKIT_DISABLE_HOST_LOOPBACK=false` : si
  Docker rootless tourne par le service standard `docker.service` de
  l’utilisateur, l’installation ajoute ce réglage et redémarre Docker ; sinon,
  elle s’arrête avec la commande à appliquer. Avec Docker système, le contrôleur
  reste sur toutes les interfaces, protégé par son jeton : bloquer le port
  11436 au pare-feu du réseau local.
- **GPU avec Docker rootless** : le runtime NVIDIA doit être enregistré dans
  le `daemon.json` de ce Docker et `no-cgroups = true` réglé dans la
  configuration `nvidia-container-runtime` lue par ce démon (fichier système
  ou `$XDG_CONFIG_HOME/nvidia-container-runtime/config.toml`). L’installation
  ne modifie pas ces prérequis système ; `docker info` doit lister le runtime
  `nvidia`.
- **Python 3.15** : l’outil d’indexation complémentaire utilise libzim 4.1.0 ;
  jusqu’à Python 3.14, libzim 3.13.1 reste utilisé, sans changement pour les
  installations existantes.
- La fin de l’installation indique l’état du démarrage automatique et si le
  portail joint le contrôleur local.

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
