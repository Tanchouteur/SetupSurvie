# Refonte des conversations : trois zones

**Base de conception — direction validée par Louis le 16 novembre 2026.**
Ce document trace sa demande ; la refonte générale n’est pas implémentée ici.
Le suivi/lecteur de traduction 0.28.0 est un chantier distinct et conservable.

## Direction retenue

Sur ordinateur, une interface familière inspirée des assistants tels que ChatGPT :

- **À gauche, retrouver et ranger** : bouton Nouvelle discussion, recherche dans
  les conversations, dossiers personnels créables et renommables, conversations
  récentes avec titres lisibles, menu renommer/déplacer/supprimer. Le classement
  est facultatif ; on peut discuter immédiatement puis ranger. Barre repliable.
- **Au centre, discuter** : colonne de lecture confortable à largeur limitée,
  saisie accessible en bas. Au départ : **Poser une question**, **Traduire un
  document**, **Faire une synthèse**, **Comprendre ou apprendre**. Ces raccourcis
  guident le choix des documents/langues/besoins ; écrire directement reste
  possible. Rapide/moyenne/approfondie reste un choix distinct de la tâche.
- **À droite, travailler avec les documents** : volet repliable distinguant
  documents choisis et sources réellement consultées, originaux ouvrables et
  suivi des traductions/synthèses. Les références restent aussi dans les réponses.
  Le volet s’ouvre lorsqu’il est utile et laisse ensuite la place à la lecture.

Sur téléphone, une seule zone à la fois, avec les boutons explicites
**Conversations**, **Discussion**, **Documents**. Même organisation et mêmes dossiers.

## Traduction dans le fil — décision du 19 novembre 2026

Louis demande de lire la traduction au fur et à mesure dans la discussion
et propose de regrouper les boutons en haut. SetupSurvie 0.58.0 retient un
bandeau repliable pour les commandes et la progression. Les passages traduits
et les blocages se lisent dans le fil. Cette disposition remplace le suivi
des traductions dans le volet droit décrit ci-dessus. La [lecture plein
écran](../utilisation/documents-et-traduction.md#lire-pendant-que-le-document-se-traduit--0280)
reste accessible depuis le bandeau. Les synthèses gardent leurs commandes
dans **Documents**.

## À préciser avec Louis avant le développement global

Comportement détaillé des dossiers, présentation de la profondeur de réponse,
parcours de chaque raccourci et contenu exact du volet documentaire. Préciser
également l’articulation avec la navigation générale du site, sans multiplier
les barres latérales ou les commandes autour de la saisie.

Préserver conversations, dossiers, choix documentaires et travaux existants.
Conserver historique navigateur, rechargement, brouillons et profils ; les
sources choisies ne deviennent jamais des sources prétendument lues. Les tâches
continuent côté serveur et une reprise d’inférence reste explicite après pause.
Ne pas modifier les moteurs pour satisfaire une simple disposition visuelle.

## Modèles à stocker hors ligne : demande complémentaire

Louis souhaite un **menu pour choisir les modèles à télécharger**, afin de
préparer davantage de possibilités que les trois modes de réponse conseillés.
Statut : **à concevoir/implémenter après le chantier en cours** ; ne pas présenter
le stock de modèles supplémentaire comme déjà acquis.

Le catalogue doit distinguer modèle disponible à télécharger, présent sur disque,
chargé en mémoire et choisi pour un mode. Télécharger plusieurs modèles ne doit
ni les charger ensemble, ni changer automatiquement les modes conseillés. Prévoir
volume à télécharger/espace libre, état et reprise, conservation/transfert hors
ligne, références/version des modèles et indication de compatibilité observée.
Ne pas imposer un petit plafond documentaire au PC de Marc. Les choix exacts du
catalogue restent à vérifier ; aucune liste de modèles ni téléchargement lourd
n’est décidée dans ce document.

## Contrat à préserver pour le chantier d’interface

Les contrôles existants gardent leurs IDs et leurs gestionnaires. Déplacer les
blocs plutôt que les cloner. En particulier, la 0.28.0 peut déplacer les passages
`translation-parts` vers son lecteur dédié pendant sa lecture. Depuis 0.58.0, ils reviennent dans le fil à la fermeture. Conserver ce confort ou le remplacer par un
parcours offrant les mêmes capacités, sans reprendre l’inférence au rechargement.
Voir la [référence d’architecture](../architecture/README.md#lecture-pendant-une-traduction--0280).

État du code observé le 16 novembre : `deploy/model-profiles.json` contient dix
profils pour sept références de modèles ; ce catalogue n’est pas une preuve de
leur présence sur un PC. Le lanceur a déjà `scripts/setup.py pull-model --model`,
qui appelle le moteur local et refuse les références cloud. Le contrôleur du site
ne propose pas encore une file dédiée de téléchargement de modèles. Le futur
menu doit donc réutiliser ces distinctions, ajouter suivi/reprise et vérification
de présence, sans confondre changement de mode et acquisition d’un modèle.

Mission préparée : [prompt de refonte](prompt-refonte-conversations.md). Les choix
de dossiers, profondeur et parcours restent à préciser avant le développement.
