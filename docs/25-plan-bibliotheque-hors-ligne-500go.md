# Bibliothèque hors ligne : quoi télécharger avec une enveloppe de 500 Go

État et proposition au **11 novembre 2026**, pour Louis et Marc. Usage retenu :
famille en France, questions en français, sources françaises et anglaises,
coupure d’Internet prolongée, services publics et approvisionnements dégradés,
puis entretien et reconstruction de moyens locaux sur plusieurs années.

**Recommandation : conserver les quatre grandes archives existantes, puis compléter
avec des manuels pratiques, des cartes locales et les notices du matériel possédé.**
Le gain principal viendra de ces compléments et de leur recherche, davantage que
d’une nouvelle encyclopédie généraliste. Préserver les illustrations, tableaux,
formules, index et annexes nécessaires pour agir.

L’objectif « avoir une réponse à toute recherche » devient : couvrir les besoins
essentiels, trouver les documents pertinents et signaler explicitement les lacunes.
Aucune bibliothèque de 500 Go ne garantit une réponse exacte à toute question.
Une information absente, périmée ou uniquement accessible sur Internet doit pouvoir
être distinguée d’une réponse documentée.

Ce fichier est un **plan de sélection et de téléchargement**, pas un téléchargement
effectué ni une modification des scripts. Les volumes des futurs lots sont des
enveloppes de stockage proposées, pas des tailles d’archives vérifiées.

## 1. Ce que les scripts préparent actuellement

Lecture du code, des manifestes locaux et des tailles des fichiers présents sur le
volume `/run/media/louis/SetupSurvie`, le 11 novembre 2026 :

| Ressource | Script qui la télécharge | Édition figée | Taille décimale | Constat |
| --- | --- | --- | ---: | --- |
| Wikipédia français illustré | `scripts/lab_library.py` | `wikipedia_fr_all_maxi_2026-05.zim` | 55,44 Go | Fichier présent ; vérification SHA-256 enregistrée dans le manifeste initial |
| Wikipédia anglais illustré | `scripts/lab_corpus.py` | `wikipedia_en_all_maxi_2026-08.zim` | 127,42 Go | Fichier présent ; manifeste marqué vérifié |
| Wikilivres français | `scripts/lab_corpus.py` | `wikibooks_fr_all_maxi_2026-10.zim` | 1,15 Go | Fichier présent ; manifeste marqué vérifié |
| Wikibooks anglais | `scripts/lab_corpus.py` | `wikibooks_en_all_maxi_2026-10.zim` | 4,74 Go | Fichier présent ; manifeste marqué vérifié |
| **Total des quatre ZIM** | | | **188,75 Go** | **188 748 555 651 octets**, hors fichiers de suivi |

La lecture des manifestes ne constitue pas un nouveau recalcul des empreintes.
Les références sont `results/library-manifest.json` et
`results/corpus-manifest.json` sur le volume, ainsi que le
[bilan du corpus](20-campagne-modeles-contexte-et-corpus.md).

Autres éléments à ne pas confondre avec une bibliothèque spécialisée :

- `scripts/setup.py demo` copie les fixtures de démonstration de la boîte ALPHA ;
  ce ne sont pas des guides de survie. Le dossier local contient trois documents
  de démonstration et leur image SVG.
- Cinq textes ont été extraits des ZIM : loi d’Ohm en français et anglais,
  kilowatt-heure, conservation alimentaire et chapitre anglais de radioamateur.
  Ce sont des extraits du corpus déjà compté, pas cinq nouvelles collections.
- `scripts/setup.py` prépare aussi les composants IA : modèle de conversation,
  embeddings et transcription. Le laboratoire contient sept modèles de comparaison,
  selon le bilan existant. Leurs poids occupent de l’espace sans remplacer les sources.
- Le lanceur standard ne télécharge pas automatiquement les quatre ZIM ; les scripts
  de laboratoire sont distincts de l’installation chez Marc.
- `scripts/pilot_kit.py export-lab` **omet Wikipédia anglais par défaut** : il faut
  l’option `--english-wikipedia` pour inclure cette archive. Contrôler le manifeste
  du kit livré, même si le laboratoire possède tous les fichiers.

**Lacunes actuelles :** aucun lot dédié de santé/secourisme, eau/assainissement,
agriculture, réparation, cartes, enseignement ou notices locales n’est automatisé
par ces scripts. Wikipédia en parle, mais ne remplace pas une sélection de manuels
complets et adaptés au terrain.

