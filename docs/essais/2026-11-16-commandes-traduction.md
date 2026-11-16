# Pause, arrêt, reprise et suppression d’une traduction

**Bilan de livraison 0.29.0 — 16 novembre 2026.** Demande de Louis après la lecture
progressive 0.28.0 ; ne constitue pas la refonte globale des conversations.

Pause et reprise existaient. La livraison ajoute **Arrêter la traduction** et
**Supprimer la traduction**, dans le panneau et dans le lecteur dédié. Arrêter
conserve les passages, donne l’état `stopped` et autorise une reprise volontaire.
Un rechargement ne reprend jamais le travail arrêté, ni son passage interrompu.
La pause est un état temporaire ; l’arrêt indique que l’on met fin au travail
courant, en laissant sa suite récupérable plutôt que de perdre le texte déjà lu.

La suppression demande une confirmation avec son périmètre : travail privé,
instantané source, passages, propositions refusées et suivi. Le document
original, la conversation et les versions déjà partagées sont conservés. Ce
bouton ne retire donc pas une traduction publiée dans la bibliothèque ; il
supprime le travail de la conversation, conformément à l’indépendance des guides
publiés. Après suppression, le travail disparaît du sélecteur et une nouvelle
traduction peut être demandée sur l’original.

Les commandes vérifient le propriétaire. Elles sont sérialisées ; les passages
ne peuvent pas être réécrits par un worker encore actif après suppression.
Le worker est annulé puis rejoint. La publication en thread est aussi rejointe
avant de relâcher son verrou, car annuler `to_thread` n’arrête pas les écritures.
Les guides publiés conservent leur provenance et restent lisibles indépendamment
du travail supprimé. Aucun nouveau modèle, téléchargement ou changement de
contexte. Version **y** pour ces nouvelles actions compatibles, sans migration.

## Vérifications en cours

Tests Python : arrêt avec un passage terminé et un autre interrompu, conservation
après redémarrage, reprise explicite, suppression avec worker actif, contrôle
d’un autre profil, cascades des passages/contrôles, conversation/original
conservés, publication toujours lisible et annulation d’une publication en thread.
Le premier ensemble de 59 tests ciblés réussit.

Une recette navigateur utilise le moteur de traduction simulé ordinaire et sa
base réelle sur petits documents : pause et reprise depuis le lecteur, arrêt,
rechargement sans reprise, seconde reprise, annulation de confirmation, suppression
unique, original/conversation conservés et sélecteur nettoyé. Premier Chromium :
15 contrôles réussis. WebKit, suite complète et CI suivent ; aucune nouvelle
inférence réelle ni commande sur le PC de Marc n’est annoncée.

## Recette locale et intégration

Les quatre recettes de lecture/commande/sélection passent sur Chromium et WebKit :
**15 contrôles de commande**, **26 de lecture progressive** et **19 de choix des
documents** par navigateur, plus la recette de traduction ordinaire. Le contrôle
concurrent vérifie qu’une reprise attend la suppression puis reçoit Introuvable,
sans recréer le travail. Les métadonnées d’une publication jamais écrite sont
également retirées avec le brouillon ; la provenance d’un fichier publié demeure.

Suite locale : **863 tests en 174,262 s**, **16 ignorés** pour lecteur optionnel
absent et contrôles Windows. Le nouveau contrôle de concurrence est exécuté
ensuite dans l’ensemble ciblé de **17 tests de traduction**, réussi. La correction
des cartes Windows 0.28.1 est fusionnée dans le candidat sans perdre son numéro
fonctionnel 0.29.0. Les contrôles d’intégration et la CI finale restent suivis.
Le PC de Marc n’a subi ni mise à jour ni suppression par l’agent.

Le groupe de lecture local est aussi retiré après fermeture du lecteur lors de
la suppression : la fermeture ne recrée plus le repère juste effacé. La recette
de commande vérifie ce point, soit **16 contrôles par navigateur**. Les autres
recettes et les données déjà partagées restent conservées.

## Validation de livraison

Les **huit jobs CI** du code `0dcd36f2005795f28927e4395dd3986173724cc4`
réussissent : [exécution 43882806582](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43882806582).
La matrice complète inclut les commandes, la lecture progressive, les originaux
illustrés et la navigation. Windows, les index et le routage sont également
vérifiés. La branche inclut le correctif de cartes Windows 0.28.1.
Une exécution précédente (`d38d1ac`) avait échoué dans la suite navigateur ; son
extrait `--log-failed` n’est pas disponible ici. Le résultat vert revendiqué est
celui du dernier code exécuté, sans conclure à une cause non observée de cet échec.

Le [prompt de refonte des conversations](../decisions/prompt-refonte-conversations.md)
est prêt ; la direction à trois zones est validée, les détails dossiers/profondeur
et raccourcis restent à préciser avec Louis. Le menu des modèles à télécharger
est conservé dans ce cadrage comme lot séparé, sans téléchargement effectué.
Aucune mise à jour du PC de Marc ni suppression de ses travaux n’a été lancée.
