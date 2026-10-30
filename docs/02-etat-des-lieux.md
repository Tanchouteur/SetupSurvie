# État des lieux

Date : 30 octobre 2026.

## Ce qui existe

Le dossier de travail était vide à son ouverture. Le contexte transmis indique qu’aucune installation ni aucun développement n’avait été réalisé dans la conversation précédente. Cela ne permet pas de conclure à l’absence de travaux menés ailleurs : à confirmer avec Louis et Marc.

## Matériel déclaré

| Élément | Information transmise | Statut |
| --- | --- | --- |
| PC envisagé : GPU | NVIDIA RTX 5060 Ti ; 8 Go de VRAM indiqués dans le contexte initial | Modèle confirmé de manière déclarative ; VRAM à vérifier |
| PC envisagé : mémoire | 32 Go ; DDR5 indiqué dans le contexte initial | Capacité redonnée par Louis ; non inspecté |
| PC envisagé : processeur | Probablement un Ryzen 5 | Estimation de Louis ; référence exacte inconnue |
| PC envisagé : stockage | Environ 4 To | Estimation de Louis ; type, capacité libre et organisation inconnus |
| PC envisagé : OS et disponibilité | Windows 11, autres usages à conserver | Confirmé par Louis ; aucune réinstallation autorisée |
| PC Linux de développement | Linux, RTX 2060, Ryzen 9 ; situé dans la chambre de Louis | Prévu pendant le développement ; distribution, VRAM, RAM et stockage à préciser |
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

## Conséquence des précisions de cadrage

Le PC principal doit conserver Windows 11 et ses usages actuels. La piste Linux initiale ne peut donc pas être appliquée par une réinstallation de cette machine. Les modes de déploiement compatibles avec Windows et l’accès GPU devront être étudiés avant tout choix.

Un PC Linux (RTX 2060, Ryzen 9), situé dans la chambre de Louis, est prévu pendant le développement. Il constitue une cible pour les essais, sans rôle d’hébergement permanent partagé entre les familles. Ne pas déduire sa VRAM ou ses performances du seul nom du GPU, ni sa capacité d’hébergement du seul processeur.

Comparer les deux machines quand leur disponibilité et leurs caractéristiques seront connues : facilité d’installation, qualité et délai des réponses, gêne pour les usages habituels, accès réseau. Le choix de la première cible reste ouvert.

## Dimensionnement de l’appareil familial

Cible confirmée : chaque famille dispose de son propre appareil. Minimiser son coût matériel tout en conservant une qualité IA suffisante est un objectif central. Budget et définition mesurable de « suffisant » restent ouverts.

L’étude devra comparer des configurations et modèles sur les mêmes questions en français et recherches documentaires, avec la charge familiale attendue. Relever coût matériel, qualité, délai, mémoire utilisée et stockage nécessaire. Aucun achat ni seuil de performance n’est décidé à ce stade.

Le souhait d’une bibliothèque maximale remplace l’idée d’une petite sélection comme cible finale. Cela n’interdit pas un échantillon réduit pour les premiers essais. Il faudra distinguer volume conservé, volume consultable et volume réellement indexé pour l’IA, puis mesurer la place des index et les temps de préparation.
