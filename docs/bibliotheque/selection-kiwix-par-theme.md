# Sélection automatique des collections Kiwix — pilote 0.1.8

**Statut : guide de référence**, fonction implémentée et testée sur Linux.

Le préparateur peut choisir des archives du catalogue officiel Kiwix selon les
thèmes demandés, en tenant compte des fichiers déjà installés. Cette fonction
est accessible par les scripts de préparation ; il n'y a pas encore de bouton
de sélection dans le portail de Marc. Aucun modèle IA n'intervient.

## Préparer une sélection

~~~bash
python3 scripts/kiwix_select.py themes
python3 scripts/kiwix_select.py select --lab \
  --theme autonomie --theme survie --theme chasse --theme agriculture \
  --theme energie --max-add-gb 10
~~~

Autres thèmes : eau, alimentation, sante, abri, reparation, communications,
education, nature et orientation. `--theme tous` les regroupe. Les identifiants
de commande s'écrivent sans accents. Français et anglais sont retenus par défaut ;
`--language fr` limite aux collections déclarant le français, y compris les
collections multilingues. Cela ne garantit pas que tout le contenu ou la piste
audio soit en français.

`--lab` vérifie le montage et la capacité du volume dédié de Louis. Sur une
installation Windows ou Linux classique, utiliser plutôt `--work-dir` :

~~~powershell
py -3 scripts\kiwix_select.py select --work-dir D:\SetupSurvie\prive --theme tous --max-add-gb 10
~~~

La consultation du catalogue et des Metalinks nécessite Internet sur la machine
de préparation. La bibliothèque et l'assistant conservent leur fonctionnement
hors ligne. La sélection ne télécharge aucune archive et ne redémarre aucun service.

Le plan est enregistré dans `donnees/catalog/kiwix-selection.json`. Il contient
l'inventaire des ZIM, PDF, cartes et autres guides locaux, leurs tailles et leur
rapprochement avec le catalogue du projet. Aucun compte ou contenu privé n'est lu.
Pour chaque correspondance, il conserve thèmes, motif, édition, état de sélection,
taille, provenance et disponibilité annoncée des images, vidéos et index plein texte.
Les ajouts sélectionnés possèdent la taille exacte et le SHA-256 du Metalink officiel.
Les thèmes sans correspondance et les problèmes de métadonnées restent explicites.

Le plan existant n'est jamais écrasé. Choisir un autre `--output CHEMIN.json`
pour préparer une nouvelle sélection. `--feed CHEMIN.xml` réutilise un catalogue
XML sauvegardé ; les Metalinks des nouveaux ajouts restent consultés en ligne.
Un catalogue paginé ou incomplet est refusé. Le plan conserve l'empreinte du
catalogue utilisé et la date de sélection.

## Télécharger les ajouts du plan

Sur le laboratoire, séparer le transfert de l'actualisation des services :

~~~bash
python3 scripts/content.py download --lab --no-refresh \
  --selection /run/media/louis/SetupSurvie/data/catalog/kiwix-selection.json
python3 scripts/lab_refresh_library.py
~~~

La seconde commande actualise Kiwix et le pilote, sans lancer le moteur IA.
Sur Windows :

~~~powershell
py -3 scripts\content.py download --work-dir D:\SetupSurvie\prive --selection D:\SetupSurvie\donnees\catalog\kiwix-selection.json
~~~

Le téléchargeur applique reprise, contrôle des tailles et SHA-256, verrou,
préservation des fichiers différents et publication après vérification. Un plan
vide ne déclenche aucun téléchargement. Conserver le plan avec les contenus pour
garder leur provenance ; ne pas modifier ses chemins ou empreintes à la main.

## Règles et budget

Les règles sont dans `deploy/kiwix-themes.json`. Elles privilégient les collections
pratiques connues, puis les mots-clés dans les titres et descriptions ; dans ces
groupes, le français principal et les petits fichiers passent d'abord.
Une archive correspondant à plusieurs thèmes n'est sélectionnée qu'une fois.
Les variantes illustrées complètes sont privilégiées, puis leur édition la plus
récente. Les jeux repérés par leurs métadonnées sont exclus.

