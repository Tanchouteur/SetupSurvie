# Audit de la qualité de recherche sur Bazzite

**Bilan du 23 novembre 2026.** Fonds complet Bazzite, portail du laboratoire
0.108.0 et correctifs candidats 0.108.1. Louis confirme avoir ajouté les
mêmes contenus chez Marc. Les mesures de ce bilan proviennent de Bazzite.
Les essais de pertinence sont faits sans inférence sur le service et les
archives déjà disponibles. Les exclusions comparatives existent dans le
processus jetable le temps du test.

## Inventaire et index

| Mesure | Résultat Bazzite |
| --- | --- |
| Fichiers ZIM présents et entrées du catalogue Kiwix | 205 de chaque, mêmes UUID |
| Taille des ZIM | 1 046,61 Go décimaux |
| Index natifs compatibles | 184 |
| Compléments SQLite | 21, dont 19 pour incompatibilité de langue et 2 pour absence d’index natif |
| Empreinte courante des index | 205 correspondances taille/date avec le manifeste, 21 `PRAGMA quick_check` réussis |
| Place des compléments SQLite | 151,55 Mo pour les fichiers d’index |
| Copies binaires | Aucun ZIM de même taille. Aucun SHA-256 identique parmi les PDF de même taille (118 PDF recensés). |

Les tailles différentes établissent l’absence de copies ZIM octet pour
octet. Le contrôle ne compare pas l’intégrité complète des 1 046,61 Go
avec leurs empreintes de téléchargement, ni le contenu de tous les articles.
Le catalogue et le manifeste prouvent la disponibilité du socle d’index.
La recherche dépend ensuite des périmètres, de la langue, des termes, des
candidats récupérés et de leur classement.

### Essai de l’index par espace

Le fonds courant ne disposait pas d’un index par espace publié. Une
construction isolée sur Ékopédia (ZIM 16,57 Mo) a indexé 2 528 articles
dans 21,57 Mo de SQLite compressé. Comparaison sur six requêtes en
restreignant au même ZIM.

- « Compost », « Eau », « Photosynthèse » et « Bibliothèque nationale de
  France » restent premiers sur leur requête respective.
- « Papier recyclé » passe de zéro résultat à « Papier », « Papier mâché »
  et « Liant papier » en tête. Cela établit un gain de rappel sur cette
  formulation, dont la pertinence exige d’ouvrir les résultats.
- « Couture » passe de « La couture », « Couture » à « Couture », « Réparer
  un pneu », « Production ». Le second réglage retrouve plus de candidats
  et laisse le bruit remonter, même sur cette petite collection.

L’index par espace peut aider sur des requêtes manquées. Le coût mesuré et
la précision observée plaident pour une qualification par collection avant
de dupliquer l’index de tout le fonds. Les ZIM de vidéos, PDF scannés et
portails de liens demandent des mesures propres à leur type de contenu.
Un index de titres ou de pages d’accueil ne rend pas automatiquement
cherchables les paroles, les images ou les manuels auxquels elles renvoient.

## Apport marginal des grosses collections

Les comparaisons gardent le même fonds et le même tri de base. Trois passes
utilisent successivement les deux Wikipédia anglais, Simple English seul,
puis aucun des deux. Un second lot retire séparément Survivor Library ou
Khan Academy FR. Le français et les autres collections restent disponibles
dans chaque passe. Le rapport relève les cinq premiers résultats et tente
d’ouvrir les deux premiers. Une ouverture réussie établit l’accès au texte,
et la relecture d’un échantillon sert à apprécier son apport.

### Wikipédia anglais

Sur **32 requêtes et 96 recherches**, les trois profils ont chacun 27
requêtes avec des résultats. Le profil complet et le profil Simple seul
ont chacun **54 ouvertures sur 54**. Le profil sans les deux archives a
**53 ouvertures sur 53**, faute de second résultat sur une requête.

- **Autonomie.** Les 16 requêtes pratiques gardent les mêmes cinq premiers
  identifiants en retirant Maxi. Les premiers résultats utiles viennent
  entre autres de l’OMS, iFixit, Appropedia et Low-tech Magazine. Certaines
  requêtes restent vides ou imprécises dans les trois profils.
