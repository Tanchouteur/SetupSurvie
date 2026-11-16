# Coordination de la refonte UX et des vidéos

**Consigne de travail actuelle — 16 novembre 2026.** Louis autorise le démarrage
de l’implémentation UX par son autre agent pendant la fin du lot vidéo. Cette
autorisation ne signifie pas que la refonte est déjà intégrée ou déployée.

Chaque agent garde sa branche et son worktree. Le lot vidéo candidat **0.33.0**
part de `main` **0.32.1**, qui conserve entièrement les corrections de
`codex/campagne-windows-20261116` (`802232c`). L’intégration doit être successive,
par fusion normale, puis reprise de `main` dans la branche UX et tests des
fonctions conservées. Ne pas écraser les fichiers générés d’une autre livraison.

## Contrats à conserver pendant la refonte

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

## Intégration UX 0.34.0

La branche UX a intégré main 0.33.0 (`3dd2409`) avant sa propre livraison.
Les événements, modules et recettes vidéo restent présents. Le retour recommandé
est archivé sous `ux-reference-0.33.0` ; voir le
[bilan UX](../essais/2026-11-16-refonte-ux.md). Cette intégration de code ne
constitue pas une mise à jour des PC cibles.
