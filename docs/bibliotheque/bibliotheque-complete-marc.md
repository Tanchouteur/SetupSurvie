# Bibliothèque complète de Marc et laboratoire réduit

**Guide de référence — pilote 0.1.19, 12 novembre 2026.** Besoin confirmé par Louis : Marc souhaite le fonds utile le plus complet possible ; son installation ne possède aucun plafond documentaire logiciel. Le laboratoire de Louis peut conserver une sélection plus petite.

Le 21 novembre 2026, Louis demande de rapprocher le laboratoire Bazzite du
fonds de Marc, avec priorité aux guides pratiques et écarts documentés quand
la capacité impose une sélection. [Plan et état du laboratoire](classement-pratique-et-laboratoire-bazzite.md)

## Fonds de référence figé

**Depuis 0.85.0 — demande de Louis du 21 novembre 2026.** Le catalogue Kiwix
change d’édition sans prévenir : neuf jours après l’installation de Marc,
28 de ses 115 archives n’étaient plus l’édition proposée et deux familles
avaient quitté le catalogue (les anciennes éditions restent téléchargeables
par leur nom exact). Pour que chaque installation reçoive le même fonds, le
manifeste [`deploy/library-reference.json`](../../deploy/library-reference.json)
fixe le nom exact, la taille et l’empreinte SHA-256 officielle de chaque archive.

Contenu de la **version de travail** du 21 novembre 2026 : **205 archives,
1 046,6 Go**, guidée par la [liste de thèmes de Marc](savoirs-durables.md#liste-de-thèmes-de-marc--21-novembre-2026). Louis précise que l’inventaire de Marc était un premier essai
large : la référence doit être ajustée aux besoins réels, sans retirer ce
qui peut servir (le moins utile passe dans **Autre** plutôt qu’en exclusion).
- Le fonds relevé chez Marc, à l’édition installée, sauf les 2 collections
  sans usage exclues par le [tri fourni](../../deploy/collection-sort-default.json).
- Les vidéos C'est pas sorcier par thème (édition 2026-11, qui remplace les
  trois thèmes 2024-11 de Marc), Mondial Tissus (couture) et Maître Lucas
  (apprentissages du primaire).
- Des ajouts pratiques : Survivor Library (220 Go de manuels techniques
  anciens), Ready.gov, MedlinePlus, NHS Medicines, CDC, médecine militaire,
  WikiCiv, Restarters, recettes du domaine public, questions-réponses
  brassage, animaux et ingénierie, LibreTexts médecine et ingénierie.
- Des contenus éducatifs et de lecture : Les Fondamentaux, Ubongo, Éducation
  et Numérique, livres Prunelle et Ganndal, poésie et littérature audio,
  vulgarisation scientifique française, rangés dans **Autre** quand ils ne
  servent pas la recherche pratique.
- Pour les thèmes de Marc : documentation Ubuntu en français, bibliothèque
  de nœuds, wiki OpenStreetMap. Pour la religion, Internet, la culture, les
  langues et les loisirs, Marc ne veut qu’une base pour « avoir de tout » :
  Wikipédia, Vikidia et C'est pas sorcier la fournissent ; aucun forum ou
  fonds spécialisé n’est ajouté pour ces sujets.

Le rapprochement du 21 novembre compte **110 éditions identiques** sur les
115 archives de Marc, **trois éditions remplacées**, **deux collections
écartées** et **92 ajouts**. Le tri par défaut conserve les choix de son
export et classe 129 archives de la référence dans le Fonds principal,
76 dans Autre.

Le 23 novembre, Louis indique avoir ajouté les mêmes contenus chez Marc.
Le [contrôle du fonds Bazzite](../essais/2026-11-23-audit-qualite-recherche-bazzite.md)
confirme 205 ZIM et détaille l'apport marginal de Wikipédia anglais, de
Khan Academy et de Survivor Library. Le relevé du 21 novembre reste l'état
observé avant cet ajout. Les résultats de pertinence du contrôle viennent
du laboratoire Bazzite. Le [relevé du 24 novembre](../essais/2026-11-24-apport-wikipedia-bazzite.md)
compare aussi le français, Maxi EN et Simple English à la lecture et
distingue le rôle encyclopédique des guides pratiques.

Bazzite disposait de **2,44 To libres sur son SSD physique** au contrôle en
cours de transfert. Les 128 archives présentes avaient le nom et la taille
attendus. La File d’attente en comptait 121 avec un reçu d’empreinte conforme
au manifeste. Le laboratoire poursuit le transfert et publie le rapprochement
final dans `results/comparaison-recherche/rapprochement-reference.json` sur
son volume dédié. Ce contrôle distingue la présence d’un fichier, la
vérification de son empreinte et sa disponibilité dans Kiwix.

