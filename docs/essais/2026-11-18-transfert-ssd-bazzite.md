# Premier transfert réel entre SSD sur Bazzite

**Recette du 18 novembre 2026.** Louis demande de mettre à jour l’installation
Linux neuve, de la transférer sur l’autre SSD et de corriger les défauts
rencontrés dans un worktree dédié.

## Point de départ

L’installation Docker rootless de l’essai était active en 0.43.2 sur le SSD
système Samsung 990 PRO 1 To, partition `nvme0n1p3`. La destination est un
nouveau dossier sur le Crucial P3 Plus 4 To, partition `nvme1n1p1`, avec Btrfs
sur les deux disques. Le volume initial de transfert compte **10 383 fichiers
ordinaires**, **151 541 992 106 octets**, ainsi que **deux liens Ollama**. Les
images Docker s’ajoutent à ce volume. Docker rootless et son stockage restent
sur le SSD système.

La mise à jour 0.43.2 → 0.43.3 a terminé avec sa sauvegarde et son journal. La
seconde mise à jour a installé la 0.44.0 de `main` avec le correctif testé. La
livraison du correctif part de la 0.45.0 de `main` et porte la version 0.45.1,
une correction compatible sans migration du schéma ni modification des versions
tierces.

## Journal des problèmes

| Constat | Correction et preuve |
| --- | --- |
| Le contrôleur n’est plus joignable après la fin de la commande de mise à jour lancée à distance dans une unité systemd transitoire. | L’unité suivante conserve ses processus avec `Type=oneshot` et `RemainAfterExit=yes`. L’API du portail confirme que le contrôleur répond après la mise à jour. |
| Le PC quitte le LAN au moment du premier lancement de la copie. | Le journal système confirme une veille demandée par PowerDevil à 12 h 27, suivie d’une reprise à 15 h 03, en heure locale. Aucun dossier de copie ni garde source à la reprise. Un inhibiteur temporaire `sleep:idle` est vérifié avant le nouvel essai. |
| Le transfert refuse un lien de manifeste Ollama v2. | Le transfert conserve les liens relatifs vers des blocs réguliers du même magasin Ollama et les vérifie après copie. Un lien vers un bloc externe, même lisible, est refusé. |
| L’installation Linux possède un environnement Python YouTube avec des chemins liés à la source. | Le dossier Python généré est exclu, le cache de roues est vérifié, et l’activation tente la reconstruction hors ligne. Le rapport indique si les outils sont prêts. |
| Kiwix est sain selon Docker mais son catalogue est vide et ses 58 ZIM sont présents. | Le masque de création à 077 a rendu les répertoires illisibles pour le compte Kiwix. Permissions d’origine rétablies sur 621 répertoires de la copie et Kiwix relancé. Le transfert conserve désormais ces permissions et vérifie qu’une entrée est visible lorsque des ZIM sont présents. |
| Le texte de secours renvoie au lanceur Windows sur une copie Linux. | Le texte renvoie à `transferer-setupsurvie.sh` pour une copie Linux. |

## Interruption et reprise

Le seul processus de copie a été interrompu par SIGKILL au milieu d’un gros
fichier. Le préfixe observé avant l’arrêt faisait **452 984 832 octets**. La
reprise avec les mêmes dossiers a repris la copie et le contrôle des empreintes.

Le journal de copie est passé à `copied` environ 7 min 44 s après le premier
lancement. Il compte **10 383 fichiers vérifiés**, **65 bases SQLite
contrôlées**, **deux liens de manifeste** et une archive des images Docker de
**5 117 729 792 octets**. Le contrôle de préparation et la validation de
l’activation sont des étapes distinctes.

La suite avant la correction des permissions a compté **1 096 tests**,
dont **33 ignorés**, sans échec. La suite ciblée après la dernière révision du transfert a exécuté
**38 tests**, dont **3 ignorés** réservés à Windows, sans échec. Elle inclut le contrôle
d’un lien Ollama copié, le refus d’une cible externe et l’exclusion contrôlée
de l’environnement Python YouTube.

## Activation et fonctionnement

L’activation a confirmé les montages de la destination, les services, les trois
routeurs, la recherche, l’ouverture d’un guide et les outils YouTube reconstruits
hors ligne. La recette après correction de Kiwix a bloqué Internet dans les sept
conteneurs de la copie, avec une connexion témoin réussie avant le blocage et
refusée pendant. Le portail et sa page de secours, Open WebUI, le catalogue
Kiwix, les profils, la recherche et le PDF de la loi d’Ohm, la lecture PMTiles,
les listes de traductions et de vidéos, yt-dlp, Deno et FFmpeg ont répondu. Les
comptages des tables contrôlées des deux bases source et destination concordent.
Les règles temporaires ont été retirées après la recette.

La version **0.45.1** a ensuite été installée sur le Crucial par le parcours
de mise à jour et relancée via une unité systemd utilisateur dédiée, activée
au démarrage. L’ancien démarrage automatique a été désactivé. Une seconde
recette a combiné le blocage d’Internet dans les sept conteneurs et le
renommage temporaire du dossier de données source. Tous les contrôles
documentaires ci-dessus ont répondu, dont le nouveau contrôle Kiwix. Le
catalogue complet annonce **58 archives**. Un navigateur Chromium a ouvert
le portail par l’adresse IPv4 du LAN. Le dossier source et les règles réseau
ont été remis en place, et l’inhibiteur temporaire de veille a été retiré.

La copie reste en service sur le Crucial avec l’assistant arrêté et le
contrôleur joignable. L’archive des images et la source sont conservées.
Le démon Docker rootless et son espace de stockage restent sur le SSD
système. Le scénario couvre la relance du service et l’absence du dossier
de données source. Le redémarrage physique du PC, le retrait du SSD système,
le retour applicatif à la source sur cette installation, l’iPhone et
l’inférence réelle restent à vérifier dans des recettes dédiées.

## Retrait de la source sur Linux

La version 0.46.0 ajoute la commande `retire-source`. L’examen réel a retenu
uniquement les anciens dossiers `application` et `donnees` sur le Samsung.
Le moteur Docker et ses fichiers sont dans un dossier voisin. La suppression,
la reprise après interruption, le refus du retour vers une source en cours de
retrait et la conservation du stockage Docker ont été testés sur des dossiers
jetables. La copie source réelle est conservée à l’issue de cet examen.
