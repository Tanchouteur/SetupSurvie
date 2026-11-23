# Architecture — recherche et index

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Socle de recherche Kiwix

Depuis 0.1.35, `pilot/library.py` sélectionne explicitement les archives par
identifiant Kiwix ou par nom en repli. Les lots sont homogènes par langue et les
archives multilingues ou sans langue connue restent isolées. Un lot refusé est
retenté archive par archive, sans masquer les succès reçus. Cela n’implique pas
que chaque archive multilingue soit prise en charge en plein texte par Kiwix.

`/api/search` et l’outil `search_library` transmettent `coverage`, avec les archives
interrogées, en échec ou non interrogées. Le compteur historique `without_fulltext`
désigne les tags d’index négatifs, pas une preuve physique d’absence d’index.
Depuis 0.1.36, ces tags servent à prioriser les sondages ; titres et reformulations
ont aussi leurs compteurs. Les recherches limitées aux favoris ou traductions
gardent leur périmètre. Le classement commun remplace l’alternance guide/article
utilisée en 0.1.35. Les états décrivent une recherche, pas une validation ou une lecture.

## Consolidation documentaire 0.1.36

`pilot/retrieval.py` prépare la requête, le périmètre et le classement lexical
commun. `library.search` rassemble des candidats FTS et Kiwix avant classement,
regroupe les pages et transmet `coverage`. `collection` filtre séparément les
archives. Les titres sont interrogés dans quatre collections prioritaires ;
32 appels plein texte au plus sont autorisés, avec trois requêtes simultanées
et dix secondes pour l’ensemble après le catalogue (trois secondes au plus).
Les reformulations Kiwix utilisent des recherches littérales distinctes, après
la première passe, et non une syntaxe OR supposée. Les métadonnées d’index
ordonnent les sondages sans exclure les archives.

**Complément 0.36.1, 17 novembre 2026 :** les mots hors du vocabulaire explicite
reçoivent des variantes de nombre bornées sur des tokens entiers. Les identifiants
alphanumériques et des formes ambiguës restent distincts ; aucun index n’est
réécrit. Le même plan sert au filtrage et à la sélection des passages lus par
l’assistant. En recherche de titres, la formulation initiale est essayée d’abord ;
au plus quatre variantes sont tentées si aucun titre ne couvre le sujet. Quatre
collections restent ciblées, avec le même budget global. `title_requests` et
`title_refinement_requests` complètent la couverture et l’export de performances.
Voir le [bilan et les limites](../essais/2026-11-16-recherche-formes-de-mots.md).

`engine.document_request` prépare certaines demandes documentaires avant le
premier appel au modèle, puis conserve les outils pour affiner. Les caches sont
propres à une réponse et au périmètre, pas un index sémantique global. Le contexte
est compacté sans modifier l’historique stocké. `engine.PROGRESS` expose un suivi
éphémère par demande, renvoyé seulement après contrôle du propriétaire dans
`/api/jobs/{id}` ; aucun schéma de base n’est changé.

La vérification depuis le site utilise uniquement santé et recherche en GET,
et produit un rapport côté navigateur. Elle ne proclame pas le fonds validé.
Le [bilan](../essais/2026-11-14-moteur-recherche-utile.md) détaille le vrai Kiwix
sur archives générées et les limites de transfert au fonds de Marc.

## Index complémentaires — 0.3.0

Les ZIM restent en lecture seule. `scripts/index_archives.py` extrait leur texte avec libzim 3.13.1 dans un environnement hôte optionnel, publie un SQLite FTS5 par archive sous `state/pilot/archive-index` et reprend les curseurs validés. Le pilote requête ces fichiers en lecture seule en parallèle de Kiwix ; les requêtes n’importent pas libzim. Les opérations passent par les mêmes droits Famille, service de contrôle, verrous et suivi que les préparations documentaires. Voir le [guide](../utilisation/indexation-archives.md).

## Préparation automatique et catalogue — 0.4.0

Les producteurs de fichiers vérifiés écrivent la file `catalog/search-index-queue.json` sous verrou. Le contrôleur lance un seul travail documentaire lorsque publication et téléchargement sont libres. Les pauses volontaires et interruptions restent explicites ; les reports horaires et le mode jeu gardent leur logique propre. Le manifeste cumulatif des index conserve les résultats des lots précédents. Le catalogue Kiwix utilise un cache court partagé entre appels et un instantané daté, sans masquer les erreurs derrière une liste vide valide. Les diagnostics exposent des codes sûrs, pas les corps HTTP ni les secrets.

## Référence de recherche et lecture — 0.5.0