- **Culture.** Sur « Howrah Bridge », Maxi fournit l’article éponyme de
  38 614 caractères extraits. Simple remonte « Howrah » puis « Cantilever
  bridge ». En supprimant les deux, les premiers résultats deviennent
  périphériques. Pour « Great Dividing Range », « Arabidopsis thaliana »
  et le traité de Waitangi, Simple fournit une première référence exacte.
  Maxi apporte un texte plus long sur ces mêmes sujets. Pour le traité
  de Tordesillas, les deux textes ouverts comptent environ 4 200 et 37 700
  caractères.
- **Illustrations et taille.** Maxi occupe 127,42 Go, soit 12,17 % des ZIM.
  Simple English occupe 3,12 Go. Le catalogue de téléchargement Kiwix
  indique 52,69 Go pour `wikipedia_en_all_nopic_2026-06.zim` et 14,39 Go
  pour `wikipedia_en_all_mini_2026-09.zim`. Nopic conserve le corps des
  articles sans images et économiserait 74,73 Go si elle remplaçait Maxi.
  Mini garde l’introduction et l’infobox. L’édition et les illustrations
  changent entre ces options, qui n’ont pas été comparées localement.
  [Formats Kiwix](https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/)

Maxi est justifié comme option encyclopédique illustrée et pour les sujets
pointus en anglais. Pour une configuration réduite centrée sur l’Autonomie,
les mesures soutiennent de conserver Wikipédia FR et Simple English en
priorité, puis de comparer Nopic à Maxi si la profondeur en anglais reste
requise. Aucune suppression ni modification du fonds de référence.

### Survivor Library, Khan Academy et les recouvrements

- **Survivor Library, 220,35 Go.** Sur les six requêtes d’artisanat et de
  jardin testées, la collection ne figure jamais dans les cinq premiers
  résultats du fonds. L’exclusion laisse ces listes identiques dans ce lot.
  Une recherche restreinte à Survivor Library retrouve « Wood Carving »
  sous une forme plus courte. La page de collection donne 19 liens PDF,
  et les deux premiers commencent par une signature PDF et répondent
  à une lecture partielle HTTP 206 dans le ZIM. Le bénéfice du fonds
  est vérifié en navigation ciblée sur ce cas. Son accès par recherche
  générale et par le texte intégral des ouvrages reste à qualifier.
- **Khan Academy FR, 100,66 Go.** Elle apparaît dans les cinq premiers
  résultats pour cinq des six sujets d’école testés. Elle mène sur les
  équations et la comparaison mitose-méiose. Sésamath et Wikiversité
  fournissent des alternatives accessibles quand elle est retirée.
  L’apport porte notamment sur la forme pédagogique. Vérifier la vidéo et
  ses exercices avant d’arbitrer uniquement sur le texte.
- **Recouvrement réel.** Khan a deux pages « Comparaison entre la mitose et
  la méiose », avec le même texte extrait et le même chemin WebM dans
  l’archive, sous deux URLs. Cela ne représente pas deux fichiers ZIM ou
  deux copies du média. iFixit sert le guide 133026 en anglais dans ses
  deux éditions, avec des habillages et des longueurs de texte différents.
  Un document traduit reste une source distincte.
- **TED, 30,02 Go dans 18 ZIM.** Le catalogue des vidéos contient 2 772
  entrées. Le rapprochement par chemin interne et taille trouve 396 groupes
  candidats sur plusieurs ZIM. Le SHA-256 de chaque média local confirme
  tous ces groupes, soit 521 occurrences en plus et 5,31 Go de données vidéo
  répétées. Certains packs peuvent avoir des pistes ou des conférences
  exclusives. Les Go répétés mesurent le contenu des entrées vidéo. Libérer
  cet espace impliquerait de choisir des packs ou de reconstruire les ZIM.
- **Autres gros lots.** Gutenberg représente 195,45 Go dans 24 partitions,
  et les trois Wiktionnaires 19,81 Go. Leur inventaire signale où
  échantillonner. Le recouvrement des œuvres ou des définitions reste à
  mesurer.

## Résultats corrigés et limites

La campagne HTTP de référence en 0.108.0 a exécuté 166 cas en combinant
les [besoins de Marc](../../tests/fixtures/domain-evaluation/besoins-marc-2026-11-21.json)
et la [recette du portail](../../portal/interface/search-reference.json).
Les deux cas du thème armes ont été écartés de cette passe. Résultat,
134 recherches avec au moins une réponse, 32 sans résultat et une seule
couverture signalée partielle. Ces nombres mesurent la récupération des
candidats, sans note de pertinence automatique.

