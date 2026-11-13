# Installer SetupSurvie sur Windows

**Guide actuel — pilote 0.1.33, 13 novembre 2026.** Lanceur unique et contrôles préliminaires
testés sur le Windows de Marc ; installation complète sur Windows vierge, redémarrages et téléphones encore à valider.
Ce parcours ne modifie pas l’installation 0.1.16 en cours chez Marc.

## Commencer avec un seul fichier

Double-cliquer sur **`Installer-SetupSurvie.cmd`**. Il vérifie et prépare le PC,
puis passe automatiquement à l’installation. Les composants déjà présents sont
conservés, y compris Docker Desktop installé sur un autre disque ou un moteur
Docker déjà accessible. Aucun service existant n’est arrêté automatiquement.

Si un redémarrage Windows est nécessaire, le parcours s’arrête et demande de
relancer ce même fichier après le redémarrage, avec les mêmes options. Une installation
applicative interrompue se reprend avec `Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Resume`.
Les anciens fichiers `1-Preparer-le-PC.cmd` et `2-Installer-SetupSurvie.cmd`
restent disponibles pour exécuter séparément les deux étapes décrites ci-dessous.

Depuis 0.1.23, les copies sont synchronisées avant d’enregistrer l’étape terminée.
Pour un arrêt brutal du PC, suivre [Coupures et redémarrage](../exploitation/coupures-et-redemarrage.md) ;
une installation interrompue reste distincte d’une mise à jour à récupérer.

Pour vérifier seulement les prérequis sans installer ni démarrer Docker :

```powershell
.\Installer-SetupSurvie.cmd -Check
```

## Préparer le PC

Depuis le dépôt récupéré ou décompressé, double-cliquer sur
**`1-Preparer-le-PC.cmd`**. Python et WinGet ne sont pas nécessaires pour ce lanceur.
Il nécessite Windows 11 24H2 ou plus récent **x64**, la virtualisation activée dans
le BIOS/UEFI, Internet et la possibilité de valider les demandes administrateur.

Le lanceur vérifie WSL 2, Python x64 3.11 à 3.15, Docker Desktop, Git et Ollama. Il
conserve les installations présentes, installe les composants absents et ne
met pas automatiquement les logiciels existants à niveau. Les versions présentes
ne sont pas toutes certifiées compatibles par ce seul diagnostic ; le second
lanceur vérifie réellement Docker/Compose et les services.

