# Guide de design Veillée

**Guide actuel — 0.63.0, 19 novembre 2026 ; compléments 0.65.0 à 0.70.0 datés dans le texte.** Il sert de référence aux
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

## Pages de réglage ponctuel

Ajout du 20 novembre 2026 (0.65.0), après le retour de Louis sur le tri des
collections jugé inutilisable dans l’onglet Collections.

- Un réglage fait une fois (tri des collections) vit dans sa page de
  **Mon appareil → Paramètres** ; la page de consultation ne garde qu’une ligne
  de résumé et un raccourci, plus une étiquette discrète sur les cartes.
- La page commence par une légende des choix possibles, chacun avec sa couleur :
  vert pour le fonds principal, ocre pour Autre, rouge pour la suppression.
  La même couleur marque la ligne (filet gauche) et l’interrupteur.
- Chaque ligne nomme l’élément tel qu’un humain le reconnaît, puis son type,
  sa taille, un **Aperçu ↗** et le nom technique en petit. Le choix courant est
  un interrupteur à deux positions enregistré immédiatement.
- Un en-tête qui se replie n’a pas l’apparence d’un bouton plein : ni fond sombre
  au survol, ni effet d’enfoncement ; le titre se souligne et le chevron, gris,
  garde un espace avec la case à cocher. Replié, il résume son contenu. Le choix
  sélectionné d’un interrupteur est une pastille claire au texte coloré, pas un
  aplat plein (retour de Louis du 20 novembre 2026, 0.65.2).
- Les actions groupées apparaissent dans une barre collante seulement quand
  quelque chose est coché. Une suppression passe par un écran de confirmation
  qui nomme les éléments et le volume libéré.

## Toujours informer — 0.70.0

Demande de Louis du 20 novembre 2026 après l’[audit du portail](../essais/2026-11-20-audit-ux-et-maintenabilite-portail.md) :
une personne qui ne comprend pas tout doit savoir quoi faire et ne jamais rester
sans information, avec un rendu soigné. Il demande aussi de **garder visibles
le modèle chargé, la RAM et la VRAM**, utiles pour surveiller l’appareil.

- **Réseau.** Toute requête `/api/` passe par `portal/core/net.js`. Ne pas
  afficher `error.message` brut d’un `fetch` : la couche le traduit déjà, et
  `toast()` applique `SurvieNet.humanize`. La perte de connexion est annoncée
  par le seul bandeau `#connection-banner` (rouge, compte à rebours, nouvel
  essai, lien vers les documents de secours), qui se masque pendant une
  maintenance. Ne pas créer de second bandeau de connexion dans un module.
- **Messages éphémères** en haut à droite (sous l’en-tête sur téléphone),
  jamais sur la zone de saisie. Ton déduit du texte (`data-tone` : info,
  succès, erreur) ou passé en second argument de `toast()`.
- **Opérations.** Un bouton désactivé juste après un clic montre un cercle
  animé (`.is-busy`) jusqu’à sa réactivation, puis un bref halo de fin.
  Ajouter `no-busy` à un bouton qui ne doit pas l’afficher ; utiliser
  `SurvieFeedback.busy(bouton, promesse)` pour une action qui ne désactive pas
  son bouton. Une liste en chargement vide et marquée `aria-busy="true"`
  montre des silhouettes de cartes (`.ds-skeleton` pour d’autres conteneurs).
- **Une phrase d’état, puis le détail.** Les résultats et états tiennent en
  une phrase concrète qui nomme ce qui a été fait (« Aucun résultat pour
  « … » dans « … » »). L’avertissement utile reste visible en petit dessous ;
  les précisions techniques vont dans un « Détails » replié. L’action suivante
  la plus utile vient en premier.
- **Écran vide = écran utile.** Un écran sans contenu propose un point de
  départ (idées, dernières recherches) ou rassure (« Rien en cours »), avec une
  seule surface plutôt qu’un encadré vide par section.
- **Résumé avant mesures.** Mon appareil commence par « Tout fonctionne » ou
  « N points à regarder », chaque point avec son explication et son action. Les
  mesures (modèle chargé, RAM, VRAM) restent dessous et dans l’en-tête ; la
  pastille compacte `.resource-chip` les garde visibles sur téléphone.
- **Assistant.** L’état (prêt, démarre, pause, arrêté, injoignable) s’écrit
  près de la saisie, et la frise d’étapes (préparer, chercher, lire, rédiger)
  accompagne une réponse en cours. Le libellé du modèle reste disponible.
- **Téléphone.** L’en-tête garde logo et commandes ; le titre de l’écran est le
  grand titre de la page. Les rangées d’onglets défilent avec un fondu de fin.
  Texte d’au moins 12 px, cibles d’au moins 40 px.
- **Couleurs et tailles.** Toute nouvelle couleur vient de
  `design/tokens.css`, chargé en premier ; `tests/test_portal_design_budget.py`
  refuse l’ajout de couleurs ou de tailles de police brutes et ses plafonds ne
  font que baisser. Les couleurs quasi identiques (écart ΔE ≤ 2) des anciennes
  feuilles pointent déjà vers les variables, avec l’ancienne valeur en repli.
- **Mouvement.** 150 à 250 ms en décélération pour les apparitions ; boucles
  réservées à un travail réellement en cours (cercle, pulsation du point).
  Tout s’arrête avec `prefers-reduced-motion`. Les transitions entre écrans
  restent l’apparition courte existante (`ds-rise`) : l’API View Transitions
  rendrait le changement d’écran asynchrone pour des modules qui l’attendent
  synchrone.

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
