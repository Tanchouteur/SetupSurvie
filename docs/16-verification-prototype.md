# Vérifications du paquet de prototype

Date : 30 octobre 2026. Environnement local : Mac ARM64, Docker Desktop, conteneurs Linux, Compose 5.5.1. Données isolées dans des dossiers temporaires, avec les fiches de démonstration uniquement et une petite archive ZIM de test. Ces contrôles ne constituent pas un test GPU du PC de Marc ou du PC Linux.

## Contrôles réussis

- Validation réelle de Compose pour les variantes Windows, Linux CPU et Linux NVIDIA, y compris les chemins contenant des espaces.
- 14 tests automatisés du lanceur : conservation des secrets/documents, refus de changer implicitement la cible ou le stockage, absence de téléchargement de préparation en mode hors ligne, révision des embeddings, refus des modèles cloud, erreurs de téléchargement, protection des réglages privés, contrôle des images importées et refus d’arrêter un PID non possédé.
- Syntaxe Bash et shell ; analyse syntaxique des trois scripts PowerShell dans l’image officielle Microsoft PowerShell 7.4. Cette analyse n’exécute pas les API Windows, le pare-feu ou le serveur natif.
- Existence des images et empreintes des quatre composants, avec variantes AMD64 disponibles ; démarrage local des quatre services, Ollama en CPU de diagnostic.
- Portail HTTP et catalogue : réponses 200 ; fiches et SVG illustratif accessibles.
- Vérification dans un navigateur ; largeur de téléphone 390 px sans débordement horizontal mesuré. L’essai depuis un vrai téléphone du LAN reste à faire.
- Kiwix vide : service disponible avec catalogue vide, sans boucle de redémarrage.
- Kiwix avec l’archive de test `wikipedia_en_100_mini_2026-01.zim` déjà fournie dans le dépôt NOMAD inspecté : chargement et recherche plein texte en anglais via le point d’accès natif. Cette archive n’est pas redistribuée dans SetupSurvie.
- Open WebUI v0.12.5 : démarrage, création automatique du compte administrateur et connexion avec les identifiants générés, sans les afficher dans les relevés.
- Préparation BGE-M3 à la révision fixée, chargement et production d’embeddings 1024 dimensions.
- BGE-M3 et tokeniseurs préchargés utilisables dans un conteneur lancé avec `--network none` et cache monté en lecture seule.
- Import réel de `box.en.txt` dans Open WebUI, statut terminé ; une question française retrouve le passage anglais contenant le volume et la limite de charge. Ce petit cas démontre le câblage, pas un taux de pertinence général.
- Connexion réelle Open WebUI → Ollama dans le réseau Compose ; version Ollama 0.40.13 relevée.

Le téléchargement du modèle de dialogue a été démarré dans l’environnement temporaire puis interrompu lors de son arrêt. Aucune génération complète ni mesure de vitesse n’est comptée comme réussie dans ce rapport. Les conteneurs de test ont été arrêtés ; les fichiers de préparation sont conservés dans les dossiers temporaires.

## Points restant à valider sur les cibles

- Exécution PowerShell complète sous Windows 11, détection du binaire Ollama, identité du processus natif, démarrage/arrêt dédié et coexistence avec le serveur habituel éventuel.
- Accès Docker Desktop → Ollama natif et règles du pare-feu Windows dans les conditions réelles.
- Réservation NVIDIA et calcul GPU sur les deux cartes ; exactitude des références matérielles et performances mesurées.
- Réponse complète de l’IA fondée sur le document anglais, citations et qualité linguistique sur un ensemble représentatif.
- Accès d’un compte lecteur aux collections partagées et distinction avec les permissions administrateur.
- Téléphone/tablette réels, lecture des PDF/EPUB et recherche dans une grande bibliothèque française.
- Déconnexion réelle d’Internet avec LAN conservé, puis redémarrage du PC ; le test réseau isolé des embeddings ne valide pas seul tout ce scénario.
- Export/import du kit d’images vers une machine distincte et restauration complète des données ; ces commandes ont des contrôles automatisés ciblés, pas encore une recette de restauration bout en bout.

## Fonctions qui ne sont pas livrées par ce socle

Recherche plein texte transversale guides + ZIM sans IA ; synchronisation automatique entre dossier de guides et collections Open WebUI ; connecteur IA vers Kiwix et récupération de figures ; outils de calcul spécialisés ; worker persistant pour dossiers longs ; mise à jour/retour arrière automatiques et installation d’un OS nu hors ligne.

Le [catalogue des fonctionnalités](15-fonctionnalites-et-user-stories.md) reste la référence pour les besoins à satisfaire. Aucun des essais ci-dessus ne certifie la fiabilité de conseils médicaux, de bricolage ou d’identification sensible.