Le second contrôle du 21 novembre porte sur **204 archives vérifiées et
servies**, totalisant **826,27 Go**. La dernière archive est Survivor Library
(220,35 Go). Le transfert a repris vers 3,15 Go depuis un miroir déclaré
dans son Metalink, après validation de la taille et du SHA-256 du manifeste.
Le test mesure séparément le classement sur ces 204 archives et l’ouverture
des passages sur le portail. L’audit définitif attend la dernière archive.

Le SSD physique de Bazzite annonce environ **4 To**, dont **2,15 To libres**
au contrôle du 21 novembre en cours de transfert. Le volume clairsemé du
labo annonce davantage de place libre que le disque physique. Le disque
physique fixe la marge réelle. Chez Marc, le diagnostic Windows du
18 novembre confirme que les données utilisent le SSD de **2 To**. Le
relevé du 21 novembre y mesure **252 Go d’index de classement avant
compression**. Il faut ajouter ces index et les autres données aux
**1 046,6 Go** des archives de référence. L’espace libre actuel chez Marc
reste à mesurer.
[Diagnostic Windows](../installation/configuration-materielle-cible.md#18-novembre-2026--transfert-déclaré-réussi-et-rapports-0430),
[mesure des index](../essais/2026-11-21-index-compresse.md)

Le contrôle des PDF trouve **100 fichiers du catalogue public**, chacun
vérifié par SHA-256 et indexé sur le labo. Le 101ᵉ document du catalogue,
les fiches de l’Anses sur les plantes toxiques, reste absent. Les adresses
du catalogue et des PDF directs de l’Anses renvoient une page de contrôle
anti-robot au téléchargeur depuis Bazzite et le runner. La taille et
l’empreinte du PDF de l’édition figée restent donc à vérifier avant de le
publier. Cette observation ne décrit pas la liste
des PDF de Marc. [Page de l’Anses](https://www.anses.fr/fr/article/confusion-entre-plantes-toxiques-plantes-comestibles)


Dans **Mon appareil → Bibliothèque → Organiser les collections**, la section
**Comparer avec la bibliothèque de référence** affiche les fichiers manquants,
les éditions différentes et les changements de classement. Le contrôle rapide
compare la taille des fichiers et les empreintes déjà enregistrées pour leur
révision actuelle. **Télécharger** demande l’édition
indiquée et ouvre un lien vers la **File d’attente**. Le serveur contrôle
l’empreinte pendant le téléchargement.

**Revenir à l’état de la référence** ouvre la liste des archives à télécharger,
des anciennes éditions et archives hors référence à retirer, et des collections
à reclasser. La confirmation concerne les fichiers affichés. Une archive de
remplacement est vérifiée avant publication et l’ancienne édition reste
disponible jusqu’à cette vérification. Les fichiers locaux hors ZIM, dont les
guides PDF et les vidéos ajoutées à la main, restent accessibles. La File
d’attente indique le déroulement de l’opération.

Installer ou compléter exactement cette référence (les collections exclues
par le tri local restent ignorées) :

```powershell
py -3 scripts\content.py download --work-dir D:\SetupSurvie\prive --selection deploy\library-reference.json
```

Comparer une installation à la référence, sans rien télécharger ;
`--deep` recalcule les empreintes, ce qui est long :

```powershell
py -3 scripts\library_reference.py verify --work-dir D:\SetupSurvie\prive
```

Le rapport distingue archive conforme, manquante, de taille ou d’empreinte
différente, autre édition et archive hors référence (conservée). Une autre
édition n’est jamais remplacée sans téléchargement de la référence. Pour
faire évoluer le fonds, régénérer le manifeste à partir d’un inventaire puis
livrer une nouvelle version :

```sh
python3 scripts/library_reference.py build --inventory inventaire.json --add 'MOTIF' --reason 'motif' --reference 'origine et date'
```

### Guides ajoutés le 22 novembre 2026 (0.100.0)

Une mise à jour ne télécharge jamais de contenu. Pour ajouter chez Marc les
18 guides des thèmes sans résultat, lancer une fois, avec Internet, après la
mise à jour en 0.100.0 (les guides déjà présents et vérifiés sont conservés) :

```powershell
py -3 scripts\content.py download --work-dir D:\SetupSurvie\prive --pack survival --pack repair --pack nature --pack food --pack agriculture --pack family-health
```

L’index par espace des archives se reconnaît périmé après la mise à jour :
la préparation automatique le refait, sinon utiliser une fois **Créer ou
reprendre les index**. Le classement des guides est recalculé à chaque
recherche.

### Reporter le tri fait chez Marc

Le fonds et le tri de Marc au 21 novembre 2026 sont conservés dans
[`inventaires/`](inventaires/README.md). Quand Marc a trié sa bibliothèque,
récupérer depuis son réseau la page `http://ADRESSE:8080/api/inventory`
(enregistrer la page au format JSON) et l’export **Mon appareil → Paramètres →
Organiser les collections → Exporter ce classement** (`SetupSurvie-tri.json`).
Puis afficher ses changements :

```sh
python3 scripts/library_reference.py diff \
  --before docs/bibliotheque/inventaires/marc-2026-11-21-archives.tsv --after inventaire-marc.json \
  --sort-before docs/bibliotheque/inventaires/marc-2026-11-21-tri.json --sort-after SetupSurvie-tri.json
```

Le rapport liste les archives retirées, ajoutées ou changées d’édition et
chaque collection déplacée entre Fonds principal, Autre et Exclues. Reporter
ces choix dans `deploy/collection-sort-default.json`, régénérer le manifeste
avec `build`, puis enregistrer les deux fichiers de Marc comme nouveau relevé
daté dans `inventaires/`.

`--inventory` accepte la page `/api/inventory` enregistrée depuis le portail
ou une liste de fichiers `.zim`. Le manifeste liste aussi les archives
écartées par le tri et celles dont le Metalink est introuvable. La taille
de la référence dépasse la capacité de nombreux disques : vérifier la place
chez Marc avant le téléchargement. `kiwix_select.py prepare` reste la
découverte des dernières éditions par thème ; il ne garantit pas un fonds
reproductible.

## Préparer directement chez Marc

Installer le kit et ses prérequis selon le [guide Marc](../installation/pilote-marc.md), puis utiliser le logiciel 0.1.15 ou ultérieur. Le kit existant ne se complète pas simplement parce que le code change. Avec Internet sur le PC de Marc :

```powershell
cd D:\SetupSurvie\application
py -3 scripts\kiwix_select.py prepare --work-dir D:\SetupSurvie\prive
```

Cette commande sélectionne puis télécharge les ajouts sans confirmation supplémentaire. Elle inclut tous les thèmes pratiques, les guides du catalogue figé et les encyclopédies françaises et anglaises, avec dédoublonnage des collections locales. Elle conserve chaque plan daté sous `donnees/catalog/`, vérifie les tailles et SHA-256, puis actualise Kiwix et le pilote. Aucun modèle n'est téléchargé ou interrogé, aucune pause IA n'est levée.

Le plafond documentaire est absent sur cette installation. La place réellement libre et une réserve de **15 Go** restent obligatoires. Si tout ne tient pas, les fichiers exclus par capacité sont indiqués dans le plan ; il faut davantage de stockage pour les ajouter. Le fonds n'est pas garanti exhaustif sur tous les sites Internet : la découverte porte sur le catalogue officiel Kiwix et les guides explicitement référencés du projet, en français et anglais par défaut.

En cas d'interruption, reprendre le plan enregistré, avec son chemin exact affiché par la commande :

```powershell
py -3 scripts\content.py download --work-dir D:\SetupSurvie\prive --selection D:\SetupSurvie\donnees\catalog\kiwix-selection-DATE.json
```

Le téléchargement reprend les partiels et conserve les fichiers différents. Pour chercher sans télécharger, utiliser `select` au lieu de `prepare`. Pour un transfert sans redémarrage des services, ajouter `--no-refresh` à `prepare` ou au téléchargeur.

### Reprise supervisée des gros plans (0.1.24)

Pour une sélection déjà enregistrée et un transfert long, notamment pendant la nuit :

```powershell
py -3 scripts\content_retry.py --work-dir D:\SetupSurvie\prive --selection D:\SetupSurvie\donnees\catalog\kiwix-selection-DATE.json
```

Ce superviseur conserve les fichiers dont la taille et le reçu vérifié correspondent
au plan, sans relire toutes les grosses archives à chaque relance. Un fichier absent,
une taille différente ou une empreinte différente dans le reçu reste à contrôler.
Les nouveaux fichiers sont toujours vérifiés intégralement avant publication.

Une erreur réseau sur un document ne bloque plus les suivants. Les contenus en
échec sont inscrits dans `catalog/content-retry.json`, puis retentés par passes
avec un délai croissant, plafonné à 15 minutes. Le nombre maximal de passes est
96 par défaut (`--max-rounds`) ; après épuisement, le statut reste incomplet et
les partiels sont conservés. Le programme ne redémarre aucun service et ne lance
aucun modèle. Une actualisation du catalogue et de la recherche reste à effectuer
séparément après les transferts.

En cas de chaîne de certificats manquante sous Windows, le superviseur effectue
une vérification HTTPS avec le client système, pour permettre à Windows de
récupérer les autorités nécessaires, puis retente Python. Aucun certificat
invalide n’est accepté et aucune vérification HTTPS n’est désactivée.

Le portail propose le fonds de référence depuis **Organiser les collections**.
La sélection de nouvelles collections par sujet reste disponible en ligne de
commande. Un transfert déjà lancé reprend avec son plan d’origine.

## Sujets recherchés

Depuis 0.1.19, **38 thèmes** incluent les [nouveaux savoir-faire de Marc](savoirs-durables.md),
dont sciences, mesure, matériaux, textile, machines, métallurgie, chimie pratique,
organisation collective et histoire des techniques. Les thèmes existants couvrent
aussi eau, alimentation, habitat, agriculture, santé, énergie, réparation,
communications, enseignement, nature, préparation et loisirs. Les anciens plans
conservent leurs choix ; préparer une nouvelle sélection avec les nouveaux thèmes.

Une correspondance désigne une collection entière ; elle ne valide pas chaque article ni la couverture de toutes les espèces, techniques, médicaments, compléments, armes ou équipements. Les ressources médicales professionnelles, ouvrages anciens et forums restent à examiner. Les droits de redistribution commerciale restent à vérifier.

Constat de la sélection **0.1.15**, conservé à son périmètre : le catalogue consulté
le 12 novembre contient **3 657 entrées** ; les règles de cette version ne repéraient
aucune collection spécialisée FR/EN pour chasse, pêche, plomberie, soudure,
carburants, nuisibles, médicaments, risques ou champignons. Les collections
générales et PDF pouvaient contenir des chapitres correspondants. La grille des
[savoirs durables](savoirs-durables.md) décrit la recherche élargie de 0.1.19 ; les
lacunes nécessitent toujours des manuels et une recette réelle, sans inventer de fichiers.

## Laboratoire et kit de transport

`--lab` conserve le montage SSD obligatoire et une marge libre de 15 Go.
Le 21 novembre 2026, Louis a levé les plafonds fixes du laboratoire. Un
échantillon réduit reste possible avec une limite explicite :

```bash
python3 scripts/kiwix_select.py prepare --lab --theme autonomie --theme agriculture --max-add-gb 10 --no-refresh
```

Le kit ne doit pas imposer sa taille à Marc. Un nouvel export inclut désormais Wikipédia anglais lorsqu'il est présent ; `--no-english-wikipedia` permet encore un transport volontairement réduit. `refresh-library` ajoute les contenus publics disponibles du catalogue figé, y compris Wikipédia anglais, ainsi que les collections enregistrées par le téléchargeur dans `catalog/downloaded-content.json`. Les sources sont vérifiées avant copie ; les comptes et modèles existants ne sont pas remplacés. La préparation et les contrôles restent dans le [guide du kit](../installation/preparer-kit-hors-ligne.md).

Pour éviter une deuxième copie volumineuse sur le SSD limité du laboratoire, préparer les compléments directement chez Marc. Les données supplémentaires chez lui n'ont pas à être téléchargées également chez Louis.

## Vérifications et limites — bilan 0.1.15 conservé

Suite locale : **149 tests, 148 réussites et un test COM Windows ignoré sur Linux** ; configuration Compose contrôlée sans démarrage. Tests sur le runner CPU, avec fichiers minuscules : sélection au-delà de 500 Go hors laboratoire, plafond laboratoire maintenu, réserve physique, sélection des guides et de Wikipédia anglais sans doublon, respect des langues, export d'une nouvelle collection et refus d'une source corrompue. Parcours Playwright avec API simulée : 29 thèmes, absence de plafond, préparation, téléchargement, pause et affichage de 320 à 1 366 pixels.

Aucun corpus, modèle, ZIM ou carte lourde téléchargé dans le runner. Le catalogue distant a été consulté pour ses métadonnées uniquement. Cette livraison ne constitue ni une actualisation physique du kit SSD, ni un téléchargement chez Marc, ni un essai Windows ou iPhone réel.


## Le plan documentaire ne couvre pas les cartes

Un plan de sélection Kiwix/PDF ne comprend ni PMTiles, ni relief, ni lieux OSM,
ni graphes de routage. Depuis 0.1.33, l’installation en ligne prépare les fonds
et le relief de base séparément : voir le [guide Windows](../installation/deux-etapes-windows.md#cartes-incluses-dans-la-préparation-de-base--0133).
L’achèvement d’un ancien plan reste limité à ses fichiers. L’[audit du fonds réel
chez Marc](../essais/2026-11-13-audit-fonds-marc.md) distingue ce résultat des besoins
pratiques, de l’indexation et des défauts d’accès encore ouverts.
