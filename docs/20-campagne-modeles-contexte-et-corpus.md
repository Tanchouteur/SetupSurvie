# Campagne modèles, contexte, outils et corpus

État au 11 novembre 2026. **Calcul IA suspendu à la demande de Louis pendant qu'il
joue. Ne lancer ni génération ni campagne avant son autorisation explicite.**
Les résultats ci-dessous proviennent des essais précédents ; aucune nouvelle
inférence n'a été faite après cette consigne.

## Correction de l'audit du harnais

La réponse du Qwen 27B citant `create_automation`, `search_calendar_events`, etc.
correspond à des fonctions réelles de l'Open WebUI installé. Le premier audit ne
recensait que les outils personnalisés, dont les listes étaient vides, et avait
omis ces outils natifs. Il ne fallait donc pas attribuer cette liste à une invention
du modèle. L'activation d'une fonction ne prouve toutefois pas qu'une action a été
effectivement exécutée ou validée hors ligne.

L'inventaire obtenu avec `get_builtin_tools` contient initialement **29 outils**,
avec **21 116 octets de schémas JSON**. Louis confirme que calendriers et
automatisations sont inutiles dans ce projet. Ils sont désactivés ; les profils
excluent aussi notes, messagerie, gestion de tâches, création de compétences,
sous-agents et autres fonctions non retenues. Il reste **11 outils natifs**, pour
**7 548 octets de schémas** : temps, demande de précisions et accès aux connaissances.
Le détail est dans `results/harness-audit.json`.

Une véritable alerte du moteur a été relevée : entrée de **6 852 tokens tronquée
à 2 050 tokens**. Une petite fenêtre remplie par les descriptions d'outils et le
budget de sortie laisse trop peu de place aux documents et à la conversation.
Les 4K étaient un réglage initial de diagnostic, pas une limite intrinsèque des
modèles. Les trois profils passent à **8K**, avec une consigne française versionnée
dans `deploy/assistant-system.fr.txt`. Les 16K et éventuellement 32K restent des
conditions de test, pas des capacités validées sur ce PC.

Un travail automatique lié au chat dont la réponse était déjà terminée occupait
encore le 27B. Il a été arrêté sans supprimer le chat. Génération automatique des
titres, étiquettes, suggestions, complétion et reformulation des requêtes sont
désactivées dans le laboratoire. La recherche documentaire utilise la question
directement ; vérifier son gain réel avec les essais RAG prévus ci-dessous.

## Modèles effectivement téléchargés

| Modèle local | Paquet approximatif | Modes prévus |
| --- | --- | --- |
| Qwen3.5 4B Q4_K_M | 3,32 Go | Sans / avec raisonnement |
| Qwen3.5 9B Q4_K_M | 6,55 Go | Sans / avec raisonnement |
| Qwen3.5 27B Q4_K_M | 17,48 Go | Sans / avec raisonnement |
| Gemma 4 E4B | 6,58 Go | Sans / avec raisonnement |
| GPT-OSS 20B | 13,79 Go | Low / high ; ne pas assimiler low à sans raisonnement |
| Gemma 4 26B A4B Q4_K_M | 17,99 Go | Sans / avec raisonnement ; candidat à experts |
| Qwen3.8 27B Q4_K_M | 17,74 Go | Sans / avec raisonnement |

Les noms « E4B » et « A4B » ne désignent pas tous les mêmes nombres de paramètres
stockés ; comparer les paquets, la mémoire réelle et les performances, pas seulement
le nombre dans le nom. Digests, tailles, capacités et métadonnées effectivement
présents sont dans `results/research-models.json`.

