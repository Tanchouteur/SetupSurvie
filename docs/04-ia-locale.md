# Rôle et limites de l’IA locale

État au 30 octobre 2026. Note de cadrage ; aucun modèle n’a été testé sur le PC envisagé. Les comportements ci-dessous sont des capacités à évaluer, pas des garanties du prototype.

## Ce que l’on cherche à obtenir

Un assistant capable de dialoguer en français, expliquer un sujet, aider à réfléchir et exploiter les documents disponibles sur le serveur. Le fonctionnement local indique où le calcul s’exécute ; il ne définit pas à lui seul la qualité des réponses.

La fiche officielle de [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) décrit notamment des capacités multilingues et de raisonnement. C’est un candidat mentionné dans le contexte initial, sans sélection définitive. Ses performances annoncées ne prouvent pas sa fiabilité sur nos usages en français.

## Trois capacités distinctes

1. **Dialoguer avec le modèle** : il produit une réponse à partir de son entraînement et du contexte fourni. Il peut se tromper, omettre une condition ou produire une explication plausible mais fausse.
2. **Exploiter la bibliothèque** : un moteur retrouve des passages et les fournit au modèle. Il faut tester la recherche, la fidélité de la réponse et les liens vers les originaux. Ajouter des fichiers au disque ne suffit pas à obtenir cette capacité.
3. **Analyser une image** : il faut un modèle et une interface compatibles. La [documentation Vision d’Ollama](https://docs.ollama.com/capabilities/vision) décrit l’entrée combinant images et texte. Qwen3-8B est un modèle de génération de texte ; sa présence ne fournit pas automatiquement cette fonction.

Consulter un guide illustré reste possible sans analyse d’images par l’IA.

## Application aux usages cités

| Usage | Objectif possible pour les essais | Limite à prendre en compte |
| --- | --- | --- |
| Médecine | Retrouver une référence et en expliquer le vocabulaire avec les sources | Une réponse fluide ou sourcée ne prouve pas un diagnostic ni l’adéquation d’un traitement |
| Ingénierie | Expliquer un principe, comparer des pistes, détailler les hypothèses d’un raisonnement | Vérifier les calculs, unités, hypothèses et contraintes avant réalisation |
| Cuisine | Proposer une recette à partir d’ingrédients disponibles | Vérifier les contraintes alimentaires et les conditions de préparation ou conservation |
| Champignons | Afficher des fiches et comparer des critères documentés | Une comparaison ou une identification photographique ne valide pas la comestibilité |

Ces objectifs sont proposés pour cadrer les essais ; ils ne sont pas encore des fonctions validées par Louis et Marc.

## Ce que le matériel ne permet pas encore de conclure

Les 32 Go de RAM et le GPU déclaré constituent une base à examiner. La VRAM exacte, la taille et la compression du modèle, la longueur des échanges et le nombre de requêtes simultanées influencent les possibilités. Selon la [FAQ Ollama](https://docs.ollama.com/faq), un modèle peut être chargé sur GPU, sur CPU ou réparti entre les deux.

En conséquence, aucune vitesse de réponse ni taille maximale de modèle n’est promise. Les quelque 4 To de stockage annoncés ne remplacent pas la mémoire nécessaire au calcul et leur disponibilité reste à vérifier.

## Photos : arbitrage provisoire

Proposition de l’assistant après délégation de Louis : essayer un modèle compatible avec les images dans une interface existante avant d’envisager tout développement spécifique. Une photo jointe à un échange représente un périmètre plus réduit qu’une indexation et une recherche de toutes les illustrations de la bibliothèque.

L’essai doit mesurer le chargement du modèle, la mémoire utilisée, le délai et la qualité sur des images de référence sans enjeu de sécurité. Il ne constitue pas une promesse d’identification fiable des champignons. Le caractère facultatif permet de conserver le socle du prototype si cette fonction s’avère coûteuse à intégrer.

## Évaluation proposée

Préparer avec Louis et Marc un petit ensemble de questions représentatives : explication simple, réflexion avec plusieurs contraintes, recherche d’un passage français, recherche d’une source anglaise depuis une question française, question sans réponse dans la bibliothèque. Prévoir un essai d’images facultatif conformément à l’arbitrage délégué par Louis ; reporter la fonction si elle complique trop l’installation ou ne donne pas de résultats satisfaisants.

Pour chaque essai, relever la pertinence, les erreurs, la fidélité aux sources et le temps de réponse. Comparer le dialogue seul et le dialogue avec documents. Utiliser des réponses de référence vérifiables ; l’impression de fluidité ne suffit pas à décider.
