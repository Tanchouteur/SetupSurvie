# Index multilingues et rapport de recherche détaillé

**Bilan daté — correction compatible 0.11.1, 14 novembre 2026.** Répond au
[rapport réel 0.10.0](2026-11-14-rapport-recherche-0100.md) et à la demande d’un
contrôle plus bavard. La base reprend les cartes 0.11.0 intégrées sur main,
avec leurs routes, leur cache d’ombrage et leurs formats de trajets.

## Cause reproduite et correction

Une archive peut contenir un index natif tout en ayant plusieurs langues déclarées.
Le Kiwix épinglé refuse alors sa recherche, même isolée. Le nombre « 135/135
archives examinées » ne prouvait donc pas que les 134 index natifs étaient tous
utilisables par cette API. Ce résultat reproduit une cause possible des refus TED
du rapport ; leurs métadonnées natives réelles restent à confirmer.

L’outil d’indexation enregistre désormais présence de l’index, langues et
`kiwix_language_compatible`. Il construit un complément SQLite lorsque les langues
sont multiples ou absentes, sans dupliquer les archives natives compatibles.
Une seule métadonnée `mul` reste compatible ; aucun choix ne dépend du nom TED
ou de la présence de `mul` dans le nom du fichier. Les originaux sont intacts.

La recherche évite les appels natifs impossibles selon ces métadonnées et signale
les compléments à préparer. Un complément terminé est interrogé localement, même
si l’archive possède aussi un index natif. Les anciennes données SQLite et leur
format restent conservés ; les compléments inchangés sont réutilisés. Une copie
locale forcée ne remplace pas la recherche native d’une archive compatible.
La mise à jour n’extrait pas spontanément les archives déjà examinées : il faut
relancer **Créer ou reprendre les index**, comme l’explique le
[guide actuel](../utilisation/indexation-archives.md).

## Diagnostic demandé depuis le site

Le contrôle existant demande `diagnostic=true` à l’API de recherche. Son rapport
inclut au maximum quarante événements par demande : étape, collections/langues,
formulation, délai client incluant l’attente, cache, nombre de résultats, taille
de réponse et erreur catégorielle. Les archives nécessitant un complément restent
distinctes d’une erreur HTTP ou d’une absence de résultat.

Ces détails sont absents de la recherche ordinaire et des outils de l’assistant.
Aucun corps d’erreur brut, conversation, chemin privé ou commande d’inférence n’est
ajouté. Ce journal ne mesure ni le CPU du serveur ni un temps interne Kiwix ; il
ne faut pas attribuer un délai au disque ou au processeur sans autre mesure.
Les plafonds de douze secondes, 32 appels et deux voies plein texte/deux titres
ne sont pas augmentés à nouveau.

## Vérifications et limites

La suite locale sur la base intégrant les cartes termine **508 tests, dont trois
ignorés sous Linux**, sans échec. Les régressions couvrent 14 archives multilingues
et 100 compatibles sans gaspiller leur budget, les traces opt-in, les erreurs
au-delà du résumé court, le complément d’un vrai ZIM indexé et sa réutilisation.
Le lecteur isolé Windows doit aussi préparer un complément multilingue et garder
ses deux SQLite inchangées au second lancement. Le Kiwix réel synthétique vérifie
le refus HTTP 400 d’une archive seule puis sa recherche locale restaurée.
Le contrôle Chromium via le MCP réussit 49 assertions ; le Kiwix épinglé
réussit 35 contrôles sur cinq archives générées de 283 260 octets au total.
La [CI sur `1836d63`](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43639780417)
réussit ses huit tâches : Linux, Windows, lecteurs isolés Windows Python
3.11/3.13/3.14, Kiwix réel synthétique, OSRM synthétique et navigateurs. Les
deux navigateurs Chromium et WebKit réussissent chacun 49 vérifications de
recherche, 18 de ses outils et 32 de la recette d’usage. Les contrôles des
cartes intégrées restent dans cette même CI. Ce ne sont pas des mesures du PC
de Marc ni un essai sur iPhone physique.

**0.11.1** corrige l’utilisation des index et complète un rapport existant, sans
nouvel écran, image tierce, modèle ou migration de schéma. La pertinence réelle,
les délais et les métadonnées des archives de Marc restent à mesurer après
préparation des compléments. Le prompt de refonte des paramètres est une consigne
pour un autre chantier, pas une refonte déclarée livrée par cette correction.
