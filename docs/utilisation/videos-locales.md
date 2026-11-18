# Retrouver et lire les vidéos

**Guide actuel — 0.49.5, 18 novembre 2026.** Les fichiers restent dans
`library/video/` du disque de données, avec leurs sous-dossiers. Cette fonction
concerne les fichiers locaux et, après examen volontaire, les médias présents
dans les collections ZIM. Le fonds complet de Marc reste à vérifier.

Pour plus tard, Louis propose d'étudier une [voix française générée à partir des sous-titres traduits](../decisions/boite-a-idees.md), notamment avec Qwen TTS. Cette piste n'est pas une fonction disponible.

## Préparer depuis le site

Après la mise à jour de maintenance, choisir **Famille → Bibliothèque → Collections →
Vidéos de la bibliothèque → Gestion de la vidéothèque → Actualiser les vidéos et leurs sous-titres**. Cela lit les noms,
les métadonnées `.info.json` et les pistes `.fr.srt`, `.en.vtt`, etc. à côté du
média. Aucun téléchargement, reconnaissance vocale ou modèle IA n’est lancé par cette actualisation.
Attendre « Inventaire terminé », puis rechercher avec le filtre des Collections
ou dans **Rechercher**.

Depuis 0.40.0, ce bouton n’est plus indispensable : le répertoire s’actualise tout
seul au démarrage du service, puis au plus une fois par minute lors d’une
recherche, si des vidéos, sous-titres ou `.info.json` ont été ajoutés, modifiés ou
retirés. Le contrôle ne lit que les noms, tailles et dates des fichiers ; il ignore
les téléchargements en cours (`.part`, `.ytdl`…). L’ancien répertoire reste
consultable pendant l’actualisation. Un inventaire arrêté avec **Arrêter
l’inventaire** n’est relancé automatiquement que si les fichiers changent ensuite ;
un inventaire interrompu par un redémarrage reprend au démarrage suivant. Les
vidéos des collections ZIM gardent leur examen volontaire, plus long (voir plus bas).

Le travail continue si l’onglet est fermé. **Arrêter l’inventaire** conserve l’ancien
index ; une nouvelle actualisation recommence son examen sans altérer les fichiers.
Les pistes mal formées, téléchargements en cours et liens symboliques détectés
ne deviennent pas des ressources prêtes. Un fichier remplacé après indexation
est refusé jusqu’à l’actualisation. Les fichiers finaux sont présumés terminés
par leur nom et l’absence de marqueur : aucun décodage intégral ne le certifie.

## Chercher seulement les vidéos — 0.40.0

Dans **Bibliothèque → Rechercher**, le menu **Documents et vidéos** propose
**Vidéos uniquement** et **Documents uniquement**. Avec **Vidéos uniquement**, on
peut laisser la recherche vide : toutes les vidéos répertoriées s’affichent, par
ordre alphabétique de titre. Avec des mots, la recherche porte sur les titres,
descriptions et sous-titres prêts. Ce mode ignore l’espace « Autonomie et
résilience / Savoirs et culture » : les vidéos sont rarement classées et ne
doivent pas disparaître d’une recherche dédiée. Le choix est conservé dans
l’adresse de la page et revient avec le bouton Précédent.

Si aucune vidéo n’apparaît, le message distingue : répertoire pas encore créé
(il se lance tout seul), actualisation en cours, dossier `library/video/` absent,
ou aucune vidéo correspondant aux mots. Une absence de résultat ne prouve pas
que les collections ZIM non examinées sont sans vidéo.

## Chercher et lire

Le bouton **Vidéos** en haut de Collections ouvre directement la liste vidéo.
Les titres et descriptions participent au filtre de Collections. **Rechercher** réunit
documents et vidéos ; les paroles ne sont cherchées que dans les pistes locales
qui passent les contrôles techniques. Un titre seul ne décrit pas toute la vidéo.
Les différents passages d’un média sont regroupés sous un résultat « Vidéo ».
Un passage trouvé ouvre le lecteur à son horodatage et garde la langue de sa piste
dans le texte envoyé à l’assistant.

