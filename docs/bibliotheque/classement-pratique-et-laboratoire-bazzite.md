# Guides pratiques et laboratoire documentaire sur Bazzite

**Décision de Louis du 21 novembre 2026 et plan de recette.** La priorité de
la bibliothèque est **Autonomie et résilience**. Louis valide un classement par
rôle des sources, un laboratoire représentant l’installation de Marc sur Bazzite
et un tri initial réglable à partir de son export.

## Ce que montrent les premiers essais

Chez Marc, le filtre « Autonomie et résilience » appliqué à « eau potable »
fait remonter un article sur la salinisation en mer d’Aral, une encyclopédie
et le thésaurus du Wiktionnaire. « Water Purification Systems », provenant
d’iFixit en anglais, apparaît avec l’étiquette Français. La recherche doit
aider à trouver une méthode d’un organisme identifiable et vérifier que le
passage ouvert répond à la question.

Sur l’installation Bazzite en service (0.71.0, fonds réduit), deux pages à
titre anglais de la collection iFixit française arrivent en tête en mode
français. Leurs extraits mêlent les deux langues. Wikilivres propose un
chapitre sur la potabilisation en troisième position.
Le résultat obtenu chez Marc inclut d’autres collections. Les deux relevés
orientent la recette de classement et de filtrage.

## Rôle des sources et tri d’installation

| Rôle | Sources de départ | Usage dans la recherche |
| --- | --- | --- |
| Guide pratique | Fiches OMS, manuels Hesperian, Appropedia, tutoriels iFixit, guides de premiers secours | Candidats à Autonomie et résilience. Vérifier que l’article ou la fiche propose une méthode utile pour la requête. |
| Référence | Wikipédia, encyclopédies et forums techniques | Savoirs et culture et recherche générale. En Autonomie, Wikipédia, Vikidia et certains forums techniques du Fonds principal peuvent fournir des pistes si aucun guide ne traite directement du sujet. |
| Langue | Dictionnaires et Wiktionnaire | Recherche de définitions et de vocabulaire. |
| Culture | Gutenberg et autres fonds littéraires ou culturels | Consultation culturelle et recherche générale. |

Une page de navigation, un catalogue d’appareils ou une table des matières
peut servir d’accès à la bonne procédure dans une collection pratique.
Les contrôles de recette distinguent ces pages des fiches qui expliquent
quoi faire. Les corrections humaines déjà enregistrées restent prioritaires.

Depuis la 0.89.0, Autonomie peut afficher jusqu’à trois discussions des
forums techniques de bricolage, jardinage, artisanat, menuiserie, vélo et
mécanique du Fonds principal. Le titre doit couvrir tous les termes
du sujet, avec au moins deux termes distincts. Les forums gardent le
rôle Référence et restent soumis au tri manuel.

Le fichier [de tri fourni avec l’installateur](../../deploy/collection-sort-default.json)
reprend les 24 collections rangées dans **Autre** et les 20 références exclues
par Louis. Ce réglage initial porte sur les collections et leurs éditions,
langue comprise. Les quatre rôles concernent la nature des sources et
guideront le classement et la recherche. Le tri manuel Fonds principal /
Autre reste le réglage qui détermine les collections consultées par défaut.
Les dictionnaires et le Wiktionnaire rangés dans Autre restent ouvrables
depuis les Collections. Les rechercher demande de choisir Autre ou Toute
la bibliothèque. Comparer plusieurs réglages sur le
même fonds et garder un export par configuration mesurée.
[Guide des classements](../utilisation/classement-et-collections.md)

## Fonds comparable sur Bazzite

1. Faire l’inventaire des éditions et des tailles chez Marc à partir d’un
   manifeste ou d’un export d’inventaire. Utiliser les mêmes sources vérifiées
   quand elles tiennent dans le laboratoire. La comparaison porte sur les
   collections et les ressources publiques.
2. Utiliser le montage dédié du SSD de 4 To. Louis a levé le 21 novembre
   les anciens plafonds de 500 Go documentaires et de 600 Go globaux.
   La marge reste calculée sur l’espace réel du SSD. Si le fonds
   complet dépasse la capacité disponible, conserver en priorité les guides pratiques,
   puis prendre des éditions encyclopédiques ou littéraires plus petites.
   Consigner pour chaque écart la collection, l’édition et le volume.
