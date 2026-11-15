# Synthèses longues, notes et reprise — 0.18.0

**Bilan de développement — 15 novembre 2026.** Nouvelle fonctionnalité compatible,
donc version mineure 0.18.0 ; schéma de livraison 1, profils conseillés et images
tierces inchangés. Ce bilan ne clôt pas l’objectif d’utilité de l’assistant.

## Problème et choix retenu

En 0.17.0, choisir plusieurs livres permet de comparer des passages pertinents,
pas de lire tout leur texte. La synthèse longue ajoute une action explicite,
distincte de la réponse rapide. Elle copie la sélection dans sa propre conversation,
prépare des instantanés privés, lit les passages par étapes puis regroupe les
notes avant de rédiger. Le [guide actuel](../utilisation/synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180)
décrit le parcours, ses plafonds et ses limites.

Chaque étape terminée est conservée dans SQLite. Pause, annulation d’une étape,
redémarrage et reprise ne recommencent pas les étapes déjà validées. Un fichier
modifié pendant sa préparation est refusé ; une reprise conserve les textes déjà
préparés. Les pages sans texte, documents indisponibles et aperçus tronqués
ne deviennent pas silencieusement des lectures complètes.

Les notes citent un extrait présent dans le texte original, avec page et position.
Les regroupements désignent les notes précises dont ils proviennent, et leurs
sources/pages suivent cette chaîne. Les notes sont des productions documentaires
à relire, pas le raisonnement privé du modèle. Elles restent consultables et
exportables, y compris après un échec. La réponse finale est enregistrée une seule
fois ; les sources PDF donnent accès aux pages retenues. Les premières douze pages
retenues par source sont proposées dans les boutons, les autres restent dans les notes.
Le moteur, sa pause et la file des questions restent partagés ; aucun démarrage
forcé. Une question dans la même conversation doit terminer avant la reprise.
Les fonctions de synthèse sont optionnelles et ne doivent pas bloquer le cœur.

## Approches corrigées pendant les essais

- La première réduction référençait un lot entier. Un lot comportant plusieurs
  sources attribuait alors trop de sources à certaines conclusions. Elle désigne
  maintenant une note individuelle par `étape:note` ; un test protège ce cas mixte.
- Le premier essai réel lisait les 42 pages, retrouvait les deux valeurs et leurs
  pages, mais sans numéros de référence cliquables : état incomplet conservé.
  La rédaction peut maintenant être suivie d’une liaison structurée de références,
  sans régénérer les faits. Une liaison échouée conserve le brouillon incomplet.
- Un bouton restait désactivé après le choix d’un document. Le suivi reçoit
  maintenant les changements d’état de la sélection ; le parcours navigateur
  protège le clic, la pause, le rechargement et la reprise.
- Une page explicitement choisie reste une page ; on n’étend pas silencieusement
  la lecture à tout le PDF. Aucun lancement long implicite pour une question rapide.

## Preuves disponibles

Les tests simulés couvrent instantanés complets, dernières pages, pages vides,
texte tronqué, provenance mixte, pause en vol, redémarrage sans inférence automatique,
reprise sans relire un original modifié, suppression en cascade, accès par profil,
verrou partagé, sortie interrompue, contexte insuffisant, export et réponse unique.
Les tests historiques d’extraction/traduction restent exécutés après leur partage
du lecteur de texte. Ils ne prouvent pas une traduction fidèle sur modèle réel.

Les essais navigateur utilisent de petits PDF et des réponses simulées, sur
Chromium et WebKit, y compris aux largeurs 390 et 320 pixels. Captures privées
`setupsurvie-0180-summary-desktop.png` et `setupsurvie-0180-summary-mobile.png`.
Les émulations ne remplacent pas Safari sur un vrai iPhone.

