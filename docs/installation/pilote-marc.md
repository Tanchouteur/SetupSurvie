# Première version d’essai chez Marc

> Guide de référence, actualisé le 12 novembre 2026 pour le pilote 0.1.22. Le [bilan Windows](../essais/2026-11-12-installateur-windows-simple.md) distingue les contrôles réalisés et la recette complète encore à faire.

Ce guide décrit le paquet pilote. Les essais réalisés sur le PC Linux de Louis ne remplacent pas la recette sur le Windows de Marc, sa RTX 5060 8 Go et ses appareils du réseau local. Les mesures de la RTX 2060 ne prédisent pas directement ses temps de réponse. La RAM, le contexte, les fichiers du modèle et la mémoire vidéo disponible comptent aussi.

## Ce que Marc pourra essayer

Le site propose trois modes conseillés et un groupe « Autres modèles à comparer ». Les sept modèles téléchargés sont conservés pour cette première campagne : Gemma4 E4B, GPT-OSS 20B, Qwen3.5 4B/9B/27B, Gemma4 26B A4B et Qwen3.8 27B. Plusieurs réglages d’un même modèle ne recopient pas ses fichiers. Le choix définitif des modes est documenté dans le bilan des tests, pas déduit du seul nombre de paramètres.

Pour comparer : nouvelle conversation, même question et mêmes documents, puis noter le modèle, le délai, les erreurs et l’utilité. Refaire aussi la question avec un autre modèle sans lui montrer la réponse précédente. Une carte graphique plus grande permettra de refaire les mesures avec les mêmes cas.

L’assistant du site peut rechercher et lire les documents locaux, calculer et convertir des unités. Open WebUI reste disponible pour ses conversations, dossiers et collections documentaires. **Même compte, historiques distincts** : les conversations créées dans une interface ne sont pas recopiées dans l’autre. Le site fournit un lien visible vers Open WebUI. Les outils du site et ceux d’Open WebUI ne sont pas identiques ; le connecteur Kiwix et le calculateur du site ne sont pas automatiquement des outils natifs Open WebUI.

## Fonds complet souhaité par Marc

Depuis 0.1.15, aucun plafond documentaire logiciel chez Marc. Le kit existant reste une sélection réduite ; compléter directement sur son PC avec la [préparation automatique du fonds complet](../bibliotheque/bibliotheque-complete-marc.md). Les limites de taille du laboratoire de Louis ne fixent pas le contenu cible de Marc.

## Avant de copier le kit

Depuis 0.1.20, le [lanceur Windows unique](deux-etapes-windows.md)
enchaîne la préparation des prérequis avec Internet et l’installation. Ses diagnostics,
conflits et raccourcis ont été testés chez Marc sans modifier la 0.1.16 en service.
L’installation complète sur un Windows vierge reste à valider.

Pour un PC sans prérequis, préparer Windows, WSL 2, le pilote NVIDIA,
Python, Docker Desktop et Ollama **avec
Internet**, puis utiliser le kit sans Internet. Le kit ne contient pas leurs
installateurs et ne prépare pas un Windows vierge entièrement hors ligne.
Un installateur système hors ligne complet reste hors du périmètre de ce pilote.


