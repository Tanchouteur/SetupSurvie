# Vidéos locales dans la recherche commune

**Complément du 16 novembre 2026 — 0.23.0 :** le [guide actuel](../utilisation/videos-locales.md)
décrit l’index volontaire des titres/descriptions et pistes locales, la recherche
commune, le lecteur et l’export par vidéo. Acquisition, transcription, traduction
synchronisée, ZIM et relecture du fonds de Marc restent à faire. L’étude ci-dessous
est conservée avec sa date ; elle ne remplace pas ce guide.

**Besoin confirmé par Louis — 14 novembre 2026 ; inventaire local livré en 0.14.0.** Marc a ajouté
un dossier `video` dans `library/` pour ses téléchargements YouTube en 480p afin
de limiter l’espace occupé. Chemin rapporté : **`library/video/`** ; aucun accès
au disque de Marc n’a été effectué pour en vérifier le contenu.

Une recherche doit pouvoir réunir documents et vidéos explicatives. Le traitement
ne se limite donc plus aux médias inclus dans les ZIM. Le dossier local doit être
inventorié sans imposer de recopier les vidéos dans les archives ou dans Git.

## Progression retenue

1. Recenser les fichiers réellement présents, leur titre, chaîne/source, langue,
   durée, format, taille et métadonnées associées quand disponibles. Dédupliquer
   sans perdre l’accès à l’original et repérer les fichiers encore en téléchargement.
2. Permettre une première recherche dans titres/descriptions, en signalant ce
   périmètre limité ; ne pas prétendre avoir cherché dans les paroles.
3. Récupérer les pistes existantes, puis transcrire localement les paroles si
   nécessaire, par segments reprenables. Préparer une piste française à partir
   des sous-titres/transcriptions, avec contrôles et relecture distincts.
4. Indexer les segments textuels et leurs horodatages dans le moteur commun.
   Présenter vidéo/document, langue et origine de la transcription, avec accès
   au passage concerné et conservation de l’ouverture complète du média.
5. Lire les médias et pistes préparés hors ligne, sans modèle IA chargé ; conserver
   progression, pause/reprise explicite, erreurs et état par vidéo.

La résolution 480p n’est pas une preuve de qualité sonore ni de compréhension.
Les contrôles vidéo par vidéo suivent le
[protocole des sous-titres français](../essais/protocole-sous-titres-videos.md).
La traduction de documents et la traduction synchronisée partagent les mécanismes
appropriés, mais leurs validations restent distinctes. Aucun téléchargement ou
transcription lourde n’est exécuté dans le runner ; les essais utilisent de petits
médias synthétiques. L’ajout du besoin ne déclare pas ces fonctions déjà livrées.

## Étude technique pour L5/L6

**Étude du 14 novembre 2026 ; aucun traitement des vidéos de Marc effectué.**
Le premier livrable vidéo doit être un inventaire/export en lecture seule :
fichiers terminés, identifiant stable, métadonnées utiles et pistes associées,
puis état par média. Ne pas attendre la transcription pour rendre les titres
recherchables. Les fichiers `.part` et téléchargements en cours restent exclus.
La déduplication doit garder la source et les titres, sans exiger une recopie.

