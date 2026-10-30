# Modes IA, agents et travaux longs : étude

Date : 30 octobre 2026. Louis demande d’étudier plusieurs tailles de modèles, un mode agentique et des travaux lancés le soir dont la réponse pourrait prendre une heure si la qualité augmente sensiblement par rapport à un 8B. Cette tolérance concerne les travaux longs volontaires ; elle ne remplace pas l’attente d’une à deux minutes exprimée pour l’usage habituel.

## Trois leviers distincts

1. Modèle plus capable : comparer plusieurs tailles, versions et niveaux de compression sur les mêmes tâches. La taille seule ne classe pas tous les modèles.
2. Raisonnement plus développé : certains modèles proposent un mode de raisonnement. Ollama expose des commandes variant selon le modèle. Le texte de raisonnement généré ne prouve pas la correction de la réponse.
3. Travail agentique : un programme organise une boucle de recherche, appels d’outils, interprétation et vérification. Ollama fournit l’appel d’outils, mais il faut fournir les outils et la logique d’exécution ; ce n’est pas un agent complet livré par cette seule fonction.

Un modèle lent ne devient pas plus savant du seul fait qu’on attend. Le budget supplémentaire doit servir à des opérations utiles. Une longue génération peut aussi répéter ou amplifier une erreur.

## Modes proposés, non encore sélectionnés

| Mode | But | Organisation à tester |
| --- | --- | --- |
| Rapide | Dialogue courant et recherche simple | Petit modèle, par exemple classe 8B comme référence, documents selon la demande |
| Approfondi | Comparaison et problème à plusieurs contraintes | Raisonnement, recherche itérative et outils vérifiables |
| Dossier long | Travail lancé le soir, résultat consultable ensuite | Modèle plus lourd si utile, plan de travail borné, recherches et calculs, rapport enregistré |

Plusieurs modèles peuvent être conservés sur disque et chargés successivement. Ne pas supposer qu’ils pourront tous rester en mémoire ou répondre simultanément.

## Exemple de dossier de bricolage

Pour un sujet tel que l’aménagement d’un récupérateur d’eau destiné à l’arrosage : recueillir les dimensions et contraintes manquantes, chercher les références locales, comparer plusieurs solutions, effectuer les calculs pertinents dans un outil, vérifier les unités et produire une synthèse avec hypothèses, sources et points restant à contrôler sur place.

Le résultat attendu est un dossier vérifiable. Les décisions impliquant structure, eau potable, gaz ou électricité exigent des références et compétences adaptées ; le fait de produire un dossier pendant une heure ne valide pas une réalisation.

## Faisabilité matérielle

[llama.cpp](https://github.com/ggml-org/llama.cpp) prend en charge la compression des modèles et une exécution hybride CPU/GPU permettant de dépasser la seule capacité VRAM. Cela rend certains modèles plus lourds envisageables en contrepartie d’une vitesse à mesurer ; ce n’est pas une promesse de fonctionnement sur les machines disponibles.

À titre de repère vérifié, le paquet [Qwen3 32B Q4_K_M dans Ollama](https://ollama.com/library/qwen3:32b) est affiché à environ 20 Go. Cette taille de fichier n’est pas la mémoire totale nécessaire : ajouter le contexte, les buffers, l’OS et les autres services. Avec les 32 Go de RAM déclarés chez Marc, la faisabilité et la coexistence avec ses applications restent à tester. La RAM du PC Linux est inconnue.

Une première comparaison pourrait couvrir la classe 8B, une classe intermédiaire autour de 14B et une classe autour de 30–32B selon la mémoire disponible. Ce sont des classes d’essai, pas une sélection des meilleurs modèles actuels ni une recommandation d’achat. Fixer versions et compression lors des essais. Accepter une heure n’autorise pas à conclure que n’importe quel modèle rentrera en mémoire ou terminera dans ce délai.

## Fonctionnement proposé des travaux longs

- File persistante avec états en attente, en cours, terminé, interrompu et échoué.
- Budget de durée, d’étapes et de génération ; détection des boucles et possibilité d’annulation.
- Clarifications initiales ; si une information indispensable manque ensuite, suspendre ou expliciter des scénarios, sans inventer la valeur.
- Enregistrement des références, calculs, paramètres et résultats intermédiaires pour comprendre un échec ; une vraie reprise nécessite une conception spécifique.
- Rapport final accessible après fermeture du navigateur, avec limites et tâches inachevées si le budget expire.
- Arbitrage entre les demandes courantes et le modèle lourd : occupation GPU/RAM, délai de rechargement et effet sur le PC Windows à mesurer.
- Outils locaux limités aux besoins : lecture documentaire et calculs contrôlés en priorité. Exécuter du code généré demande une isolation et des limites ; pas d’accès libre au système ou aux équipements par défaut.

## Protocole comparatif proposé

Comparer sur les mêmes problèmes : petit modèle seul ; petit modèle avec documents ; petit modèle avec outils ; modèle plus lourd avec les mêmes documents et outils. Comparer aussi différents budgets de raisonnement lorsque disponibles. Conserver un ensemble de cas non utilisé pour régler les invites.

Noter justesse, erreurs importantes, fidélité aux sources, pertinence des hypothèses, calculs, abstention, mémoire, durée et consommation si mesurable. Les réponses doivent être évaluées sur des références vérifiables ; longueur et style ne sont pas des mesures de qualité.

Retenir le travail long uniquement si son gain justifie son coût. Une bonne cible peut être un petit modèle pour l’interaction et un modèle plus lourd chargé ponctuellement, mais ce choix dépend des résultats.

## Références techniques consultées

- [Ollama — raisonnement](https://docs.ollama.com/capabilities/thinking).
- [Ollama — appels d’outils](https://docs.ollama.com/capabilities/tool-calling).
- [llama.cpp — quantification et exécution hybride](https://github.com/ggml-org/llama.cpp).
- [Qwen3 32B — paquet Ollama](https://ollama.com/library/qwen3:32b).

Ces capacités des composants ne sont pas encore implémentées dans SetupSurvie.