Le contrôle complet lit une référence JSON statique versionnée ; ses sources
attendues fictives restent dans les tests, sans être imposées à la bibliothèque
réelle. Les avis de pertinence sont conservés dans le rapport côté navigateur,
sans écriture dans les comptes ni les documents. Le contrôle court reste distinct.
Le lecteur HTTP suit les redirections de contenu à origine et archive identiques,
au plus cinq, sans suivre les catalogues ni les liens externes. Sa réponse conserve
le chemin final pour résoudre les images, tout en préservant l’identifiant demandé.

## Métadonnées corrigibles — 0.6.0

`pilot/catalogue.py` conserve une surcouche JSON versionnée dans `settings`, sous
les clés `catalogue:v1:`. Identité canonique par article ZIM ou document guide,
sans suffixe de page PDF ; révision locale par référence, taille et date de
modification. Une nouvelle révision invalide l’ancien classement humain et les
noms corrigés, sans effacer leur enregistrement avant retour explicite.

Le moteur commun applique les espaces corrigés avant filtrage et transmet le
type/état à l’assistant. Les groupes corrigés filtrent Kiwix et les index SQLite.
Les libellés originaux et identifiants restent inchangés ; l’export ne lit que
les clés de la surcouche et une liste autorisée de champs. Les erreurs de lecture
de métadonnées sont signalées sans supprimer les candidats de recherche globale.

## Corrections de recherche 0.9.1

`pilot/kiwix_queries.py` partage deux sémaphores texte/titres de capacité deux,
regroupe les appels identiques et garde uniquement les réponses valides réussies
pendant quinze secondes (64 réponses, huit millions d’octets au maximum). Le
service annule les appels restants à son arrêt. `library.search_archives` conserve
les causes bornées et ne redécoupe un lot qu’après rejet de sélection 400/404/413.
Le budget du comparatif IA porte sur toute la demande, puis une série de deux
échecs est interrompue. Les nouvelles observations sont numériques ou catégorielles,
sans réponse brute, jeton ni raisonnement privé. Voir le
[bilan](../essais/2026-11-14-corrections-rapports-recherche.md).

## Vérification du lecteur isolé (0.9.2)

`scripts/index_reader_probe.py` reste indépendant de la passerelle Web. Il vérifie
libzim et SQLite FTS5 sans archive ni réseau. `search_index_tools.py` l’appelle
dans le Python dédié avant de publier le marqueur prêt ; `index_archives.py` le
répète avant son pool et enregistre `reader_probe` dans la progression.
Le superviseur retire le marqueur en cas d’échec, y compris pendant sa récupération.
Les erreurs d’archives ont un motif borné sans message natif privé. Voir le
[guide actuel](../utilisation/indexation-archives.md).
Le pool conserve la sélection d’exécutable de CPython : substituer le `pythonw.exe`
du venv Windows empêche son démarrage adapté aux environnements isolés. La recette
exécute le vrai CLI à deux processus dans un venv sans dépendances Web.
La restauration automatique d’une recherche par `navigation.js` attend le résultat
du profil, y compris son repli anonyme, pour éviter les trois requêtes au démarrage.

## Maintenance et écrivains d’index (0.9.3)

`pilot_backup.maintenance` exclut les tâches Web, publications, transferts et
écrivains d’index avant l’arrêt des services. `pilot_update` garde ce contexte
pendant le remplacement et le retour arrière ; sa récupération explicite le reprend.
`index_locks.py` enregistre les verrous par archive avant toute soumission au pool,
et `index_archives.build_one` les détient pendant chaque extraction. La maintenance
acquiert aussi ces verrous pour exclure les processus restants et les départs tardifs.
Les instantanés excluent les `.lease` des états ; le retour arrière conserve les
inodes existants, y compris ceux détenus par son propre contexte de maintenance.

## Ordonnancement et volume des recherches (0.9.4)

`library.search_archives` ordonne les lots entre langues après correction des tags
par les index réels, isole les grosses archives et limite les lots compatibles à
douze. Deux consommateurs prennent les reformulations des collections pratiques
avant les lots généraux restants ; l’échéance est de douze secondes, 32 appels au
maximum. Les titres privilégient la diversité des familles. `kiwix_queries`
annule un appel partagé seulement au départ de son dernier lecteur.
`coverage.local_index` résume les compteurs et diagnostics sans répéter le manifeste
par archive ; l’API d’administration et le rapport d’indexation gardent le détail.
Le cache d’une question de l’assistant réutilise son intention préparée si le modèle
la raccourcit au seul sujet, sans confondre deux actions explicites.

