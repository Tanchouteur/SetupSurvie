# Architecture concrète à essayer et installation reproductible

Proposition du 30 octobre 2026, fondée sur les besoins et la [comparaison NOMAD / assemblage](12-comparaison-nomad-assemblage.md). Architecture du paquet de prototype préparé ; services testés localement en conteneurs, validation sur vos deux PC encore à faire. La réponse reçue de Marc confirme l’importance du dialogue français et de la recherche dans les documents anglais avec réponse/traduction en français.

## Objectif de la première démonstration

Commencer sur Windows 11 chez Marc sans supprimer ses usages habituels, puis répéter sur le PC Linux de développement : ouvrir la bibliothèque depuis un téléphone, lire un article illustré sans IA, poser une question en français sur un guide anglais et ouvrir la source. Refaire sans Internet puis après redémarrage.

Les deux PC sont déclarés à 32 Go de RAM et 8 Go de VRAM. Une génération à la fois au départ ; consultation documentaire en parallèle. Commencer avec Qwen3.5 4B Q4 puis 9B Q4. Les essais 27B interviennent une fois le socle vérifié.

## Socle choisi pour l’essai

| Composant | Déploiement envisagé | Rôle / accès |
| --- | --- | --- |
| Ollama | Conteneur GPU sous Linux ; natif sous Windows pour le premier essai | API de calcul accessible aux services, pas nécessaire aux lecteurs de la bibliothèque |
| Open WebUI | Conteneur Compose dans les deux cas | Chat et collections de guides ; port LAN proposé 3000 |
| Kiwix Serve | Conteneur Compose | Archives ZIM et recherche directe ; port LAN proposé 8081 |
| Caddy | Conteneur Compose | Petit accueil français, catalogue statique et fichiers de guides en lecture seule ; port LAN proposé 8080 |
| BGE-M3 | Modèle local configuré dans la chaîne documentaire Open WebUI, CPU au premier essai | Recherche dans les guides français/anglais ; chargement anticipé nécessaire |

Ports proposés à vérifier avant usage pour éviter les conflits. Le portail ne remplace pas les lecteurs : il offre « Bibliothèque », « Assistant », puis les collections de guides et encyclopédies. Pour commencer, lire les PDF avec le lecteur du navigateur et conserver un lien de téléchargement ; vérifier l’ergonomie réelle sur téléphone. Un lecteur spécialisé peut être ajouté si les essais le justifient.

Les fichiers PDF sont gérés par Louis/Marc dans la bibliothèque commune, avec une copie importée dans Open WebUI pour les premiers essais. Conserver un identifiant et un lien vers l’original dans le catalogue. La synchronisation des ajouts et suppressions doit ensuite être automatisée ; ne pas supposer qu’un dossier monté dans le conteneur devient automatiquement une collection de connaissances.

La base documentaire native d’Open WebUI suffit pour la première collection d’essai ; pas de Qdrant séparé imposé immédiatement. Si son index devient limitant, choisir un stockage pris en charge et documenter la migration. Qdrant et Docling sont des extensions possibles à décider sur les résultats.

## Connexions et données

- Téléphone/ordinateur → portail, Open WebUI ou Kiwix, sur le LAN sans Internet.
- Open WebUI → Ollama pour la réponse ; recherche documentaire locale pour les passages.
- Kiwix → fichiers ZIM, sans dépendance à l’IA.
- Portail → catalogue et originaux PDF, sans dépendance à l’IA.

Séparer les volumes : `models`, `library/zim`, `library/guides`, `catalog`, `state/openwebui`, puis `state/jobs` pour l’évolution des dossiers longs. Les contenus servis aux lecteurs sont montés en lecture seule. Les écritures d’administration passent par la procédure des auteurs du système.

L’index du chat, les conversations et les réglages ont leur stockage persistant. Les représentations documentaires peuvent être recalculées, mais les sauvegarder évite une longue reconstruction. Les originaux, métadonnées de version/licence et réglages sont à conserver.

## Étape suivante : recherche encyclopédique et illustrations

Créer un petit service local indépendant, exposant des outils structurés :

1. Chercher dans les archives Kiwix sélectionnées.
2. Lire un article ou une section, avec adresse locale et identifiant de version.
3. Lister les images liées au passage et leurs légendes, puis fournir leurs adresses locales existantes.
4. Faire des calculs ou conversions ciblés avec les outils retenus.

Le connecter à Open WebUI par une interface d’outils documentée, par exemple OpenAPI. Conserver les associations texte/image et les mentions d’attribution disponibles. Tester la prise en charge du rendu et la pertinence des illustrations. Aucun index visuel complet de la bibliothèque n’est nécessaire pour ce premier niveau.

Le premier accès IA à Wikipédia utilisera la recherche à la demande, pas une indexation de toute Wikipédia dans la base vectorielle. Les ressources anglaises pourront demander une reformulation ou traduction de la requête : à tester explicitement. BGE-M3 sur les guides ne rend pas magiquement multilingue l’index de recherche Kiwix.

## Étape ultérieure : dossiers du soir

