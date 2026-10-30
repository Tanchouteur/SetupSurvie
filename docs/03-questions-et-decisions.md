# Questions et décisions

Mis à jour le 30 octobre 2026. Les réponses seront intégrées progressivement aux autres documents.

## Première série : finalité et prototype

| Question | Réponse |
| --- | --- |
| Le premier objectif est-il un prototype pour Louis et Marc, un produit destiné à la vente, ou d’abord une bibliothèque sans IA ? | Prototype complet pour Louis et Marc, puis envisager la vente. |
| Quel PC sera utilisé, avec quel OS, processeur et stockage disponible ? | Probablement Ryzen 5, RTX 5060 Ti, 32 Go de RAM, environ 4 To. PC de Marc sous Windows 11 à conserver ; références et espace libre à confirmer. |
| Quels sont les trois usages prioritaires, avec des exemples concrets de recherches ou questions ? | Médecine, réflexion en ingénierie, recettes et différenciation de champignons. Louis s’interroge sur les limites des modèles locaux ; pas de classement arrêté. |

## Deuxième série : fonctions et conditions d’utilisation

| Question | Réponse |
| --- | --- |
| Analyse de photos dès le prototype, ou texte et guides illustrés pour commencer ? | Louis délègue l’arbitrage selon la complexité. Proposition : essai facultatif au prototype ; reporter si matériel, qualité ou installation bloquent. |
| Nombre d’utilisateurs simultanés et attente acceptable pour une réponse IA ? | Plusieurs personnes ; attente d’une à deux minutes acceptable. Nombre précis et délai sous charge à définir. |
| PC dédié sous Linux, ou système et usages actuels à conserver ? | Windows 11 à conserver avec les usages actuels du PC principal. |
| Comptes individuels ou espace commun ? | Un espace commun suffit pour commencer. |
| Autre machine disponible ? | PC Linux avec RTX 2060 et Ryzen 9 dans la chambre de Louis, pour la période de développement ; caractéristiques exactes à confirmer. |

## Troisième série : cible familiale et bibliothèque

| Question | Réponse |
| --- | --- |
| Le PC Linux servira-t-il durablement aux familles ? | Il sert pendant le développement. À terme chaque famille aura son appareil. |
| Quel objectif pour le matériel final ? | Minimiser le coût tout en conservant une machine assez capable pour des modèles suffisants ; configuration à déterminer par les essais. |
| Quelle ampleur pour la bibliothèque ? | Le maximum de contenu ; aucune limite chiffrée fixée. |
| Quel rôle de l’IA ? | Combiner ses connaissances apprises et les documents locaux. |
| Quel budget matériel par appareil familial ? | Environ 1 000 €, indicatif et à ajuster selon les performances ; pas un prix de vente. |
| Un appareil familial dédié sous Linux est-il acceptable ? | Chez Marc, le PC doit d’abord faire serveur et PC habituel sous Windows 11. Achat ultérieur d’une machine dédiée éventuellement allumée en crise envisagé ; OS final non choisi. |
| Quelle place pour les sources françaises et anglaises ? | Le maximum dans les deux langues ; lire les sources anglaises et répondre en français est souhaité. Fonctionnement multilingue à tester. |

## Quatrième série : réseau, énergie et gestion des contenus

| Question | Réponse |
| --- | --- |
| Wi-Fi dédié indépendant de la box ou réseau habituel de la maison ? | LAN domestique au départ ; routeur et point d’accès Wi-Fi dédiés dans un second temps. |
| Prise électrique uniquement au départ ou batterie à intégrer dès la conception ? | Prise électrique pour commencer ; batterie à étudier plus tard. |
| Qui peut ajouter des documents et gérer les mises à jour ? | Seulement Louis et Marc au début pour simplifier le prototype. |

## Études complémentaires demandées

Louis souhaite étudier la fiabilité des usages sensibles avec des outils spécialisés. Les champignons sont un exemple, pas un recentrage du projet sur la mycologie. Voir [l’étude de fiabilité](06-fiabilite-et-outils.md).

Il demande aussi d’examiner un mode agentique, plusieurs tailles de modèles et des travaux longs lancés le soir : une heure de traitement est acceptable si le gain sur un 8B est réel. Cela complète le dialogue courant sans modifier son délai cible. Voir [les modes IA et travaux longs](07-modes-ia-et-travaux-longs.md). Les solutions décrites sont des pistes à tester, sans modèle ni architecture imposés.

## Étude comparative demandée

