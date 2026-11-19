# Mesurer le classement des espaces documentaires

**Protocole actuel et bilan Bazzite du 19 novembre 2026 — candidat 0.57.0.**
Louis demande d'établir une mesure avant d'améliorer le classement, d'examiner
les catégories des encyclopédies et d'inclure les vidéos dans la recette. Le
[guide des classements](../utilisation/classement-et-collections.md) décrit
les corrections accessibles aux lecteurs.

## Préparer la référence

Constituer un lot de réglage (`tune`) et un lot réservé à la vérification
(`verify`). Choisir des sujets pratiques, des contenus de culture générale,
des documents mixtes et des titres ambigus. Pour Marc, échantillonner aussi
les guides, plusieurs encyclopédies et les vidéos locales et en ZIM. Inclure
des sujets pratiques et culturels dans chaque famille quand le fonds le permet.
Lire ou regarder chaque source avant de saisir les espaces attendus et le motif.
Consigner les cas incertains en dehors du score jusqu'à relecture. Deux
personnes peuvent annoter le même lot séparément et résoudre leurs désaccords
avant de regarder les résultats.

L'espace **Autonomie et résilience** couvre les méthodes et moyens utiles à
l'autonomie, y compris une explication technique qui aide à les comprendre.
**Savoirs et culture** couvre notamment les sciences générales, l'histoire,
les arts et l'enseignement. Une source peut répondre aux deux usages si elle
consacre une partie substantielle à chacun. Une mention suffit à motiver une
recherche par mot, mais le classement d'espace dépend du sujet traité.

Dans le [dossier des références](../../tests/fixtures/domain-evaluation/),
chaque cas indique une requête, le type de recherche, les espaces attendus
et le motif. Une source est identifiée par le chemin exact et la collection
ZIM, ou par `source_id` pour un guide, un article ou une vidéo. Pour une
vidéo connue par son titre, `title_prefix` permet de la retrouver dans une
installation dont les identifiants diffèrent. `kind: videos` avec
`dedicated: true` contrôle que la vidéo est trouvée dans la recherche dédiée
depuis chacun des deux espaces. Ajouter des cas `kind: all` distincts sur le
même sujet pour vérifier la recherche mixte, qui applique le filtre d'espace
aussi aux vidéos.

## Capturer, mesurer et comparer

Exécuter depuis la racine du dépôt, avec Python 3.10 ou plus. Les adresses de
l'exemple sont les ports locaux par défaut. Choisir un dossier privé, car la
capture contient les extraits de la bibliothèque et les références des résultats.

```sh
mesure=$(mktemp -d)
python3 scripts/evaluate_domains.py capture tests/fixtures/domain-evaluation/bazzite-v1.json "$mesure"/capture.json --portal http://127.0.0.1:8080 --check-filters
python3 scripts/evaluate_domains.py score "$mesure"/capture.json "$mesure"/avant.json --legacy
python3 scripts/evaluate_domains.py score "$mesure"/capture.json "$mesure"/apres.json --kiwix http://127.0.0.1:8081
python3 scripts/evaluate_domains.py compare "$mesure"/avant.json "$mesure"/apres.json "$mesure"/comparaison.json
```

Le premier appel capture les résultats publics du portail et leur position
parmi les résultats rendus. Si la recherche manque un article de référence,
il tente une lecture directe et indique l'absence de position. Un cas absent de
la recherche peut ainsi mesurer le classement automatique tout en restant un
échec de repérage. Les deux scores utilisent la même capture, identifiée par
son SHA-256. Rejouer les scores avec les mêmes éditions ZIM. Le score évalue
la règle automatique même si une correction humaine est présente, et signale
celle-ci dans le rapport. Dans le portail, la correction à jour reste prioritaire.

Le rapport donne les effectifs, les décisions exactes, les faux positifs, les
faux négatifs, la précision et le rappel par espace, ainsi que les cas qui
changent. Un bon classement exact doit reproduire l’ensemble des espaces
attendus. Le rappel mesure combien d’appartenances attendues sont retrouvées,
la précision combien des appartenances proposées sont attendues. Les sources
absentes ou illisibles figurent dans les effectifs demandés et sont exclues du
dénominateur des scores. Les résultats manquants et la couverture de recherche
restent à examiner avant de conclure.

`compare` réussit si le nombre de classements exacts monte sur le lot réservé
et si aucun de ces cas ne perd un espace attendu qu'il avait avec l'ancienne
règle. C'est un critère de décision pour ce protocole, à compléter par les
mesures de recherche réelle. Avec `--check-filters`, capturer une fois par
version de portail sur le même fonds. Le rapport de capture contient le rang
et la couverture de chaque requête. Comparer la visibilité, les pertes
attendues par filtre, les vidéos dédiées et les délais avec
`python3 scripts/evaluate_domains.py compare-live capture-ancienne.json capture-nouvelle.json comparaison-filtres.json`.
Refaire avec des caches comparables et noter le matériel, les éditions et les
recherches partielles. Le score à partir de
la capture lit directement la structure des articles de référence. La
recherche réelle prélève seulement certains candidats dans un temps borné.

Si la vérification sur un nouveau fonds montre une perte pratique ou un coût
inacceptable, conserver le rapport et reproduire les cas avant publication.
L'ancienne règle reste disponible dans le code pour le rejeu et peut être
réactivée dans une livraison corrective sans migration des données. La
[procédure de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)
décrit la sauvegarde et la récupération de la version précédente.

