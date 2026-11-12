# Paramètres, déplacements et cartes hors ligne

Guide initial du pilote **0.1.10**. Depuis **0.1.11**, voir aussi les [listes de points et itinéraires](points-et-itineraires.md) : préparation sans GPS et consultation mobile. Les téléchargements décrits sont des fonctions du
logiciel ; leur disponibilité ne prouve pas qu’une zone a été préparée sur un PC.

## Paramètres de l’appareil

Avec un compte administrateur, ouvrir **Paramètres** dans le menu. Cette page
regroupe les lieux de référence, les commandes du moteur, l’ajout de guides,
les accès aux comptes, au réseau et aux téléchargements, ainsi que le contexte
fourni à l’assistant et les retours. Les mesures restent dans État de l’appareil ;
le choix du modèle reste dans la conversation.

Deux lieux distincts sont enregistrés dans la base privée du pilote :

- **Domicile** : point de référence conservé.
- **Point de départ actuel** : remplace le domicile pour les recherches proches.
  Revenir au domicile efface uniquement ce remplacement.

Ils sont communs aux comptes de l’appareil. Seul l’administrateur les modifie ;
les utilisateurs connectés et l’assistant peuvent les lire. Ce n’est pas un suivi
GPS. La recherche cartographique et les mesures restent possibles depuis un point
choisi sans modifier ces références.

## Trouver et confirmer une adresse

1. Choisir Domicile ou Point de départ actuel.
2. Saisir une adresse et choisir **hors ligne** ou **en ligne · France (IGN)**.
3. Lire le libellé proposé et, si nécessaire, vérifier son emplacement sur la carte.
4. Confirmer le résultat. Le texte et les coordonnées restent disponibles hors ligne.

