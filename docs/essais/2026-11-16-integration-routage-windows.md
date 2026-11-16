# Intégration du correctif d’itinéraires Windows

**Bilan daté — 16 novembre 2026, 0.28.1.** Branche fournie par un autre agent :
`codex/windows-osrm-routing`, code `e855b5b`, version proposée `fd927b9` en 0.27.1.
Son [CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43878266143) réussit.
Louis demande son intégration sur main après la livraison de lecture 0.28.0.

Les graphes Windows sont préparés avec UID/GID Linux 1000:1000. Les services
OSRM utilisaient l’utilisateur par défaut de l’image ; certains fichiers
limités à leur propriétaire n’étaient alors pas lisibles. L’override Windows
applique 1000:1000 aux trois routeurs seulement lorsque le graphe préparé est
présent. Les montages restent en lecture seule, sans publication de port ni
changement des images ou de la configuration Linux.

La revue conserve les deux commits et leur histoire, par fusion normale.
API/release/README sont réconciliés en **0.28.1**, correction compatible après
0.28.0 ; la version ne redescend pas vers la proposition 0.27.1. Les tests
Compose contrôlent configuration avec/sans graphe, utilisateur Windows et
absence de cet override Linux, ainsi que ports, capacités et montages.
Les tests ciblés installation/transfert/routage sont exécutés localement ;
le CI de l’ensemble suit. Aucun redémarrage client ni nouvelle préparation
de cartes n’est lancé par l’agent. Les permissions réelles du disque Windows de
Marc restent à contrôler après mise à jour et recréation de ses services.

Guide actuel : [points et itinéraires](../utilisation/points-et-itineraires.md).

## Validation d’intégration

Les **huit jobs CI** de `1d1696494be0257b975a2be6042a8e9c6d179547`
réussissent : [exécution 43880285891](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43880285891).
Les **43 tests locaux ciblés** réussissent en 7,442 s. Le routage Windows réel
chez Marc et son redémarrage restent à vérifier ; aucune intervention sur son
installation n’est exécutée ici.
