# Contrôle d’usage hors ligne depuis le portail

**Bilan en cours — 0.10.0, 14 novembre 2026.** Suite de L9 et du rapport R7 du
[plan de fiabilisation](../decisions/plan-ameliorations-marc.md), distincte des
corrections de classement et d’ordonnancement de la 0.9.4. Le
[guide actuel](../utilisation/verifier-usage-hors-ligne.md) décrit l’usage.

## Résultat et organisation

Un bouton rejoint le panneau existant Vérifier la recherche. Le dialogue réunit
conditions d’essai, contrôles automatiques, observations courantes et opérations
de maintenance dans des volets distincts. Il n’ajoute pas un onglet à la navigation
principale ni une nouvelle commande de préparation.

Dix mesures au maximum : versions avant/après, contrôleur IA avant/après,
diagnostic documentaire, deux recherches avec périmètres différents, deux aperçus
distincts et réponse de la page de secours. Le total est borné à 90 secondes,
chaque lecture à quinze secondes ; l’arrêt conserve le reçu partiel. Ce ne sont
ni une nouvelle mesure du classement réel ni une preuve de coupure réseau.

Quatorze étapes humaines restent initialement non effectuées : lecture originale
et PDF, navigation, rechargement, deux onglets, profils/données, brouillon, confort,
secours, puis cinq étapes après maintenance prévue ou sur copie jetable. Une
étape non applicable n’est pas comptée comme un essai effectué. Aucune décision
de validation complète n’est produite automatiquement.

## Reprise, isolation et limites

Le brouillon local conserve seulement les étapes, leurs conditions et l’observation,
par profil/version. Fermer le dialogue préserve les mesures en mémoire ; recharger
les abandonne et réclame une nouvelle mesure. Changer de profil annule l’ancien
contrôle ; une génération et un contrôleur propres à chaque exécution empêchent
une réponse ou une échéance ancienne d’interrompre l’essai suivant. Le dialogue
ignore son ancien événement de fermeture s’il vient déjà d’être rouvert.

Une version serveur modifiée interrompt le contrôle, au lieu de réattribuer les
observations à la nouvelle version. Un contrôleur absent reste non vérifié.
L’export garde les titres/identifiants et compteurs sans textes documentaires,
manifeste détaillé ni identité de profil ; l’observation libre reste incluse.
Une mémoire navigateur indisponible préserve l’export et affiche la limite.

## Vérifications

La recette navigateur couvre 32 assertions : lectures locales seulement,
absence de commandes de préparation/inférence, source indisponible, recherche
partielle, contrôleur absent, arrêt et reçu incomplet, nouvel essai, brouillons,
changement de profil pendant une demande bloquée, mémoire indisponible, changement
de version au début/à la fin et limites de quinze/quatre-vingt-dix secondes.
Les horloges de ces deux derniers essais sont simulées ; les requêtes retardées
appartiennent à la fixture et ne bloquent aucun service réel.

Chromium via le MCP Playwright réussit ces 32 assertions, avec largeurs 1366,
390 et 320 pixels, puis inspection de la capture mobile. La suite locale termine
495 tests, dont trois ignorés sous Linux, sans échec. Le lancement du runner
navigateur complet local ne trouve pas son Chromium ; le WebKit local manque
de bibliothèques système. Ces essais ne sont pas comptés comme exécutés : la CI
Ubuntu prévue avec les dépendances navigateur doit les prendre en charge.
Résultat de CI à consigner avant publication sur main.

Le premier passage CI réussit sept tâches sur huit, mais interrompt la recette
navigateur au rechargement après un changement de profil. Le test cumulait une
sélection par API et un rechargement forcé alors que le portail peut déjà
recharger un onglet périmé. La recette utilise maintenant le choix de profil de
l’interface pour les essais d’isolation. Une perte de profil simulée pendant un
appel bloqué garde un contrôle séparé de l’annulation et de la réponse tardive.
Ces 32 assertions repassent ensuite dans Chromium via le MCP ; la nouvelle CI
reste à consigner.
Aucun modèle, gros corpus, panne provoquée sur installation réelle ou coupure
physique d’Internet n’est utilisé. WebKit ne vaut pas Safari sur iPhone physique.

**Version retenue : 0.10.0**, nouvelle fonction compatible de recette exportable,
sans modification d’image tierce ni migration de données. Le rapport réel R7
reste attendu chez Marc, ainsi que R2 après les corrections 0.9.4. Le
[journal depuis 0.2.0](journal-recherche-depuis-020.md) conserve ces distinctions.