3. Vérifier les fichiers à la copie ou au téléchargement. Recréer le catalogue
   et les index localement. Utiliser des profils d’essai et laisser l’inférence
   en pause jusqu’à sa reprise explicite par Louis.
4. Partager les chemins, ports, moteurs et budgets avec les sessions qui
   travaillent sur Bazzite. Des ports distincts permettent de garder
   l’installation 0.71.0 disponible pendant les comparaisons.

**Démarrage vérifié le 21 novembre.** La session GPT « Installateur Linux et
point de restauration » a confirmé la fin de sa recette en VM. Le montage du
laboratoire a été recréé dans l’image de 590 Go sur le SSD de 4 To.
La copie initiale comprend 18 ressources publiques et 5 343 024 423 octets
vérifiés par SHA‑256, depuis l’installation d’essai Bazzite 0.71.0.
L’ajout des lots pratiques porte le fonds à **100 ressources vérifiées**
(**6 ZIM, 94 PDF**, 10 406 371 992 octets). Le fichier sur les plantes
toxiques reste en attente après interruption et échec de reprise.
L’enrichissement suivant a démarré avec les lots éducatifs et locaux,
Wikilivres et Wikipédia en français et en anglais. Le transfert du
catalogue figé a démarré avec une limite de 215 Go pour cette tranche, avant
la levée des plafonds. Le volume existant reste à agrandir après ce transfert.
Les nouvelles images sont dimensionnées d’après la taille du SSD et sont
clairsemées. Les écritures consomment l’espace au fur et à mesure. Une fois
la publication des téléchargements terminée, l’agrandissement d’un montage
existant se lance avec les droits administrateur par
`./scripts/lab.sh grow --mount-user louis`. L’opération conserve le volume
et les fichiers existants. La commande peut être relancée si la taille de
l’image a changé avant la fin de l’agrandissement du système de fichiers.
Sur le SSD Bazzite, une recette réelle sur image jetable a doublé le volume
ext4 monté, conservé le fichier témoin et confirmé la relance de la commande.
L’agrandissement de l’image de travail attend la fin du transfert actif.
La liste exacte des éditions de Marc et les écarts de couverture restent
à établir.
L’[audit de Marc du 13 novembre](../essais/2026-11-13-audit-fonds-marc.md)
recensait 753,34 Go, dont 241,56 Go de Gutenberg et 43,05 Go de jeux de
société Alexandria. Ce fonds historique dépassait de 253,34 Go l’ancien
plafond documentaire de 500 Go du laboratoire, levé depuis. Ses éditions et les volumes
actuels restent à comparer après le tri de Louis et les téléchargements
ultérieurs. Pour la comparaison, l’inventaire des archives avec tailles
et éditions peut être relevé via le [catalogue local](../utilisation/inventaire-local.md),
sans copier les comptes, vidéos privées ou historiques.

Le portail documentaire 0.76.3 répond sur la boucle locale de Bazzite
(port 18080), avec Kiwix (18081), Open WebUI (13000) et le pilote (18000).
L’installation existante répond sur 8080. Le volume conserve le lanceur de
recette dans `private/demarrer-recherche.py` et son marqueur de pause
d’inférence. Sur Bazzite, après vérification du montage dédié, exécuter
`python3 /run/media/louis/SetupSurvie/private/demarrer-recherche.py`
depuis `/var/mnt/data/AI/.setupsurvie-biblio-code`. Le transfert en cours
se suit dans **Mon appareil → File d’attente → Téléchargements**. Le
lanceur démarre aussi le relevé local avec `scripts/lab_activity.py`. Ce
relevé publie le nom et les volumes des fichiers en cours ainsi que le
résultat du transfert, en lecture seule. L’accès SSH distant demande un montage du
volume séparé quand UDisks refuse l’autorisation de la session.

### Alignement sur la référence de Marc — 21 novembre 2026

