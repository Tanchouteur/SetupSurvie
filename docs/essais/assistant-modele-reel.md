# Tester l’assistant avec un modèle réel

**Recette de développement — 0.16.0, 15 novembre 2026.** Elle complète les tests
simulés ; elle ne s’exécute jamais automatiquement dans la CI. Le runner CPU
n’accueille aucun modèle. Employer une machine explicitement autorisée, avec
le moteur déjà installé et un environnement Python isolé contenant
`tests/requirements.txt`. Les accès propres à Louis restent dans Nexus.

`tests/real_assistant_check.py` appelle le vrai moteur d’assistant et la recherche
SQLite sur cinq notices fictives temporaires. Chaque information utile se trouve
après une longue introduction. Les archives ZIM sont absentes de cet essai.
Deux formulations demandent une synthèse puis une comparaison ; `--case natural`
permet de ne rejouer que la seconde. Aucun compte ni document réel n’est copié.

Exemple CPU, à exécuter **sur la machine du moteur** après contrôle des ressources :

```sh
python tests/real_assistant_check.py \
  --endpoint http://127.0.0.1:11434 --model gemma4:e4b \
  --context 16384 --predict 4096 --think true \
  --report /chemin/prive/assistant-reel.json
```

CPU et deux threads sont les défauts, y compris pour le préchargement. Le GPU
nécessite `--gpu-layers`, une estimation `--gpu-expected-mib` et une réserve
`--gpu-reserve-mib` explicites. Par exemple, huit couches et six threads ont été
essayés sur le R7. Le contrôle refuse un autre modèle Ollama en cours ou une
marge vidéo insuffisante ; il ne stoppe aucune application. Les sondages ne
garantissent pas l’absence de concurrence ultérieure. Ne pas assimiler une
estimation de l’API à une mesure continue de l’occupation GPU réelle.

L’outil n’installe aucun modèle et ne change pas le service. Les requêtes ont un
maintien en mémoire de quinze secondes. L’URL doit être locale. Le rapport est
privé et contient les réponses, sources, mesures, options demandées, empreinte du
code Python, empreinte de la recette, passages transmis et identité du modèle.
La présence des cinq valeurs est un repère
automatique ; elle ne valide ni les unités, ni les associations, ni les conclusions.

Lire les réponses : chaque valeur doit correspondre à sa notice ; le modèle ne
doit inventer ni obsolescence ni absence d’information. Un état `done` indique
une demande terminée, pas une approbation éditoriale. Comparer les formulations,
les échecs et un code antérieur à options égales. Conserver les essais défavorables.
Les limites de génération et de temps font partie du résultat.

Cette recette ne mesure pas la bibliothèque de Marc, les appels Kiwix, une vraie
contradiction documentaire, les illustrations ou la qualité d’une procédure.
Une validation réelle doit encore employer des besoins variés et des sources
relues, avec le modèle et le PC Windows cibles. Voir le
[bilan des premiers essais](2026-11-15-synthese-multi-sources-et-essais-reels.md).

Pour vérifier un changement de modèle dans la première demande, ajouter
`--switch-from llama3.1:8b --case natural`, en nommant un autre modèle **déjà installé**.
Ollama doit d’abord être au repos. La recette précharge uniquement ce modèle
d’essai, puis laisse l’assistant préparer le modèle sélectionné. Le rapport
conserve `switch_from` et les préparations mesurées. Cette option ne décharge
aucun modèle tiers et ne lève pas une pause d’une installation réelle.

Depuis 0.17.0, `--selected` donne une sélection explicite de cinq notices à
l’assistant, sans recherche préparatoire globale. `--pdf-fixture` remplace ces
notices par cinq petits PDF de six pages : chaque valeur utile se trouve à la
page six. Ces options permettent de vérifier la sélection des pages et leurs
références ; elles ne prouvent pas la lecture intégrale d’un livre. Les documents
sont fabriqués dans le répertoire temporaire et ne sont pas conservés dans le dépôt.

## Lecture longue — 0.18.0

`tests/real_summary_check.py` utilise deux petits PDF temporaires de 21 pages,
avec les deux valeurs à la dernière page, pour éprouver les étapes et leur
regroupement. L’API est fixée à la boucle locale 11434. Elle ne tourne jamais dans
la CI et ne télécharge aucun modèle. Exemple sur une machine autorisée disposant
déjà du modèle et après contrôle des ressources :

```sh
python tests/real_summary_check.py --model gemma4:e4b --gpu-layers 8 \
  --report /chemin/prive/synthese-longue.json
```

Sans `--gpu-layers`, l’essai demande le CPU. Cette recette dédiée utilise six
threads, contexte 16k, sortie maximale 4 096 tokens, maintien de quinze secondes,
estimation GPU 8 192 Mio et réserve 1 536 Mio ; la pause d’une installation réelle
n’est jamais levée. Elle refuse les autres modèles en cours, sans les arrêter.
Le rapport privé conserve réponses, instantanés de progression, graphe des notes
et empreinte du code. Relire attribution, unités, pages, limites et omissions ;
`completed` ne mesure pas cette fidélité. Voir le [bilan](2026-11-15-syntheses-longues-et-reprise.md).
