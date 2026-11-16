# Points et itinéraires hors ligne

Guide actuel **0.11.0**. La carte sert à préparer et consulter des déplacements,
sans suivi GPS et sans service de routage Internet.

## Consulter sur téléphone

Ouvrir Cartes puis utiliser **Choisir un profil**, en haut de la carte. Les profils sont libres et sans mot de passe, comme dans le portail. Ouvrir **Rechercher · Mes repères**, puis l’onglet **Mes repères**.
Choisir une liste, toucher un point ou ouvrir un trajet. La fiche indique les
kilomètres par les voies, le mode et la durée estimée. Les notes et le tracé restent
accessibles même si le moteur de calcul est arrêté. Le téléphone consulte les
contenus du serveur sur le réseau local ; il ne devient pas une carte autonome
loin du serveur. Exporter le GPX ou imprimer la carte et la fiche avant de partir.

L’édition est masquée sur petit écran et appareil tactile. Le panneau mobile est repliable ; la carte conserve sa hauteur. Un résumé du trajet avec kilomètres et durée reste visible quand le panneau est fermé. Les lecteurs ne peuvent
pas modifier les listes, points ou trajets, quelle que soit la taille de l’écran.
Le profil Famille prépare sur ordinateur.

## Préparer sur ordinateur

Avec le profil **Famille** ou un profil donnant accès aux réglages, sur ordinateur :

1. Cliquer sur **Ajouter un point**, au-dessus de la carte.
2. Cliquer sur l’emplacement choisi : le formulaire s’ouvre. Donner un nom au point, choisir sa liste ou **Créer une nouvelle liste**, puis enregistrer. Les coordonnées restent consultables dans un volet du formulaire.
3. Ouvrir l’onglet **Itinéraire**. Choisir les points de départ et d’arrivée, et éventuellement des étapes (8 maximum).
4. Choisir **à pied**, **moto** ou **petite voiture**. **Options du trajet** permet de régler la vitesse moyenne et les autoroutes à éviter.
5. Calculer, contrôler le tracé et enregistrer le trajet dans la liste.

Les listes sont communes aux utilisateurs authentifiés de l’appareil. Elles ne
sont pas exposées comme bibliothèque publique. Modification, déplacement et
suppression des points sont possibles. Une liste contenant des points ou trajets
ne peut pas être supprimée directement. Les trajets sont des instantanés : changer
ou supprimer un point ne modifie pas un trajet déjà enregistré. Le recalcul est
explicite ; une ancienne fiche ne constitue pas une nouvelle vérification du terrain.

La marche propose **4 km/h** : 8 km donnent 2 heures, hors pauses. La moto et la
petite voiture proposent 40 km/h, valeur modifiable. Cette vitesse sert à estimer
la durée ; elle ne change pas le choix des voies du profil OSRM. Les kilomètres
sont ceux du trajet calculé, pas la distance à vol d’oiseau. Le calcul ordinaire cherche une voie à 100 m maximum de chaque point. Les écarts de plus de 5 m sont dessinés en pointillés et indiqués comme **liaisons à vérifier**. Leurs distances à vol d’oiseau sont séparées des kilomètres et de la durée sur le réseau.

## Choisir un accès lorsque le point est loin d’une voie

Si un point ne peut pas être raccordé, le panneau Itinéraire propose jusqu’à trois
accès du réseau du mode choisi, dans un rayon de **1 km** du point. Choisir un
bouton numéroté ou le repère correspondant sur la carte, puis **Utiliser cet accès**.
Le point enregistré reste à sa place ; seul l’accès du trajet change. Si plusieurs
étapes sont éloignées, elles sont traitées une par une.

Le nom de voie peut manquer. La distance affichée est à vol d’oiseau : elle ne
garantit pas le passage entre le point et la voie. Un mur, une propriété ou le
relief peuvent empêcher cette liaison. La ligne en pointillés sert de repère,
jamais de chemin calculé ou vérifié. Les kilomètres et la durée restent ceux des
voies calculées, hors raccordements.

