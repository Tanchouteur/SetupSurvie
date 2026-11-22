# Pilote chez Marc : kit, accès réseau, sauvegarde

**Guide de référence — revu le 20 novembre 2026 pour la 0.67.0.** Les essais
sur le PC Linux de Louis ne remplacent pas la recette sur le Windows de Marc
(RTX 5060 Ti 8 Go) et ses appareils du réseau local : elle reste à faire sur
place. Pour l’installation Windows pas à pas, voir le
[parcours Windows](deux-etapes-windows.md) ; pour le portail, le
[guide du portail](../utilisation/portail.md) ; pour la préparation du kit, le
[guide du kit](preparer-kit-hors-ligne.md). Le [bilan Windows](../essais/2026-11-12-installateur-windows-simple.md)
distingue les contrôles réalisés de la recette complète.

## Ce que Marc peut essayer

- **Assistant du portail** : trois modes conseillés et un groupe « Autres modèles
  à comparer ». Le kit contient sept modèles : GPT-OSS 20B, Gemma4 E4B, Qwen3.5
  4B/9B/27B, Gemma4 26B A4B et Qwen3.8 27B (`deploy/model-profiles.json`). Plusieurs
  réglages d’un même modèle ne recopient pas ses fichiers. Le choix définitif
  des modes ne se déduit pas du seul nombre de paramètres : voir le bilan des tests.
- **Ses outils** : recherche et lecture des documents locaux, calcul, conversion
  d’unités.
- **Open WebUI** (lien **Assistant avancé · Open WebUI**) : dossiers, collections
  et conversations avancées. Il reprend le profil choisi dans le portail, mais
  **les historiques restent distincts** : une conversation créée dans une
  interface n’est pas recopiée dans l’autre. Les outils des deux interfaces
  diffèrent (le calculateur et le connecteur Kiwix du portail ne sont pas des
  outils natifs d’Open WebUI).
- **Comparer des modèles** : nouvelle conversation, même question et mêmes
  documents ; noter le modèle, le délai, les erreurs et l’utilité. Refaire la
  question avec un autre modèle sans lui montrer la réponse précédente.

Les mesures de la RTX 2060 de Louis ne prédisent pas celles de Marc : la RAM, le
contexte, les fichiers du modèle et la mémoire vidéo disponible comptent aussi.

**Fonds complet.** Aucun plafond documentaire logiciel chez Marc depuis 0.1.15.
Le kit reste une sélection réduite ; on complète directement sur son PC avec la
[préparation du fonds complet](../bibliotheque/bibliotheque-complete-marc.md). Les
limites de taille du laboratoire de Louis ne fixent pas le contenu cible de Marc.

## Avant de copier le kit

Le kit ne contient pas les logiciels système et ne prépare pas un Windows vierge
hors ligne. Il faut d’abord, **avec Internet**, installer ou vérifier :