Le R7 utilise un vrai `gemma4:e4b`, contexte 16k, huit couches GPU demandées,
six threads, réserve vidéo de 1 536 Mio et maintien du modèle de quinze secondes.
Aucun autre modèle/processus n’est arrêté. Ollama natif 0.40.14 est distinct de
l’image épinglée 0.40.13 du pilote. Deux PDF fictifs de 21 pages placent les faits
uniquement à la page 21. Les premiers passages sont volontairement sans valeur
utile ; les sources ne constituent pas de vraies contradictions scientifiques.

Le premier essai après correction de provenance termine en **77 546 ms**, puis
le rejeu avec les contrôles de fichier/reprise en **79 515 ms** : 42 passages sur
42 examinés, sept étapes de notes dont un regroupement. Les deux valeurs 17 et
59, leur attribution, leur limite de non-extrapolation, dates, éditions et pages
21 sont correctes dans les réponses relues. Les notes finales transportent
respectivement seulement la source 1 et la source 2. Les rapports restent privés.
Le paragraphe comparatif final répète les valeurs sans références sur chaque
phrase ; les faits précédents portent les bonnes références. Ce n’est pas une
certification de couverture phrase par phrase.

## Limites et suite

Pas d’essai d’un vrai livre de 500 pages, d’OCR, d’extraction/interprétation de
schémas, d’un grand ensemble de contradictions ni du corpus Windows de Marc.
Les notes peuvent omettre des faits ou déformer leur sens ; leur compression
rend ces contrôles éditoriaux nécessaires. Un numéro et un extrait existants ne
valident pas une conclusion. Les citations courtes peuvent également ne pas
couvrir toute une paraphrase : cette fidélité reste à éprouver.

La suite conserve illustrations originales, scénarios représentatifs avec les
modèles conseillés, puis amélioration de la traduction et acquisition/création
contrôlée des sous-titres français. Aucun sous-titre créé par ce lot ; l’inventaire
vidéo livré précédemment reste distinct de ces traitements.

## Rejeu du candidat final

Le candidat fonctionnel `cad905c` incluant les liens vers les pages termine en **74 265 ms** : 42/42
passages, sept étapes enregistrées, valeurs 17 et 59 correctement attribuées,
limites, dates, éditions et pages 21 conservées. Le modèle écrit cette fois les
références sous la forme `[1, p. 21]` dans le corps, avec `[1]` et `[2]` dans la
bibliographie. Les boutons de sources proposent aussi les pages ; ce format
composé n’est pas transformé en bouton dans le corps du texte.
Empreinte du code Python `f0e72e4024423967b57abbd4c1b9647fbc21bfdf0c919d2619fc18cd12595c5c`.
Rapport privé `report-gemma4-long-summary-release-0180.json`, SHA-256
`6fcd9a026c650e313231441cf6050391d888a069c830d70af54d40da7c4ca815`.
Les essais précédents et leurs limites restent conservés : ce rejeu ne les efface pas.

## Vérifications locales finales

- 686 tests unitaires réussis, dont trois ignorés propres à Windows sur le runner
  Linux ; les 21 tests ciblés du nouveau parcours passent aussi séparément.
- 97 contrôles par Chromium et WebKit : synthèse longue 18, sélection 19,
  confort 37 et diagnostic 23. Les liens de dernière page sont réellement ouverts.
- 418 liens locaux et ancres vérifiés dans les documents concernés ; `git diff --check`
  sans erreur. Aucun modèle ni corpus lourd téléchargé dans le runner CPU.
- Aucune installation, mise à jour ni validation physique Windows/iPhone chez Marc.

Le suivi conserve maintenant les extraits dépliés lors des actualisations et
ajoute la réponse finale sans recharger la conversation. Le parcours commence
aussi sur écran mobile : quitter le champ de question déplaçait l’en-tête pendant
le clic et pouvait faire viser le mauvais contrôle. L’en-tête reste stable lorsque
le panneau de synthèse est ouvert ; le clic réel est protégé par la recette.
