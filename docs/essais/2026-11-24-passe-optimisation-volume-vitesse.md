# Passe d’optimisation volume et vitesse — 24 novembre 2026

**Bilan daté — version 0.115.0, laboratoire Bazzite de Louis (Ryzen 9, 32 Go,
RTX 2060 6 Go, fonds de 205 archives ZIM soit 976 Go, 17 375 vidéos indexées).**
Les mesures ont été faites sur le laboratoire en service, avec la session de
Louis ouverte et d’autres travaux en cours (inventaire vidéo des ZIM, recette
documentaire) : elles donnent des ordres de grandeur, pas des chronométrages de
référence. Aucune mesure Windows ni chez Marc ; aucun essai sur iPhone réel.
Les mesures de la passe ont été faites dans des conteneurs jetables (dossier
d’état temporaire, données réelles en lecture seule) pendant que le labo restait
en 0.108.0 ; le labo a ensuite été mis à jour en 0.115.0 (section « Mise à jour
réelle du laboratoire »).

## Objectif fixé

| Axe | État initial mesuré | Objectif |
| --- | --- | --- |
| Index vidéo `videos.db` | 6,87 Go, plus un journal de 1,8 Go au repos et 7,7 Go pendant une reconstruction | −40 % au moins, journal borné |
| Instantanés de mise à jour et sauvegardes | Recopient l’index vidéo régénérable (7 à 14 Go) | Ne plus le recopier |
| Démarrage de Kiwix | 42 à 59 s pour cataloguer 205 archives | Moins de 5 s |
| Premier chargement du portail | 983 Ko en 69 fichiers, sans compression ; chaque visite revalide tout | ÷3 transféré, aucune revalidation des fichiers versionnés |
| Reconstructions de l’index vidéo | En boucle pendant l’inventaire vidéo des ZIM (≈ 25 min de CPU du pilote chacune) | Plus de boucle |

## Constats initiaux

- `videos.db` stockait deux fois le texte des sous-titres : une fois dans
  `video_text`, une seconde fois dans les 92 partitions de recherche
  (2,22 Go + 2,21 Go de contenu, 0,95 + 0,99 Go d’index, 11,5 millions de
  répliques). La reconstruction réécrivait tout l’index dans une seule
  transaction : le journal WAL atteignait la taille de la base et restait
  ensuite sur le disque.
- Au labo, l’inventaire vidéo des ZIM publie ses archives une à une ; chaque
  publication changeait l’empreinte, et la recherche suivante relançait une
  reconstruction complète. Une nouvelle reconstruction a démarré dès la fin de
  la précédente (06 h 33 puis 07 h 02).
- Pendant ce temps, une recherche documentaire nouvelle prenait 12 à 41 s, dont
  environ 8 s seulement chez Kiwix (33 requêtes, deux voies parallèles).
- Kiwix exécutait `kiwix-manage` une fois par archive : chaque appel relisait et
  réécrivait le catalogue grandissant.
- Caddy servait le portail sans compression et en `no-cache` partout.

## Changements de la 0.115.0