**Choisir sur la carte** permet de cliquer près d’une voie, toujours à moins de
1 km du point d’origine ; le moteur vérifie la présence d’un accès dans les 100 m
autour du clic. **Revenir au trajet** conserve les étapes. **Choisir un autre
accès** permet de revoir un raccordement après calcul ou absence de liaison.
Les accès proches ne garantissent pas qu’un trajet existe entre eux.

Un changement de mode ou d’étapes efface les choix d’accès précédents. Les
propositions expirent après quinze minutes, au redémarrage du pilote ou lors du
remplacement du réseau ; il faut alors les choisir à nouveau. Un trajet déjà
enregistré reste consultable, sans recalcul ni moteur.

Les messages distinguent absence de voie, absence de liaison, zone non préparée,
moteur indisponible, calcul trop long et ancien réseau chargé. Les choix restent
présents après un échec. Préparer une zone plus large est proposé lorsque les
données manquent ; une panne du moteur ne produit pas de faux accès.

À l’impression, le tracé et les liaisons en pointillés restent distincts, avec la
fiche donnant les écarts. L’export GPX conserve seulement le parcours calculé dans
la trace ; les points d’origine et les accès sont des points séparés. Les anciens
trajets gardent leur tracé historique, sans raccordements inventés a posteriori.

## Préparer les routes et chemins sur le PC cible

Dans Données locales, choisir le centre et le rayon, puis **Préparer les itinéraires
de cette zone**. Cette action télécharge le réseau OSM et, si absente, l’image du
moteur OSRM épinglée dans `deploy/routing-engine.json`. Elle utilise le même
contrôleur et verrou que les autres préparations documentaires. Aucun modèle IA
n’est démarré. Les fonds de carte PMTiles restent une préparation distincte.

La préparation a besoin de 10 Go supplémentaires, en plus de la marge physique
obligatoire de 15 Go. Elle utilise au maximum 2 CPU et 4 Go RAM par commande de
préparation ; les trois profils sont préparés successivement. Chaque service
local est limité à 1 CPU et 2 Go RAM. Un PC trop juste peut refuser ou échouer la
préparation : réduire la zone et préparer sur une machine adaptée.

Le réseau est extrait dans une zone rectangulaire avec une marge d’environ 1 km,
avec restrictions de circulation. L’extraction OSM est limitée à 50 Mo. Les réponses
incomplètes sont refusées. Les fichiers et profils sont empreintés, le nouveau
réseau est publié après préparation des trois profils. L’ancien dossier est
conservé sous `library/maps/routing/previous-*`. Ne le supprimer qu’après vérification
du nouveau réseau et sauvegarde ; aucune suppression automatique des anciens lots.

Une extraction locale déjà disponible peut également être préparée :

```bash
python scripts/routing_prepare.py --work-dir CHEMIN_PRIVE \
  --source CHEMIN_EXTRAIT.osm.pbf --bbox OUEST SUD EST NORD --allow-download
```

Pour le laboratoire, ajouter `--backend lab` ; les contrôles de montage dédiés
restent obligatoires. Cette commande s’exécute sur le PC cible, pas dans le petit
runner de développement. Sans `--allow-download`, une image OSRM absente est refusée.
Le graphe peut être préparé hors ligne avec un extrait et une image déjà disponibles.

Les services de routage n’exposent aucun port au LAN ; le pilote les interroge sur
le réseau interne. Compose les active seulement si un réseau a été préparé. Le
lanceur du laboratoire et son actualisation de bibliothèque les relancent aussi.
Le moteur vérifie l’identifiant de préparation renvoyé par OSRM : un service
resté sur l’ancien graphe est refusé, sans inventer un trajet de remplacement.

Sous Windows, les conteneurs utilisent le même identifiant Linux que la
préparation des graphes (1000:1000) pour lire les index dont l’accès est
limité à leur propriétaire. Les graphes restent montés en lecture seule.
Après l’installation de la mise à jour qui apporte ce correctif,
utiliser **Arrêter SetupSurvie**, puis **Ouvrir SetupSurvie**, pour recréer
les conteneurs d’itinéraires avec la nouvelle configuration.

