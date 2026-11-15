# Titres de tâches et ouverture des articles

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

La campagne complète réussit **531 tests Python, trois ignorés**. Les 32 demandes
de référence existantes, leurs cas de réglage et leurs huit cas de vérification
ne sont pas réécrits pour s’adapter à la correction. Aucun modèle réel n’est lancé.

Le Kiwix épinglé réel réussit **53 contrôles** sur cinq archives générées,
**285 477 octets**. Huit contrôles ajoutés mélangent des guides généraux locaux
et de vrais résultats natifs vélo/solaire ; la tâche nommée arrive en premier
avec Toute la bibliothèque et Résilience, et le guide général reste retrouvé.
Les archives et conteneurs temporaires sont supprimés après l’essai.

### Suggestions Kiwix et documents indisponibles

L’examen d’un identifiant du rapport réel contenant `&apos;` a motivé un essai
supplémentaire sur un ZIM généré de quelques dizaines de Ko. Le Kiwix 3.8.1
épinglé renvoie ses suggestions JSON avec un encodage HTML dans `path` :
`Compost_et_l&apos;urbanisme` pour l’entrée contenant une apostrophe et
`Compost &amp; jardin` pour l’entrée contenant une esperluette. Le plein texte
renvoie la référence correcte après lecture XML. Le portail gardait donc deux
identifiants différents pour le même article ; celui de la suggestion ne s’ouvrait pas.
La reproduction a lu les bons liens et échoué sur les deux mauvais, dans le même
service réel. Les accents simples fonctionnaient déjà.

La suggestion est maintenant décodée **une seule fois, avant** ses contrôles de
chemin. Le résultat est validé puis encodé pour construire l’URL locale ; plein
texte et titre se dédupliquent sur le même identifiant. On ne décode pas une
seconde fois les références XML ou les noms contenant littéralement `&amp;`.
Les réponses brutes déjà en cache bénéficient de cette correction à la lecture.
Les anciennes références fautives enregistrées ne sont pas réécrites : une nouvelle
recherche fournit le lien corrigé. Aucun changement d’archive ni réindexation complète.

Deux tests automatisés supplémentaires couvrent identités avec apostrophe,
esperluette, accent, entité littérale et refus des URLs distantes, traversées et
barres inverses après décodage. Dix contrôles natifs supplémentaires vérifient
quatre articles uniques et lisibles, à la fois dans une archive plein texte et
dans une archive avec titres seuls. La boucle ouvre réellement chaque source.
Le symptôme de Marc est compatible avec ce défaut ; faute de son URL exacte et
de recette sur son PC, sa cause historique n’est pas déclarée certaine.

CI Windows/Linux, navigateurs et audit du paquet : à compléter après exécution.
Les résultats sur les vrais documents de Marc restent à mesurer ; les fixtures
ne prédisent ni leur ordre final ni la qualité pratique de leur contenu.

## Livraison et suite

**0.13.1** est une correction compatible de classement, d’où l’incrément du
correctif. Aucun changement de schéma, d’image, de cache ou d’interface. La construction
des références d’articles est corrigée comme décrit ci-dessous.
Les versions des fichiers Web inchangés restent celles de leur dernière modification.
La version affichée continue de provenir de l’API. Les index et caches documentaires
existants restent utilisables ; le classement s’applique aux réponses relues.

Le prochain R2 doit comparer notamment vélo, solaire, semences et leurs variantes,
puis ouvrir les résultats prioritaires. Les rapports réels et avis humains restent
nécessaires pour clore l’objectif de fiabilité. Les deux chantiers parallèles lancés par Louis
sont décrits dans les [prompts coordonnés](../decisions/prompts-agents-videos-et-performances.md) ;
ils ne modifient pas ce moteur et ne sont pas déclarés réalisés.

## Ajustement du test avec cache disque actif

La première CI de la correction de liens a exposé une incohérence du nouveau
jeu de test : entre quatre sous-cas, il changeait la réponse simulée de la même
archive sans en changer l’édition. Sur le runner disposant de plus de 15 Go libres,
le cache disque conservait donc correctement la première réponse. Le test modèle
maintenant quatre éditions différentes avec un fichier source de taille changée ;
il conserve le vrai mécanisme d’invalidation, sans désactiver le cache. Les neuf
tests de protocole réussissent aussi avec réserve de test abaissée pour forcer
les écritures disque. Le code du produit ne change pas pour cet ajustement.