Voir l’[architecture des vidéos](../architecture/videos.md#index-vidéo-compact-et-publication-dun-bloc--01140),
l’[architecture générale](../architecture/README.md#compression-cache-du-portail-et-catalogue-kiwix--01140)
et le [guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

1. Index vidéo construit dans `videos.db.next`, sans journal, puis publié d’un
   bloc quand aucune connexion n’est ouverte ; les recherches gardent l’ancien
   index pendant la construction. Une construction interrompue est supprimée.
2. Nouveau format : identifiant et titre une fois par vidéo (`video_doc`),
   chaque réplique une fois (`video_cue`) ; la recherche principale
   (`video_search`) et les partitions indexent une vue sans rien recopier.
3. Journal borné à 64 Mo après point de contrôle.
4. Pendant un inventaire vidéo des ZIM en cours, une reconstruction de plus
   d’une minute n’est relancée qu’après quatre fois sa durée (au plus un
   cinquième du temps du pilote, environ 2 h au labo) ; les vidéos locales, le
   tri des collections et la fin de l’inventaire la relancent toujours. Un
   essai existant impose que les archives publiées restent consultables avant
   la fin de l’inventaire : un délai fixe de 6 h, d’abord envisagé, a été écarté.
5. Index vidéo, journal et rapport exclus des instantanés et sauvegardes ; une
   installation restaurée sans index le reconstruit au démarrage.
6. Caddy : gzip (préféré) ou zstd pour les réponses textuelles ; cache immuable
   d’un an pour les fichiers appelés avec `?v=` (empreinte du contenu).
7. Kiwix : catalogue en un seul appel ; repli archive par archive si l’une
   d’elles est illisible.
8. Cache disque des réponses Kiwix : les réponses arrivées pendant une écriture
   sont enregistrées ensemble, en une transaction (voir plus bas).

## Résultats

| Mesure | Avant | Après | Méthode |
| --- | --- | --- | --- |
| Index vidéo, contenu identique (instantané figé) | 7,70 Go | 3,42 Go (−56 %) | conversion d’une copie ; 1 395 requêtes aux réponses identiques, temps équivalents |
| Variante intermédiaire (texte non recopié dans les partitions seulement) | 7,70 Go | 4,67 Go (−39 %) | même méthode, non retenue |
| Journal pendant et après reconstruction | jusqu’à 7,7 Go | aucun pendant la construction, ≤ 64 Mo ensuite | observation du labo ; essai jetable |
| Catalogue Kiwix, 205 archives | 42 à 59 s | 3 s | conteneur jetable, même image |
| Premier chargement du portail | 983 Ko | 304 Ko gzip, 318 Ko zstd | Caddy jetable, même image |
| Revalidations au rechargement | 69 | 1 (la page) | en-têtes `Cache-Control` |

### Scan réel complet avec le code de la branche

Conteneur jetable (image du pilote du labo, réseau coupé, 2 Go de mémoire),
code de la branche, dossier d’état temporaire, vidéos, ZIM et inventaires
vidéo des ZIM du labo en lecture seule :

| Mesure | Ancien format (pilote du labo) | 0.115.0 (conteneur jetable) |
| --- | --- | --- |
| Vidéos, pistes | 17 375 vidéos, 61 586 pistes | identiques |
| Durée | 1 494 à 1 850 s | 399 s |
| Fichier final | 6,87 puis 8,53 Go (journal vide) | 3,42 Go, aucun journal |
| Occupation maximale pendant la construction | ≈ 14,6 Go (base + journal de 7,7 Go) | 3,42 Go (l’ancien fichier n’existait pas) |

Les durées ne sont pas comparables strictement : l’ancien code tournait dans le
pilote du labo, avec les recherches et d’autres travaux, et un premier essai
jetable sans le dossier `deploy` monté avait pris 1 494 s avec des erreurs de
recherche des transcriptions. Seize recherches vidéo (8 mots, tous les domaines
et « résilience ») ont répondu en 0,5 à 1,5 s sur l’index neuf, sans erreur ;
leur statut reste « partiel » car l’état temporaire n’avait pas tous les
inventaires du labo. Lors d’une mise à jour réelle, l’ancien fichier reste en
place jusqu’à la publication : prévoir la place des deux.

### Où passe le temps d’une recherche documentaire

- Sonde de latence de la boucle du pilote : médiane 1,07 ms et 95ᵉ centile
  1,41 ms au repos ; 1,17 et 4,29 ms pendant une reconstruction vidéo. Le
  verrou de l’interpréteur n’explique donc pas les recherches lentes.
- Échantillonnage des piles (5 ms) d’un pilote jetable relié à un Kiwix jetable
  sur le fonds réel : le code du pilote ne calcule qu’environ 0,5 s par
  recherche neuve ; il attend surtout Kiwix et son cache disque. Une recherche
  déjà en cache répond en 0,2 à 0,6 s.
- Concurrence Kiwix, 33 lots plein texte d’une vraie recherche, rejoués :

  | Voies parallèles | Durée murale |
  | --- | --- |
  | 1 | 4,3 à 6,1 s |
  | 2 (réglage actuel) | 2,0 à 3,3 s |
  | 4 | 1,7 à 2,1 s |
  | 6 | 1,5 à 2,7 s |

  Mémoire maximale de Kiwix : 690 Mo. Ce rejeu isolé suggérait environ 1 s de
  gain avec quatre voies, mais cinq recherches complètes neuves, rejouées deux
  fois avec 2 puis 4 voies (pilote jetable, cache vidé), donnent les mêmes
  durées : 50,4 et 45,5 s cumulées avec 4 voies, 45,8 et 51,3 s avec 2. Le
  réglage n’est pas modifié.
- Diagnostic d’une recherche lente (« isoler un grenier », 14 s) : 33 requêtes
  plein texte Kiwix cumulent 22,9 s sur deux voies ; les archives Gutenberg
  dominent (un lot de 12 archives à 5,9 s, d’autres lots de 1 à 2 s). Le coût
  principal est donc la recherche plein texte de Kiwix dans ces grandes
  archives, pas le pilote.
- Cache disque des réponses Kiwix : sur cinq recherches neuves, 223 écritures,
  chacune dans sa propre transaction synchronisée (médiane 38 ms, jusqu’à
  0,84 s), et 223 lectures, dont certaines restaient bloquées jusqu’à 150 ms
  par ces écritures. Les écritures se font maintenant par lots. Essai alterné
  ancien/nouveau (cinq recherches neuves, cache vidé, deux passes chacune) :
  durées identiques (47,1 et 51,0 s cumulées avant, 47,5 et 46,9 s après), car
  la file d’écriture était déjà hors du chemin des résultats. Le gain est une
  synchronisation disque par lot au lieu d’une par réponse (337 pour ces cinq
  recherches), utile sur un disque plus lent, sans gain de temps mesuré au labo.

## Mise à jour réelle du laboratoire — 24 novembre 2026

Le labo tournait en 0.108.0 (code `runtime/candidat-0108.ddESzy`, ports
décalés 18080, 18000 et 18081 parce que 8080 et 11436 sont pris par
l’installation « neuf » du PC). Un `lab.sh up` standard aurait repris les ports
par défaut : les conteneurs pilote, portail et Kiwix ont été recréés avec leur
commande de création d’origine, seuls les chemins du code étant remplacés par
`runtime/livraison-0114-<commit>`. Retour arrière : commandes d’origine et état
du pilote (hors fichiers régénérables, 208 Mo) dans
`runtime/avant-livraison-0114/`. Open WebUI et Ollama (arrêté) n’ont pas été
touchés.

| Mesure réelle | 0.108.0 | 0.115.0 |
| --- | --- | --- |
| Kiwix prêt après création, 205 archives | ≈ 1 min (démarrage de 06 h 33) | 8 s |
| Index vidéo | 9,44 Go | 3,42 Go, même nombre de vidéos (17 375) et de pistes (61 586) |
| Reconstruction unique au premier démarrage | — | 323 s ; pic de 12,7 Go le temps de la publication (ancien et nouveau fichiers) |
| Portail, 77 fichiers liés à la page | 1,17 Mo | 468 Ko (gzip), cache d’un an pour les fichiers `?v=` |
| 16 recherches vidéo (domaine par défaut) | 5,7 s cumulées pendant la reconstruction | 2,75 s, mêmes listes 16/16 |

Pendant la reconstruction, les recherches vidéo ont continué sur l’ancien
index (0,2 à 0,6 s) avec l’avertissement d’actualisation. Après publication,
elles prenaient d’abord 9,4 s cumulées : la comparaison « avant » était
favorisée par un rapport vidéo minuscule pendant la reconstruction. Le
profilage a montré que le décodage du rapport complet (25 Mo, déjà présent en
0.108.0) coûtait environ 0,3 s par recherche, et le tri par alias de bm25
environ 0,1 s. Les deux corrections, déployées par deux redémarrages du seul
pilote (09 h 27 et 09 h 34), ramènent la série à 2,75 s. Les résultats de la
recette vidéo enregistrés en 0.108.0 (quatre requêtes) se retrouvent tous.

Constats de ce premier déploiement : le pilote du labo pointait vers un
contrôleur (`10.89.0.1:21436`) qui n’écoutait plus depuis le redémarrage du PC
(déjà le cas en 0.108.0 ; marche et arrêt du moteur indisponibles depuis le
portail) ; le domaine par défaut « résilience » ne renvoyait rien pour
« greffer un pommier », alors que le domaine « tout » trouvait « Greffe
anglaise » et Baltet. Ils sont traités dans la section suivante.

Numérotation : la branche portait 0.114.0 pendant ces essais ; la PR #129 a
aussi publié une 0.114.0 sur `main`. Après rapprochement, cette livraison est
numérotée **0.115.0** (niveau `y` : changement de format de l’index vidéo et
nouveau réglage `control_port`, évolutions compatibles).

## Corrections après la mise à jour — 24 novembre 2026

- **Contrôleur** : nouveau réglage `control_port` (21436 au labo, 11436 par
  défaut) lu par `scripts/control.py` et par `linux_lab.py`, qui envoie le
  pilote vers `host.containers.internal:<port>` (adresse de l’hôte vue par
  pasta, stable après redémarrage). Au labo, un service utilisateur
  `setupsurvie-lab-controle.service` relance le contrôleur au démarrage.
  Vérifié : `control_available` vrai, GPU, RAM et disque visibles dans le
  portail ; aucun moteur IA n’a été démarré.
- **Arrêt du pilote** : `--timeout-graceful-shutdown 5` pour uvicorn (Compose,
  laboratoire, scripts de rafraîchissement et de restauration). Le déploiement
  suivant s’est arrêté sans arrêt forcé par Podman.
- **Greffe** : concepts `greffe` et `pommier` ajoutés à la recherche (verbe,
  pluriels et traduction anglaise). Le premier essai au labo renvoyait encore
  0 résultat, mais pour une autre raison : le conteneur Kiwix du labo avait été
  créé avec `--memory=1g` (valeur antérieure à cette passe, alors que
  `linux_lab.py` prévoit 6 Go). Saturé et en swap, il mettait 2 min 40 s pour
  une seule recherche, d’où 65 lots en erreur et le dépassement du délai.
  Kiwix a été recréé avec 6 Go : même requête en 0,05 s, recherche complète en
  3,7 s sans échec, et 3 réponses pertinentes (gardening.stackexchange :
  greffe sur pommier adulte, sur souche, coing et pommier). Limite observée :
  « purifier l’eau de pluie » ne renvoie qu’un résultat hors sujet
  (« Air purifier ») ; non traité dans cette passe.

## Limites et suites proposées

- Les tests automatisés couvrent la publication, la reprise après échec,
  l’attente des connexions ouvertes, l’anti-boucle et les écritures groupées du
  cache et du rapport vidéo.
- L’arrêt du pilote attendait la fermeture des connexions HTTP ouvertes (arrêt
  forcé par Podman après 30 s lors de la deuxième bascule) ; corrigé par le
  délai de 5 s ci-dessus.
- Mise à jour vers 0.115.0 : une reconstruction unique de l’index vidéo au
  premier démarrage (changement de format), avec l’ancien index consultable
  jusqu’à la fin.
- Recherche documentaire neuve : 3,6 à 15 s au labo, sans gain obtenu dans
  cette passe. Pistes à mesurer : lancer d’abord les lots les plus lents
  (Gutenberg), régler les fils de `kiwix-serve`, ou indexer localement les
  archives dont la recherche Kiwix est la plus lente.
- Proposition non réalisée : réutiliser les lignes des vidéos inchangées au
  lieu de relire toutes les pistes (reconstruction partielle).
- Proposition non réalisée : compresser `images.tar` du kit (couches non
  compressées, environ 10 Go) ; plusieurs outils lisent ce nom de fichier.
- Le choix du fonds (doublons de couverture, grandes archives anciennes) reste
  une décision de Louis, hors de cette passe.
- Réglages d’inférence (cache KV quantifié, attention optimisée) non mesurés :
  Ollama était arrêté au labo et aucun démarrage forcé n’a été fait.
