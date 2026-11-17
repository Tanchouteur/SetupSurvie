# Mémoire visible et lecture des traductions

**Bilan de développement — 17 novembre 2026, candidat 0.39.0.** Retours de Louis
sur 0.38.3 : modèle chargé difficile à retrouver, lien mémoire qui laisse les
mesures masquées, lecture trop étroite et progression qui clignote. Il demande
ensuite l’état des ressources dans la navbar PC, la navigation conservée dans
les cartes et la suppression de l’expiration du modèle après inactivité.

## Causes et comportement proposé

Les mesures existaient mais avaient été déplacées dans des détails fermés.
Elles sont maintenant directement visibles en tête de Vue d’ensemble, avec un
accès depuis la navbar et les réglages de l’assistant. RAM, VRAM totale du PC
et allocation par modèle restent distinguées. Une observation de modèles échouée
ne devient pas un inventaire vide confirmé. Les mesures inconnues et périmées
restent signalées. Navigation et affichage ne lancent pas de modèle.

Le lecteur appliquait les styles généraux des fenêtres, dont un maximum de
470 pixels malgré sa propre largeur demandée. Cette limite est corrigée. Le
panneau Bibliothèque masquait ses commandes avant chaque polling : elles restent
en place sur un travail déjà affiché. Passages inchangés, comparaison, sélection
et groupe de lecture sont conservés. L’accès aux derniers passages est volontaire.
Un rendu Markdown local assaini remet les titres/listes/tableaux en forme et
réunit les retours simples de prose. L’original, les chiffres, les formules et
les contrôles ne sont pas réécrits. Ce n’est pas une recomposition du PDF illustré.

Les appels de génération demandaient `keep_alive: 5m`. La politique partagée
et les lanceurs passent à une conservation sans expiration après inactivité.
Arrêt, mode jeu, changement de modèle et déchargements explicites de calibration
restent possibles. Aucune inférence réelle n’est lancée pour ces tests.

Version mineure compatible : évolution visible des parcours et du comportement
de conservation, sans migration des données ni mise à jour des composants tiers.

## Vérifications en cours

Contrôleur : 13 tests en 7,200 s. Sessions de modèle : 15 tests en 2,564 s,
avec charge préparatoire et requête finale sans expiration. Chromium : nouveau
parcours de 27 contrôles ; lecteur existant 16, lecture progressive 26, réglages
182 et confort de discussion 38. Le nouveau parcours de 27 contrôles passe
aussi sur WebKit dans le conteneur Playwright existant, sans téléchargement. Le premier essai sur écran de 844×390 a révélé
que l’indicateur consommait trop de hauteur ; il est désormais réservé aux
fenêtres d’au moins 1001×501. Les mesures détaillées restent accessibles partout.
Les contrôles de contenu sont fictifs ; ils ne certifient pas une traduction réelle.
Suite complète locale : **1 014 tests en 218,272 s, 6 ignorés**, aucun échec.
Après les derniers réglages des lanceurs : 5 tests du laboratoire réussis,
20 tests ciblés des lanceurs/installations réussis en 1,636 s. La CI reste à
terminer avant intégration. La durée d’inactivité réelle sur Windows n’a pas été
rejouée : les essais vérifient les requêtes émises sans expiration. La
[référence Ollama](https://docs.ollama.com/faq#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately)
confirme le rôle de la valeur négative ; les demandes explicites de déchargement
restent distinctes.

## Suite vidéo demandée

Les captures suivantes montrent l’assistant qui répond à une recherche de vidéo
par un article et affirme sans preuve une absence de vidéo. Louis demande une
recherche spécifique visible dans le moteur. Le chemin vidéo existant mélange
ses résultats aux documents ; l’outil IA ne porte pas encore de filtre de type
et réduit les détails de couverture. Ce lot est tracé, pas déclaré corrigé par
la présente livraison : filtre, découverte sans piste et absence/non-indexation
à distinguer, puis test de la demande réelle et de sa relance.


La première CI relève une carte trop petite : la navbar nouvellement ajoutée
s’empilait avec l’ancien en-tête. Ils sont réunis en un seul bandeau, en gardant
les boutons de profil et d’impression. Le seuil de hauteur de carte n’est pas
abaissé pour accepter cette régression.
Louis réserve ensuite toute la recherche vidéo à un autre agent ; aucune
modification de ce moteur vidéo n’est incluse dans ce lot. Le travail préparatoire
API reste isolé, non intégré et non publié, dans son worktree dédié.

Paquet candidat source `b3e84d0b1eefbd15a341bf2d636806556fa7a5c3` : 988 fichiers,
17 334 674 octets décompressés, ZIP 7 750 184 octets, SHA-256
`b26930208868c5a11b5b1570cca3fa5e2e76acbe662a7e85d5fbfc721b4b763b`.
Comparé intégralement à Git et au manifeste ; ce premier paquet précède
l’ajustement de la hauteur de carte et n’est pas le paquet final de livraison.
