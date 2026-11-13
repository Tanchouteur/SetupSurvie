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
| Gestion des collections | Depuis Données locales, bloc administrateur repliable ; aperçu par thème puis téléchargement explicite, sans nouvelle entrée dans le menu (12 novembre 2026) |
| Installation Windows | Depuis 0.1.20, [un seul lanceur](../installation/deux-etapes-windows.md) prépare le PC puis installe depuis Internet ou un kit ; les deux anciens restent utilisables. Diagnostic des composants et conflits avant copie, reprise explicite et raccourcis préservés ; installation complète sur Windows vierge encore à valider |
| Mise à jour Windows | Depuis 0.1.21, [raccourci Git fourni à l’installation](../exploitation/mises-a-jour-et-bibliotheque-pilote.md) : récupération de main dans un dépôt séparé, sauvegarde, paquet vérifié et retour arrière ; lanceur stable hors du logiciel remplacé |
| Prérequis du pilote Marc | Préparation initiale Windows / WSL 2 / pilotes / Python / Docker / Ollama avec Internet ; kit applicatif hors ligne ensuite, sans installateur système complet (12 novembre 2026) |
| Mode jeu | Respect du marqueur de pause ; reprise du moteur uniquement après levée explicite |
| Coupures du PC | Depuis 0.1.23, [écritures synchronisées, verrous libérés à l’arrêt et reprise explicite](../exploitation/coupures-et-redemarrage.md). Alimentation solaire susceptible de coupures, précisée par Louis le 13 novembre 2026 ; aucun arrêt propre de l’alimentation ni comportement physique du disque n’est validé par les tests de processus |
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
