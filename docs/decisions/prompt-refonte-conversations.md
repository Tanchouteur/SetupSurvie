# Mission pour la refonte des conversations

**Prompt de préparation — 16 novembre 2026.** Direction validée par Louis, détails
à préciser avant le développement global. Ce prompt ne donne pas une validation
humaine du moteur ni des contenus et ne lance aucun déploiement client.

## Objectif

Refaire l’usage de l’assistant pour une personne non informaticienne, avec une
organisation familière : conversations à gauche, discussion centrale de largeur
confortable, documents à droite. Sur téléphone : Conversations, Discussion,
Documents, une seule zone à la fois. Lire d’abord la [base validée](conversations-trois-zones.md).

Avant de coder la refonte globale, présenter à Louis les choix restant ouverts :
fonctionnement des dossiers, emplacement/profondeur de réponse et parcours des
quatre raccourcis. Une proposition concrète et courte suffit ; ne pas lancer
une longue liste de questions ni inventer un accord sur ces points.

## Contexte de travail

Lire AGENTS.md, docs/README.md, choix-actuels.md et les guides de conversation,
documents/traduction, synthèse et profils. Vérifier l’état Git, synchroniser avec
`git pull --ff-only`, puis créer un worktree isolé sous tasks et une branche
`codex/`. Ne pas travailler dans le dossier d’un autre agent ni forcer l’historique.
Prendre la version réellement intégrée de main : la lecture progressive 0.28.0,
la correction cartes 0.28.1 et les commandes de traduction 0.29.0 doivent être
conservées lorsqu’elles sont présentes. Une branche d’intégration en cours ne
constitue pas une livraison : examiner l’état réel avant de choisir la base.

## Parcours attendu

- À gauche : Nouvelle discussion, recherche des conversations, dossiers personnels
  créables/renommables, récents, menu renommer/déplacer/supprimer. Le classement
  est facultatif et la barre repliable.
- Au centre : lecture à largeur limitée, saisie accessible, invitation simple et
  raccourcis Poser une question / Traduire un document / Faire une synthèse /
  Comprendre ou apprendre. L’écriture directe reste possible. Les trois modes
  rapide/moyenne/approfondie restent distincts du type de tâche.
- À droite : volet repliable avec documents choisis, sources réellement consultées,
  originaux et suivi des travaux. Ne pas transformer la sélection en preuve de
  lecture. Garder les références ouvrables dans les réponses.
- Sur téléphone : même logique et données, boutons explicites, une zone à la fois,
  sans débordement ou saisie masquée par le clavier.

## Fonctions et données à conserver

Comptes/profils sans mot de passe, conversations, dossiers déjà existants,
associations multiples, favoris, références, brouillons, recherche documentaire,
choix du mode, dictée, illustrations originales, traductions et synthèses longues.
Pause/reprise/arrêt/suppression d’un travail doivent conserver leur périmètre et
leurs protections. Un arrêt ne reprend pas au rechargement. La suppression d’un
travail de traduction garde l’original et ses versions déjà publiées, comme
l’annonce la confirmation. Ne pas retirer cette information.

Préserver retour/avance du navigateur, liens directs, rechargement, position de
lecture et changement de profil. Une consultation ne lance pas de modèle ni de
téléchargement. Les contrôles ne doivent pas disparaître silencieusement sur
mobile. Garder l’accès à Open WebUI et aux documents de secours.

## Contrat technique de l’interface

Le moteur de recherche, les outils IA, le contrôleur machine, Compose et les
cartes ne font pas partie de cette refonte. Ne pas les modifier pour faire passer
un test de disposition. Lire les états/routes existants avant d’ajouter une API.
Les dossiers du portail ne sont pas implicitement les dossiers Open WebUI :
leurs historiques restent distincts ; concevoir explicitement les données
manquantes et leur migration compatible si nécessaire.

Déplacer les blocs existants plutôt que cloner leurs IDs ou gestionnaires.
Le lecteur de traduction peut déplacer `translation-parts`, les actions et leur
navigation dans `translation-reading-content`, puis les remet à leur place.
Conserver un seul jeu de contrôles, la lecture pendant la préparation, la position
par profil/traduction, les comparaisons ouvertes et la sélection de texte.
Le routeur gère les dialogues dans l’historique : ne pas doubler ses écritures.
Les publications restent indépendantes des conversations privées supprimées.

`portal/index.html` et `portal/interface/index.html` sont générés : modifier
`scripts/build_portal.py` et les sources, puis régénérer. Incrémenter la
version du logiciel logiquement, maintenir API/release/README et les clés de
cache des fichiers modifiés. Ne pas modifier les versions tierces épinglées
pour une refonte d’interface.

## Validation et livraison

Tester les fonctions concernées sur fixtures minuscules, puis la suite requise
et les recettes navigateur Chromium/WebKit. Couvrir mobile 320/390 px et bureau,
clavier, focus, Retour/Avancer, rechargement, profils et travaux en cours. Garder
les assertions du moteur ; adapter uniquement les chemins de navigation rendus
obsolètes. Ne pas filtrer les erreurs JavaScript pour obtenir un résultat vert.
L’émulation WebKit ne vaut pas validation d’un iPhone physique.

Documenter décisions retenues/écartées, comportement courant, captures et limites
dans les guides de référence, pas seulement le bilan. Vérifier liens, secrets et
paquet. Committer/pousser, obtenir les vérifications requises, puis intégrer main
sans force en conservant les autres livraisons. Ne pas mettre à jour le PC de
Marc ni interrompre ses services pour la recette de développement.

Le catalogue de téléchargement de modèles demandé par Louis est un **lot séparé** :
stock disque, modèle chargé et modes conseillés restent distincts. Ne pas mêler
ses téléchargements ou ses règles au réaménagement des conversations.
