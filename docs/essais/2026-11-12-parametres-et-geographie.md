# Paramètres et géographie — 12 novembre 2026

Bilan de développement du pilote **0.1.10**, dans le runner Linux.
Référence d’utilisation : [Paramètres et cartes](../utilisation/parametres-et-cartes.md).

## Livré

- Page Paramètres et regroupement des accès de gestion ; commandes du moteur déplacées.
- Domicile partagé et départ distinct, confirmation d’adresse IGN, recherche locale
  d’adresses téléchargées, coordonnées manuelles et transfert d’un point depuis la carte.
- Préparation de zones OSM (adresses/lieux) et HGT (altitudes), par tâche hôte
  persistante et bornée ; conservation des contenus existants, pause sans moteur IA.
- Recherche de lieux, altitude, ombrage du relief, distance et coupe du terrain.
- Cinq outils géographiques locaux pour l’assistant, en plus des quatre existants.

## Vérifications exécutées

- **116 tests unitaires réussis** dans un environnement Python isolé. Le runner a moins
  de 15 Go libres : les premiers essais ont rencontré les refus de marge disque
  attendus. Une seconde exécution fournit une capacité disque synthétique aux tests,
  sans changer les contrôles de stockage de l’application. La CI GitHub exécute
  également la commande standard dans ses environnements Linux et Windows.
- Tests géographiques : protection des réglages, absence de réseau pendant les
  recherches locales, domicile conservé lors d’un déplacement, refus des candidats
  inconnus et coordonnées invalides, données absentes, distances connues,
  interpolation HGT, valeurs manquantes, PNG et publication atomique d’un lot.
- Appels d’outils de l’assistant vérifiés avec un modèle simulé : recherche locale
  réellement exécutée et trace conservée. Aucune nouvelle génération LLM ou mesure
  de qualité de GPT-OSS n’a été effectuée.
- Playwright MCP / Chromium : Paramètres et Cartes aux largeurs 1366, 768, 390 et
  320 pixels, recherche/confirmation d’adresse, départ distinct, lancement de tâche,
  recherche de lieux et lien retour vers les paramètres. Aucune erreur JavaScript
  ni débordement horizontal dans cette recette ; les API y sont simulées. Recette
  versionnée : `tests/browser_settings.js`.
- Prévisualisation avec les vraies API FastAPI et un terrain synthétique : lecture
  d’altitude, recherche d’un lieu et affichage des tuiles de relief dans MapLibre.
- Fournisseurs réels contrôlés sur des exemples publics : géocodage IGN (HTTP 200
  et résultat pour l’exemple public à Amiens), extraction Overpass d’un hôtel de
  ville dans un rayon de 150 m, dalle HGT N43E006 téléchargée en mémoire et format
  décompressé de 25 934 402 octets vérifié. Aucune adresse personnelle utilisée.
- Syntaxe JavaScript/Python et `git diff --check` vérifiés.

Captures dans les artefacts privés de navigateur, hors Git. Le relief synthétique
n’est pas un nouveau téléchargement de terrain sur le PC de Louis.

## Limites

Pas de déploiement du pilote sur le PC de Louis ou celui de Marc dans cette tâche,
pas de nouveau lot installé sur leur stockage, pas d’essai physique iPhone ou GPS,
ni de nouveau test WebKit. La CI Windows ne valide pas le GPU ou l’installation
réelle de Marc. Les adresses OSM sont incomplètes ; les fonds PMTiles restent une
préparation séparée. Pas de routage routier, de suivi GPS de l’IA ou de certification
des conditions actuelles. Examiner les conditions régionales des sources de
relief avant redistribution commerciale.
