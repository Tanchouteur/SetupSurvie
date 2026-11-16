# Des MP4 seuls aux sous-titres recherchables

**Bilan candidat 0.26.0 — 16 novembre 2026.** Nouvelle fonction compatible,
avec état distinct des traductions : version mineure. La livraison et la CI ne
sont pas encore acquises. Le [guide vidéo](../utilisation/videos-locales.md)
décrit le parcours prévu par ce candidat.

## Réalisation

`transcriptions.py` conserve des unités audio dans `video-transcriptions.db`.
Un enfant privé `speech_worker.py` décode le média avec PyAV et utilise le modèle
Whisper small déjà préparé pour la dictée, sur CPU/int8, sans téléchargement.
La révision épinglée du modèle et le marqueur de préparation sont vérifiés avant
lancement. Les dépendances sont celles de l'image Open WebUI existante ; aucune
image tierce ni empreinte de modèle n'est modifiée. Leur fonctionnement dans le
conteneur installé chez Marc reste à vérifier.

Les unités d'une minute gardent deux secondes de contexte de chaque côté.
Les mots sont affectés selon leur milieu temporel et leurs limites sont bornées
par l'unité. Une fin de fichier atteinte dans le contexte de l'unité précédente
ne fait pas perdre la dernière fraction. Les longues pauses et les grands groupes
de mots donnent plusieurs sous-titres courts. Les temps restent estimés par la
reconnaissance, jamais certifiés exacts. Les segments bruts restent dans le rapport
privé ; les images et gestes ne sont pas interprétés.

La file partage le verrou de l'assistant par unité, respecte la pause, termine
et rejoint son seul enfant à l'arrêt. Une pause pendant création de l'enfant ne
le laisse pas tourner seul. Le redémarrage attend une reprise explicite ; les
unités terminées ne sont pas reconnues à nouveau. Les diagnostics refusent un
travail concurrent. La publication rejoint son thread et recontrôle l'état actif.
Un média changé, une chronologie incohérente, aucune parole ou aucune piste audio
ne devient pas une piste prête. Les originaux restent en lecture seule.

Seule la transcription complète rejoint l'index vidéo. La traduction française
réutilise la file existante, ses contrôles et ses horodatages. Une phrase coupée
entre deux sous-titres est traduite comme fragment ; ce découpage ne justifie
pas à lui seul un refus ni l'invention de la fin de phrase. Une traduction reste
associée au contenu exact de sa transcription source. Une ancienne bonne piste
reste stockée mais n'est pas rattachée à une source remplacée.

## Tests sans modèle

Douze tests de workflow passent sur de petits fichiers fictifs : indexation source
et française, fin située dans le contexte, pause/reprise, source modifiée, refus
de publier du silence ou un média sans audio, invalidation du français et arrêt
des seuls enfants de test. La création annulée de l'enfant est également rejointe.
Sept tests vérifient le protocole, l'affectation des mots aux unités, la négation,
les longues pauses, les anomalies et l'absence de logs privés dans le JSON.
Les treize tests de traduction de pistes existantes passent aussi.

Les mots du navigateur sont simulés ; ils ne valident pas un moteur vocal. Quinze contrôles du parcours audio passent dans chacun des navigateurs Chromium
et WebKit : création explicite, pause/reprise, conservation, lien vers la
traduction courante, index et rapport. La recette attend ce travail précis au
lieu de confondre une ancienne préparation terminée avec la nouvelle. La suite
locale précédente compte 828 tests, quatre réservés à Windows ignorés ; le cas
supplémentaire de proposition rejetée est vérifié séparément. Le paquet et la CI suivent.

## Essai réel R7

Un MP4 de 132 secondes, 852 × 480, 267 806 octets, est créé pour l'essai : image
noire et quatre phrases anglaises synthétiques, placées à 1, 54, 62 et 119 secondes.
La voix provient du runtime Kokoro déjà installé, voix `af_heart`, anglais américain ;
aucune voix humaine personnelle ni vidéo de Marc. Les silences sont longs : cet
exemple ne représente pas deux minutes de parole dense ni le bruit d'une vidéo
YouTube. Les fichiers et sorties de cette recette restent hors Git.

