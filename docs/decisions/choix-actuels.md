# Choix et contraintes actuels

Référence mise à jour le 12 novembre 2026 à partir des consignes de Louis et des
guides du pilote. L’[historique des échanges](questions-et-decisions.md) reste
conservé ; ses premières hypothèses matérielles et fonctionnelles ne priment pas
sur les précisions ci-dessous.

| Sujet | Choix retenu ou contrainte |
| --- | --- |
| Première étape | Pilote accompagné chez Marc ; recueillir les retours avant de considérer l’offre commerciale validée |
| Usages | Bibliothèque familiale, assistant local, enseignement et préparation aux services dégradés ; aucun sinistre présumé |
| PC de Louis | Linux Bazzite, Ryzen 9, RTX 2060 **6 Go**, 32 Go RAM ; laboratoire de développement |
| PC de Marc | Windows, RTX 5060 **8 Go**, **32 Go RAM** ; préserver ses usages habituels |
| Budget documentaire | **Aucun plafond logiciel chez Marc** ; laboratoire de Louis limité à 500 Go décimaux hors modèles et caches. Marc vise le fonds utile complet, préparé directement chez lui si nécessaire (Louis, 12 novembre 2026) |
| Stockage du laboratoire | SSD de 4 To ; image de 590 milliards d’octets, sous le plafond global de **600 Go**, avec au moins 15 Go libres |
| Accès local | Nom demandé **survie.local**, accès par IP et QR code maintenus ; mDNS à tester sur les clients |
| Interfaces | Portail et Open WebUI conservés ; mêmes comptes, historiques distincts |
| IA | Trois modes conseillés et autres modèles pour essais ; aucun gagnant désigné sur la seule taille |
| Fiabilité des réponses | Depuis 0.1.18, [dates distinctes, citations lues, faits et déductions, contradictions et incertitude](../utilisation/sources-et-fiabilite.md) ; consignes renforcées et métadonnées conservées, respect par les modèles réels encore à évaluer |
| Savoirs durables | [Référence unique des besoins de Marc](../bibliotheque/savoirs-durables.md) : principes, mesures, fabrication, contrôle, entretien et transmission ; parcours et thèmes intégrés en 0.1.19, couverture documentaire à examiner |
| Gestion des collections | Depuis 0.1.32, **Bibliothèque → Collections** ouvre les contenus ; **Mon appareil → Téléchargements** regroupe préparation et suivi. L’interface classique conserve Données locales. [Guide actuel](../utilisation/nouvelle-interface.md), organisation validée par Louis le 13 novembre |
| Installation Windows | Depuis 0.1.20, [un seul lanceur](../installation/deux-etapes-windows.md) prépare le PC puis installe depuis Internet ou un kit ; les deux anciens restent utilisables. Diagnostic des composants et conflits avant copie, reprise explicite et raccourcis préservés ; installation complète sur Windows vierge encore à valider |
| Mise à jour Windows | Depuis 0.1.21, [raccourci Git fourni à l’installation](../exploitation/mises-a-jour-et-bibliotheque-pilote.md) : récupération de main dans un dépôt séparé, sauvegarde, paquet vérifié et retour arrière ; lanceur stable hors du logiciel remplacé |
| Prérequis du pilote Marc | Préparation initiale Windows / WSL 2 / pilotes / Python / Docker / Ollama avec Internet ; kit applicatif hors ligne ensuite, sans installateur système complet (12 novembre 2026) |
| Mode jeu | Respect du marqueur de pause ; reprise du moteur uniquement après levée explicite |
| Coupures du PC | Depuis 0.1.23, [écritures synchronisées, verrous libérés à l’arrêt et reprise explicite](../exploitation/coupures-et-redemarrage.md). Alimentation solaire susceptible de coupures, précisée par Louis le 13 novembre 2026 ; aucun arrêt propre de l’alimentation ni comportement physique du disque n’est validé par les tests de processus |
| Disque de secours complet | Besoin exprimé par Louis le 13 novembre 2026 : copie complète sur un autre disque physique, réinstallation Windows/Linux sans Internet ni disque source, documentation humaine autonome. [Protocole cible](../exploitation/disque-de-secours-hors-ligne.md) ; installateur complet et compatibilité entre OS à développer et qualifier |
| Sauvegarde et diagnostic | Depuis 0.1.22, pause du moteur et registre documentaire sauvegardés ; préparations concurrentes refusées. Diagnostic documentaire possible en pause, test IA refusé jusqu’à levée explicite. Voir le [guide de restauration](../installation/pilote-marc.md#sauvegarder-et-restaurer) |
| Confidentialité | Comptes, conversations, clés, modèles et gros contenus hors Git ; préservation des données lors des opérations |

Les guides de l’[installation](../installation/README.md), de
l’[exploitation](../exploitation/README.md) et l’[architecture](../architecture/README.md)
décrivent l’application de ces choix. Les pistes d’offre et de routeur dédié
restent des hypothèses dans [Connexion simple et direction du produit](acces-simple-et-offre.md).

Les [contrôles Windows datés](../essais/2026-11-12-installateur-windows-simple.md) sont acquis dans leur périmètre.
Restent à évaluer : installation complète sur Windows vierge, fonctionnement hors ligne après
redémarrage, restauration chez Marc, Safari iPhone, dictée humaine, résolution du
nom, qualité des modèles et couverture documentaire pratique. Les droits de
redistribution commerciale restent à examiner par ressource. Les résultats Linux
ne prédisent pas les performances Windows.

Toute nouvelle décision doit préciser son origine, sa date, sa conséquence sur
les guides concernés et les validations encore nécessaires.

Depuis le pilote 0.1.10, les lieux communs et commandes de gestion sont regroupés dans Paramètres. Le domicile est distinct du départ actuel ; les adresses locales sont recherchées dans les zones préparées ou choisies manuellement. Voir le [guide](../utilisation/parametres-et-cartes.md).

Le 12 novembre 2026, Louis demande la conservation du document associé et une traduction progressive. Depuis 0.1.16, ce traitement privé dispose d’une progression, de plages PDF, d’une pause/reprise et d’un export texte. L’original est conservé ; les figures et la mise en page ne sont pas traduites. Voir le [guide actuel](../utilisation/documents-et-traduction.md). Les essais réels des modèles restent distincts des tests simulés. La branche `main` reste la référence unique à maintenir ; les branches de travail intégrées créées pour ces livraisons sont temporaires.

Le 13 novembre 2026, Louis demande le partage des traductions terminées dans les
documents locaux, les favoris et une meilleure isolation des pannes. Le pilote
0.1.25 publie les nouvelles traductions en HTML marqué IA non vérifiée, conserve
les anciennes privées jusqu’à action explicite et ajoute des favoris personnels
recherchables. Le lecteur PDF dédié et l’accès statique de secours réduisent la
dépendance à l’API. Le [guide actuel](../utilisation/documents-et-traduction.md)
précise les replis et les limites ; cette isolation ne couvre pas une panne du
disque ou du serveur web.


Le 13 novembre 2026, Marc demande le miroir le plus rapide et des transferts
simultanés. La 0.1.26 mesure les miroirs officiels Kiwix avec taille et SHA-256
figés, reprend les partiels sans les tronquer lors du changement de miroir et
utilise deux fichiers simultanés (un à trois en ligne de commande). Voir le
[guide d’exploitation](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#miroirs-et-transferts-simultanés-depuis-0126).
Le débit dépend du serveur et de la connexion ; les reçus, la capacité disque et
la vérification intégrale restent protégés.


Le 13 novembre 2026, Marc autorise la reprise Windows de son plan documentaire
sans démarrage IA et sans interrompre le transfert actif. La 0.1.27 prépare une
tâche limitée, vérifiée par un test HTTPS sous le compte cible, et conserve une
pause volontaire. Le mode `inference_autostart: false` laisse le moteur sur
commande explicite. Les modifications de pare-feu et le créneau Windows Update
18 h–midi sont propres à cette activation autorisée. Voir le
[guide de reprise Windows](../exploitation/coupures-et-redemarrage.md#reprise-automatique-de-la-bibliothèque-sous-windows--0127).

Le 13 novembre 2026, Louis demande une traduction plus exploitable. En 0.1.28,
le moteur existant est conservé avec contrôle local des nombres/unités, blocage
des anomalies fortes et avertissements de complétude. La comparaison source/texte
reste privée. Les anciens travaux ne sont pas déclarés contrôlés. Une comparaison
avec un moteur spécialisé et une évaluation bilingue sur documents réels restent
à réaliser avant de choisir un nouveau moteur ; aucun gain de fidélité des modèles
n’est affirmé sur la seule base des tests simulés.

Le 13 novembre 2026, Louis demande de supprimer les mots de passe et codes de
secours, pour ne pas bloquer l’usage en urgence, tout en gardant des profils.
Depuis 0.1.29, Famille fonctionne immédiatement ; les anciens identifiants et
historiques restent conservés et les profils sont librement sélectionnables sur
le réseau. Les profils ne garantissent pas la confidentialité entre utilisateurs.
Le [guide actuel](../utilisation/profils-locaux.md) remplace les anciennes procédures
de connexion du pilote. Les deux accès secondaires du menu sont décrits et séparés.


Marc demande le 13 novembre 2026 le démarrage automatique du site et l’intégration
à l’installateur après un redémarrage Windows. Depuis 0.1.30, le choix de démarrage
par défaut prépare deux tâches utilisateur : services web sans IA et reprise du
dernier plan documentaire explicitement autorisé. Les chemins d’outils sont
persistés et aucun fichier temporaire d’installation Docker n’est requis. La
bibliothèque avant ouverture de session reste une option indépendante. Voir le
[guide Windows](../installation/deux-etapes-windows.md#démarrage-automatique-windows-depuis-0130).

La même livraison évite le choix implicite « PC seulement » : un unique réseau
privé est proposé par défaut, LOCAL reste explicite, et la version répondant sur
l’IPv4 locale est contrôlée. Les règles Ollama publiques sont revues uniquement
pour l’exécutable installé. La validation depuis le serveur reste distincte d’un
vrai essai depuis un téléphone.

Le 13 novembre 2026, Louis valide la présentation PC et demande la mise en place
normale sur Windows/Linux, son téléchargement étant terminé. Depuis 0.1.32,
l’entrée principale utilise la nouvelle organisation ; la classique reste
accessible sans retour de base et la maquette demeure fictive. Les validations
simulées et recettes physiques restent distinguées dans le [bilan](../essais/2026-11-13-interface-fonctionnelle.md).

Le 14 novembre 2026, Louis demande une conversation plus confortable, le retrait
de **Faire un retour** et des boutons de retour classique. Depuis 0.1.35,
l’historique s’ouvre par **Conversations**, l’archive `/classique/` est conservée
sans lien dans les menus, et l’accueil demande **Qu’avez-vous envie d’apprendre ?**.
La recherche Kiwix isole les échecs et expose ses limites au portail et à l’assistant ;
aucune absence de source sur le feu chez Marc n’est déduite d’un test simulé.

Le 14 novembre 2026, le [retour d’expérience de Marc](../essais/2026-11-14-retour-experience-marc.md)
rapporté par Louis place la pertinence de la recherche au premier rang : retrouver
les savoir-faire réellement présents avant de conclure à leur absence ou d’ajouter
des volumes. Le regroupement lisible des collections, la compréhension de Parcours,
le français pour pages/vidéos et le délai de l’assistant font partie du besoin.
Les solutions proposées dans ce compte rendu restent à implémenter et à mesurer.
L’espace Maison de Solliès-Ville est une [idée reportée](boite-a-idees.md).

Le chantier de [fiabilisation du cœur documentaire](fiabilisation-recherche-et-contenus.md)
est demandé par Louis le 14 novembre. La 0.1.36 en implémente un premier lot :
classement commun, filtres, préparation de sources, contexte, regroupements et
recette depuis le site. La bibliothèque réelle et les modèles de Marc restent
à qualifier ; sous-titres, traduction de lecture généralisée et profondeur des
procédures demeurent suivis explicitement, sans réalisation implicite.

## Recherche : suite du 14 novembre 2026

Le [plan actuel](plan-ameliorations-marc.md) retient deux espaces dans un seul produit, indexation complémentaire des ZIM non recherchables, priorité aux savoir-faire et usage parallèle du CPU. La 0.3.0 en livre une première étape, avec contexte réglable par modèle. Les limites et essais manquants sont au [bilan](../essais/2026-11-14-recherche-index-et-espaces.md).

La 0.4.0 ajoute l’[indexation après publication vérifiée](../utilisation/indexation-archives.md),
avec file persistante, créneau horaire et réglage des ressources. Le catalogue
Kiwix est partagé brièvement entre les recherches ; un instantané ancien est
daté et signalé. Le diagnostic depuis le site distingue disponibilité, index et
résultats, sans conclure à l’absence d’un document sur une recherche partielle.
La capture suivante de Louis retrouve des sources pertinentes avec le filtre ;
elle ne prouve pas la cause de l’incident précédent. La recette sur le fonds réel
reste distincte des [contrôles de développement](../essais/2026-11-14-indexation-automatique-et-diagnostic.md).
