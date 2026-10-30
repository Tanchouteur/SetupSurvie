# NOMAD ou assemblage : comparaison et recommandation d’essai

Étude du 30 octobre 2026. Lecture de documentation et de code, sans installation ni test fonctionnel. NOMAD inspecté au commit `54ee30a44902e5c252b477f8685c26ec3064ab72` du 5 octobre 2026, associé aux notes de version v1.35.1. Les évolutions ultérieures nécessiteront une nouvelle vérification.

## Conclusion

Proposition : essayer d’abord un assemblage Ollama + Open WebUI + Kiwix avec un petit portail français, en réutilisant leurs fonctions existantes. Nos différenciateurs sont la recherche français/anglais, les illustrations documentaires et les dossiers longs avec outils ; l’assemblage offre des points d’extension adaptés sans modifier le cœur d’un portail tiers.

NOMAD reste une alternative crédible et un bon point de comparaison : il apporte déjà une gestion centralisée des services et contenus que l’assemblage de trois logiciels ne fournit pas. Si la priorité devient un appareil regroupant rapidement encyclopédie, livres, cartes et cours, avec peu de personnalisation IA, sa valeur augmente nettement.

Ce choix est une recommandation pour le prototype, pas une preuve de supériorité ou une décision irréversible. Aucun déploiement n’a encore été effectué.

## Ce que l’examen de NOMAD confirme

