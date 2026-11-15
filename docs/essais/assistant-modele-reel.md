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
