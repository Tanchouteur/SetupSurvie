# Avant la première version installée chez Marc

État vérifié le 11 novembre 2026. Objectif : une **version pilote utilisable et
récupérable par Marc**, sans Internet après préparation, sous Windows, accessible
depuis les appareils du réseau domestique. Ce document complète les fonctionnalités
du document 15 avec les constats des essais 17–18 et les nouvelles demandes de Louis.
Il constitue une liste de travaux ; les fonctions proposées ici ne sont pas déjà livrées.

Mise à jour : le [document 20](20-campagne-modeles-contexte-et-corpus.md) corrige
l'inventaire des outils natifs et décrit la consigne commune désormais installée,
le contexte de 8K, le périmètre d'outils réduit et le corpus bilingue téléchargé.
Les tableaux d'audit ci-dessous conservent l'état initial ayant motivé les travaux.

## Ce qui fonctionne déjà sur Linux

Les quatre services démarrent ; Wikipédia français illustré est installé et sa
recherche fonctionne depuis l'accueil. Trois modèles Qwen3.5 Q4_K_M sont disponibles
avec les noms rapide, moyenne et approfondie. La dictée a ses fichiers locaux et
a été testée sans réseau avec une voix de synthèse. Un guide anglais importé dans
Open WebUI est retrouvé depuis une question française, avec une réponse et une source.
Le stockage sur le SSD de 4 To reste plafonné sous 600 Go. Ces essais ne valident
ni Windows chez Marc ni l'ensemble du produit hors ligne et après redémarrage.

## Audit de la connexion et récupération souhaitée

Open WebUI fournit déjà un cookie de connexion `token`, `HttpOnly`, avec échéance
et durée maximale. Dans la configuration actuelle, la durée par défaut est `4w`,
soit 28 jours. La demande de Louis est **30 jours**, à appliquer explicitement
avec `JWT_EXPIRES_IN=30d`, et à vérifier côté cookie, expiration du jeton, fermeture
du navigateur, redémarrage du PC et nouvelle connexion. Décider explicitement si
ces 30 jours courent depuis la connexion ou sont prolongés après une nouvelle
authentification ; proposition pour la première version : 30 jours depuis la connexion.
Conserver les secrets de signature entre les redémarrages et tester la déconnexion.

Récupération à livrer sans dépendance à Internet ou au courrier électronique :

1. Un lecteur peut faire réinitialiser son compte par un administrateur local.
2. Pour le compte administrateur : code de récupération aléatoire, imprimable,
   conservé séparément du PC ; le serveur conserve une empreinte, pas le code en clair.
3. Le parcours « Mot de passe oublié » exige ce code pour définir un nouveau mot
   de passe, invalide le code utilisé et les anciennes sessions, puis fournit un
   nouveau code de secours. Limiter les essais et éviter toute remise à zéro ouverte
   à un simple visiteur du réseau.
4. Si mot de passe et code sont perdus : commande de secours sur le PC serveur,
   nécessitant l'accès local autorisé au système. Préserver comptes, conversations,
   documents et index. Ne pas supprimer la base Open WebUI pour récupérer un compte.
5. Tester tous les cas sur des comptes de recette, sans changer le compte courant
   de Louis, puis mettre la fiche de secours dans le kit remis à Marc.