## 2. Répartition proposée : 500 Go pour le système utilisable

Hypothèse prudente : les **500 Go incluent les données, les logiciels, les modèles,
les index et une marge libre**. Un Go vaut ici 1 000 000 000 octets ; 500 Go valent
environ 465,7 Gio. Si les 500 Go ne concernaient finalement que les documents,
conserver cette sélection en premier et élargir après mesure réelle.

| Lot | Plafond proposé | Ce que l’on y met |
| --- | ---: | --- |
| A — Encyclopédies et Wikilivres existants | 189 Go | Les quatre ZIM actuels, arrondi de budget |
| B — Vie quotidienne, santé, eau, alimentation, risques | 45 Go | Guides illustrés spécialisés et fiches imprimables |
| C — Cultures, élevage, biodiversité utile | 20 Go | Manuels, atlas régionaux, maladies et semences |
| D — Réparation, énergie, construction et communications | 25 Go | Manuels techniques, schémas, fiches et collections ciblées |
| E — Cartographie et orientation | 45 Go | France et voisinage utile, détails régionaux et lecteur |
| F — Éducation, langues et culture | 20 Go | Manuels, exercices corrigés, dictionnaires, livres |
| G — Dossier local et familial | 6 Go | Notices exactes, plans, inventaires et documents privés |
| H — Vidéos pédagogiques sélectionnées | 10 Go | Gestes difficiles à comprendre sur une image fixe |
| **Sous-total documentaire** | **360 Go** | **Environ 171 Go à ajouter à la base actuelle** |
| Modèles IA et auxiliaires | 45 Go | Sélection utile, embeddings, transcription et éventuel OCR |
| Logiciels, images de conteneurs, outils de restauration | 20 Go | Paquets et dépendances nécessaires hors ligne |
| Index de recherche, OCR et métadonnées | 30 Go | Index reconstruisibles et textes dérivés sélectionnés |
| Espace libre de fonctionnement et de mise à jour | 45 Go | Fichiers temporaires, journaux, renouvellement de petits lots |
| **Total** | **500 Go** | **455 Go occupés au maximum dans ce plan** |

Ces enveloppes ne sont pas des objectifs à remplir : un ensemble de PDF utile
peut peser beaucoup moins. Réaffecter seulement après inventaire des tailles.
Les lecteurs cartographiques sont comptés avec leurs logiciels dans le lot
logiciel ; les données des cartes restent dans E.

Le budget de 45 Go de modèles suppose de sélectionner les modèles de production,
pas de conserver indéfiniment tous les candidats de recherche. Mesurer les blobs
partagés pour éviter de compter plusieurs fois le même fichier. Le plan ne demande
aucune suppression immédiate du laboratoire.

Attention aux mises à jour : **45 Go libres ne suffisent pas à remplacer en parallèle
le ZIM anglais de 127 Go**. Préparer les gros remplacements sur un support externe,
les vérifier puis les basculer ; prévoir une sauvegarde externe distincte.
Une deuxième copie de toute la bibliothèque n’entre pas dans ces 500 Go.

Le laboratoire utilise actuellement une image plafonnée à **590 Go** dans
`scripts/linux_lab.py`, issue du précédent cadre de 600 Go. Ce document fixe une
cible de contenu à 500 Go ; il ne réduit pas ce volume et ne modifie pas son système
de fichiers. Un éventuel plafond technique à 500 Go devra être traité séparément.

## 3. Catalogue recommandé et ordre de priorité

**P0 :** indispensable avant de considérer la machine prête pour une crise.
**P1 :** autonomie sur plusieurs mois et entretien des équipements.
**P2 :** approfondissement, transmission et confort sur plusieurs années.
Les lots peuvent contenir plusieurs priorités ; télécharger leurs parties P0 d’abord.

