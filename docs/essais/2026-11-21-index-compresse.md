# Index de classement compressé — 21 novembre 2026

**Bilan daté, version 0.88.0, PC Windows de Marc (SSD E:).** Un téléchargement
de 351 Go tournait en même temps : les durées sont un peu bruitées ; les
comparaisons de résultats, elles, sont exactes.

## Constat de départ

Le classement du fonds principal (`state/pilot/category-index`) pesait 252 Go
chez Marc pour environ 650 Go d’archives. Chaque passage d’environ 2 400
caractères y était stocké en clair dans la table FTS5, en plus de son index.

## Choix de la variante

Quatre variantes ont été reconstruites à partir des mêmes lignes de trois index
réels, puis interrogées avec les 136 questions de la liste de thèmes de Marc
(`tests/fixtures/domain-evaluation/besoins-marc-2026-11-21.json`), converties par
le code du pilote en version stricte et élargie (272 recherches par archive),
avec le filtre de domaine de la production :

| Variante | Taille | p95 | Résultats identiques |
|---|---|---|---|
| Texte compressé (zlib, contenu externe) | −37 à −45 % | 30 à 40 % plus rapide | 100 % (16 066 résultats) |
| Sans texte, relu dans le ZIM | −66 à −71 % | 5 à 15 fois plus lent | textes différents dans 73 à 90 % des cas |
| `detail=column` | −14 % | 1,7 à 3 fois plus lent | 100 %, mais aucune expression testée |

Contrôle de la mesure : l’index de production et sa reconstruction donnent
100 % de résultats identiques. La variante compressée est retenue.

## Vérification du code livré

Le script de vérification copie un index réel, lance `archive_index.search` du
code 0.88.0, convertit la copie avec `archive_index.compress`, puis relance les
mêmes recherches. Il y a 1 088 recherches par archive : 272 requêtes × 2 espaces
× 2 langues (toutes, français). La comparaison porte sur les résultats complets :
identifiant, titre, langue, extrait, 4 000 premiers caractères, domaines, rang
et couverture.

| Archive | Avant | Après | Conversion | p50 avant → après | p95 avant → après | Identiques |
|---|---|---|---|---|---|---|
| Wikibooks FR | 435 Mo | 242 Mo (−44 %) | 13 s | 3,5 → 3,9 ms | 54 → 35 ms | 1 088 / 1 088 |
| iFixit FR | 958 Mo | 603 Mo (−37 %) | 32 s | 2,3 → 2,9 ms | 1 540 → 1 615 ms | 1 088 / 1 088 |
| Wikipédia simple EN | 1 907 Mo | 1 139 Mo (−40 %) | 76 s | 1,3 → 1,2 ms | 87 → 58 ms | 1 088 / 1 088 |

Pour iFixit en français, 26 recherches atteignent le délai de 3 s, avant comme
après. Le filtre de langue d’iFixit relit le texte de chaque candidat : c’est
déjà le cas avec l’ancien format, et la conversion ne l’améliore pas.

## Limites

- Les 272 recherches ne contiennent pas d’expression de plusieurs mots. Le format
  compressé garde un index de recherche strictement identique, positions comprises :
  les expressions ne sont donc pas concernées.
- Le gain sur Wikipédia FR et EN (la majorité des 252 Go) est extrapolé, environ
  100 Go ; il sera mesuré par la conversion réelle.
- La conversion demande environ 70 % de la taille de l’index en place temporaire.
  Wikipédia anglais (131 Go) en demande donc environ 90 Go.
- Les tests unitaires couvrent la conversion, la pause, le manque de place,
  l’index republié pendant la conversion et la construction réelle avec libzim.
  Le parcours complet depuis le portail reste à observer chez Marc.

Guide de référence : [Rendre les archives recherchables](../utilisation/indexation-archives.md#index-compressés-depuis-0880).
