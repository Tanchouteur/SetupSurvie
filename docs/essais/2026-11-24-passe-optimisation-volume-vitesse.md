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

## Résultats

| Mesure | Avant | Après | Méthode |
| --- | --- | --- | --- |
| Index vidéo, contenu identique (instantané figé) | 7,70 Go | 3,42 Go (−56 %) | conversion d’une copie ; 1 395 requêtes aux réponses identiques, temps équivalents |
| Variante intermédiaire (texte non recopié dans les partitions seulement) | 7,70 Go | 4,67 Go (−39 %) | même méthode, non retenue |
| Journal pendant et après reconstruction | jusqu’à 7,7 Go | aucun pendant la construction, ≤ 64 Mo ensuite | observation du labo ; essai jetable |
| Catalogue Kiwix, 205 archives | 42 à 59 s | 3 s | conteneur jetable, même image |
| Premier chargement du portail | 983 Ko | 304 Ko gzip, 318 Ko zstd | Caddy jetable, même image |
| Revalidations au rechargement | 69 | 1 (la page) | en-têtes `Cache-Control` |

## Limites et suites proposées

- Les essais du scan réel et de la réactivité du pilote sont décrits plus bas
  quand ils ont abouti ; les tests automatisés couvrent la publication, la
  reprise après échec, l’attente des connexions ouvertes et l’anti-boucle.
- Proposition non réalisée : réutiliser les lignes des vidéos inchangées au
  lieu de relire toutes les pistes (reconstruction partielle).
- Proposition non réalisée : compresser `images.tar` du kit (couches non
  compressées, environ 10 Go) ; plusieurs outils lisent ce nom de fichier.
- Le choix du fonds (doublons de couverture, grandes archives anciennes) reste
  une décision de Louis, hors de cette passe.
- Réglages d’inférence (cache KV quantifié, attention optimisée) non mesurés :
  Ollama était arrêté au labo et aucun démarrage forcé n’a été fait.
