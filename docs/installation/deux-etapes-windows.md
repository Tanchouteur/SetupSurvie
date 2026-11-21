# Installer SetupSurvie sur Windows

**Guide de référence — revu le 20 novembre 2026 pour la 0.67.0.** Le lanceur
unique et les contrôles préliminaires ont été testés sur le Windows de Marc le
13 novembre 2026 ; l’installation complète sur un Windows vierge, le démarrage à
froid, les redémarrages et les téléphones restent à valider. Ce parcours ne
modifie pas l’installation 0.1.16 en cours chez Marc.

Pour une installation **déjà en service**, ne pas réinstaller par-dessus : la
déplacer avec **Transférer SetupSurvie** ([parcours SSD](../exploitation/transfert-installation.md) ;
ne pas copier le disque virtuel Docker comme un dossier) ou la mettre à jour avec
**Mettre à jour SetupSurvie** ([guide](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)).

## Commencer avec un seul fichier

Double-cliquer sur **`Installer-SetupSurvie.cmd`** : il vérifie et prépare le PC
(étape 1), puis installe (étape 2). Les composants déjà présents sont conservés,
y compris Docker Desktop installé sur un autre disque ou un moteur Docker déjà
accessible ; aucun service existant n’est arrêté. Options (`scripts/install-all-windows.ps1`) :

