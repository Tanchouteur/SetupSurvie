# Retrouver et lire les vidéos locales

**Guide actuel du candidat 0.23.0 — 16 novembre 2026.** Les fichiers restent dans
`library/video/` du disque de données, avec leurs sous-dossiers. Cette fonction
concerne les fichiers locaux ; les vidéos à l’intérieur des archives ZIM restent
à inventorier séparément. Aucun contenu de Marc n’a été examiné dans le runner.

## Préparer depuis le site

Après la mise à jour de maintenance, choisir **Famille → Bibliothèque → Collections →
Vidéos locales → Actualiser les vidéos et leurs sous-titres**. Cela lit les noms,
les métadonnées `.info.json` et les pistes `.fr.srt`, `.en.vtt`, etc. à côté du
média. Aucun téléchargement, reconnaissance vocale ou modèle IA n’est lancé.
Attendre « Inventaire terminé », puis rechercher avec le filtre des Collections
ou dans **Rechercher**. Relancer cette actualisation après un nouveau téléchargement
ou une modification de sous-titre ; elle n’est pas automatique dans cette version.

Le travail continue si l’onglet est fermé. **Arrêter l’inventaire** conserve l’ancien
index ; une nouvelle actualisation recommence son examen sans altérer les fichiers.
Les pistes mal formées, téléchargements en cours et liens symboliques détectés
ne deviennent pas des ressources prêtes. Un fichier remplacé après indexation
est refusé jusqu’à l’actualisation. Les fichiers finaux sont présumés terminés
par leur nom et l’absence de marqueur : aucun décodage intégral ne le certifie.

## Chercher et lire

Les titres/descriptions participent au filtre de Collections. **Rechercher** réunit
documents et vidéos ; les paroles ne sont cherchées que dans les pistes locales
qui passent les contrôles techniques. Un titre seul ne décrit pas toute la vidéo.
Les différents passages d’un média sont regroupés sous un résultat « Vidéo ».
Un passage trouvé ouvre le lecteur à son horodatage et garde la langue de sa piste
dans le texte envoyé à l’assistant.

Le lecteur propose la piste française locale quand elle existe, la langue source
et **Sans sous-titres**. Les SRT sont servis en WebVTT sans changer l’original.
La lecture, le changement de piste et les déplacements dans le média fonctionnent
sans Internet ni IA. La position est mémorisée par profil et navigateur pour la
même révision ; un passage explicitement trouvé prend priorité sur cette position.
Quitter le lecteur met la vidéo en pause.

Le décodage dépend du format et du navigateur. Un MKV/AVI peut demander un lecteur
installé : le lien **Ouvrir la vidéo originale** reste disponible. Le logiciel ne
transcode pas automatiquement le fichier. Un message explique un échec de lecture.
Chromium et WebKit ont lu une petite fixture VP8/WebM ; cela ne certifie pas les
codecs de tous les fichiers de Marc ni Safari sur son téléphone réel.

## Utilisation par l’assistant

Une question ordinaire peut chercher et lire des sous-titres et des documents,
avec références et horodatages. On peut choisir la vidéo pour l’assistant comme
un document. Une vidéo sans piste n’a **aucune parole consultée** : son titre et
sa description ne deviennent pas une transcription. L’IA ne voit pas les images
et ne comprend pas les gestes grâce au seul texte des sous-titres.

L’aperçu contient au plus 80 segments et 100 000 caractères à partir du passage
demandé ; la lecture partielle reste signalée. La synthèse longue et la traduction
intégrale de vidéos ne sont pas encore préparées : elles refusent cet aperçu au
lieu de perdre silencieusement ses horodatages. La création/traduction synchronisée
des pistes est un chantier distinct. Les favoris et classements humains gardent
la même référence vidéo ; un classement humain ne certifie pas la procédure.

## Rapport et sous-titres manquants

**Télécharger le rapport vidéo** fournit l’état de chaque vidéo : pistes trouvées,
langues déclarées, origine fournie/automatique/inconnue, erreurs, contrôles et
prochaine action. Une piste nommée « fr » n’est pas une preuve de langue française,
de traduction fidèle ou de synchronisation ; la relecture humaine reste à faire.
Une piste distante annoncée dans `.info.json` n’est pas disponible hors ligne.

Sans piste exploitable, le média reste lisible et cherchable par ses métadonnées,
avec **Sous-titres à préparer**. Il ne disparaît pas du rapport. Récupération en
ligne, transcription des manques, traduction synchronisée et validation réelle
de chaque vidéo restent à développer/exécuter selon le
[protocole R6](../essais/protocole-sous-titres-videos.md).

## Installation et conservation

Le pilote reçoit le montage **en lecture seule** de `library/video/` vers `/videos`.
Le lanceur crée le dossier s’il manque, sans copier de vidéo. Windows et Linux
utilisent la même API ; le laboratoire reste protégé par ses contrôles de montage.
Une mise à jour de code dans une installation active doit passer par la procédure
de maintenance, qui recrée les services avec ce montage.

L’index `state/pilot/videos.db` et son rapport sont séparés des originaux et de
l’index documentaire principal. Une actualisation est transactionnelle : l’ancien
index reste utilisable tant que le nouveau n’est pas terminé. Les statuts et
révisions de taille/date détectent des changements observés, pas toute altération
possible. L’[outil d’inventaire en ligne de commande](inventaire-videos.md) reste
disponible, sans modifier cet index du site.