Ajouter un worker local avec file persistante, budgets de durée/étapes, annulation, enregistrement du rapport et état consultable. LangGraph reste le candidat pour organiser les étapes ; le mécanisme de file, stockage et reprise doit être conçu séparément.

Le worker appelle le même Ollama et les mêmes outils que le chat, en chargeant éventuellement un 27B. Arbitrer l’usage du GPU : un dossier lourd peut retarder le dialogue courant, mais ne doit pas empêcher la consultation de la bibliothèque. Ne pas considérer les tâches de chat en mémoire comme une reprise garantie après redémarrage du serveur.

## Rendre l’installation simple

Prévoir un paquet de version comprenant :

- Un Compose commun pour les services Web, et un complément Linux GPU pour Ollama.
- Un fichier d’exemple des paramètres, puis des valeurs propres à l’appareil : adresse LAN, chemins, ports et secrets générés.
- Un lanceur Linux et un lanceur PowerShell, chacun vérifiant les prérequis avant d’agir.
- Une commande de diagnostic puis une commande de validation après installation.
- Un manifeste des images, modèles et contenus avec versions, empreintes et état de préparation.

L’objectif utilisateur sera un lanceur qui prépare les paramètres, démarre les services et affiche l’adresse d’accueil. Ce paquet est désormais préparé : voir le [guide](14-installation.md) et le [rapport de vérification](16-verification-prototype.md). Les prérequis système restent à installer séparément ; ne pas annoncer une installation en un clic validée sur les deux PC.

Le lanceur vérifie : espace disque, moteur Docker/Compose, ports, accès GPU, présence des fichiers attendus et disponibilité d’Ollama. Il doit pouvoir être relancé sans perdre les données, signaler précisément une erreur et ne pas recréer les identifiants à chaque exécution.

Sous Windows, prévoir Docker Desktop/WSL2 pour les services et Ollama natif ; vérifier l’accès des conteneurs à l’API, le pare-feu LAN, le démarrage après reboot, l’ouverture de session et la mise en veille. Sous Linux, vérifier pilote NVIDIA et accès GPU des conteneurs. Docker ne remplace pas ces prérequis.

## Versions et fonctionnement hors ligne

Le Compose utilise les versions et empreintes enregistrées dans `deploy/versions.json`. Leur démarrage a été contrôlé localement ; ne pas utiliser `latest` comme définition d’une livraison. Le téléchargement et l’indexation sont une phase de préparation distincte du démarrage normal. Précharger notamment embeddings, OCR éventuel et ressources du navigateur ; aucun téléchargement implicite ne doit être nécessaire à la recette hors ligne.

Préparer ensuite un kit hors ligne contenant les images exportées, modèles, contenus et index ainsi que les réglages et notices nécessaires. Les pilotes et l’installation initiale de Docker demandent aussi des supports/prérequis adaptés au système. Ne pas confondre « redémarrer hors ligne après préparation » et « installer un PC nu sans Internet » : valider ces deux scénarios séparément si le second est retenu.

## Mise à jour et restauration

Sauvegarder les données persistantes de manière cohérente avec leurs bases, conserver la version précédente et tester la nouvelle avant bascule. Séparer mises à jour des logiciels, modèles, index et bibliothèque. Un changement de modèle d’embeddings exige une réindexation cohérente ; une nouvelle archive doit être accompagnée des références à jour.

La restauration doit être essayée vers un dossier ou une machine distincte, sans toucher aux originaux. Vérifier lecture des guides/ZIM, conversations, réglages, accès LAN et réponse IA sans téléchargement. Copier des volumes sans test ne suffit pas à déclarer une sauvegarde restaurable.

## Critères pour accepter le socle

1. Accueil et lecture des guides/articles illustrés depuis téléphone et ordinateur, sans passer par le chat.
2. Question française sur un document anglais : bonne source retrouvée, sens restitué en français, original ouvrable.
3. Services lisibles et erreurs compréhensibles si un modèle est absent ou occupé.
4. Fonctionnement sans Internet et après redémarrage, avec LAN conservé.
5. Installation relançable et données conservées ; versions et état documentaire identifiables.
6. Sauvegarde puis restauration réussie du petit jeu d’essai.

Les critères spécifiques aux images retrouvées et aux travaux longs s’ajoutent quand ces extensions sont réalisées. Utiliser ensuite le protocole des modèles pour décider du matériel ; aucun achat préalable n’est nécessaire à la première preuve de concept.

## Références de la proposition

- [Open WebUI : collections et recherche documentaire](https://docs.openwebui.com/features/workspace/knowledge/).
- [Open WebUI : outils et services externes](https://docs.openwebui.com/features/extensibility/plugin/tools/).
- [Ollama natif sous Windows](https://docs.ollama.com/windows).
- [Kiwix Serve : recherche et lecture de contenu](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html).
- [BGE-M3 : modèle de recherche multilingue](https://huggingface.co/BAAI/bge-m3).

Les versions, paramètres et interactions de cette proposition doivent être vérifiés dans la phase d’implémentation ; les sources ne constituent pas une recette locale réussie.
