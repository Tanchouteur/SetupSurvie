# Points et itinéraires hors ligne

Guide du pilote **0.1.11**. La carte sert à préparer et consulter des déplacements,
sans suivi GPS et sans service de routage Internet.

## Consulter sur téléphone

Se connecter au portail, ouvrir Cartes puis **Mes points et itinéraires enregistrés**.
Choisir une liste, toucher un point ou ouvrir un trajet. La fiche indique les
kilomètres par les voies, le mode et la durée estimée. Les notes et le tracé restent
accessibles même si le moteur de calcul est arrêté. Le téléphone consulte les
contenus du serveur sur le réseau local ; il ne devient pas une carte autonome
loin du serveur. Exporter le GPX ou imprimer la carte et la fiche avant de partir.

L’édition est masquée sur petit écran et appareil tactile. Les lecteurs ne peuvent
pas modifier les listes, points ou trajets, quelle que soit la taille de l’écran.
Le compte administrateur prépare sur ordinateur.

## Préparer sur ordinateur

Dans **Préparer les listes et trajets** :

1. Créer une liste (eau, famille, repli…).
2. Choisir un point sur la carte puis l’enregistrer avec un nom, un type et des notes.
3. Choisir les points de départ et d’arrivée, et éventuellement des étapes (8 maximum).
4. Choisir **à pied**, **moto** ou **petite voiture** et une vitesse moyenne.
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
sont ceux du trajet calculé, pas la distance à vol d’oiseau. Les points sont
accrochés à une voie à 100 m maximum ; les écarts sont indiqués et ne sont pas
comptés comme des chemins d’accès praticables.

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
