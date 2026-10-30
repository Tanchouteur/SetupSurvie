# Modèles et outils : sélection pour les essais

Étude documentaire du 30 octobre 2026. Aucun benchmark local réalisé : les deux PC ne sont pas accessibles depuis cet environnement. Les recommandations sont une sélection d’essai, pas une architecture définitivement adoptée.

## Conclusion de travail

Tester Qwen3.5 4B et 9B pour l’usage habituel, Qwen3.5 27B pour isoler autant que possible l’effet de taille dans une même famille, puis Qwen3.8 27B pour chercher un meilleur résultat avec une génération plus récente. Ajouter GPT-OSS 20B comme alternative agentique. Garder Gemma 4 26B A4B et Qwen3.6 35B A3B pour une deuxième passe si nécessaire.

Les deux PC ont, selon Louis, 32 Go de RAM et 8 Go de VRAM. Cela justifie de tester dès maintenant un gros modèle en calcul hybride, avec contexte limité et autres applications fermées pour le premier relevé. Ni le délai d’une heure ni la qualité supérieure ne sont acquis.

## Candidats et capacités à vérifier

Tailles arrondies des paquets locaux affichés par Ollama ; elles ne représentent pas la mémoire totale en fonctionnement. Les balises peuvent changer : enregistrer le digest avant les essais. « Q4 » est une compression des poids, avec compromis qualité/mémoire. Le nombre de paramètres ne classe pas à lui seul les capacités.

| Candidat et variante | Paquet observé | Capacités documentées et intérêt pour nous | Rôle proposé |
| --- | --- | --- | --- |
| `qwen3.5:4b-q4_K_M` | 3,3 Go | Texte, images, outils et raisonnement ; candidat léger pour explications courtes et questions sur quelques passages | Mode rapide sur 8 Go VRAM ; qualité sur tâches complexes à vérifier |
| `qwen3.5:9b-q4_K_M` | 6,6 Go | Même famille multimodale ; candidat principal pour dialogue français, documents et raisonnement courant | Mode courant plus capable ; GPU seul pas garanti avec 8 Go |
| `qwen3.5:27b-q4_K_M` | 17 Go | Multimodal ; utile pour comparer petit et gros modèle de la même famille | Étude de gain de taille, dossiers longs en hybride |
| `qwen3.8:27b-q4_K_M` | 18 Go | Texte/images, raisonnement et tâches longues avec outils ; génération plus récente | Candidat principal aux dossiers approfondis |
| `gpt-oss:20b` | 14 Go, MXFP4 | Texte, outils, effort de raisonnement réglable ; pas d’analyse d’image native dans cette sélection | Alternative agentique à comparer en français |
| `gemma4:26b-a4b-it-q4_K_M` | 18 Go | Texte/images, raisonnement et outils ; modèle à experts | Alternative de deuxième passe, compromis qualité/vitesse à mesurer |
| `qwen3.6:35b` | 23 Go, Q4_K_M observé | Texte/images, outils et raisonnement ; architecture à experts, orientée notamment tâches de code | Deuxième passe ; davantage de pression mémoire sur 32 Go |

Un modèle à experts active une partie de ses paramètres pour chaque token ; ses poids complets restent à stocker et la mémoire nécessaire ne se réduit pas au nombre de paramètres actifs. La répartition CPU/GPU peut changer le compromis de vitesse. Ne pas supposer qu’un 35B à experts sera meilleur ou plus lent qu’un 27B dense.

