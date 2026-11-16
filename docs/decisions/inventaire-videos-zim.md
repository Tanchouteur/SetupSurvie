# Vidéos et sous-titres dans les archives ZIM

**Chantier en cours — 16 novembre 2026, non livré.** Complément de L6, distinct
à la fois de `library/video/` et d’un index documentaire Kiwix natif. Le code
candidat est isolé sur `codex/zim-video-inventory` ; les commandes du site, la
lecture et la recherche de ces médias ne sont pas encore raccordées. Aucune
archive réelle de Marc n’est examinée dans le runner.

## Première brique réalisée

`pilot/zim_video_inventory.py` examine les entrées de chaque ZIM via le lecteur
libzim épinglé, même si son index texte existe déjà. Il relève les ressources
vidéo/pistes, les éléments HTML video/source/track et certains lecteurs distants
YouTube/Vimeo. Les chemins relatifs, variantes encodées et redirections internes
sont résolus dans l’archive. Les références distantes restent des liens ; aucun
accès Internet, téléchargement ou modèle n’est lancé. Les gros médias ne sont
ni lus en entier ni extraits. Un fichier présent n’est pas déclaré décodé,
transcrit ou traduit fidèlement.

Une base SQLite reconstruisible par archive conserve les ressources, références,
anomalies et curseur. Les écritures sont par points de reprise ; une interruption
ne publie pas une base partielle à la place de la dernière terminée. Une édition
modifiée doit être rescannée ; les données d’une préparation interrompue de
l’ancienne édition restent séparées. Les pages HTML trop grandes, limites de
références et entrées illisibles restent des limites explicites de couverture.

`scripts/inventory_zim_videos.py` fournit une commande de développement explicite,
avec bail OS, réserve disque, processus par archive et rapport de progression.
Elle réutilise le lecteur isolé existant et ses petits caches hors ligne. Elle
ne modifie pas l’index texte ni les originaux. Son exécution n’est pas encore
proposée depuis le site et ne tourne pas automatiquement après une mise à jour.

Huit tests locaux passent sur le lecteur libzim **3.13.1**, avec de petites ZIM
générées : index texte natif sans oubli des vidéos, liens internes/distants,
bonne association des pistes, pages dépassant la limite, reprise après pause,
édition remplacée, sortie paginée bornée et commande multiprocessus réutilisable.
Les fixtures binaires sont délibérément minuscules et non décodables ; ces essais
ne prouvent pas la lecture vidéo. Le test de redirection de piste est conservé
avec son résultat dans les journaux privés de développement.

## Suite requise pour le parcours complet

- Raccorder une préparation volontaire au contrôleur et à l’outil d’archives
  isolé ; garantir arrêt/reprise, coordination avec mises à jour/transfert et
  respect du mode jeu pour les traitements lourds. Ne pas exiger libzim dans le
  processus du portail ou charger un modèle à l’ouverture d’une page.
- Afficher dans Collections ce qui est présent, manquant ou seulement distant,
  avec archives non examinées et anomalies visibles. Garder l’ouverture directe
  de la collection et du document qui héberge la vidéo.
- Servir le média local et les pistes sans Internet, avec demandes partielles
  pour la lecture, chemin/édition revalidés et contrôle du format. Lire les
  sous-titres contrôlés ; ne pas traiter une piste seulement nommée comme prête.
- Joindre les paroles contrôlées à la recherche commune et à l’assistant, avec
  source/temps/langue, puis traduction française locale si demandée. Réutiliser
  la file existante quand possible, sans prétendre à une récupération Internet
  ou reconnaissance de gestes non réalisées.
- Tester de vrais médias synthétiques décodables dans Chromium/WebKit et le
  lecteur isolé Windows, sans gros ZIM téléchargé. La qualification du fonds de
  Marc (disponibilité, audio, langues, fidélité, temps et codecs) reste distincte.

La première énumération de trois ressources synthétiques, avant ce module, est
tracée dans le [choix d’acquisition](acquisition-sous-titres.md#prochaine-étape--les-médias-dans-les-zim).
Ce jalon n’est pas utilisé pour annoncer L6 ou l’objectif global terminé.
