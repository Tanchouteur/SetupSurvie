# Vidéos et sous-titres dans les archives ZIM

**Référence du lot 0.33.0 — 16 novembre 2026.** Le parcours comprend maintenant
la commande volontaire dans Collections, son suivi/pause/reprise, l’index commun,
la lecture via Kiwix et la préparation française depuis une piste interne.
Il réutilise le lecteur libzim isolé, sans l’imposer au processus du portail.
Le [guide utilisateur](../utilisation/videos-locales.md#vidéos-dans-les-collections-zim--0330)
décrit le parcours courant. La qualification du fonds réel reste distincte de ces
fonctions ; aucune archive réelle de Marc n’a été examinée dans le runner.

Les médias originaux ne sont pas extraits ni copiés : seuls les petits textes de
pistes techniquement contrôlés rejoignent un cache et l’index. Le lecteur revalide
taille/date de l’archive avant de servir le média par portions, sans suivre un lien
distant. Une archive modifiée exige un nouvel examen. Les contenus sont ensuite
cherchables avec langue et horodatage ; l’assistant lit les paroles, pas les gestes.

Les pistes utilisables rejoignent le parcours français existant avec mêmes temps,
pause/reprise et contrôles. Une piste absente reste absente : reconnaissance audio
des médias internes, interprétation des lecteurs JavaScript et qualification des
codecs/alignements de chaque vidéo réelle restent à poursuivre. Un simple lien
YouTube/Vimeo n’est pas une vidéo présente sur cet appareil.

L’état reconstruit est dans `state/pilot/zim-videos/` ; l’index partagé reste
`state/pilot/videos.db`. Sauvegarde et transfert de tout l’état du pilote les
incluent. Les originaux restent dans `library/zim/`. L’examen natif ne démarre
ni modèle ni téléchargement, refuse le mode jeu et garde le dernier inventaire
publié pendant la reprise du suivant. Le lecteur n’est déclaré à jour qu’après
prise en compte de la même fin de travail, pas de l’ancien inventaire.

Les preuves et limites sont dans le [bilan du lot](../essais/2026-11-16-videos-collections.md).
Ce jalon ne clôt ni L6 ni l’objectif global : les mots, langues, temps et besoins
pratiques du fonds de Marc demandent des observations réelles.

## Historique : première brique avant raccordement au site

**Note de développement conservée — avant le lot 0.33.0.** Complément de L6, distinct
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
ne modifie pas l’index texte ni les originaux. Le contrôleur hôte reconnaît ce
travail via le lecteur isolé, refuse le mode jeu et une préparation absente,
conserve pause et rapport terminal en cas de perte du superviseur. Quatre tests
simulés du superviseur passent, sans redémarrage de services. Les routes et
commandes du portail ne sont pas encore raccordées ; aucune préparation
vidéo ne tourne automatiquement après une mise à jour.

Neuf tests locaux passent sur le lecteur libzim **3.13.1**, avec de petites ZIM
générées : index texte natif sans oubli des vidéos, liens internes/distants,
bonne association des pistes, pages dépassant la limite, reprise après pause,
édition remplacée, sortie paginée bornée, commande multiprocessus réutilisable et chemin d’archive
non examiné conservé dans une couverture globale partielle.
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
