# Titres de tâches et mentions dans des textes généraux

**Bilan de développement — 0.13.1, 15 novembre 2026.** Suite à l’audit du moteur
après la [livraison 0.13.0](2026-11-14-recherche-0120-et-travail-nocturne.md).
Les exports privés 0.12.0 orientent l’examen ; leurs extraits ne constituent pas
une relecture humaine des documents ni une mesure du nouveau classement.

## Défaut reproduit

Sur deux candidats fictifs, « réparer un vélo » plaçait un texte général intitulé
« Les vélos d’aujourd’hui » avant « Mécanique vélo/Réparer un pneu », trouvé par
son titre. Les scores étaient 112 et 99 : la mention de l’action dans l’extrait
du premier et sa présence du sujet au titre suffisaient à dépasser la tâche nommée.
Même défaut pour « installer un panneau solaire », scores 118 et 99. Un contrôle
supplémentaire sur l’entretien d’une vanne reproduit le cas hors vocabulaire vélo.

La correction donne davantage de poids à un titre portant tous les concepts
du sujet et l’action demandée, lorsque la question est pratique. Un titre de
contexte « pourquoi » ou « histoire » seul ne reçoit pas cette priorité ; un
titre associant « pourquoi et comment » peut la recevoir. Les demandes « pourquoi »
sans « comment » sont explicatives et ces mots de question ne deviennent pas
des mots obligatoires du sujet. L’article général reste dans les résultats
quand il correspond à la demande. Aucune source n’est renommée ou remplacée.

Le type et l’état du document restent inchangés : une correspondance dans un
titre n’est pas une source lue ni une procédure humainement examinée. Aucune
nouvelle ressource ou liste de liens manuels ne cache le défaut de classement.

## Vérifications exécutées

Huit tests ciblés couvrent tâches françaises/anglaises, entretien d’une vanne,
explication « pourquoi », demande mixte, histoire et sujet différent. Cinq sous-cas de classement étaient en échec lors de la reproduction initiale,
puis réussissent après correction. Les autres protègent les usages voisins. Le type inconnu
et la provenance par titre restent explicitement conservés.

La campagne complète réussit **529 tests Python, trois ignorés**. Les 32 demandes
de référence existantes, leurs cas de réglage et leurs huit cas de vérification
ne sont pas réécrits pour s’adapter à la correction. Aucun modèle réel n’est lancé.

Le Kiwix épinglé réel réussit **43 contrôles** sur cinq archives générées,
**283 708 octets**. Huit contrôles ajoutés mélangent des guides généraux locaux
et de vrais résultats natifs vélo/solaire ; la tâche nommée arrive en premier
avec Toute la bibliothèque et Résilience, et le guide général reste retrouvé.
Les archives et conteneurs temporaires sont supprimés après l’essai.

CI Windows/Linux, navigateurs et audit du paquet : à compléter après exécution.
Les résultats sur les vrais documents de Marc restent à mesurer ; les fixtures
ne prédisent ni leur ordre final ni la qualité pratique de leur contenu.

## Livraison et suite

**0.13.1** est une correction compatible de classement, d’où l’incrément du
correctif. Aucun changement de schéma, d’image, de cache, de lecture ou d’interface.
Les versions des fichiers Web inchangés restent celles de leur dernière modification.
La version affichée continue de provenir de l’API. Les index et caches documentaires
existants restent utilisables ; le classement s’applique aux réponses relues.

Le prochain R2 doit comparer notamment vélo, solaire, semences et leurs variantes,
puis ouvrir les résultats prioritaires. Les rapports réels et avis humains restent
nécessaires pour clore l’objectif de fiabilité. Les chantiers parallèles proposés
sont décrits dans les [prompts coordonnés](../decisions/prompts-agents-videos-et-performances.md) ;
ils ne modifient pas ce moteur et ne sont pas déclarés réalisés.