Dans **Sous-titres**, le réglage **Automatique** choisit le français si une
piste existe pour une vidéo anglaise, puis l’anglais. Une vidéo française s’ouvre
sans sous-titres. Si la langue parlée est inconnue, le lecteur privilégie
le français, puis l’anglais. Pour les autres langues, il affiche une piste
française si elle est disponible.

Choisissez une piste ou **Sans sous-titres** dans le menu du lecteur pour
mémoriser ce choix pour cette vidéo, avec votre profil et dans ce navigateur.
Sélectionnez **Automatique** pour revenir au réglage par défaut. Si la piste
mémorisée devient indisponible, le lecteur utilise le réglage automatique.
Les SRT sont servis en WebVTT sans changer l’original.
La lecture, le changement de piste et les déplacements dans le média fonctionnent
sans Internet ni IA. La position est mémorisée par profil et navigateur pour la
même révision ; un passage explicitement trouvé prend priorité sur cette position.
Quitter le lecteur met la vidéo en pause.

## Créer, traduire et suivre les sous-titres dans le lecteur — 0.45.0

Avec le profil **Famille**, ouvrez une vidéo depuis une recherche, un lien de
l’assistant ou les Collections. Sous le lecteur, choisissez **Créer les
sous-titres depuis l’audio** si aucune piste n’est lisible. Vous pouvez demander
la version française en même temps. Si une piste source est déjà disponible,
ouvrez **Préparer une piste française**, choisissez la piste et lancez la
traduction.

Le lecteur affiche l’attente, l’avancement, les erreurs et les résultats de
cette vidéo, avec les commandes **Mettre en pause** et **Reprendre**. Vous
retrouvez le suivi en rouvrant la vidéo. Dès que l’inventaire a pris en compte
la nouvelle piste, elle rejoint le menu **Sous-titres** sans fermer le lecteur.
**Lire la transcription** déroule les paroles disponibles. Sur un grand écran,
les sous-titres et les options se placent à côté de la vidéo lorsqu’elle est
ouverte directement, sans liste de résultats.
**Qualité des sous-titres** affiche les informations de provenance et les limites
des pistes. Dans **Collections → Vidéos**, les cartes affichent d’abord le titre,
l’état des sous-titres et **Voir la vidéo**. **Options de sous-titrage** regroupe
les commandes de la carte. **Suivi des sous-titres** rassemble les travaux et
leurs rapports, et **Gestion de la vidéothèque** contient les commandes d’inventaire.

## Vidéos dans les collections ZIM — 0.33.0

Choisir **Famille → Bibliothèque → Collections → Vidéos de la bibliothèque → Gestion de la vidéothèque →
Vidéos dans les collections → Examiner ou reprendre les collections**. L’outil
d’archives doit avoir été préparé dans **Paramètres → Bibliothèque**. Cet examen
ne télécharge rien et ne lance pas l’IA. Il peut durer longtemps au premier
passage ; le nombre de collections terminées et les pistes lisibles sont affichés.
**Mettre l’examen en pause** conserve les points de reprise. Reprendre reste
volontaire après un redémarrage ou une pause.

L’examen continue si la page est fermée. Les anciennes données terminées restent
disponibles pendant le suivant. Ensuite, une mise à jour du lecteur et de la
recherche prend les pistes en compte. Si le service a redémarré entre-temps,
**Actualiser le lecteur vidéo** permet de terminer cette étape. Le rapport des
collections conserve l’examen, les erreurs et les archives non examinées.

Les vidéos effectivement incluses apparaissent avec les fichiers locaux. **Ouvrir
l’article d’origine** conserve l’accès au document qui les héberge. Le lecteur
passe par Kiwix sur votre appareil ; un Internet coupé n’empêche pas cette lecture.
Si Kiwix est arrêté, les textes de pistes déjà préparés restent cherchables,
mais la lecture du média doit attendre son retour.

