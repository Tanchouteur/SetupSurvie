# Recherche documentaire et confort des conversations

**Bilan daté du 14 novembre 2026 — pilote 0.1.35.** Développement dans le runner
Linux CPU, données minuscules et réponses simulées. Aucun modèle, archive ou
fond cartographique téléchargé, aucune inférence ni intervention sur le PC de Marc.

## Problème observé

Louis signale une réponse peu étayée à « comment faire un feu » malgré environ
755 Go de contenus, ainsi qu’une conversation trop encombrée nécessitant de
réduire le zoom. Il demande aussi de retirer les boutons de retour classique et
« Faire un retour », puis de corriger la phrase d’accueil.

L’[audit réel du 13 novembre](2026-11-13-audit-fonds-marc.md) avait identifié des
requêtes Kiwix refusées avec HTTP 400 lors du mélange de langues. L’ancien code
absorbait ces erreurs et ne montrait que les résultats des guides. Le volume reçu
ne prouve donc pas que le moteur avait effectivement interrogé ces archives.
Cela n’établit pas non plus qu’une procédure adaptée sur le feu existe dans ce fonds.

Le [contrat officiel de Kiwix](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html#search)
demande une même langue pour les recherches multi-archives et permet les sélections
répétées par `books.id` ou `books.name`. Le correctif utilise ces sélections explicites,
isole les archives multilingues, retente les lots refusés individuellement et
conserve les réponses réussies. Les collections sans index, les échecs et les
limites de temps/appels sont signalés au lecteur et à l’assistant via `coverage`.
Les termes feu/feux et leurs équivalents anglais sont ajoutés au vocabulaire.

Une source trouvée reste distincte d’une source lue. Les consignes renforcent
la nécessité d’une référence directement pertinente pour une procédure pratique ;
un texte de prévention ne suffit pas à valider une méthode de réalisation.

## Interface livrée

La conversation conserve les fonctions existantes dans une colonne lisible,
avec un texte de 16 pixels et une saisie compacte. **Conversations** ouvre les
historiques et dossiers dans une fenêtre dédiée. Les menus empilés au-dessus de
la réponse disparaissent. Les liens Open WebUI et secours restent accessibles,
y compris depuis cette fenêtre sur téléphone. Les boutons demandés sont retirés
des menus ; `/classique/` conserve ses fichiers et accès direct. L’accueil demande
**Qu’avez-vous envie d’apprendre ?**.

Le [guide actuel](../utilisation/nouvelle-interface.md) décrit la navigation et
la mise à jour habituelle Windows/Linux ; la livraison ne remplace pas une
installation active par un simple pull.

## Vérifications dans le runner

- Tests unitaires Python complets : 341 tests, trois ignorés selon les prérequis.
- Cas Kiwix simulés : sélection explicite, UUID/noms, langues, repli après HTTP 400,
  catalogue indisponible, collection sans index, limite de requêtes et rejet d’un
  résultat provenant d’une archive hors sélection.
- API et orchestration simulées : transmission de l’état incomplet même sans résultat,
  conservation des résultats des guides et distinction trouvé/lu.
- Chromium via Playwright MCP : 37 contrôles de confort avec réponse longue synthétique,
  sept dimensions de 320 × 568 à 1440 × 900, dont paysage 844 × 390. Pas de
  débordement horizontal, bouton Envoyer visible et réellement accessible au clic.
- Même navigateur : 29 contrôles de navigation, mémoire, rechargement, lecture,
  profils, accès classique direct, carte et suivi ; traduction associée, pause,
  reprise, rechargement et export vérifiés sur l’API simulée.

La recette de confort rejoint la CI Chromium/WebKit ; le test Kiwix rejoint la
suite Windows. Les résultats de CI sont à lire sur le commit livré.

## Limites et recette sur la machine cible

Les fixtures ne prouvent ni la pertinence des résultats du fonds complet ni la
fidélité d’une réponse du modèle. Après mise à jour chez Marc, rechercher « feu »,
« allumer un feu » et « fire », comparer avec les lecteurs Kiwix, puis ouvrir les
sources proposées avant d’évaluer une nouvelle réponse de l’assistant. Un message
partiel doit rester explicite ; une archive sans index demeure consultable dans
Collections. Ne pas réutiliser l’ancienne réponse comme preuve du correctif.

Aucune installation physique Windows/Linux ni utilisation sur iPhone réel n’est
validée par cette campagne. Les comptes, conversations et contenus ne sont pas
migrés ; les images tierces restent épinglées à leurs références existantes.
