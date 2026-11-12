# Démarrage Windows et données cartographiques locales — 12 novembre 2026

**Bilan daté du pilote 0.1.13.** Les procédures actuelles restent le
[guide Marc](../installation/pilote-marc.md#installer-à-partir-du-kit), le
[guide géographique](../utilisation/parametres-et-cartes.md) et les
[points et itinéraires](../utilisation/points-et-itineraires.md).

## Installation Windows préparée

La première installation depuis le kit ou le lanceur en ligne crée désormais
les raccourcis **Ouvrir SetupSurvie** et **Arrêter SetupSurvie** sur le Bureau,
avec l’icône feu/livre existante. Le lancement à l’ouverture de session de cet
utilisateur est activé par défaut. `--no-startup` / `-NoStartup` garde seulement
les raccourcis manuels. `create-shortcuts.ps1 -DisableStartup` retire uniquement
le démarrage de l’installation concernée et conserve les raccourcis du Bureau.

Le démarrage attend Docker Desktop, conserve une éventuelle pause et ouvre le
navigateur seulement depuis le Bureau. Les erreurs restent visibles dans une
fenêtre et dans un journal privé. L’arrêt conserve les données et ne coupe ni le
PC ni Docker Desktop ni les autres projets. Les préparations détachées sont mises en pause avant l’arrêt pour ne pas
redémarrer les services après leur fermeture. Le nettoyage de l’Ollama natif dédié
reste tenté si Docker est indisponible ; l’identité du processus est vérifiée.

Le kit de transport existant a reçu la nouvelle copie logicielle. Ses contenus
lourds n’ont pas été réexportés dans cette tâche : les nouveaux fichiers
géographiques et graphes décrits ci-dessous sont présents sur le laboratoire,
pas implicitement dans ce kit. Une mise à jour de l’application existante ne
réactive pas automatiquement une préférence de démarrage désactivée.

## Préparation réelle sur le Linux de Louis

Les deux fonds PMTiles du Sud et des alentours de Solliès-Ville étaient déjà
présents. Aucun domicile ni départ personnel n’était enregistré. La préparation
utilise le centre public du fond Solliès-Ville, rayon **10 km**, sans enregistrer
ce centre comme domicile et sans modifier les listes de points.

| Jeu préparé | Résultat contrôlé |
| --- | --- |
| Adresses et lieux OSM | 6 118 adresses / localités et 1 042 lieux utiles |
| Relief | Deux dalles HGT, avec lecture d’altitude ; ensemble géographique de 53,02 Mo |
| Routes et chemins | Trois profils OSRM : marche, moto, petite voiture ; graphes de 95,52 Mo |
| Intégrité | 82 fichiers de données comparés à leurs tailles et SHA-256 des manifestes |

Le serveur Overpass principal a renvoyé plusieurs HTTP 502, y compris pour une
zone réduite. La préparation des routes a abouti par le secours fixe Private.coffee,
[répertorié par OpenStreetMap](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances).
Le code ne retente que les erreurs temporaires, conserve les plafonds et garde
le fournisseur réellement utilisé dans la provenance. Une erreur de requête ou
un dépassement de taille n’est pas masqué par le secours.

Le premier essai OSRM a révélé une incompatibilité d’UID avec Podman sans
privilèges. Un petit graphe synthétique a permis de valider les trois profils
avec l’UID 0 du conteneur, correspondant ici à l’utilisateur Linux du PC. Puis la
zone réelle a été préparée et publiée. Les limites CPU/RAM, capacités retirées et
absence de réseau pendant la construction restent appliquées. L’image OSRM
épinglée a été téléchargée dans le stockage Podman du volume dédié.

Les trois services ont calculé des trajets réels depuis le pilote sur un couple
de points de recette proches du centre. Marche : 2 011 m / 1 810 s à 4 km/h ;
moto et voiture : 3 165,4 m / 285 s à 40 km/h. Les étapes ont été accrochées aux
voies pour cette vérification ; aucun trajet n’a été enregistré pour l’utilisateur.
Ces résultats vérifient le calcul, pas l’ouverture ou la praticabilité des voies.

## Vérifications et limites

- 130 tests exécutés : **129 réussites**, un test COM Windows ignoré sur Linux.
  La CI Windows contient ce test de création, lecture et retrait des raccourcis
  dans son profil jetable ; son ajout ne constitue pas un résultat distant réussi.
- Analyse syntaxique des cinq scripts PowerShell concernés sous PowerShell 7
  Linux ; cela ne remplace ni le COM, ni Docker Desktop, ni une ouverture de session Windows.
- Préparation réelle du relief et des trois graphes, lecture des données et
  appels aux services locaux ; aucun modèle IA lancé, aucun réglage de pause levé.
- Les gros contenus et rapports restent sur le SSD, hors Git. Résultats sous
  `results/update-0.1.13/`, test synthétique sous `results/routing-smoke-lab/`.

Restent à valider chez Marc : première installation Windows, création des deux
icônes, ouverture de session, démarrage de Docker, arrêt et reprise depuis les
raccourcis. Les données actuelles couvrent la zone choisie ; elles ne constituent
pas une préparation des routes, lieux et relief de toute la France.