Les installateurs manquants sont téléchargés depuis Python, Docker, Git for Windows et Ollama,
avec SHA-256 vérifié avant exécution. Les versions, URL, empreintes et sources
consultées figurent dans `deploy/windows-installers.json`. Ces métadonnées ont
été relues dans les [manifestes Microsoft](https://github.com/microsoft/winget-pkgs)
et, pour Git, dans son [API de livraison officielle](https://api.github.com/repos/git-for-windows/git/releases/tags/v2.56.1.windows.1) ;
les binaires ne sont pas téléchargés ni installés dans le runner CPU.
La référence Ollama native reste celle de `deploy/versions.json`.

Les installateurs affichent leurs écrans et licences. Pour Python, conserver
l’ajout au PATH ; pour Docker, choisir WSL 2 et les conteneurs Linux. Les fichiers
sont conservés dans `%LOCALAPPDATA%\SetupSurvie\installateurs`. Le paramètre
`-CacheDir` permet de choisir un autre emplacement. Ce cache ne constitue pas
encore un kit système hors ligne complet.

Si WSL doit être préparé ou un installateur demande un redémarrage, le lanceur
rend le code 3010 et affiche la marche à suivre. Redémarrer Windows puis relancer
**le même fichier**. Il n’installe pas Ubuntu et ne redémarre pas lui-même le PC.
L’état de préparation conserve seulement le besoin de redémarrage et l’identifiant
du démarrage ; il ne contient aucun identifiant de compte SetupSurvie.

Le pilote NVIDIA reste à installer depuis le constructeur pour le matériel exact.
Le diagnostic appelle `nvidia-smi` sans charger de modèle ; cela ne valide pas
l’inférence réelle ni les performances. Une virtualisation désactivée ou un OS
non pris en charge arrête le parcours avant installation.

Pour un diagnostic sans installation ni démarrage de Docker :

```powershell
.\1-Preparer-le-PC.cmd -Check
```

## Installer SetupSurvie

Double-cliquer sur **`2-Installer-SetupSurvie.cmd`** et renseigner :

1. Un dossier dédié sur le disque de données. Entrée accepte `D:\SetupSurvie` si le disque D: existe, sinon `SetupSurvie` dans votre dossier utilisateur. Le contrôle de capacité reste obligatoire.
2. Le dossier du kit contenant `manifest.json`, ou Entrée pour télécharger.
3. Le réseau privé proposé : Entrée confirme son adresse lorsqu’il est unique.
   Saisir LOCAL pour limiter volontairement l’accès au PC.

Docker Desktop démarre si nécessaire. Terminer son accueil et vérifier **Settings
→ Resources → Advanced → Disk image location**. Le lanceur attend une confirmation
de l’emplacement : il ne déplace pas un disque Docker existant. Une autre instance
Docker déjà accessible doit utiliser des conteneurs Linux.

Avant les questions sur le kit et le réseau, le lanceur vérifie les ports. Si une
autre installation fonctionne déjà, il indique comment l’ouvrir ou la mettre à
jour et s’arrête avant de copier ou télécharger. Un autre dossier ne suffit pas
à faire cohabiter deux serveurs : les ports de service sont communs. La reprise
accepte les services et processus identifiés comme appartenant à cette installation.

Le dossier choisi contient ensuite :

| Dossier | Contenu |
| --- | --- |
| `application` | Copie indépendante du logiciel, compatible avec les mises à jour |
| `donnees` | Modèles, bibliothèque, caches et états des services |
| `prive` | Réglages et identifiants de cette installation |

Sans kit, le parcours prépare les services, caches, les deux modèles des trois modes conseillés et le lot
`survival` du catalogue figé. Il ne télécharge pas tous les modèles de comparaison,
ni toute la bibliothèque ni les cartes. Bibliothèque et cartes se complètent dans
le portail ; les autres modèles peuvent être ajoutés avec `scripts/survie.ps1 pull-model`.
Le contrôle préliminaire réserve au moins 60 Go libres sur le disque de données,
en plus du logiciel à copier ; cela ne garantit pas la place nécessaire au fonds
complet. Contrôler séparément l’espace du disque Docker.

Avec kit, toutes les empreintes et dépendances sont contrôlées avant copie. Les
images sont importées localement ; aucun lot documentaire n’est téléchargé.
L’espace exigé correspond aux copies restantes plus 22 Go de marge (le contrôle des services exige 20 Gio libres), hors espace
Docker. Le kit et la destination doivent rester séparés.

Le lanceur crée les raccourcis **Ouvrir SetupSurvie** et **Arrêter SetupSurvie** et
le démarrage à l’ouverture de session. `-NoStartup` conserve seulement les
raccourcis manuels. Le portail s’ouvre à la fin ; `-NoBrowser` évite cette ouverture.
Il crée aussi **Mettre à jour SetupSurvie** sur le Bureau et
`Mettre-a-jour-SetupSurvie.cmd` à côté du dossier `application`. Ce lanceur stable
utilise Git puis la sauvegarde et le retour arrière existants ; voir le
[guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).
Les raccourcis d’une autre installation sont conservés ; les nouveaux reçoivent
un suffixe si leur nom est déjà utilisé. Désactiver le démarrage ne supprime que
le raccourci et désactive les tâches appartenant à l’installation concernée.
Les tests de disponibilité n’interrogent aucun modèle. Une pause existante reste
respectée. L’installation initiale peut lancer Ollama pour préparer les modèles ;
les démarrages automatiques suivants ouvrent les services documentaires sans IA.

Exemple avec paramètres :

```powershell
.\Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Kit E:\livraison-marc -LanHost 192.168.1.50
```

Pour un kit ancien sans ces deux fichiers à sa racine, utiliser le second lanceur
du dépôt 0.1.17 en lui indiquant le dossier du kit. Le logiciel installé reste
celui du kit, avec sa version. Les nouveaux exports/rafraîchissements du kit
incluent le lanceur d’installation, celui de mise à jour et les deux anciens. Les mises à jour d’une installation existante incluent
leurs scripts et le générateur du lanceur stable, mais excluent les quatre fichiers racine `.cmd` pour rester
lisibles par le programme de mise à jour 0.1.16 ; une installation terminée utilise
ses raccourcis habituels.

## Reprendre une interruption

Le journal `.installation.json` enregistre la source, les options et la phase
d’installation ; un verrou système empêche deux installations simultanées dans
la même destination et est libéré à la fermeture du processus.

Après une interruption, conserver le dépôt ou kit source inchangé puis lancer :

```powershell
.\Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Resume
```

Le parcours retrouve le kit, le partage réseau et le choix de démarrage. Les
copies déjà conformes sont réutilisées ; une copie partielle est remplacée après
contrôle. Une fois la configuration commencée, les contenus initiaux ne sont
plus recopiés sur les éventuels ajouts utilisateur. Les téléchargements des
composants utilisent leurs mécanismes de cache et de reprise existants.

Une source modifiée, des options différentes, des dossiers déjà occupés sans
journal ou une installation terminée sont refusés. Ne pas supprimer le journal
pour contourner ce contrôle. Pour une installation terminée, utiliser les
[mises à jour et sauvegardes](../exploitation/README.md).

## Réseau et limites de validation

Si une IPv4 a été fournie, le lanceur demande les droits administrateur pour
exécuter les règles existantes de pare-feu : accès Web sur le réseau privé et
blocage des ports de commande sur les interfaces physiques. Un refus laisse
l’application installée et affiche la configuration réseau restant à terminer.
Il ne transforme pas un réseau Windows public en réseau privé.

Réserver l’IP dans le routeur, tester l’accès depuis un autre appareil puis suivre
le [guide Marc](pilote-marc.md#accès-depuis-tout-le-réseau-local) pour le certificat
public et les téléphones. La confiance HTTPS sur chaque client reste une étape
manuelle ; ni `survie.local` ni Safari iOS ne sont validés par ce lanceur.

Références système : [WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
et [Docker Desktop Windows](https://docs.docker.com/desktop/setup/install/windows-install/).

Ce premier lot ne fournit pas encore les installateurs système hors ligne, la
réinstallation de Windows, les sauvegardes planifiées depuis le portail ni les
métadonnées enrichies des notices. Ces lots restent à réaliser et à tester selon
le plan retenu. Ne pas annoncer une réinstallation complète hors ligne validée.


## Démarrage automatique Windows depuis 0.1.30

L’installation avec démarrage automatique (choix par défaut) prépare un lanceur
stable dans `maintenance/startup-windows.ps1`, ses chemins Python/Docker/Ollama
réels et deux tâches Windows limitées à l’utilisateur courant. À l’ouverture de
session, Docker Desktop est démarré si nécessaire, puis le portail, Open WebUI,
Kiwix et le contrôleur. Un contrôle toutes les cinq minutes retente si le démarrage
a échoué ; un site déjà sain à la version installée n’est pas redémarré. Le lanceur
ne dépend pas de `Docker/install-settings.json`, fichier qui peut disparaître.
Les outils portables sur le disque de données restent trouvables après redémarrage.

La préférence `inference_autostart: false` est enregistrée : les services
s’ouvrent sans lancer le moteur IA. L’utilisateur peut démarrer l’IA depuis le
portail. La pause du mode jeu est conservée. Seul le raccourci de démarrage
Ollama correspondant exactement à l’exécutable utilisé est déplacé hors du
dossier Startup, avec conservation d’une copie ; les autres installations sont
laissées en place. Les modèles nécessaires à l’installation peuvent toujours
être préparés pendant l’installation initiale.

Une tâche distincte, **sans limite de durée**, reprend le dernier plan documentaire
autorisé et figé. Les commandes de sélection/téléchargement et le téléchargement
web arment cette reprise quand le lanceur automatique est installé. Aucun nouveau
catalogue n’est choisi à l’insu de l’utilisateur. Sans plan sélectionné, elle ne
fait rien. Les pauses volontaires restent respectées. Un transfert déjà actif
n’est pas remplacé ; les reçus permettent de garder les fichiers vérifiés sans
relire toutes les grosses archives. Une sélection web reprise conserve son
identifiant et actualise son état dans le portail.

Ces tâches utilisateur fonctionnent **après ouverture de session Windows**,
nécessaire à Docker Desktop. Elles n’activent pas l’ouverture de session automatique.
La [reprise avant ouverture de session](../exploitation/coupures-et-redemarrage.md#reprise-automatique-de-la-bibliothèque-sous-windows--0127)
reste une option distincte pour la bibliothèque seule ; elle est déjà configurée
chez Marc et coexiste sans doublon grâce aux verrous.

`-NoStartup` désactive les nouveaux raccourcis et tâches de surveillance ; une
reprise avant session activée séparément reste indépendante. Les journaux sont
sous `data/diagnostics/demarrage-automatique.log` et `bibliotheque-auto.log`.
Pour une installation existante, installer la version correspondante puis lancer
`python scripts/setup.py --work-dir CHEMIN_PRIVE shortcuts` depuis son dossier
application. Ajouter `--no-startup` pour désactiver les tâches et le raccourci de
démarrage. Une mise à jour logicielle seule ne réactive pas un démarrage
explicitement désactivé.

Vérifications chez Marc le 13 novembre : 94 tests ciblés sans échec, dont cinq
ignorés Windows, exécution réelle des deux tâches et accès au site 0.1.29 réussis,
même téléchargement en cours et IA en pause. Le nouveau démarrage à froid et une
installation complète sur Windows vierge restent à tester ; aucun redémarrage du
PC n’a été imposé pour ces contrôles.


## Éviter une installation limitée au PC par erreur

**Réserve de recette du 13 novembre :** après correction de l'écoute locale,
Marc signale encore une expiration depuis son Wi-Fi, par IP et par nom. L'accès
entre appareils n'était donc pas validé lors de ce premier essai. Un retour
ultérieur de Marc confirme que les deux liens fonctionnent après connexion au
Wi-Fi. La cause des premiers échecs et la qualification de tous les points d'accès
restent distinctes de ce succès. Le [journal Windows](../exploitation/journal-incidents-windows.md#win-008--observations-et-essais-du-13-novembre)
conserve les faits, les essais sans effet et le prochain test à effectuer.

Sur un unique réseau Windows privé avec passerelle, l’installateur propose son
IPv4 : Entrée confirme le partage sur ce réseau. Pour rester volontairement
limité au PC, saisir **LOCAL**. Si plusieurs réseaux privés sont présents,
choisir leur adresse explicitement. Sans réseau privé détecté, le lanceur ne
choisit pas silencieusement un mode inaccessible : passer le réseau domestique
en privé ou choisir LOCAL. Il ne change pas la catégorie réseau à votre place.

L’étape pare-feu autorisée ouvre les ports web sur le profil privé et le sous-réseau
local. Elle conserve le blocage des commandes IA sur les interfaces physiques et
retire seulement les autorisations publiques entrantes Ollama correspondant à
l’exécutable de cette installation, avec copie de leurs réglages précédents.
Un refus d’élévation est signalé comme une validation réseau non terminée.

Avant de donner l’adresse à utiliser, le lanceur contrôle `/api/health` sur
l’IPv4 choisie et exige la version installée ; un site limité à localhost ou une
ancienne version ne passent pas ce contrôle. L’adresse HTTP est fournie d’abord
pour un premier essai simple. HTTPS est également disponible, mais nécessite la
confiance dans le certificat racine public de SetupSurvie sur chaque appareil,
notamment pour la dictée. Ne pas contourner un avertissement TLS comme preuve
que le certificat est installé.

Un contrôle effectué depuis le serveur ne remplace pas celui du téléphone : le
Wi-Fi invité, l’isolation des clients ou un autre pare-feu peuvent encore empêcher
l’accès. Lors de la recette du 13 novembre chez Marc, HTTP, nom local, recherche,
lecture PDF par plage et les trois services HTTPS avec la CA locale sont validés
sur le PC. Le contrôle depuis un autre appareil reste à faire par Marc.


Le raccourci **Suivi bibliothèque SetupSurvie** est également installé. Le suivi
reconnaît `python.exe` et `pythonw.exe` ; il lit la longueur réelle des partiels
par un handle partagé Windows, car la taille d’annuaire peut rester à zéro tant
que le fichier est ouvert. Seules les lignes d’erreur sont affichées comme telles,
pas les titres des contenus en cours. Fermer ou rouvrir ce suivi ne coupe aucun
transfert. Ces corrections ont été vérifiées sur la reprise active de Marc.


Le raccourci Arrêter conserve un marqueur d’arrêt volontaire pour le site : la
surveillance ne le relance pas cinq minutes plus tard. Ouvrir SetupSurvie ou une
commande `up` explicite permet de reprendre. La pause de téléchargement reste
indépendante ; ne pas confondre l’arrêt du site avec celui du superviseur de
bibliothèque. Les mises à jour inachevées bloquent les redémarrages automatiques
jusqu’à leur récupération explicite.


## Cartes incluses dans la préparation de base — 0.1.33

En installation **avec Internet**, le lanceur prépare désormais les fonds locaux
PMTiles : Sud (PACA, Occitanie et Corse, zoom 13) et Solliès-Ville (zoom 15), puis
le relief et les lieux/adresses dans un rayon de 25 km autour de Solliès-Ville.
Il s’agit des zones du pilote de Marc, déclarées dans `deploy/map-catalog.json`,
pas d’une couverture mondiale. Les altitudes permettent l’ombrage et la coupe
du terrain. Le calcul d’itinéraires reste une préparation distincte.

L’outil PMTiles Windows/Linux x64 est téléchargé depuis sa publication officielle
avec empreinte SHA-256 figée, avant toute exécution. Les cartes terminées sont
vérifiées et réutilisées. Une extraction partielle est conservée en diagnostic,
puis reprise en recommençant uniquement cette extraction ; le programme PMTiles
ne permet pas ici la reprise octet par octet. Le fond quotidien officiel peut
expirer : un fond récent du même fournisseur est alors recherché, avec sa **vraie
date et sa source enregistrées**, sans prétendre conserver l’ancienne édition.

Le relief est préparé indépendamment des adresses/points d’intérêt. Une panne
Overpass conserve les fonds et altitudes déjà prêts et affiche un avertissement
explicite ; `catalog/map-installation.json` distingue les états de chaque jeu.
Les fournisseurs fixes de secours sont conservés dans le manifeste du jeu acquis.
Les coordonnées de la zone sont transmises à ces fournisseurs. Les lieux OSM ne
prouvent pas un accès, des horaires à jour, une ressource disponible ou de l’eau potable.

Une installation **depuis un kit hors ligne** ne télécharge rien : les cartes
présentes sont contrôlées ; les jeux absents sont signalés explicitement. Préparer
le kit avec les cartes avant de l’apporter sur un site sans Internet.

Pour compléter une installation existante, sans réinstaller les comptes ni
relancer un modèle :

```powershell
python application/scripts/setup.py --work-dir prive prepare-maps
```

Adapter les deux chemins au dossier existant. Cette commande vérifie les cartes,
prépare les éléments manquants et réindexe le guide cartographique. Le suivi de
bibliothèque affiche aussi le nombre de fonds présents : les 100 % d’un plan
Kiwix/PDF ne signifient plus implicitement que des cartes ont été téléchargées.