Les paroles sont cherchées seulement dans une piste techniquement exploitable.
Le résultat indique sa langue et ouvre le média au passage trouvé. Une piste
source interne peut être traduite avec **Préparer une piste française** ; les
mêmes temps et contrôles que pour un fichier local sont conservés. Ces pistes
restent automatiques et demandent une comparaison à l’original.

L’examen lit les références explicites des pages HTML ; il n’interprète pas tous
les lecteurs JavaScript. Un lien distant ne prouve pas que le média est téléchargé.
Les conteneurs vidéo peuvent aussi contenir des pistes non extraites : elles ne
sont pas automatiquement prêtes. Depuis 0.35.0, la commande audio ci-dessous est
aussi disponible pour les médias inclus sans piste exploitable. Avant cette
préparation, une vidéo se cherche par son titre, pas par des paroles inventées.
Une archive remplacée nécessite un nouvel examen.

## Créer les sous-titres d’une vidéo de collection — 0.35.0

Après l’examen des collections, ouvrir **Créer les sous-titres depuis l’audio**
sur une vidéo sans piste exploitable. Choisir la langue parlée ou la détection
automatique, puis **Créer les sous-titres**. La case **Préparer aussi la version
française** utilise ensuite le modèle choisi pour les préparations. Comme pour
un MP4 local, la reconnaissance doit avoir été préparée une fois par l’installateur ;
elle utilise ensuite ses fichiers locaux, sans Internet.

Kiwix doit fonctionner sur cet appareil. La vidéo est lue par portions, sans
extraire une copie entière avant de commencer. Le suivi compte la durée audio
traitée et les segments conservés. **Mettre en pause** arrête notre outil audio ;
**Reprendre** réutilise les unités terminées de la même édition. Fermer la page
ne l’arrête pas. Après un redémarrage ou le mode jeu, la reprise reste volontaire.

La piste source complète rejoint la recherche et le lecteur ; le français a son
propre suivi de préparation. Les deux pistes restent sélectionnables. Un brouillon
ne devient pas une piste prête. L’absence de piste audio ou un échec du lecteur
est signalé, sans publier un faux succès. Une reconnaissance terminée peut encore
se tromper dans les mots : l’écouter et la comparer à l’original reste nécessaire.
Si Kiwix utilise une ancienne édition après le remplacement d’une collection,
arrêter puis rouvrir SetupSurvie avec ses raccourcis, puis refaire l’examen. Un
ancien travail dont la source a changé ne sera pas repris sur une autre édition.

Le **rapport audio** conserve les passages, la reconnaissance, les contrôles et,
pour les médias de collection, les requêtes/octets et le temps de lecture HTTP.
Ces octets sont transférés, parfois relus ; ils ne mesurent pas les lectures du
disque. Les temps de décodage, chargement et reconnaissance restent distincts.
Le rapport contient les paroles : le conserver comme un document privé.

Comparer le début, le milieu, la fin et les passages techniques avec l’audio.
Les mots et leurs temps sont estimés ; les images ou gestes ne sont pas reconnus.
Les lecteurs distants et listes de diffusion ne deviennent pas des fichiers locaux.

Le décodage dépend du format et du navigateur. Un MKV/AVI peut demander un lecteur
installé : le lien **Ouvrir la vidéo originale** reste disponible. Le logiciel ne
transcode pas automatiquement le fichier. Un message explique un échec de lecture.
Chromium et WebKit ont lu une petite fixture VP8/WebM ; cela ne certifie pas les
codecs de tous les fichiers de Marc ni Safari sur son téléphone réel.

## Préparer une piste française depuis le site — 0.24.0

Le modèle reçoit le nombre exact de segments à traduire. Depuis **0.49.5**,
SetupSurvie réduit aussi les lots quand une réponse est tronquée ou illisible,
ou que les identifiants sont modifiés ou réordonnés. Quand un contrôle échoue
pour un segment, les segments valides sont enregistrés et celui qui a échoué
est réessayé seul. Un échec persistant laisse la piste en brouillon et le rapport
indique le problème. Les propositions rejetées restent dans le rapport.
Un refus explicite arrête le travail et la pause reste prioritaire.

