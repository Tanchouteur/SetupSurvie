# Cartes riches, accueil utile et transitions — 0.76.0

**Bilan daté — 21 novembre 2026, runner CPU (Chromium distant, données fictives,
sans Kiwix réel).** Demande de Louis du même jour. Référence : [guide de design](../architecture/guide-design.md#cartes-accueil-et-transitions--0760).

## Niveau de version

Passage de 0.75.0 à **0.76.0** (`y`) : nouvelles fonctions d’interface
compatibles. Les données et les API sont inchangées, hormis le champ `icon_id`
ajouté à l’inventaire.

## Réalisé

- **Cartes de collections** : vignette (illustration Kiwix via `icon_id`, sinon
  pictogramme), liseré par type, description sur trois lignes, relief au
  survol, collection non prête grisée. [Capture](captures/portail-0760/cartes-collections.png)
- **Accueil** : huit tuiles **Trouver par besoin**, qui lancent une recherche, et
  ligne **Sur cet appareil** (contenus prêts, état de l’assistant).
  [Ordinateur](captures/portail-0760/accueil-par-besoin.png) ·
  [Téléphone](captures/portail-0760/telephone-accueil.png)
- **Transitions** : glissement directionnel des blocs au changement d’écran ou
  d’onglet (240 ms, en cascade), fondu seul pour les blocs à éléments fixes,
  apparition en cascade des cartes et des tuiles. `#main` coupe le débordement
  horizontal pendant l’animation.

## Vérifications

- Tests unitaires : `python -m unittest discover -s tests` réussi (1 251 tests, 39 ignorés).
- Recettes navigateur Chromium distant : suite complète. Les 5 recettes qui
  échouent déjà sur la référence sont inchangées. Les recettes de réglages, de
  finition, d’animation, de filtre et de catalogue ont été rejouées après la
  correction du débordement.

## Limites

- L’adresse d’illustration Kiwix n’a pas été vérifiée contre un vrai
  `kiwix-serve` dans le runner. Si elle échoue, l’image est retirée et le
  pictogramme reste affiché.
- Firefox, WebKit et Windows sont confirmés par la CI GitHub. Aucun essai sur
  téléphone réel.