| Option | Effet |
| --- | --- |
| `-BaseDir D:\SetupSurvie` | Dossier d’installation |
| `-Kit E:\livraison-marc` | Installer depuis un kit hors ligne |
| `-LanHost 192.168.1.50` | Partager sur le réseau privé à cette IPv4 |
| `-Resume` | Reprendre une installation interrompue |
| `-Check` | Diagnostic seul : rien n’est installé, Docker n’est pas démarré |
| `-NoStartup`, `-NoBrowser` | Pas de démarrage automatique ; pas d’ouverture du navigateur |
| `-CacheDir` | Autre dossier pour les installateurs téléchargés |
| `-CollectionSort` | Reprendre un tri de collections ([voir plus bas](#reprendre-le-tri-dune-autre-installation)) |

```powershell
.\Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Kit E:\livraison-marc -LanHost 192.168.1.50
```

Si un redémarrage Windows est nécessaire, le parcours s’arrête et demande de
relancer ce même fichier, avec les mêmes options. Les deux lanceurs
`1-Preparer-le-PC.cmd` et `2-Installer-SetupSurvie.cmd` exécutent séparément les
deux étapes. Un kit ancien sans `Installer-SetupSurvie.cmd` à sa racine s’installe
avec le second lanceur du dépôt, en lui indiquant le dossier du kit : le logiciel
installé reste celui du kit.

## Préparer un kit pour Windows sans Internet

Avec la 0.81.0, depuis un PC connecté qui dispose du lanceur de préparation,
prendre un kit public SetupSurvie dont le dossier **app** est en 0.81.0 ou
ultérieur. Exécuter une fois cette commande avec le chemin du kit.

```powershell
.\1-Preparer-le-PC.cmd -Kit E:\livraison-marc -DownloadOnly
```

Cette commande place les installateurs vérifiés de WSL, Python, Docker Desktop,
Git et Ollama dans `installateurs-windows` à la racine du kit. Elle prépare
le support sans installer les composants sur le PC connecté.

Sur le PC hors ligne, ouvrir **Installer-SetupSurvie.cmd** dans le dossier
**app** du kit. Le lanceur détecte ce kit et vérifie les installateurs
manquants avant de modifier Windows. Si la plateforme de virtualisation est
désactivée, DISM utilise les composants locaux. Un dossier
`installateurs-windows\sxs` issu de la version de Windows correspondante peut
servir de source au besoin. WSL est installé depuis le MSI du kit. Après
chaque demande de redémarrage, rouvrir le même lanceur. En l’absence de pilote
NVIDIA utilisable, la préparation du PC peut continuer. Les écrans de licence
et de placement de Docker restent à suivre.

[Installation WSL hors ligne](https://learn.microsoft.com/en-us/windows/wsl/install#offline-install) · [Préparation DISM](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/enable-or-disable-windows-features-using-dism?view=windows-11)

## Préparer le PC

**`1-Preparer-le-PC.cmd`** (ni Python ni WinGet requis) exige Windows 11 24H2 ou
plus récent **x64** (build 26100), la virtualisation activée dans le BIOS/UEFI,
la validation des demandes administrateur et un accès Internet ou un kit préparé.
Il vérifie WSL 2, Python x64
3.11 à 3.15, Docker Desktop, Git et Ollama, conserve ce qui est présent, installe
ce qui manque et **ne met pas à niveau** les logiciels existants. Les versions
présentes ne sont pas toutes certifiées compatibles par ce diagnostic : l’étape 2
vérifie réellement Docker, Compose et les services.

- Les installateurs manquants (Python, Docker, Git for Windows, Ollama) sont
  téléchargés avec SHA-256 vérifié avant exécution. Versions, URL, empreintes et
  sources sont dans `deploy/windows-installers.json` (relues dans les
  [manifestes Microsoft](https://github.com/microsoft/winget-pkgs) et l’[API officielle de Git](https://api.github.com/repos/git-for-windows/git/releases/tags/v2.56.1.windows.1) ;
  rien n’a été téléchargé ni installé dans le runner CPU). La référence Ollama
  native est dans `deploy/versions.json`.
- Les installateurs affichent leurs écrans et licences : pour Python, garder
  l’ajout au PATH ; pour Docker, choisir WSL 2 et les conteneurs Linux. Ils sont
  conservés dans `%LOCALAPPDATA%\SetupSurvie\installateurs` (cache ; ce n’est pas
  le dossier de préparation locale du PC).
- Si WSL doit être préparé ou si un installateur demande un redémarrage, le
  lanceur rend le code 3010 et affiche la marche à suivre : redémarrer Windows,
  puis relancer **le même fichier**. Il n’installe pas Ubuntu et ne redémarre pas
  le PC. L’état conservé ne contient que le besoin de redémarrage et
  l’identifiant du démarrage, aucun identifiant de compte SetupSurvie.
- Le pilote NVIDIA s’installe depuis le constructeur. Le diagnostic appelle
  `nvidia-smi` sans charger de modèle : cela ne valide ni l’inférence ni les
  performances. Une virtualisation désactivée ou un système non pris en charge
  arrête le parcours avant toute installation.
- Diagnostic seul : `.\1-Preparer-le-PC.cmd -Check`.

## Installer SetupSurvie

**`2-Installer-SetupSurvie.cmd`** demande :

1. Un dossier dédié sur le disque de données (Entrée accepte `D:\SetupSurvie` si
   D: existe, sinon `SetupSurvie` dans le dossier utilisateur).
2. Le dossier du kit contenant `manifest.json`, ou Entrée pour télécharger.
3. Le réseau privé proposé (Entrée confirme son adresse si elle est unique) ou
   **LOCAL** pour limiter l’accès au PC.

Docker Desktop démarre si nécessaire : terminer son accueil et vérifier **Settings
→ Resources → Advanced → Disk image location**. Le lanceur attend une confirmation
de l’emplacement et ne déplace pas un disque Docker existant. Une autre instance
Docker déjà accessible doit utiliser des conteneurs Linux. Avant les questions, le
lanceur vérifie les ports : si une autre installation fonctionne, il indique
comment l’ouvrir ou la mettre à jour et s’arrête avant de copier. Un autre dossier
ne permet pas de faire cohabiter deux serveurs (ports communs) ; la reprise
accepte les services identifiés comme appartenant à cette installation.

| Dossier créé | Contenu |
| --- | --- |
| `application` | Copie indépendante du logiciel, compatible avec les mises à jour |
| `donnees` | Modèles, bibliothèque, caches, états des services |
| `prive` | Réglages et identifiants de cette installation |

**Sans kit** (Internet) : services, caches, **le modèle par défaut `gpt-oss:20b`**
(`deploy/versions.json`) et le lot `survival` du catalogue figé, plus les cartes
de base (voir plus bas). Ni les autres modèles, ni toute la bibliothèque : les
compléter depuis le portail (**Mon appareil → Paramètres → Assistant → Modèles de
l’assistant**, profil Famille, et **Bibliothèque et préparations**) ; sur le
serveur, `scripts\survie.ps1 pull-model NOM_DU_MODELE` reste possible. Le contrôle
préliminaire réserve au moins **60 Go libres** sur le disque de données en plus
du logiciel ; cela ne garantit pas la place du fonds complet. Vérifier
séparément l’espace du disque Docker.

**Avec kit** : toutes les empreintes et dépendances sont contrôlées avant copie,
les images sont importées localement, aucun lot documentaire n’est téléchargé.
Espace exigé : copies restantes plus **22 Go** de marge (le contrôle des services
exige 20 Gio libres), hors Docker. Le kit et la destination restent séparés.
Voir aussi le [guide Marc](pilote-marc.md#installer-à-partir-du-kit).

Raccourcis et démarrage : le lanceur crée sur le Bureau **Ouvrir SetupSurvie**,
**Arrêter SetupSurvie**, **Mettre à jour SetupSurvie**, **Transférer SetupSurvie**
(et **Suivi bibliothèque SetupSurvie** s’il est présent), ainsi que
`Mettre-a-jour-SetupSurvie.cmd` à côté du dossier `application` (lanceur stable :
Git, sauvegarde, retour arrière). Le démarrage à l’ouverture de session est activé
sauf `-NoStartup`. Les raccourcis d’une autre installation sont conservés ; les
nouveaux reçoivent un suffixe si le nom est pris. Désactiver le démarrage ne
supprime que le raccourci et désactive les tâches de cette installation. Le
portail s’ouvre à la fin (sauf `-NoBrowser`). Les tests de disponibilité
n’interrogent aucun modèle et une pause existante est respectée ; l’installation
initiale peut lancer Ollama pour préparer le modèle, les démarrages automatiques
suivants ouvrent d’abord les services documentaires.

Les nouveaux exports de kit incluent les quatre lanceurs racine ; les paquets de
mise à jour d’une installation existante contiennent les scripts et le générateur
du lanceur stable, mais **excluent les fichiers `.cmd` racine**, pour rester
lisibles par le programme de mise à jour 0.1.16.

## Réseau et accès depuis les autres appareils

Sur un unique réseau Windows privé avec passerelle, l’installateur propose son
IPv4 : Entrée confirme le partage, **LOCAL** limite volontairement au PC. Avec
plusieurs réseaux privés, choisir l’adresse explicitement. Sans réseau privé
détecté, il ne choisit rien en silence : passer le réseau domestique en privé ou
choisir LOCAL. Il ne change jamais la catégorie du réseau.

Si une IPv4 est fournie, le lanceur demande les droits administrateur pour les
règles de pare-feu existantes : accès Web sur le réseau privé et sous-réseau
local ; blocage des ports de commande sur les interfaces physiques ; retrait
(avec copie de leurs réglages) des seules autorisations publiques entrantes
Ollama correspondant à l’exécutable de cette installation. Un refus laisse
l’application installée et signale la configuration réseau restant à terminer.

Avant de donner l’adresse, le lanceur contrôle `/api/health` sur l’IPv4 choisie
et exige la version installée : un site limité à localhost ou une ancienne version
échouent. L’adresse HTTP est donnée d’abord ; HTTPS demande que chaque appareil
fasse confiance au certificat racine public de SetupSurvie (ne pas contourner un
avertissement TLS comme preuve). Réserver l’IP dans le routeur, tester depuis un
autre appareil, puis suivre le [guide Marc](pilote-marc.md#accès-depuis-tout-le-réseau-local)
pour le certificat et les téléphones. Un contrôle fait depuis le serveur ne
remplace pas celui d’un téléphone (Wi-Fi invité, isolation des clients, autre
pare-feu).

## Reprendre une interruption

Le journal `.installation.json` enregistre la source, les options et la phase ;
un verrou système empêche deux installations simultanées dans la même
destination et se libère à la fermeture du processus. Conserver le dépôt ou le kit
source inchangé, puis :

```powershell
.\Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Resume
```

Le parcours retrouve le kit, le partage réseau et le choix de démarrage. Les
copies conformes sont réutilisées, une copie partielle est remplacée après
contrôle ; une fois la configuration commencée, les contenus initiaux ne sont plus
recopiés sur les ajouts de l’utilisateur. Les téléchargements de composants
utilisent leurs caches de reprise. Sont **refusés** : source modifiée, options
différentes, dossiers occupés sans journal, installation terminée (utiliser alors
les [mises à jour et sauvegardes](../exploitation/README.md)). Ne pas supprimer le
journal pour contourner ce contrôle. Depuis 0.1.23, les copies sont synchronisées
avant d’enregistrer l’étape terminée : après un arrêt brutal du PC, voir
[Coupures et redémarrage](../exploitation/coupures-et-redemarrage.md) (une
installation interrompue reste distincte d’une mise à jour à récupérer).

## Reprendre le tri d’une autre installation

À la seconde étape, donner le chemin du fichier `SetupSurvie-tri.json` exporté
depuis **Mon appareil → Paramètres → Bibliothèque et préparations → Organiser les
collections** (0.65.0), ou l’option `-CollectionSort`. Le récapitulatif liste les
collections à télécharger ou copier, les collections **Autre** et les exclusions ;
confirmer pour démarrer. Le journal conserve tri et plan pour `-Resume`. Les
contenus absents du catalogue ou du kit restent en attente d’une source
compatible. En ligne de commande (aussi sous Linux) :
`scripts/kiwix_select.py select --work-dir … --collection-sort …` prépare et
affiche le plan ; `scripts/content.py download --work-dir … --selection …` l’exécute
après vérification.

## Démarrage automatique Windows depuis 0.1.30

Avec le démarrage automatique (choix par défaut), l’installation prépare
`maintenance/startup-windows.ps1`, les chemins réels de Python, Docker et Ollama,
et deux tâches Windows limitées à l’utilisateur courant. À l’ouverture de
session : Docker Desktop si nécessaire, puis portail, Open WebUI, Kiwix et
contrôleur. Un contrôle toutes les cinq minutes retente un démarrage échoué ; un
site déjà sain à la version installée n’est pas redémarré. Le lanceur ne dépend
pas de `Docker/install-settings.json`, qui peut disparaître ; les outils portables
du disque de données restent trouvables. Ces tâches fonctionnent **après ouverture
de session Windows** (nécessaire à Docker Desktop) et n’activent pas l’ouverture
de session automatique.

- **Moteur IA** : depuis 0.43.1, il démarre avec les services ; la mise à jour d’un
  démarrage géré remplace l’ancien réglage `inference_autostart: false`. Une
  pause explicite (mode jeu) reste respectée. Le site peut être accessible avant
  que le moteur soit prêt. Seul le raccourci de démarrage d’Ollama correspondant
  exactement à l’exécutable utilisé est déplacé hors du dossier Startup (copie
  conservée).
- **Reprise des téléchargements** : une tâche distincte, **sans limite de durée**,
  reprend le dernier plan documentaire autorisé et figé (armée par les commandes de
  sélection/téléchargement et le téléchargement web). Sans plan, elle ne fait rien ;
  aucun nouveau catalogue n’est choisi à l’insu de l’utilisateur ; pauses et
  transferts actifs sont respectés ; les reçus évitent de relire les grosses
  archives. Une reprise avant ouverture de session est une option distincte,
  décrite dans [Coupures et redémarrage](../exploitation/coupures-et-redemarrage.md#reprise-automatique-de-la-bibliothèque-sous-windows--0127).
- **Arrêt volontaire** : **Arrêter SetupSurvie** laisse un marqueur ; la
  surveillance ne relance pas le site cinq minutes plus tard. **Ouvrir SetupSurvie**
  ou un `up` explicite reprend. La pause de téléchargement reste indépendante de
  l’arrêt du site. Une mise à jour inachevée bloque les redémarrages automatiques
  jusqu’à sa récupération explicite.
- **Silencieux** : la tâche lance `pythonw.exe` avec `windows_background.py`
  (`CREATE_NO_WINDOW`, entrées fermées, sorties dans
  `diagnostics/startup-background.log` ; un échec renvoie un code non nul au
  planificateur). Les fenêtres de suivi et de mise à jour ouvertes volontairement
  restent visibles. Les mesures NVIDIA lisent directement la bibliothèque NVML du
  pilote, sans lancer `nvidia-smi` ni PowerShell ; sans NVML, la mesure est
  indisponible.
- **Journaux** : `data/diagnostics/demarrage-automatique.log` et `bibliotheque-auto.log`.
- **Options** : `-NoStartup` désactive les nouveaux raccourcis et tâches (une reprise
  avant session activée séparément reste indépendante). Pour une installation
  existante : `python scripts/setup.py --work-dir CHEMIN_PRIVE shortcuts` depuis le
  dossier application, avec `--no-startup` pour désactiver. Une mise à jour seule
  ne réactive pas un démarrage désactivé et rafraîchit les helpers d’un démarrage
  déjà configuré sans toucher aux préférences IA, au réseau, aux données ni à
  Ollama ; un nom de tâche ou un dossier de maintenance d’une autre application
  est refusé.
- **Docker introuvable** : si Docker est arrêté, le lanceur vérifie aussi son
  emplacement enregistré par Windows. Une installation non enregistrée est
  signalée sans ouvrir l’interface ; une installation enregistrée qui ne démarre pas
  reçoit **une seule tentative automatique par démarrage Windows**
  (`docker-start-attempt.json` dans le dossier privé). **Ouvrir SetupSurvie**
  permet une nouvelle tentative après réparation. Réparer Docker avec son
  installateur officiel, après sauvegarde de ses données à l’arrêt ; ne pas
  désinstaller ni supprimer les distributions WSL. Cas observé : [WIN-019](../exploitation/journal-incidents-windows.md#win-019--docker-desktop-introuvable-dans-le-registre-et-boîtes-derreur-répétées).

Le suivi **Suivi bibliothèque SetupSurvie** reconnaît `python.exe` et `pythonw.exe`
et lit la longueur réelle des partiels par un handle partagé (la taille
d’annuaire peut rester à zéro tant que le fichier est ouvert). Le fermer ou le
rouvrir ne coupe aucun transfert.

## Cartes incluses dans la préparation de base — 0.1.33

En installation **avec Internet**, le lanceur prépare les fonds PMTiles locaux :
Sud (PACA, Occitanie, Corse ; zoom 13) et Solliès-Ville (zoom 15), puis relief,
lieux et adresses dans un rayon de 25 km autour de Solliès-Ville
(`deploy/map-catalog.json`). Ce sont les zones du pilote de Marc, pas une
couverture mondiale. L’ombrage et la coupe du terrain s’appuient sur le relief ;
le calcul d’itinéraires reste une préparation distincte.

- L’outil PMTiles Windows/Linux x64 vient de sa publication officielle, avec
  SHA-256 figé vérifié avant exécution. Les cartes terminées sont vérifiées et
  réutilisées ; une extraction partielle est conservée en diagnostic puis reprise
  depuis le début de cette extraction (pas de reprise octet par octet).
- Si le fond quotidien officiel expire, un fond récent du même fournisseur est
  cherché, avec sa **vraie date et sa source enregistrées**.
- Le relief est préparé indépendamment des adresses et points d’intérêt. Une panne
  Overpass conserve fonds et altitudes prêts et affiche un avertissement ;
  `catalog/map-installation.json` distingue les états de chaque jeu. Les
  coordonnées de la zone sont transmises aux fournisseurs. Les lieux OSM ne
  prouvent ni accès, ni horaires à jour, ni ressource disponible, ni eau potable.
- **Depuis un kit hors ligne** : rien n’est téléchargé ; les cartes présentes sont
  contrôlées et les jeux absents signalés. Préparer le kit avec les cartes avant
  de l’apporter sur un site sans Internet.

Pour compléter une installation existante, sans réinstaller ni relancer un modèle
(adapter les deux chemins) :

```powershell
python application/scripts/setup.py --work-dir prive prepare-maps
```

La commande vérifie les cartes, prépare les éléments manquants et réindexe le
guide cartographique. Le suivi de bibliothèque affiche aussi le nombre de fonds
présents : 100 % d’un plan Kiwix/PDF ne signifient pas que des cartes ont été
téléchargées.

## Limites de validation

- **Chez Marc, 13 novembre 2026** : 94 tests ciblés sans échec (cinq ignorés sous
  Windows) ; exécution réelle des deux tâches et accès au site 0.1.29 réussis,
  téléchargement en cours conservé, IA en pause ; HTTP, nom local, recherche, lecture
  PDF par plage et les trois services HTTPS avec la CA locale validés **sur le PC**.
  Aucun redémarrage du PC n’a été imposé.
- **Accès depuis un autre appareil** : un premier essai a signalé une expiration en
  Wi-Fi (IP et nom) ; un retour ultérieur de Marc confirme que les deux liens
  fonctionnent après connexion au Wi-Fi. La cause des premiers échecs et la
  qualification de tous les points d’accès restent distinctes de ce succès : voir
  [WIN-008](../exploitation/journal-incidents-windows.md#win-008--observations-et-essais-du-13-novembre).
  Ni `survie.local` ni Safari iOS ne sont validés.
- **Reste à tester** : démarrage à froid, installation complète sur Windows vierge,
  téléphones. Depuis la 0.81.0, la préparation vérifie et utilise les
  installateurs système du kit. La chaîne complète sur un Windows fraîchement
  installé et déconnecté reste à qualifier.
- Aucun téléchargement lourd ni installation système dans le runner de
  développement.

Références système : [WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands),
[Docker Desktop Windows](https://docs.docker.com/desktop/setup/install/windows-install/).

## Historique

- **0.1.17** : parcours en deux étapes (`1-Preparer-le-PC.cmd`,
  `2-Installer-SetupSurvie.cmd`). **0.1.20** : lanceur unique. **0.1.21** :
  lanceur de mise à jour stable.
- **0.1.30** : démarrage automatique et reprise des téléchargements. **0.1.33** :
  cartes dans la préparation de base. **0.2.0** : démarrage silencieux et
  migration des lanceurs (le correctif local a été intégré à la refonte moteur après
  autorisation de Louis). **0.43.1** : moteur IA démarré avec les services.
  **0.65.0** : reprise d’un tri de collections.
