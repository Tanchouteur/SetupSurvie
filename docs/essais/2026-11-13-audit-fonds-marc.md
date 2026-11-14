# Fonds réellement présent chez Marc : volume et besoins

**Bilan daté du 13 novembre 2026, Windows, après achèvement du plan documentaire.**
Ce rapport distingue fichiers, accès, recherche et validation du contenu. Aucun
modèle n’a été interrogé et aucun contenu n’a été supprimé.

**Suivi du 14 novembre :** le défaut de recherche décrit ici est corrigé dans le
code 0.1.35 ; voir le [bilan](2026-11-14-recherche-et-conversations.md). Cette
correction est testée sur fixtures, sans nouvelle validation du fonds de Marc.

## Acquisition vérifiée

Le plan contient 181 ajouts pour 753,27 Go ; tous sont reçus. En comptant le
fonds initial, les reçus décrivent **235 fichiers, 753,34 Go : 135 archives ZIM
et 100 fichiers de guides**. Les fichiers existent aux tailles enregistrées.
Les empreintes ont été contrôlées lors de chaque réception ; l’audit ne relit
pas les 753 Go pour refaire une vérification intégrale du disque.

Les 100 fichiers de guides ne sont pas 100 ouvrages indépendants : plusieurs
sont des chapitres du même livre (32 fichiers Where There Is No Doctor,
13 Where There Is No Dentist), ou des fascicules d’une même série.

| Ensemble | Volume | Part du fonds | Lecture du résultat |
| --- | ---: | ---: | --- |
| Gutenberg, toutes sous-collections comprises | 241,56 Go | 32,1 % | Littérature et fonds ancien très large ; ouvrages techniques à identifier individuellement |
| Wikipédia, trois archives | 185,98 Go | 24,7 % | Références générales FR/EN et anglais simplifié ; pas des modes opératoires validés |
| Collections vidéo pédagogiques et thématiques | 174,28 Go | 23,1 % | Khan Academy FR, Maths et tiques, Mic Maths, Nota Bene, C’est pas sorcier, TED, préparation ; volume des archives, pas des seuls fichiers vidéo |
| Alexandria boardgames | 43,05 Go | 5,7 % | Fonds sur les jeux de société ; complément culturel |
| Autres archives et guides | 108,48 Go | 14,4 % | Réparation, encyclopédies spécialisées, dictionnaires, guides et autres collections |

Ces cinq groupes sont exclusifs dans ce tableau. Les PDF/guides seuls occupent
0,785 Go : leur faible taille ne signifie pas une faible valeur pratique.

Langues des fichiers : **242,40 Go français (54 fichiers), 492,18 Go anglais
(167), 18,76 Go multilingues (14)**. Ce classement normalise fr/fra et en/eng ;
il ne signifie pas que tout le contenu multilingue existe intégralement en français.

## Besoins couverts et limites

| Besoin | Présent et observé | Ce qui reste à examiner ou compléter |
| --- | --- | --- |
| Eau et hygiène | Fascicules OMS sur puits, réservoirs, réseaux, traitement, chlore et assainissement | Beaucoup d’anglais ; accès rapide aux procédures appropriées et compréhension à qualifier |
| Alimentation et cultures | USDA conservation, jardin méditerranéen, semences bio, jardin scolaire et micro-jardins FAO, collections jardinage | Élevage, maladies/ravageurs, irrigation et cultures de base : recette pratique détaillée à mener |
| Santé et secours | MSF FR, références françaises de secours, Hesperian médecine/dentaire EN, premiers secours psychologiques, plantes toxiques | Édition, public visé et compétences nécessaires à examiner ; présence ne vaut pas validation clinique |
| Enseignement | Lecture/calcul CP, Sésamath, Khan Academy FR, Maths et tiques, Mic Maths | Organiser des parcours et exercices réellement utilisables selon l’âge ; les guides CP visent aussi les enseignants |
| Réparation et énergie | iFixit, câblage/batteries Victron, INRS soudage et prévention, collections de questions-réponses | Notices des équipements réellement possédés, plans cotés, métrologie, fabrication et entretien approfondis |
| Textile, matériaux, machines, chimie pratique | Quelques références générales et forums ; pas de collection spécialisée locale suffisante établie | Manuels progressifs et procédures concrètes à sélectionner, pas seulement davantage d’encyclopédies |
| Organisation collective | Aucun fichier spécialisé repéré localement par la grille actuelle | Inventaires, comptabilité, règles communes, répartition du travail, conservation des archives |
| Données familiales | Modèle de dossier familial identique au modèle vierge | Notices du matériel, contacts, stocks et procédures propres à la famille restent à renseigner |
| Cartographie | Absente au début de l’audit ; préparation engagée à la demande de Louis | Vérifier séparément fonds PMTiles, relief/lieux et itinéraires ; les 100 % du plan documentaire n’incluent pas ces jeux |

La grille de métadonnées repère notamment des collections LibreTexts sciences,
ingénierie, mesure et organisation absentes de ce PC, ainsi qu’un fonds couture.
Cela donne des candidats à examiner, pas une autorisation de télécharger tous
les candidats ni une preuve que Wikipédia ne traite pas déjà de ces thèmes.
Le catalogue de téléchargement initial précède l’élargissement des thèmes en
0.1.19 ; ses 181 ajouts ne se mettent pas à inclure automatiquement les nouveaux domaines.

## Accès réellement testé

- 101 fichiers indexés, aucun fichier pris en charge manquant dans l’index,
  aucune erreur d’intégrité sur les guides du catalogue vérifiés pendant l’audit.
