# Choix et contraintes actuels

La 0.22.0 ajoute un [diagnostic commun des lenteurs](../exploitation/diagnostic-complet-performances.md) :
recherches répétées, rédaction seule, recherche/lecture/réponse et documents déjà
sélectionnés, avec compteurs natifs du serveur. Le cache n’est pas vidé, le modèle
n’est pas déchargé et les réglages ne sont pas changés. Les constats restent
distincts des causes possibles et des mesures manquantes. Les demandes de synthèse
courte avec « documents de la bibliothèque » conservent leur sujet de recherche.

La 0.21.0 ajoute la [lecture française depuis l’original](../utilisation/documents-et-traduction.md#lire-une-version-française-déjà-terminée--0210),
sans inférence pour ouvrir une traduction publiée. Les versions anciennes ou dont
la correspondance est inconnue restent à comparer ; aucune traduction d’image
ni relecture humaine du sens n’est déduite de cette fonction.

La 0.20.0 ajoute la [relecture des conditions de départ et des relances](../utilisation/sources-et-fiabilite.md#reprendre-une-discussion-et-vérifier-les-conditions-de-départ--0200).
Les compléments sont des extraits exacts sélectionnés, sans réécriture de faits.
Une commande JSON décrite sans exécution reçoit une reprise bornée, puis une erreur
explicite si nécessaire. La validation réelle reste distincte d’un statut terminé.

La 0.16.0 prépare un [dossier de plusieurs sources](../utilisation/synthese-documentaire.md),
avec passages liés au sujet, budget partagé avec le modèle et arrêt des boucles
sans nouvelle lecture. Les essais réels R7 distinguent l’accès aux faits, la
syntaxe des références et la fidélité de la synthèse. Une liaison structurée ajoute
les références sans réécrire les faits ; elle ne certifie pas leur véracité.
Les profils conseillés restent inchangés. Le [bilan](../essais/2026-11-15-synthese-multi-sources-et-essais-reels.md)
conserve aussi les approches essayées puis abandonnées. La sélection manuelle multiple est ajoutée en 0.17.0 ;
la 0.18.0 ajoute les longues lectures avec notes et reprise explicite.
La 0.19.0 ajoute les [illustrations originales](../utilisation/illustrations-et-references.md),
sélectionnées selon le texte et les légendes. Vision et fidélité sur de vrais livres
restent à qualifier.

Le R2 réel 0.15.0 reçu ensuite annonce **32 recherches complètes**, médiane de fin
2,11 s avec cache déjà largement réutilisé, sans avis humain. Les captures
d’assistant montrent encore zéro source consultée. La 0.15.1 corrige un défaut
reproduit de préparation des demandes de synthèse ; la priorité devient
l’[utilité documentaire de l’assistant](assistant-recherche-et-synthese.md), avec
multi-source et boucle d’outils bornée à développer. Ni achat GPU ni changement
de profil n’est décidé sur la seule base des captures. Voir le
[bilan](../essais/2026-11-15-rapport-0150-et-requetes-synthese.md).

La 0.15.0 conserve un [suivi documentaire indépendant du modèle](../essais/2026-11-15-suivi-documentaire-assistant.md) :
recherches et lectures observées, limites et liens vers les documents consultés
même sans citation. Le texte du modèle reste distinct et peut encore être faux.
Les anciennes conversations ne reçoivent pas d’observations inventées ; la table
optionnelle préserve le schéma compatible 1. La recette réelle R4 reste nécessaire.

La 0.14.3 corrige l’ordre des titres de tâche face aux questions périphériques et
préserve la correspondance exacte des titres avec mots de liaison. Les sources
restent accessibles et non certifiées ; le [bilan](../essais/2026-11-15-questions-peripheriques-et-titres-exacts.md)
distingue les titres réellement observés des extraits et archives de reproduction.

La 0.14.2 adapte le plafond des reformulations aux lots du flux long : un document
manqué avec 28 appels principaux et seulement quatre variantes est retrouvé dans
la [reproduction](../essais/2026-11-15-budget-reformulations.md). La concurrence et
les 60 secondes sont conservées ; le JSON court et l’assistant gardent leurs
limites précédentes. Davantage de couverture peut prolonger la durée finale.

La 0.14.1 réduit le retraitement des résultats progressifs et mesure séparément
sélection et appels natifs, sans changer score ni budgets. Le
[R2 réel 0.14.0](../essais/2026-11-15-rapport-0140-et-traitement-progressif.md)
confirme des premiers documents en médiane à 311 ms, mais une fin à 36,24 s et
des reformulations limitées. Aucun CPU ou HDD saturé n’est établi par ce rapport.
La correction du traitement est reproduite sur fixtures ; son gain Windows et
les avis humains restent à vérifier. Le matériel peut évoluer après mesure.

La 0.14.0 intègre deux outils volontaires en lecture seule :
[inventaire des vidéos](../utilisation/inventaire-videos.md) et
[diagnostic Kiwix](../exploitation/diagnostic-performances-kiwix.md).
L’inventaire ne crée ni sous-titres ni index vidéo ; les validations réelles
et la suite transcription/traduction restent distinctes.


Complément 0.13.0 : [recherche progressive et cache reconstructible](../exploitation/cache-et-recherche-progressive.md).
Louis accepte davantage d’attente si les documents arrivent progressivement ;
2 Go est un exemple de cache ajustable et le matériel pourra évoluer après mesure.
La recherche générale reste centrale ; les six dossiers sont des aides facultatives.
La 0.13.1 corrige la priorité des titres correspondant à une tâche face aux
mentions dans des textes généraux, avec distinction des questions « pourquoi ».
Le classement ne déclare pas automatiquement une procédure qualifiée.

Les [vidéos locales 480p](videos-locales-et-recherche.md) sont à intégrer, avec
transcriptions horodatées et contrôle français par média ; réalisation prévue.

Le [rapport réel 0.10.0](../essais/2026-11-14-rapport-recherche-0100.md) conserve
31 recherches partielles sur 32 et une médiane de 12,3 s. La correction 0.11.1
traite les index natifs aux langues incompatibles et enrichit le diagnostic
explicite, sans relever encore les budgets. Le [prompt des paramètres](prompt-refonte-parametres.md)
cadre le chantier parallèle demandé ensuite par Louis, distinct de la recherche.

Référence mise à jour le 14 novembre 2026 à partir des consignes de Louis et des
guides du pilote. L’[historique des échanges](questions-et-decisions.md) reste
conservé ; ses premières hypothèses matérielles et fonctionnelles ne priment pas
sur les précisions ci-dessous.

| Sujet | Choix retenu ou contrainte |
| --- | --- |
| Première étape | Pilote accompagné chez Marc ; recueillir les retours avant de considérer l’offre commerciale validée |
| Usages | Bibliothèque familiale, assistant local, enseignement et préparation aux services dégradés ; aucun sinistre présumé |
| PC de Louis | Linux Bazzite, Ryzen 9, RTX 2060 **6 Go**, 32 Go RAM ; laboratoire de développement |
| PC de Marc | Windows, RTX 5060 Ti **8 Go**, **32 Go RAM** ; GPU détecté dans les [rapports du 14 novembre](../essais/2026-11-14-rapports-recherche-093.md), auparavant noté RTX 5060 ; préserver ses usages habituels |
| Budget documentaire | **Aucun plafond logiciel chez Marc** ; laboratoire de Louis limité à 500 Go décimaux hors modèles et caches. Marc vise le fonds utile complet, préparé directement chez lui si nécessaire (Louis, 12 novembre 2026) |
| Stockage du laboratoire | SSD de 4 To ; image de 590 milliards d’octets, sous le plafond global de **600 Go**, avec au moins 15 Go libres |
| Accès local | Nom demandé **survie.local**, accès par IP et QR code maintenus ; mDNS à tester sur les clients |
| Interfaces | Portail et Open WebUI conservés ; mêmes comptes, historiques distincts |
| IA | Trois modes conseillés et autres modèles pour essais ; aucun gagnant désigné sur la seule taille |
| Fiabilité des réponses | Depuis 0.1.18, [dates distinctes, citations lues, faits et déductions, contradictions et incertitude](../utilisation/sources-et-fiabilite.md) ; consignes renforcées et métadonnées conservées, respect par les modèles réels encore à évaluer |
| Savoirs durables | [Référence unique des besoins de Marc](../bibliotheque/savoirs-durables.md) : principes, mesures, fabrication, contrôle, entretien et transmission ; parcours et thèmes intégrés en 0.1.19, couverture documentaire à examiner |
| Gestion des collections | Depuis 0.1.32, **Bibliothèque → Collections** ouvre les contenus ; **Mon appareil → Paramètres → Bibliothèque et préparations** donne accès aux téléchargements et au stockage depuis 0.12.0 ; **Travaux en cours** garde le suivi. L’interface classique conserve Données locales. [Guide actuel](../utilisation/nouvelle-interface.md), organisation validée par Louis le 13 novembre |
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

La 0.5.0 étend la référence à 32 demandes et sépare la relecture humaine de la
mesure automatique. Le contrôle court reste disponible. Les redirections d’articles
locaux sont prises en charge et l’original reste proposé en cas d’échec d’aperçu.
Le [bilan](../essais/2026-11-14-reference-recherche-et-lecture.md) distingue le défaut
reproduit des articles indisponibles rapportés par Marc sans leur adresse précise.

La 0.6.0 rend le classement et les noms [corrigibles depuis Famille](../utilisation/classement-et-collections.md),
avec deux espaces possibles, type inconnu par défaut et état d’examen humain.
Les fichiers restent en un exemplaire, sans modification des ZIM. Les corrections
sont liées à la révision locale et exportables sans les textes. La relecture réelle
du fonds, de ses titres et de ses procédures reste nécessaire ; livrer l’outil
ne qualifie pas automatiquement toute la bibliothèque.

La 0.7.0 ajoute les [rapports de délais et l’essai mémoire volontaire](../utilisation/mesurer-assistant-et-memoire.md).
Le plus grand palier terminé avec les marges du scénario peut être proposé, puis
appliqué explicitement ; aucun remplissage systématique de RAM ni reprise du mode
jeu. La lecture associée préparée par le portail est réutilisée. Les mesures et
budgets sont testés sur HTTP simulé ; la vitesse, le contexte stable et la qualité
des modèles chez Marc attendent toujours R4 réel.

## Comparatif de recherche 0.8.0 — 14 novembre 2026

Le [comparatif volontaire](../utilisation/comparer-recherche-ia.md) est retenu pour
mesurer reformulation bilingue et reclassement sur le modèle local. Les avis humains,
cas réservés, faux positifs, couverture et budget de délai conditionnent la décision.
L’aide reste désactivée dans la recherche ordinaire ; l’index sémantique est reporté
jusqu’au bénéfice établi par R2/R4 réel. Aucun nouveau modèle n’est imposé.

## Dossiers pratiques 0.9.0 — 14 novembre 2026

Six objectifs de lecture sont retenus dans Apprendre par thème. Les
[repères](../utilisation/dossiers-pratiques.md) sont ajoutés explicitement après
examen d’une source, avec localisation et révision ; les points non documentés
restent visibles. Une qualification automatique sur le titre seul est écartée.
L’enrichissement du fonds attend des lacunes confirmées et les droits examinés.

## Corrections prioritaires 0.9.1 — 14 novembre 2026

Les rapports réels ont montré des recherches partielles et des appels IA expirés.
Le budget choisi borne désormais toute la demande ; deux échecs arrêtent l’essai.
Les requêtes Kiwix sont bornées en commun, les erreurs ne déclenchent pas de
sous-requêtes en cascade et les replis sur un mot isolé sont filtrés. Les
[preuves et limites](../essais/2026-11-14-corrections-rapports-recherche.md) restent
distinctes d’une validation sur le fonds réel. Réorganisation des réglages reportée
après fiabilisation (IDEE-006), conformément à la demande de Louis.

## Contrôle de l’indexation 0.9.2 — 14 novembre 2026

La préparation seule par pip n’est plus assimilée à un lecteur vérifié : import
natif et SQLite sont contrôlés dans son environnement isolé. Un échec commun
arrête le travail avant les archives ; les erreurs individuelles restent distinctes.
Le [bilan](../essais/2026-11-14-indexation-isolee.md) conserve les essais Linux et
Windows isolés et la correction du lancement des processus. La cause réelle chez
Marc attend R1, sans nouveau corpus ajouté. La restauration de recherche déclenche
une seule requête après lecture du profil, avec repli public si ce dernier échoue.

## Conservation des index 0.9.3 — 14 novembre 2026

Sauvegarde, remplacement et retour arrière partagent les exclusions des écrivains
CLI/Web, y compris un processus d’extraction restant après son superviseur.
Les verrous OS ne sont pas restaurés comme des données ni supprimés pendant le
nettoyage. Les [preuves et limites](../essais/2026-11-14-index-sauvegarde-et-retour-arriere.md)
restent distinctes d’un essai du fonds de Marc ou d’une restauration physique complète.

## Rapports réels 0.9.3 et corrections 0.9.4

L’indexation réelle est terminée : 134 index natifs et un index local de 120 articles.
Les 31 recherches partielles sur 32 motivent la priorité entre langues, les replis
pratiques précoces, l’isolement des grosses archives et une phase bornée à douze
secondes. Les réponses des outils ne répètent plus le manifeste des 135 archives
dans le contexte du modèle. Les [corrections et leurs limites](../essais/2026-11-14-corrections-rapports-093.md)
restent distinctes d’une nouvelle mesure sur le fonds. La reformulation IA n’a pas
abouti dans les deux essais reçus ; aucun gain ni panne mémoire n’en est conclu.

## Recette d’usage 0.10.0

La [recette R7](../utilisation/verifier-usage-hors-ligne.md) réunit des lectures
sans IA et des observations humaines distinctes. Aucun résultat automatique
ne certifie la coupure Internet ou la qualité documentaire. Le contrôle ne
modifie pas la pause du moteur ; les mesures ne reprennent pas au rechargement.

## Paramètres par usage — 0.12.0

La réorganisation demandée par Louis conserve les commandes dans quatre rubriques :
profils/connexion, bibliothèque/préparations, assistant, entretien/diagnostics.
Le suivi reste indépendant dans Mon appareil ; les options techniques sont
secondaires et les commandes d’arrêt restent accessibles sur téléphone.
La [correspondance exhaustive](../utilisation/parametres-et-appareil.md) décrit
les déplacements, sans suppression de fonctionnalité ni migration des données.
Les moteurs et cartes restent ceux de main, avec la recherche 0.11.1 intégrée avant
l’UX. Les [essais](../essais/2026-11-14-parametres-ux.md) distinguent fixtures et
validation physique. Un écran unique de boutons et les duplications de contrôles
ont été écartés ; les nœuds existants sont déplacés pour conserver leurs événements.

- **Reprise après changement de modèle (0.15.1)** : préparation explicite quand
  un autre modèle est chargé, une seule récupération avant toute sortie, état
  lisible et mesures exportables. Pas de changement silencieux du modèle/contexte,
  pas de levée de pause. La cause et le résultat sur le PC Windows restent à
  confirmer avec les mesures réelles ; voir le [guide assistant](../utilisation/mesurer-assistant-et-memoire.md).


Le guidage pratique 0.19.1 couvre aussi les questions ordinaires de procédure et
les dimensions, avec lecture effective des résultats et pages PDF groupées.
Le [cas réel Baofeng](../essais/2026-11-15-notices-et-guidage-pratique.md) reste une
recette parmi d’autres ; aucune commande d’appareil n’est codée dans le moteur.
L’objectif de fidélité et les essais sur des besoins variés restent ouverts.
