# Essais sur le PC Linux de Louis — 11 novembre 2026

## Environnement et stockage

Ryzen 9 7950X (16 cœurs / 32 threads), 32 Go de RAM, RTX 2060 de 6 Go ; Bazzite 45.
Le pilote reconnaît la carte. Podman et le support NVIDIA CDI sont déjà disponibles.
Cette voie d'essai utilise Podman directement ; les installateurs Docker Windows/Linux existants ne sont pas modifiés.

Limite demandée : **600 Go décimaux au total**. Le fichier
`/var/mnt/data/AI/SetupSurvie/storage.img`, sur le SSD Crucial de 4 To, a une taille
logique fixe de **590 000 000 000 octets**. C'est une image ext4 creuse : elle ne
consomme que les blocs réellement écrits. Les 10 Go de marge couvrent notamment
les métadonnées du système de fichiers hôte. Ne pas agrandir cette image ni créer
de sauvegarde ou de téléchargement à côté sans revoir le budget.

UDisks monte le volume dans `/run/media/louis/SetupSurvie` ; **les octets restent
physiquement sur le SSD de 4 To**, malgré ce point de montage sous `/run/media`.
Images des conteneurs, modèles, documents, caches, journaux et résultats sont dans
ce volume. Les sockets et verrous temporaires sont dans `/run/user/1000/setupsurvie`
(mémoire volatile). Le dépôt source existant reste à son emplacement initial.

Chaque appel Podman vérifie le montage, la taille de l'image, son périphérique loop
et son fichier de backing : si le volume manque, il refuse de télécharger plutôt
que d'écrire dans le point de montage vide sur le SSD système.
Les journaux des services sont limités à 10 Mo par conteneur.

## Commandes

Depuis le dépôt :

```bash
./scripts/lab.sh mount       # à refaire après un redémarrage
./scripts/lab.sh up          # démarre avec les images et modèles déjà préparés
./scripts/lab.sh status
./scripts/lab.sh down        # arrête, conserve toutes les données
./scripts/lab.sh unmount     # arrête, retire les conteneurs et démonte ; conserve les données
```

Préparation initiale, seulement si nécessaire et avec Internet :

```bash
./scripts/lab.sh pull
./scripts/lab.sh prepare
./scripts/lab.sh up
./scripts/lab.sh pull-model
```

Le laboratoire écoute uniquement sur le PC : portail `http://localhost:8080`,
assistant `http://localhost:3000`, Kiwix `http://localhost:8081`.
Identifiants administrateur dans `/run/media/louis/SetupSurvie/private/identifiants.txt`.
Les services ne sont pas configurés pour démarrer automatiquement au démarrage du PC.

Nettoyage complet **irréversible**, à exécuter seulement pour tout supprimer :

```bash
./scripts/lab.sh clean --erase-data
```

Cette commande arrête les services dédiés, démonte le volume puis supprime
`storage.img` : modèles, documents, comptes et résultats sont effacés ensemble.
Elle conserve le dépôt et n'utilise aucun nettoyage global de Podman.
Le raccourci `/var/mnt/data/AI/SetupSurvie/gerer.sh` accepte les mêmes arguments.

## Protocole des premiers essais

`python3 scripts/lab_benchmark.py` enregistre les réponses, paramètres, temps
jusqu'au premier texte, compteurs du moteur, placement GPU et relevés de VRAM dans
`/run/media/louis/SetupSurvie/results/benchmark.json`. Trois répétitions par cas :
addition, réserve d'eau, réponse française à partir de la fiche anglaise ALPHA
fournie dans le prompt. Le premier appel commence avec le modèle déchargé.

Le cas ALPHA avec texte fourni ne valide pas la recherche documentaire : celle-ci
demande un import puis une récupération effective du passage par Open WebUI.
Les relevés incluent l'activité habituelle du bureau et les éventuelles opérations
de préparation concomitantes ; ce sont des mesures de premier démarrage, pas un
classement contrôlé de modèles.

## Résultats