Louis demande une sélection de modèles et outils pour chaque mode, la faisabilité sur les PC actuels et le gain réel d’un gros modèle lent. Il ajoute des exemples de machines autour de 1 000 € et des paliers plus puissants pour Marc si les résultats le justifient. Neuf et occasion acceptés ; aucun achat autorisé par cette étude.

Capacités déclarées pour les deux machines : 32 Go RAM et 8 Go VRAM. Références exactes à inventorier ; ne pas déduire une variante de GPU de ce seul chiffre. Voir [modèles et outils](08-selection-modeles-et-outils.md), [matériel dédié](09-machines-dediees.md), [évaluation](10-protocole-comparaison-ia.md).

## Points encore ouverts

Le cadrage permet de préparer l’étude technique sans prolonger l’entretien sur les choix déjà exprimés. Restent notamment :

- Inventaire exact des deux PC : références CPU/GPU, versions des systèmes, pilotes et stockage libre ; 8 Go VRAM et 32 Go RAM déclarés pour chacun.
- Sélection des composants, modèles et contenus ; licences et compatibilité à vérifier.
- Scénarios de test, nombre d’utilisateurs simultanés et définition de la qualité IA suffisante.
- Méthode de sauvegarde, restauration, livraison des mises à jour et préparation hors ligne.
- Configuration familiale de référence et éventuelle commercialisation, après les essais.

La [fiche du prototype](05-perimetre-prototype.md) regroupe le périmètre actuel et propose des vérifications. Aucun déploiement ni achat n’est décidé par cette fiche.

## Registre des décisions

| Date | Sujet | Statut | Conclusion et origine |
| --- | --- | --- | --- |
| 2026-10-30 | Travail immédiat | Confirmé | Clarifier le projet par des questions et produire des documents Markdown ; demande de Louis. |
| 2026-10-30 | Dépôt cible | Confirmé | Initialiser le projet avec `git@github.com:Tanchouteur/SetupSurvie.git` ; demande de Louis. |
| 2026-10-30 | Première étape | Confirmé | Prototype complet pour Louis et Marc ; vente envisagée dans un second temps. |
| 2026-10-30 | Publication de la documentation | Autorisé | Louis autorise la publication de tous les documents créés, contexte initial inclus. |
| 2026-10-30 | Système principal | Confirmé | Conserver Windows 11 et les usages actuels. Pas de réinstallation Linux décidée. |
| 2026-10-30 | Utilisation partagée | Confirmé | Plusieurs utilisateurs, attente acceptable d’une à deux minutes ; espace commun au prototype. |
| 2026-10-30 | Analyse de photos | Arbitrage délégué | Tester si simple à intégrer ; proposition de fonction facultative, reportable selon les essais. |
| 2026-10-30 | Visibilité du dépôt | Déclaré par Louis | Dépôt passé en privé ; réglage non vérifié indépendamment. |
| 2026-10-30 | Appareils familiaux | Confirmé | Un appareil par famille ; minimiser le coût pour une qualité IA suffisante, à définir et mesurer. |
| 2026-10-30 | PC Linux | Précisé | Machine de développement dans la chambre de Louis, sans rôle de serveur permanent commun aux familles. |
| 2026-10-30 | Bibliothèque et assistant | Confirmé | Viser le maximum de contenu et combiner connaissances du modèle et recherche dans les documents. |
| 2026-10-30 | Budget matériel familial | Indicatif | Autour de 1 000 €, à ajuster selon les performances, sans prix de vente arrêté. |
| 2026-10-30 | Déploiement chez Marc | Confirmé / envisagé | PC Windows partagé avec ses usages habituels au départ ; éventuel achat ultérieur d’une machine dédiée. |
| 2026-10-30 | Langues documentaires | Confirmé | Inclure largement le français et l’anglais, avec utilisation en français ; recherche multilingue à vérifier. |
| 2026-10-30 | Réseau | Confirmé | LAN domestique au prototype ; routeur et Wi-Fi dédiés dans un second temps. |
| 2026-10-30 | Alimentation | Confirmé | Prise électrique ; batterie reportée. |
| 2026-10-30 | Gestion des contenus | Confirmé | Ajouts documentaires et mises à jour assurés uniquement par Louis et Marc au début. |
| 2026-10-30 | Architecture et modèle IA | Ouvert | Aucune sélection définitive dans le contexte transmis. |

Chaque décision ultérieure doit indiquer ce qui a été retenu, pourquoi, et les vérifications encore nécessaires. Une suggestion de l’assistant ne devient pas une décision sans validation ou instruction correspondante.
