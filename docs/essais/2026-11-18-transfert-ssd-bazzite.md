# Premier transfert réel entre SSD sur Bazzite

**Recette du 18 novembre 2026.** Louis demande de mettre à jour l’installation
Linux neuve, de la transférer sur l’autre SSD et de corriger les défauts
rencontrés dans un worktree dédié.

## Point de départ

L’installation Docker rootless de l’essai était active en 0.43.2 sur le SSD
système Samsung 990 PRO 1 To, partition `nvme0n1p3`. La destination est un
nouveau dossier sur le Crucial P3 Plus 4 To, partition `nvme1n1p1`, avec Btrfs
sur les deux disques. Le volume initial de transfert compte **10 383 fichiers
ordinaires**, **151 541 992 106 octets**, ainsi que **deux liens Ollama**. Les
images Docker s’ajoutent à ce volume. Docker rootless et son stockage restent
sur le SSD système.

La mise à jour 0.43.2 → 0.43.3 a terminé avec sa sauvegarde et son journal. La
seconde mise à jour a installé la 0.44.0 de `main` avec le correctif testé. La
livraison du correctif est numérotée 0.44.1, une correction compatible sans
migration du schéma ni modification des versions tierces.

## Journal des problèmes

| Constat | Correction et preuve |
| --- | --- |
| Le contrôleur n’est plus joignable après la fin de la commande de mise à jour lancée à distance dans une unité systemd transitoire. | L’unité suivante conserve ses processus avec `Type=oneshot` et `RemainAfterExit=yes`. L’API du portail confirme que le contrôleur répond après la mise à jour. |
| Le PC quitte le LAN au moment du premier lancement de la copie. | Le journal système confirme une veille demandée par PowerDevil à 12 h 27, suivie d’une reprise à 15 h 03, en heure locale. Aucun dossier de copie ni garde source à la reprise. Un inhibiteur temporaire `sleep:idle` est vérifié avant le nouvel essai. |
| Le transfert refuse un lien de manifeste Ollama v2. | Le transfert conserve les liens relatifs vers des blocs réguliers du même magasin Ollama et les vérifie après copie. Un lien vers un bloc externe, même lisible, est refusé. |
| L’installation Linux possède un environnement Python YouTube avec des chemins liés à la source. | Le dossier Python généré est exclu, le cache de roues est vérifié, et l’activation tente la reconstruction hors ligne. Le rapport indique si les outils sont prêts. |
| Le texte de secours renvoie au lanceur Windows sur une copie Linux. | Le texte renvoie à `transferer-setupsurvie.sh` pour une copie Linux. |

## Interruption et reprise

Le seul processus de copie a été interrompu par SIGKILL au milieu d’un gros
fichier. Le préfixe observé avant l’arrêt faisait **452 984 832 octets**. La
reprise avec les mêmes dossiers a repris la copie et le contrôle des empreintes.