Mesures locales du 11 novembre, avec `qwen3.5:4b-q4_K_M`, digest
`d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`,
Ollama 0.40.13, contexte 4 096, raisonnement désactivé pour les réponses mesurées.

| Essai | Résultat observé |
| --- | --- |
| Portail, Kiwix, Open WebUI | HTTP 200 sur les trois services ; Kiwix avec catalogue vide |
| NVIDIA dans le conteneur | RTX 2060 reconnue ; Ollama indique 100 % GPU, `size_vram = size = 3 140 495 604` octets |
| Neuf générations, trois cas répétés trois fois | Réponses attendues sur les neuf : quatre ; 33 jours et 6 litres ; 72 litres avec charge indéterminée |
| Génération à chaud | Médiane 78,56 tokens/s, plage 73,36–84,34 ; sorties courtes et prompts répétés, avec cache |
| Premier texte à chaud | Médiane 0,056 s sur ces petits prompts ; ne représente pas le délai complet de la chaîne documentaire |
| Premier appel à froid | 56,01 s jusqu'au premier texte ; le moteur relève 27,34 s de chargement, le reste comprend notamment le traitement initial |
| VRAM totale du PC pendant ce benchmark | Pic échantillonné de 4 913 Mio, bureau compris ; une mesure par seconde |
| Import et recherche documentaire | Import réel de `box.en.txt`, statut terminé ; question française retrouvant le passage anglais via BGE-M3 |
| Réponse avec récupération par Open WebUI | 72 litres, charge non mesurée, citation `[1]` et source renvoyée par l'API ; réponse complète en 26,82 s lors du second essai |
| Embeddings sans réseau | Conteneur `--network=none`, cache en lecture seule, deux textes → matrice `(2, 1024)` |
| Génération sans réseau | Conteneur `--network=none`, modèles en lecture seule et GPU : 33 jours et 6 litres ; 58,36 s pour l'essai complet à froid |
| Arrêt, démontage, remontage, recréation des services | Réussis ; comptes, modèles, import et résultats conservés, HTTP 200 et liaison Open WebUI → Ollama vérifiés |
| Réponse documentaire après remontage | Source retrouvée, réponse complète avec `[1]` ; 82,32 s à froid pour toute la chaîne, sans retéléchargement |
| Stockage physique de l'image après ces essais | Environ 18,8 Go décimaux, pour une capacité logique de 590 Go ; aucune image dans le stockage Podman par défaut |
| Vérifications du code | 16 tests unitaires réussis, compilation Python, syntaxe Bash ; intégration Docker Compose non exécutée car Docker absent |

Le premier essai documentaire a retrouvé la source, mais a épuisé la limite de
512 tokens en raisonnement sans produire de réponse finale. Le rapport initial
est conservé dans `results/document-test-initial-empty.json`. L'API Open WebUI
attend ici `think: false` **dans `options`**, contrairement à l'appel direct au
moteur : le test a été corrigé et refuse désormais les réponses vides, tronquées
ou sans source. Les 26,82 s incluent les étapes supplémentaires d'Open WebUI,
notamment la génération des requêtes ; ils ne sont pas une mesure de génération
pure du modèle. Les réglages de raisonnement de l'interface restent à affiner
selon les usages.

Les réponses brutes et compteurs sont conservés dans `results/benchmark.json`,
`results/document-test.json` (après remontage), `results/document-test-warm.json`, `results/offline-generation.json` et
`results/remount-check.json`, et les journaux dans `logs/`. Les identifiants et
jetons d'authentification ne figurent pas dans les rapports des tests.

Aucune application du bureau n'a dû être fermée. Téléphone, vraie bibliothèque
ZIM française, comptes lecteurs, coupure physique d'Internet de toute la pile,
redémarrage du PC et restauration complète restent à tester. Les essais réseau
isolé ci-dessus valident deux composants, pas à eux seuls tout le scénario hors
ligne. Les petits cas réussis ne mesurent pas la fiabilité générale de l'IA.
