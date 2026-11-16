# Tester l’assistant avec un modèle réel

**Recette de développement — actualisée en 0.23.1, 16 novembre 2026.** Elle complète les tests
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

## Identifiants longs et budget documentaire — 0.23.1

`tests/real_context_check.py --model gemma4:e4b --context 16384 --report /chemin/prive/contexte.json`
exerce l’orchestrateur avec douze sources fictives aux identifiants/métadonnées
longs, puis un vrai modèle déjà installé. La recherche et les textes sont simulés,
sans archive téléchargée. Le dossier doit tenir dans le contexte, atteindre le
modèle et conserver des citations lues ; la fidélité se relit séparément. Le code
de la recette explicite 32 couches GPU, six threads, 4 096 tokens de sortie,
réserve 1 536 Mio et estimation vidéo 8 192 Mio. Adapter ces constantes si une
autre machine est autorisée ; cette recette GPU ne tourne jamais dans le runner CPU.
Elle refuse les autres modèles chargés et n’en décharge aucun. `--context 32768`
change seulement cet essai, sans régler le logiciel. Le rapport privé conserve
les propositions rejetées et les mesures ; un échec de citation reste un échec.

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


## Illustrations originales — 0.19.0

`tests/real_illustrations_check.py` fait lire un PDF de 21 pages et un article HTML
fictifs, avec deux schémas et un logo à écarter. Le vrai moteur et le vrai modèle
choisissent des identifiants de visuels, jamais des pixels ; le lecteur de l’article
est simulé. Aucun contenu externe n’est téléchargé. L’API locale, les six threads,
le contexte 16k, les plafonds et réserves sont ceux de la recette longue ci-dessus.

```sh
python tests/real_illustrations_check.py --model gemma4:e4b --gpu-layers 8 \
  --report /chemin/prive/illustrations.json
```

Le rapport privé conserve réponse, sources, sélection, mesures et empreintes du
code, de la recette et du contexte produit. Relire le choix et la prose : deux bons
identifiants ne suffisent pas si le modèle annonce une impossibilité d’affichage.
Cette recette ne teste pas le rendu navigateur, protégé par une recette distincte.

Ajouter `--illustrations` à `tests/real_summary_check.py` pour la sélection de deux
pages originales après lecture intégrale des deux PDF et avant la rédaction longue.
Le rapport conserve alors aussi les sources réellement enregistrées. Ces essais
sur fixtures ne valident pas la fidélité d’un vrai livre ou la compréhension des
schémas. Le [bilan 0.19.0](2026-11-15-illustrations-originales.md) conserve les échecs,
les modifications retenues et les observations du vrai modèle.


## Procédures sur une vraie notice — 0.19.1

`tests/real_radio_check.py` utilise une notice UV-5R préparée séparément sur la
machine d’inférence. Le fichier doit correspondre à l’empreinte du catalogue ;
le script ne le télécharge pas et n’entre pas dans la CI. Il fait une vraie
recherche, lit les passages et appelle le modèle, avec les réserves, le contexte
16k, les six threads et le maintien court des autres recettes. Aucun poste radio
n’est contrôlé. Exemple sur une machine autorisée avec ces prérequis :

```sh
python tests/real_radio_check.py --model gemma4:e4b --gpu-layers 8 \
  --manual /chemin/prive/notice-baofeng.pdf --report /chemin/prive/radio.json
```

`--case keypad`, `memory`, `quarter`, `dipole`, `quarter-calculated` ou
`unspecified` limite le rejeu à une question ; sinon les six sont jouées. Le script vérifie le PDF avant de
l’indexer temporairement, puis utilise la fiche d’antenne du dépôt. Les rapports
restent privés et gardent réponses, outils et références, pas seulement `done`.
`review_reference` est une grille de relecture, pas une certification automatique.
Comparer la séquence des touches au PDF et les calculs aux formules, rechercher
les erreurs de bras/longueur totale, la lecture effective et les paramètres manquants.
Le [bilan](2026-11-15-notices-et-guidage-pratique.md) conserve les cas défavorables.
Ce manuel ne représente pas tous les savoir-faire ou tous les appareils.


Pour élargir à d’autres domaines sans modifier le moteur, la même recette accepte
`--scenario-file /dossier/prive/scenarios.json` à la place de `--manual`.
Le JSON contient `documents` (nom de fichier simple `path`, `title`, `language`,
`sha256`, métadonnées optionnelles) et `cases` (`name`, `question`, `review_reference`).
Les fichiers doivent être dans le même dossier que ce manifeste et correspondre
à leur empreinte ; pas de lien extérieur au dossier ni de téléchargement implicite.
Douze documents et 32 questions au maximum ; chaque document fait au plus 32 Mo.
Ce dispositif compare des besoins différents et des modèles déjà installés,
sans introduire leurs commandes ni leurs réponses dans le moteur du produit.

Le mode de réflexion du profil d’essai peut être choisi avec `--think false`,
`true`, `low`, `medium` ou `high` selon ce que le modèle installé prend en charge.
Le défaut de cette recette est `true` pour les essais Gemma décrits ; ne pas le
transposer à un modèle dépourvu de cette capacité. Les profils du produit ne sont
pas modifiés par ce choix de laboratoire.

La recette accepte `--domain resilience` pour vérifier que les mêmes ressources
restent accessibles dans l’espace pratique. Le défaut reste `all` ; le rapport
conserve ce choix, qui ne doit pas être déduit du seul titre d’un document.


Depuis 0.20.0, `--follow-up "Et les conditions pour cette procédure ?"` ajoute
une seconde question dans la même conversation après chaque cas choisi.
Utiliser `--case memory` ou un nom de manifeste pour isoler le besoin. Le rapport
conserve deux demandes, leurs lectures propres, références, mesures et même
`conversation_id`. La recette ne doit pas considérer un ancien numéro de citation
comme une nouvelle lecture. La relecture des conditions reste un choix du modèle,
à comparer aux textes et prérequis réels ; le statut `done` n’en certifie pas le sens.


## Recette réelle de traduction — 0.20.1

Sur le R7 autorisé, `tests/real_translation_check.py` accepte un PDF déjà présent
`--source`, son `--sha256`, son `--title`, sa `--provenance`, une plage de dix pages
au maximum `--first` / `--last`, le `--model` installé et un `--report` privé.
Les options `--gpu-layers` et `--think` sont explicites ; aucune inférence dans la CI.
`--pause-after 1` interrompt puis reprend après un passage terminé, si d’autres
restent. `--preload-model` teste un changement avec un autre modèle déjà installé,
en exigeant un moteur sans modèle chargé au départ. Le modèle préchargé par la
recette expire naturellement ou suit l’ordonnanceur ; aucun arrêt forcé.
Le rapport contient des textes sources/traduits et doit rester privé. Les contrôles
techniques, la traduction terminée et une relecture humaine sont des états distincts.
