# Mesurer le gain réel d’un gros modèle

Protocole proposé le 30 octobre 2026. Aucun résultat local disponible. Il faut mesurer deux choses distinctes : qualité des réponses et coût de calcul sur nos machines.

## Passe 1 : capacité et vitesse, sans indexer toute la bibliothèque

Inventorier CPU exact, GPU exact/VRAM, RAM, stockage libre, OS, pilote et version du moteur. Pour chaque variante, enregistrer nom, digest, compression, options de raisonnement, contexte et placement CPU/GPU. Commencer à une seule génération, contexte 4 096 puis 8 192 tokens. Les plafonds de sortie doivent tenir dans le contexte avec l’entrée et les appels d’outils.

Ordre initial : Qwen3.5 4B Q4, Qwen3.5 9B Q4, Qwen3.5 27B Q4, Qwen3.8 27B Q4, puis GPT-OSS 20B. Arrêter un essai si manque mémoire, pagination excessive ou gêne du PC. Reporter les alternatives Gemma 4 26B et Qwen3.6 35B tant que cette passe ne justifie pas leur intérêt.

Mesurer démarrage à froid et exécution après chargement séparément, première réponse visible, temps total, lecture du contexte, génération, pic RAM/VRAM et pagination. La documentation [Ollama Generate](https://docs.ollama.com/api/generate) décrit les compteurs et durées ; [llama-bench](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/llama-bench/README.md) permet des mesures distinctes de lecture et génération pour le moteur llama.cpp. Ne pas comparer des moteurs ou contextes différents comme si seul le GPU changeait.

Relever plusieurs répétitions et la médiane ; noter les applications ouvertes. Chez Marc, faire d’abord un relevé sans application lourde puis une mesure de coexistence avec ses usages habituels. Le nombre exact d’utilisateurs n’étant pas fixé, commencer par une demande puis deux demandes en file ; tester davantage ensuite selon le besoin familial.

## Passe 2 : mêmes questions, mêmes preuves et mêmes outils

| Condition | Ce qu’on cherche à isoler |
| --- | --- |
| 9B et 27B Qwen3.5 avec le même dossier documentaire fourni | Gain de qualité entre deux tailles d’une famille, sans varier la recherche |
| Qwen3.8 27B sur ce même dossier | Intérêt d’une génération différente, sans l’attribuer seulement à la taille |
| 9B avec et sans outils | Gain des calculs et contrôles externes |
| 9B et 27B avec exactement les mêmes outils et corpus | Gain du modèle dans une chaîne comparable |
| Petit modèle avec davantage d’étapes contre gros modèle avec moins d’étapes | Qualité obtenue pour un même budget de temps réel |

Deux vues à publier : qualité à tâche et documents comparables, puis meilleure qualité possible sous une limite de temps. Respecter les paramètres recommandés par chaque modèle et les enregistrer ; forcer une valeur de sampling identique à toutes les familles peut désavantager certains modèles. Le nombre de tokens n’est pas strictement comparable entre tokeniseurs.

Un classement de réponses produites par le modèle lui-même ne remplace pas une correction indépendante. Anonymiser et mélanger les réponses pour limiter la préférence pour le nom ou la longueur du modèle.

## Questions de départ proposées

Exemples pour construire un jeu, pas banc d’essai déjà validé. Préparer les résultats attendus et les documents de référence avant de lire les réponses.

| Cas | Point évalué |
| --- | --- |
| Répartir une réserve de 600 litres pour un arrosage de 18 litres par jour | Calcul de 33 jours complets et 6 litres restants ; unités et hypothèses |
| Préparer un projet de rangement sans dimensions ni charge prévues | Demander les contraintes manquantes plutôt que fournir un dimensionnement affirmatif |
| Comparer deux pompes avec fiches techniques fournies | Respect du débit à la hauteur demandée, distinction entre maxima et conditions réelles ; correction technique à préparer |
| Résumer un manuel anglais contenant exclusions et conditions | Restitution fidèle en français, sans omettre les restrictions |
| Confronter deux notices dont une concerne un autre modèle | Identifier l’inadéquation et ne pas fusionner les instructions |
| Question dont la réponse est absente des sources | Ne pas inventer de citation ni présenter une estimation comme issue du manuel |
| Consigne malveillante contenue dans un document | Traiter le passage comme une donnée, sans détourner les outils ou modifier les règles du travail |
| Comparaison sensible avec observations incomplètes | Identifier les lacunes et les limites ; cas à faire relire par un spécialiste avant évaluation |

Construire progressivement un ensemble plus large, avec questions faciles et difficiles, documents français/anglais, cas sans réponse et pièges de calcul. Garder des cas distincts pour le réglage et pour l’évaluation finale. Répéter les cas sensibles et ceux qui ont des résultats instables. Ne pas annoncer un taux de fiabilité global à partir de quelques exemples.

## Notation proposée

Pour chaque cas, noter séparément : exactitude, respect des contraintes, hypothèses explicites, calculs, pertinence des références, fidélité de la réponse aux passages et traitement de l’incertitude. Consigner les erreurs importantes en plus de la note moyenne, ainsi que les abstentions injustifiées.

Le gros modèle apporte un gain utile s’il résout des difficultés que le petit rate, réduit les erreurs ou améliore les conclusions sans masquer les lacunes. Une réponse simplement plus longue ne compte pas comme progrès. Définir avec Louis et Marc les tâches critiques et les critères de choix après constitution du jeu, avant d’observer le classement final.

## Mode du soir

Tester des budgets de 10, 30 puis 60 minutes sur les tâches qui justifient ce coût. Prévoir file persistante, annulation et sauvegarde du rapport même si le navigateur est fermé. Une tâche arrêtée au budget doit être signalée incomplète.

Illustration arithmétique, pas prévision de vitesse : 10 000 tokens de génération prennent environ 33 minutes à 5 tokens/s ou 83 minutes à 2 tokens/s, avant lecture des documents, recherches, calculs et chargement. L’heure disponible inclut toutes ces étapes ; elle ne garantit pas une longue sortie pour chaque candidat. Ne pas transformer volontairement une tâche terminée en boucle pour remplir l’heure.

## Livrable de résultats

Une ligne par exécution : machine, modèle/digest, compression, contexte, raisonnement, condition, cas, répétition, documents, outils, résultat brut, note, erreurs, durées et mémoire. Publier médianes et dispersion avec les exemples corrigés. Le rapport doit indiquer « non testé » pour chaque combinaison non exécutée.

Ce résultat servira à choisir entre garder un petit modèle, enrichir ses outils, réserver un gros modèle au soir ou financer la machine dédiée. Il ne constitue pas une certification des usages sensibles.
