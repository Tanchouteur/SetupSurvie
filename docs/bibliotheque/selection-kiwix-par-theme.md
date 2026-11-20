# Sélection automatique des collections Kiwix — pilote 0.1.15

**Statut : guide de référence**, fonction implémentée et testée sur Linux.

L’administrateur peut choisir des archives du catalogue officiel Kiwix selon les
thèmes demandés, en tenant compte des fichiers déjà installés. La sélection
est accessible dans le portail et par les scripts de préparation. Aucun modèle
IA n’intervient.

## Fonds complet de Marc

Voir le [guide de la bibliothèque complète](bibliotheque-complete-marc.md). `prepare --work-dir DOSSIER_PRIVE` sélectionne tous les thèmes et télécharge les ajouts en une commande. `select` prépare uniquement le plan. Tous les thèmes sont retenus par défaut en CLI ; les premières sélections du portail cochent aussi tous les thèmes. Les préférences précédemment enregistrées restent conservées.

Le thème `fonds-general` ajoute tous les guides du catalogue figé et les encyclopédies FR/EN, y compris Wikipédia anglais. Les plans peuvent donc contenir des PDF et des ZIM. Les langues et éditions locales sont respectées ; la présence locale ne vaut pas une nouvelle vérification d'intégrité. Le téléchargeur enregistre les références effectivement vérifiées pour les futurs exports du kit.

## Depuis le site

Depuis 0.1.19, les [savoirs durables](savoirs-durables.md) étendent la sélection à
38 thèmes pratiques, avec les fonds culturels et grandes vidéos sur choix explicite, et rattachent des guides figés aux thèmes concernés. Le plan affiche
les sujets à examiner pour chaque parcours, sans certifier leur couverture.

1. Choisir le profil **Famille** (sans mot de passe), puis ouvrir **Mon appareil → Paramètres → Bibliothèque et préparations → Télécharger des collections et préparer les cartes**.
2. Déplier **Enrichir la bibliothèque**. Les lecteurs ne voient pas ce bloc et
   aucune entrée supplémentaire n’est ajoutée au menu principal.
3. Cocher les thèmes, choisir les langues et le maximum à ajouter, puis cliquer
   sur **Chercher les contenus**. Cette étape prépare une sélection sans
   télécharger d’archive. Une connexion Internet est nécessaire sur le serveur.
4. Consulter le volume proposé, les thèmes sans correspondance et, au besoin,
   **Voir les collections proposées**. Après modification des choix, préparer
   une nouvelle sélection avant de lancer le téléchargement.
5. Cliquer sur **Télécharger la sélection**. La progression est conservée sur
   le PC serveur : changer de page ou fermer le navigateur n’arrête pas le travail.
   **Mettre en pause** conserve les partiels ; **Reprendre le téléchargement**
   reprend et vérifie les fichiers. Une réponse réseau peut demander jusqu’à
   une minute avant de prendre en compte la pause.

Les choix et le plan courant sont conservés dans le dossier privé du serveur,
sous `library-web/`. L’interface n’accepte ni chemin, ni URL, ni commande libre.
Les tâches s’exécutent dans un processus hôte distinct, par l’intermédiaire du
contrôleur authentifié. Elles survivent à son redémarrage. Une tâche disparue
après une coupure est signalée comme interrompue : préparer une nouvelle sélection
pour reprendre les partiels. Ne pas lancer simultanément un transfert CLI sur les
mêmes données : le verrou existant refuserait le second téléchargement.
Si une coupure a laissé un verrou de transfert, vérifier depuis le PC serveur
que son processus propriétaire est arrêté avant de retirer ce verrou ; les
fichiers partiels eux-mêmes doivent être conservés.

À la fin, Kiwix est redémarré pour rendre les nouvelles archives disponibles. Si le plan comprend des guides PDF, le pilote est aussi redémarré pour les indexer.
Le pilote interroge son catalogue à chaque recherche ; il n’est pas nécessaire
pour ces seuls ZIM de réindexer les PDF ou de démarrer Ollama. Cela ne remplit pas
les collections Open WebUI. Une archive sans index plein texte reste signalée
comme consultable directement, sans promettre une recherche par l’assistant.

Si le service de téléchargement est indisponible, les contenus existants restent
lisibles. Le lanceur doit démarrer le contrôleur hôte ; la récupération du
laboratoire `scripts/lab_refresh_library.py` le rétablit sans démarrer le moteur IA.

## Préparer une sélection en ligne de commande

~~~bash
python3 scripts/kiwix_select.py themes
python3 scripts/kiwix_select.py select --lab \
  --theme autonomie --theme survie --theme chasse --theme agriculture \
  --theme energie --max-add-gb 10
~~~

La commande `themes` donne les 29 catégories actuelles, dont élevage, pêche, plomberie, soudure, médicaments, risques, nautisme, champignons, sport et culture. `--theme tous` les regroupe. Les identifiants
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

Hors laboratoire, il n’y a **aucun plafond documentaire ni plafond de transfert par défaut**. `--max-add-gb` limite volontairement les nouveaux transferts, `--budget-gb` limite volontairement le fonds total ; 0 signifie aucun plafond hors laboratoire. La marge physique libre de **15 Go** reste obligatoire. En mode `--lab`, les **500 Go documentaires** et le plafond physique du laboratoire restent appliqués. Les partiels comptent
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

Pour le parcours du site ajouté en 0.1.9, voir le [bilan du 12 novembre 2026](../essais/2026-11-12-gestion-bibliotheque-et-controleur.md) :
106 tests, navigation Chromium/WebKit, préparation réelle et récupération du
contrôleur. Les chiffres précédents décrivent la recette des scripts en 0.1.8.