- 18 cas de recherche/lecture de la recette existante : **17 passent** ; le cas
  cartes échoue avant préparation car aucun fond n’était présent. Les autres
  cas couvrent eau, jardin, semences, enseignement, radio, risques, prévention,
  santé et document familial. Ce n’est pas une validation exhaustive du fond.
- Le catalogue Kiwix sert 135 archives ; aucun livre de l’inventaire n’est non prêt.
  Les métadonnées indiquent **71 archives avec index de texte et 64 sans**.
  Les collections sans index se parcourent directement ; elles ne deviennent pas
  recherchables en plein texte par simple présence sur le disque.
- Une vidéo Khan Academy « Compter de un en un » a été ouverte jusqu’au média
  local : réponse HTTP 206, format WebM et en-tête valide. Lecture humaine,
  son et compatibilité Safari réels restent à essayer.

### Défaut important : recherche générale Kiwix masquée par un rejet multilingue

Un sondage de 12 questions pratiques donne 9 réponses vides dans le portail.
Il serait faux d’en déduire l’absence de toute information correspondante :
la recherche directe, limitée à Wikipédia français, trouve par exemple 818
résultats pour « plomberie », alors que la recherche générale du portail n’en
remonte aucun.

Le serveur Kiwix refuse HTTP 400 une recherche `books.filter.lang=fra` lorsque
la sélection contient des collections multilingues ; le détail indique que des
livres de langues différentes participeraient à la recherche. Le pilote masque
actuellement ce rejet et renvoie les seuls résultats des guides, sans expliquer
la dégradation. La correction du périmètre de recherche et de son signalement
est prioritaire avant de conclure à un manque documentaire ou d’ajouter des Go.
Voir le [contrat de recherche Kiwix](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html#search).
Ce bilan trace le défaut ; il ne prétend pas que sa correction est livrée.

## Ordre conseillé pour la suite

1. Rendre accessibles les fichiers acquis : cartes, recherche Kiwix et accès
   visibles aux vidéos ; contrôler les originaux et la navigation hors ligne.
2. Préparer le relief et les lieux dans un rayon de 25 km autour de Solliès-Ville,
   choix confirmé par Louis ; conserver le fond régional Sud séparément.
3. Sélectionner un petit noyau pratique par besoin, en priorité en français,
   avec sources, dates, prérequis, schémas et exercices. Lire des échantillons.
4. Ajouter les notices et données de la famille, puis tester une recherche réelle
   depuis le téléphone et un usage sans Internet, sans arrêter le réseau distant.
5. Préparer une sauvegarde sur un autre support et tester une restauration isolée.
   Un redémarrage ou une copie sur le même disque ne constitue pas une sauvegarde.

Aucun nettoyage automatique du fonds culturel n’est proposé. La priorité est la
qualité d’accès et les lacunes ciblées ; l’espace libre observé ne justifie pas
de supprimer des acquisitions conservées par Louis.

Les preuves détaillées (reçus, réponses HTTP, indexation, volumes et sondages)
restent dans les diagnostics privés du PC. Les comptes, conversations et traces
réseau personnelles ne sont pas publiés dans Git.


## Complément cartographique acquis pendant cet audit

Les deux fonds sont maintenant présents et vérifiés : Sud 598 803 265 octets,
Solliès-Ville 36 644 630 octets. Le relief et les lieux de Solliès-Ville (25 km)
sont publiés : quatre dalles HGT, **3 582 lieux et 28 842 entrées d’adresses/localités**,
108 698 264 octets pour ce jeu. La présence d’une entrée n’atteste pas une adresse
postale complète. Les deux premiers serveurs Overpass expiraient ; le secours
fixe VK Maps a répondu. Le manifeste conserve la source réelle et les empreintes.
Le guide initial de cartes et les données de relief sont distincts des 235 reçus
documentaires. Leur ajout ne rend pas les calculs d’itinéraires disponibles.


Validation ciblée de la livraison 0.1.33 après intégration de l’interface 0.1.32 :
93 tests exécutés, 91 réussites et deux cas ignorés (liens symboliques sans privilège).
Le script d’installation bloque une fausse réussite si les fonds requis échouent ;
un test distinct vérifie qu’une panne des lieux conserve le relief en signalant
leur absence. Le catalogue figé utilise aussi la nouvelle URL Anses vérifiée,
avec la taille et l’empreinte initiales conservées. Installation complète sur
Windows vierge, Safari réel, redémarrage à froid et calcul d’itinéraires restent
à qualifier séparément.


### Recette Windows après déploiement 0.1.33

Mise à jour terminée, état privé contrôlé et 123 fichiers de l’instantané vérifiés.
Les routes `/`, `/nouveau/`, `/classique/`, `/maquette/` et `/cartes.html` répondent
200 ; la racine sert la nouvelle interface et l’API annonce 0.1.33 sans dégradation.
Deux fonds de carte sont disponibles. Une altitude locale est retournée, une
tuile PNG de relief est calculée hors ligne et la recherche de points d’eau
renvoie des repères locaux. Le suivi confirme 181/181 ajouts et deux fonds séparés.
Ces contrôles HTTP ne remplacent pas une recette visuelle sur téléphone.

Nettoyage autorisé : six dossiers temporaires/essais et copies d’application
en échec ont été supprimés après vérification des chemins, des processus et des
tâches. Volume logique retiré : 4 599 568 717 octets, dont une image de test.
Les sauvegardes de retour arrière, données documentaires et états privés restent
conservés. Le détail des suppressions reste dans les diagnostics du PC.
Windows Update ne signalait pas de redémarrage obligatoire ; des opérations
Firefox en attente ont été relevées. Un redémarrage à froid reste à exécuter,
avec ouverture de session nécessaire au lanceur web configuré.
