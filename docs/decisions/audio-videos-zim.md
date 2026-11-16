# Reconnaissance audio des vidéos internes

**Chantier isolé — 16 novembre 2026, non livré.** Suite de la 0.33.0 sur
`codex/audio-videos-archives`. Le lecteur et les pistes internes existent ; la
création de sous-titres depuis leur audio n’est pas encore raccordée au site.

## Lecture choisie

Utiliser un objet lisible avec déplacement pour le décodeur audio, servi par
portions HTTP du Kiwix configuré sur l’appareil. Le descripteur sera construit
par le backend depuis l’inventaire vérifié ; une page HTML ne peut pas désigner
un autre hôte. Le fichier vidéo complet n’a pas à être extrait ni écrit dans un
cache disque avant de commencer. Le cache mémoire de lecture est borné à 256 Kio
par objet ; ce n’est ni une limite de taille des vidéos ni celle du cache de recherche.

Le prototype `pilot/archive_media.py` vérifie l’identifiant de l’édition et le
nom de collection via l’entrée du catalogue Kiwix, puis exige des portions
cohérentes avec la taille du média. Il refuse les redirections, réponses HTML,
portions tronquées, édition changée et lecture complète implicite d’un gros fichier.
Les mesures comptent requêtes, octets transférés, cache mémoire et temps HTTP,
sans enregistrer l’adresse interne dans le rapport. Les octets peuvent être
relus ; il ne s’agit pas d’un total d’octets uniques.

## Preuves présentes

- **Six tests locaux**, service HTTP simulé, en **0,012 s** : déplacements dans
  un fichier de 1,28 Mo, lecture de la fin sans copier le fichier entier, cache,
  entrées invalides, édition/collection, plages, réponses mauvaises et fermeture.
- **Kiwix réel 3.8.1 épinglé**, archive générée de 36 675 octets :
  `/catalog/v2/entry/<uuid>` répond avec l’identité attendue. Un chemin de contenu
  utilisant directement cet UUID répond 404 ; garder le nom de collection pour
  la lecture et vérifier son identité par le catalogue. Aucun corpus téléchargé.

Ces preuves ne valident ni un décodeur, ni la reconnaissance ou le français.
L’interface garde pour l’instant le parcours audio sur les MP4 locaux seulement.

## Raccordement restant

1. Construire le descripteur depuis le seul service configuré, vérifier la
   révision de l’archive avant/après chaque unité et lier la source au travail.
2. Brancher cette lecture dans `speech_worker.py`, avec fermeture sur erreur ou
   pause. Le décodeur ne doit ouvrir ni protocole secondaire, ni liste distante.
3. Réutiliser progression, reprise et publication contrôlée de `transcriptions.py`,
   puis la préparation française et la recherche existantes. Ne pas publier de
   piste partielle ni confondre audio absent et absence d’information.
4. Tester un vrai petit média décodable et la reprise ; mesurer les octets lus.
   Une inférence réelle se fait sur le R7 après ses contrôles de ressources/pause,
   jamais en téléchargeant un modèle dans le runner CPU.

Références primaires de conception : [PyAV, ouverture d’un objet fichier](https://pyav.org/docs/6.2.0/api/toplevel.html)
et [FFmpeg, protocoles autorisés](https://ffmpeg.org/ffmpeg-protocols.html#Protocol-Options).
La version installée reste celle épinglée du projet ; ces références ne changent
aucun composant ni ne remplacent les essais du runtime réel.