Choisir **Famille → Bibliothèque → Collections → Vidéos de la bibliothèque**. Sur une carte vidéo,
ouvrir **Options de sous-titrage → Préparer une piste française**, choisir la langue source puis **Traduire
les sous-titres**. Le modèle se choisit dans **Suivi des sous-titres → Modèle de traduction**. Il doit être installé et démarré volontairement. Une vidéo sans
piste exploitable utilise le parcours audio ci-dessous ; ce bouton de traduction seul ne connaît pas ses paroles.

Le suivi compte les segments terminés. **Mettre en pause** conserve ces segments ;
**Reprendre** utilise le modèle choisi pour les segments restants. Un redémarrage,
un mode jeu ou un moteur arrêté attend une reprise explicite. Fermer l’onglet
n’arrête pas un traitement en cours. Les questions et traductions documentaires
partagent la file IA ; celle-ci est libérée entre les petits lots de sous-titres.
Les essais de performance/calibration refusent une préparation concurrente.

Les horodatages sont copiés de la source, jamais inventés par le modèle. Un lot
perdant un segment ou modifiant son ordre est refusé. Les changements détectés de
nombres/unités bloquent la publication. Pour une piste déclarée en anglais,
un montant comme « $70,000 » garde la même valeur s’il est écrit
« 70 000 dollars » en français. Les négations et longueurs suspectes peuvent
produire des avertissements. **Télécharger le rapport** conserve segments source,
traduction, propositions refusées, modèle et contrôles. Ce rapport contient du
texte de la vidéo et doit rester privé. Le rapport vidéo général inclut aussi
l’état des préparations, sans le texte des segments.

Seule une piste complète, passant les contrôles techniques, rejoint le lecteur et
la recherche. L’index est actualisé après publication ; si un inventaire était
déjà actif, relancer **Actualiser les vidéos et leurs sous-titres**. Le lecteur
propose **fr · traduction locale**, garde la piste source et permet de désactiver
les sous-titres. La lecture fonctionne ensuite sans Internet ni IA.

Comparer début, milieu, fin et passages techniques avec l’original. Une piste
préparée n’est pas une traduction relue, ni une preuve de bonne synchronisation.
Une modification du média ou de sa piste source empêche de reprendre l’ancien
brouillon et retire l’association de l’ancienne traduction après actualisation.
Les anciens fichiers et brouillons restent conservés pour comparaison.

Essai du 18 novembre 2026 sur Bazzite avec GPT-OSS 20B et un contexte de
8 192 jetons. À partir des 93 segments du rapport Windows, une préparation
isolée a produit une piste française complète avec les 93 horodatages d’origine.
Trois avertissements ont été conservés. Le test a utilisé les sous-titres du
rapport et un média factice. La fidélité à l’audio et la reprise sur
l’installation Windows de Marc restent à vérifier.

## Récupérer les pistes YouTube — 0.31.0

Dans **Famille → Bibliothèque → Collections → Vidéos de la bibliothèque**, ouvrir
**Options de sous-titrage → Récupérer sur YouTube** sur le média. Si son adresse est déjà associée au fichier,
laisser le champ vide ; sinon, copier l’adresse exacte de la vidéo correspondante.
Le logiciel ne cherche pas cette adresse depuis un titre approximatif.
Choisir la piste automatique, française ou anglaise, puis **Récupérer les sous-titres**.
Cette commande nécessite Internet ; elle ne télécharge pas la vidéo.

Le choix automatique privilégie le français, puis la langue déclarée de la vidéo,
puis l’anglais. Dans une même langue, une piste déclarée fournie est prioritaire
sur une piste automatique. « Français » accepte aussi une variante comme `fr-FR`.
Une langue annoncée par YouTube ne prouve pas que la piste a été relue.

