# Passe d’optimisation volume et vitesse — 24 novembre 2026

**Bilan daté — version 0.114.0, laboratoire Bazzite de Louis (Ryzen 9, 32 Go,
RTX 2060 6 Go, fonds de 205 archives ZIM soit 976 Go, 17 375 vidéos indexées).**
Les mesures ont été faites sur le laboratoire en service, avec la session de
Louis ouverte et d’autres travaux en cours (inventaire vidéo des ZIM, recette
documentaire) : elles donnent des ordres de grandeur, pas des chronométrages de
référence. Aucune mesure Windows ni chez Marc ; aucun essai sur iPhone réel.
Le laboratoire lui-même est resté en 0.100.0 : les essais du code de la
branche ont été faits dans des conteneurs jetables, avec un dossier d’état
temporaire et les données réelles montées en lecture seule.

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

## Changements de la 0.114.0

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

| Mesure | Ancien format (pilote du labo) | 0.114.0 (conteneur jetable) |
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

## Limites et suites proposées

- Les tests automatisés couvrent la publication, la reprise après échec,
  l’attente des connexions ouvertes, l’anti-boucle et les écritures groupées du
  cache. Le laboratoire lui-même n’a pas été mis à jour en 0.114.0 pendant cette
  passe : les gains sont mesurés dans des conteneurs jetables.
- Mise à jour vers 0.114.0 : une reconstruction unique de l’index vidéo au
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
