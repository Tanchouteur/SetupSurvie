# Refonte de la carte — 12 novembre 2026

Bilan du pilote **0.1.12**, après retour de Louis et capture Safari de la page
0.1.11. Références : [points et itinéraires](../utilisation/points-et-itineraires.md)
et [installation](../installation/pilote-marc.md).

## Problèmes observés

Les panneaux empilés réduisaient fortement la hauteur de carte. L’utilisateur
était déconnecté : les outils protégés affichaient un message sans fournir de
connexion directe. Le bouton relief désactivé ne distinguait pas absence de
session, absence d’altitudes et panne. La création d’un point exigeait de trouver
une liste et une commande dans un autre panneau, sans parcours guidé.

## Changements

- Carte principale avec colonne d’outils sur ordinateur ; onglets Rechercher,
  Mes repères, Itinéraire et Affichage. Sur téléphone : panneau repliable au-dessus
  de la carte, consultation prioritaire et résumé des kilomètres/durée visible.
- Connexion dans une fenêtre sur la carte, même API et cookie que le portail.
- Recherche proche avec état de chargement, fin explicite, résultats localisés,
  erreurs visibles et effacement des propositions périmées. Sans point choisi,
  le centre de la carte sert de référence. Les lieux non préparés sont distingués
  d’une recherche vide et d’une panne.
- Relief manquant expliqué, bouton activable pour comprendre le blocage et lien
  vers les données à préparer. Aucun téléchargement automatique ajouté.
- Bouton Ajouter un point : choix sur la carte, puis formulaire de nom et liste.
  La première liste peut être créée dans ce même formulaire. Coordonnées repliées.
- Identifiant initial des nouvelles installations fixé à `admin` et mot de passe
  initial défini à la demande explicite de Louis dans l’installateur. Les installations
  existantes ne sont pas réinitialisées. Les secrets techniques restent aléatoires.

## Vérifications

- **124 tests unitaires réussis**, commande standard dans l’environnement Python
  isolé du runner ; conservation du mot de passe d’une installation existante testée.
- Playwright MCP / Chromium : connexion intégrée, recherche sans session, données
  absentes, relief indisponible, première liste créée avec le premier point,
  recherche en cours, résultat proche et erreur sans résultats périmés.
- Sept formats : 1440×900, 1024×768, 768×900, 390×844, 375×667, 320×568,
  844×390. Carte conservant la hauteur disponible, absence de débordement horizontal,
  rôle lecteur sans mutation, formulaires de préparation masqués sur téléphone.
- Régression des itinéraires rejouée : calcul, enregistrement, kilomètres/durée,
  erreur sans trajet enregistrable et rejet d’une réponse après changement de mode.
- Recettes : `tests/browser_map_redesign.js` et `tests/browser_map_notebook.js`.
  CI dédiée **réussie sur Chromium et WebKit** sur Ubuntu 24.04, Playwright 1.58.2. Les deux recettes passent sur chacun des deux moteurs. Les tests
  utilisent uniquement des réponses locales fictives ; aucun corpus ou modèle IA
  téléchargé dans le runner. Les navigateurs de CI sont installés sur la machine
  GitHub, pas sur les PC utilisateurs.
- Captures inspectées dans les artefacts privés du navigateur, hors Git. Syntaxe
  JavaScript, `git diff --check` et construction du paquet vérifiés par les contrôles.

## Limites

Aucune machine existante ni compte existant modifié, pas de déploiement sur le Mac
ou les PC de Louis/Marc. Les captures de recette utilisent un état sans fond de
carte et des données fictives ; elles ne sont pas une nouvelle recette de cartes
PMTiles ou d’une région réelle. WebKit automatisé ne remplace pas Safari sur le
Mac de Louis ni un iPhone physique. Les altitudes et lieux utiles restent à préparer
sur l’installation cible lorsqu’ils manquent.
