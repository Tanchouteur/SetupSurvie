# Lire pendant une traduction

**Bilan du candidat 0.28.0 — 16 novembre 2026.** Demande de Louis après les
rapports Windows 0.25.0. La [direction générale des conversations](../decisions/conversations-trois-zones.md) est validée ; les détails attendent encore le cadrage de Louis.

Le panneau ordinaire montrait déjà les dix premiers passages et son compteur.
Il reconstruisait cependant tous les éléments à chaque actualisation, refermant
les comparaisons et perdant une sélection de texte. Après rechargement, il
revenait au début ; pause et reprise y revenaient aussi. Ce défaut rendait la
lecture d’une traduction en cours inconfortable.

Le candidat ajoute les pages/sections entièrement terminées, celles commencées,
et la page qui attend encore un passage. Une page sans texte extractible ne
compte jamais comme traduite. La barre compte les passages réellement traduits.
Le lecteur indique explicitement que les passages terminés sont lisibles pendant
que le moteur poursuit le document.

Les cartes inchangées restent les mêmes éléments DOM ; la lecture, le texte
sélectionné et les comparaisons ouvertes survivent aux actualisations. Les cartes
modifiées sont remplacées individuellement. Aucune navigation automatique vers
la dernière page n’interrompt la lecture. Deux commandes explicites donnent
accès au début et au groupe contenant les derniers passages traduits.

Le groupe de dix passages affiché est mémorisé par profil et traduction dans le
navigateur, sans texte ni conversation dans cette mémoire. Rechargement et retour
à la conversation le retrouvent ; pause/reprise ne déplacent pas le lecteur.
La fenêtre de lecture dédiée libère la place occupée par le formulaire de conversation.
Son ouverture est aussi retrouvée après rechargement ; Fermer, Échap et retour
navigateur restent disponibles. La fermeture explicite ne doit pas être annulée
par une actualisation de progression.

Cette position de lecture n’est pas synchronisée entre appareils ; le travail
traduit et sa progression restent enregistrés côté serveur et transférables.

Les appels de consultation restent des GET locaux ; ils ne démarrent aucune
inférence. L’accès reste associé au profil propriétaire du travail. Le brouillon
est consultable depuis sa conversation avant d’être partagé : seule une
traduction terminée rejoint la publication automatique. Aucun nouveau modèle,
aucune modification des seuils de contrôle ou migration de données.

Version **y** car le parcours de lecture évolue de façon significative, tout en
conservant les champs/API antérieurs et les données. La formule « entièrement
traduit » décrit la couverture des passages, pas leur fidélité sémantique.

## Validation

Un test Python construit une page partiellement traduite, une terminée, une
illisible et une en attente ; il contrôle leurs compteurs, la page courante,
le dernier passage et l’accès d’un autre profil. Une recette navigateur simule
un livre de trente pages avec des arrivées successives : lecture immédiate,
actualisation sans remplacement du passage déjà lu, comparaison et sélection
conservées, accès volontaire à la fin, pause, rechargement sans relance et trois
largeurs d’écran. Les premiers essais Chromium/WebKit passent ; une recette renforcée vérifie aussi
la fenêtre de lecture, sa fermeture et sa restauration. La CI finale est encore
en cours. Aucun nouveau délai ou résultat de fidélité du
modèle de Marc n’est revendiqué.

## Incidents conservés pendant les recettes

Le premier ensemble intégré `40886ba` réussit la lecture progressive sur les
deux navigateurs, puis rencontre une erreur WebKit de chargement du worker PDF
pendant la recette des illustrations originales. L’import différé pouvait
reprendre après `pagehide` et créer un worker alors que la page quittait son
origine. Le correctif vérifie le départ et la présence de l’image après import,
arrête la file d’aperçus et détruit les tâches PDF en cours. Le fournisseur PDF.js
et ses versions restent inchangés. Une recette retarde réellement l’import,
déclenche le départ puis vérifie qu’aucun worker n’est créé tardivement.
La relecture normale des illustrations et la CI finale restent requises.

Le lecteur dédié a également révélé une course à la fermeture : une actualisation
pouvait relire l’état « ouvert » avant l’événement de fermeture et rouvrir la
fenêtre. Le choix de fermeture est maintenant enregistré avant la fermeture,
et la restauration automatique ne se fait qu’à la première lecture du travail.
La recette vérifie fermeture, pause, rechargement et retour sans retirer les
assertions de navigation ou d’erreur JavaScript.

Le rejeu local des illustrations rencontre ensuite la même famille d’erreur sur
la vérification facultative de version française : ce module avait son propre
`fetch`, hors du suivi commun des requêtes de page. Il annule maintenant ses
requêtes au départ et refuse de démarrer une vérification tardive. Les aperçus
et cette vérification peuvent repartir après un retour depuis le cache du
navigateur. Une seconde recette retient réellement une requête puis contrôle son
annulation et sa reprise après `pageshow` ; l’original reste lisible.
Les recettes normales des illustrations et du lecteur bilingue repassent sur
Chromium et WebKit, sans filtrer les erreurs de page.

L’arrêt d’un wrapper PDF.js seul ne suffisait pas : son port natif n’est conservé
qu’après le signal de disponibilité. Le portail possède maintenant ce port dès
la construction et le termine aussi pendant son démarrage. La recette retenant
ce signal échoue avec l’ancien code et réussit avec le nouveau. Les requêtes sont
aussi annulées dès `beforeunload`, avant la désactivation du document, sans
confirmation ni attente de fin du modèle. **Cinq relectures natives successives
sous WebKit**, avec les deux rechargements de la recette et sans filtre d’erreur,
réussissent après cet ajustement. Le PDF reste rendu dans un vrai Worker.

## Recette locale finale

Les six recettes ciblées terminent : **77 contrôles sur Chromium et 77 sur
WebKit** (lecture progressive, requêtes françaises, import PDF tardif,
démarrage du Worker, rendu natif des illustrations et lecture bilingue).
Les annulations de navigation sont distinguées d’un vrai délai de lecture ;
un abandon avant désactivation conserve ainsi le contrôle facultatif pour un
retour, tandis qu’un délai réel garde son message de reprise. La reprise depuis
le cache est simulée par ses événements ; un Safari physique reste à essayer.

Captures de la recette, avec données fictives et sans génération réelle :
[ordinateur](images/traduction-progressive-0280-pc.png),
[téléphone 390 px](images/traduction-progressive-0280-mobile.png).
La CI finale de cette dernière correction est encore en cours ; ne pas confondre
ces contrôles locaux avec une nouvelle traduction exécutée chez Marc.

La restauration du lecteur réutilise aussi l’entrée d’historique courante, afin
que chaque rechargement ne rajoute pas une étape de retour. Un événement de
fermeture arrivé tardivement ne referme pas le repère d’une fenêtre rouverte par
Avancer. La recette renforcée vérifie la taille de l’historique, Retour/Avancer
et Échap, soit **24 contrôles de lecture par navigateur**.
