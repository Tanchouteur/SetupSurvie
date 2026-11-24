# Réinstallation de SetupSurvie sur Bazzite — 20 novembre 2026

Recette sur le PC de Louis, Bazzite avec RTX 2060 6 Go et Python 3.15.2.
L'installation utilise le SSD Crucial de 4 To, un Docker rootless dédié dont le
stockage est vide au départ, et Docker Compose 5.8.0. Bazzite, Docker, Compose,
Python et le pilote NVIDIA sont des prérequis déjà présents sur la machine.

## Remise à zéro et lancement

- Arrêt et retrait des trois services utilisateur des anciens essais. Suppression
  des deux anciennes installations du Samsung et du Crucial, avec leur stockage
  Docker dédié. Vérification de l'absence des anciens services, du socket Docker
  dédié et d'écoute sur les anciens ports. Les clones, notes et rapports de Louis
  n'appartiennent pas aux dossiers d'installation supprimés.
- Premier lancement sur la 0.69.4 refusé par l'analyseur d'options.
  `scripts/install.sh` plaçait `--work-dir` après la sous-commande, alors
  que celle-ci ne l'acceptait qu'en option globale. La 0.69.5 accepte les deux
  positions et valide les lots avant de créer les dossiers ou de démarrer les
  téléchargements. Niveau correctif compatible, schéma et images tierces inchangés.
- Le vrai lanceur utilise un dossier privé et un dossier de données distincts,
  avec accents et espaces, en mode LAN. Les lots santé, eau,
  Wikilivres et primaire servent de fonds à la recette. Une liste Blender est
  fournie dans la copie de recette du fichier YouTube d'installation, avec un
  doublon, une vidéo indisponible et une adresse de liste de lecture.
- Première interruption volontaire pendant le téléchargement des images Docker.
  La relance conserve les paramètres et termine les téléchargements. Deuxième
  interruption pendant le téléchargement de Wikilivres, avec un partiel
  de 18 874 368 octets conservé. La relance reprend avec les mêmes chemins.
- Les refus du lanceur sont vérifiés avec un lot inconnu, des options
  hors ligne et en ligne combinées, un autre dossier de données, un autre
  mode GPU, un volume temporaire trop petit et Docker absent. Les deux erreurs
  d'options ne créent ni dossier de données ni réglages privés.

## Fonds et vidéos préparés automatiquement

- Les 17 ressources choisies, soit 1 690 743 700 octets, passent une seconde
  vérification de taille et de SHA-256. Kiwix affiche Wikilivres et Wikiversité.
  La file d'indexation des ZIM traite les deux archives et revient à zéro.
  Le classement des collections se termine. Une recherche Chromium trouve
  des articles et des PDF du lot eau. Le lecteur rend la page d'un PDF et une
  requête partielle reçoit son en-tête `%PDF-` avec HTTP 206.
- Le lanceur installe les cartes Sud et Solliès-Ville, ainsi que le relief et
  les points d'intérêt locaux. Le portail sert le début de l'archive PMTiles
  avec sa signature. Les graphes OSRM relèvent d'une préparation séparée.
- L'inventaire vidéo des deux archives démarre seul et publie un résultat
  partiel. Il parcourt 308 511 entrées, dont 106 pages HTML dépassent la limite
  de 2 Mo et sont signalées comme ignorées pour le repérage des vidéos.
- La liste YouTube de la première installation rejoint la file automatiquement.
  Deux films Blender, *Sintel* et *Big Buck Bunny*, sont téléchargés en MP4,
  puis trouvés par titre. La file lance la transcription Whisper sur CPU et
  traduit les pistes produites. Pour *Sintel*, la piste anglaise et la piste
  française ont chacune 21 repères. La recherche retrouve le même passage à
  120 000 ms par le texte anglais et par le texte français. Les deux pistes
  sont servies en WebVTT. La vidéo répond en HTTP 206 avec son en-tête MP4.
  Les pistes produites restent des transcriptions et traductions automatiques.

## Rejeu du suivi YouTube et mise à jour

La 0.69.5 affiche « 4 / 3 » dans la file et compte le doublon dans les vidéos
déjà présentes. La 0.69.6 corrige le calcul de progression et le bilan sans
changer le schéma ni les dépendances. Le dossier applicatif de cette recette
a été enregistré dans les réglages privés avant le test du paquet logiciel.

Le paquet 0.69.6 est appliqué avec le lanceur `pilot_update.py`,
sa vérification SHA-256 et son instantané préalable. Le journal termine
en `complete`. Le compteur de l'ancienne ligne est corrigé au démarrage.
Le rejeu depuis la file affiche **3 / 3** dans Chromium et identifie deux
vidéos déjà présentes, une indisponible et deux lignes écartées. Les deux MP4 gardent leur
SHA-256. La vidéo indisponible, le doublon et la liste de lecture sont des
cas introduits volontairement dans la liste d'essai.

## Redémarrage des services et ajout de contenu

- Démarrage de l'unité SetupSurvie alors que son Docker dédié est arrêté.
  systemd programme une nouvelle tentative. Une fois Docker disponible, la
  tentative automatique rétablit le portail 0.69.6, son contrôleur et les
  vidéos déjà rangées. Les deux unités sont activées avec linger.
- Ajout du guide *Botanique* de Tela Botanica par `content.py download`,
  après l'installation. La recherche le trouve à la page 61 à l'issue du
  téléchargement. Les 16 PDF téléchargés ont tous des passages non vides
  dans l'index SQLite, dont le contrôle d'intégrité est réussi.
- Arrêt temporaire du seul conteneur Ollama. Le portail conserve la recherche,
  la lecture PDF, les collections Kiwix et la page de secours. Ollama répond
  de nouveau après sa remise en service.
- Le portail répond sur l'IP locale en HTTP et HTTPS. Le portail, Kiwix et
  Open WebUI répondent depuis le runner. Les ports internes 11435 et 11436
  sont inaccessibles depuis le réseau utilisé par le runner. La confiance du
  certificat HTTPS et la résolution de `survie.local` restent à vérifier
  sur les appareils clients.

La recette occupe **36,8 Go** sur le Crucial, instantané de mise à jour et
rapports compris. L'API 0.69.6 est saine. La suite Python finale exécute
**1 224 tests, dont 7 ignorés**, sans échec. La vérification syntaxique du
JavaScript et les contrôles Chromium de la recherche, du PDF et du compteur
YouTube sont réussis.

Le redémarrage physique du PC, la préparation des prérequis sur un OS
nouveau et le transfert autonome vers un autre SSD sans Internet feront
l'objet d'une recette distincte.
