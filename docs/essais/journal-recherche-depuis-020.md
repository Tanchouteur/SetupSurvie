# Journal de fiabilisation depuis la 0.2.0

**Suivi actuel — 14 novembre 2026.** Demandé par Louis pour préparer le résumé
final. Ce journal suit les livraisons, décisions, preuves et limites ; les bilans
liés conservent leurs détails et résultats historiques. Une ligne livrée ne
signifie pas que le fonctionnement sur tout le fonds de Marc a été validé.

## Livraisons et différences

Les commits ci-dessous introduisent la version ; leurs bilans donnent les
corrections et la CI finales de chaque lot. Toutes ces livraisons sont sur `main`.

| Version | Ce qui a été fait et pourquoi | Preuves et limites conservées |
| --- | --- | --- |
| 0.2.0 · `aead6b0f` | Point de départ : nouvelle interface en service et premier rapport de recherche réel | Le [bilan de départ et de 0.3.0](2026-11-14-recherche-index-et-espaces.md) distingue les résultats réels des petites fixtures |
| 0.3.0 · `064a44f1` | Index ZIM complémentaire manuel et reprenable, recherche partagée, titres réservés, classement pratique, deux espaces, contexte réglable | CI Windows/Linux et navigateurs ; le fonds de Marc n’est pas répliqué ni indexé dans le runner |
| 0.4.0 · `bffc3956` | File d’indexation après installation/téléchargement, pause/créneau nocturne, diagnostic Kiwix/catalogue et index réels | [Bilan](2026-11-14-indexation-automatique-et-diagnostic.md), 399 tests et CI ; validation réelle initialement attendue |
| 0.5.0 · `1d6b40ef` | Référence de 32 demandes, avis humains exportables, vocabulaire FR/EN et lecture des redirections | [Bilan](2026-11-14-reference-recherche-et-lecture.md), 408 tests et CI ; une attente de test a été corrigée, sans prétendre expliquer une ancienne capture sans URL |
| 0.6.0 · `db1f1778` | Domaines/type/examen corrigibles par document, noms et regroupements de collections modifiables, ouverture directe conservée | [Bilan](2026-11-14-classement-et-collections.md), 420 tests et CI ; la relecture éditoriale du fonds reste humaine |
| 0.7.0 · `382cc85f` | Mesures des phases de réponse, budget de contexte, limite native du modèle, calibration mémoire volontaire et retour au réglage précédent | [Bilan](2026-11-14-mesures-assistant-et-contexte.md), 435 tests et CI ; aucun grand contexte recommandé sans mesure du PC cible |
| 0.8.0 · `6828201e` | Comparatif facultatif : moteur actuel, reformulation bilingue et reclassement local ; questions réservées et avis humains | [Bilan](2026-11-14-comparatif-recherche-ia.md), 447 tests et CI ; aide désactivée par défaut et gain réel non établi |
| 0.9.0 · `5dfce5dc` | Six dossiers pratiques avec objectifs, repères de sources, révision et lacunes visibles | [Bilan](2026-11-14-dossiers-pratiques.md), 459 tests et CI ; deux courses de chargement WebKit corrigées, sources réelles à qualifier |
| 0.9.1 · `3b73822d` | Corrections après rapports 0.8.0 : appels Kiwix partagés et bornés, cache court, erreurs détaillées, moins de replis sur un seul mot ; budget IA appliqué à toute la demande et arrêt après deux échecs | [Bilan](2026-11-14-corrections-rapports-recherche.md), 469 tests et CI ; ne prouve pas la correction de l’indexation réelle |
| 0.9.2 · `8427aad0` | Vérification du lecteur dans son Python isolé, causes d’erreur catégorielles, correction du pool Windows et d’une recherche déclenchée trois fois au chargement | [Bilan](2026-11-14-indexation-isolee.md), 478 tests et CI dont Python Windows 3.11 à 3.14 ; erreurs de fixture UTF-8/création ZIM distinguées du défaut de lancement réel reproduit |
| 0.9.3 · `faaa6f16` | Exclusions entre indexation, sauvegarde et mise à jour ; verrous par archive pour les processus restants ; conservation des verrous et des index au retour arrière | [Bilan](2026-11-14-index-sauvegarde-et-retour-arriere.md), 486 tests et CI ; un chemin temporaire Windows du test a été corrigé ; première mise à jour depuis une ancienne version à faire après pause effective |

Les nombres de tests incluent trois tests ignorés sous Linux ; les bilans
précisent les plateformes réellement essayées. Aucun de ces nombres ne mesure
la pertinence du fonds réel, la traduction d’un livre ou la tenue physique du disque.

## Retours réels et changements de priorité

La correction 0.9.4 est en préparation : priorité entre langues, reformulations
des collections pratiques, annulation des appels sans lecteur, filtrage des
correspondances et résumé des index dans les outils. Son
[bilan](2026-11-14-corrections-rapports-093.md) consigne les causes reproduites,
la piste booléenne écartée et les vérifications avant publication.

- Rapports 0.8.0 : recherches partielles, index non préparés, comparatif IA expiré,
  puis capture d’échec d’indexation. [Analyse datée](2026-11-14-rapports-recherche-080.md).
- Rapports 0.9.3 reçus ensuite : indexation terminée sans erreur, mais 31 recherches
  partielles sur 32 et nouveau comparatif IA interrompu. L’indexation manquante ne
  suffit plus à expliquer les résultats. [Analyse datée](2026-11-14-rapports-recherche-093.md).
- Une recette d’usage hors ligne R7 est préparée dans une branche de travail,
  **non livrée**. Les rapports réels 0.9.3 donnent priorité aux expirations et
  au classement du moteur commun. Son brouillon est conservé pour reprise.

## Décisions conservées ou reportées

Les deux espaces partagent un même fonds ; les archives directement ouvrables
et leurs index natifs sont conservés. L’index local complète les manques, sans
extraire systématiquement tout Wikipédia une seconde fois. Les réserves mémoire,
pause du moteur et reprise explicite restent appliquées.

L’aide IA reste expérimentale : les rapports reçus ne démontrent pas son intérêt
dans le budget choisi. Un nouvel index sémantique est reporté jusqu’à une base
comparative exploitable. Le contexte n’est pas porté au maximum théorique sans
mesure de stabilité et de réactivité.

La traduction de lecture, les sous-titres et les livres longs restent des lots
du [plan](../decisions/plan-ameliorations-marc.md), pas des fonctions déclarées
terminées par ce journal. Maison de Solliès-Ville et réorganisation générale des
réglages sont tracées pour plus tard dans la [boîte à idées](../decisions/boite-a-idees.md).

## Règle de mise à jour

Pour chaque suite : ajouter différence concrète, cause vérifiée ou hypothèse,
tests exécutés et non exécutés, choix retenu/reporté/abandonné et lien vers la
livraison. Le résumé final s’appuiera sur ces preuves et séparera développement,
déploiement chez Marc et validation humaine des documents.
