# Télécharger une liste de vidéos YouTube dans la bibliothèque

**Plan / proposition de l’agent — 17 novembre 2026. Rien n’est implémenté ni
téléchargé.** Demande de Louis du même jour : un outil qui lit un fichier texte
(une adresse YouTube par ligne), télécharge chaque vidéo, la renomme et la range
seule dans un dossier connu de la bibliothèque. Ces vidéos sont des guides visuels
choisis à la main, en complément des archives ZIM. Ce document trace l’outil
avant son développement. Il attend la validation de Louis.

## Ce qui existe déjà

- Les vidéos ajoutées à la main se rangent dans **`library/video/`** (au singulier),
  sous-dossiers compris. C’est le chemin créé par `scripts/setup.py` et monté en
  lecture seule dans le pilote (`compose.yaml` → `/videos`). Louis a écrit
  `library/videos/` dans sa demande : **à confirmer**. Le code ne lit pas un
  dossier `videos/` au pluriel.
- Depuis la 0.39.0, le répertoire des vidéos se met à jour tout seul : au
  démarrage, puis lors d’une recherche si le dossier a changé. Une vidéo
  correctement rangée devient donc trouvable sans clic supplémentaire
  ([guide vidéo](../utilisation/videos-locales.md)).
- L’inventaire lit les fichiers qui accompagnent la vidéo : `.info.json` pour le
  titre, la chaîne, la description, la langue et l’adresse d’origine ; `.fr.srt`
  ou `.en.vtt` pour les sous-titres. Les fichiers `.part`, `.ytdl` et `.fNNN.*`
  sont ignorés comme téléchargements inachevés.
- La récupération des sous-titres YouTube (0.31.0) utilise `youtube-transcript-api`.
  `yt-dlp` avait alors été écarté parce qu’il n’était pas nécessaire **pour ce
  seul besoin** ([décision](acquisition-sous-titres.md)). Le téléchargement des
  médias, lui, en a besoin.

## Fonctionnement proposé

### Fichier d’entrée

Un fichier `.txt` en UTF-8 :

```text
# Les lignes vides et celles qui commencent par # sont ignorées.
[eau]
https://www.youtube.com/watch?v=XXXXXXXXXXX
https://youtu.be/YYYYYYYYYYY
[feu et chauffage]
https://www.youtube.com/watch?v=ZZZZZZZZZZZ
```

- Une adresse par ligne. Seules les adresses de **vidéos** YouTube sont acceptées
  (`youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`), comme le fait déjà
  `pilot/provider_subtitles.py`. Les listes de lecture et les chaînes sont refusées
  dans un premier temps : sinon, une seule ligne pourrait déclencher des centaines
  de téléchargements.
- `[thème]` est une option qui range les vidéos suivantes dans un sous-dossier.
  Sans thème, la vidéo est rangée sous le nom de la chaîne.
- Une ligne mal formée est signalée avec son numéro, sans arrêter le reste.

### Rangement et noms

```text
library/video/youtube/<thème ou chaîne>/<Titre> [<identifiant>].mp4
                                         <Titre> [<identifiant>].info.json
                                         <Titre> [<identifiant>].fr.srt   (si disponible)
                                         <Titre> [<identifiant>].en.srt   (si disponible)
```

- Les noms sont nettoyés pour Windows et Linux : caractères interdits, longueur
  limitée, accents conservés si le système les accepte. L’identifiant YouTube
  entre crochets évite les collisions et permet de repérer les doublons.
- Le `.info.json` est conservé : c’est lui qui donne le titre lisible, la chaîne,
  la description et l’adresse d’origine, que le logiciel utilise pour la recherche
  et pour récupérer plus tard des sous-titres.
- Les sous-titres sont demandés en français puis en anglais, en distinguant ceux
  fournis par l’auteur et les automatiques. Leur absence n’empêche pas le
  téléchargement de la vidéo.

### Qualité et taille

- **480p maximum** par défaut, comme les téléchargements actuels de Marc :
  `bv*[height<=480]+ba/b[height<=480]`, conteneur MP4 si possible pour la lecture
  dans le navigateur, y compris sur iPhone.
- Il faut **FFmpeg** pour assembler l’image et le son quand YouTube les fournit
  séparément. Sans FFmpeg, seul un format déjà complet est utilisé, souvent de
  moindre qualité. Le rapport le signale.
- Plafond par vidéo (par exemple 1,5 Go) et contrôle de l’espace libre avant
  chaque vidéo. Dans le laboratoire de Louis, mêmes contrôles de montage et de
  capacité que `scripts/linux_lab.py` (plafond de 600 Go du SSD 4 To).

