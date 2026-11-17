# Reprise de la base et finition de l’interface

**Bilan du candidat 0.36.0 — 16 novembre 2026.** Ce chantier répond aux captures
utilisateur après 0.34.0. Il conserve le lot audio des collections intégré entre-temps
en 0.35.0, sans modifier les moteurs ni les données.

## Défauts et corrections

| Défaut observé | Changement |
| --- | --- |
| Gros « i » perturbant la saisie et les formulaires | Aide retirée de la saisie ; aides facultatives compactes et séparées des libellés |
| Case et explication séparées | Case et texte alignés, clic sur le libellé, champ documentaire nommé explicitement |
| Trois boutons de volets peu clairs, Discussion redondant | Fermeture dans chaque volet, réouverture dans l’en-tête ; retour direct à la conversation sur mobile |
| Deux commandes Nouvelle discussion | Un seul contrôle, déplacé selon l’espace disponible, ID et comportement préservés |
| Peu d’évolution hors de l’accueil et de l’assistant | Cartes, paramètres, état de l’appareil, recherche, collections et lecteurs repris avec les mêmes règles |
| Cartes de paramètres de tailles et structures différentes | Modèle partagé titre/description/action, grilles égales et actions alignées ; formulaires longs non tronqués |
| Cascade fragile | Thème complet de l’ancienne maquette retiré, anciennes règles de conversation supprimées, responsabilités CSS séparées |
| Carte sans affichage graphique exposant une erreur technique | Explication française visible dans la zone de carte, commandes graphiques désactivées et retour vers la bibliothèque |
| Scripts et générateur difficiles à suivre | Modules repris formatés, primitives UI sans API, liste ordonnée des ressources dans le générateur |

La version mineure correspond à une évolution significative de l’interface et
de son organisation. Les API et `data_schema: 1` restent compatibles. Aucune
version tierce de fonctionnement n’a changé. Le [guide des composants](../architecture/composants-interface.md)
explique aussi le choix de rester sur une petite base locale après examen de
bibliothèques existantes.

## Vérifications enregistrées

Runner Linux CPU, API et inférence simulées, petites fixtures. Aucune nouvelle
inférence réelle, aucun modèle ni corpus lourd téléchargé.

- Suite Python : **962 tests, aucun échec, 6 ignorés**, environ 207 s.
- Recettes existantes : les douze recettes du lanceur paramètres passent sous
  Chromium et WebKit, dont 182 contrôles paramètres, 51 recherche, 29 portail,
  16 volets et dossiers, 13 traduction dans les lecteurs et 41 fondations UX.
- Nouvelle recette de finition : 126 contrôles par moteur, dont les cartes
  dépliables et leurs descriptions, avec cartes
  de descriptions longues, état peuplé, cases, fermeture/réouverture, cinq
  largeurs et vérification des zones cliquables. La recette vérifie aussi le
  chevauchement des libellés de navigation et les volets pendant la saisie mobile.
- Vérifications ciblées finales : Chromium, WebKit et Firefox passent chacun
  les contrôles de finition, 38 de confort de discussion, 9 du repli graphique
  des cartes et le cycle association/pause/reprise/export/plage PDF.
- Cartes : 15 tests unitaires adaptés réussis. Le repli graphique est testé avec
  un pilote volontairement indisponible ; le Firefox Linux du conteneur confirme
  aussi l’absence de contexte WebGL dans cet environnement, ce qui ne prouve pas
  l’état graphique du PC Windows de Marc.
- Syntaxe JavaScript, génération HTML et `git diff --check` vérifiés.
- Captures Playwright MCP examinées sur PC et téléphone, avec réponses longues,
  tableaux, options ouvertes, dossiers, recherche et lecteur.

La vérification initiale des cartes de destination comptait 94 contrôles ; les
32 vérifications supplémentaires portent sur les cartes dépliables dans quatre
rubriques et à quatre largeurs. Le comparatif de recherche a aussi révélé une
hypothèse fragile dans la recette WebKit : un panneau déjà mémorisé ouvert était
refermé par un clic sans vérification. La recette respecte désormais cet état et
attend ses champs visibles ; aucun contrôle fonctionnel n’a été retiré.

La recette complète et la CI du dernier état sont suivies avant intégration.
Le résultat final et le commit intégré seront ajoutés à la clôture.

## Portée de la preuve

Une revue visuelle complète les assertions : l’absence de débordement ne suffit
pas à juger le design propre. Ces essais couvrent les défauts signalés et les
régressions trouvées pendant la reprise ; ils ne certifient pas l’absence de
n’importe quel bogue futur. Safari sur iPhone physique et la perception de Marc
restent distincts des navigateurs automatisés.

Aucune mise à jour du PC de Marc ou de Louis n’est exécutée par ce chantier.
La procédure normale de mise à jour conserve les données ; les anciennes
références et leurs limites restent dans le [guide de retour](../exploitation/retour-version-avant-refonte.md).
