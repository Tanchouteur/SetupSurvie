# Paramètres par usage — 14 novembre 2026

**Bilan 0.12.0 — préparation de livraison après recherche 0.11.1.**

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
Les captures après proviennent du code 0.12.0 ; les avant ont été prises avant
modification, avec les mêmes dimensions (1440 × 950 et 390 × 844).

| Écran | Avant (0.11.0) | Après (0.12.0) |
| --- | --- | --- |
| Paramètres ordinateur | [Avant](captures/parametres-ux/avant-ordinateur.png) | [Après](captures/parametres-ux/apres-ordinateur.png) |
| Paramètres téléphone | [Avant](captures/parametres-ux/avant-mobile.png) | [Après](captures/parametres-ux/apres-mobile.png) |

Autres vues : [assistant sur téléphone](captures/parametres-ux/assistant-mobile.png),
[bibliothèque sur téléphone](captures/parametres-ux/bibliotheque-mobile.png),
[vue d’ensemble sur ordinateur](captures/parametres-ux/appareil-ordinateur.png).
Les boutons du moteur sont désactivés dans ces captures car la fixture ne fournit
pas de contrôleur réel ; leur déclenchement est vérifié avec des API simulées.

## Vérifications pendant la préparation

Sur la base initiale : 503 tests Python réussis, 12 ignorés (dépendances natives
optionnelles et tests Windows non applicables au runner Linux). Les parcours
Chromium déplacés ont réussi : recherche, outils, catalogue, assistant, comparatif
et dossiers. Le nouveau parcours UX contrôle les liens directs, les IDs uniques,
les rubriques ouvertes, les brouillons et l’absence de commande à l’ouverture.
Après fusion de `3254f2e` puis du complément documentaire `3e46f30` : **508 tests
Python réussis, 13 ignorés** dans le runner (lecteur natif facultatif absent et
contrôles Windows). Le contrôle du générateur repasse après changement du cache.
Les recettes finales des navigateurs et la CI sont consignées ci-dessous avant
intégration.

Les essais utilisent exclusivement des documents minuscules et des API simulées,
sans modèle, gros corpus ni accès aux données réelles. Les commandes de moteur,
d’indexation et téléchargement utilisées dans les recettes sont simulées.

Safari iPhone physique, Windows chez Marc, coupure réelle d’Internet, dictée
humaine et confort avec un lecteur non informaticien restent à qualifier. Une
capture mobile ou WebKit ne prouve pas ces usages physiques.

## Défauts détectés et corrigés pendant la recette

- Une sous-rubrique de réglages pouvait être remplacée par l’accueil pendant la
  lecture asynchrone du profil. La destination attendue est maintenant conservée.
  Un profil lecteur ouvre une seule liste de choix, sans doubles boutons Famille.
- Le rechargement ne conserve plus le marqueur d’un dialogue fermé, qui pouvait
  réapparaître au prochain retour navigateur.
- Les deux couches de navigation écrivaient successivement une adresse historique
  puis l’adresse moderne. WebKit atteignait sa limite lors des passages répétés.
  `portal/app.js` laisse maintenant le routeur moderne gérer l’adresse. Les
  écritures de position identiques sont évitées ; le défilement est mémorisé au
  plus toutes les 250 ms, puis immédiatement avant départ/navigation.
- La première CI a aussi révélé une attente de test qui lisait `S` avant la fin
  d’un rechargement de profil. Les recettes attendent sa présence. Cette correction
  du test ne remplace pas les contrôles de conservation des profils et brouillons.

La charte est conservée. Les doublons de navigation sont retirés ; les panneaux
fonctionnels et leurs contrôles restent uniques. Les options avancées restent
secondaires. Les actions de moteur et de pause accessibles au téléphone gardent
les mêmes contrats et avertissements ; aucun travail ne démarre à l’ouverture.