Sources des paquets : [Qwen3.5 4B](https://ollama.com/library/qwen3.5:4b-q4_K_M), [9B](https://ollama.com/library/qwen3.5:9b-q4_K_M), [27B dans la liste des variantes](https://ollama.com/library/qwen3.5/tags), [Qwen3.8](https://ollama.com/library/qwen3.8/tags), [GPT-OSS](https://ollama.com/library/gpt-oss:20b), [Gemma 4](https://ollama.com/library/gemma4/tags), [Qwen3.6 35B](https://ollama.com/library/qwen3.6:35b).

## Ce que les résultats publiés suggèrent

Les tableaux de l’éditeur Qwen donnent les résultats suivants. Ils motivent des essais, sans constituer un test de nos documents français ni des versions Q4 locales.

| Épreuve | Qwen3.5 9B | Qwen3.5 27B | Écart publié |
| --- | --- | --- | --- |
| MMLU-Pro : connaissances et raisonnement | 82,5 | 86,1 | +3,6 points |
| GPQA Diamond : questions scientifiques difficiles | 81,7 | 85,5 | +3,8 points |
| LiveCodeBench v6 : programmation | 65,6 | 80,7 | +15,1 points |
| VITA-Bench : tâches agentiques | 29,8 | 41,9 | +12,1 points |

Le gain varie donc fortement avec la tâche. Comparaison publiée entre tailles d’une famille, pas expérience isolant parfaitement la taille : entraînement, budgets de génération et protocoles peuvent différer. Le 27B ne rend pas toutes les réponses beaucoup meilleures. Sources : [fiche du 9B](https://huggingface.co/Qwen/Qwen3.5-9B), [fiche du 27B](https://huggingface.co/Qwen/Qwen3.5-27B).

Qwen publie aussi pour Qwen3.8 27B un GPQA Diamond de 89,2 et un LiveCodeBench v6 de 90,3. Ce sont des indices pour ajouter ce candidat récent ; les comparer directement au 9B mélange génération, taille et protocole. Ses résultats de tâches logicielles longues ne prouvent pas la justesse d’un plan de bricolage. [Fiche Qwen3.8](https://huggingface.co/Qwen/Qwen3.8-27B).

## Faisabilité des deux PC actuels

Hypothèse de départ : texte, contexte de 4 096 puis 8 192 tokens, une génération à la fois, modèles de recherche déchargés ou sur CPU. Les fenêtres annoncées de 128K/256K ne sont pas des objectifs réalistes automatiques sur ces PC.

| Candidat | PC de Marc, RTX 5060 Ti, 8 Go / 32 Go | PC Linux, carte déclarée RTX 2060, 8 Go / 32 Go |
| --- | --- | --- |
| Qwen3.5 4B Q4 | Premier candidat au chargement GPU complet ; mesurer la marge | Même cible de capacité ; vitesse à mesurer |
| Qwen3.5 9B Q4 | Plausible, marge VRAM étroite : affichage, images et contexte peuvent imposer une part CPU | Même risque de dépassement ; ne pas déduire la vitesse du nom Ryzen 9 |
| GPT-OSS 20B | Hybride CPU/GPU à tester ; pas de chargement complet dans 8 Go | Hybride à tester avec un moteur compatible ; ne pas appliquer les exigences du backend Transformers à tous les moteurs |
| Qwen3.5 / 3.8 27B Q4 | Essai lourd plausible en hybride, contexte court et applications fermées ; marge RAM à relever | Même classe d’essai, sans garantie de délai ni de qualité |
| Gemma 4 26B Q4 | Autre essai hybride plausible après les premiers résultats | Même réserve |
| Qwen3.6 35B Q4 | Plus contraignant ; arrêter si forte pagination ou impact excessif sur Windows | Même prudence ; ce n’est pas le premier essai lourd |

Ces conclusions sont des estimations de faisabilité, pas des mesures. RAM et VRAM ne forment pas un réservoir parfaitement interchangeable ; allocations, caches et duplication éventuelle dépendent du moteur. Un SSD rapide ne remplace pas la RAM pour calculer efficacement.

La documentation Ollama répertorie les RTX 5060 Ti et RTX 2060 comme GPU pris en charge. Le nom exact de la carte Linux doit néanmoins être vérifié par inventaire : Louis annonce 8 Go sans référence détaillée. Vérifier les pilotes et les opérations réellement accélérées pour chaque modèle. [Support matériel](https://docs.ollama.com/gpu).

## Outils retenus pour l’étude

| Besoin | Candidat | Usage proposé / limite |
| --- | --- | --- |
| Exécuter les modèles | Ollama | Première solution d’essai, API locale et changement de modèles ; versions et digests à figer |
| Contrôler finement le chargement et mesurer | llama.cpp / llama-bench | Référence technique pour répartition CPU/GPU et vitesses ; ne pas cumuler deux moteurs sans besoin |
| Interface navigateur | Open WebUI | Interface existante pour comparer modèles, documents et outils ; ne fournit pas à elle seule notre service de dossiers longs |
| Représenter les passages pour la recherche | BGE-M3 ou Qwen3-Embedding-0.6B | Deux candidats multilingues à comparer sur recherche français → anglais ; CPU possible à tester pour préserver la VRAM |
| Recherche locale | Qdrant + recherche lexicale | Combiner proximité sémantique et mots exacts ; configuration hybride à construire, pas automatique |
| Retrier les passages trouvés | BGE-reranker-v2-m3 | Outil multilingue facultatif ; mesurer le gain et le délai sur CPU |
| Préparer les PDF | Docling | Extraction de structure, tableaux et OCR selon pipeline ; contrôler les résultats et préparer les modèles avant coupure réseau |
| Calculs et unités | SymPy + Pint | Fonctions ciblées : équations, calculs et conversions ; formules, hypothèses et entrées restent à contrôler |
| Travaux approfondis | LangGraph avec état persistant local | Enchaîner recherche, lecture, calcul, critique et synthèse ; limites et reprise à concevoir, pas de service cloud nécessaire au principe |
| Bibliothèque consultable | Kiwix en complément | ZIM consultables ; extraction/indexation IA à étudier séparément |

Pour commencer : Ollama + interface existante + un petit corpus + outils de calcul limités. Ajouter la recherche hybride puis le travail durable ; éviter de déployer tous les candidats simultanément. Cette étude ne tranche pas le choix global NOMAD / assemblage propre.

Chez Marc, Ollama peut fonctionner nativement sous Windows ; cela évite d’imposer un conteneur GPU au moteur lors des premiers essais. Les services adaptés restent candidats à Compose. Le déploiement Windows et celui Linux devront chacun être documentés. [Ollama Windows](https://docs.ollama.com/windows).

## Fonctionnement hors ligne et distribution

Télécharger à l’avance poids, modèles de recherche/OCR, images de conteneurs et dépendances. Utiliser uniquement des identifiants de modèles locaux, sans variante `cloud`. Tester physiquement sans Internet : la présence d’une option locale ne prouve pas que toute la chaîne l’est.

Les fiches consultées indiquent notamment Apache 2.0 pour les Qwen candidats et GPT-OSS ; BGE-M3 affiche MIT. La licence actuelle d’Open WebUI comporte une clause de marque avec exceptions : elle n’est pas à décrire comme une simple licence MIT. Examiner le fichier exact de chaque version avant toute distribution et conserver les notices ; les licences des documents restent distinctes. [Licence Open WebUI](https://github.com/open-webui/open-webui/blob/main/LICENSE).

## Autres sources techniques

- [OpenAI : GPT-OSS local avec Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama) : préférence pour au moins 16 Go de VRAM ou mémoire unifiée pour le 20B ; déport CPU possible, plus lent.
- [Gemma 4 : fiche de modèle](https://ai.google.dev/gemma/docs/core/model_card_4).
- [Qwen3.6 35B A3B : fiche](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).
- [Open WebUI](https://docs.openwebui.com/), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview).
- [BGE-M3](https://huggingface.co/BAAI/bge-m3), [Qwen3 Embedding 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), [BGE reranker](https://huggingface.co/BAAI/bge-reranker-v2-m3).
- [Recherche hybride Qdrant](https://qdrant.tech/documentation/search/hybrid-queries/), [Docling](https://github.com/docling-project/docling), [SymPy](https://docs.sympy.org/latest/index.html), [Pint](https://pint.readthedocs.io/en/stable/).