La recherche en ligne transmet le texte saisi à l’[IGN Géoplateforme](https://data.geopf.fr/geocodage/search).
Elle repose sur la BAN ; un résultat peut être une rue ou une commune plutôt
qu’un numéro. La confirmation porte sur le résultat choisi, sans certification
d’exactitude du domicile. Aucune recherche n’est envoyée pendant la frappe.

Hors ligne, le pilote utilise les adresses et lieux nommés OpenStreetMap des zones
préparées, ainsi que les références déjà enregistrées. **La couverture est
incomplète**, notamment pour les numéros de rue. Si l’adresse manque, choisir un
point sur la carte ou saisir latitude et longitude. Ce point est marqué manuel,
sans prétendre que l’adresse postale a été trouvée. Un point transféré depuis la
carte propose par défaut le départ actuel pour préserver le domicile.

## Préparer une zone avec Internet

Dans **Données locales → Cartes, adresses et relief hors ligne** :

1. Reprendre le point de départ ou saisir le centre d’une autre zone de déplacement.
2. Choisir un rayon de 5, 10 ou 25 km.
3. Garder ou retirer le téléchargement des altitudes.
4. Télécharger, puis actualiser le suivi.

Le contrôleur hôte lance un processus détaché, commun au gestionnaire documentaire.
Fermer le navigateur n’annule pas l’opération. Une seule opération documentaire
est lancée à la fois. Les vérifications de volume monté (laboratoire), budget
500 Go et marge physique de 15 Go restent appliquées, avec une réservation de
300 Mo pour la préparation. Aucune commande ne démarre Ollama.

Les sources sont fixes :

| Données | Source / format | Usage local |
| --- | --- | --- |
| Adresses, lieux nommés et lieux utiles | OpenStreetMap via Overpass, JSON | Recherche d’adresse et de lieux proches |
| Altitudes du terrain | Mapzen Terrain Tiles / Skadi, HGT | Altitude, ombrage du relief et coupe du terrain |
| Fond de carte | Préparation PMTiles existante, distincte | Routes, bâtiments, cours d’eau et localités |

La zone de téléchargement est transmise aux fournisseurs, pas les conversations
ni les identifiants. L’extraction OSM est limitée à 30 Mo et 150 000 éléments ;
les réponses signalant une extraction incomplète sont refusées. Les HGT sont des
dalles de 1° ; au maximum neuf dalles et deux tailles standard sont acceptées.
Les données sont préparées sur le disque documentaire et publiées ensemble après
contrôle. Les empreintes SHA-256 sont **calculées à réception HTTPS**, pas comparées
à des empreintes indépendantes publiées par les fournisseurs.

Les anciennes zones sont conservées. Une préparation identique le même jour
réutilise la zone existante après vérification des empreintes. Arrêter une préparation
géographique supprime seulement son dossier temporaire ; la relancer recommence
son téléchargement. Les zones terminées restent accessibles pendant ce temps.

Les fichiers sont dans `library/maps/geography/`. Le manifeste conserve les sources,
la date de collecte, la zone, les tailles, les empreintes et les attributions.
La date de collecte n’est pas une garantie de fraîcheur de chaque objet OSM ou
de chaque mesure d’altitude. Les attributions Mapzen sont conservées dans chaque
lot et dans `deploy/terrain-attribution.txt`. Les conditions des sources de relief
restent à examiner pour une redistribution commerciale du kit, selon les régions.

**Préparer les lieux et le relief ne prépare pas le fond de carte d’une nouvelle
région.** Les fonds PMTiles existants couvrent le Sud et les environs de Solliès-Ville.
La recette de fond reste `scripts/maps.py`. Hors de cette couverture, la carte ne
promet pas de routes ou bâtiments ; les outils utilisent seulement les données
localement présentes.

## Utiliser les outils de carte

Ouvrir **Bibliothèque → Cartes hors ligne**, puis le volet des outils.
La consultation du fond reste publique. Se connecter au portail pour les outils
et les données de localisation.

- Rechercher une adresse locale ou toucher la carte pour choisir un point.
- Chercher autour de ce point : eau, alimentation, santé, abri, réparation ou communications.
- Lire l’altitude approximative si la dalle est téléchargée.
- Activer l’ombrage du relief, calculé localement.
- Mesurer entre deux points et afficher une coupe du terrain (50 km maximum).
- Choisir les positions manuellement ; le bouton GPS a été retiré du parcours en 0.1.11.

Les distances sont **à vol d’oiseau**. Le profil est une ligne droite, sans calcul
de chemin praticable ou de dénivelé cumulé de randonnée. Les itinéraires par les voies utilisent le [circuit de routage distinct](points-et-itineraires.md).
Les altitudes interpolent les échantillons HGT voisins : elles restent
approximatives et n’indiquent pas la hauteur des bâtiments. L’absence de données
est signalée, pas remplacée par une altitude supposée.

Un lieu cartographié n’est pas une confirmation d’ouverture, d’accès ou de potabilité.
Une recherche vide ou une couverture partielle ne prouve pas l’absence d’un lieu.
La carte fonctionne sans Internet à proximité du serveur accessible sur le LAN ;
elle n’est pas une application autonome téléchargée sur le téléphone.

## Outils de l’assistant

Le portail et l’IA partagent les mêmes fonctions géographiques locales :

| Outil | Fonction |
| --- | --- |
| `get_location` | Lire le point de départ ou, à défaut, le domicile |
| `search_nearby` | Trouver des lieux par catégorie et rayon (25 km maximum) |
| `get_elevation` | Lire l’altitude locale d’un point |
| `terrain_profile` | Lire 41 altitudes sur un segment de 50 km maximum |
| `distance_between` | Calculer une distance à vol d’oiseau |

Ils s’ajoutent à recherche documentaire, lecture, calcul et conversion. Ils ne
permettent ni téléchargement, ni changement d’adresse, ni appel Internet, ni
localisation GPS en direct. Les résultats donnent la couverture et les dates ;
les lieux trouvés fournissent un lien vers la carte. Aucune nouvelle performance
de GPT-OSS n’est déduite des tests simulés de ces outils.

La calculatrice accepte les nombres, parenthèses, `+ - * / // % **`, avec des bornes
sur la taille des expressions, puissances et résultats. Elle calcule avec des
fractions exactes ; le champ numérique peut être une approximation décimale.
L’IA peut formuler une expression puis la faire vérifier, mais elle peut se tromper
dans les hypothèses ou la formule. Pas de solveur symbolique, de variables ou
d’exécution libre de Python.

## Sauvegardes

Les adresses sont dans `state/pilot/pilot.db`, inclus dans les sauvegardes privées
existantes. Ne pas placer cette base dans la bibliothèque publique. Les lots
cartographiques restent des contenus volumineux : conserver le kit correspondant
ou copier séparément `library/maps`, notamment les zones ajoutées depuis le kit.
La sauvegarde privée ne les recopie pas automatiquement.
