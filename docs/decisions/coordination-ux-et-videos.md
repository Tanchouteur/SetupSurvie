# Coordination de la refonte UX et des vidéos

**Consigne de travail actuelle — 16 novembre 2026.** Louis autorise le démarrage
de l’implémentation UX par son autre agent pendant la fin du lot vidéo. Cette
autorisation ne signifie pas que la refonte est déjà intégrée ou déployée.

Chaque agent garde sa branche et son worktree. Les lots **0.33.0** et **0.33.1**
sont intégrés sur `main` (`fafc21e` au début du raccordement audio), avec les
corrections de `codex/campagne-windows-20261116` (`802232c`). L’intégration de la
suite audio et de l’UX doit être successive, par fusion normale, puis reprise de
`main` dans l’autre branche et tests des fonctions conservées. Ne pas écraser les
fichiers générés d’une autre livraison. Le numéro de la livraison UX se choisit
à cette intégration, d’après le dernier `main`, sans réutiliser un numéro livré.

## Contrats à conserver pendant la refonte

Le correctif moteur **0.33.1** complète ensuite le classement dans
`pilot/retrieval.py`. Il ne change aucun écran, route ni identifiant ; les versions
API/release/README sont les seuls autres points de code partagés à réconcilier.

La suite audio **0.34.0** est sur `codex/audio-videos-archives`. Elle raccorde
`pilot/archive_videos.py`, `transcriptions.py` et `speech_worker.py`, avec le nouveau
`archive_media.py`. Routes et identifiants sont conservés. Le champ vidéo public
`audio_transcription_supported` permet aux contrôles existants de `transcriptions.js`
et `captions.js` d’accepter les médias inclus sans piste. Le générateur actualise
seulement les clés de cache de ces deux scripts. La lecture seule du site ne doit
toujours pas démarrer une reconnaissance ou un modèle.

- Le moteur documentaire, les contrôleurs hôtes et les bases de données ne sont
  pas à réécrire pour changer leur présentation. Conserver conversations,
  dossiers, documents associés et préparations existantes.
- Les commandes vidéo du portail utilisent `portal/nouveau/videos.js`,
  `captions.js`, `transcriptions.js`, `acquisitions.js` et le nouveau
  `archive-videos.js`. Les identifiants existants et événements
  `survie:video-cards`, `survie:videos-changed`, `survie:source` et `survie:auth`
  restent nécessaires tant que leurs consommateurs n’ont pas été adaptés ensemble.
- `scripts/build_next_portal.py` inclut ces scripts ; régénérer les deux HTML
  avec ce script. Réconcilier ses inclusions et versions de cache, sans perdre
  les composants du lot vidéo.
- Les nouvelles routes `/api/zim-videos` et `/api/admin/zim-videos/{start,pause,report}`
  complètent les routes `/api/videos` et de préparation des sous-titres.
  Ouverture d’un onglet ou lecture ne doit pas déclencher l’examen lourd, un
  téléchargement, une transcription ou un démarrage IA.
- Les messages distinguent examen terminé, mise en recherche terminée, piste
  présente, traduction automatique et relecture humaine. Un index en cours ne
  devient pas un résultat vide définitif.

La version API dans `pilot/app.py`, `deploy/release.json`, le README et les
documents partagés se réconcilient au moment de l’intégration. Une version UX
future ne doit pas être annoncée comme disponible sur les PC avant leur mise à jour.

Voir la [direction à trois zones](conversations-trois-zones.md) et les
[objectifs décidés par Louis](choix-actuels.md#deux-prochains-objectifs--décision-de-louis-du-16-novembre-2026).
