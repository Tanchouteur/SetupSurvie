# Guide de design Veillée

**Guide actuel — 0.63.0, 19 novembre 2026.** Il sert de référence aux
prochaines interventions sur l’interface. Le portail fonctionne avec ses assets
locaux. Les usages de l’installation sont décrits dans le [guide du portail](../utilisation/portail.md).

## Hiérarchie et alignements

- Utiliser Fraunces pour les titres et Atkinson Hyperlegible Next pour le texte
  et les commandes. Reprendre les couleurs et espacements de
  [la feuille de variables](../../portal/design/tokens.css).
- Réserver la braise à l’action principale et à la position courante. Le papier
  chaud forme les surfaces. Le vert signale qu’une ressource est prête.
- Aligner les titres, les commandes et le contenu sur les mêmes marges.
  Une carte garde son titre complet et une commande identifiable. Les liens
  au milieu d’un texte gardent la forme d’un lien. Les actions indépendantes,
  comme ouvrir une collection, ont une zone cliquable et un focus visible.
- Les titres de rubrique ont un chevron à droite et restent sous la navigation
  pendant le défilement de leur rubrique. Les regroupements sont des cartes
  distinctes. Leur contenu occupe la grille entière lorsqu’on les déplie.

## Navigation, lecture et vidéo

- La navigation de bureau regroupe les destinations sur une surface en creux.
  La jauge reprend cette forme et la pastille claire du modèle. Vérifier la
  place disponible avec un nom de profil long et des valeurs à trois chiffres.
  Le numéro de version reste petit, atténué et en graisse normale.
- Pendant la lecture sur ordinateur, les résultats forment une colonne qui
  défile jusqu’au dernier résultat. L’élément ouvert a un repère visuel et
  `aria-current`. Le lecteur garde sa propre largeur. Un document ouvert
  directement occupe l’espace disponible. Sur téléphone, **Résultats** ramène
  à la liste.
- Dans la vidéothèque, mettre en avant **Voir la vidéo** et l’état des pistes.
  Dans le lecteur, garder le choix des pistes près de la vidéo. Sur grand écran,
  le panneau peut prendre place à côté du média quand la colonne des résultats
  est vide. La transcription, la qualité des pistes et les actions secondaires
  sont dépliables. Le suivi et l’entretien ont leurs propres entrées.

## File d’attente

Refonte du 19 novembre 2026 (0.63.0), demandée par Louis qui garde le principe
de la file mais jugeait sa présentation peu réussie : trois niveaux de boîtes
imbriquées, bordures partout, grosses poignées encadrées.

- Un groupe est un titre en Fraunces suivi d’**une seule surface** ; les tâches
  sont des lignes séparées par un filet, sans carte dans la carte. L’aperçu au
  survol reprend la même grammaire avec des intitulés de groupe en petites
  capitales.
- Chaque ligne commence par une **pastille d’état** : verte et pulsée en cours,
  braise pour la suivante, cercle vide en attente, ambre en pause, rouge en
  erreur. La pastille complète le libellé d’état, elle ne le remplace pas.
- Les erreurs et pauses teintent la ligne entière, sans bordure rouge
  supplémentaire. Le libellé d’état reste une pastille de texte à droite.
- La poignée de déplacement est un motif de six points, sans cadre, avec une
  cible de 44 px ; elle prend la braise au survol et au focus.
- Une tâche en erreur montre toujours, dans cet ordre : le message réel, un
  encadré **Que faire ?** rédigé pour une personne qui ne connaît pas
  l’informatique, la commande de relance, puis des **Détails techniques**
  repliés. Le serveur fournit `help` et `retry_label` quand il connaît la
  démarche ; sinon l’interface donne une consigne générique. Un titre-lien est
  souligné, en braise, suivi d’une flèche.
- Les barres de progression sont fines (6 px), vertes pour une tâche en cours,
  braise sinon. La pulsation et l’inclinaison de la carte déplacée s’arrêtent
  avec `prefers-reduced-motion`.

## Mouvement et recette

- Utiliser le mouvement pour signaler un changement précis. La pastille suit
  l’onglet, le chevron accompagne le repli, et le contenu qui s’ouvre peut
  apparaître par une courte variation d’opacité. Les mises à jour de données
  fréquentes doivent laisser les commandes stables.
- Honorer `prefers-reduced-motion` dans les feuilles de style **et** les animations
  pilotées en JavaScript. Le focus et l’état des commandes doivent se comprendre
  avec ou sans animation.
- Vérifier au clavier et au toucher les menus, les cartes, les champs et les
  aides. Vérifier les longs titres, les noms de profil, les listes qui défilent,
  les états de chargement et d’erreur, ainsi que les écrans étroits et courts.
  Utiliser les recettes de navigateur et regarder le rendu avant livraison.
  Les résultats de WebKit en laboratoire et les essais sur un iPhone physique
  doivent être indiqués séparément.
