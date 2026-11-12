# Points et itinéraires — 12 novembre 2026

Bilan du pilote **0.1.11**, développement dans le runner Linux sur CPU.
Guide : [points et itinéraires hors ligne](../utilisation/points-et-itineraires.md).

## Fonctions

Listes partagées, points avec notes et catégories, modification et suppression,
exports GPX. Calcul local OSRM avec profils distincts marche/moto/petite voiture,
étapes, kilomètres par les voies et estimation à vitesse choisie (4 km/h à pied).
Trajets enregistrés comme instantanés consultables indépendamment du moteur.
Préparation sur ordinateur administrateur ; consultation sur mobile, sans GPS.
Préparation du réseau sur le PC cible, via le contrôleur hôte ou la commande dédiée.
Image OSRM 6.0.0 épinglée après lecture du manifeste du registre, sans téléchargement
de couche dans le runner. Ancien graphe conservé lors d’un remplacement.

## Tests

- **123 tests unitaires réussis** dans l’environnement Python isolé du runner.
  Les tests de téléchargement et de livraison de petites fixtures utilisent une capacité
  disque simulée ; les cas de capacité insuffisante restent explicitement testés.
  La commande standard passe dans le runner, sans changer les réserves de production. Aucun modèle ou document lourd téléchargé dans cette VM.
- Tests nouveaux : droits lecteur/administrateur, listes non vides protégées,
  points déplacés, trajets indépendants des points, brouillons limités au compte
  et à une utilisation, GPX échappé, données non préparées, couverture, erreurs
  moteur, kilomètres et durée à 4 km/h, profils locaux séparés, préparation bornée
  et conservation du graphe précédent en cas d’échec.
- Playwright MCP / Chromium, données entièrement simulées et requêtes extérieures
  bloquées : création de liste et points, calcul, estimation de 8 km en 2 h,
  enregistrement, relecture, absence de trajet après erreur, rejet d’une réponse
  périmée après changement de mode, masquage de l’édition chez les lecteurs et sur
  téléphone. Largeurs/hauteurs : 1366×900, 768×900, 390×844, 375×667, 320×568 et
  844×390. Aucun débordement horizontal ni erreur JavaScript dans cette recette.
  La liste se replie lors de l’ouverture d’un trajet sur téléphone.
- Recette reproductible : `tests/browser_map_notebook.js`. Captures dans les
  artefacts privés du navigateur, hors Git.
- La CI Linux/Windows exécute les tests habituels. Un job GitHub distinct exécute
  réellement OSRM et les trois profils sur `fixtures/maps/routing-small.osm`,
  réseau entièrement fictif de 1 045 octets. Son image est téléchargée dans la
  machine CI GitHub, jamais dans le runner de développement. La fixture dispose
  d’une réserve test de 2 Go ; la réserve de production reste 10 Go + 15 Go libres.
  Ce test a identifié et permis de corriger le nom `--data_version` et les tags Lua
  absents (`nil`) qui excluaient à tort les voies piétonnes. Il a aussi révélé les
  permissions 0600 de certains index OSRM, incompatibles avec les conteneurs sans
  capabilities ; les graphes OSM sont désormais publiés lisibles (0644). Les points
  privés restent dans la base protégée.
- **OSRM réel réussi dans GitHub CI** : 325,8 m à pied, 394,1 m à moto et 769,9 m
  en voiture sur le réseau fictif. Les modes suivent bien des voies distinctes.
  Les trois graphes sont préparés, servis et interrogés avec contrôle de version
  du graphe et estimation à 4 km/h pour le piéton.
- Vérification syntaxique Python/JavaScript, construction du paquet de mise à jour
  et `git diff --check` exécutés.

## Limites

Pas de nouvelle installation ou extraction réelle sur les PC de Louis et Marc.
Le réseau fictif ne certifie pas une couverture géographique, les performances
sur une région réelle ou la praticabilité des voies. Pas de test physique iPhone
ni de nouvelle recette WebKit. Les durées restent à vitesse constante, sans pauses,
trafic ou pénalisation altimétrique. Les petits chemins dépendent du contenu OSM
et du profil ; le fond PMTiles et le réseau routable sont distincts.
