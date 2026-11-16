# Traduction française des pistes locales — 16 novembre 2026

**Bilan candidat 0.24.0.** Nouvelle fonction compatible, donc niveau mineur.
Le [guide actuel](../utilisation/videos-locales.md) décrit la commande depuis
Collections. Le [protocole R6](protocole-sous-titres-videos.md) reste la référence
pour la validation de chaque vraie vidéo ; ce bilan ne la remplace pas.

## Fonctionnement

Une piste SRT/WebVTT exploitable, dans une langue connue autre que le français,
peut être préparée en français avec un modèle local installé. La file durable
stocke les segments, leur texte d’origine et leurs temps. Pause, redémarrage,
mode jeu et reprise restent explicites, et les segments terminés sont réutilisés.
Les questions ordinaires partagent le verrou d’inférence, libéré entre les lots.
Les mesures de calibration et performance détectent aussi cette préparation.

Un lot contient au plus seize segments et environ 2 400 octets de texte source,
sauf un segment indivisible plus long. Le modèle reçoit les identifiants et le
texte des segments ; il ne crée pas les temps. Ordre et identités doivent rester
exacts. Le contrôle de traduction existant garde chiffres, unités et avertissements.
Les propositions bloquées et les erreurs de format sont conservées dans le
rapport privé. Les contrôles n’établissent ni la langue réelle de toute la piste,
ni la fidélité ou la synchronisation.

Une piste complète est écrite durablement dans l’état du pilote, en WebVTT, puis
contrôlée à nouveau avant publication. Les originaux restent en lecture seule.
Le lecteur et l’index fusionnent les pistes préparées dont l’édition source
correspond encore. Aucun brouillon partiel n’est exposé comme piste française.
Une pause joint le thread de publication ; un travail annulé ne peut pas publier
ensuite en arrière-plan. Une actualisation manuelle peut finir un index resté en
attente. Les rapports globaux gardent aussi l’état des préparations.

## Vérifications de développement

Tests sur des fichiers minuscules et une IA simulée : publication complète,
horodatages exacts, recherche commune, origine automatique visible, ancien anglais
conservé, duplication de demande, reprise des seules unités manquantes, chiffres
ou unités modifiés, propositions refusées conservées après reprise, mode jeu,
redémarrage, source remplacée, parcours malveillant, liens symboliques et pause
pendant le thread de publication. API réservée au profil Famille ; lecture d’un
rapport ou ouverture d’une vidéo sans inférence.

La recette navigateur utilise quarante segments et un clip vert synthétique de
12 secondes. Elle prépare seize segments, met en pause, vérifie l’absence de
français partiel, reprend les autres et lit les quarante segments dans le vrai
lecteur. Recherche française, sélection de l’anglais, export et trois largeurs
d’écran sont vérifiés. La première recette fermait un panneau déjà mémorisé
ouvert et confondait une ancienne préparation avec la courante ; les attentes
utilisent maintenant l’identifiant exact et l’état effectif du panneau.
La traduction de cette recette est simulée ; ce n’est pas un essai de modèle réel.

## Essai réel sur le R7

`tests/real_caption_check.py`, Gemma `gemma4:e4b`, Ollama natif 0.40.14, contexte
16 384, sortie au plus 4 096 tokens, 32 couches GPU et six threads. Le GPU et
l’absence de modèle tiers sont vérifiés, avec réserve 1 536 Mio et maintien
quinze secondes. Aucun poids téléchargé, aucun processus tiers arrêté.

Six segments anglais fictifs sont traduits, publiés et indexés en français.
L’original reste identique. Relecture des six traductions : 17 mm, l’interdiction
de remplacer le support de 23 mm par celui de 31 mm, la condition avant de
continuer, la séparation des pièces bleues/rouge et les valeurs 12 V / 8 W sont
conservées correctement. Cela ne valide pas la fidélité de toute une vidéo réelle.
La transcription de l’audio et l’acquisition en ligne ne sont pas exercées.

Rapport privé `report-gemma4-captions.json`, empreinte Python du premier essai :
`93985d41ef64d97a7c1ffa69b6e850ece674651367d21ee694b03796f52a77bc`.
La protection de pause pendant publication et le rapport global ont ensuite été
complétés et testés séparément ; un rejeu final et le reçu de livraison suivent.

## Encore à faire

Acquisition des pistes distantes, transcription locale des manques, sous-titres
intégrés aux conteneurs, médias dans les ZIM et relecture du fonds de Marc restent
ouverts. La langue cible est une demande au modèle, pas une détection certifiée.
Les pauses physiques du PC et Safari iPhone réel ne sont pas validés par la CI.
L’essai long de traduction et le sous-menu de tests demandés ensuite par Louis
sont tracés dans le [plan](../decisions/plan-ameliorations-marc.md).