## Bilan sur Bazzite

Le portail en service en 0.52.2 a fourni les candidats et Kiwix les pages
locales. La règle de référence a été exécutée à partir du dépôt **0.55.2**
avant la modification, puis vérifiée avec `--legacy`. Les références
par lot ont été annotées à partir du contenu disponible. Les scores utilisent
les mêmes candidats et les mêmes éditions dans chaque comparaison.

| Lot | Sources | Trouvées par la recherche globale ou dédiée | Exact avant | Exact après |
| --- | ---: | ---: | ---: | ---: |
| Initial, 28 articles et 3 vidéos | 31 | 25 | 14 | 29 |
| Extension | 12 | 11 | 2 | 8 |
| Vérification intermédiaire | 10 | 9 | 4 | 8 |
| Premier lot indépendant, dont 3 témoins Vikidia | 27 | 26 | 11 | 19 |
| Confirmation indépendante | 24 | 23 | 11 | 16 |
| Total | 104 | 94 | 42 | 80 |

| Espace | Faux positifs avant → après | Faux négatifs avant → après | Précision avant → après | Rappel avant → après |
| --- | ---: | ---: | ---: | ---: |
| Autonomie et résilience | 26 → 9 | 17 → 3 | 60 % → 85 % | 70 % → 95 % |
| Savoirs et culture | 12 → 12 | 37 → 8 | 76 % → 85 % | 50 % → 89 % |

Le premier candidat, très bien noté sur les exemples déjà utilisés pour
régler les règles, échouait au test indépendant. Il passait de 10 à 12
classements exacts sur 24 nouvelles pages Wikipédia mais retirait **Autonomie
et résilience** à huit sources qui devaient le conserver. Le pilote conserve
désormais l'espace pratique si la structure est équivoque. Les trois témoins
Vikidia, qui utilisent encore la règle précédente, restent à 1 classement
exact sur 3.

Après cette reprise, la confirmation a porté sur **24 autres articles**,
12 en français et 12 en anglais simplifié. Les jugements et références
ont été figés avant calcul et la règle est restée la même après ce test.
Le gain est de **11 → 16 classements exacts**, sans perte d'un espace attendu
que l'ancienne règle retrouvait. Le rappel d'Autonomie et résilience reste à
9/12. Les articles sur les pannes électriques, les moteurs électriques et
l'hydroélectricité restent à retrouver dans cet espace. L'échantillon couvre
plusieurs sujets et deux éditions. Les scores décrivent uniquement les cas
annotés, sélectionnés pour la recette.

Les trois vidéos de Bazzite sont classées Savoirs et culture dans les deux
scores. Le portail en service les trouve en mode **Vidéos uniquement** depuis
chacun des deux espaces. Il s'agit de trois vidéos locales d'essai. Le PC de
Marc et ses résultats mixtes avec vidéos pratiques ou ZIM restent à mesurer.

### Métadonnées réellement disponibles

Le code sait lire les catégories d’article si le HTML local les porte, via
les liens Parsoid ou la liste de catégories visibles de MediaWiki.
Ce champ est distinct des catégories du catalogue Kiwix, communes à toute
l'archive. Parmi les 98 pages de Wikipédia français et anglais simplifié
testées, 90 avaient des titres de section et aucune n'exposait de catégorie
d'article dans les formats reconnus. Le gain observé provient du titre et
des sections. La lecture de catégories a été vérifiée avec des fixtures.
Voir la [spécification DOM de MediaWiki](https://www.mediawiki.org/wiki/Parsoid/MediaWiki_DOM_spec#Category_links).

En recherche, le diagnostic donne le nombre de candidats Wikipédia examinés
et le temps passé. Le pilote donne la priorité à un titre qui correspond
exactement à la requête, puis à la pertinence des autres candidats. Il
programme jusqu'à douze lectures, au plus deux à la fois pour le service, et
leur réserve 700 ms. Les pages qui ne sont pas lues dans ce délai, les autres collections,
les guides et les vidéos utilisent leur règle habituelle. Si les nouveaux
indices laissent le sujet incertain, le classement préserve les appartenances
déjà indiquées par les mots du titre et du texte. Les résultats
progressifs de Wikipédia peuvent changer à la fin de la recherche, quand
la structure a été lue. Un cache en mémoire réemploie temporairement les
indices pour la même édition.

### Recherche réelle

Le moteur des deux versions a interrogé les éditions Kiwix de Bazzite depuis
deux états de test isolés, avec 52 articles (lot initial et confirmation) et
trois filtres par article. Sur les 45 articles retrouvés en recherche globale,
la répartition exacte entre les filtres passe de **18 à 36**. Le moteur rend
48 appartenances attendues au lieu de 32, et 8 inattendues au lieu de 18.
Les deux moteurs trouvent les mêmes 45 articles en recherche globale.
Aucun cas auparavant trouvé dans son espace attendu n'a disparu.

Sur les 156 requêtes de chaque version, le délai médian passe de 43 à 62 ms
et le 95e percentile de 471 à 994 ms. Les mesures incluent le tunnel SSH et
mêlent les premiers appels aux répétitions. Elles ne prédisent pas la latence
chez Marc. Les services en place sur Bazzite ont continué à servir le fonds
pendant les essais.
