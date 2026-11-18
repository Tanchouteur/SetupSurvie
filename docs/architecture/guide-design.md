# Guide de design Veillée

**Guide actuel — 0.49.0, 18 novembre 2026.** Il sert de référence aux
prochaines interventions sur l’interface. Le portail fonctionne avec ses assets
locaux. Les usages de l’installation sont décrits dans le [guide du portail](../utilisation/nouvelle-interface.md).

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
