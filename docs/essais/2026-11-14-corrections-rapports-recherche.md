# Corrections après les rapports réels 0.8.0

**Bilan en cours — 0.9.1, 14 novembre 2026.** Suite prioritaire L2/L8 aux
[rapports transmis par Louis](2026-11-14-rapports-recherche-080.md). Le problème
d’indexation réel reste à diagnostiquer avec son export ; sa cause n’est pas
déduite de la seule capture « 135 / 135 examinées, 0 article indexé ».

## Ce qui a été reproduit et corrigé

- Le comparatif utilisait les 15 secondes comme critère final, mais autorisait
  30 secondes par appel IA. Le budget est désormais une échéance commune à la
  demande : moteur initial, reformulations, recherches supplémentaires et
  reclassement. Les étapes déjà terminées sont conservées. Deux demandes
  successives en erreur arrêtent la série, sans lancer les 32 échecs possibles.
- Les appels gardent des compteurs de trames, caractères de réflexion et de
  sortie et premiers délais, sans texte privé. L’indisponibilité du contrôleur
  garde une cause limitée — délai, HTTP, connexion ou format — distincte d’une
  pression RAM/vidéo effectivement mesurée.
- Le moteur envoyait jusqu’à 12 recherches simultanées **par demande** et un lot
  en échec pouvait provoquer des sous-requêtes supplémentaires. Deux voies de
  recherche de texte et deux voies de titres sont maintenant communes aux
  demandes concurrentes. Seul un rejet de sélection 400/404/413 autorise l’essai
  individuel d’un lot ; délai, connexion et surcharge ne multiplient pas les appels.
- Les réponses réussies et valides sont regroupées si identiques et gardées
  quinze secondes, avec limites en nombre et taille. Les erreurs et formats
  invalides ne sont pas mis en cache. Le rapport indique les réutilisations,
  limites et causes, sans réponse brute du serveur ni données d’authentification.
- Un repli local `OR` peut trouver un manuel ne contenant qu’un mot de la demande.
  Les candidats élargis doivent désormais couvrir au moins deux tiers des concepts,
  arrondis au supérieur. Les correspondances de texte intégral à la requête complète
  restent recevables, même sans extrait fourni par Kiwix. Un quiz est écarté d’une
  demande pratique lorsqu’il n’est pas explicitement demandé.
- Les concepts crevaison/poncture, fuite/leak et filtration sont bilingues ;
  « how to start a fire » ne conserve plus `start` comme un sujet indépendant.
  Les expressions anglaises sont aussi converties pour les archives françaises.

## Choix et limites

La borne de concurrence protège le serveur documentaire et réserve un accès aux
titres. Elle ne prétend pas que quatre appels sont optimaux sur tous les PC et ne
réduit pas le nombre de processus d’indexation configurable. Un échec des archives
reste signalé ; aucune panne n’est présentée comme une absence de document.
Une source trouvée n’est toujours ni lue ni qualifiée par le seul résultat de recherche.

L’indexation complémentaire reste indépendante des index natifs. Le suivi distingue
désormais index natifs réutilisés, index locaux prêts et archives en erreur. Ce
changement explique les compteurs ; il ne répare pas à lui seul l’échec réel de Marc.

La référence technique du protocole est l’[API officielle Kiwix](https://raw.githubusercontent.com/kiwix/kiwix-tools/main/docs/kiwix-serve.rst),
avec sélections répétées par nom/UUID et contraintes de langue. Le
[gabarit XML officiel](https://raw.githubusercontent.com/kiwix/libkiwix/main/static/templates/search_result.xml)
rend l’extrait conditionnel : la nouvelle sélection ne doit pas exiger un extrait
pour une correspondance native complète. Les durées et flux IA suivent l’[API Ollama](https://docs.ollama.com/api/chat).

## Vérifications

Tests simulés : concurrence commune, accès aux titres, cache borné/expiré,
échec non mémorisé, réponse invalide, arrêt des requêtes, faux positifs de repli,
recherche bilingue, délai réel d’une seconde et arrêt après deux erreurs,
progression numérique du flux et diagnostic matériel sans contenu privé.

Le vrai Kiwix épinglé passe 29 vérifications sur cinq ZIM générés de 282 587 octets.
Ce contrôle a aussi révélé un résultat natif légitime sans extrait ; il est conservé
avec sa limite visible. La fixture de classement a été corrigée pour contenir
effectivement les deux sujets de sa demande, et le contrôle pédagogique ne suppose
plus que le premier appel réseau est une recherche plutôt qu’un titre.

Chromium MCP : recherche principale (45 contrôles), outils (14), comparatif (16).
La suite finale Linux/Windows/WebKit et le nombre de tests restent à consigner.
Aucun modèle ni corpus de Marc n’a été chargé. Les délais, gains et stabilité réels
après correction restent à vérifier chez Marc, d’abord avec R1 puis R2 court.

**Version corrective 0.9.1** : corrections compatibles de recherche, délais et
diagnostics ; schéma de données, références et images tierces conservés.
