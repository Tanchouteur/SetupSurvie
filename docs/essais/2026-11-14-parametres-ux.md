# Paramètres par usage — 14 novembre 2026

**Bilan de préparation 0.12.0 — intégration après recherche 0.11.1.**

Le [guide actuel](../utilisation/parametres-et-appareil.md) contient l’inventaire
complet des commandes et leurs nouvelles destinations. Les quatre entrées
regroupent profils/connexion, bibliothèque/préparations, assistant et entretien.
Mon appareil sépare vue d’ensemble et travaux en cours ; les mesures détaillées
et essais techniques sont dépliables. Les commandes sont déplacées, sans clonage.

La base initiale est `af30c09` (cartes 0.11.0 conservées). La recherche 0.11.1
s’intègre d’abord sur main ; ses moteurs et nouveaux diagnostics sont conservés.
Le générateur, la navigation, les versions, la recette de recherche et les guides
communs sont réconciliés successivement. Aucun changement de Compose, modèle,
schéma de données, moteur de recherche, indexation ou cartes n’est nécessaire.

Le niveau mineur 0.12.0 correspond à une évolution fonctionnelle compatible de
l’organisation et de la navigation ; il ne revendique pas une version stable.
Aucune image tierce n’est renumérotée.

## Captures

Captures de la petite installation de test du runner, avec profils et documents
fictifs ; elles ne montrent ni les données ni les mesures des PC de Louis ou Marc.
Les captures après intégration et les résultats finaux sont ajoutés à la fin de
la validation.

| Écran | Avant (0.11.0) | Après (0.12.0) |
| --- | --- | --- |
| Paramètres ordinateur | [Avant](captures/parametres-ux/avant-ordinateur.png) | Capture finale à ajouter |
| Paramètres téléphone | [Avant](captures/parametres-ux/avant-mobile.png) | Capture finale à ajouter |

## Vérifications pendant la préparation

Sur la base initiale : 503 tests Python réussis, 12 ignorés (dépendances natives
optionnelles et tests Windows non applicables au runner Linux). Les parcours
Chromium déplacés ont réussi : recherche, outils, catalogue, assistant, comparatif
et dossiers. Le nouveau parcours UX contrôle les liens directs, les IDs uniques,
les rubriques ouvertes, les brouillons et l’absence de commande à l’ouverture.
La validation complète après fusion est à consigner avant intégration.

Les essais utilisent exclusivement des documents minuscules et des API simulées,
sans modèle, gros corpus ni accès aux données réelles. Les commandes de moteur,
d’indexation et téléchargement utilisées dans les recettes sont simulées.

Safari iPhone physique, Windows chez Marc, coupure réelle d’Internet, dictée
humaine et confort avec un lecteur non informaticien restent à qualifier. Une
capture mobile ou WebKit ne prouve pas ces usages physiques.