Le suivi est sous **Suivi des sous-titres → Récupérations YouTube**. **Mettre en pause** arrête la requête ; **Reprendre avec Internet** la
relance à votre demande. Fermer la page ne l’arrête pas ; après un redémarrage,
la reprise reste explicite. Un refus du fournisseur ou une piste absente reste
une erreur expliquée, avec la création locale depuis l’audio comme autre possibilité.
Aucun contournement de blocage n’est exécuté.

Seule la piste complète contrôlée rejoint le lecteur et la recherche. Elle reste
ensuite utilisable sans Internet ni IA. La case **Traduire ensuite en français si
nécessaire** utilise le modèle local choisi si la piste récupérée est dans une autre
langue. Si le moteur est arrêté ou en pause, la piste source reste disponible ;
lancer sa traduction depuis la vidéo après avoir rétabli le moteur. Une récupération
terminée n’atteste pas que sa traduction est elle aussi terminée.

Les intervalles qui se chevauchent sont raccourcis pour l’affichage, sans retirer
les mots ; les temps bruts et chaque ajustement restent dans le rapport privé.
**Télécharger le rapport de récupération** contient donc des paroles de la vidéo.
Le lecteur affiche l’origine et demande de vérifier l’alignement avec votre média
local : une autre édition ou un montage peut avoir des temps différents. Les
originaux restent intacts. Les pistes et leurs états suivent la sauvegarde et le
transfert de l’installation ; aucun compte YouTube n’est nécessaire pour ce parcours.

## Créer les sous-titres depuis un MP4 seul — 0.26.0

Dans **Famille → Bibliothèque → Collections → Vidéos de la bibliothèque**, actualiser les
vidéos dans **Gestion de la vidéothèque**. Sur une carte sans piste exploitable,
ouvrir **Options de sous-titrage → Créer les sous-titres depuis l’audio**, choisir la langue parlée ou la détection automatique, puis **Créer les
sous-titres**. **Préparer aussi la version française** utilise ensuite le modèle
choisi dans les préparations de pistes. Aucun traitement ne démarre à la lecture
ou à l’ouverture de Collections.

La reconnaissance réutilise le modèle local préparé pour la dictée. S’il manque,
le message demande cette préparation par l’installateur, une fois avec Internet ;
le bouton ne télécharge rien. Une fois préparée, elle fonctionne hors ligne,
sur le processeur du serveur. La traduction française utilise aussi un modèle
local installé et volontairement démarré. La pause IA est respectée.

Le suivi est dans **Suivi des sous-titres → Transcriptions audio**. **Mettre en pause** garde les passages terminés ;
**Reprendre** continue les autres. Fermer la page ne stoppe pas le serveur, mais
un redémarrage attend une reprise explicite. Aucun sous-titre partiel n’est annoncé
prêt. Une vidéo modifiée demande une nouvelle préparation après actualisation.

La transcription source complète rejoint la recherche et le lecteur, puis sa
version française lorsque celle-ci termine. Les deux pistes restent distinctes.
**Télécharger le rapport audio** conserve les paroles, temps estimés, informations
sur le moteur et anomalies : ce fichier contient le texte de la vidéo et reste privé.

Comparez les passages utiles, en particulier nombres, noms techniques et négations,
avec la vidéo. La reconnaissance peut se tromper, mal estimer les temps ou manquer
une langue/un son ; elle ne décrit pas les gestes ni les images. Une vidéo sans
audio ou sans parole reconnue ne reçoit pas de sous-titre vide présenté comme prêt.
Les résultats réels limités de cette version sont dans le [bilan](../essais/2026-11-16-transcription-audio-videos.md).

## Demander une vidéo à l’assistant — 0.40.0