Sources : [variantes Gemma 4](https://ollama.com/library/gemma4),
[variantes Qwen3.8](https://ollama.com/library/qwen3.8),
[documentation officielle OpenAI pour GPT-OSS avec Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama).
Les modèles sont exécutés localement, sans API payante OpenAI.

## Corpus effectivement prêt

| Collection | Taille | État |
| --- | --- | --- |
| Wikipédia français illustré, mai 2026 | 55,44 Go | Téléchargé, SHA-256 vérifié |
| Wikipédia anglais illustré, août 2026 | 127,42 Go | Téléchargé, SHA-256 vérifié |
| Wikilivres français, octobre 2026 | 1,15 Go | Téléchargé, SHA-256 vérifié |
| Wikibooks anglais, octobre 2026 | 4,74 Go | Téléchargé, SHA-256 vérifié |

Les fichiers restent dans `data/library/zim`, sur le volume plafonné de 590 Go,
avec une marge sous les **600 Go** autorisés. Occupation physique relevée après
téléchargements : environ **286 Go décimaux**. Manifeste initial dans
`results/library-manifest.json`, compléments dans `results/corpus-manifest.json`.
Les originaux conservent leurs attributions et mentions de licence ; leur présence
ne constitue pas une validation éditoriale de tous les contenus.

Les transferts sont reprenables, par plages contrôlées, puis soumis au SHA-256
complet avant publication. Les archives publiques doivent être lisibles par
l'utilisateur du conteneur Kiwix : permission 0644 après vérification. Une erreur
de permission sur les nouveaux fichiers a été corrigée. Le répertoire de stockage
interne de Podman et les secrets ne sont pas rendus publics.

Cinq sources réelles ont aussi été extraites avec titre, identifiant, URL locale
et archive : loi d'Ohm, kilowatt-heure, conservation des aliments, chapitre anglais
de radioamateur et chapitre anglais de cuisine. Les formules MathML conservent
leur représentation alternative LaTeX lorsqu'elle existe ; contrôler les autres
tableaux/formules avant de généraliser cette extraction expérimentale.

Elles sont importées dans une collection Open WebUI dédiée. **La recherche française
retrouve effectivement le passage anglais du manuel de radioamateur**, dans une
collection comprenant plusieurs documents. Cette vérification porte sur la
récupération ; la nouvelle réponse complète de l'IA sur ce corpus reste à mesurer.
Fichiers : `results/research-sources.json`, `research-import.json` et
`real-rag-retrieval.json`.

## Protocole reproductible

Les fixtures sont dans `fixtures/evaluation/`. Le moteur n'évalue pas lui-même ses
réponses : les résultats attendus des exercices fermés sont préparés à l'avance,
et les réponses documentaires ouvertes doivent être relues indépendamment.

### 1. Sélection initiale

Deux cas : réserve de 600 litres à 18 litres/jour et inventaire des outils d'une
requête ne déclarant aucun outil. Tester les sept candidats, avec leurs deux modes,
à 8K, mêmes questions, consigne et graine. Une configuration incompatible, un
serveur occupé, un délai dépassé ou une réponse tronquée doivent être identifiés
séparément d'une réponse factuellement fausse.

### 2. Qualité sur des finalistes

Ajouter calcul d'énergie en plusieurs étapes, conversions, document anglais avec
valeur absente, choix de pompe suivant les conditions de sa fiche, information
inconnue et instruction malveillante dans un document. Faire trois répétitions sur
les configurations les plus prometteuses. Le script note les champs attendus,
les erreurs, le temps total, le premier texte, les tokens de génération, RAM/swap,
VRAM et placement CPU/GPU. Il ne publie pas un taux général de fiabilité à partir
de ces quelques cas.

### 3. Contexte et recherche documentaire

Comparer le **même document** à 4K, 8K et 16K : manuel anglais réel, article sur
l'énergie et repère artificiel au milieu d'un document d'environ 20 000 caractères.
Ce dernier est un test de capacité du contexte, pas un guide réel. Les avertissements
de troncature du moteur sont conservés. Éventuellement essayer 32K si la mémoire
et les délais le permettent. Une fenêtre plus grande coûte de la mémoire et du
traitement ; il faut aussi comparer document entier et passages ciblés par recherche.

### 4. Outils réellement exécutés

`lab_tool_eval.py` expose un petit outil déterministe de division avec reste,
limité aux nombres positifs et sans exécution de code arbitraire. Le modèle doit
appeler l'outil, recevoir son résultat et répondre. Conserver schéma, arguments,
résultat de l'outil et réponse finale. Cela permet de comparer petit modèle avec
calcul vérifié et modèle avec raisonnement seul. Ce prototype n'est pas encore
un calculateur général branché à l'interface publique.

### 5. Chaîne complète et décision

Question française sur les sources anglaises, collection partagée, réponse et
source ouvrable dans Open WebUI ; comparer avant/après suppression des traitements
automatiques et vérifier sans réseau. Relever les premiers chargements séparément
des appels à chaud. Les téléchargements et l'activité du PC peuvent influencer les
mesures ; la première série n'était pas une mesure en laboratoire isolé.

Choisir les profils selon exactitude, fidélité aux sources, utilisation correcte
des outils, délai total et ressources. Une réponse plus longue ne compte pas comme
un progrès. Garder les modes sans raisonnement pour les tâches où ils réussissent
de façon reproductible ; mesurer le surcoût et le bénéfice du raisonnement ailleurs.

## Premiers résultats, avant le mode jeu

Une seule exécution par cas et mode à 8K, donc résultats exploratoires. Les temps
ci-dessous sont ceux du cas réserve, avec chargement éventuel : pas des médianes
à chaud ni une comparaison parfaite des seuls modes.

| Modèle / mode | Réserve | Temps total de cet appel |
| --- | --- | --- |
| Qwen3.5 4B sans raisonnement | Non mesuré correctement : serveur occupé, délai dépassé | Exclu de la comparaison |
| Qwen3.5 4B avec raisonnement | 33 jours, 6 litres | 33,55 s |
| Qwen3.5 9B sans raisonnement | Faux : 33 jours, 12 litres | 12,43 s |
| Qwen3.5 9B avec raisonnement | 33 jours, 6 litres | 31,02 s |
| Qwen3.5 27B sans raisonnement | 33 jours, 6 litres | 32,09 s |
| Qwen3.5 27B avec raisonnement | 33 jours, 6 litres | 383,90 s |
| Gemma 4 E4B sans raisonnement | 33 jours, 6 litres | 22,52 s |
| Gemma 4 E4B avec raisonnement | 33 jours, 6 litres | 7,95 s |

L'écart Gemma sans/avec raisonnement ne prouve pas que raisonner accélère : l'ordre
des appels et le chargement diffèrent. Tous les inventaires d'outils terminés
répondent correctement avec une liste vide. Deux appels initiaux du 4B ont expiré
pendant le travail du 27B en arrière-plan ; ils doivent être rejoués, sans être
présentés comme des erreurs de connaissance du 4B.

Gemma E4B mérite des essais supplémentaires. **Aucun vainqueur n'est déclaré.**
GPT-OSS 20B, Gemma 26B et Qwen3.8 27B sont téléchargés, mais n'ont pas encore été
évalués dans cette campagne. Les grands contextes, l'outil et les réponses complètes
sur les nouvelles sources restent à tester après autorisation de reprendre l'IA.

## Reprise explicite après le jeu

Le marqueur `private/inference-paused.json` bloque les lanceurs de tests et le
démarrage d'Ollama par les scripts. `lab.sh up` laisse Ollama arrêté tant qu'il
existe ; les autres services restent gérables. Aucune reprise automatique prévue.

Seulement lorsque Louis autorise à nouveau les calculs :

```bash
./scripts/lab.sh resume-inference
python3 scripts/lab_eval.py --models qwen3.5:4b-q4_K_M qwen3.5:9b-q4_K_M qwen3.5:27b-q4_K_M gemma4:e4b --run screening-v1 --retry-errors
python3 scripts/lab_eval.py --models gpt-oss:20b gemma4:26b-a4b-it-q4_K_M qwen3.8:27b-q4_K_M --run screening-extra-v1
```

Puis choisir les finalistes et lancer les conditions nécessaires. Exemples :

```bash
python3 scripts/lab_eval.py --models qwen3.5:4b-q4_K_M gemma4:e4b gpt-oss:20b --run core-v1 --cases reserve energy units english_source pump missing injection harness --repetitions 3
python3 scripts/lab_eval.py --models qwen3.5:4b-q4_K_M gemma4:e4b gpt-oss:20b --modes off low --run context-v1 --contexts 4096 8192 16384 --cases --real-documents --context-probe
python3 scripts/lab_tool_eval.py --models qwen3.5:4b-q4_K_M gemma4:e4b gpt-oss:20b
python3 scripts/lab_rag_research.py --model qwen3.5:4b-q4_K_M
```

`--max-tokens` permet de distinguer un budget de sortie insuffisant d'un échec de
raisonnement. Chaque campagne conserve son protocole et son empreinte ; utiliser
un nouveau nom pour changer les conditions. Les résultats déjà terminés sont
conservés à la reprise ; `--retry-errors` archive et rejoue les erreurs d'exécution.

Arrêt et consultation sans modèle :

```bash
./scripts/lab.sh pause-inference
./scripts/lab.sh status
./scripts/lab.sh jobs
```

Le téléchargement documentaire est terminé. Son éventuelle reprise explicite se
fait avec `lab.sh download-corpus`; `down` arrête le service de transfert dédié
avant les conteneurs. Le nettoyage complet existant efface aussi les nouveaux
modèles, corpus et résultats contenus dans le volume.

Vérifications sans LLM pendant le mode jeu : 27 tests unitaires cumulés réussis,
dont verrou de démarrage, reprise de transfert, correction des réponses et calcul
exact ; syntaxe Python/Bash et diff vérifiés. L'intégration Docker Compose n'est
pas exécutée faute de Docker sur ce PC. Les quatre collections sont accessibles
dans Kiwix ; son conteneur a été recréé pour rétablir le port publié après le dernier
rechargement. Ollama est arrêté et le verrou empêche sa relance par les scripts.