- Portail, catalogue et gestion de services, contenus et téléchargements ; Kiwix et chat local, avec options de bibliothèques de livres et fichiers. Voir [dépôt officiel](https://github.com/Crosstalk-Solutions/project-nomad) et [catalogue d’applications au commit inspecté](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/database/seeders/service_seeder.ts).
- Indexation des textes ZIM pour l’IA : service d’extraction, métadonnées d’articles et de sections, puis jobs d’embeddings par lots. Ce n’est donc pas une fonction intégralement à développer dans NOMAD. Son coût sur une encyclopédie entière et sa qualité multilingue restent à mesurer. [Extraction ZIM](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/services/zim_extraction_service.ts), [jobs d’indexation](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/jobs/embed_file_job.ts).
- Chat avec pièces jointes image, sélection du modèle, raisonnement et sources issues de la recherche. Dans le chat en streaming inspecté, une fermeture de connexion annule la génération amont ; ce parcours n’est pas notre service de dossiers continuant toute la nuit. L’interface du raisonnement transmet notamment `medium` pour GPT-OSS lorsqu’il est activé, pas un choix complet de tous les niveaux. [Contrôleur du chat](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/controllers/ollama_controller.ts).
- Les sections ZIM extraites sont textuelles ; le parcours inspecté ne constitue pas un moteur de récupération de figures avec légendes et attribution. Les sources du chat sont dédupliquées notamment par fichier/archive : ne pas les assimiler sans test à des liens précis vers chaque passage et image. [Extraction HTML](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/utils/zim_html.ts), [sources du chat](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/utils/rag_prompt.ts).
- Le modèle d’embeddings du chemin inspecté est `nomic-embed-text:v1.5`, défini dans le code et utilisé par le service de recherche. Sa fiche est étiquetée anglais. Cela ne prouve pas un échec en français, mais ne valide pas notre recherche français → anglais ; prévoir évaluation et éventuellement adaptation puis réindexation. [Constantes](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/constants/ollama.ts), [recherche](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/admin/app/services/rag_service.ts), [fiche du modèle](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5).
- Un module de traduction hors ligne de pages Kiwix existe, avec français parmi les langues prévues. Son README mentionne notamment des tableaux et résultats de recherche non traduits, et une recherche conservant les termes de la langue originale. Il ne remplace pas la recherche documentaire multilingue ni une interface utilisateur française complète. [Module Translate](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/install/nomad-translate/README.md).

Présence de code signifie capacité implémentée à examiner, pas fonction validée dans nos conditions. L’absence de fonction trouvée dans ces parcours n’est pas une preuve qu’aucune extension communautaire ne l’offre.

## Comparaison selon nos besoins

| Besoin | NOMAD inspecté | Assemblage proposé |
| --- | --- | --- |
| Portail commun | Déjà présent ; administration et contenu intégrés | Petit accueil français à préparer ; liens vers les lecteurs existants |
| Bibliothèque indépendante de l’IA | Kiwix et applications de lecture disponibles | Kiwix + catalogue local de guides ; ne pas confondre Open WebUI et lecteur de toute la bibliothèque |
| Téléphone | Interface Web et lecteurs existants ; confort réel non testé | Open WebUI/Kiwix et portail à vérifier sur mobile ; pas de promesse fondée sur le seul accès Web |
| Français de l’interface | Parcours inspectés en anglais ; pas de localisation complète française constatée | Open WebUI dispose de traductions françaises ; portail commun sous notre contrôle ; lecteurs à configurer |
| Question française sur document anglais | Pipeline existant, configuration de recherche à évaluer/adapter | Modèle de recherche multilingue configurable ; BGE-M3 comme premier candidat |
| Wikipédia/ZIM dans les réponses | Indexation textuelle déjà implémentée, avec préparation | Connecteur Kiwix à créer pour chercher et lire à la demande ; indexation massive évitée au départ |
| PDF et guides dans le chat | Import et recherche existants | Fonctions Knowledge/RAG déjà présentes dans Open WebUI |
| Envoyer une photo à l’IA | Parcours présent pour modèle compatible | Parcours disponible avec modèle compatible ; tester le modèle et la version |
| Retrouver une illustration de la bibliothèque | Pas de chaîne complète texte/figure/légende identifiée dans le parcours inspecté | Connecteur à développer ; pas automatique avec le RAG textuel |
| Plusieurs modèles et raisonnement | Déjà présents ; paramètres de l’intégration à contrôler | Déjà disponibles ; profils et options exactes à configurer/tester |
| Outils de calcul et recherche itérative | Pas de boucle générale d’appel d’outils identifiée dans le chat inspecté | Interfaces d’outils OpenAPI/MCP/Python documentées ; outils métier à fournir |
| Dossier long navigateur fermé | Le chat streaming inspecté est annulé à la déconnexion | Documentation de tâches de chat côté serveur ; ne vaut pas une file durable résistant aux redémarrages |
| Windows 11 | WSL2 documenté comme parcours communautaire | Ollama natif possible ; services Web sous Docker Desktop/WSL2 à vérifier |
| Linux | Cible privilégiée de l’installation | Compose et préparation GPU à fournir |
| Versions, mise à jour, restauration | Gestion intégrée ; politique d’images à adapter pour reproductibilité stricte | Versions et procédure entièrement à notre charge, mais structure choisie pour ce besoin |

Open WebUI : [RAG](https://docs.openwebui.com/features/chat-conversations/rag/), [outils](https://docs.openwebui.com/features/extensibility/plugin/tools/), [exécution après déconnexion](https://docs.openwebui.com/features/extensibility/plugin/development/events/#persistence--browser-disconnection), [traductions](https://github.com/open-webui/open-webui/tree/main/src/lib/i18n/locales). Les traductions françaises sont aussi mentionnées dans ses [notes de version](https://open-webui.com/open-webui-release-notes/).

## Déploiement et maintenance

NOMAD est déjà conteneurisé, mais son Compose de gestion pilote des conteneurs supplémentaires via Docker et ajoute notamment MySQL, Redis, mise à jour et collecte disque. Le modèle fourni utilise des images `latest` et `pull_policy: always` pour certains composants : il faut figer et conserver les images de la version familiale, puis contrôler les mises à jour. Ce n’est pas un simple Compose contenant tous les services applicatifs déclarés à l’avance. [Compose inspecté](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/install/management_compose.yaml).

Le guide Windows NOMAD décrit WSL2, deux modes Docker, le démarrage et l’exposition sur le LAN. Il ne faut donc ni le déclarer incompatible Windows, ni promettre une installation Windows native en un clic. [Guide WSL2](https://www.projectnomad.us/install/wsl2).

L’assemblage comporte moins de services imposés au départ, mais nous prenons en charge l’installation, les données, les mises à jour et la recette sur les deux OS. Docker ne prépare pas les pilotes, WSL, la mise en veille ou l’accès réseau. Les deux options doivent passer une restauration sans téléchargement.

Le Command Center de NOMAD est volontairement sans authentification, pour LAN de confiance. Notre besoin distingue lecteurs et administrateurs Louis/Marc : avec NOMAD il faudrait prévoir cette séparation, par exemple une protection devant l’administration ; l’espace commun ne signifie pas administration ouverte à tous. [Politique officielle](https://github.com/Crosstalk-Solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/SECURITY.md).

## Travail propre à chaque option

| Chantier | Si base NOMAD | Si assemblage |
| --- | --- | --- |
| Catalogue et téléchargements | Réutiliser largement ; vérifier sélection française | Préparer manifeste de contenus et outil d’acquisition contrôlé |
| Interface française simple | Traduire ou créer un accueil simplifié ; ne pas confondre traduction des articles et de l’interface | Créer un petit accueil/catalogue ; réutiliser le chat et les lecteurs |
| Recherche français/anglais | Mesurer puis adapter le pipeline et réindexer si nécessaire | Configurer le modèle multilingue et tester les collections |
| Articles et illustrations ZIM | Étendre la récupération et les références du chat, ou ajouter un service externe | Créer un petit service indépendant de recherche/lecture/images |
| Calculs et agent | Ajouter une intégration agentique au chat ou une interface séparée | Brancher des outils ciblés via les interfaces existantes |
| Dossiers durables | Construire un worker et son accès utilisateur | Même besoin ; l’exécution de chat en mémoire ne suffit pas |
| Installation familiale | Adapter l’installateur, les versions, les secrets et le paquet hors ligne | Écrire les lanceurs et Compose, les vérifications et le paquet hors ligne |
| Sauvegarde/restauration | Couvrir bases et volumes NOMAD et de ses apps | Couvrir volumes du chat, catalogue, contenus et futurs jobs |

Ne pas développer notre propre moteur LLM, lecteur Wikipédia, chat complet ou base vectorielle. Éviter au premier essai NOMAD + Open WebUI + deux bibliothèques IA parallèles : cela dupliquerait une partie des index, réglages et parcours. Réutiliser les mêmes poids et fichiers de contenu dans une comparaison reste possible avec des volumes et écritures correctement séparés.

## Essai permettant de confirmer le choix

Une petite collection française/anglaise, une archive illustrée et les mêmes modèles suffisent pour comparer : accès direct mobile, question française trouvant une source anglaise, réponse avec original ouvrable, récupération d’image correcte, arrêt d’Internet, redémarrage et charge d’un gros modèle. Utiliser le [protocole existant](10-protocole-comparaison-ia.md).

Commencer par l’architecture décrite dans [le plan d’essai](13-architecture-et-installation-prototype.md). Revenir à NOMAD si le coût de notre gestion de bibliothèque dépasse sa valeur et que les extensions IA ne justifient pas l’assemblage. Ce point doit reposer sur les essais et l’expérience de Marc, pas seulement une grille de fonctions.