Quand la question parle de vidéo (« trouve une vidéo pour faire du feu », « montre
une vidéo de la bibliothèque »), l’assistant cherche d’abord dans les vidéos
répertoriées, avec les mots utiles de la question, ou sans mot-clé pour une
demande générale. Il reçoit pour chaque vidéo son titre, sa chaîne, sa durée, les
langues de sous-titres prêtes et un lien qui ouvre le lecteur. Il peut aussi
lancer lui-même cette recherche avec l’outil `find_videos`. Si rien ne correspond
au sujet, il reçoit aussi quelques autres vidéos disponibles et le nombre de
vidéos répertoriées, pour ne pas conclure que la bibliothèque n’en contient aucune.

Si le modèle oublie de donner les liens, le logiciel ajoute à la fin de la réponse
une liste **Vidéos trouvées dans la bibliothèque** avec ces liens. Ces liens
proviennent uniquement des résultats réels. Un titre n’est pas une parole
consultée : pour résumer une vidéo, l’assistant doit lire ses sous-titres comme
un document. Une vidéo sans piste reste proposée par son titre seulement.

Depuis 0.43.4, si la demande porte sur un sujet, l’assistant lit d’abord les
sous-titres exploitables des vidéos trouvées : il peut répondre sur leur contenu,
sans demander de confirmation. Les liens mal écrits par le modèle sont réparés, et
les liens réels restent affichés si sa réponse est rejetée. Ce parcours a été essayé
avec de vrais modèles sur des vidéos fictives ([bilan](../essais/2026-11-18-demandes-videos-modele-reel.md)) ;
il reste à essayer avec le modèle et le fonds de Marc.

## Utilisation des paroles par l’assistant

Une question ordinaire peut chercher et lire des sous-titres et des documents,
avec références et horodatages. On peut choisir la vidéo pour l’assistant comme
un document. Une vidéo sans piste n’a **aucune parole consultée** : son titre et
sa description ne deviennent pas une transcription. L’IA ne voit pas les images
et ne comprend pas les gestes grâce au seul texte des sous-titres.

L’aperçu contient au plus 80 segments et 100 000 caractères à partir du passage
demandé ; la lecture partielle reste signalée. La synthèse longue et la traduction
documentaire intégrale refusent cet aperçu au lieu de perdre ses horodatages.
La traduction synchronisée utilise le parcours vidéo ci-dessus. Les favoris et classements humains gardent
la même référence vidéo ; un classement humain ne certifie pas la procédure.

## Rapport et sous-titres manquants

Dans **Gestion de la vidéothèque**, **Télécharger le rapport vidéo** fournit l’état de chaque vidéo : pistes trouvées,
langues déclarées, origine fournie/automatique/inconnue, erreurs, contrôles et
prochaine action. Une piste nommée « fr » n’est pas une preuve de langue française,
de traduction fidèle ou de synchronisation ; la relecture humaine reste à faire.
Une piste distante annoncée dans `.info.json` n’est pas disponible hors ligne.

Sans piste exploitable, le média reste lisible et cherchable par ses métadonnées,
avec **Sous-titres à préparer**. Il ne disparaît pas du rapport. Récupération en
ligne (0.31.0), transcription des MP4 locaux (0.26.0), examen ZIM (0.33.0) et audio
interne (0.35.0) sont des parcours distincts. La validation réelle de chaque vidéo
reste à exécuter selon le
[protocole R6](../essais/protocole-sous-titres-videos.md).

## Installation et conservation

Le pilote reçoit le montage **en lecture seule** de `library/video/` vers `/videos`.
Le dossier s’appelle `video`, au singulier : un dossier `library/videos/` n’est pas lu.
Depuis 0.41.0, et depuis le site en 0.43.0, l’outil [Télécharger une liste de vidéos YouTube](telecharger-videos-youtube.md)
range les vidéos dans `library/video/youtube/`, avec `.info.json` et sous-titres ;
le répertoire les reprend ensuite tout seul.
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

Les préparations sont dans `state/pilot/video-captions.db` et
`state/pilot/video-captions/`. Les originaux de `library/video/` restent montés
en lecture seule. Sauvegarder tout l’état du pilote conserve les brouillons,
contrôles et pistes publiées. Les mises à jour de code ne les suppriment pas.
