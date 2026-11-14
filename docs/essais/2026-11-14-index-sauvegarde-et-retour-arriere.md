# Conserver les index pendant la maintenance

**Bilan daté — version corrective 0.9.3, 14 novembre 2026.** Suite L1/L9 de
la fiabilisation du moteur. Ce travail ne résout ni ne reconstitue l’incident
des 135 archives de Marc, dont le rapport R1 reste attendu.

## Défaut reproduit

Avec le code 0.9.2, une sauvegarde privée termine et publie `backup.json` alors
que le verrou d’une indexation CLI est détenu. Les services sont simulés, mais
le verrou OS et les fichiers sont réels. Le refus des tâches Web actives ne
couvre donc pas tous les chemins d’indexation. Copier un SQLite, son manifeste
et sa progression pendant leurs écritures ne donne pas un instantané cohérent.

Le retour arrière supprimait aussi tout `state/pilot`, y compris les fichiers
de verrou. Détenir un verrou sur l’ancien fichier puis le supprimer permettrait
à un autre écrivain de créer un nouveau fichier de même nom. Sur Windows, cette
suppression peut également être refusée tant que le fichier est ouvert.

## Correction

- La sauvegarde acquiert les mêmes verrous que les tâches Web, publications,
  transferts CLI et indexation, avant l’arrêt des services. Une indexation active
  entraîne un refus sans nouvel instantané ni arrêt du site.
- La mise à jour conserve ces exclusions pendant son instantané, le remplacement,
  les contrôles de démarrage et l’éventuel retour arrière. La récupération manuelle
  les acquiert aussi ; un refus initial ne laisse pas de journal « préparé ».
- Chaque processus d’extraction détient en plus son verrou par archive. Tous ces
  fichiers sont enregistrés avant de soumettre les tâches. La maintenance fige
  leur ensemble : un processus sans superviseur bloque encore la copie, et une
  tâche démarrée tardivement ne peut pas écrire au milieu de celle-ci.
- Un nouveau lancement refusé par un de ces verrous signale `index_busy` et garde
  l’outil prêt ; il ne classe pas le lecteur comme manquant ou l’archive comme
  corrompue. Aucun écrivain n’est tué ni verrou inconnu supprimé pour forcer le passage.
- Les nouveaux instantanés excluent les `.lease` des états. Les anciennes entrées
  sont vérifiées, puis ignorées à la restauration. Le nettoyage du retour arrière
  conserve les fichiers de verrou existants, leur identité et leur possession.

La protection concerne les commandes livrées, pas des copies manuelles du dossier
en cours d’écriture. Pour passer d’une ancienne version à 0.9.3, arrêter ou mettre
en pause les préparations et attendre leur fin : le programme de mise à jour déjà
installé ne reçoit pas rétroactivement ces nouvelles exclusions.

## Vérifications

Tests ciblés : sauvegarde refusée avant arrêt, verrou détenu pendant la copie,
index SQLite FTS5 retrouvé après restauration vers des dossiers vides, ancien
fichier de verrou ignoré, mise à jour refusée sans journal incomplet, et maintien
des exclusions pendant l’échec de démarrage puis le retour arrière. Un fichier
ajouté par ce démarrage défectueux disparaît, l’ancien index et le même fichier
de verrou sont conservés.

Un processus jetable exécute le vrai wrapper d’extraction avec une extraction
simulée bloquée. Le verrou du superviseur est libre, celui du processus est actif :
la sauvegarde refuse. Après sa mort forcée par le test, elle réussit et conserve
l’index précédent. Un autre test bloque une tâche déjà enregistrée pendant la
maintenance. L’interruption d’une sauvegarde libère aussi ses verrous et ne la
présente pas comme terminée. Aucun processus utilisateur ou service réel n’est tué.

Les 486 tests locaux passent, dont trois ignorés. La
[CI du code livré](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43625480527)
sur `a77699c` réussit ses huit travaux : Linux, Windows Python 3.12, lecteur isolé
Windows 3.11/3.13/3.14, Kiwix réel synthétique, calcul de trajet synthétique et
interface Chromium/WebKit. Chaque navigateur passe 48 contrôles de recherche et
18 de préparation/indexation. `git diff --check`, 276 liens locaux et leurs
ancres sont vérifiés sur les documents modifiés.
La première recette Windows a détecté une comparaison du chemin temporaire court
avec son équivalent canonique dans le nouveau test de retour arrière. Les chemins
de la fixture sont désormais résolus comme ceux de l’installation ; aucun défaut
du verrou ou de la copie n’est déduit de cet échec d’instrumentation.
Les services de restauration sont simulés ; l’essai SQLite n’est ni une
réinstallation de Windows ni une copie autonome de tout le serveur. Les formats,
versions tierces et schémas de données sont inchangés : le niveau correctif `z`
est retenu. La copie physique du fonds, les délais et les recettes de Marc restent
distincts de ces essais. Le [guide des index](../utilisation/indexation-archives.md)
et le [guide de maintenance](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)
décrivent les gestes courants.
