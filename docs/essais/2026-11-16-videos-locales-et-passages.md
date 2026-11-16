# Vidéos locales et passages de sous-titres — 16 novembre 2026

**Bilan de développement 0.23.0.** Nouvelle fonction compatible, niveau mineur ;
schéma principal 1, images tierces et profils conseillés conservés. Le
[guide actuel](../utilisation/videos-locales.md) décrit les actions et les limites.
Ni média ni piste de Marc n’ont été examinés, aucun déploiement client effectué.

## Réalisé

L’inventaire standard de 0.14.0 est partagé avec le pilote sans dupliquer le
parseur. Un index SQLite/FTS séparé contient titres/descriptions et segments
horodatés des pistes SRT/WebVTT techniquement exploitables. La recherche commune
mélange documents et vidéos, groupe les passages et préserve la piste effectivement
trouvée. L’assistant lit du texte et le cite ; il ne voit ni images ni gestes.

Collections permet l’actualisation explicite, l’arrêt et l’export par vidéo.
Originaux montés en lecture seule, publication transactionnelle de l’index,
refus d’un média/piste modifié, maintien de l’ancienne base après arrêt/échec.
Le lecteur sert le média avec requêtes HTTP par plages, sous-titres WebVTT locaux,
choix de langue/désactivation, accès au passage et position conservée par profil.
Un média sans piste reste visible avec ses limites et sa prochaine action.

La traduction intégrale et la synthèse longue refusent les aperçus vidéo pour
conserver les horodatages ; leur préparation complète reste à développer. La
récupération en ligne et la transcription ne sont pas ajoutées par cette livraison.

## Vérifications

Neuf tests API/index sur fichiers minuscules couvrent recherches françaises et
anglaises, langue/passage conservés, mélange document/vidéo, lecture par lot de
l’assistant, modification/suppression de fichier, absence de piste, conversion
SRT sûre, téléchargements incomplets/liens, arrêt/reprise, favoris, classement
humain, autorisations et HTTP Range réel. Les vingt tests de l’inventaire partagé
restent réussis. La suite complète locale comptait 786 tests (quatre ignorés
réservés à Windows), avant les dernières précisions de suivi/limite d’aperçu.
CI finale et paquet restent à consigner.

Une fixture créée pour ce dépôt, aplat vert VP8/WebM de douze secondes, 1 135 octets,
est réellement décodée dans Chromium et WebKit. Vingt contrôles par navigateur :
indexation depuis Collections, piste absente, recherche commune, accès à huit
secondes, pistes française/anglaise/désactivée, position conservée, aucune IA de
lecture, tailles 1366/390/320, pause en quittant et export par vidéo. Un premier
rejeu a révélé que l’ancien état « terminé » pouvait être lu immédiatement après
un nouveau lancement ; l’état serveur et le message de l’interface sont maintenant
changés avant l’attente asynchrone. Les assertions de lecture sont conservées.

## Modèle réel

R7, `gemma4:e4b` préexistant, Ollama natif 0.40.14, contexte 16k, 32 couches GPU,
six threads, sortie au plus 2 048 tokens, maintien quinze secondes et réserve
vidéo 1 536 Mio. La recette `tests/real_video_check.py` refuse les modèles tiers
et n’effectue aucun téléchargement, déchargement forcé ni traitement audiovisuel.

Deux sources fictives se contredisent : guide 23 mm, piste vidéo à huit secondes
17 mm. Le rapport privé `report-gemma4-videos.json` termine en **13 454 ms**, cite
les deux sources réellement lues et distingue les deux nombres. La réponse relue
signale explicitement la limite aux paroles écrites et l’absence de vérification
physique ; elle n’invente pas une observation des gestes. Empreinte Python :
`bfd89e86a40978765136d35638d0fe0ed12d7882dc8792ab24557d1cd4e00240`.
Le suivi de lancement et la taille de l’aperçu ont ensuite été complétés ; leur
contrôle est séparé de ce résultat réel. Aucun essai sur les vidéos de Marc.

## Restant

Télécharger ou créer des pistes françaises, conserver leur préparation par
segments, relecture humaine par vidéo, ZIM et pistes intégrées aux conteneurs,
gros fonds, Windows de Marc et iPhone réel restent à qualifier/développer.
Le décodage d’un aplat vert n’est pas un test de reconnaissance vocale ou de
traduction. Les origines, langues déclarées et contrôles techniques ne certifient
pas le sens, l’exhaustivité des paroles ni l’utilité pratique d’un geste.