Le R7 avait environ 15 942 Mio de VRAM libres et aucun modèle Ollama chargé.
Whisper small épinglé `536b0662742c02347bc0e980a01041f333bce120` est préparé
dans le seul laboratoire R7 (486 213 828 octets). L'environnement isolé utilise
faster-whisper 1.2.1, CTranslate2 4.9.0 et PyAV 19.0.2. Il reste environ 3,1 Go
libres sur ce disque après préparation ; pas de corpus ou modèle ajouté au runner.
Aucun service tiers ni profil GPU modifié.

Le premier probe échoue : PyAV 19 n'accepte plus l'option `metadata_errors` passée
par le candidat. L'appel est corrigé et le décodage de la piste AAC mono 24 kHz
retrouve 132 000 ms. Le premier découpage laisse un sous-titre présent pendant
un long silence ; le regroupement est corrigé pour utiliser les pauses entre mots.

Reconnaissance seule : trois unités traitées sur CPU/int8, quatre threads,
sept segments retenus. Les nombres, couleurs et la négation sont reconnus ;
« four hundred and twenty » devient `420`. Cette normalisation vient du moteur
vocal, pas de la traduction. Les frontières à 60 et 120 secondes conservent les
fragments et la fin. Ce contrôle limité ne certifie pas toutes les paroles.

Premier parcours complet `report-workflow.json` : transcription terminée mais
Gemma renvoie `status: refused` pour les fragments. Aucun français incomplet
n'est publié ; la proposition refusée reste dans le rapport. La consigne générique
est précisée pour les phrases coupées, sans fusionner ni déplacer leurs segments.

Rejeu `report-workflow-v2.json` : **22 031 ms** pour MP4 → transcription → français
→ index, trois unités et sept segments source/français, original inchangé. La
traduction utilise Gemma `gemma4:e4b`, Ollama 0.40.14, contexte 16k, sortie 4 096,
24 couches GPU, six threads, réflexion désactivée et maintien quinze secondes.
La garde vérifie la place initiale, puis la marge GPU libre et les modèles tiers.
Aucun déchargement forcé ; Ollama ne conserve plus de modèle après expiration.

Les sept couples de texte sont relus : 17 millimètres, 420, couleurs bleue/rouge/
verte/jaune, négation et condition de batterie conservées. Les phrases coupées
restent réparties aux mêmes temps. Tous les contrôles techniques de traduction
passent. Empreinte Python du rejeu :
`5c1839c7ed4d6d0d5fb3d12785d253dae742329ac65909e7aa5e6a68ddf89043`.
Le rapport porte encore la base 0.25.0 sur laquelle le candidat était construit ;
ce n'est pas un déploiement 0.26.0 chez Marc ni une mesure Windows.

Le [manifeste amont de l'image Open WebUI v0.12.5](https://github.com/open-webui/open-webui/blob/v0.12.5/backend/requirements.txt)
épingle faster-whisper 1.2.1 et PyAV **14.0.1**. Le laboratoire est donc aussi
rejoué avec cette version PyAV, sans changer l'image produit. Le rapport
`report-workflow-av14.json`, candidat 0.26.0, termine en **22 118 ms**, avec les
six contrôles de parcours réussis et les sept traductions à nouveau relues.
Le CPU utilise ici quinze threads selon la disponibilité annoncée par le R7 ;
la reconnaissance seule précédente utilisait quatre threads. La traduction garde
les mêmes options que ci-dessus. Aucun gain entre ces deux réglages n'est isolé.
Les propositions de reconnaissance rejetées sont désormais conservées dans le
rapport privé et chaque unité enregistre sa version de moteur. Empreinte Python :
`320c23e0324e93c4ebc467fc83aae7d4cc1ab80e8ce7fcd9b0d3e4be089b4d39`.
Ce rejeu vérifie ces dépendances dans un environnement Linux séparé ; le conteneur
Windows installé reste à éprouver et CTranslate2 4.9.0 n'est pas identifié dans
l'image épinglée par ce seul relevé du manifeste amont.

## Travail restant

Valider le parcours navigateur et le runtime emballé, terminer la CI et le paquet,
puis qualifier les vrais MP4. Acquisition de sous-titres en ligne, inventaire et
préparation des vidéos/pistes des ZIM restent distincts et non achevés. Une bonne
traduction de cet exemple n'est pas la validation de chaque vidéo de la bibliothèque.