Les liens ci-dessous sont des points d’entrée chez les producteurs. Lorsqu’un ZIM
est envisagé, choisir l’édition disponible au [catalogue Kiwix](https://browse.library.kiwix.org/),
puis figer son URL, sa taille et son empreinte. L’accès automatisé au catalogue a
rencontré une confirmation anti-robot lors de cette recherche : aucune liste actuelle
de ZIM supplémentaires ni leur taille n’est donc annoncée comme vérifiée ici.

### Lot A — Socle général : conserver l’existant

- **P0 :** les quatre archives FR/EN, avec leurs images et index internes.
- **P1 :** dictionnaires français, anglais et bilingues, vocabulaire technique,
  unités, conversions, symboles, tables mathématiques. Chercher les éditions de
  Wiktionnaire/Wiktionary au catalogue ; préférer un dictionnaire exploitable
  localement plutôt qu’une nouvelle encyclopédie qui répète Wikipédia.
- **P2 :** autres collections Wikimedia seulement si elles apportent une couverture
  identifiée, par exemple des cours structurés ou des textes de référence.

### Lot B — Santé et besoins immédiats : enveloppe de 45 Go

Répartition indicative interne : santé 12 Go ; eau/hygiène 6 Go ; alimentation
6 Go ; habitat/vie quotidienne 8 Go ; organisation 5 Go ; soutien psychologique
3 Go ; risques 5 Go. Ces sous-enveloppes incluent les images et annexes.

| Priorité | À télécharger | Couverture attendue et source |
| --- | --- | --- |
| P0 | Référentiels français de premiers secours, fiches de gestes et logigrammes | Éditions proposées par la [Sécurité civile](https://www.securite-civile.interieur.gouv.fr/documentation/secourisme-et-associations/secourisme-references-techniques-nationales.html), avec séparation citoyen / secouriste formé |
| P0 | Guides cliniques et médicaments essentiels MSF, en français | [MSF Medical Guidelines](https://medicalguidelines.msf.org/en) : conserver date et public visé ; le site signale que le PDF de certains guides n’est pas à jour par rapport au contenu en ligne |
| P0 | Santé familiale en ressources limitées | [Hesperian Health Guides](https://store.hesperian.org/) : sélectionner notamment *Where There Is No Doctor*, santé des femmes, enfants, santé dentaire et handicap ; obtenir les éditions numériques autorisées, éventuellement achetées |
| P0 | Eau, assainissement et hygiène en urgence | Les [notes techniques OMS/WEDC](https://www.who.int/teams/environment-climate-change-and-health/water-sanitation-and-health/environmental-health-in-emergencies/technical-notes-on-wash-in-emergencies) couvrent notamment puits, réservoirs, traitement, besoins en eau et déchets ; prendre les PDF et leurs figures |
| P0 | Organisation d’un foyer ou d’un petit collectif sans services fiables | [Manuel Sphère en français](https://spherestandards.org/fr/read-download-order/) : eau, alimentation, abris et santé ; extraire aussi des index de repérage par problème |
| P0 | Conservation des aliments et recettes de référence | [USDA Complete Guide to Home Canning, via NCHFP](https://nchfp.uga.edu/resources/category/usda-guide), toutes les parties utiles, complétées par des fiches françaises sélectionnées |
| P1 | Techniques simples adaptées aux moyens disponibles | Sélection de fiches du [centre de connaissances Practical Action](https://practicalaction.org/learning/knowledge-centre/) : conserver les documents techniques, pas tout le fonds institutionnel |
| P1 | Santé communautaire et apprentissage des soins | Ressources [Hesperian et HealthWiki](https://en.hesperian.org/hhg/New_Where_There_Is_No_Doctor:How_to_Use_the_HealthWiki), en conservant les chapitres complets, pages de médicaments et renvois ; certaines parties du nouveau livre restent en développement |

**Liste de couverture à vérifier avant de clore ce lot :**

- Premiers secours, plaies, brûlures, traumatismes, chaleur, froid, intoxications,
  prévention des infections ; reconnaître les limites d’une prise en charge locale.
- Enfants, grossesse et nouveau-nés ; personnes âgées, handicap, dépendance,
  maladies chroniques, santé dentaire, lunettes et appareillages.
- Notices officielles des médicaments effectivement conservés, principes actifs,
  conditions de stockage et documentation du matériel de soin possédé.
- Captage, transport, stockage, filtration et désinfection de l’eau ; entretien des
  installations ; séparation des risques microbiologiques et chimiques.
- Toilettes, eaux usées, déchets, lavage, linge, hygiène menstruelle,
  lutte contre les nuisibles, prévention des épidémies.
- Nutrition par âge, allergies, menus avec stocks limités, cuisson économe,
  conservation sans froid, séchage, fermentation et conserves avec procédés documentés.
- Chauffage, ventilation, monoxyde de carbone, incendie, abri temporaire,
  isolation, protection contre pluie/chaleur/froid.
- Sommeil, stress, deuil, soutien des enfants, entraide, médiation, prévention
  des violences et accompagnement des personnes vulnérables.
- Inondations, tempêtes, canicule, feux, séisme selon la zone, risques industriels,
  chimiques et radiologiques : fiches des organismes compétents, consignes locales
  et documents publics de la préfecture/mairie.
- Organisation des stocks, rationnement, rotation, partage des tâches, accueil,
  évacuation, communication et fiches papier si le serveur est éteint.

Les références professionnelles doivent être identifiables comme telles.
Pour santé, conserves et eau potable, conserver la procédure complète, ses conditions
et sa date : un extrait isolé peut supprimer une condition essentielle.

### Lot C — Produire et connaître le vivant : enveloppe de 20 Go

| Priorité | À télécharger | Sélection pratique |
| --- | --- | --- |
| P0 | Potager et production de calories en climat français | Sol, rotations, semis, calendrier régional, pommes de terre, céréales, légumineuses, stockage des récoltes ; guides de terrain illustrés |
| P1 | Semences et reproduction | Ressources de la [FAO sur les semences](https://www.fao.org/seeds/en/) et [guide de séchage et stockage référencé par la FAO](https://www.fao.org/family-farming/detail/en/c/1709911/) ; conserver le document source complet |
| P1 | Eau et fertilité au jardin | Irrigation, récupération de pluie, compost, amendements, analyse du sol, serre, pépinière, greffe, taille et arboriculture |
| P1 | Petits élevages | Poules, lapins et autres espèces réellement envisageables ; logement, alimentation, reproduction, biosécurité et manuels vétérinaires de référence |
| P1 | Reconnaissance du vivant local | Flores régionales, clés botaniques, photos des caractères distinctifs, noms scientifiques et synonymes ; ne pas compter une simple galerie de photos comme un guide complet |
| P0 | Toxicité et confusions des plantes/champignons | Guides modernes régionaux avec clés et espèces ressemblantes, plus [documents de prévention et toxicovigilance](https://sante.gouv.fr/sante-et-environnement/denrees-alimentaires/article/prevention-des-intoxications-par-les-champignons) et [fiches du centre antipoison de Lille](https://www.cap.chu-lille.fr/champignons-syndromes/) |
| P2 | Apiculture, transformation et activités forestières | Fiches d’entretien, maladies, outils manuels, bois de chauffage, sciage et affûtage ; compléter selon les activités locales |

Pour les guides agricoles français, rechercher les publications des organismes
agronomiques, chambres d’agriculture et associations spécialisées, puis sélectionner
des éditions téléchargeables avec droits identifiés. C’est une recherche éditoriale
à faire, pas un catalogue de fichiers déjà validé.

La comparaison des champignons est un besoin explicite du projet. Télécharger
les pages décrivant les confusions et les limites d’identification, autant que les
photos des espèces comestibles. Une ressemblance dans un atlas ou une réponse IA
ne vaut pas validation de consommation ; cette limite doit apparaître dans les résultats.

### Lot D — Maintenir, réparer et reconstruire : enveloppe de 25 Go

| Priorité | À télécharger | Sélection pratique et source |
| --- | --- | --- |
| P0 | Notices et schémas des équipements de la maison | Pompe, filtre, réchaud, poêle, batterie, onduleur, panneaux, chargeur, groupe, vélo, outils ; priorité à la référence exacte du fabricant |
| P1 | Guides de réparation illustrés | [iFixit](https://www.ifixit.com/Guide), en priorité familles d’appareils possédées ; vérifier les modalités d’export et la licence, ou chercher un ZIM adapté |
| P1 | Techniques à faibles moyens | [Appropedia](https://www.appropedia.org/Welcome_to_Appropedia) : eau, énergie, construction, outils ; le projet indique un accès hors ligne via Kiwix, édition à sélectionner |
| P1 | Électricité autonome | Batteries, production solaire, câblage, protections et diagnostic ; [Wiring Unlimited de Victron](https://www.victronenergy.com/media/pg/The_Wiring_Unlimited_book/en/index-en.html), notices exactes des équipements et brochures [INRS sur le risque électrique](https://www.inrs.fr/media.html?refINRS=ED%206187), avec date d’édition |
| P1 | Plomberie et hydraulique | Joints, raccords, pompes, vannes, fuites, pression, débits, matériaux, schémas de réseaux et entretien |
| P1 | Bâtiment et artisanat | Menuiserie, charpente, couverture, maçonnerie, isolation, couture, cordonnerie, cordage, nœuds, affûtage, métrologie et travail des métaux |
| P1 | Mobilité et mécanique | Vélo, remorque, petits moteurs et véhicules réellement présents ; manuels d’atelier, pièces, lubrifiants et diagnostics |
| P1 | Radio et communications locales | Manuels des radios présentes, antennes, propagation, dépannage, procédures et plans de communication ; archiver les règles officielles applicables avec leur date |
| P1 | Informatique de secours | Réseau local, adressage, Wi-Fi sans Internet, Linux/Windows, stockage, récupération et restauration ; documentation correspondant aux versions livrées |
| P2 | Questions techniques spécialisées | Candidats Kiwix : sélections Stack Exchange sur électronique, bricolage, mécanique et radio ; vérifier disponibilité, volume, qualité et doublons avant ajout |

Ajouter des tables d’unités et de matériaux, abaques, visserie, roulements,
connecteurs, câbles et composants usuels. Les fiches techniques des pièces présentes
et les vues éclatées sont souvent plus utiles qu’un énorme fonds de discussions.
Conserver les modèles numériques utiles uniquement s’ils sont accompagnés des plans,
matériaux, tolérances et logiciels de lecture nécessaires.

### Lot E — Savoir où aller : enveloppe de 45 Go

Commencer par la France et les zones de déplacement plausibles de Louis et Marc.
Leurs communes et éventuels lieux de repli restent à renseigner ; ne pas inventer
une localisation à partir d’un exemple de document préfectoral.

| Priorité | À télécharger | Forme attendue |
| --- | --- | --- |
| P0 | Carte vectorielle France | Routes, chemins, localités, bâtiments et repères ; les [extraits Geofabrik](https://download.geofabrik.de/europe.html) fournissent des données OSM, à transformer ou accompagner d’un lecteur compatible |
| P0 | Cartes détaillées autour des lieux de vie et de repli | Zones proches et itinéraires alternatifs ; relief, courbes de niveau, hydrographie et ponts ; exporter aussi des cartes PDF imprimables |
| P1 | Relief et topographie régionale | Sélection de données [IGN du RGE](https://www.data.gouv.fr/datasets/referentiel-a-grande-echelle-rge), résolution adaptée au volume ; garder le rendu utilisable, pas seulement les fichiers bruts |
| P0 | Risques et informations locales | DICRIM communal et DDRM départemental publics, cartes d’inondation et autres risques ; archiver les fichiers pertinents de la mairie/préfecture |
| P1 | Pays frontaliers et grands itinéraires utiles | Extraits régionaux, sans doublonner France entière + Europe entière ; élargir selon les besoins |
| P1 | Orientation sans électronique | Lecture de carte, boussole, coordonnées, échelles, déclinaison et observation du ciel ; fiches imprimables |

Répartition initiale : 10 Go pour fond vectoriel et données de navigation, 25 Go
pour détails/relief régionaux, 5 Go pour le voisinage et 5 Go pour cartes PDF et
documents de risques. Ajuster selon les fichiers réels ; aucune couverture France
entière en très haute résolution n’est promise avec ce budget.

Un `.osm.pbf` n’est pas une application cartographique prête à consulter. Préparer
avant la coupure le rendu, les styles, polices, symboles, index de lieux et éventuel
graphe de routage. Tester les fonctions retenues dans le lecteur réellement livré.
Privilégier des exports prévus pour l’usage hors ligne ; un service WMS/WMTS en
ligne ne constitue pas une carte sauvegardée.

Les points d’eau, magasins, ponts et structures de soins d’une carte sont des
**repères datés**, sans garantie de fonctionnement ni de potabilité en crise.

### Lot F — Apprendre, comprendre et transmettre : enveloppe de 20 Go

- **P1 :** lecture, écriture, calcul, sciences, histoire/géographie, du primaire au
  lycée ; exercices et corrections pour pouvoir apprendre sans professeur connecté.
- **P1 :** mathématiques pratiques, physique, chimie, biologie et bases d’ingénierie ;
  les [manuels OpenStax](https://openstax.org/faq) existent en PDF téléchargeables.
- **P1 :** dictionnaires FR/EN et vocabulaire médical, mécanique, botanique et
  agricole ; ne pas doubler les mêmes dictionnaires s’ils sont déjà dans A.
- **P2 :** contenus pédagogiques par niveau, avec progression et exercices.
  [Kolibri](https://kolibri.readthedocs.io/en/latest/faq.html) permet le transport
  hors ligne d’installateur et de chaînes : choisir quelques chaînes et tester
  l’export/import complet ; le serveur n’est pas actuellement intégré à SetupSurvie.
- **P2 :** littérature, histoires pour enfants, jeux, musique écrite, arts,
  philosophie et histoire ; [Project Gutenberg](https://www.gutenberg.org/) propose
  des livres téléchargeables. Sélectionner les titres diffusables en France ;
  le statut de domaine public américain ne suffit pas à déterminer le statut local.

Proposition interne : 8 Go de manuels/exercices, 4 Go de langues/références et
8 Go de lecture/culture. Les vidéos éducatives vont dans H. Éviter de dupliquer
une même vidéo en ZIM, chaîne Kolibri et MP4.

### Lot G — Le dossier qui rend la bibliothèque utile chez nous : 6 Go

Une partie doit être **créée ou numérisée**, elle ne se télécharge pas sur Internet.

- **P0 :** liste des appareils avec marque, modèle, numéro de pièce, notices,
  entretien, consommables, schémas et pièces de rechange compatibles.
- **P0 :** plans utiles de la maison, accès, coupures eau/gaz/électricité,
  tableaux, réseaux, réserves, évacuation et points de rendez-vous.
- **P0 :** inventaire alimentaire, eau, énergie, médicaments, semences, outils ;
  modèles imprimables et règles de mise à jour manuelle.
- **P0 :** contacts familiaux et locaux, informations médicales choisies,
  ordonnances et documents administratifs utiles ; espace privé séparé du catalogue
  public. Ne pas exporter ces fichiers dans un kit générique.
- **P1 :** observations du terrain, calendrier local des cultures, rendements,
  pannes résolues et retours d’expérience avec date et auteur.
- **P0 :** guide papier « démarrer et chercher », avec accès sans IA et procédure
  si le serveur, le routeur ou le disque tombe en panne.

### Lot H — Montrer les gestes : enveloppe de 10 Go

**P1/P2 :** vidéos courtes de réparation, greffe, affûtage, couture, entretien,
orientation et gestes de secourisme provenant de formateurs/organismes identifiés.
Choisir les fichiers téléchargeables autorisés, conserver sous-titres, transcription,
date et source. Le texte permet de rechercher un passage avant de regarder la vidéo.

Privilégier une définition lisible pour le geste, sans télécharger systématiquement
la 4K ni des chaînes entières. Une vidéo de démonstration complète un manuel ;
elle doit être visionnable sans compte ni lecteur distant.

## 4. Ce qu’il faut aussi télécharger pour que les connaissances restent accessibles

Dans les 20 Go de logiciels et les 45 Go de modèles :

- Versions exactes de Kiwix/lecteurs, du portail, de l’assistant, de leurs images
  de conteneurs, dépendances et documentation de déploiement.
- Installateurs adaptés aux machines cibles, paquets Python nécessaires,
  pilotes utiles et outils de diagnostic/récupération ; vérifier le volume réel.
- Lecteur de PDF/EPUB et lecteur cartographique hors ligne, avec leurs ressources.
- Modèle IA principal et solution légère de repli, choisis après les essais ;
  embeddings et transcription déjà prévus, sans télécharger tous les modèles possibles.
- OCR et données linguistiques FR/EN si l’on ajoute des scans ; convertisseurs
  de formats et polices nécessaires aux formules et aux cartes.
- Outils de contrôle des empreintes, manifestes, export/import et restauration.

**Point bloquant actuel :** le kit pilote documente encore Python, Docker Desktop,
Ollama et le pilote NVIDIA comme prérequis Windows. Posséder `images.tar` ne
garantit donc pas une réinstallation complète hors ligne sur un PC vierge.
Archiver les prérequis autorisés et tester réellement ce scénario.

## 5. Télécharger ne suffit pas : rendre chaque lot trouvable

### Limites constatées dans le code actuel

`pilot/library.py` combine un index textuel des guides et des recherches Kiwix par
langue. Il ne constitue pas à lui seul un moteur sémantique exhaustif de tous les ZIM.
L’essai bilingue sur quelques documents décrit dans le bilan ne prouve pas la
couverture de centaines de gigaoctets.

- L’indexeur ignore les guides de **plus de 20 000 000 octets**.
- Il limite le texte conservé à **500 000 caractères par guide**.
- Les PDF sont lus par extraction de texte avec `pypdf`, sans OCR intégré dans
  cette fonction ; un scan peut rester sans contenu recherchable.
- L’extraction des guides HTML conserve le texte ; le résultat documentaire d’un
  guide ne remonte pas actuellement ses images comme pièces associées.
- Une recherche française envoyée telle quelle à une archive anglaise ne garantit
  pas de retrouver son vocabulaire technique anglais.

Il faudra donc préparer des textes OCR et/ou des divisions par chapitre avec
renvoi au document original, vérifier leur couverture, gérer les gros documents
et relier pages, figures et tableaux. Conserver l’original complet : découper
l’index ne doit pas supprimer le contexte du manuel.

### Recherche cible

1. Catalogue commun par domaine, langue, titre, édition et public visé ; accès
   direct aux collections et dossiers même si l’IA est arrêtée.
2. Recherche exacte et plein texte sur ZIM et guides ; synonymes français,
   noms scientifiques, références de pièces et équivalents anglais.
3. Recherche sémantique sur les manuels prioritaires et passages utiles ;
   mesurer la taille de l’index avant d’étendre aux deux Wikipédia.
4. Résultats avec titre, édition, page/section, image ou tableau utile et lien
   local ouvrable. La citation doit renvoyer à la bonne édition.
5. Présentation claire de la couverture : source trouvée, source ancienne,
   contradiction, ou information absente du fonds.

Les 30 Go d’index sont une réserve, pas une estimation validée du coût d’indexation
intégrale. Utiliser d’abord les index internes des ZIM et indexer finement les
manuels P0/P1 ; ne pas extraire toutes les pages uniquement pour remplir un index.

## 6. Préparer des téléchargements reproductibles

Pour chaque ressource retenue, le futur manifeste devra enregistrer :

| Champ | Usage |
| --- | --- |
| Identifiant, titre, domaine, priorité et public | Savoir pourquoi le document est là et à qui il s’adresse |
| Producteur, URL source et URL du fichier | Retrouver l’origine ; une page catalogue n’est pas le fichier |
| Langue, édition, date de publication et de collecte | Identifier ce qui peut être périmé |
| Format, taille exacte en octets et SHA-256 | Planifier, reprendre et vérifier ; distinguer empreinte publiée et calculée localement |
| Licence, attribution et conditions de redistribution | Séparer usage personnel, partage familial et diffusion du kit |
| Chemin local, documents annexes et lecteur requis | Ouvrir réellement hors ligne, avec images et styles |
| État du texte/OCR, index et contrôle de lecture | Distinguer fichier présent, lisible et retrouvable |
| Zone géographique et matériel concerné | Écarter les conseils ou notices hors contexte |

Ordre conseillé pour l’implémentation future :

1. Créer un manifeste unique pour les quatre ZIM existants et les ressources
   sélectionnées, en distinguant prévu / en cours / vérifié / indexé / testé hors ligne.
2. Acquérir un petit échantillon de chaque source, vérifier licence, contenu,
   images et consultation sans Internet avant un téléchargement massif.
3. Télécharger d’abord les parties P0 des lots B, C, D, E et G. Prévoir un premier
   ajout de **10 à 30 Go**, selon les tailles effectivement sélectionnées.
4. Ajouter les ressources P1 puis P2 ; calculer avant chaque transfert l’occupation
   finale et le pic temporaire, y compris conversion, index et copie d’export.
5. Réutiliser la reprise et les contrôles des scripts ZIM ; ne publier qu’après
   vérification. Pour un fichier sans empreinte éditeur, conserver au moins son
   empreinte locale et la provenance, sans appeler cela une validation éditoriale.
6. Documenter les formats nouveaux et leur export : cartes et chaînes Kolibri
   ne sont pas prises en charge simplement parce que Kiwix accepte des ZIM.
7. Tester le kit chez Marc : son manifeste doit correspondre à la sélection,
   notamment pour Wikipédia anglais. Ne pas créer une seconde copie de 360 Go
   dans le même volume sous prétexte d’export.

Privilégier les fichiers et exports proposés par les producteurs. Un site lisible
gratuitement n’autorise pas automatiquement un miroir complet ou la redistribution.
Les éditions achetées et documents privés restent identifiés séparément.

## 7. Vérifier que les questions importantes ont une réponse

Constituer une matrice d’au moins **100 questions réelles**, réparties entre les
domaines, avec des formulations françaises simples, des synonymes, quelques
références techniques exactes et des sources uniquement anglaises.
Les exemples ci-dessous servent à choisir les documents, pas à fournir des procédures.

| Question représentative | Preuve documentaire attendue |
| --- | --- |
| Comment gérer l’eau si le réseau s’arrête ? | Manuel WASH complet, limites du traitement et schéma de stockage |
| Que dit le guide sur l’eau contaminée par un produit chimique ? | Source distinguant ce problème de la contamination microbienne |
| Où trouver la fiche d’un médicament de notre stock ? | Notice correspondant au produit, date et document original |
| Quel manuel consulter pour un enfant malade ? | Source adaptée à l’âge et identification des situations nécessitant un soignant |
| Comment conserver une récolte sans réfrigérateur ? | Procédé documenté, conditions et tableaux complets |
| Que semer ici et comment garder des graines ? | Guide régional et chapitre sur reproduction/stockage |
| Quels caractères distinguent deux espèces ressemblantes ? | Clé et photos des caractères, confusions et limites explicites |
| Pourquoi notre pompe ne débite plus ? | Notice de la bonne référence, schéma et tableau de diagnostic |
| Où trouver le fusible et le câblage du système solaire ? | Plan de l’installation et documentation des composants présents |
| Quel trajet à pied rejoint notre point de rendez-vous ? | Carte locale ouvrable, itinéraire et alternative imprimable |
| Comment réparer le vélo ou le poêle que nous possédons ? | Manuel de la bonne famille et liste de pièces |
| Comment un enfant peut-il poursuivre les fractions ? | Cours, exercices et corrections disponibles hors ligne |
| Que faire si l’IA ou le serveur ne démarre plus ? | Accès direct aux documents et guide de restauration local/papier |
| Peut-on connaître l’état actuel d’un pont ou d’une pharmacie ? | Réponse indiquant que l’archive ne fournit pas cette information en temps réel |
| Comment retrouver une information publiée après notre dernière collecte ? | Lacune signalée, sans invention de source |

Pour chaque question, relever : ressource attendue, résultat de recherche, page
exacte, lisibilité du tableau/illustration, fonctionnement sur téléphone et état
de la couverture. Faire d’abord cette recette documentaire **sans génération IA**,
puis contrôler séparément la fidélité de la réponse de l’assistant lorsque les
calculs sont autorisés.

Critère proposé : chaque besoin P0 possède au moins une référence complète,
lisible et retrouvable dans la version livrée. Une lacune connue demeure marquée
comme telle ; le nombre de gigaoctets ne vaut pas résultat de recette.

## 8. Ce qui passe après les priorités

- Une autre encyclopédie très proche des deux Wikipédia déjà présents.
- Commons entier, planète OSM entière, orthophotos nationales haute résolution
  ou collections vidéo intégrales : sélectionner les zones et sujets utiles.
- Accumulation de modèles IA presque équivalents au détriment des manuels et cartes.
- Dumps de forums sans sélection, provenance ou contrôle de couverture.
- Très vieux manuels médicaux ou techniques utilisés comme références actuelles ;
  les ouvrages historiques utiles restent identifiés comme historiques.
- Uniquement des fiches « survie » courtes sans explication, schéma ni conditions
  d’application ; préférer les manuels complets accompagnés de fiches de repérage.

## 9. Entretien de la réserve

À chaque mise à jour : figer les éditions, vérifier les empreintes, contrôler les
renvois locaux, garder un journal des changements et rejouer les recherches P0.
Prévoir une revue semestrielle de santé/secourisme, cartes, risques et logiciels,
et une revue annuelle des fonds plus stables ; adapter si un producteur publie
une correction importante.

Avant de remiser une machine : démarrage sans WAN, consultation de plusieurs
manuels illustrés, recherche FR/EN, affichage des cartes, export d’une fiche
imprimable et restauration depuis un support séparé. L’épreuve utile est de
retrouver une information au moment voulu, avec les moyens réellement disponibles.
