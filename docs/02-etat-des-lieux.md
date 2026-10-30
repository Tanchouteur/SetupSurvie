# État des lieux

Date : 30 octobre 2026.

## Ce qui existe

Le dossier de travail était vide à son ouverture. Le contexte transmis indique qu’aucune installation ni aucun développement n’avait été réalisé dans la conversation précédente. Cela ne permet pas de conclure à l’absence de travaux menés ailleurs : à confirmer avec Louis et Marc.

## Matériel déclaré

| Élément | Information transmise | Statut |
| --- | --- | --- |
| PC de Marc : GPU | NVIDIA RTX 5060 Ti, 8 Go de VRAM | Confirmé par Louis ; non inspecté |
| PC envisagé : mémoire | 32 Go ; DDR5 indiqué dans le contexte initial | Capacité redonnée par Louis ; non inspecté |
| PC envisagé : processeur | Probablement un Ryzen 5 | Estimation de Louis ; référence exacte inconnue |
| PC envisagé : stockage | Environ 4 To | Estimation de Louis ; type, capacité libre et organisation inconnus |
| PC envisagé : OS et disponibilité | Windows 11, autres usages à conserver | Confirmé par Louis ; aucune réinstallation autorisée |
| PC Linux de développement | Linux, carte déclarée RTX 2060 avec 8 Go VRAM, Ryzen 9, 32 Go RAM ; situé dans la chambre de Louis | Capacités confirmées par Louis ; référence GPU exacte, distribution et stockage à préciser |
| Réseau du prototype | LAN habituel de la maison | Confirmé ; routeur et point d’accès dédiés dans un second temps |
| Alimentation du prototype | Prise électrique | Confirmé ; batterie à étudier plus tard |

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

Louis évoque environ 1 000 € de matériel par appareil familial, à décider selon les performances. Cette enveloppe est indicative et ne constitue pas un prix de vente. Budget des éventuels compléments du prototype, matériel de série et consommation acceptable : à préciser.

## Reproduction envisagée

Séparer le système et les applications, les contenus communs (bibliothèque, modèles, index), puis les données propres à chaque appareil. Définir la préparation de l’hôte en complément de Docker, les versions, les sauvegardes, les mises à jour et une restauration hors ligne.

Les modalités restent à concevoir. Une éventuelle vente nécessitera une vérification distincte des licences des logiciels, modèles et contenus effectivement distribués.

## Conséquence des précisions de cadrage

Le PC principal doit conserver Windows 11 et ses usages actuels. La piste Linux initiale ne peut donc pas être appliquée par une réinstallation de cette machine. Les modes de déploiement compatibles avec Windows et l’accès GPU devront être étudiés avant tout choix.

Un PC Linux (RTX 2060, Ryzen 9), situé dans la chambre de Louis, est prévu pendant le développement. Il constitue une cible pour les essais, sans rôle d’hébergement permanent partagé entre les familles. Ne pas déduire sa VRAM ou ses performances du seul nom du GPU, ni sa capacité d’hébergement du seul processeur.

Comparer les deux machines quand leur disponibilité et leurs caractéristiques seront connues : facilité d’installation, qualité et délai des réponses, gêne pour les usages habituels, accès réseau. Le choix de la première cible reste ouvert.

## Dimensionnement de l’appareil familial

Cible confirmée : chaque famille dispose de son propre appareil. Minimiser son coût matériel tout en conservant une qualité IA suffisante est un objectif central. L’enveloppe indicative est d’environ 1 000 €, ajustable selon les performances. La définition mesurable de « suffisant » reste ouverte.

L’étude devra comparer des configurations et modèles sur les mêmes questions en français et recherches documentaires, avec la charge familiale attendue. Relever coût matériel, qualité, délai, mémoire utilisée et stockage nécessaire. Aucun achat ni seuil de performance n’est décidé à ce stade.

Le souhait d’une bibliothèque maximale remplace l’idée d’une petite sélection comme cible finale. Cela n’interdit pas un échantillon réduit pour les premiers essais. Il faudra distinguer volume conservé, volume consultable et volume réellement indexé pour l’IA, puis mesurer la place des index et les temps de préparation.

Chez Marc, conserver un premier déploiement sur son PC Windows à usages multiples. Une éventuelle machine dédiée, allumée au besoin, constitue une étape ultérieure envisagée. L’OS de cette machine et le budget effectivement engagé restent ouverts.

Le catalogue visé doit couvrir largement le français et l’anglais. La sélection et les essais devront vérifier la recherche de sources anglaises à partir d’une question française ainsi que la restitution fidèle en français, sans présumer que la langue du dialogue garantit la qualité de la recherche.

## Administration du prototype

Louis et Marc gèrent seuls les ajouts documentaires et les mises à jour au départ. L’import autonome par les familles n’est pas demandé pour cette version. Le mode d’administration et la méthode de livraison des mises à jour restent à concevoir.

Les tests sans Internet doivent conserver le LAN domestique opérationnel. Le fonctionnement avec une box éteinte n’est pas garanti par ce premier périmètre ; il relève de l’évolution vers un réseau dédié.

## Étude des modèles et machines dédiées

Louis précise que les deux PC disposent de 32 Go de RAM et 8 Go de VRAM. Il accepte les appareils neufs ou d’occasion et souhaite aussi connaître les spécifications de machines plus puissantes si Marc constate un gain des gros modèles. Aucun achat n’est demandé.

La [sélection des modèles et outils](08-selection-modeles-et-outils.md), les [pistes matérielles](09-machines-dediees.md) et le [protocole comparatif](10-protocole-comparaison-ia.md) distinguent les sources publiées des estimations et des futurs essais locaux. Ils actualisent les premières pistes Qwen3 8B/32B sans les effacer de l’historique.
