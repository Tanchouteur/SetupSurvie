# Audit et fiabilisation de la CI du 20 novembre 2026

**Bilan daté — SetupSurvie 0.68.1, tests sur données synthétiques.** Louis a
demandé de revoir la chaîne de tests et de refondre les parties qui en avaient besoin.

Le dernier run vert de `main` avant l’audit date du 19 novembre à 23 h 03 UTC.
Le 20 novembre, les échecs répétés se concentraient sur le portail en Chromium
et WebKit. Le dernier run étudié de la 0.68.1 échouait sur la position des livres
à 320 px. Des révisions antérieures échouaient sur un champ de recherche masqué.
La [PR 67](https://github.com/Tanchouteur/SetupSurvie/pull/67) a aussi eu un échec
de suivi de sauvegarde sur Windows, après lequel les contrôles Python de son
job avaient été ignorés.

- [Dernier run vert avant l’audit](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44634252275)
- [Run de main examiné](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44723627696)
- [Run de la PR de maintenance examiné](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44721727782)

Le workflow utilisait la découverte Python sous Linux et une longue sélection
manuelle sous Windows, dont une entrée répétée. Le lanceur du portail
enchaînait les scénarios sans annoncer chaque résultat et s’arrêtait au
premier échec. Le filtre navigateur des PR pouvait ignorer un changement au
générateur du portail. Le paquet zip était construit et publié sans relecture
de l’archive produite.

La [chaîne actuelle](../architecture/tests-et-ci.md) simplifie ces points
en gardant les recettes existantes et les contrôles spécialisés. Elle réutilise
le lecteur de mise à jour pour vérifier le contenu du zip. Le contrôle à 320 px
vise l’accès à l’en-tête de la section et vérifie l’ouverture réelle de son
contenu. Les recettes navigateur sur données fictives et la vérification du
paquet sans l’appliquer couvrent les changements de cette livraison.