## Index multilingues et traces explicites (0.11.1)

L’extraction distingue `has_fulltext_index` et `kiwix_language_compatible` dans le
manifeste existant. Plusieurs langues ou leur absence nécessitent un complément
SQLite, sans changer son format. Toute archive `ready` est interrogée localement ;
une archive incompatible non préparée reste signalée et ne consomme pas d’appel
natif voué au refus. Une métadonnée `mul` unique n’est pas exclue par son nom.
`/api/search?diagnostic=true` ajoute au maximum quarante événements et les
compléments nécessaires. Seul le contrôle explicite de recherche le demande ;
les réponses normales aux outils IA n’embarquent pas ces journaux. Les délais
rapportés incluent l’attente client et ne sont pas une mesure CPU du serveur.

## Recherche progressive et cache — 0.13.0

`pilot/search_stream.py` diffuse des instantanés SSE sur `/api/search?stream=true`,
à partir du même moteur et des mêmes filtres que le JSON existant. La file garde
uniquement le dernier instantané en attente. La fermeture du flux annule le travail
client. Le budget natif est de 60 secondes sur ce parcours, de 12 sur l’ancien JSON.
`diagnostic=true` utilise également 60 secondes ; le journal reste borné à 40 appels.
Le portail conserve la lecture ouverte et les résultats lors d’un arrêt.

`pilot/search_cache.py` complète les requêtes mutualisées de `kiwix_queries.py` :
SQLite reconstructible sous `state/pilot/cache/search`, réponses valides seulement,
invalidation par état des ZIM/catalogue/manifeste, quotas et réserve disque.
Aucune migration des données privées ni changement d’image tiers. Voir le
[guide d’exploitation](../exploitation/cache-et-recherche-progressive.md).
La traduction et l’indexation des [vidéos locales](../decisions/videos-locales-et-recherche.md)
restent un chantier distinct ; le flux actuel ne cherche pas dans leurs paroles.

Depuis 0.14.1, `catalogue.SearchAnnotations` conserve les annotations des candidats
inchangés pendant une demande et mutualise les révisions par fichier physique,
avec nouvelle vérification à la sélection finale. `retrieval.NormalCache` borne
le réemploi du texte normalisé à 4 096 entrées et 32 Mo de charge textuelle.
Ces caches sont locaux à la demande et ne modifient ni le cache de réponses
Kiwix ni les scores. La sélection utilise le thread attendu par `disk_io`, y
compris lors d’une annulation. `coverage.processing` mesure cette phase seulement ;
le [guide](../exploitation/cache-et-recherche-progressive.md) précise les limites
des durées réelles, du CPU du thread et des compteurs. Les deux voies plein texte,
deux voies titres et jusqu’à huit threads SQLite ne sont pas un parallélisme CPU
illimité ; les contraintes de Kiwix et du stockage restent à mesurer sur la cible.

Depuis 0.14.2, le plafond d’appels plein texte du parcours long s’adapte aux lots
natifs et à leurs deux termes de reformulation au plus, avec plancher 32. Le
parcours court conserve 32 appels. Le budget temporel, les sémaphores et les
conditions de reformulation restent inchangés. `coverage.request_limit` contient
la valeur effective ; les 40 traces bornées ne comptent pas tous les appels lorsque
le plafond dépasse 40. Voir la [reproduction](../essais/2026-11-15-budget-reformulations.md).

Depuis 0.14.3, le bonus d’action distingue aussi quantité, question périphérique
et risques, avec marqueurs de guide, manuel et « how to » au lieu du seul « how ».
Les demandes contextuelles restent cherchables. La comparaison de titre exact
accepte la requête originale normalisée et ses mots de liaison ; ces règles ne
modifient aucune classification humaine. Le [bilan](../essais/2026-11-15-questions-peripheriques-et-titres-exacts.md)
conserve les cas observés et les limites du classement sans lecture du contenu.


## Qualité du classement et variantes de source — 0.108.1

L'inspection des candidats Wikipédia conserve la destination de la lecture
d'une redirection valide. Deux liens dont la destination est identique
occupent une seule place dans le classement. Pour iFixit, l'identifiant du
guide et la langue de l'article servent à rapprocher les variantes d'une
même procédure. La sélection conserve les identifiants d'origine de ses
résultats. Le plan commun reconnaît aussi les expressions de mise à la terre
et les variantes bilingues liées aux semences potagères. Le
[bilan Bazzite](../essais/2026-11-23-audit-qualite-recherche-bazzite.md)
présente les cas reproduits, les limites de pertinence du fonds et la recette.
