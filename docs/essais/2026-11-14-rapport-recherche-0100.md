# Rapport réel de recherche 0.10.0

**Bilan de réception et reproduction — 14 novembre 2026.** Louis transmet le
contrôle complet créé à 20:05:25 UTC. Le JSON brut reste dans sa pièce jointe
privée. Suite des [rapports 0.9.3](2026-11-14-rapports-recherche-093.md), avec la
même référence de 32 demandes `2026-11-14.1`. Aucun avis humain n’est enregistré.

## Comparaison mesurée

| Mesure | 0.9.3 | 0.10.0 |
| --- | --- | --- |
| Recherches complètes / partielles | 1 / 31 | 1 / 31 |
| Délai médian | 6 368,5 ms | 12 331 ms |
| Délai maximal | 10 266 ms | 12 663 ms |
| Demandes sans interrogation plein texte terminée | 6 | 0 |
| Échéance globale atteinte | 31 | 12 |
| Reformulations tentées au total | 0 | 4 |

Le feu retrouve les techniques de production dans Wikilivres/Wikipédia. Le vélo
retrouve iFixit et des pages de maintenance Wikibooks, sans le modèle d’inventaire
et les exercices de prix précédents. Les titres ne certifient pas une procédure
utile ; eau stockée/chauffe-eau et affûtage/dictionnaire restent notamment à relire.
La radio ne trouve aucun résultat dans cette recherche partielle ; le cas négatif
de propulsion n’en trouve aucun non plus. Ces deux absences ont un sens différent.

Les 31 demandes générales consomment chacune le budget de 32 appels. Des archives
TED renvoient systématiquement HTTP 400, tandis que des lots importants expirent
vers trois secondes. Au moins 43 archives restent non interrogées dans presque
toutes ces demandes. Le délai plus long n’est pas un succès de performance :
la phase passée de six à douze secondes en 0.9.4 n’a pas suffi. Les passages
successifs sur le feu/générateur sont plus rapides, mais sans état des caches
ni charge du PC on ne les qualifie pas de mesures indépendantes à froid.

## Index et services

Kiwix répond en 80 ms, le catalogue en direct de 135 collections en 74 ms.
Les 102 guides restent prêts. R1 demeure terminé sans erreur : 134 index natifs,
un index local de 120 articles ; aucun index local périmé ou illisible signalé.
Cela confirme la présence des index, pas leur utilisabilité par toute API.

## Refus multilingue reproduit

Un service Kiwix 3.8.1 épinglé et cinq archives minuscules générées montrent :
une archive `Language=fra,eng` ou une longue liste de langues renvoie HTTP 400,
même seule, avec les sélecteurs nom, UUID ou contenu. Les paramètres `lang`,
`userlang` et `language` ne corrigent pas ce cas. Une archive à langue unique,
y compris le code `mul` seul, reste interrogeable. L’index est pourtant présent
et la recherche libzim directe retrouve l’article dans les cinq archives.

Cette reproduction correspond à la règle du
[serveur Kiwix](https://github.com/kiwix/libkiwix/blob/main/src/server/internalServer.cpp)
qui refuse une sélection contenant plusieurs langues. Elle n’inspecte pas les
fichiers TED réels de Marc : leur métadonnée exacte reste à enregistrer, sans
déduire une incompatibilité du seul nom contenant `mul`.

## Suite et demande de diagnostic

Louis autorise un contrôle plus bavard à lancer sur le PC de Marc. Les prochaines
preuves doivent distinguer index natif présent, compatible Kiwix et complément
local disponible ; consigner les appels, leurs collections, langue, formulation,
délais, résultat et limite atteinte. Les informations de diagnostic détaillé ne
doivent pas remplir le contexte ordinaire de l’assistant.

Le [journal depuis 0.2.0](journal-recherche-depuis-020.md) conserve cette réouverture
du travail : objectif non validé, erreurs reproductibles et prochaine mesure réelle.

**Suite livrée :** la [correction 0.11.1](2026-11-14-index-multilingues-et-diagnostic.md)
prépare les compléments multilingues et enrichit le rapport existant. La CI est
réussie ; l’amélioration des délais et du fonds réel n’est pas encore mesurée.