## Petits chemins et limites

Les sentiers, pistes et petits chemins présents dans le fond OpenStreetMap sont
consultables selon le détail téléchargé. Le routage utilise son propre réseau OSM,
qui peut avoir une autre date que le fond : l’un ne remplace pas l’autre.

- À pied : voies admises par le profil piéton ; les itinéraires d’alpinisme indiqués
  par `sac_scale` au-delà de `hiking` sont écartés.
- Moto : accès `motorcycle`, `motor_vehicle`, `vehicle`, puis `access` ; aucun
  franchissement automatique des voies interdites aux véhicules motorisés.
- Petite voiture : profil automobile ; pas un profil camion ou véhicule hors gabarit.
- Pour moto/voiture, les pistes `track` non déclarées `grade1` sont écartées.
- Bacs/ferries exclus pour les trois profils ; téléphériques exclus à pied.
- Autoroutes évitées par défaut pour les véhicules, choix désactivable avant calcul.

Les données peuvent être incomplètes ou anciennes. Ni l’affichage d’un chemin ni
le calcul d’un itinéraire ne garantit son ouverture, l’état d’un pont, l’absence
d’obstacle ou la praticabilité réelle. Le calcul n’intègre pas l’état d’une crise,
le trafic, les pauses ou le relief dans l’estimation à vitesse constante. Un détour
hors de la zone préparée peut nécessiter de préparer une zone plus large.

Sans réseau préparé ou sans chemin trouvé, le site indique l’échec : **aucun segment
à vol d’oiseau n’est présenté comme itinéraire**. Les trajets déjà enregistrés
restent lisibles sans service OSRM. Il n’y a aucune dépendance aux satellites
pour créer, consulter, imprimer ou exporter ces données.

Les points et trajets sont dans `state/pilot/pilot.db`, inclus dans la sauvegarde
privée existante. Les graphes sont dans `library/maps/routing`, à conserver avec
les contenus ou le kit ; la sauvegarde privée ne les recopie pas. L’export d’images
Compose inclut OSRM lorsqu’un réseau existe ; son import conserve l’identifiant
local pour une reprise sans accès au registre.

Limites de volume : 50 listes, 1 000 points, 100 trajets ; les exports GPX de listes
et trajets sont disponibles aux utilisateurs connectés.

## Comprendre une recherche qui ne trouve rien

L’onglet **Rechercher** affiche « Recherche… » pendant l’appel, puis le nombre de
résultats ou un message d’erreur. Si aucun point n’est choisi, la recherche proche
part du centre de la carte. Les résultats proches sont matérialisés sur la carte ;
cliquer un résultat le sélectionne et permet de l’ajouter à une liste sur ordinateur.
Les anciennes propositions sont effacées quand une nouvelle recherche commence.

Sans profil disponible, l’action ouvre le choix du profil. Si les lieux
ne sont pas téléchargés, la page explique la différence entre fond de carte et
lieux utiles et propose **Préparer les données de cette zone**. Une recherche vide
ne prouve pas l’absence de lieu sur le terrain.

L’onglet **Affichage** contient la sélection du fond, les informations de date et
le relief. Le bouton du relief manquant reste activable pour expliquer la raison :
profil nécessaire, service indisponible ou altitudes non préparées. Les données
manquantes ne sont pas téléchargées automatiquement.

Sur le laboratoire Podman sans privilèges de Louis, la préparation utilise l’UID
0 du conteneur, qui correspond à l’utilisateur Linux dans cet espace de noms.
Cela préserve l’écriture sur le volume monté, sans privilèges root sur le PC.
La préparation Docker conserve son utilisateur non privilégié habituel. Les
limites CPU, RAM, réseau et capacités restent appliquées. Les extractions en
ligne consignent aussi le serveur Overpass réellement utilisé dans le manifeste.
