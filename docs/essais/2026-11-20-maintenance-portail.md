# Mises à jour et copies suivies dans le portail — 0.68.0

**Bilan daté — 20 novembre 2026, runner CPU de développement et CI GitHub.**
Référence actuelle : [guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#depuis-le-portail-et-suivi-sur-laccueil--0680).

## Réalisé et vérifié

- Tests unitaires de la page temporaire : routes, refus des API, attente puis
  libération des ports, ressources gardées en mémoire après renommage de
  l’application, HTTPS avec un certificat au format de Caddy, page désactivable.
- Ordre des services : la page s’ouvre après l’arrêt des conteneurs et se ferme
  avant `compose up`, y compris lors d’un retour arrière.
- Vérification de `main` avec un vrai dépôt Git local : version et changements
  lus sans modifier le clone, échec hors ligne sans perte de la dernière version
  connue, dépôt inattendu refusé, lancement refusé pendant un transfert ou une
  mise à jour non récupérée, lanceur arrêté avant son premier rapport.
- Routes du pilote réservées au profil Famille ; pause préalable de la file.
- Liste des étapes identique entre Python et le lanceur PowerShell (test).
- Chromium sur écran de bureau (1440 × 950) et mobile (390 × 844), contrôleur
  simulé : survol avec date de vérification, actualisation, confirmation,
  lancement, bandeau, mode maintenance avec retour à l’accueil, perte de
  connexion, résultat, retour à la page précédente, suivi périmé sans blocage,
  page autonome rechargée.

## Non réalisé

- Aucune mise à jour réelle sous Windows : écriture du suivi par le lanceur
  PowerShell (contrôlée seulement par la CI Windows si elle l’exerce), lancement
  sans fenêtre depuis le contrôleur, libération des ports par Docker Desktop.
- Aucun essai sur iPhone réel ni en HTTPS chez Marc.
- Aucune copie complète réelle avec la page de suivi.
