# Paramètres par usage — 14 novembre 2026

**Bilan 0.12.0 — livraison après recherche 0.11.1.**

Le [guide actuel](../utilisation/parametres-et-appareil.md) contient l’inventaire
complet des commandes et leurs nouvelles destinations. Les quatre entrées
regroupent profils/connexion, bibliothèque/préparations, assistant et entretien.
Mon appareil sépare vue d’ensemble et travaux en cours ; les mesures détaillées
et essais techniques sont dépliables. Les commandes sont déplacées, sans clonage.

La base initiale est `af30c09` (cartes 0.11.0 conservées). La recherche 0.11.1
a été intégrée d’abord sur main ; ses moteurs et nouveaux diagnostics sont conservés.
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
Les neuf recettes concernées totalisent **378 vérifications par navigateur** :

| Parcours | Chromium | WebKit |
| --- | --- | --- |
| Nouveau parcours paramètres, liens directs, profils, brouillons, clavier, pause/arrêt simulés, mémoire, retour carte | 175 | 175 |
| Portail, documents, conversation, rechargement, cartes directes et mobile | 29 | 29 |
| Recherche et diagnostic détaillé 0.11.1 conservé | 49 | 49 |
| Outil/indexation et contexte simulés | 18 | 18 |
| Classement et export des métadonnées | 20 | 20 |
| Mesures et essai mémoire simulés | 19 | 19 |
| Comparatif IA simulé | 16 | 16 |
| Dossiers pratiques et export | 20 | 20 |
| Contrôle d’usage hors ligne sur fixtures | 32 | 32 |

Les tailles 320, 390, 760, 820 et 1440 px sont contrôlées sans débordement, avec
navigation, focus clavier et accès au suivi. Les rubriques avancées, les
historiques précédent/suivant, les liens conservés, la saisie des formulaires
pendant la visite et les brouillons de conversation après rechargement sont vérifiés.
Les IDs sont uniques et les ancêtres nécessaires aux contrôleurs conservés.
Un changement de profil conserve le brouillon Famille et ne le reprend pas dans
le nouveau profil. L’arrêt et le démarrage simulés reçoivent exactement un appel
par clic ; la simple navigation ne lance aucune commande.

Le paquet candidat `a638f0a` a été construit et décompressé par le lecteur réel :
**721 fichiers validés**, version API/manifeste 0.12.0, assets UX et HTML identiques
au worktree, intégrité ZIP conforme. Cela ne constitue pas une installation sur
le PC de Marc. Les liens locaux et leurs ancres sont contrôlés ;
`git diff --check` réussit. Les fichiers ajoutés sont du logiciel, de la
documentation et des captures fictives ; aucune donnée privée ni contenu lourd.

Pour reproduire les recettes, lancer le serveur de fixtures dans l’environnement
Python isolé, puis le runner avec Playwright installé (comme en CI) :

```bash
python tests/browser_translation_server.py
# Dans un autre terminal, avec le module Playwright disponible :
UX_BASE=http://127.0.0.1:8769 node tests/browser_settings_runner.cjs
```

Le runner couvre Chromium et WebKit, crée un contexte isolé par recette et écrit
ses résultats/captures sous `/tmp/setupsurvie-settings-artifacts`. Les essais de
ce bilan utilisent le port 8782 pour éviter les autres travaux du runner ; les
navigateurs sont exécutés dans l’image Playwright TEST déjà disponible, sans
secrets, GPU ou données utilisateur.

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
  puis l’adresse moderne. Pendant la matrice rapide, WebKit pouvait rester sur
  l’adresse historique (`#storage`) ; ce défaut n’est plus reproduit après correction.
  `portal/app.js` laisse maintenant le routeur moderne gérer l’adresse. Les
  écritures de position identiques sont évitées ; le défilement est mémorisé au
  plus toutes les 250 ms, puis immédiatement avant départ/navigation.
- La première CI a aussi révélé une attente de test qui lisait `S` avant la fin
  d’un rechargement de profil. Les recettes attendent sa présence. Cette correction
  du test ne remplace pas les contrôles de conservation des profils et brouillons.
- Les recettes exécutées dans le même navigateur peuvent retrouver un panneau
  déjà ouvert. Elles le déplient seulement si nécessaire, au lieu de le refermer
  involontairement ; la mémorisation demandée reste testée.

La charte est conservée. Les doublons de navigation sont retirés ; les panneaux
fonctionnels et leurs contrôles restent uniques. Les options avancées restent
secondaires. Les actions de moteur et de pause accessibles au téléphone gardent
les mêmes contrats et avertissements ; aucun travail ne démarre à l’ouverture.

## CI et intégration

La [PR #10](https://github.com/Tanchouteur/SetupSurvie/pull/10) porte
`codex/parametres-ux`. Le code final **`32dbed5`** réussit les **huit jobs** de la
[CI du 14 novembre](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43642402141) :
Linux, Windows, lecteurs Python Windows 3.11/3.13/3.14, Kiwix synthétique,
itinéraires synthétiques et interface/cartes. Ce dernier exécute aussi la suite
complète Chromium/WebKit (documents, profils, traduction, favoris, navigation et
recettes déplacées), avec les 175 vérifications UX ajoutées. Les derniers ajouts
au bilan et aux guides sont documentaires et ne modifient pas ce code validé.

La suite complète Chromium réussit également en TEST local. Un passage de la
suite complète WebKit locale a expiré dans l’attente du rendu PDF page 3
(`browser_documents.js`), avant le parcours UX ; il n’est pas présenté comme
réussi. Les neuf recettes ciblées WebKit (378 contrôles) et la suite complète
WebKit de la CI ont réussi. Ce résultat ne constitue pas une validation de Safari
sur un iPhone physique, ni une garantie sur tous les PDF du fonds réel.

La fusion reprend successivement la recherche `3254f2e` et son bilan de paquet
`3e46f30`, puis l’UX. Les notes de contrôle des 708 fichiers de recherche sont
conservées. Le paquet UX ajoute seulement les fichiers recensés dans ce bilan ;
les modèles, corpus, cartes et données personnelles restent séparés du logiciel.
