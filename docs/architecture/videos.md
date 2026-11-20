# Architecture — vidéos et sous-titres

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Vidéos et sous-titres locaux — 0.23.0

`pilot/video_inventory.py` partage le parseur standard avec le lanceur
`scripts/library_videos.py`. `pilot/videos.py` publie un index SQLite/FTS séparé
dans `state/pilot/videos.db`, avec métadonnées et segments par piste. Actualisation
explicite, annulation par événement rejoint, transaction globale et rapport R6
par vidéo ; une interruption laisse l’index précédent. Aucun original n’est écrit.
Le montage `library/video:/videos:ro` reste indépendant des guides/ZIM et ne change
pas le schéma du magasin principal. Une recherche vidéo optionnelle défaillante
est signalée sans supprimer les résultats documentaires.

Les identifiants `video:HASH#t=MILLISECONDES&track=N` sont opaques et gardent le
passage/la piste réellement trouvés. Résolution limitée au catalogue local et aux
fichiers réguliers vérifiés, détection des changements média/métadonnées/pistes.
L’API média accepte les plages HTTP ; l’API piste normalise SRT/WebVTT en texte
WebVTT échappé. Le lecteur n’effectue ni inférence, ni accès Internet, ni transcodage.
Les outils IA reçoivent des paroles avec horodatages et limites, sans pixels.
Voir le [guide](../utilisation/videos-locales.md) pour les limites et procédures.


Depuis 0.40.0, `videos.signature()` résume les noms, tailles et dates des fichiers
finis (médias, pistes, `.info.json`) et l’état de l’examen des ZIM ; `ensure_fresh()`
relance l’inventaire au démarrage et, au plus une fois par minute, avant une
recherche vidéo si cette empreinte a changé. `library.search(kind=…)` sépare
vidéos et documents ; en mode vidéos, une requête vide liste les titres et
l’espace documentaire est ignoré. `pilot/video_requests.py` détecte les demandes
de vidéo, nettoie la requête, compacte les résultats de l’outil `find_videos`
avec leur `open_url` et ajoute les liens oubliés par le modèle.

Depuis 0.43.0, `pilot/youtube_downloads.py` dépose la liste dans
`state/pilot/youtube-lists/` (lisible par l’hôte) et envoie son identifiant au
contrôleur. L’action `youtube-download` de `scripts/library_tasks.py` lance
`scripts/youtube_videos.py` avec fichiers de progression et d’annulation ;
`pilot/youtube_list.py` partage l’analyse de la liste entre site et hôte.

## Préparation des sous-titres — 0.24.0

`pilot/captions.py` garde file, segments, contrôles et propositions refusées dans
`video-captions.db`, séparé du magasin principal. Les fichiers complets sont dans
`video-captions/UUID/fr.vtt`, avec identifiant strict et contrôle des liens.
La publication est conditionnelle à un état encore actif, puis l’index vidéo est
actualisé. Le thread de publication est rejoint même à l’annulation. Une panne
entre fichier et état laisse un brouillon, jamais une piste implicitement prête.

L’édition source est calculée sur les originaux et leurs pistes, sans les sorties
préparées. L’index ne rattache que les sorties complètes pour cette édition et
dont l’empreinte de texte correspond à la publication. Les lecteurs ordinaires
restent sans IA et les originaux montés en lecture seule. Les pistes françaises
préparées gardent origine/langue source et avertissement dans les outils de l’IA.

## Transcription audio — 0.26.0

`transcriptions.py` garde les unités dans une base privée distincte et pilote un
enfant CPU `speech_worker.py`, avec entrée locale, modèle préinstallé et réseau
de téléchargement désactivé. Une pause rejoint cet enfant ; le journal conserve
les unités terminées et seule une piste complète est publiée. Le lecteur et
l’index joignent ensuite source reconnue et traduction française par leurs
révisions et empreintes. La consigne de traduction accepte les phrases coupées
sans déplacer les fragments. Voir le [bilan et ses limites](../essais/2026-11-16-transcription-audio-videos.md).

## Acquisition de pistes vidéo — 0.31.0

Les routes admin `/api/admin/video-acquisitions` isolent la récupération YouTube dans
`caption_acquisition.py`. Aucun réseau à l’import, à la lecture ou à l’ouverture
de Collections. Un enfant à environnement minimal exécute `caption_fetch_worker` ;
son délai et sa sortie sont bornés, la pause et l’arrêt du service le rejoignent.
`provider_subtitles` choisit une piste existante ; aucune traduction distante n’est
appelée. La bibliothèque réutilise celle de l’image Open WebUI épinglée.

La base privée `video-acquisition.db` et `video-acquisition/UUID/` conservent état,
rapport brut et WebVTT complet. Le résumé dans SQLite évite de relire les paroles
complètes à chaque suivi. La source locale est recontrôlée avant publication ;
les éditions modifiées ne récupèrent pas une ancienne piste. Deux requêtes réseau
au maximum ; commandes pause/reprise sérialisées. Le changement de schéma ajoute
seulement un résumé nullable aux premiers candidats, sans supprimer de données.

Le scan joint les pistes complètes, puis la file `captions` peut préparer le
français. Un arrêt IA n’efface pas la piste source acquise. Le rapport vidéo général
inclut l’état sans les paroles ; le rapport dédié est privé et contient les temps
bruts. Sauvegarde/transfert emportent cet état avec les autres états du pilote.
Voir le [guide](../utilisation/videos-locales.md) et les
[preuves et limites](../essais/2026-11-16-acquisition-sous-titres.md).