- Windows 11 24H2 ou plus récent (x64), virtualisation activée, WSL 2 ;
- le pilote NVIDIA adapté à la carte ([GPU pris en charge par Ollama](https://github.com/ollama/ollama/blob/main/docs/gpu.mdx)) ;
- Python 3.11 à 3.15 (x64), Docker Desktop (conteneurs Linux), Git et Ollama
  Windows. Le [parcours Windows](deux-etapes-windows.md#préparer-le-pc) les prépare ;
  la référence Ollama du projet est dans `deploy/versions.json`.

Ensuite, hors ligne :

- **Place** : vérifier la RAM et l’espace libre. Le kit constaté en 0.1.14 fait
  environ 161 Go : prévoir NTFS ou exFAT (FAT32 ne convient pas) et de la place
  pour la copie des données et les images Docker.
- **Docker** : régler son disque virtuel sur le SSD de données avant d’installer ;
  le paquet ne déplace pas un disque Docker existant.
- **Modèles** : les 27B peuvent utiliser beaucoup de RAM et rester lents avec 8 Go
  de VRAM ; le pilote doit permettre de les annuler.
- **Contenu du kit** : images de services, sept modèles, BGE-M3, Whisper, archives
  sélectionnées (Wikipédia français, Wikilivres français et anglais). Wikipédia
  anglais, exclue du kit 0.1.14, est incluse par défaut dans les exports depuis
  0.1.15 si elle est présente.
- **Cartes** : deux fonds PMTiles (Sud et Solliès-Ville), lieux, adresses et relief
  autour du centre public de Solliès-Ville (10 km dans le kit 0.1.14), trois
  graphes de trajet (marche, moto, voiture) et leur image OSRM. Ces données ne
  couvrent pas toute la France.
- **Confidentialité** : le kit ne contient aucun compte, historique ni certificat
  privé de Louis.

## Installer à partir du kit

Le plus simple est `Installer-SetupSurvie.cmd -Kit D:\livraison-marc` (voir le
[parcours Windows](deux-etapes-windows.md)). La commande directe est :

```powershell
cd D:\livraison-marc\app
py -3 scripts\pilot_kit.py verify D:\livraison-marc
py -3 scripts\pilot_kit.py install D:\livraison-marc --target windows --data-dir D:\SetupSurvie\donnees --work-dir D:\SetupSurvie\prive
```

Copier le dossier complet `livraison-marc` sur le disque choisi (adapter la lettre
`D:`), sans modifier les fichiers après la vérification des empreintes, et
choisir des dossiers de données et de réglages **vides**. Le contrôle et la copie
de plus de 100 Go prennent plusieurs minutes.

`install` importe les images locales, copie les fichiers, vérifie les caches hors
ligne, démarre les services et configure les profils partagés dans Open WebUI. Il
ne télécharge pas les modèles. Ouvrir ensuite le portail et choisir un profil
(sans mot de passe). Conserver le dossier privé : réglages et sauvegardes.

Le code installé est dans `D:\SetupSurvie\application`, séparé du kit, qui peut
ensuite être débranché. L’installation crée sur le Bureau **Ouvrir SetupSurvie**,
**Arrêter SetupSurvie**, **Mettre à jour SetupSurvie**, **Transférer SetupSurvie**
(et **Suivi bibliothèque SetupSurvie** si le suivi est présent), et active le démarrage à l’ouverture
de session.

- **Ouvrir SetupSurvie** démarre Docker Desktop si nécessaire, lance les services,
  puis ouvre le portail. À l’ouverture de session, le même lancement se fait sans
  ouvrir le navigateur. Une pause du moteur est conservée. Ce n’est pas un service
  avant ouverture de session.
- **Arrêter SetupSurvie** met en pause les préparations, puis arrête les services
  de cette installation et son Ollama dédié ; les données restent. Le PC, Docker
  Desktop et les autres projets ne sont pas arrêtés. Les autres appareils perdent
  l’accès jusqu’à la remise en route ; fermer seulement le navigateur laisse le
  serveur disponible.
- En cas d’échec, une fenêtre explique le problème ; les journaux `demarrage.log`
  et `arret.log` sont dans le dossier privé.

Pour recréer les raccourcis ou régler le démarrage automatique :

```powershell
cd D:\SetupSurvie\application
.\scripts\create-shortcuts.ps1 -WorkDir D:\SetupSurvie\prive -Startup          # activer
.\scripts\create-shortcuts.ps1 -WorkDir D:\SetupSurvie\prive -DisableStartup   # garder les raccourcis, sans démarrage automatique
```

Une nouvelle installation peut aussi recevoir `--no-startup` (`pilot_kit.py install`)
ou `-NoStartup` (`install.ps1`). Une mise à jour ne réactive pas un démarrage
désactivé : la commande de création est volontaire. Les lanceurs et l’ouverture
de session restent à essayer sur le Windows réel de Marc.

Depuis la 0.100.0, le kit public peut aussi démarrer sur un PC Linux sans
Python ni Docker. Préparer à l’avance
[les installateurs du kit Linux](preparer-kit-hors-ligne.md#ajouter-les-installateurs-linux).
Sur Debian 12, Debian 13 ou Ubuntu 22.04 x86-64, avec un bureau équipé de
Zenity et PolicyKit, lancer le même fichier et choisir un dossier système
sur le disque cible. L’autorisation administrateur se fait dans une
fenêtre. Le lanceur installe ses outils et un moteur Docker dédié dans
le dossier choisi. Les services locaux démarrent avec le système après
installation. Le kit public crée une nouvelle installation. La
[copie de secours Linux complète](../exploitation/transfert-installation.md#installer-depuis-le-ssd-de-secours)
propose le point de restauration protégé.

Depuis la 0.99.0, sur un PC Linux déjà préparé, ouvrir
**Installer-Kit-SetupSurvie.desktop** dans le dossier `app` du SSD.
Il faut Python avec Tkinter, Docker et Compose déjà disponibles. Choisir
le disque et confirmer la création d’un nouveau dossier. Le kit
fonctionne sur le processeur et le site se lance avec l’IA en pause.
Après un redémarrage, ouvrir **Ouvrir-SetupSurvie.desktop** dans le
dossier installé, avec Docker démarré. Le SSD peut être retiré après
l’installation terminée.

Depuis la 0.101.0, le lanceur graphique reprend dans le dossier
`SetupSurvie-Kit` si on choisit le même disque avec le même kit après
une coupure. Il contrôle les fichiers de la copie et recopie ceux qui
sont incomplets. Si les services avaient commencé à démarrer, il
relance la vérification avec les données actuelles. Le parcours sans
Python ni Docker réutilise aussi les outils déjà extraits. Un dossier
déjà occupé par une autre installation reste protégé.

Sur un PC Linux avec Python 3.11, Docker et Compose déjà installés, le kit
public peut utiliser le processeur sans GPU NVIDIA depuis la 0.98.0. Depuis
le dossier `app` du SSD, lancer la commande suivante. Choisir un autre
emplacement si les dossiers sont déjà utilisés.

```sh
python3 scripts/pilot_kit.py install .. --target linux --cpu --data-dir "$HOME/SetupSurvie/data" --work-dir "$HOME/SetupSurvie/private"
```

Le lanceur graphique pour préparer un PC Linux depuis le SSD est dans la
[copie de secours Linux complète](../exploitation/transfert-installation.md#installer-depuis-le-ssd-de-secours).
La notice **LISEZ-MOI.html** à la racine du kit public décrit les deux parcours.

## Accès sur le PC serveur

- Portail : `http://localhost:8080`
- Open WebUI : `http://localhost:3000`
- Kiwix : `http://localhost:8081`

`localhost` désigne l’appareil sur lequel on le saisit ; sur un téléphone, ce n’est
pas le PC de Marc.

## Accès depuis tout le réseau local

1. Relier serveur et lecteurs au même réseau domestique (un Wi-Fi invité ou
   l’isolation des appareils bloque l’accès).
2. Relever l’IPv4 du serveur avec `ipconfig` (par exemple `192.168.1.50`) et la
   réserver dans le routeur.
3. Configurer l’écoute réseau, puis redémarrer les services :

```powershell
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive configure --lan --lan-host 192.168.1.50 --name survie
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive up
```

4. Sur un réseau Windows déclaré **Privé**, exécuter une fois
   `scripts\open-lan-firewall.ps1` dans PowerShell administrateur : règle limitée
   aux ports Web et au sous-réseau local, sans redirection de port Internet. Le
   script bloque aussi les ports internes `11435` et `11436` sur les interfaces
   physiques ; ne jamais les ouvrir aux lecteurs, et vérifier les règles Ollama
   préexistantes. (Le lanceur d’installation applique ces règles lorsqu’une IPv4
   lui est donnée.)
5. Depuis les autres appareils : `https://192.168.1.50:8443` (portail), `:8444`
   (Open WebUI), `:8445` (Kiwix). Les liens du portail s’adaptent à l’adresse et
   au protocole utilisés.

Les ports HTTP (`8080`, `3000`, `8081`) fonctionnent aussi sur le réseau local ;
HTTPS chiffre le transport. Caddy crée une autorité de certification locale propre
à l’installation, sans Internet ; ses clés sont dans `donnees\state\caddy`
([principe](https://caddyserver.com/docs/running)). Exporter son certificat
**public**, puis l’installer sur chaque appareil :

```powershell
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive certificate D:\SetupSurvie\certificat-local.crt
Import-Certificate -FilePath D:\SetupSurvie\certificat-local.crt -CertStoreLocation Cert:\CurrentUser\Root
```

Téléphones : transférer ce même fichier public ; Android : réglages de sécurité /
installation d’un certificat d’autorité ; iOS : installer le profil, puis activer
sa confiance dans Réglages / Général / Informations / Réglages de confiance des
certificats (intitulés variables). Références : [Apple](https://support.apple.com/fr-fr/102390),
[Google Pixel / Android](https://support.google.com/pixelphone/answer/2844832?hl=fr).
Comparer l’empreinte avec le certificat remis par le serveur, puis vérifier que la
page HTTPS n’affiche plus d’avertissement et que la permission micro est proposée.
Ne jamais transférer le dossier des clés privées Caddy.

Revenir à un usage limité au serveur : `configure --no-lan`, puis `up`. Supprimer
la règle de pare-feu : `Remove-NetFirewallRule -Name SetupSurvie-Web-Private`.

Laboratoire Linux de Louis : `./scripts/lab.sh network --lan-host ADRESSE_IP` (sans
`--lan-host`, retour à l’accès local). Cette commande ne demande pas de privilèges
administrateur et ne touche pas au pare-feu Linux.

Le nom `survie.local` et Safari sur iPhone ne sont pas validés : conserver l’accès
par IP et QR code (**Mon appareil → Paramètres → Profils et connexion**).

## Sauvegarder et restaurer

Conserver le kit public d’origine et une sauvegarde privée des comptes,
historiques, guides et certificats. La sauvegarde arrête brièvement le site et
les services de compte pour obtenir une copie cohérente, puis les redémarre. Les
modèles, ZIM et caches du kit ne sont pas recopiés.

```powershell
py -3 scripts\pilot_backup.py backup E:\Sauvegardes\survie-essai-01 --work-dir D:\SetupSurvie\prive
py -3 scripts\pilot_backup.py restore E:\Sauvegardes\survie-essai-01 --kit D:\livraison-marc --work-dir D:\SurvieRestaure\prive --data-dir D:\SurvieRestaure\donnees
```

Règles de la restauration (sur une installation arrêtée ou une autre machine) :

- dossiers vides ; sauvegarde, kit, données, réglages et application dans des
  dossiers séparés, sans imbrication ;
- ports libres ; adresse LAN à reconfigurer si elle change ;
- la sauvegarde conserve la pause du moteur, le registre des contenus téléchargés
  et le classement des collections (`collection-sort.json`) ; la restauration
  conserve une pause sauvegardée. Un diagnostic en pause contrôle la bibliothèque
  et reporte les contrôles Ollama ; un test avec inférence est refusé tant que la
  pause n’est pas levée ;
- le registre restauré décrit les téléchargements passés : il ne remplace ni leurs
  fichiers ni une vérification d’intégrité ;
- les anciennes sauvegardes restent acceptées mais ne restituent pas ce qu’elles
  ne contenaient pas ;
- la restauration conserve les comptes et secrets ; une installation neuve du kit
  en crée de nouveaux.

Avant de sauvegarder, mettre les préparations documentaires en pause et attendre
leur arrêt : un transfert ou une préparation concurrente entraîne un refus
explicite. Les index de recherche sont copiés seulement quand leurs écrivains ont
libéré leurs verrous (le refus a lieu avant l’arrêt du site) ; un index restauré
dont l’archive a changé est signalé périmé et demande une reprise. Les fichiers
`.lease` ne sont pas des données à restaurer et ne doivent pas être supprimés :
voir [Coupures et redémarrage](../exploitation/coupures-et-redemarrage.md).

Les ZIM ajoutés après le kit et les nouveaux modèles se sauvegardent séparément ou
s’incluent dans un nouveau kit. Les sauvegardes privées contiennent des secrets :
les garder hors de la bibliothèque publique.

### Restaurer les données personnelles sur l’autre système

Depuis la 0.94.0, une machine Linux préparée peut charger une sauvegarde privée
Windows, et une machine Windows préparée peut charger une sauvegarde privée
Linux. Il faut créer cette sauvegarde avec la 0.94.0 ou une version ultérieure et
emporter le kit public complet correspondant exactement à l’installation
d’origine, avec la même version d’Open WebUI. Le kit fournit les modèles, les
ZIM et les cartes. Préparer sur la machine cible Python, Docker avec Compose
et les conteneurs Linux. Sous Windows, préparer aussi Ollama pour pouvoir
réactiver l’IA après restauration. Voir le
[manuel de secours](../exploitation/manuel-de-secours.md#7-restaurer-une-sauvegarde-personnelle)
pour les prérequis hors ligne.

Sur une machine préparée avec Python et son interface Tkinter, ouvrir dans le
dossier `app` du kit **Restaurer-Mes-Donnees-SetupSurvie.cmd** sous Windows ou
**Restaurer-Mes-Donnees-SetupSurvie.desktop** sous Linux. La fenêtre demande de
choisir le dossier de la sauvegarde, puis le disque de destination. Elle crée
un nouveau dossier horodaté, affiche l’étape en cours et propose d’ouvrir le
site à la fin. Ce lanceur 0.95.0 couvre aussi le changement de PC avec le même
système. Un poste Linux doit déjà avoir le paquet Tkinter de sa distribution.

Sur la machine de destination, lancer la commande depuis le dossier `app` du
kit. Remplacer les chemins d’exemple par ceux du SSD et du disque cible.
Réserver sur le disque cible l’espace des fichiers à copier, plus 20 Gio de
marge par volume de destination. Laisser les ports habituels de SetupSurvie
libres. Le débit du SSD et le volume de fichiers déterminent la durée, avec
une lecture pour contrôler la source puis une autre pour vérifier la copie.

**Sauvegarde Windows vers cible Linux**

```bash
python3 scripts/pilot_backup.py restore /media/secours/sauvegarde --kit /media/secours/kit --work-dir "$HOME/SurvieRestaure/private" --data-dir "$HOME/SurvieRestaure/data" --target linux
```

**Sauvegarde Linux vers cible Windows**

```powershell
py -3 scripts\pilot_backup.py restore E:\Secours\sauvegarde --kit E:\Secours\kit --work-dir D:\SurvieRestaure\private --data-dir D:\SurvieRestaure\data --target windows
```

La restauration crée une installation indépendante, accessible sur
`http://127.0.0.1:8080`. Les profils, historiques et documents personnels sont
copiés depuis la sauvegarde. Les certificats et l’adresse réseau concernent la
nouvelle machine et sont à établir sur celle-ci. Sous Linux, la configuration
utilise le processeur par défaut. Le moteur IA reste en pause sur les deux
systèmes jusqu’à une action volontaire. Avant de retirer le SSD de secours,
ouvrir un profil, un échange existant et un document personnel.

À partir de la 0.97.0, le nouveau dossier de destination contient
**Ouvrir-SetupSurvie.cmd** sous Windows ou **Ouvrir-SetupSurvie.desktop** sous
Linux. Après un redémarrage du PC, ce lanceur démarre et vérifie les services
locaux, puis ouvre le site. Laisser le dossier restauré à son emplacement.
Le kit et la sauvegarde peuvent être retirés après la restauration terminée.
Docker et Python doivent rester disponibles sur le PC. Sous Linux, le service
Docker doit avoir démarré. Sous Windows, le lanceur peut démarrer Docker Desktop.

Depuis la 0.96.0, en cas de coupure, rouvrir le lanceur, choisir la même
sauvegarde et le même disque, puis accepter la reprise. Le journal
`restauration.json` dans le dossier de destination identifie l’opération.
Les fichiers déjà vérifiés sont réutilisés, et les fichiers partiels sont
recopiés. Si les services avaient commencé à démarrer, la reprise repart
des données actuelles de la copie et relance les contrôles. En ligne de
commande, ajouter `--resume` à la commande d’origine avec les mêmes
destinations et les mêmes sources. Un kit ou une sauvegarde modifiés
demandent une nouvelle restauration. La recette sur deux machines
différentes hors ligne reste à effectuer.

## Moteur, mode jeu et comparaisons

**Mon appareil → Vue d’ensemble** (« État de l’appareil ») affiche le moteur, le
modèle chargé, la file des questions, la VRAM, l’activité et la température du
GPU (tous programmes confondus), la RAM et l’espace libre. Le démarrage et l’arrêt
du moteur sont dans **Mon appareil → Paramètres → Assistant**, réservés au profil
Famille. Lorsque le moteur est en pause (mode jeu), le bouton devient **Forcer le
démarrage de l’IA**, avec un avertissement sur les performances du jeu ; le
modèle se charge à la prochaine question. Un redémarrage des services respecte la
pause.

Le portail parle à un petit contrôleur du PC hôte, authentifié par un secret propre
à l’installation, sans accès au shell. Les ports `11435` et `11436` ne doivent pas
être ouverts aux lecteurs. Le blocage par le pare-feu Windows reste à vérifier
sur le Windows réel.

Pour refaire les comparaisons de modèles (jeux arrêtés ; aucun modèle n’est
téléchargé) :

```powershell
py -3 scripts\compare_models.py --work-dir D:\SetupSurvie\prive --profiles rapide moyenne approfondie --repetitions 3
py -3 scripts\compare_models.py --work-dir D:\SetupSurvie\prive --profiles test-qwen4 test-qwen9 test-qwen27 test-gemma26 test-qwen38
```

La seconde ligne se lance séparément pour limiter la durée. Résultats, version
Ollama et relevé du GPU sont dans le dossier privé `comparaisons`.

## Recette sur le PC de Marc (à faire)

Relever GPU, RAM et version Ollama ; vérifier l’usage réel du GPU ; choisir un
profil ; chercher un article et un passage de guide ; comparer trois modèles sur
une même question ; ouvrir les sources ; vérifier un calcul ; annuler un gros
modèle ; retrouver les conversations dans chaque interface ; télécharger un
modèle et l’utiliser hors ligne ; couper Internet en gardant le réseau local ;
redémarrer le PC ; faire une sauvegarde puis une restauration distincte. Une
recette Windows ou téléphone non exécutée reste « à vérifier sur place ».

## Arrêt, nettoyage, mises à jour

`survie.ps1 --work-dir D:\SetupSurvie\prive down` arrête les services, le
contrôleur, l’annonce du nom local et l’Ollama dédié ; les données restent. Après
sauvegarde, les dossiers de données, réglages et kit peuvent se supprimer dans
l’Explorateur (sans toucher aux répertoires d’autres projets Docker). Règles de
pare-feu du projet, en PowerShell administrateur :
`Remove-NetFirewallRule -Name SetupSurvie-Web-Private,SetupSurvie-mDNS-Private,SetupSurvie-Engine-Physical`.

Pour remplacer seulement le logiciel, préserver les comptes et ajouter des lots,
suivre le [guide des mises à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

## Historique

- **Avant 0.1.29** : le produit demandait un compte, un mot de passe et un code
  de secours (identifiant `admin` en 0.1.12). **Depuis 0.1.29**, on choisit un
  profil local sans mot de passe ; les anciens comptes et leurs données sont
  conservés. Voir les [profils locaux](../utilisation/profils-locaux.md).
- `scripts/setup.py recover-account` reste disponible pour une maintenance native
  ou une ancienne version, hors parcours normal. Ne jamais supprimer les bases
  pour retrouver un profil.
- Le mot de passe interne du compte natif Open WebUI est généré aléatoirement par
  `scripts/setup.py` ; il n’est jamais demandé aux utilisateurs ni écrit dans la
  documentation. Les secrets de session et de contrôle sont aussi générés
  aléatoirement.
- **0.1.13** : création automatique des raccourcis du Bureau. **0.1.14** : kit
  de référence (161 Go, sans Wikipédia anglaise). **0.1.15** : fonds complet
  possible chez Marc. **0.1.20** : lanceur Windows unique.
