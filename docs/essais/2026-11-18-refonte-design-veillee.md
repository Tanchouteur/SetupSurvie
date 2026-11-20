# Refonte du design « Veillée » — 0.44.0

**Bilan daté du 18 novembre 2026.** Les règles durables sont dans
[composants et présentation](../architecture/composants-interface.md#direction-visuelle--veillée---0440).

## Livré

- Palette, typographie, boutons, champs, cartes et fenêtres communs à tout le portail.
- Accueil « feu de camp », navigation à pastille glissante, onglets à soulignement mobile.
- Accès rapide au clavier ou par la loupe, progression de lecture, barre d’actions
  du lecteur qui reste visible sur PC.
- Cartes, lecteur PDF, page de secours et suivi de copie alignés sur la même identité.

## Vérifié

Essais dans Chromium, avec des données fictives et sans modèle :

- captures relues sur PC et téléphone pour les écrans principaux ;
- absence de débordement et de chevauchement de la navigation de 320 à 1920 px ;
- contrastes des couleurs de texte principales supérieurs ou égaux à 4,5:1 ;
- recette `tests/browser_design_system.js`.

## Non vérifié

Safari sur iPhone réel, Firefox et WebKit pour ce design, Windows chez Marc, une
vraie réponse de modèle dans l’assistant et un fonds documentaire complet. La
compréhension par des utilisateurs non techniques reste à observer.
