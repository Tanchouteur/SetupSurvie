# Télécharger une liste de vidéos YouTube

**Guide actuel — 0.41.0, 17 novembre 2026.** Outil en ligne de commande, à lancer
sur le PC qui héberge SetupSurvie, **avec Internet**. Il range les vidéos dans la
bibliothèque ; le site les répertorie ensuite tout seul. Aucun essai réel sur
YouTube n’a encore été fait : voir [Limites](#limites).

## 1. Préparer la liste

Créer un fichier texte, par exemple `videos.txt`, en UTF-8 (le Bloc-notes de
Windows convient) :

```text
# Les lignes vides et celles qui commencent par # sont ignorées.
[Eau]
https://www.youtube.com/watch?v=XXXXXXXXXXX
https://youtu.be/YYYYYYYYYYY
[Feu et chauffage]
https://www.youtube.com/watch?v=ZZZZZZZZZZZ
[]
https://www.youtube.com/shorts/WWWWWWWWWWW
```

- Une adresse de **vidéo** par ligne : `watch?v=`, `youtu.be/`, `shorts/`, `live/`
  ou `embed/`. Ce qui suit l’adresse sur la ligne est ignoré.
- `[Thème]` range les vidéos suivantes dans `library/video/youtube/Thème/`.
  `[]` revient au rangement par défaut : le nom de la **chaîne**.
- Les listes de lecture et les pages de chaîne sont refusées : une seule ligne
  pourrait sinon lancer des centaines de téléchargements. Mettre l’adresse de
  chaque vidéo.
- Une adresse en double est signalée et téléchargée une seule fois.

Pour relire la liste sans rien télécharger :

```text
python scripts/youtube_videos.py check videos.txt
```

## 2. Préparer l’outil (une fois, puis de temps en temps)

Depuis le dossier de SetupSurvie :

```text
python scripts/youtube_videos.py prepare
```

Sous Windows, utiliser `py -3` à la place de `python` si besoin. La commande
installe la dernière version de `yt-dlp` dans `tools/youtube/` du dossier de
données, à part du reste du système. YouTube change souvent : si les
téléchargements se mettent à échouer, relancer `prepare` met yt-dlp à jour.
La version utilisée figure dans chaque rapport.

Deux outils facultatifs améliorent le résultat :

- **Deno**, que yt-dlp utilise pour lire les pages YouTube. Sans lui, YouTube
  peut refuser des vidéos ou limiter les formats. Windows : `winget install
  DenoLand.Deno`. Node.js ou Bun conviennent aussi s’ils sont déjà installés.
- **FFmpeg**, pour assembler image et son en 480p. Sans lui, seuls les formats
  déjà complets sont utilisés, souvent en 360p. Windows : `winget install
  Gyan.FFmpeg`, ou indiquer son chemin avec `--ffmpeg`.

L’outil signale en début de téléchargement s’ils sont absents.

## 3. Télécharger

```text
python scripts/youtube_videos.py download videos.txt
```

- L’installation est trouvée automatiquement, comme pour la mise à jour Windows :
  dossier `prive` à côté de l’application, `.local` dedans ou `moteur\.local`.
  Sinon, ajouter `--work-dir DOSSIER_PRIVÉ` ou `--data-dir DOSSIER_DONNÉES`.
  Dans le laboratoire Linux de Louis, ajouter `--lab`, qui contrôle le volume
  dédié.
- Qualité **480p maximum** par défaut, conteneur MP4 si possible. `--max-height 720`
  aide pour les vidéos où les gestes doivent être bien visibles.
- Limite de **1,5 Go par vidéo** (`--max-size-gb`), et **10 Go** gardés libres sur
  le disque (`--reserve-gb`). L’outil s’arrête proprement si l’espace manque.
- Les sous-titres français et anglais sont demandés : ceux de l’auteur et les
  automatiques. Leur absence n’empêche pas le téléchargement. Le site peut
  ensuite récupérer, créer depuis l’audio ou traduire les pistes manquantes
  ([guide vidéo](videos-locales.md)).

Chaque vidéo est d’abord téléchargée dans `state/video-downloads/en-cours/`,
puis déplacée terminée dans la bibliothèque, à côté de son `.info.json` et de
ses sous-titres :

```text
library/video/youtube/Eau/Titre de la vidéo [XXXXXXXXXXX].mp4
library/video/youtube/Eau/Titre de la vidéo [XXXXXXXXXXX].info.json
library/video/youtube/Eau/Titre de la vidéo [XXXXXXXXXXX].fr.vtt
```

L’identifiant entre crochets permet de reconnaître une vidéo déjà présente,
**y compris celles téléchargées avant cet outil** avec le nommage habituel de
yt-dlp, où qu’elles soient dans `library/video/`.

## 4. Coupure, reprise et rapport

- **Relancer la même commande** reprend les vidéos inachevées (fichiers `.part`
  conservés dans le dossier de travail) et passe celles déjà rangées.
- Le site n’affiche jamais une vidéo à moitié écrite : le fichier vidéo arrive
  en dernier, une fois complet.
- Une vidéo privée, supprimée, bloquée dans le pays, réservée aux abonnés ou
  avec limite d’âge donne une erreur claire. **Aucun contournement** n’est
  tenté : pas de cookies du navigateur, pas de compte, pas de proxy.
- À la fin : un résumé à l’écran et un rapport détaillé dans
  `state/video-downloads/rapports/`. Il contient, ligne par ligne, le statut, le
  dossier, la taille, les sous-titres obtenus et la raison des erreurs. Il est
  privé. Code de sortie 0 si tout est passé, 2 s’il reste des erreurs ou des
  lignes refusées.

Ensuite, il suffit d’ouvrir le site : les nouvelles vidéos sont répertoriées au
démarrage ou à la prochaine recherche, sans clic
(**Bibliothèque → Rechercher → Vidéos uniquement**).

## Droits

Ces vidéos restent la propriété de leurs auteurs. Elles sont téléchargées pour un
usage privé et ne font **pas** partie du kit ni du PC vendu préinstallé. Elles
suivent la sauvegarde de l’installation comme les autres données personnelles.
Voir la [décision et les questions ouvertes](../decisions/telechargement-videos-youtube.md).

## Limites

- Testé uniquement avec un yt-dlp simulé et une vérification des options par le
  vrai yt-dlp 2026.10.26, sans téléchargement. Le premier essai réel doit se faire
  sur le PC cible avec 3 à 5 vidéos courtes. Points à observer : 480p, sous-titres
  fr/en, vidéo sans sous-titres, adresse invalide, vidéo indisponible, puis
  lecture dans le site.
- Le comportement de YouTube évolue : un refus anti-robot ou une limite de débit
  est signalé, sans garantie de réussite.
- Pas encore de bouton dans le site : ce sera l’étape 2 si elle est validée.