### Téléchargement fiable

- Le téléchargement se fait dans un dossier de travail, en dehors de
  `library/video/`, par exemple `state/video-downloads/en-cours/`. La vidéo et ses
  fichiers associés ne sont déplacés dans la bibliothèque qu’une fois terminés.
  La bibliothèque ne voit donc jamais un fichier à moitié écrit.
- Reprise : relancer avec le même fichier reprend les vidéos inachevées et passe
  celles déjà présentes (registre des identifiants téléchargés, et contrôle du
  fichier réellement présent dans la bibliothèque).
- Une vidéo indisponible (privée, supprimée, réservée à une région, limite d’âge)
  donne une erreur claire dans le rapport. **Aucun contournement** : pas de cookies
  de navigateur, pas de compte, pas de proxy. C’est la même règle que pour les
  sous-titres.
- À la fin, un rapport ligne par ligne : téléchargée, déjà présente, refusée,
  erreur (avec la raison), dossier de destination. Pas besoin de lancer
  l’inventaire à la main : il démarre tout seul à la recherche suivante ou au
  prochain démarrage.

### Où et comment le lancer

1. **Étape 1 — outil en ligne de commande** : `scripts/youtube_videos.py liste.txt`,
   lancé sur le PC cible avec Internet, sous Windows comme sous Linux. Jamais dans
   le runner de développement (aucun téléchargement de média dans la VM).
2. **Étape 2 — depuis le site, si Louis le valide** : « Famille → Bibliothèque →
   Vidéos → Ajouter depuis une liste YouTube ». On dépose le `.txt`, on suit la
   progression, et on peut mettre en pause puis reprendre explicitement, comme pour
   la récupération des sous-titres. Le pilote monte `library/video/` en lecture
   seule : cette étape demande donc soit un montage en écriture limité à
   `library/video/youtube/`, soit un petit service séparé. Ce choix d’architecture
   reste à faire.

### Dépendances

- `yt-dlp`, avec une version figée et vérifiée dans `deploy/versions.json`.
  YouTube change souvent et casse les anciennes versions : il faudra une procédure
  de mise à jour volontaire de l’outil. Une version figée peut cesser de
  fonctionner sans que le code ait changé.
- FFmpeg portable sous Windows (même logique que les autres outils préparés par
  l’installateur). Sous Linux, le paquet système ou une version statique, sans
  installation globale sur Bazzite.
- Les deux sont des outils de préparation, utilisés avec Internet. Ils ne sont
  pas nécessaires pour lire les vidéos ensuite.

## Droits et offre commerciale — point bloquant à trancher

Les vidéos YouTube restent la propriété de leurs auteurs. Les télécharger pour un
usage privé chez Marc ne donne **aucun droit de les redistribuer**. Les conditions
d’utilisation de YouTube encadrent aussi le téléchargement. Conséquences
proposées :

- ces vidéos ne font **pas** partie du kit ni du PC vendu préinstallé. Elles
  restent des données personnelles de l’installation, comme les conversations ;
- l’outil peut être livré pour que **le client** télécharge ses propres listes ;
  sa responsabilité juridique est à faire examiner avant toute vente ;
- le rapport conserve l’adresse d’origine et la chaîne de chaque vidéo pour
  pouvoir retrouver son auteur et ses conditions.

## Essais prévus

- Tests unitaires sur fixtures : lecture du `.txt` (thèmes, commentaires, lignes
  invalides, doublons), nettoyage des noms, déplacement atomique, reprise,
  rapport. `yt-dlp` est simulé ; aucun réseau.
- Essai réel sur le PC cible avec 3 à 5 vidéos courtes et libres de droits :
  480p, sous-titres fr/en, une vidéo sans sous-titres, une adresse invalide, une
  vidéo indisponible. Ensuite : la vidéo apparaît dans « Vidéos uniquement »,
  l’assistant donne son lien et le lecteur l’ouvre sans Internet.
- Lecture réelle sur Windows (Marc) et sur iPhone, distincte des essais Linux.

## Questions pour Louis

1. Dossier : garder `library/video/` (déjà utilisé par le code et par Marc) ou
   passer à `library/videos/` (il faudrait alors migrer les installations) ?
2. Rangement : par thème `[eau]` dans le fichier, par chaîne, ou les deux ?
3. Étape 1 seule (ligne de commande) pour commencer, ou directement le bouton
   dans le site ?
4. Plafond de qualité : 480p pour tout, ou 720p pour certaines vidéos où les
   gestes doivent être bien visibles ?
5. Droits : confirmer que ces vidéos restent hors de l’offre commerciale.
