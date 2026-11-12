# Installer Windows en deux étapes

**Guide actuel — pilote 0.1.17, 12 novembre 2026.** Lanceurs implémentés ; installation
réelle sur Windows vierge, redémarrages, RTX 5060 et téléphones encore à valider.
Ce parcours ne modifie pas l’installation 0.1.16 en cours chez Marc.

## Préparer le PC

Depuis le dépôt récupéré ou décompressé, double-cliquer sur
**`1-Preparer-le-PC.cmd`**. Python et WinGet ne sont pas nécessaires pour ce lanceur.
Il nécessite Windows 11 24H2 ou plus récent **x64**, la virtualisation activée dans
le BIOS/UEFI, Internet et la possibilité de valider les demandes administrateur.

Le lanceur vérifie WSL 2, Python x64 3.11 à 3.15, Docker Desktop et Ollama. Il
conserve les installations présentes, installe les composants absents et ne
met pas automatiquement les logiciels existants à niveau. Les versions présentes
ne sont pas toutes certifiées compatibles par ce seul diagnostic ; le second
lanceur vérifie réellement Docker/Compose et les services.

Les installateurs manquants sont téléchargés depuis Python, Docker et Ollama,
avec SHA-256 vérifié avant exécution. Les versions, URL, empreintes et sources
consultées figurent dans `deploy/windows-installers.json`. Ces métadonnées ont
été relues dans les [manifestes Microsoft](https://github.com/microsoft/winget-pkgs) ;
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

1. Un dossier dédié sur le disque de données, par exemple `D:\SetupSurvie`.
2. Le dossier du kit contenant `manifest.json`, ou Entrée pour télécharger.
3. Une adresse IPv4 du réseau Windows privé affiché pour partager le serveur,
   ou Entrée pour limiter l’accès au PC.

Docker Desktop démarre si nécessaire. Terminer son accueil et vérifier **Settings
→ Resources → Advanced → Disk image location**. Le lanceur attend une confirmation
de l’emplacement : il ne déplace pas un disque Docker existant. Une autre instance
Docker déjà accessible doit utiliser des conteneurs Linux.

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
Les tests de disponibilité n’interrogent aucun modèle. Une pause existante reste
respectée ; le démarrage normal d’une nouvelle installation lance le service
Ollama sans génération de réponse.

Exemple avec paramètres :

```powershell
.\2-Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Kit E:\livraison-marc -LanHost 192.168.1.50
```

Pour un kit ancien sans ces deux fichiers à sa racine, utiliser le second lanceur
du dépôt 0.1.17 en lui indiquant le dossier du kit. Le logiciel installé reste
celui du kit, avec sa version. Les nouveaux exports/rafraîchissements du kit et
les paquets de mise à jour incluent les deux lanceurs.

## Reprendre une interruption

Le journal `.installation.json` enregistre la source, les options et la phase
d’installation ; un verrou système empêche deux installations simultanées dans
la même destination et est libéré à la fermeture du processus.

Après une interruption, conserver le dépôt ou kit source inchangé puis lancer :

```powershell
.\2-Installer-SetupSurvie.cmd -BaseDir D:\SetupSurvie -Resume
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