- Windows 11 à jour, pilote NVIDIA compatible avec la RTX 5060, Python 3.11 à 3.15 (x64), Docker Desktop utilisant les conteneurs Linux et Ollama Windows. La référence Ollama du projet est dans `deploy/versions.json` ; relever toute différence pour les comparaisons. [GPU pris en charge par Ollama](https://github.com/ollama/ollama/blob/main/docs/gpu.mdx).
- Vérifier la quantité de RAM et l’espace libre. Les modèles de 27B peuvent utiliser beaucoup de RAM et rester lents avec 8 Go de VRAM. Le pilote doit permettre de les annuler.
- Docker Desktop doit être configuré pour placer son disque virtuel sur le SSD de données choisi ; le paquet ne déplace pas automatiquement un disque Docker existant.
- Le kit contient les images de services, les sept modèles, BGE-M3, Whisper et les archives sélectionnées. Le kit initial, constaté en 0.1.14, exclut la très grosse Wikipédia anglaise ; Wikipédia français et Wikilivres français/anglais sont inclus. Wikipédia anglaise reste disponible sur le PC de Louis. Les nouveaux exports 0.1.15 l’incluent par défaut lorsqu’elle est présente ; elle peut aussi être téléchargée directement chez Marc.
- Depuis le kit 0.1.14 : deux fonds PMTiles (Sud et Solliès-Ville), lieux, adresses et relief autour du centre public de Solliès-Ville sur 10 km, trois graphes de trajet (marche, moto, voiture) et leur image OSRM. Ces données ne couvrent pas les trajets dans toute la France. Voir la [préparation et vérification du kit](preparer-kit-hors-ligne.md).
- Le kit ne contient aucun compte, mot de passe, historique ni certificat privé de Louis. Les réglages et identifiants de Marc sont créés à l’installation.

## Installer à partir du kit

Copier le dossier complet `livraison-marc` sur le disque choisi. Le kit 0.1.14 actualisé fait environ 161 Go ; prévoir un support NTFS ou exFAT et suffisamment d’espace pour la copie des données et les images Docker. FAT32 ne convient pas aux gros fichiers de ce kit. Ne pas modifier les fichiers après la vérification des empreintes. Les exemples utilisent `D:` : adapter à la lettre réelle du SSD. Choisir des dossiers de données et réglages **vides**. Le contrôle complet des empreintes et la copie de plus de 100 Go peuvent prendre plusieurs minutes.

```powershell
cd D:\livraison-marc\app
py -3 scripts\pilot_kit.py verify D:\livraison-marc
py -3 scripts\pilot_kit.py install D:\livraison-marc --target windows --data-dir D:\SetupSurvie\donnees --work-dir D:\SetupSurvie\prive
```

L’installation importe les images locales, copie les fichiers, vérifie les caches hors ligne, démarre les services et configure les profils partagés dans Open WebUI. Elle ne télécharge pas les modèles. Les logiciels prérequis doivent être installés auparavant. Depuis 0.1.29, ouvrir le portail et choisir un profil, sans mot de passe. Conserver le dossier privé pour les réglages et sauvegardes.

Le code installé se trouve dans `D:\SetupSurvie\application`, séparé du kit de transport. À partir de 0.1.13, l’installation Windows crée automatiquement **Ouvrir SetupSurvie** et **Arrêter SetupSurvie** sur le Bureau, avec le logo du projet, et active le démarrage à l’ouverture de session de cet utilisateur. Le kit de transport peut ensuite être débranché.

Pour une installation existante, ajouter ou recréer ces raccourcis depuis la copie installée :

```powershell
cd D:\SetupSurvie\application
.\scripts\create-shortcuts.ps1 -WorkDir D:\SetupSurvie\prive -Startup
```

**Ouvrir SetupSurvie** démarre Docker Desktop si nécessaire, attend son démarrage, lance les services puis ouvre le portail. À l’ouverture de session, le même lancement s’effectue sans ouvrir le navigateur. Aucun modèle n’est interrogé et une pause du moteur est conservée. Il s’agit d’un démarrage après connexion à Windows, pas d’un service avant ouverture de session.

**Arrêter SetupSurvie** met en pause les préparations en cours, puis arrête les services de cette installation et son Ollama dédié ; les données restent conservées. Il peut attendre la fin d’un échange réseau avant de terminer. Le PC, Docker Desktop et les autres projets ne sont pas arrêtés. Les autres appareils du réseau perdent l’accès au serveur jusqu’à sa remise en route. Fermer seulement le navigateur laisse le serveur disponible.

Pour désactiver le démarrage automatique tout en gardant les deux raccourcis du Bureau :

```powershell
.\scripts\create-shortcuts.ps1 -WorkDir D:\SetupSurvie\prive -DisableStartup
```

Une nouvelle installation peut aussi demander `--no-startup` à `pilot_kit.py install` ou `-NoStartup` à `install.ps1`. Les raccourcis manuels restent créés. Après mise à jour d’une ancienne installation, la commande de création est volontaire : une mise à jour ne réactive pas une préférence de démarrage désactivée.

En cas d’échec, une fenêtre explique le problème et les journaux `demarrage.log` ou `arret.log` restent dans le dossier privé. Les lanceurs et l’ouverture de session doivent encore être essayés sur le Windows réel de Marc.

## Accès sur le PC serveur

- Site : `http://localhost:8080`
- Open WebUI, dossiers et conversations : `http://localhost:3000`
- Kiwix : `http://localhost:8081`

`localhost` désigne toujours l’appareil sur lequel on le saisit. Sur un téléphone, il ne désigne donc pas le PC de Marc.

## Accès depuis tout le réseau local

1. Relier le serveur et les lecteurs au même réseau domestique. Un réseau Wi-Fi invité ou une option d’isolation des appareils peut empêcher l’accès.
2. Sur le PC serveur, relever l’adresse IPv4 avec `ipconfig`, par exemple `192.168.1.50`. Réserver cette adresse dans le routeur pour éviter qu’elle change.
3. Configurer l’écoute réseau, puis redémarrer les services avec le lanceur :

```powershell
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive configure --lan --lan-host 192.168.1.50 --name survie
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive up
```

4. Sur un réseau Windows déclaré **Privé**, exécuter une fois `scripts\open-lan-firewall.ps1` dans PowerShell administrateur. La règle concerne les ports Web et le sous-réseau local. Aucune redirection de port sur Internet n’est nécessaire. Ne pas ouvrir le port API Ollama `11435` aux lecteurs et vérifier les éventuelles règles Ollama préexistantes.
5. Depuis les autres appareils, utiliser `https://192.168.1.50:8443` pour le site, `:8444` pour Open WebUI et `:8445` pour Kiwix. Les liens du site adaptent leurs adresses au serveur et au protocole utilisés.

Les ports HTTP `8080`, `3000` et `8081` fonctionnent aussi sur le LAN, mais HTTPS permet de chiffrer le transport des données. Le choix de profil se fait sans mot de passe. Caddy crée une autorité de certification locale propre à cette installation ; elle fonctionne sans Internet et conserve ses clés dans `donnees\state\caddy`. [Principe du HTTPS local Caddy](https://caddyserver.com/docs/running).

Exporter son certificat **public**, puis installer sa confiance sur chaque appareil lecteur :

```powershell
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive certificate D:\SetupSurvie\certificat-local.crt
Import-Certificate -FilePath D:\SetupSurvie\certificat-local.crt -CertStoreLocation Cert:\CurrentUser\Root
```

Pour les téléphones : transférer ce même fichier public ; sous Android, passer par les réglages de sécurité / installation d’un certificat d’autorité ; sous iOS, installer le profil puis activer sa confiance dans Réglages / Général / Informations / Réglages de confiance des certificats. Les intitulés peuvent varier selon l’appareil. Références : [Apple](https://support.apple.com/fr-fr/102390), [Google Pixel / Android](https://support.google.com/pixelphone/answer/2844832?hl=fr). Comparer l’empreinte avec le certificat remis depuis le serveur, puis tester que la page HTTPS n’affiche plus d’avertissement et que la permission micro est proposée. Ne jamais transférer le dossier contenant les clés privées Caddy.

Pour revenir à un usage limité au serveur : `configure --no-lan`, puis `up`. La règle de pare-feu peut se supprimer avec `Remove-NetFirewallRule -Name SetupSurvie-Web-Private`.

Sur le laboratoire Linux de Louis, le réglage correspondant est `./scripts/lab.sh network --lan-host ADRESSE_IP` ; sans `--lan-host`, cette commande revient à l’accès local seul. Un pare-feu Linux peut nécessiter une règle séparée. Ce lanceur ne demande pas de privilèges administrateur et ne modifie pas automatiquement le pare-feu.

## Mot de passe et code de secours

**Depuis 0.1.29, ils ne sont plus nécessaires.** Le portail utilise des profils
librement sélectionnables sur le réseau local. Choisir son nom pour retrouver
ses conversations et favoris ; **Famille** ouvre les réglages. Les anciens
comptes et leurs données sont conservés. Voir les [profils locaux](../utilisation/profils-locaux.md).

Les anciens outils techniques `recover-account` restent disponibles pour une
maintenance native ou une ancienne version ; ils ne font plus partie du parcours
normal. Ne jamais supprimer les bases pour retrouver un profil.

## Sauvegarder et restaurer

Conserver le kit public d’origine et une sauvegarde privée des comptes, historiques, guides et certificats. La sauvegarde arrête brièvement le site et les services de compte pour obtenir une copie cohérente, puis les redémarre. Les modèles, ZIM et caches déjà présents dans le kit ne sont pas recopiés dans cette sauvegarde privée.

Depuis 0.1.22, elle conserve aussi la pause du moteur et le registre des contenus
téléchargés. Mettre d’abord les préparations documentaires en pause et attendre leur
arrêt ; un transfert ou une préparation concurrente entraîne un refus explicite.
Depuis 0.1.23, les verrous du système se libèrent à la mort du processus ; leurs
fichiers `.lease` restent présents et ne doivent pas être supprimés. Les anciens
verrous inconnus sont conservés pour diagnostic. Lire [Coupures et redémarrage](../exploitation/coupures-et-redemarrage.md).

Depuis 0.9.3, les index de recherche et leur progression sont copiés seulement
quand leurs écrivains CLI et Web ont libéré leurs verrous. Un refus se produit
avant l’arrêt du site. Les `.lease` ne sont pas des données à restaurer : les
nouvelles sauvegardes les excluent et les anciennes entrées sont ignorées. Un
index restauré dont l’archive a changé reste signalé périmé et demande une reprise.

```powershell
py -3 scripts\pilot_backup.py backup E:\Sauvegardes\survie-essai-01 --work-dir D:\SetupSurvie\prive
```

Pour restaurer sur une installation arrêtée ou une autre machine, utiliser des dossiers vides et le kit correspondant :

```powershell
py -3 scripts\pilot_backup.py restore E:\Sauvegardes\survie-essai-01 --kit D:\livraison-marc --work-dir D:\SurvieRestaure\prive --data-dir D:\SurvieRestaure\donnees
```

Sauvegarde, kit, données, réglages et application doivent être dans des dossiers
séparés, sans imbrication. La restauration conserve une pause sauvegardée ; un
diagnostic en pause contrôle la bibliothèque et reporte les contrôles Ollama.
Un test avec inférence est refusé tant que la pause n’a pas été explicitement levée.
Les anciennes sauvegardes restent acceptées mais ne peuvent restituer les fichiers
qu’elles ne contenaient pas. Le registre restauré décrit les téléchargements passés :
il ne remplace ni leurs fichiers ni une nouvelle vérification de leur intégrité.

Les archives ZIM ajoutées après le kit et les nouveaux modèles doivent être sauvegardés séparément ou inclus dans un nouveau kit. Les sauvegardes privées contiennent des secrets : les conserver hors de la bibliothèque publique. La restauration conserve les comptes et secrets ; l’installation neuve du kit en crée de nouveaux. Les ports doivent être libres et l’adresse LAN doit être reconfigurée si elle change.

## Recette sur le PC de Marc

Avant de considérer l’essai prêt : relever GPU/RAM/version Ollama ; vérifier l’usage réel du GPU ; créer un lecteur ; chercher un article et un passage de guide ; comparer trois modèles sur une même question ; consulter et ouvrir les sources ; vérifier un calcul avec le calculateur ; annuler un gros modèle ; retrouver les conversations dans chaque interface ; tester récupération et déconnexion ; vérifier le téléchargement d’un modèle et l’utilisation hors ligne ; débrancher Internet tout en conservant le LAN ; redémarrer le PC ; réaliser une sauvegarde puis une restauration distincte.

Les tests automatiques et les réserves locales figurent dans le bilan de livraison. Une recette Windows ou téléphone non exécutée doit rester marquée « à vérifier sur place ».


## État du moteur et priorité au jeu

La page **État de l’appareil** affiche le moteur, le modèle chargé, la file des questions, la VRAM, l’activité et la température du GPU, la RAM et l’espace libre. Les valeurs du GPU comprennent tous les programmes du PC. Les administrateurs peuvent démarrer ou arrêter le moteur ; lorsqu’il est en pause, **Forcer le démarrage de l’IA** permet de le reprendre explicitement, avec un avertissement sur les performances du jeu. Le modèle attend la prochaine question pour se charger.

Un simple redémarrage des services respecte le marqueur de pause. Le panneau communique avec un petit contrôleur sur le PC hôte, authentifié par un secret propre à l’installation. Aucun accès au shell n’est proposé. Les lecteurs peuvent consulter les mesures mais ne peuvent pas lancer les commandes réservées à l’administration. Les ports internes 11435 et 11436 ne doivent pas être ouverts aux lecteurs ; le script de pare-feu Windows les bloque sur les interfaces physiques, tout en ouvrant les ports Web et mDNS sur le réseau privé. Cette règle reste à vérifier sur le Windows réel.

## Refaire les comparaisons sur la RTX 5060

La même série de cas peut se lancer après arrêt des jeux :

```powershell
py -3 scripts\compare_models.py --work-dir D:\SetupSurvie\prive --profiles rapide moyenne approfondie --repetitions 3
# Alternatives, à lancer séparément pour limiter la durée :
py -3 scripts\compare_models.py --work-dir D:\SetupSurvie\prive --profiles test-qwen4 test-qwen9 test-qwen27 test-gemma26 test-qwen38
```

Les résultats, la version Ollama et le relevé du GPU sont enregistrés dans le dossier privé `comparaisons`. Les essais demandés ne téléchargent aucun modèle. Comparer également les réponses dans le site sur les questions concrètes de Marc.

## Arrêt et nettoyage

Utiliser `survie.ps1 --work-dir D:\SetupSurvie\prive down` pour arrêter les services, le contrôleur, l’annonce du nom local et l’Ollama dédié. Les données restent conservées. Après sauvegarde, les dossiers choisis pour les données, réglages et kit peuvent se supprimer dans l’Explorateur ; ne pas supprimer les répertoires d’autres projets Docker. Pour retirer les règles ajoutées par le projet : `Remove-NetFirewallRule -Name SetupSurvie-Web-Private,SetupSurvie-mDNS-Private,SetupSurvie-Engine-Physical` dans PowerShell administrateur.

## Mises à jour et nouveaux contenus

Suivre le [guide des mises à jour du pilote](../exploitation/mises-a-jour-et-bibliotheque-pilote.md) pour remplacer seulement le logiciel, préserver les comptes et ajouter des lots sans réinstallation.

## Identifiant initial du pilote 0.1.12

**Historique, remplacé depuis 0.1.29 par les [profils sans mot de passe](../utilisation/profils-locaux.md).** Les nouvelles installations n’utilisent plus ce mot de passe initial pour accéder au produit.

Les nouvelles installations utilisent l’identifiant `admin` (compte interne
`admin@survie.local`) et le mot de passe initial demandé par Louis dans
l’installateur. Le mot de passe n’est pas recopié dans cette documentation.
Ces valeurs ne remplacent jamais le mot de passe d’une installation existante.
Les secrets techniques de session et de contrôle restent générés aléatoirement.
La connexion sur la carte utilise le même compte que le portail. La publication
du code ne modifie aucun compte sur les machines existantes.