Une édition locale est conservée sans téléchargement d'une nouvelle édition
ou variante. Pour les collections Wikimedia reconnues, un extrait thématique
est écarté si la collection complète de même langue est présente ou déjà
sélectionnée. Cela ne garantit pas l'identité des éditions ni l'absence de
recoupements entre éditeurs différents. Les fichiers existants ne sont jamais
supprimés. Leur présence ne constitue pas une nouvelle vérification SHA-256.

Le plafond de nouveaux transferts est **10 Go par défaut**, réglable avec
`--max-add-gb`. Il ne remplace ni les **500 Go documentaires**, ni la marge physique
libre de **15 Go**, ni le plafond du volume du laboratoire. Les partiels comptent
dans l'occupation et réduisent les octets restant à transférer. Les contrôles
sont rejoués pendant le téléchargement. Les tailles OPDS étant arrondies, les
tailles exactes des ajouts proviennent des Metalinks officiels.

## Portée et limites

La sélection porte sur des **collections entières**, pas sur tous les articles
d'un thème à l'intérieur d'une encyclopédie générale. Une correspondance de
métadonnées ne valide pas la pertinence, l'actualité, la sécurité des conseils
ou les droits commerciaux. Les règles sont explicites et extensibles ; elles
peuvent manquer une source dont la description est pauvre.

Les archives sans `_ftindex:yes` sont signalées comme dépourvues d'index plein
texte annoncé. Elles peuvent rester consultables directement dans Kiwix mais
ne sont pas présentées comme recherchables par l'assistant. Les vidéos déjà
embarquées dans un ZIM ne constituent pas un import YouTube ni une transcription
ou une compréhension des vidéos par l'IA.

Les anciens ouvrages et les forums demandent une revue éditoriale. Toutes les
nouvelles sélections restent marquées `commercial_review`. Leur présence dans
Kiwix ne valide pas une redistribution commerciale. Les encyclopédies et les
guides officiels existants restent complémentaires de la sélection automatique.

## Vérifications des 11 et 12 novembre 2026

Au début de cette tâche, sur le volume monté de Louis, les **78 entrées figées** du projet étaient présentes
avec la taille attendue. Il contient **10 ZIM, 68 PDF et 2 PMTiles**, ainsi que
les guides complémentaires, pour environ **200,60 Go** de bibliothèque.
Les empreintes des gros fichiers n'ont pas toutes été recalculées dans cette
tâche. La recette précédente est conservée dans le bilan « Bibliothèque du Sud,
recherche et IA » de la livraison 0.1.7. Des ajouts documentaires indépendants
peuvent faire évoluer cet inventaire ; chaque nouveau plan relève les fichiers
présents au moment de sa création.

Le catalogue officiel consulté contient **3 555 entrées**. La sélection réelle
repère Gardenology, energypedia, les questions-réponses de jardinage, de radio et
de réparation, ainsi que les bibliothèques Zimgit. Aucune collection spécialisée
chasse n'a été repérée dans les langues retenues ; cela ne prouve pas l'absence
d'articles sur la chasse dans Wikipédia ou les autres ouvrages.

Les tests simulés contrôlent langues, éditions, variantes, extraits Wikimedia,
jeux hors sujet, fichiers existants, partiels, budgets, Metalinks incohérents et
transmission du plan au téléchargeur avec publication vérifiée. Les rapports
réels et tests locaux sont sur le SSD sous `results/kiwix-themes/`. Aucun nouvel
essai d'inférence n'a été lancé. La sélection sur Windows réel et l'évaluation
éditoriale des ajouts restent à faire. Le workflow Windows inclut les tests de
sélection ; sa présence ne signifie pas que son exécution distante a réussi.

La recette finale sur les seuls fichiers de cette livraison réussit **91 tests**,
dont 14 dédiés à la sélection Kiwix, dans un conteneur sans réseau, données
privées ni GPU. Les trois configurations Compose sont analysées sans démarrage.
Le plan conservé dans `data/catalog/kiwix-selection.json` propose 30 ajouts,
pour **9,93 Go** supplémentaires, avec un plafond de 10 Go. Ces archives sont
sélectionnées, pas téléchargées ni validées éditorialement.
