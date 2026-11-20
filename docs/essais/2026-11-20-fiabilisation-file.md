# Actualisation des cartes de la file d’attente

**Bilan du 20 novembre 2026 — SetupSurvie 0.67.2.**

Dans l’historique, l’arrivée d’un nouvel état pouvait enlever le focus du
volet technique en cours de lecture. Le rendu identifiait l’ouverture d’un
volet par la carte entière et restaurait le focus seulement dans **À suivre**.
Cette logique pouvait également confondre deux volets d’une même carte.

L’actualisation restaure l’ouverture et le focus de chaque volet encore
présent. La version corrective 0.67.2 correspond à cette correction
compatible. Voir le [guide de la file](../utilisation/file-attente.md).

La recette navigateur utilise une préparation terminée dans l’historique
et une carte simulée combinant détails techniques et lignes à vérifier.
Elle vérifie l’ouverture, la fermeture et le focus au clavier pendant la
réception d’un nouvel état. Les essais se font sur le runner avec une API de
test, sans IA réelle ni intervention sur les installations familiales.

Les deux scénarios ont chacun échoué avec le script 0.67.1 sous Chromium.
Les 23 tests Python ciblés couvrant la file, la génération du portail et
la cohérence de version ont réussi.
La recette complète de la file a réussi sous Chromium et WebKit avec le
correctif.
