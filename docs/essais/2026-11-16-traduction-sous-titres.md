# Traduction française des pistes locales — 16 novembre 2026

**Bilan de livraison 0.24.0.** Nouvelle fonction compatible, donc niveau mineur.
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
complétés et testés séparément. Un dernier contrôle a relevé que toute la durée
était rangée dans « file d’attente » ; la mesure distingue désormais préparation,
premier texte, rédaction et contexte observé après génération.

Rejeu final privé `report-gemma4-captions-measured.json` : six traductions à nouveau
correctes sur les mêmes repères, 8 457 ms pour l’appel mesuré, dont 4 865 ms de
chargement et 3 027 ms de génération annoncés. Contexte chargé 16 384, entrée réelle
271 tokens, sortie 209 tokens. Empreinte Python finale :
`7183942f7d945aef73c589e8f30426532126896396e07b3dcf4e8268a573e285`.
Le coût d’une vidéo réelle, la qualité vocale et la traduction de longs contenus
ne se déduisent pas de ces six segments. La suite locale compte 802 tests Python,
quatre réservés à Windows ignorés ; les treize tests de préparation passent après
le dernier ajustement de mesure. Les contrôles CI et le paquet sont consignés
après terminaison.

Code fonctionnel `8775e03`, [huit jobs CI réussis](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43834177218) :
802 tests Python (quatre réservés à Windows ignorés sous Linux), treize tests de
préparation réussis aussi sous Windows et dix-neuf contrôles de préparation dans
chacun des navigateurs Chromium et WebKit. Les autres recettes existantes passent.
WebKit émulé ne valide pas Safari sur un iPhone physique. Captures du parcours
ordinateur/téléphone relues ; aucune interface carte ou recherche documentaire
n’est refondue. Aucun déploiement sur les PC clients.

Paquet `setupsurvie-0240-validated.zip`, commit documentaire `e8527d9`, **843 fichiers**,
6 998 688 octets compressés et 15 728 367 octets décompressés, comparés au commit
avec les filtres Git de fins de ligne Windows et au manifeste :
`098ea97b5bfbd42ae2a4af8e8f02027c8c57e52ea03227960f3189aabb77d3ea`.
Le présent reçu est ajouté après construction. Aucun média, modèle ou rapport
privé n’est ajouté au paquet ; la petite fixture vidéo synthétique reste un test.

## Encore à faire

Acquisition des pistes distantes, transcription locale des manques, sous-titres
intégrés aux conteneurs, médias dans les ZIM et relecture du fonds de Marc restent
ouverts. La langue cible est une demande au modèle, pas une détection certifiée.
Les pauses physiques du PC et Safari iPhone réel ne sont pas validés par la CI.
L’essai long de traduction et le sous-menu de tests demandés ensuite par Louis
sont tracés dans le [plan](../decisions/plan-ameliorations-marc.md).
