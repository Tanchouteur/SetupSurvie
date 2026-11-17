# Projets dépliables et largeur du volet — 17 novembre 2026

Statut : bilan du candidat 0.38.0, intégration finale en cours.

## Comportement

La demande de Louis et sa capture du 17 novembre conduisent à afficher les
conversations directement sous chaque projet dépliable. Les anciens dossiers
utilisent les mêmes identifiants et API ; aucune migration n’est nécessaire.
Une seule surface défile verticalement pour atteindre tous les projets et fils.
Les titres restent sur une ligne avec une ellipse ; le titre complet est
disponible au survol. La poignée de déplacement reste visible au format PC,
même si le navigateur ne déclare pas la capacité de survol.
Le menu de chaque projet et conversation permet le renommage. Recherche,
classement par menu et glisser-déposer restent disponibles.

Sur PC, la séparation du volet accepte la souris et le clavier (flèches,
Début/Fin). La largeur est bornée entre 220 et 480 pixels, selon la place
restante pour la discussion. Sur téléphone, les volets conservent leur ouverture
séparée. Les projets ouverts sont mémorisés par profil dans l’onglet.
La liste d’un projet charge ses conversations à l’ouverture et propose la suite
au-delà de 100 éléments, avec reprise sur erreur.

La version augmente de 0.37.3 à **0.38.0** : nouvelle fonctionnalité compatible,
schéma de données 1 et versions tierces conservés. Les corrections documentaires
et de formules de 0.37.3 sont intégrées avant cette livraison.

## Vérifications réalisées

- Tests unitaires du classement : 3 réussis ; génération des portails : 2 réussis.
- Recette du volet : 22 contrôles réussis dans Chromium, WebKit et Firefox sur
  fixtures, dont renommage, classement, imbrication, repli et réglage au clavier.
- Recettes existantes de confort et de glisser-déposer passées sur Chromium et
  WebKit ; 35 contrôles de glisser-déposer repassés sur Firefox depuis la poignée
  dédiée ; vérification ciblée de l’aide au clavier sur WebKit.
- Playwright MCP : déplacement réel de la séparation jusqu’à 340 pixels,
  relâchement de la capture du pointeur, conversation imbriquée et projet renommé.
- Plus de 25 projets sur fixture : défilement jusqu’au bas du volet ; largeur
  mobile de 390 pixels sans débordement horizontal.
- Le test d’aide attend la restauration du focus du routeur ; le contrôle de
  largeur cible directement la séparation après changement de format.
- Le test de plage PDF attend l’identifiant du travail qu’il vient de créer et
  vérifie aussi les bornes envoyées, avant d’en examiner les passages. Le parcours
  PDF passe localement dans Chromium et WebKit après la navigation du portail.

CI complète : résultat à consigner avant fusion de la
[PR 18](https://github.com/Tanchouteur/SetupSurvie/pull/18).

## Limites

Les tests utilisent de petits documents fictifs et une inférence simulée.
Aucune validation physique sur les PC de Louis ou Marc ni sur iPhone n’a été
faite pour ce lot. Le code n’est pas encore déployé sur ces machines.
Aucun modèle, corpus ou service utilisateur n’a été démarré pour ces essais.