Références : [durée de session Open WebUI](https://docs.openwebui.com/reference/env-configuration/#jwt_expires_in),
[récupération administrateur](https://docs.openwebui.com/troubleshooting/password-reset/).
Le code exact du conteneur installé a aussi été inspecté : `routers/auths.py`,
`utils/auth.py`, `env.py` et `config.py`. La récupération proposée est à développer,
pas une fonction de code imprimable supposée présente dans Open WebUI.

## Ce que les trois IA reçoivent réellement aujourd'hui

| Élément | Constat |
| --- | --- |
| Consigne commune SetupSurvie | Absente : aucun prompt système de projet dans les trois profils ; pas de consigne personnelle sur le compte audité |
| Contexte de dialogue | Messages de la conversation transmis par Open WebUI, dans une fenêtre de 4 096 tokens, pas toute la bibliothèque |
| Documents | Passages issus des documents explicitement associés ; aucune collection attachée par défaut aux profils |
| Consigne documentaire | Modèle de prompt natif Open WebUI : utiliser le contexte, citer les sources identifiées, répondre dans la langue de la question, reconnaître les lacunes |
| Profils | 4B sans raisonnement ; 9B et 27B avec raisonnement ; ces réglages ne constituent pas des spécialisations métier |
| Outils et fonctions ajoutés | Les listes des outils et fonctions personnalisés sont vides |
| Recherche Kiwix par l'IA | Absente, même si Kiwix fonctionne dans le navigateur |
| Calculateur vérifié / conversions | Absent ; les erreurs de calcul observées sont conservées dans les résultats |
| Recherche Internet | Désactivée |
| Fonctions natives de code et mémoire | L'API de configuration annonce code execution, code interpreter et mémoires activés ; leur comportement hors ligne et leurs droits ne sont pas validés |

Les fonctions natives activées dans l'interface ne signifient pas que chaque
modèle dispose déjà d'un outil fiable, connecté et testé. Aucun accès au shell de
l'agent de développement ou à ses connecteurs n'est transmis aux modèles locaux.

À réaliser : consigne commune versionnée, différences des trois modes explicites,
outils autorisés limités et testés, mémoire personnelle définie, sources traçables.
La consigne doit préciser le français, les unités, la distinction entre document
et connaissance générale, les hypothèses, l'absence de source, les questions à
poser quand des données manquent et le traitement des instructions présentes dans
un document comme des données. Elle accompagne les outils ; elle ne garantit pas
à elle seule la fiabilité des réponses.

## Liste des travaux nécessaires pour le pilote

| Lot | Travail restant | Critère avant validation |
| --- | --- | --- |
| 1 — Connexion et comptes | Session de 30 jours, compte lecteur distinct de l'administration, partage explicite des modèles et connaissances, historique par compte | Un lecteur peut utiliser les trois modes et les documents partagés ; il ne modifie pas l'installation et ne voit pas les conversations des autres |
| 2 — Récupération hors ligne | Parcours avec code de secours et commande locale de dernier recours | Récupération réussie sans réseau ni perte de conversations ; anciens accès invalidés |
| 3 — Comportement IA | Prompt commun, profils documentés, audit des fonctions natives et de la mémoire | Même question reproduite avec versions/paramètres connus ; distinction sources/hypothèses ; capacité à reconnaître les informations manquantes |
| 4 — Outils utiles | Calculs et conversions déterministes ; recherche/lecture de Kiwix par l'assistant ; liens locaux vers les sources et illustrations pertinentes | L'IA retrouve réellement un article, ouvre sa source et utilise le résultat d'un calcul vérifié ; erreurs d'outils compréhensibles |
| 5 — Bibliothèque pratique | Petit corpus réel de guides français/anglais, provenance/date/licence, procédure d'ajout et d'indexation, recherche dans le contenu des guides | Une information absente du titre d'un guide est retrouvée sans IA ; les documents utiles sont aussi interrogeables dans l'assistant |
| 6 — Interface | Parcours complet accueil, recherche, lecture, assistant, connexion, récupération et attente ; identité graphique et vocabulaire cohérents ; administration séparée | Une personne découvrant le système trouve une information, ouvre la source, pose une question et retrouve sa conversation sans aide technique |
| 7 — Comparaison et stabilité | Jeu plus exigeant, corrections indépendantes, vitesse et mémoire, requêtes simultanées, annulation, erreurs et reprise | Les erreurs connues ne sont pas masquées ; les guides restent consultables pendant un 27B ; une demande ne se perd pas ou ne semble pas bloquée sans explication |
| 8 — Réseau, téléphone et dictée | Accès LAN réel, adresse simple, pare-feu privé, HTTPS local et confiance des appareils, dictée avec voix humaine | Lecture et assistant fonctionnent sur ordinateur et téléphone ; micro accessible et transcription compréhensible sans Internet |
| 9 — Portage Windows | Reporter les nouveautés Linux dans le paquet Windows : dictée préchargée, profils, consignes/outils, recherche et récupération ; inventorier le PC de Marc | Installation sur Windows avec GPU reconnu, fichiers préparés, chemins corrects, accès Docker → Ollama natif, sans remplacer ses usages habituels |
| 10 — Démarrage et maintenance | Lanceur simple, démarrage après ouverture de session/redémarrage, diagnostic lisible, contrôle des versions/espace, arrêt et nettoyage ciblés | Marc retrouve le service après redémarrage sans terminal ni réparation manuelle de conteneurs ; panne expliquée avec une action utile |
| 11 — Livraison et restauration | Kit transférable compatible Podman Linux → Docker Windows, modèles/caches/ZIM, empreintes, secrets propres à Marc, sauvegarde cohérente et retour arrière | Installation et restauration dans une cible distincte sans téléchargement ; aucune copie brute du stockage interne Podman supposée portable |
| 12 — Recette finale et fiche utilisateur | Scénario guidé, aide courte, fiche imprimée d'adresse/accès/récupération, liste des limites connues | Tous les tests de livraison ci-dessous passent ; les réserves restantes sont acceptées et écrites |

Le lot 4 inclut le connecteur Kiwix dans la cible de cette première version,
car une encyclopédie disponible mais invisible à l'assistant laisserait un écart
important avec l'expérience attendue. Ce n'est pas un connecteur déjà livré.
Les premières illustrations peuvent être des liens vers leur page source ;
l'analyse visuelle automatique exhaustive n'est pas nécessaire au pilote.

Attention au réseau : `localhost` permet le micro sur le PC mais une adresse IP
LAN en HTTP n'offre généralement pas le contexte sécurisé exigé par le navigateur.
L'accès au micro sur téléphone doit donc être testé avec une solution HTTPS locale
et des certificats reconnus, sans dépendance au renouvellement Internet pour la
recette. [Référence navigateur](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

## Refonte : références consultées et direction proposée

Les changements de texte et de couleurs actuels ne constituent pas une conception
de produit complète. Préparer des maquettes des parcours avant de refaire le code,
puis les essayer avec des personnes qui ne connaissent pas le projet.

- [Readwise Reader](https://readwise.io/read) : référence pour une lecture confortable
  et une bibliothèque réunissant plusieurs formats, avec accès aux passages.
- [Linear](https://linear.app/) : référence de cohérence visuelle, de navigation
  stable et de présentation des états d'un travail ; adapter sa densité à des débutants.
- [GOV.UK Design System](https://design-system.service.gov.uk/) : référence pour
  des parcours et formulaires compréhensibles, accessibles et des erreurs utiles.
- [Principes de navigation Home Office](https://design.homeoffice.gov.uk/accessibility/page-structure/navigation) :
  proposer recherche et navigation, avec des repères qui restent cohérents.

Ce sont des inspirations de conception, pas de nouveaux services à installer.
Le DSFR a également été consulté, mais son périmètre est réservé aux services de
l'État : ne pas reprendre son identité ou le présenter comme le thème du produit.

Direction proposée pour SetupSurvie : une application de connaissances, avec
navigation stable **Accueil / Bibliothèque / Assistant**, recherche centrale,
résultats avec aperçu et provenance, lecteur conservant le retour aux résultats,
et action « Poser une question sur ce document ». Montrer les sources à côté de
la réponse, le mode choisi, l'attente et l'annulation. Intégrer la dictée dans ce
parcours. Thèmes, favoris et reprise de lecture à prioriser après les essais de
maquettes. Les commandes de maintenance restent hors du parcours des lecteurs.

## Ordre proposé

1. Fixer l'expérience du pilote, les parcours de connexion/récupération et les maquettes.
2. Réaliser comptes/récupération, contexte IA et outils locaux, guides et recherche.
3. Intégrer ces fonctions dans l'interface commune et le paquet Windows.
4. Préparer le kit, puis exécuter la recette Windows, LAN, hors ligne et restauration.

## Recette de livraison à Marc

- [ ] Installation ou restauration sur un Windows distinct, puis démarrage sans retéléchargement.
- [ ] Connexion conservée après fermeture/réouverture du navigateur et redémarrage ; expiration 30 jours vérifiée par un test adapté.
- [ ] Mot de passe perdu : récupération avec code ; code également perdu : secours local ; aucune conversation effacée.
- [ ] Compte lecteur : modèles/documents partagés accessibles, administration inaccessible, conversations séparées.
- [ ] Recherche d'un article et d'un passage de guide, lecture des illustrations, retour aux résultats, téléphone réel.
- [ ] Question française sur guide anglais, question sur Wikipédia via l'assistant, source ouvrable.
- [ ] Calcul vérifié, cas sans réponse, information manquante, document contradictoire, instruction malveillante dans une source.
- [ ] Trois modes, attente compréhensible, annulation et consultation de la bibliothèque pendant un calcul long.
- [ ] Dictée avec voix humaine sur PC et téléphone, autorisation refusée et silence correctement traités.
- [ ] Internet réellement coupé, LAN conservé : refaire lecture, recherche, IA, dictée et récupération.
- [ ] Redémarrage du PC puis reprise ; arrêt/reprise des services ; coupure d'un service avec message compréhensible.
- [ ] Sauvegarde restaurée sur une cible distincte avec comptes, historique, modèles et bibliothèque cohérents.

Pas requis avant ce premier pilote : vente, machine dédiée définitive, batterie,
routeur dédié, analyse visuelle de toute la bibliothèque, nombreux autres modèles,
traduction/indexation exhaustive de Wikipédia et worker des dossiers du soir.
Ces fonctions restent au référentiel du projet, sans bloquer ce premier appareil.
