# Apport des éditions de Wikipédia sur Bazzite

**Bilan du 24 novembre 2026.** Laboratoire Bazzite, catalogue Kiwix de
205 ZIM et portail 0.114.0. Le [comparatif du 23 novembre](2026-11-23-audit-qualite-recherche-bazzite.md#apport-marginal-des-grosses-collections)
mesurait déjà le retrait temporaire des éditions anglaises. Ce nouveau
relevé vérifie ce que chaque Wikipédia peut apporter à la lecture et ce
que le portail fait remonter avec le fonds complet.

| Édition installée | Taille du fichier |
| --- | ---: |
| Français Maxi, mai 2026 | 55,44 Go |
| Anglais Maxi, août 2026 | 127,42 Go |
| Simple English Maxi, septembre 2026 | 3,12 Go |

## Méthode

Quinze besoins choisis pour couvrir trois usages, sur la base des
[besoins de Marc](../bibliotheque/savoirs-durables.md). Pour chaque besoin,
interroger séparément les trois ZIM par `/search` avec `books.name` égal au
nom du fichier sans `.zim`, `format=xml`, `pageLength=5` et la formulation
de la colonne correspondante. Tester ensuite l'accès au titre connu via
`/content/<archive>/<titre>`, relever le sommaire et lire les passages
pertinents. Une page ouverte par son titre peut avoir été absente des
cinq résultats. Les titres essayés qui donnent 404 ne prouvent pas
l’absence d'un article équivalent sous un autre titre.

Dans le portail, envoyer la formulation française sans filtre de langue
à `/api/search` avec `kind=documents`, `limit=5` et le domaine
`resilience` pour les cas pratiques et techniques, `culture` pour les
savoirs. Comparer les cinq premiers résultats et vérifier des passages
des guides repérés. La requête Kiwix anglaise emploie le vocabulaire
anglais du domaine. Ce test mesure l'accès lorsqu'on connaît ce
vocabulaire, avec des formulations qui n'ont pas toujours la même
précision d'une langue à l'autre. Sur les 45 recherches ciblées, deux
appels au texte intégral de Maxi EN ont atteint le délai de 12 secondes,
pour « vapor barrier » et « T budding ».

Les appels sont séquentiels et limités aux services déjà ouverts. Le
catalogue et le stockage du laboratoire sont conservés. Aucun modèle
n'a été lancé.

## Recherches et lecture des archives

| Usage | Formulation française | Formulation anglaise | Comparaison des pages ouvertes |
| --- | --- | --- | --- |
| Pratique | réparer une crevaison de vélo | bicycle puncture repair | « Crevaison » en FR et « Flat tire » en EN expliquent le problème et évoquent la réparation. L'article anglais a une section vélo. |
| Pratique | conserver les graines du potager | seed saving | « Seed saving » traite la sélection et la pollinisation. Le FR a une page d’homonymie « Semence » et une page « Semence (agriculture) » plus générale. |
| Pratique | comment faire du compost | how to make compost | « Compostage (biologie) » arrive en tête dans le ZIM FR et traite les matières, l'aération et la maturation. « Compost » existe dans les deux éditions anglaises, y compris avec une courte section pratique dans Simple. |
| Pratique | recoudre un vêtement troué | mending clothes | « Darning », atteint avec le titre, décrit le reprisage et montre plusieurs exemples. La requête anglaise retrouve aussi « Visible mending ». |
| Pratique | protéger les réserves des rongeurs | rodent proof food storage | Aucun mode d'emploi repéré dans les cinq résultats de chaque Wikipédia. |
| Pratique | installer un séchoir solaire pour fruits | solar food drying | « Solar dryer » arrive en tête de Maxi EN. Il distingue les séchoirs directs et indirects, avec un schéma de principe. Le FR ouvre « Séchoir », plus général. |
| Savoirs | photosynthèse | photosynthesis | Article exact en tête dans les trois éditions. Le FR a une vue générale, des schémas et des sections détaillées. |
| Savoirs | théorème de Pythagore | Pythagorean theorem | Article exact en tête dans les trois éditions. Le FR couvre les énoncés, les applications et l'arpentage. Les deux éditions anglaises donnent plusieurs démonstrations. |
| Savoirs | pourquoi y a-t-il des saisons | what causes seasons | « Saison » et « Season » expliquent les mécanismes à partir de leur titre. La question longue classe d'autres articles en tête de chaque ZIM. |
| Savoirs | traité de Waitangi | Treaty of Waitangi | Les trois éditions ouvrent l'article. Le FR contient déjà le texte et l'interprétation du traité. Maxi EN détaille davantage les signatures, l'interprétation et les conséquences. Simple EN classe l'article exact premier. |
| Technique | bélier hydraulique | hydraulic ram | Article exact premier en FR et en EN Maxi. Le FR explique le principe. Maxi EN développe le rendement, le dimensionnement de la conduite et les problèmes de fonctionnement. |
| Technique | poêle à bois de masse rocket | rocket mass heater | Article exact premier dans le FR et le Maxi EN. L'anglais distingue davantage les configurations et détaille les composants. |
| Technique | cloison à étanchéité à l'air frein vapeur | vapor barrier | « Pare-vapeur » arrive en tête en FR et couvre condensation, matériaux et caractéristiques. |
| Technique | greffe en écusson | T budding | « Greffe en écusson » arrive en tête en FR, avec préparation, mode opératoire et périodes. « Shield budding » est accessible par son titre dans Maxi EN. |
| Technique | diode de roue libre | flyback diode | « Flyback diode » arrive en tête de Maxi EN, avec des schémas, du dimensionnement et des applications. Le FR remonte notamment « Diode » et « Relais électromécanique ». |

## Ce qui remonte dans le portail

Sur 15 requêtes, le pilote signale **5 recherches complètes et 10
partielles**. Six n'ont fourni aucun résultat. Les six requêtes pratiques
et les cinq techniques n'ont fait remonter aucune édition de Wikipédia
dans les cinq premiers résultats. Sur l'ensemble du lot, Maxi EN
apparaît dans les cinq premiers résultats une seule fois, hors sujet.
La requête sur le séchoir a été rejouée après une réponse HTTP 502.
Le statut des recherches partielles limite l'interprétation des absences.

- Pour la crevaison, iFixit FR arrive en tête avec un tutoriel de pose de
  rustine. Pour le compost, Wikilivres et un guide Appropedia en français
  arrivent en tête. Pour les semences, le seul résultat de la recherche
  partielle est le PDF « Produire des semences potagères bio », page 20.
- Vikidia arrive en tête sur « photosynthèse » et « théorème de
  Pythagore ». L'article Wikipédia FR « Photosynthèse » est deuxième.
- En recherche ciblée, les deux Maxi ouvrent un article sur les saisons.
  Dans le portail, le premier résultat Maxi EN pour « pourquoi y a-t-il
  des saisons » est un article sur un album. Le deuxième résultat
  ouvre bien « Saison » dans Wikipédia FR. L'archive peut contenir
  l'explication attendue sans que la recherche la classe correctement.
- Le bélier hydraulique fait remonter Low-tech Magazine et Appropedia.
  Un résultat sur l'histoire des réseaux hydrauliques et la description
  de l'Hydrautomat couvrent d'autres aspects que l'article Maxi EN sur
  le fonctionnement du bélier.
- Pour les rongeurs, le raccommodage et le séchoir solaire, ces
  formulations n'ont fourni aucun résultat dans le portail. Le
  raccommodage et le séchoir ont néanmoins une référence dans Maxi EN
  par recherche dans l'archive ou ouverture de l'article. La greffe en
  écusson illustre le même écart côté français : article exact en tête
  dans Kiwix, aucun résultat dans la recherche partielle du portail.

## Recommandation pour le kit de base

Le 24 novembre, Louis privilégie Wikipédia FR avec le fonds existant
et demande que l’installation ne télécharge aucune édition anglaise.

La 0.113.3 applique ce choix à l’installation en ligne sur Windows et Linux,
y compris à une sélection préparée avec un fichier de tri importé.

**Garder Wikipédia FR et proposer Maxi EN en option.** Le français
documente les bases de science et de culture, fournit des illustrations
et peut expliquer des gestes comme la greffe en écusson. Pour les
procédures, donner la priorité aux guides du fonds. Le relevé de la
veille confirme que les cinq premiers résultats sont restés identiques
sur **16 requêtes pratiques** quand seul Maxi EN a été retiré.

Maxi EN a une valeur en consultation ciblée sur des sujets techniques
comme le diagnostic d'un bélier hydraulique et les schémas de diode de
roue libre. Simple English à 3,12 Go est un complément de culture
générale en anglais. Il ne retrouve pas un équivalent de ces deux
articles dans les essais. Un kit resserré peut économiser **127,42 Go**
en omettant Maxi EN si Simple est déjà compris, ou **124,30 Go** en
choisissant Simple à sa place. L'export d'un nouveau kit réduit dispose déjà
de l'option `export-lab --no-english-wikipedia`. Elle laisse passer le fichier
`wikipedia_en-simple_…` s'il est présent. Le rafraîchissement des contenus
d'un kit suit [ses règles propres](../installation/preparer-kit-hors-ligne.md#sous-commandes-de-pilot_kitpy).

Pour une demande de couverture technique
en anglais, Kiwix propose aussi Nopic, qui garde les articles complets
sans les images. Le comparatif du 23 novembre a relevé **52,69 Go** pour
l'édition Nopic de juin 2026. Cette variante n'a pas été testée dans le
laboratoire. [Formats Kiwix](https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/)