Louis a fourni l’inventaire réel de Marc (115 archives, 700,2 Go, 91 guides).
Le labo reçoit d’abord les 54 archives vidéo demandées (C'est pas sorcier
par thème, Mondial Tissus, Maître Lucas, 86,9 Go), puis l’ensemble du
[fonds de référence](bibliotheque-complete-marc.md#fonds-de-référence-figé)
après agrandissement du volume. Le tri fourni du 21 novembre est fusionné
au tri du labo avant ce transfert. État à compléter avec le bilan de
`library_reference.py verify --lab` ; aucune conformité n’est annoncée
avant ce contrôle.

### Mémoire de Kiwix dans le labo — 21 novembre 2026

Avec environ 85 archives et un relevé de recherche en parallèle du
téléchargement, Kiwix a été arrêté par manque de mémoire : le conteneur du
labo était limité à 1 Gio et ne redémarrait pas. Le relevé des 68 thèmes
de Marc mesuré pendant cet arrêt n’a interrogé que les guides PDF ; il est
écarté. Depuis la 0.86.2, le labo donne 6 Gio à Kiwix et le relance en cas
d’échec. L’installation du produit (`compose.yaml`) ne limite pas Kiwix et
le redémarre déjà automatiquement. Sur ce fonds, 51 collections, surtout
vidéo, n’annoncent pas d’index plein texte : leur recherche dépend des
index locaux à préparer.

## Mesurer avant chaque changement

Reprendre le [protocole de mesure existant](../essais/mesurer-classement-documentaire.md)
et ajouter un relevé côté portail pour les recherches en français, en anglais
et mixtes. Noter la version, les éditions, le rang, la langue affichée et
la langue du passage lu, les résultats partiels, le délai et la source
réellement ouverte. Mesurer le nombre de requêtes avec un guide pertinent
dans les trois premiers résultats, les résultats sans rapport dans
Autonomie et les erreurs de filtre de langue. Relire les extraits en aveugle
sur un lot réservé avant de retenir un réglage.

| Famille | Trois recherches de départ |
| --- | --- |
| Eau | Eau potable à la maison après une coupure, stockage d’eau, hygiène avec peu d’eau |
| Premiers secours et santé | Premiers secours citoyen, trousse familiale, hygiène en hébergement partagé |
| Alimentation | Aliments après une panne du réfrigérateur, conservation des légumes, cuisiner avec peu d’énergie |
| Abri et risques | Fixation d’une bâche, information officielle en cas d’inondation, préparer le domicile à une coupure |
| Énergie et éclairage | Batterie de secours, besoins électriques du foyer, éclairage sans réseau |
| Agriculture | Semis, arrosage économe, compost |
| Réparation | Crevaison vélo, réparation d’une fermeture, entretien d’une pompe manuelle |
| Communications et orientation | Écouter les informations locales, organiser les contacts d’urgence, lire une carte hors ligne |
| Enseignement | Activité de lecture CP, exercices de mesure, calcul de consommation |
| Témoins de référence | Salinisation de la mer d’Aral, définition de « potable », littérature de Gutenberg |

Étendre la grille à chaque thème actif du catalogue. Pour chaque besoin,
distinguer guide trouvé et lu, guide présent mais difficile à retrouver,
absence de guide dans la langue choisie et absence de source dans le fonds.
La première recette « eau potable » vise la fiche OMS sur le traitement au
point d’utilisation dans les trois premiers résultats en français et anglais,
avec sa langue réelle. En français uniquement, elle doit être filtrée tant
qu’une édition française correspondante manque. Les témoins encyclopédiques
et lexicaux restent accessibles par une recherche plus large.

Comparer dans cet ordre le résultat initial, le rôle des sources et la langue
au niveau des contenus, puis l’ajout de requêtes bilingues et la priorité aux
guides. Faire les ajouts documentaires en fonction des manques observés.
Vérifier provenance, édition, illustrations et droits avant diffusion.
Pour l’assistant, mesurer les documents effectivement ouverts et cités
lorsque Louis autorise l’inférence. Conserver les essais Windows et iPhone
comme validations sur les appareils cibles.

## Premier relevé sur le fonds pratique — 21 novembre 2026

Quatorze recherches API portent sur douze formulations avant modification du
moteur. Le scénario principal confirme que le PDF OMS sur le traitement au
point d’utilisation s’ouvre depuis le portail. La recherche bilingue « eau
potable » renvoie trois pages d’Appropedia dans les trois premiers résultats
et le chapitre Wikilivres arrive dixième. Le PDF attendu ne figure pas dans
les seize résultats rendus. En français, Wikilivres arrive premier. Le
parcours a aussi été ouvert avec Chromium à 1 366 et 390 pixels. Le
portail signalait des index d’archives et de vidéos incomplets lors de cette
recette.

La fiche de premiers secours citoyen arrive deuxième sur sa requête. La
recherche de crevaison renvoie d’abord un tutoriel pour une chambre à air.
« Batterie de secours » commence par le remplacement d’une batterie
d’appareil photo. « Arrosage économe » et « écouter les informations locales »
ne donnent aucun résultat dans Autonomie. Ces constats décrivent ce que la
recherche fait remonter sur le fonds initial. La couverture et la qualité
de chaque guide restent à apprécier après lecture et comparaison des éditions.

### Suivi du transfert dans la file d’attente

**Recette du 21 novembre 2026.** Sous Chromium, à 1 366 et 390 pixels,
la carte **Téléchargement de la bibliothèque** affiche Wikipédia anglais,
son volume reçu et sa taille totale pendant le transfert réel. La file
reste accessible pendant l’enrichissement. La carte compte séparément les
volumes vérifiés et indique la dernière observation dans les détails.
La 0.80.1 corrige le suivi en lecture seule sans migration de données.

### Relevé étendu et premiers correctifs en essai

Le relevé initial a couvert les **38 thèmes** du catalogue, pendant
l’enrichissement. Kiwix servait six ZIM au début et à la fin. Parmi les 32
réponses de recherche partielles, dix requêtes ne renvoyaient aucun résultat.
Six relevés ont dépassé le délai du client de mesure. Ces chiffres décrivent
la recherche sur ce fonds intermédiaire. Ils restent à comparer à ceux du fonds
enrichi, avant de conclure sur les documents manquants.

Sur le scénario bilingue « eau potable », la fiche OMS sur le traitement au
point d’utilisation passe du **12e au 2e rang** lorsque les mêmes 411 candidats
sont reclassés avec la formulation bilingue et la priorité aux guides
documentaires. L’essai isole l’effet du classement. La couverture de la
requête en production et la lecture des résultats sur tous les thèmes
restent à mesurer.

Dans l’archive iFixit anglaise de décembre 2025, le HTML de la page
« Water Purification Systems » indique le français, tandis que le contenu
et le reste de l’édition sont anglais. Le candidat test reconnaît l’anglais
sur le fichier réel et conserve l’indication française sur la page mixte
de l’édition française. Les essais unitaires couvrent le passage dans le filtre
et l’absence de requête Kiwix vers le Wiktionnaire rangé dans Autre.

Le relevé sur 204 archives a aussi trouvé un article de Low-tech Magazine
écrit en français alors que son HTML indiquait `en-us`. Depuis la 0.88.2,
SetupSurvie lit la langue dans le chemin des articles datés de cette archive.
Le classement et le filtre de langue fonctionnent aussi sur les index du
magazine déjà construits. Sur l’archive réelle, la recherche « dimensionner
une installation solaire » limitée au magazine en français retrouve le guide
et le lecteur renvoie son texte en français.

La recette se rejoue depuis le dépôt avec la liste des 38 thèmes et les
variantes linguistiques du cas OMS.

```sh
python3 scripts/evaluate_domains.py scan-library tests/fixtures/domain-evaluation/autonomie-38-themes.json rapport.json --portal http://127.0.0.1:18080
```

Le rapport conserve la couverture, l’ordre et les titres. Il indique si le
lecteur a renvoyé du texte. L’analyse de la pertinence et la lecture humaine
des passages restent à ajouter. Conserver chaque rapport dans un dossier de
recette hors du dépôt.


### Comparer la recherche sur les thèmes de Marc

La grille `tests/fixtures/domain-evaluation/besoins-marc-2026-11-21.json`
contient 136 requêtes pour 68 thèmes. Comparer le classement précédent,
le repli encyclopédique seul, le filtre PDF seul, les deux réglages
ensemble, le classement de tutoriels de la 0.88.1 et l’ajout des forums
de la 0.89.0. Garder le même catalogue Kiwix, le même tri et les mêmes index.
Relever les requêtes sans résultat, les trois premiers titres, la place des
guides attendus et les recherches partielles. Un résultat présent demande
une lecture du passage avant de déclarer le besoin couvert. Comparer les
latences avec des caches dans le même état.

Le repère encyclopédique garde le classement documentaire de l’article.
La recherche en Autonomie en ajoute jusqu’à trois après les premiers
résultats si aucun guide ou article pratique ne traite directement du
sujet. Son titre doit correspondre au sujet demandé. Un passage PDF doit faire correspondre le sujet dans le titre et
l’extrait pris ensemble. Ces règles permettent de distinguer un résultat
sur le sujet d’une simple mention dans le reste de la page.

Depuis la 0.88.1, un titre de trousse de réparation ou de liste de
fournitures reçoit la priorité d’une piste de matériel. Pour une demande
de méthode, un titre de tutoriel passe plus haut. Les titres qui
expliquent comment employer un kit gardent leur priorité, et les
demandes explicites de matériel conservent leurs résultats. Cette règle
s’appuie sur le titre propre de l’article à l’intérieur d’un ouvrage.
Le classement reste un point de départ pour ouvrir et lire le document.


Sur le laboratoire isolé, les téléchargements alimentent bien la file
persistante de préparation. Le contrôleur hôte dédié n’y étant pas joignable,
lancer explicitement les deux outils sur le SSD et contrôler les deux
`progress.json` dans `data/state/pilot/archive-index/` et
`data/state/pilot/zim-videos/`. L’inventaire indique les pistes réellement
détectées. Le lecteur libzim 4.x expose une méthode publique de lecture
que l’inventaire utilise aussi pour les titres des vidéos YouTube archivées.
La création ou traduction des sous-titres est une étape distincte.

Le relevé du 21 novembre a parcouru les 136 requêtes sur 89 collections
servies. Il a trouvé 47 requêtes sans résultat et signalé une couverture
partielle pour chaque requête. Les archives et les index en cours de
préparation restent à couvrir avant de conclure à des lacunes documentaires.


### Recette du périmètre de recherche

La 0.87.1 applique l’espace Autonomie et résilience aux recherches
ordinaires qui n’indiquent pas d’espace. La recette Kiwix intercepte les
appels en provenance de `/api/search` et d’une question réelle adressée
à `/api/questions`, avec un modèle simulé. Elle vérifie les archives
demandées à Kiwix pour la préparation de la réponse et lors d’un appel
d’outil du modèle. Le Wiktionnaire et Gutenberg rangés dans Autre
sont consultés uniquement dans les recherches explicitement élargies.


### Relevé de recherche sur 204 archives — 21 novembre 2026

Kiwix servait les 204 archives déjà vérifiées du manifeste. La comparaison
a parcouru les 136 requêtes des 68 thèmes de Marc et sept témoins. Le
candidat a renvoyé au moins un résultat pour 82 des 136 requêtes.
Les 136 recherches étaient partielles avec le délai de 12 secondes et
l’index local encore incomplet. À titre de contrôle, avec 60 secondes
sur « eau potable », Kiwix a interrogé 119 collections et a signalé huit
collections incompatibles avec la recherche native et 21 collections
sans annonce d’index texte. Ce relevé ne suffit pas à établir une absence
de ressource.

Un second passage rejoue les mêmes candidats avec les deux classements, à
60 secondes. Le tutoriel iFixit de réparation de crevaison passe de la
deuxième à la première place. La fiche OMS sur le traitement au point
d’utilisation reste deuxième. Les deux repères sur le compas de relèvement
sont trouvés avec chaque classement. Dans le passage suivant, le lecteur a
ouvert le premier résultat de 87 des 136 requêtes et renvoyé du texte à
chaque ouverture (53 en français, 34 en anglais). Les 49 autres requêtes
n’ont trouvé aucun résultat avec ce réglage. Le catalogue est resté stable
et chaque recherche signalait encore une couverture partielle. La lecture
automatique vérifie l’accès au texte et ne qualifie pas sa pertinence.

Kiwix a été relancé deux fois après avoir atteint 6 Gio. La limite a
été portée à 10 Gio sur ce laboratoire pour terminer le relevé. Le lecteur
écrit un point de reprise après chaque requête pour conserver les résultats
en cas d’interruption.

Les trois éditions installées du Wiktionnaire sont rangées dans Autre.
La recherche « compost » dans le Wiktionnaire français sélectionne zéro
collection en Autonomie et en sélectionne une dans Autre. Le premier
article s’ouvre et renvoie du texte français. Depuis la navigation
Collections, Chromium à 1 366 px et WebKit à 390 px ouvrent la page
d’accueil hors ligne du Wiktionnaire sur **18081** et la carte indique
« Rangée dans Autre ».

Les liens du portail isolé 18080 utilisent **18081** pour Kiwix et
**13000** pour Open WebUI. Cette adaptation concerne la copie du portail
dans `/var/mnt/data/AI/.setupsurvie-biblio-code` et sa copie servie sur
le volume du labo. Si cette copie est reconstruite à partir d’une
livraison, conserver les ports propres au labo et régénérer la page avec
`scripts/build_portal.py` avant de publier les fichiers du portail.

Une fois la préparation texte des 204 archives terminée, le relevé compte
183 index Kiwix et 21 index locaux. Les cinq réglages ont été rejoués sur
sept requêtes, avec les mêmes archives, le même tri et le même code que le
passage où 115 archives étaient traitées. Avec le réglage livré, trois
requêtes passent à une couverture complète (ruche, orage, crevaison).
Le résultat sur le tannage reste hors sujet. Les deux relevés sont conservés
dans `results/comparaison-recherche/` sur le labo.

Le relevé de lecture `lecture-fonds-204-indexe.json` a ensuite rejoué les
136 requêtes sur le portail 0.88.1 avec le même fonds et le même tri. Les
136 recherches signalent une couverture complète. Les mêmes 87 requêtes
ouvrent un premier résultat (54 en français et 33 en anglais) et les
mêmes 49 restent sans résultat. La couverture complète signifie que le
moteur a parcouru son périmètre. Les 49 requêtes restent à examiner sous
d’autres formulations et sur le fonds final. Les trois témoins OMS
retrouvent la fiche au deuxième rang en recherche bilingue et en anglais,
et l’écartent avec le filtre Français. En Autonomie, le contrôle
Wiktionnaire sélectionne zéro collection. Dans Autre, il sélectionne une
collection, trouve dix résultats et ouvre le premier.

| Famille de thèmes | Requêtes | Premier résultat ouvert | Aucun résultat |
| --- | ---: | ---: | ---: |
| Autonomie et ressources | 20 | 14 | 6 |
| Alimentation et agriculture | 28 | 15 | 13 |
| Santé et soins | 8 | 4 | 4 |
| Techniques, fabrication et réparation | 32 | 23 | 9 |
| Milieux naturels, déplacement et survie | 14 | 10 | 4 |
| Risques et situations de conflit | 12 | 6 | 6 |
| Connaissances fondamentales et transmission | 14 | 9 | 5 |
| Communication et informatique | 8 | 6 | 2 |

Sur le portail 0.88.2, une actualisation du lecteur a indexé **3 525 vidéos
et huit pistes** alors que l’inventaire avait traité 119 archives sur 122.
Les recherches « couture » et « addition » étaient vides avant l’actualisation.
« Couture » trouve ensuite
Mondial Tissus, « addition » trouve Maître Lucas et « énergie » trouve
C’est pas sorcier. Les trois premiers résultats correspondants s’ouvrent
dans le catalogue et leurs titres sont recherchables. Le lecteur a renvoyé
les 1 024 premiers octets de chaque média avec une réponse HTTP 206.
Le relevé n’a pas
trouvé de transcription pour ces trois vidéos et la recherche vidéo
reste partielle. Les identifiants, les résultats de lecture et les plages
renvoyées se trouvent dans `videos-119-archives.json` et
`lecture-video-extraits-119.json` sur le labo.

Le contrôle des reformulations sur les 204 archives indexées a donné les
résultats suivants avec la 0.88.1. Les quatre premières pistes de chaque
recherche sont conservées dans `reformulations-204-indexees.json`.

| Recherche | Résultat observé |
| --- | --- |
| Mise à la terre | La requête courte place le passage INRS sur la mise à la terre en premier et la page 64 de Victron en troisième. Les deux pages s’ouvrent. Sur la formulation longue du premier relevé, le passage Victron était précédé d’un article sur les colombiers. |
| Tannage | La requête courte retrouve le repère Vikidia en troisième position. Le premier résultat traite de la gélatine en photographie. Aucun manuel de tannage des peaux n’a été confirmé parmi les pistes examinées. |
| Vannerie | Les deux articles français de Low-tech Magazine s’ouvrent et abordent le tressage. Le résultat les affiche en anglais en 0.88.1. |
| Fertilité du sol | Un article MDWiki en anglais s’ouvre en deuxième position. Il explique la fertilité et évoque le compost. Le passage retenu ne fournit pas de plan de permaculture. |
| Isolation fenêtre | Les trois premiers résultats abordent la performance énergétique, les matériaux ou le chauffage sans répondre directement à l’isolation d’une fenêtre. |
| Installer une ruche | Le premier résultat est le repère Wikipédia « Ruche ». Le lecteur l’ouvre. La disponibilité d’un guide d’installation reste à établir. |

Sur les mêmes 204 archives, la recherche « réparer une fuite de tuyau »
renvoyait surtout des pages sur des appareils. Dans le portail 0.89.0,
une discussion du forum de bricolage remonte en premier et son texte
anglais s’ouvre. Le filtre Français testé sur ce forum l’écarte. Les sondages ciblés sur
la fertilité des sols, le cuir et l’outillage de menuiserie montrent que
les trois forums correspondants sont consultables en Savoirs et culture.
Leurs pistes demandent encore une lecture avant d’être retenues.

Avec le portail 0.89.0, 42 formulations ont été testées sur 14 besoins.
Le catalogue de 204 archives est resté stable. Le relevé
`reformulations-prioritaires.json` indique aussi si le texte du premier
résultat s’ouvre et si une transcription est disponible. Cas vérifiés :

| Besoin | Résultat des reformulations |
| --- | --- |
| Calfeutrer une fenêtre | Deux formulations françaises sans résultat. « Weatherstripping windows » retrouve une discussion technique en anglais sur le changement des joints d’une fenêtre. |
| Récupérer l’eau de pluie | La phrase de départ trouve le guide du jardinier. « Récupération eau pluie » fait remonter une page du même sujet. |
| Élever des poules pondeuses | Deux formulations françaises sans résultat. La demande anglaise ouvre la piste générale « Livestock and Animal Management ». Un guide français consacré aux poules reste à repérer. |
| Fabriquer un panier en osier | La phrase précise reste sans résultat. « Vannerie osier » retrouve l’article français de Low-tech Magazine consacré aux objets tressés. |
| Recoudre une déchirure | Les variantes dans les vidéos ramènent des titres de couture sur des patrons et des vêtements. Aucun de ces premiers résultats ne décrit le raccommodage demandé. |
| S’orienter sans boussole | Aucun résultat dans les trois formulations testées. |
| Exercices d’addition au CE1 | Une recherche plus courte retrouve le guide de l’enseignement du calcul. Les requêtes vidéo trouvent des titres de Maître Lucas sur les additions et le calcul mental. |

Le relevé des lacunes indique aussi des sources françaises à examiner. Ces
références n’ont pas été intégrées au manifeste. Les deux liens PDF de l’ADEME
renvoient actuellement une erreur 403 depuis Bazzite. Le PDF de l’Anses sur
l’hygiène en cuisine renvoie une page de contrôle anti-robot. Pour toute
intégration, vérifier l’accès au fichier, l’édition et les droits associés.

| Lacune observée | Contenu de la source à examiner |
| --- | --- |
| Isolation des fenêtres | Choix de rénovation et points à contrôler sur les menuiseries et la ventilation. [Comment isoler sa maison ?, ADEME](https://librairie.ademe.fr/ged/9380/guide-comment-isoler-sa-maison.pdf) |
| Humidité et moisissures | Repérage des causes fréquentes et renouvellement de l’air. [Bien ventiler son logement, ADEME](https://librairie.ademe.fr/cadic/7180/guide-bien-ventiler-logement-202307.pdf) |
| Conservation et hygiène en cuisine | Conseils pour limiter les contaminations et conserver les plats. [Hygiène dans la cuisine, Anses](https://www.anses.fr/fr/article/conseils-dhygiene-cuisine-dix-gestes-simples-prevenir-risques-microbiologiques) |
| Élevage familial | Mesures de prévention pour les détenteurs d’une basse-cour. Pour l’alimentation et l’entretien courant des poules, chercher aussi un manuel d’élevage. [Ministère de l’Agriculture](https://agriculture.gouv.fr/influenza-aviaire-les-mesures-de-biosecurite-pour-les-operateurs-professionnels-et-les-particuliers) |
| Observation du ciel | Repères illustrés pour reconnaître les nuages. [Les différents types de nuages, Météo-France](https://meteofrance.com/meteo-a-z/les-differents-types-de-nuages) |

Les relances documentaires automatisées utilisent une unité transitoire
de type scope pour garder les conteneurs actifs après la fin de la tâche
qui les démarre. Le pilote est resté joignable après un redémarrage
ainsi lancé depuis une tâche courte. Le redémarrage du PC reste à tester.
