# Prompt pour l’agent de refonte des paramètres

**Consigne de chantier demandée par Louis — 14 novembre 2026.** La refonte est
conservée comme consigne historique ; la [référence 0.12.0](../utilisation/parametres-et-appareil.md) décrit maintenant l’interface implémentée, et le [bilan](../essais/2026-11-14-parametres-ux.md) ses validations.
Louis autorise sa préparation en parallèle du moteur de recherche. Les cartes
0.11.0 sont intégrées à main ; la correction recherche 0.11.1 s’intègre avant
le chantier UX. Les travaux de recherche se poursuivent séparément de celui-ci.

## Texte à transmettre

Tu interviens sur SetupSurvie pour réorganiser les paramètres et la partie
« Mon appareil ». L’interface actuelle disperse beaucoup de commandes et mélange
usage courant, préparations et diagnostics. Rends-la compréhensible pour une
personne non informaticienne, confortable sans dézoomer, en conservant toutes les
fonctions et la charte visuelle actuelle.

Lis les AGENTS.md applicables, README.md, docs/README.md, les choix actuels et les
guides concernés avant de modifier le produit. Fais l’inventaire des commandes
existantes et de leur destination future ; ne supprime pas une fonction pour
simplifier l’écran. Les cartes 0.11.0 sont déjà intégrées : conserve leurs
corrections. Un autre agent travaille sur l’indexation et la recherche.

### Organisation et confort

- Regroupe les réglages par tâche : profils/connexion, bibliothèque/préparations,
  assistant, puis entretien/diagnostics. Ajuste cette proposition à l’inventaire.
  Les options techniques avancées se dévoilent au besoin ; les actions courantes
  et l’état des opérations doivent rester faciles à trouver.
- Utilise des libellés français simples, des descriptions courtes et une recherche
  visuelle claire des commandes. Évite les grands écrans de boutons sans ordre,
  les doublons et les termes internes inutiles.
- Conserve retour/avance navigateur, liens directs existants, rechargement et
  mémorisation des rubriques, filtres et brouillons par profil. Préserve les IDs
  et branchements des contrôles, ou adapte et teste leurs dépendances DOM ensemble.
  Ne duplique ni les ID ni les gestionnaires lors des changements de rubrique.
- Sur mobile, garde état, suivi et usages principaux confortables. Les opérations
  complexes peuvent rester sur ordinateur avec une explication claire. Vérifie
  clavier, focus, zoom normal, défilement et absence de débordement.
- Conserve le lien Open WebUI, la page de secours et les profils sans mot de passe.
  Ne réintroduis ni bouton « Faire un retour » ni lien vers l’interface classique.
  L’ancienne interface et les données restent conservées.

### Périmètre et travail parallèle

- Utilise un worktree séparé et une branche `codex/parametres-ux`. Commence par
  `git status` et la synchronisation prévue dans les consignes. Préserve tous les
  changements existants ; aucun reset, stash automatique, rebase ou push forcé.
- Travaille sur la présentation/navigation des paramètres. Ne modifie pas le
  moteur de recherche, les index, les modèles, la logique des cartes ou les
  téléchargements. Préserve leurs commandes, contrats d’API et états.
- Les fichiers de recherche `pilot/library.py`, `pilot/archive_index.py`,
  `pilot/retrieval.py`, `pilot/engine.py`, `scripts/index_*.py`,
  `scripts/search_index_*.py` et `portal/interface/search-check.js` sont réservés
  à l’autre chantier. Toute dépendance nécessitant une modification doit être
  identifiée et coordonnée, sans élargissement silencieux du périmètre.
- Navigation commune, `pilot/app.py`, version, Compose, générateur du portail et
  index documentaires demandent coordination. Prépare ton travail sur ta branche ;
  les intégrations sur main se font successivement après vérification. La
  recherche réserve 0.11.1 ; une évolution UX peut viser 0.12.0 après elle, en
  vérifiant la version réellement disponible au moment de l’intégration.
- Régénère les HTML via `python3 scripts/build_portal.py`, sans éditer
  directement les fichiers générés. Ne change pas les images tierces ni le schéma
  des données pour une réorganisation d’interface.

### Préservation et validation

Aucune ouverture de rubrique ne doit lancer d’inférence, indexation, traduction
ou téléchargement. Préserve le mode jeu, la pause/reprise explicite et les travaux
en cours. Garde profils, conversations, favoris, réglages, documents, index et
cartes ; aucune migration destructive n’est nécessaire à cette refonte.

Utilise les petits jeux d’essai du dépôt, sans modèle ni corpus lourd dans le
runner. Exécute les tests adaptés, la suite Python dans l’environnement isolé,
`git diff --check`, puis les parcours navigateur Chromium et WebKit : ordinateur,
tablette et téléphone à 320/390 px. Vérifie notamment changement de profil,
historique, rechargement et commandes toujours accessibles. Une émulation WebKit
ne prouve pas un essai sur iPhone physique.

Mets à jour les guides de référence, index, décisions et journal depuis la 0.2.0
avec les choix gardés/écartés et les limites réellement testées. Fournis des
captures avant/après et la correspondance entre anciennes et nouvelles rubriques.
Commite et pousse ta branche avec des messages explicites ; livre version,
commit, tests et limites. Préserve le travail des autres agents et coordonne
l’intégration finale sur main.
