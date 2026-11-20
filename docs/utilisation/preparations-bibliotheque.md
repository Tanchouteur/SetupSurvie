# Préparations de la bibliothèque et suivi des travaux

**Guide actuel — SetupSurvie 0.66.0, 20 novembre 2026.** Ce guide décrit les
travaux disponibles dans le logiciel. La progression d'une installation se
consulte sur son propre appareil.

## Collections et documents

| Travail | Résultat et déclenchement | Suivi |
| --- | --- | --- |
| Sélectionner, télécharger ou importer les collections, puis vérifier les fichiers | Les archives vérifiées rejoignent la file d'indexation. Une archive partielle ne passe pas pour complète. L'installateur peut aussi copier les archives d'un kit. | Téléchargements et, pour les opérations remontées par le PC serveur, File d'attente. |
| Préparer l'outil des archives | Installe et teste le lecteur ZIM. L'installation en ligne le prépare. Une installation existante peut demander **Préparer l'outil**. L'examen des archives fonctionne ensuite hors ligne. | **Préparer la recherche dans les archives** et carte de préparation du PC serveur. |
| Examiner les index natifs et créer les compléments | Réutilise les index natifs compatibles avec Kiwix. Extrait et indexe le texte des autres archives. Peut démarrer après un téléchargement vérifié dans le créneau autorisé. | Panneau des archives, rapport d'indexation et carte **Indexation des documents**. |
| Organiser les collections | Le profil Famille choisit **Fonds principal** ou **Autre**. Une suppression est une opération séparée, confirmée et suivie. | **Organiser les collections**. La suppression a sa propre carte dans la file. |
| Classer les archives du Fonds principal | Prépare l'index par espace pour les archives ZIM du Fonds principal, en commençant par les grandes éditions de Wikipédia en français. La recherche utilise chaque index dès qu'il est prêt. **Toute la bibliothèque** utilise les index habituels. | Panneau des archives et carte **Classement du fonds principal**. Reprise dans le panneau après une pause manuelle. |
| Indexer et classer les guides locaux et les pages de PDF | Le pilote indexe les guides et les passages lisibles au démarrage ou lors d'une actualisation. Les pages de PDF reçoivent une indication automatique par page. Une correction manuelle s'applique au PDF entier. | État de l'index des guides et rapports documentaires. Cette indexation n'a pas de carte de travail dédiée dans la file. |
| Traduire puis publier un document local | Le modèle traduit par passages. Une traduction publiée rejoint l'index documentaire. | Travail de traduction suivi dans le profil concerné. L'indexation de la publication passe par le pilote. |
| Corriger le classement d'un élément | Depuis son lecteur, le profil Famille donne la priorité à son choix. Une correction d'article peut rendre l'index par espace de son archive à refaire. | Formulaire **Corriger le classement**. La reconstruction éventuelle se suit dans le panneau des archives. |

L'extraction textuelle ne traite pas les scans sans texte par OCR et n'indexe pas
la parole des vidéos. Voir [Rendre les archives recherchables](indexation-archives.md)
et [Classer les documents et nommer les collections](classement-et-collections.md).

## Vidéos et sous-titres

| Travail | Résultat et déclenchement | Suivi |
| --- | --- | --- |
| Télécharger des vidéos YouTube | Une liste lancée volontairement peut fournir les médias, métadonnées et pistes disponibles. | File d'attente et suivi YouTube. |
| Découvrir les vidéos locales | Parcourt les fichiers locaux et leurs métadonnées et pistes associées. L'actualisation peut démarrer au lancement ou à la détection d'un changement. | Gestion de la vidéothèque et carte **Inventaire des vidéos et sous-titres** pendant le travail. |
| Découvrir les vidéos des archives | Examine séparément les ZIM avec le lecteur d'archives. La première installation programme cet examen pour les archives présentes. Les lecteurs particuliers et pistes non extraites peuvent limiter la couverture. | Gestion de la vidéothèque, rapport et carte **Inventaire des vidéos dans les collections**. |
| Indexer les vidéos et classer celles du Fonds principal | Indexe titres, descriptions et texte des pistes exploitables avec leurs repères de lecture. Le classement utilise le titre, le début de la description et le début de chaque piste exploitable. Il peut retenir les deux espaces. Le texte recherché peut couvrir toute la piste, même si le classement échantillonne son début. | Même actualisation et même carte que l'inventaire vidéo. Une absence de piste laisse le titre et la description disponibles. |
| Récupérer une piste YouTube existante | Récupère une piste d'une vidéo identifiée. Nécessite Internet et une demande depuis le lecteur. | **Récupérations YouTube** et créneau Téléchargements. |
| Préparer puis utiliser Whisper | L'installateur prépare le moteur local ou le récupère depuis le cache du kit. Une transcription demandée décode l'audio et crée une piste horodatée en langue source. | **Transcriptions audio** et créneau Préparation locale. La préparation du moteur fait partie de l'installation. |
| Traduire une piste en français | Un modèle local installé et démarré traduit une piste exploitable en conservant ses horodatages. La traduction peut suivre une transcription demandée avec l'option française. Le suivi YouTube prévoit aussi une préparation automatique selon les options du lot. | **Suivi des sous-titres** et créneau Assistant et traductions. |
| Publier et réindexer les pistes | Après les contrôles techniques, la récupération, la transcription et la traduction demandent chacune une actualisation de l'index vidéo. Elle rend la piste recherchable et peut mettre à jour le classement. Le suivi d'une piste distingue sa publication de la demande d'actualisation. | Suivi de la piste et carte d'inventaire. Le suivi YouTube peut attendre que la piste soit dans l'index. |

Les sous-titres automatiques décrivent les paroles reconnues. La qualité du
contenu et les gestes à l'image demandent un examen humain. Dans **Vidéos
uniquement**, le choix entre les deux espaces ne filtre toujours pas
individuellement les vidéos. **Toute la bibliothèque** inclut aussi les groupes
rangés dans **Autre**. Voir [Retrouver et lire les vidéos](videos-locales.md).

## Ce que la file d'attente rassemble

Le portail reçoit une liste commune via `/api/work-queue`. Le pilote y assemble
les travaux qu'il programme, les états des inventaires relus dans leurs rapports
et la préparation que le contrôleur du PC serveur signale via `/activity`.
Le classement du fonds, les compléments d'index et la préparation de l'outil
remontent par ce contrôleur. L'examen vidéo des collections peut remonter par
deux voies. Le pilote rattache alors les détails du PC serveur à la carte
existante.

Le contrôleur garde ses propres créneaux et commandes. La pause et le
réordonnancement communs concernent les tâches pilotées par la file. Les
préparations indépendantes s'arrêtent ou reprennent depuis leur panneau.
L'historique et la progression dépendent de la source des états. Un inventaire
vidéo réussi peut quitter la file alors que son rapport reste disponible.
Pour une piste traitée individuellement, le statut **terminé** de la carte
peut indiquer une publication avec l'actualisation de l'index encore à suivre.

Voir [Suivre les travaux de SetupSurvie](file-attente.md) pour les commandes et
les créneaux visibles dans le portail.
