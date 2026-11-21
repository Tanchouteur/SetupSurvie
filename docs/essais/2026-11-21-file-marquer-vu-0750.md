# Marquer comme vu dans la file d’attente — 0.75.0

**Bilan daté — 21 novembre 2026, runner CPU (Chromium distant, données fictives).**
Demande de Louis : ne plus voir indéfiniment l’inventaire des vidéos « Terminé
avec des limites » dans « À suivre ». Référence : [guide du portail](../utilisation/portail.md#être-toujours-informé--0700).

## Réalisé

- Table `work_seen` (profil, élément, empreinte, date) créée au démarrage, sans
  changement des tables existantes ni du `data_schema`.
- `pilot/work_queue.py` : les éléments terminés (statut `partial`, `error`,
  `failed`, ou terminé avec des lignes en échec) reçoivent `dismissible`,
  `signature` (empreinte de statut, avancement, étape et erreur) et `seen`.
  Route `POST /api/work-queue/{id}/seen` dans `pilot/routes/work.py`.
- Portail : bouton **Marquer comme vu**. L’élément quitte « À suivre », l’en-tête
  « Tâches » et le résumé de Mon appareil. Il reste dans « Historique récent »
  avec la mention « Vu ».

## Vérifications

- Tests unitaires : marquage par profil, retour de l’élément si son état change,
  refus pour les travaux en cours ou à reprendre ; suite complète (voir le
  message de livraison).
- Nouvelle recette `browser_work_queue_seen.js` (Chromium distant) avec
  `browser_ux_foundations`, `browser_ui_finish` et `browser_settings_ux` : réussies.

## Limites

- Firefox, WebKit et Windows restent vérifiés par la CI GitHub.
- Pas d’essai sur l’installation de Marc ; la carte réelle y disparaîtra après
  la mise à jour et un clic, jusqu’au prochain changement de l’inventaire.
