# Maquette navigable du portail — 13 novembre 2026

**Bilan daté — version 0.1.31, runner CPU.**
Voir le [guide d’essai](../utilisation/maquette-ux.md) et le
[plan de refonte](../decisions/plan-refonte-ux.md).

## Réalisé

Maquette séparée `/maquette/`, cinq rubriques, pages de collection et exemples de
lecture, favoris fictifs, brouillon, suivis simulés, états dégradés et présentation
mobile. Le portail actuel reste l’entrée principale avec ses fonctionnalités ;
un lien permet d’essayer la maquette. API et version de livraison passent en
0.1.31, sans migration ni changement d’image tierce.

Les deux interfaces ne partagent pas encore leurs données fonctionnelles : la
maquette utilise volontairement des exemples. La conservation du portail actuel
est assurée par son maintien à la racine et la référence Git
`interface-classique-0.1.30`. Ce n’est pas encore la migration complète du lot 1
vers une interface classique autonome sous `/classique/`.

## Vérifications locales

- Playwright MCP, Chromium : 34 contrôles réussis (recette `browser_ux_preview.js`).
- Navigation Précédent/Suivant, recherche restaurée, ouverture directe d’une
  collection, brouillon conservé après navigation/rechargement, changement de
  profil sans mélange des brouillons, volet et sous-rubrique mémorisés.
- Dialogue fermé par Retour, position restaurée par Retour et rechargement,
  distinction transfert/vérification/inconnu, pause fictive et favoris de démo.
- Présentations ordinateur et téléphone, absence de débordement horizontal à
  320, 390, 760, 820 et 1440 pixels ; carte et suivi accessibles sur téléphone,
  commandes complexes retirées. Captures visuelles relues après correction
  de l’espacement des sous-rubriques mobiles.
- Aucun appel `/api/` ni erreur JavaScript pendant cette recette.
- Syntaxe JavaScript et `git diff --check` vérifiés.

La suite Python a été exécutée dans un environnement isolé, avec les dépendances
figées de `tests/requirements.txt` : **308 tests, 6 erreurs, 3 ignorés**. Les six
erreurs ont été reproduites sur le commit de référence `9162728`, avant la maquette :
cinq tests de reprise rencontrent la réserve disque de 15 Go sur le runner
(environ 14 Go libres) et une fixture de kit Windows ne contient pas
`startup-windows.ps1`, désormais attendu par le démarrage automatique.
Ces limites ne sont pas des régressions introduites par la maquette ; la suite
complète n’est néanmoins pas annoncée verte. Les protections de capacité réelles
et le code d’installation n’ont pas été assouplis pour contourner les erreurs.

Le lanceur navigateur local Node n’a pas pu démarrer : exécutables Chromium/WebKit
absents de son cache. La recette a été exécutée par le MCP Chromium disponible ;
le lanceur CI conserve les deux moteurs. Aucun navigateur supplémentaire n’a été
installé dans le runner pour cette livraison.

## Vérifications CI

Sur le [run 43449686090](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43449686090)
du commit fonctionnel `906b3bb`, l’étape `browser_maps_runner.cjs` a réussi :
la recette de la maquette passe donc aussi sous Chromium et WebKit dans la CI.
Le scénario de routage hors ligne réussit également.

La CI globale reste en échec : fixture `startup-windows.ps1` absente dans le test
de kit Linux, et test Windows `test_second_installation_preserves_first_installation_shortcuts`.
Les mêmes deux échecs sont présents dans le
[run de référence 43446870838](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43446870838)
du commit `9162728`, avant la maquette. Aucun résultat CI global vert n’est revendiqué.

## Restant à valider
- iPhone/Safari réels, clavier et dictée humaine, confort avec Marc et une personne novice.
- Machine Windows réelle, état du transfert existant, mesures matérielles,
  lecture Kiwix réelle depuis la nouvelle interface et fonctionnement hors ligne complet.
- Conservation autonome de la classique et raccordement de toutes les fonctions
  avant de proposer un remplacement de l’interface principale.

Aucune inférence réelle, aucun téléchargement lourd, aucune intervention sur le
PC de Marc ou son transfert en cours n’ont été nécessaires.
