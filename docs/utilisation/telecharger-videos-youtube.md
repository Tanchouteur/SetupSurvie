# Télécharger une liste de vidéos YouTube

**Guide actuel — 0.43.5, 18 novembre 2026.** Depuis le site ou en ligne de commande
sur le PC qui héberge SetupSurvie ; ce PC doit avoir **Internet**. Depuis 0.42.0, yt-dlp, Deno
et FFmpeg sont préparés automatiquement : rien à installer à la main. Il range les vidéos dans la
bibliothèque ; le site les répertorie ensuite tout seul. Essai réel sur Bazzite ; sous Windows, voir les [limites](#limites).

## Depuis le site — 0.43.5

Avec le profil **Famille**, ouvrir **Mon appareil → Paramètres → Bibliothèque et
préparations → Ajouter des vidéos depuis YouTube**. Un raccourci se trouve aussi dans
**Bibliothèque → Collections → Vidéos de la bibliothèque**.

1. Coller les adresses, ou choisir un fichier texte (format ci-dessous).
2. **Vérifier la liste** indique le nombre de vidéos et explique les lignes écartées.
3. Choisir la qualité, puis **Télécharger les vidéos**.

Le PC serveur fait le travail : la page peut être fermée. Le suivi donne la vidéo
en cours et le résultat de chaque ligne. **Mettre en pause** arrête la vidéo en
cours en gardant ses fichiers partiels ; **Reprendre** continue la liste et passe
les vidéos déjà rangées. Une seule préparation de bibliothèque tourne à la fois.
À la fin, le répertoire des vidéos s’actualise tout seul.

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

## 2. Outils nécessaires : rien à faire

Le téléchargement utilise trois outils, aux versions figées et vérifiées par
empreinte (`deploy/youtube-tools.json`, `scripts/requirements-youtube.txt`) :

- **yt-dlp** 2026.10.26, qui télécharge depuis YouTube ;
- **Deno** 2.9.8, le moteur JavaScript que YouTube exige désormais ;
- **FFmpeg** 8.1.3 (version LGPL), qui assemble image et son en 480p.

Ils sont rangés dans `tools/` du dossier de données, à part du reste du système,
et préparés sans intervention :

| Moment | Ce qui se passe |
| --- | --- |
| Installation en ligne | Téléchargés, vérifiés et installés avec le reste. |
| Installation depuis le kit hors ligne | Pris dans le kit, sans Internet. |
| Copie vers un autre disque ou un autre PC | Leurs fichiers suivent le dossier de données ; l’environnement Python est recréé hors ligne à la réactivation. |
| Premier téléchargement, si quelque chose manque | Réparé depuis les fichiers déjà présents, sinon téléchargé : Internet est de toute façon nécessaire pour YouTube. |

Un échec de préparation ne bloque jamais l’installation : le reste de SetupSurvie
fonctionne, et l’outil se termine au premier téléchargement avec Internet.

Si YouTube change et que les téléchargements se mettent à échouer (refus,
formats introuvables), passer à la toute dernière version de yt-dlp :

```text
python scripts/youtube_videos.py prepare --latest
```

La version utilisée, ainsi que la présence de Deno et FFmpeg, figurent dans chaque rapport.

### Kit hors ligne

L’export du kit depuis le laboratoire (`scripts/pilot_kit.py`) complète lui-même
le cache avec les fichiers **Windows** (Python 3.13) et **Linux** de ces outils, puis
les place sous `app/vendor/youtube/` avec leurs empreintes. L’installation depuis
le kit les vérifie et les installe sans Internet. Si Internet manque pendant
l’export, le kit le signale et l’outil se préparera au premier téléchargement.
Pour compléter le cache à la main, par exemple pour une autre version de Python :

```text
python scripts/youtube_tools.py --data-dir <données> --cache-target windows:3.12
```

## 3. Télécharger

```text
python scripts/youtube_videos.py download videos.txt
```

- L’installation est trouvée automatiquement, comme pour la mise à jour Windows :
  dossier `prive` à côté de l’application, `.local` dedans ou `moteur\.local`.
  Sinon, ajouter `--work-dir DOSSIER_PRIVÉ` ou `--data-dir DOSSIER_DONNÉES`.
  Dans le laboratoire Linux de Louis, ajouter `--lab`, qui contrôle le volume
  dédié.
- Qualité **480p maximum** par défaut, H.264 et MP4 en priorité pour la compatibilité
  avec les téléphones et anciens PC. `--max-height 720`
  aide pour les vidéos où les gestes doivent être bien visibles.
- Limite de **1,5 Go par vidéo** (`--max-size-gb`), et **10 Go** gardés libres sur
  le disque (`--reserve-gb`). L’outil s’arrête proprement si l’espace manque.
- Les sous-titres français et anglais sont demandés : ceux de l’auteur et les
  automatiques. Leur absence, ou un refus de YouTube, n’empêche pas le téléchargement. Le site peut
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

- Trois vraies vidéos ont été téléchargées sur Bazzite avec le candidat de la 0.43.4, avec pause, reprise,
  répertoire et recherche ([bilan](../essais/2026-11-18-youtube-reel-bazzite-windows.md)).
  Sous Windows, les vrais outils sont contrôlés en CI, sans accès à YouTube : le premier
  téléchargement réel reste à faire sur le PC cible.
- Le comportement de YouTube évolue : un refus anti-robot ou une limite de débit
  est signalé, sans garantie de réussite.
