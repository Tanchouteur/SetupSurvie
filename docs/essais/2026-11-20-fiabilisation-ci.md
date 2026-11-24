# Audit et fiabilisation de la CI du 20 novembre 2026

**Bilan daté — audit de la 0.68.1 puis intégration sur la 0.69.0.** Louis a
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

La première validation GitHub Actions de la branche a exécuté 1 194 tests
Python sous Linux, dont 7 ignorés. Le paquet téléchargé contenait 1 091
fichiers vérifiés et son empreinte concordait. Les 51 recettes du portail
ont réussi sur Chromium et WebKit. Une capture de Firefox a isolé un
échec dans la recette de traduction du lecteur. La recette utilise
désormais la préférence de mouvement réduit, tandis que les recettes
d’animation conservent leurs réglages. L’essai WebKit de navigation
attend la réponse initiale de la file d’attente avant de quitter les cartes.

La découverte Windows a révélé quatre scénarios système propres à Linux
et un test du kit dont l’injection d’erreur dépendait du chemin temporaire
Windows. Les premiers restent exécutés sur Linux. Le test du kit compare
désormais le chemin résolu, comme le code de publication. La recette
d’installation des cartes simule la préparation YouTube, dont les
binaires sont déjà exercés séparément.

[Premier run de la branche](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44729474592).


Sur la 0.69.0, la suite Windows a aussi montré que les fixtures Git de
maintenance devaient simuler un dépôt absent en le renommant. La recette de
recherche vidéo contrôle désormais l’instant où l’inventaire peut finir. Elle
vérifie ainsi les résultats avant et après publication.

[Run de la 0.69.0 avant ces corrections](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44731300431).
