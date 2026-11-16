# Intégration des corrections reproduites sous Windows

**Bilan daté — 0.32.1, 16 novembre 2026.** La branche fournie
`codex/campagne-windows-20261116`, tête `802232c`, est fusionnée normalement sur
0.32.0. Version patch : corrections compatibles du contrôleur et de la remise
en service après mise à jour ; aucun nouveau modèle ou composant tiers.

Le [bilan de l’autre agent sur le Windows de Marc](2026-11-16-campagne-windows-marc.md)
porte ses conditions, ses preuves et ses limites. L’agent principal consulte ces
résultats mais ne dispose pas ici d’une nouvelle connexion à ce PC ni de ses
rapports bruts. Aucune action sur l’installation active n’est déclenchée par
l’intégration dans Git.

## Corrections conservées

Les routeurs déjà créés avant la surcharge de droits Windows pouvaient conserver
leur configuration après une mise à jour. Le redémarrage logiciel demande
maintenant à Compose de remettre les trois seuls routeurs en conformité quand un
graphe préparé existe. Aucun graphe reconstruit, téléchargement ou changement de
Linux ; montages en lecture seule et ports inchangés. L’échec d’un routeur optionnel
reste signalé et n’annule pas le portail. Le mode jeu n’est pas levé.

Le contrôleur répond aux refus POST Windows après drainage d’un corps petit
(1 024 octets maximum, 250 ms maximum). Les jetons contenant un octet hors ASCII
sont comparés comme octets et refusés par HTTP 401, sans exception de comparaison.
Les routes et droits ne sont pas élargis. Les tests n’affichent aucun jeton réel.

Les essais isolent aussi le cache de concurrence Kiwix, alignent PowerShell sur
les lanceurs réels et attendent la libération des verrous Windows après fin des
processus de test. La contention pendant leur vie reste testée. Les moteurs de
recherche et les contrôles de traduction ne sont pas modifiés par ce correctif.

## Qualification et limites

Les scénarios ciblés, le CI complet et le paquet sont consignés après exécution.
Les observations actives chez Marc concernent 0.30.0 et les scénarios dédiés
0.31.0 : elles ne constituent pas une recette complète de la 0.32.1. Le seul
support externe de la campagne ne permettait pas de sauvegarder les 752 Go de
ZIM ; la restauration physique complète hors ligne reste un prochain objectif,
pas une réussite déduite du transfert de fixtures.

## Vérifications ciblées du candidat

Les **46 tests ciblés** contrôleur, mise à jour, coupure, concurrence Kiwix et
transfert Windows passent sur le runner, dont **2 ignorés** car réservés au
Windows natif : contrôleur 11 (6,473 s), mise à jour 16 (2,830 s), coupure 13
(1,635 s), concurrence 4 (0,201 s), transfert Windows 2 ignorés. Le CI Windows
reste la référence d’exécution de ces deux derniers scénarios. Le correctif ne
modifie ni JavaScript ni rendu ; la campagne navigateur CI vérifie la conservation
de l’interface complète.

## Validation d’intégration

Les **huit jobs CI** du code `e2f3e1d03f1a707e3d8bcdefc0b4170f57851586`
réussissent : [exécution 43919149637](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43919149637).
La suite Linux compte **906 tests en 56,668 s, 6 ignorés**. Le job Windows,
les lecteurs isolés, la recherche Kiwix, les routeurs et le navigateur sont réussis.
Aucun redémarrage ni déploiement chez Marc n’est exécuté par l’agent principal.
