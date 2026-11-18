# Téléchargement YouTube réel sur Bazzite et contrôle Windows — 0.43.2

**Bilan daté du 18 novembre 2026.** Le parcours a été exécuté sur l’installation
Linux d’essai de Louis, sous Python 3.15, après mise à jour officielle avec
sauvegarde. Il a utilisé l’API du bouton, le vrai contrôleur de l’hôte, YouTube,
yt-dlp 2026.10.26, Deno 2.9.8 et FFmpeg 8.1.3. Le navigateur n’a pas été utilisé ici.

## Liste essayée

| Ligne | Résultat final |
| --- | --- |
| *Me at the zoo* | H.264 240p + AAC, sous-titres anglais automatiques |
| *Caminandes 2* (Blender) | H.264 480p + AAC |
| *Big Buck Bunny* (Blender) | H.264 480p + AAC, 55,3 Mo, sous-titres fr et en |
| Vidéo indisponible | erreur expliquée |
| Liste de lecture | refusée avant téléchargement |

Une pause réelle a été demandée pendant la liste, puis reprise : les deux vidéos déjà
rangées ont été passées et la troisième terminée. Le site a ensuite répertorié les
trois vidéos sans clic. Une recherche limitée aux vidéos a retrouvé « elephants » dans
les sous-titres à 1,2 s, et l’adresse du média a répondu à une demande de plage HTTP.
Les trois fichiers d’essai restent dans `library/video/youtube/Essai réel/`.

## Défauts trouvés puis corrigés

| Constat | Correction |
| --- | --- |
| HTTP 429 sur des sous-titres : vidéo entière perdue | Nouvelle tentative sans sous-titres, signalée dans le suivi ; pause de 3 s entre sous-titres |
| Fichiers AV1, moins compatibles | H.264 et audio M4A choisis en priorité |
| « This video is unavailable » non reconnu | Message d’indisponibilité |

## Windows

Le job Windows de la CI exécute les tests de l’outil et `tests/youtube_tools_smoke.py` :
préparation réelle de yt-dlp, Deno et FFmpeg, détection par yt-dlp, assemblage FFmpeg,
téléchargement réel depuis un serveur local, rangement avec accents et espaces, puis
recréation hors ligne après copie. Il ne contacte pas YouTube, car les machines de CI ne
représentent pas un PC domestique. Le résultat de la version livrée est celui de la PR.

## Limites

- Aucun téléchargement YouTube réel sur Windows ni sur le PC de Marc.
- Lecture réelle sur iPhone et sous Windows à vérifier.
- YouTube peut limiter ou refuser des requêtes ; aucun contournement n’est prévu.