Pour une source YouTube encore accessible, `yt-dlp` distingue sous-titres fournis
et pistes automatiques, permet de lister les langues, de récupérer les pistes
et les métadonnées sans retélécharger le média. Prévoir français puis langue
source et distinguer piste humaine, transcription automatique et traduction
automatique. Une langue annoncée ne garantit pas le contenu. Voir les
[options officielles de sous-titres](https://github.com/yt-dlp/yt-dlp#subtitle-options).
L’outil, sa version et sa distribution hors ligne restent à choisir et vérifier ;
aucun téléchargement YouTube n’a été lancé pour cette étude.

Pour les ZIM, inventorier les éléments vidéo et leurs `<track>` réellement
présents, puis les pistes accessibles dans la même archive. Ne pas déduire
l’existence d’une piste d’un titre TED ou d’un lien externe. Les chemins de média
et de piste doivent suivre les contrôles de lecture locale ; un échec ne bloque
pas les résultats documentaires. Relever les sources non examinées.

Sans piste exploitable, étudier la réutilisation du modèle de dictée déjà préparé,
sans téléchargement implicite. `faster-whisper` fournit des segments horodatés ;
PyAV décode l’audio avec ses bibliothèques FFmpeg. La compatibilité des codecs des
vidéos réelles doit néanmoins être testée. Voir sa
[documentation officielle](https://github.com/SYSTRAN/faster-whisper).
Le mode `translate` de Whisper vise **l’anglais**, pas le français : garder une
transcription dans la langue source, puis une étape de traduction française.
Voir la [documentation Whisper](https://github.com/openai/whisper#command-line-usage).
Le modèle de dictée préparé et le contrat de ses fichiers sont déjà décrits dans
`deploy/versions.json` ; sa présence chez Marc et sa fidélité vidéo restent à mesurer.

La file durable doit séparer inventaire, acquisition, transcription, traduction,
contrôles et publication. Elle conserve les segments terminés et les horodatages
de l’original. Une reprise explicite après arrêt doit traiter seulement les unités
restantes, respecter le mode jeu et laisser les questions prioritaires passer.
Indexer la transcription source et sa traduction avec origine/langue, révision
et intervalle temporel ; ne pas faire passer le texte traduit pour une source native.
Un nouveau média ou une piste remplacée invalide les segments correspondants.

Le lecteur cible conserve l’original et ajoute une piste française locale WebVTT,
désactivable, avec accès au passage trouvé. Les fichiers originaux restent intacts.
Contrôler fichiers mal formés, temps inversés, chevauchements, segments manquants,
langue et allongement du texte ; distinguer anomalie technique et sens non vérifié.
Un petit média synthétique suffit pour tester la reprise et la navigation, puis
R6 doit examiner chaque vraie vidéo. Windows, Chromium et WebKit sont à tester ;
le contrôle Safari iPhone réel reste distinct.

## Traduction de pages et de livres

Firefox traduit localement avec des langues installées sur l’appareil. Préparer
les langues source/cible avec Internet, puis vérifier une vraie page Kiwix après
redémarrage et coupure Internet sur le PC de Marc ; ne pas présumer les langues
présentes ni le même fonctionnement sur tous les téléphones. Ce complément ne
prépare pas de sous-titres ni une traduction partagée du livre. Références Mozilla :
[traduction locale](https://www.mozilla.org/en-US/firefox/features/translate/) et
[installation des langues](https://support.mozilla.org/en-US/kb/website-translation).

Le moteur documentaire existant découpe déjà un livre en passages enregistrés.
Un livre de 500 pages n’est donc pas envoyé en une seule question : les
[limites actuelles](../utilisation/documents-et-traduction.md#taille-des-documents-et-livres-longs)
restent celles de l’extraction et du volume. L’étude initiale décrivait un contexte
fixe de 8 192 tokens ; depuis 0.20.1, la traduction reprend le contexte configuré,
borné par le modèle et ses budgets. Aucune traduction réelle de
500 pages n’est validée. L5 doit ajouter comparaison original/français, glossaire
et cohérence entre passages, puis mesurer chapitre et livre, sans annoncer que
le seul contexte agrandi résout la cohérence. Conserver les contrôles actuels de
nombres, unités et refus ; ils ne certifient pas le sens.

Ordre proposé après correction du moteur : inventaire/export vidéo, titres dans
la recherche, récupération de pistes, lecture locale, traduction synchronisée,
transcription des manques, puis recette complète par vidéo. Chaque étape reste
utilisable sans forcer la suivante ; aucune étape n’est annoncée livrée ici.

## Première étape intégrée — 0.14.0

L’[outil d’inventaire local](../utilisation/inventaire-videos.md) recense les vidéos
et pistes SRT/WebVTT associées et produit un état par média, en lecture seule.
Les contrôles techniques ne valident ni la langue, ni le sens, ni la lecture
synchronisée. Les médias des ZIM et pistes intégrées aux conteneurs ne sont pas
examinés par ce premier outil. Le [bilan d’intégration](../essais/2026-11-15-integration-outils-validation-videos.md)
distingue tests fictifs et recette réelle à exécuter. Recherche par titre ou paroles
et lecteur ont ensuite été ajoutés en 0.23.0 ; acquisition, transcription et
traduction synchronisée restent à développer.
