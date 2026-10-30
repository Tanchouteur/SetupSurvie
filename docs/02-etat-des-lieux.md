# État des lieux

Date : 30 octobre 2026.

## Ce qui existe

Le dossier de travail était vide à son ouverture. Le contexte transmis indique qu’aucune installation ni aucun développement n’avait été réalisé dans la conversation précédente. Cela ne permet pas de conclure à l’absence de travaux menés ailleurs : à confirmer avec Louis et Marc.

## Matériel déclaré

| Élément | Information transmise | Statut |
| --- | --- | --- |
| PC de Marc : GPU | NVIDIA RTX 5060 Ti, 8 Go de VRAM | Déclaré, non inspecté |
| PC de Marc : mémoire | 32 Go DDR5 | Déclaré, non inspecté |
| Processeur, stockage et OS | Inconnus | À renseigner |
| PC de Louis | Peut servir au développement | Configuration et rôle à préciser |
| Réseau dédié et alimentation autonome | Pas de choix | À cadrer |

## Pistes techniques, sans choix arrêté

| Sujet | Pistes du contexte initial | Ce qui reste à établir |
| --- | --- | --- |
| Base logicielle | [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad), assemblage Compose propre | Adéquation aux besoins, versions, licences, tests |
| Collecte de contenus | [Offline Survival](https://github.com/carlospolop/offline-survival) | Utilité réelle, contenus français, intégration |
| Bibliothèque | Kiwix / archives ZIM et documents illustrés | Sélection, consultation, droits de redistribution |
| IA | Ollama ; Qwen3 8B proposé comme premier candidat | Qualité en français, mémoire, vitesse sur le matériel réel |
| Recherche documentaire | Embeddings multilingues ; Qdrant évoqué | Documents réellement indexables et qualité des sources retrouvées |
| Hôte et réseau | Linux, GPU accessible aux conteneurs, point d’accès dédié | OS, pilotes, démarrage, accès client sans Internet |

Les liens sont conservés comme références du contexte fourni. Leur contenu actuel n’a pas encore été audité pour ce dépôt. Aucune solution de cette table n’est approuvée comme dépendance du projet.

Consulter un ZIM dans Kiwix et permettre à l’IA d’en rechercher le contenu sont deux capacités distinctes à vérifier séparément.

## Stockage et coût

Le contexte contient une addition estimative d’environ 235 Go de ressources et modèles, une marge proposée de 350–500 Go et une suggestion de SSD de 1 To. Ces valeurs ne sont pas des mesures d’installation ni un dimensionnement retenu. Les index, dépendances, fichiers temporaires et sauvegardes doivent être comptés après sélection du contenu.

Budget du prototype, matériel de série, prix de vente et consommation acceptable : inconnus.

## Reproduction envisagée

Séparer le système et les applications, les contenus communs (bibliothèque, modèles, index), puis les données propres à chaque appareil. Définir la préparation de l’hôte en complément de Docker, les versions, les sauvegardes, les mises à jour et une restauration hors ligne.

Les modalités restent à concevoir. Une éventuelle vente nécessitera une vérification distincte des licences des logiciels, modèles et contenus effectivement distribués.