Le contrôle historique de 18 références précises acquitte 14 ouvertures
avec texte et fichier source. Le PDF attendu pour « fractions CM2 »,
« plantes toxiques » et « douleur dents » manque parmi les premiers
résultats de cette recette. Le même contrôle cherche un identifiant
cartographique via la recherche documentaire et le catalogue de cartes
du laboratoire est vide. Le cas cartes reste en échec, à part de la
qualification du moteur de texte.

- Wikipédia groupe les URLs dont la lecture établit la même destination
  dans la même archive. « Photosynthese » et « Photosynthèse » du même
  Wikipédia FR cèdent une place à un autre résultat. Les éditions
  encyclopédiques restent individuellement cherchables.
- iFixit regroupe le même identifiant de guide dans la même langue pour
  éviter que deux habillages se suivent dans les résultats. La recherche
  « réparer un poste radio » retrouve des références distinctes, mais
  privilégie encore trop les autoradios.
- Les pénalités de titres de catégories et le filtre des chansons sur
  une demande pratique fonctionnent à nouveau. Le test couvre le cas d’un
  titre de catégorie sans URL caractéristique.
- « Seed saving for vegetable garden » passe de zéro résultat à
  *Produire des semences potagères bio*, page 20, ouverte. La variante
  française trouve ce même PDF derrière un résultat commercial. La
  formulation de mise à la terre remonte le guide Victron dans les trois
  premiers, avec deux références iFixit encore trop spécialisées. Les
  changements de vocabulaire ont corrigé l’accès sans établir le bon
  ordre sur toutes les variantes.

**Le fonds est large et l’index textuel de base couvre les fichiers
recensés. La recherche pratique reste irrégulière.** « Complet » indique
qu’une interrogation a abouti dans le périmètre choisi. Le test retrouve
des listes sans source utile ou sans aucun résultat, notamment pour les
rongeurs, la pêche en rivière, certaines notices et des formulations
d’alimentation. La recherche ciblée et l’ouverture permettent ensuite de
distinguer une source présente mais mal classée d’une vraie lacune de
contenu. Les [quatre lacunes détaillées](../bibliotheque/classement-pratique-et-laboratoire-bazzite.md#quatre-lacunes-après-lecture-du-fonds)
restent à traiter avec des sources françaises directement utilisables.

## Contrôles logiciels

La suite Python complète du candidat, exécutée dans un conteneur de test
sans accès au réseau ni aux données du labo sur Bazzite, a terminé avec
**1 362 tests, 7 ignorés, aucun échec**. Les tests couvrent notamment la
recherche, le classement et le lecteur d'archives. Les routes de recherche
JSON et progressive, puis l'ouverture par `/api/source`, ont aussi été
exercées sur le vrai Kiwix Bazzite pour les alias de photosynthèse, le
doublon d'autoradio et les semences, avec une requête témoin sans résultat.
La 0.108.1 est une
correction compatible. Elle utilise le schéma et les index existants.

## Reproduction

`scripts/audit_search_quality.py` fonctionne avec les dépendances du pilote,
un Kiwix local et un état jetable initialisé. Sur Bazzite, le processus
utilise les dépendances de l’image du labo, les ZIM et compléments SQLite
montés en lecture seule et un SQLite neuf. Pour une comparaison avec les
guides, y copier uniquement les lignes d’index des guides publics
(`documents`, `passages`, `guide_meta`, `guide_search_domains`, `guide_dates`),
sans traductions privées ni état des comptes. Monter aussi le catalogue
de la bibliothèque en lecture seule. Les chemins sont configurés par
`PILOT_STATE_DIR`, `ZIM_DIR`, `GUIDES_DIR`, `CATALOG_DIR` et `KIWIX_URL`.
Créer le marqueur `audit-search-state` dans l’état jetable.

```sh
python scripts/audit_search_quality.py \
  tests/fixtures/domain-evaluation/apport-wikipedia.json wikipedia.jsonl

python scripts/audit_search_quality.py \
  tests/fixtures/domain-evaluation/apport-collections-volumineuses.json volumes.jsonl \
  --profile all --profile without-survivor --profile without-khan
```

Pour chaque demande, comparer les identifiants dans les cinq premiers,
l’ouverture des documents, les différences entre variantes et la lecture
des passages pertinents. Pour les requêtes sans source pertinente, essayer
une formulation courte ou le titre connu puis un accès direct à la
collection. Prendre un échantillon par usage et langue et vérifier les
cas difficiles séparément. Comparer la précision et le rang avant
d’utiliser les délais recueillis pour l’optimisation.
