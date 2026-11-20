# Choix et contraintes actuels

**Référence des décisions en vigueur — revue le 20 novembre 2026 (0.66.0).**
Les décisions sont datées, les plus récentes en premier. Une décision plus
récente l’emporte sur une plus ancienne du même sujet ; les remplacements sont
signalés. Les notes de chaque livraison sont dans les
[livraisons détaillées](../historique/livraisons.md) et les
[bilans datés](../essais/README.md). Les consignes permanentes pour les agents
(Git, versions, données privées, tests) sont dans [AGENTS.md](../../AGENTS.md).


## Mises à jour et copies suivies dans le portail — 20 novembre 2026

Louis demande de pouvoir lancer une mise à jour depuis la barre de navigation,
avec un avertissement d’indisponibilité. Il demande aussi de suivre la mise à
jour et la copie complète sur l’accueil, avec les informations des fenêtres de
script, et de voir au survol la date de la dernière vérification avec une
actualisation possible. La 0.69.0 garde les scripts existants comme moteur et
moyen de secours. Elle publie leur état dans `catalog/maintenance.json` et sert
une page temporaire pendant l’arrêt des conteneurs. Le lancement depuis le
portail est réservé au profil Famille et aux installations Windows.
Le rechargement à chaud des collections après suppression, évoqué le même jour,
n’est pas réalisé. Voir le [guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#depuis-le-portail-et-suivi-sur-laccueil--0690).

## Préparation de la bibliothèque — 20 novembre 2026

Louis demande que le classement soit lisible sur les résultats et dans le
lecteur, et que les préparations suivent les changements de la bibliothèque.
La 0.67.0 affiche les espaces et utilise le même classement pour une vidéo
dans la recherche et son lecteur. La file rapproche les états, la pause et
la reprise des préparations. Les téléchargements vérifiés déclenchent les
compléments textuels. Les ajouts ou remplacements de ZIM entraînent aussi
un examen vidéo dans le créneau d'indexation. Les guides et les fichiers
vidéo locaux sont surveillés. Voir le [guide des préparations](../utilisation/preparations-bibliotheque.md).

## Page dédiée pour organiser les collections — 20 novembre 2026

Louis juge inutilisables les deux panneaux de tri et d’index Wikipédia de
**Bibliothèque → Collections** (on ne comprenait ni quelle collection était
laquelle, ni l’effet des boutons). La 0.65.0 déplace le tri dans **Mon appareil →
Paramètres → Bibliothèque et préparations → Organiser les collections**, avec
trois choix (Fonds principal, Autre, Supprimer) ; les 0.65.1 et 0.65.2 regroupent
et replient les familles ; la 0.66.0 prépare et parallélise le classement du fonds
principal. Voir le [guide](../utilisation/classement-et-collections.md) et les
[préparations de la bibliothèque](../utilisation/preparations-bibliotheque.md).

## Interface unique — 19 novembre 2026

À la demande de Louis, la maquette fictive est retirée du paquet en 0.59.0, puis
l’interface « classique » en 0.63.0. `portal/index.html` est généré par
`scripts/build_portal.py` depuis `portal/interface/modele.html` ; `/classique/` et
`/nouveau/` ne sont plus que des redirections vers la racine qui conservent la
page demandée. Aucune donnée n’est migrée. Voir les
[anciennes adresses](../utilisation/portail.md#anciennes-adresses--0630).

## File d’attente commune des travaux — 18 novembre 2026

Le portail donne un point de suivi commun aux questions, traductions,
transcriptions, sous-titres, téléchargements YouTube et préparations de la
bibliothèque, avec ordre réglable des travaux en attente et erreurs visibles.
Décision et suites : [file d’attente des travaux](file-attente-travaux.md) ;
[guide](../utilisation/file-attente.md).

## Modèles et saisie de l’assistant — décision de Louis du 19 novembre 2026

Louis demande de retirer la dictée de la discussion, qu’il n’utilise pas, et
de pouvoir télécharger les modèles depuis l’interface. La 0.62.0 applique
ce choix au portail. Le profil Famille installe les modèles du catalogue des
modes de réponse depuis **Mon appareil → Paramètres → Assistant**. Le serveur utilise son
stockage Ollama existant. La reconnaissance vocale reste utilisée pour les
sous-titres des vidéos. Le lot avait d’abord été numéroté 0.61.0 dans la
PR 66. Le numéro 0.61.0 était déjà utilisé par le chantier « interface unique ».
La version 0.62.0 identifie la livraison des modèles et permet de l’installer
depuis une installation marquée 0.61.0. Voir le [guide d’utilisation](../utilisation/portail.md#télécharger-un-modèle-pour-lassistant).


## Traductions partielles publiées automatiquement — 19 novembre 2026

Louis valide l’assouplissement des contrôles ambigus, la conservation automatique
des références et une seule tentative de correction par passage avant de continuer.
Il demande qu’une traduction avec des passages manquants soit publiée automatiquement
dès que le traitement a parcouru le document. Le lecteur indique que la version est
partielle et renvoie à l’original. La reprise groupée complète la même version
partagée. Les contrôles bloquants de fidélité gardent leurs propositions refusées
dans le travail privé. Cette décision remplace l’exigence de résoudre tous les
refus avant la publication automatique. [Guide de traduction](../utilisation/documents-et-traduction.md)

## Classement des espaces documentaires — 19 novembre 2026

Louis demande de mesurer la qualité du tri avant et après une modification,
d'examiner les métadonnées des encyclopédies, de compter les vidéos dans la
recette et de vérifier le gain sur de nouveaux documents après réglage. La 0.57.0 utilise la structure des articles Wikipédia lorsque
disponible. Le [protocole et bilan Bazzite](../essais/mesurer-classement-documentaire.md)
trace les gains, les écarts et la vérification à poursuivre sur le fonds de Marc.

## Carte sur téléphone hors du réseau de la maison — 18 novembre 2026

Louis demande de pouvoir rouvrir la carte sur son téléphone après fermeture du
navigateur et départ de la maison. La 0.50.0 ajoute le téléchargement explicite
d’un fond par zone depuis le serveur en HTTPS. Le [guide des cartes](../utilisation/parametres-et-cartes.md#télécharger-une-zone-sur-le-téléphone)
décrit l’ouverture par favori et les données qui restent sur le serveur.

## Finition Veillée — 18 novembre 2026

Louis demande une jauge intégrée à la navigation, des actions lisibles, un
volet de recherche mieux cadré, des transitions et un guide pour les travaux
suivants. La 0.49.0 reprend ces points et place les options vidéo à côté
du lecteur sur grand écran lorsqu’il est ouvert directement. Voir le
[guide de design](../architecture/guide-design.md).

## Collections et lecteur vidéo — 18 novembre 2026

Louis demande de reprendre les titres de rubrique au défilement et de clarifier
la présentation des vidéos. La 0.48.0 intègre les titres à la mise en page
Veillée, pose la lecture au premier plan et rassemble le sous-titrage, son suivi
et la gestion de la vidéothèque dans leurs panneaux. Voir le
[guide vidéo](../utilisation/videos-locales.md#chercher-et-lire).

## Préférences de sous-titres vidéo — 18 novembre 2026

Louis demande de mémoriser la piste choisie et d’ajuster le réglage par défaut
à la langue parlée. Depuis la 0.47.0, les vidéos anglaises privilégient la piste
française puis anglaise. Les vidéos françaises s’ouvrent sans sous-titres.
Le choix manuel est mémorisé par vidéo, profil et navigateur. Voir le
[guide vidéo](../utilisation/videos-locales.md#chercher-et-lire).

## Sous-titres depuis le lecteur vidéo — 18 novembre 2026

Louis demande de lancer et suivre les sous-titres directement dans la vidéo.
La 0.45.0 ajoute au lecteur la transcription audio, la traduction française
et les commandes de suivi pour la vidéo ouverte. Les pistes terminées
rejoignent le menu du lecteur après leur indexation. Voir le
[guide vidéo](../utilisation/videos-locales.md#créer-traduire-et-suivre-les-sous-titres-dans-le-lecteur--0450).

## Refonte du design « Veillée » — 18 novembre 2026

Louis demande une refonte du design sans changement de fonctions, avec le champ
libre sur l’expérience tant que l’existant n’est pas dégradé. La 0.44.0 applique
une identité tirée du logo à tout le portail. Les règles sont dans
[composants et présentation](../architecture/composants-interface.md#direction-visuelle--veillée---0440).
Les choix de palette, de polices et l’accès rapide sont des propositions de l’agent,
à confirmer par Louis et par les retours de Marc.

## Fiabilité documentaire — 18 novembre 2026

À la suite de la première vague sur le R7, Louis demande de corriger les
problèmes reproduits. La 0.43.5 améliore la recherche sur les demandes
formulées en phrases et prépare des passages pour certaines demandes de
planning ou d’identification d’une œuvre. Le
[bilan du R7](../essais/2026-11-18-fiabilite-documentaire-r7.md#contre-épreuve-en-0435)
conserve les résultats avant et après.

## Démarrage du moteur avec SetupSurvie — 18 novembre 2026

Louis demande que l’assistant soit prêt lorsque SetupSurvie démarre avec le PC.
Depuis 0.43.1, les nouvelles installations Windows ne désactivent plus le moteur
et la mise à jour d’un démarrage Windows géré corrige l’ancien réglage automatique.
Sous Linux, le service automatique démarre aussi le moteur : un redémarrage réel
sur Bazzite l’a montré en ligne le 17 novembre 2026, sans génération de test.
Les pauses explicites, notamment le mode jeu, restent actives. Windows démarre à
l’ouverture de session si le démarrage automatique est activé ; la disponibilité
de l’IA dépend du démarrage réussi du moteur et de ses modèles. Essai Windows à
froid non réalisé.

## Installation Linux neuve — recette du 17 novembre 2026

Le parcours Docker dédié sur Bazzite est en service. Louis confirme de terminer
avec le fonds déjà présent : 110 ressources du catalogue hors Wikipédia anglais,
toutes vérifiées par taille/SHA-256, compléments et partiels conservés. Les
candidats internes 0.40.0–0.40.3, puis la livraison 0.41.0, corrigent démarrage autonome, réseau rootless, outil
cartographique, lecteur Python 3.15 et suivi de l’index. Le [bilan réel](../essais/2026-11-17-installation-neuve-bazzite.md) distingue les preuves acquises et les limites restantes. Aucun transfert entre SSD ni redémarrage physique n’est annoncé.

## Feuille de route V1 et installation neuve sur Bazzite — 17 novembre 2026

Louis demande un bilan général de ce qui doit ou peut être amélioré pour une V1,
des gros essais manquants, puis une installation Linux complète de zéro sur son
PC Bazzite (RTX 2060, deux SSD), un transfert d’un SSD à l’autre limité à
**300 Go** et un nettoyage ; pas de modification du code à ce stade. Il précise
que le bilan porte sur le projet en général, d’autres agents travaillant en
parallèle. La [feuille de route V1](feuille-de-route-v1.md) est une proposition
de l’agent à valider ; le [protocole Bazzite](../essais/plan-installation-neuve-et-transfert-bazzite.md)
liste les décisions préalables (dépassement temporaire du plafond de 600 Go
sur le SSD 4 To, sens du transfert, Docker dédié, créneaux IA). Cette demande
ouvre le chantier d’installation neuve et de transfert mis de côté plus tôt le
même jour ; aucun résultat n’est annoncé. Documentation seule, sans changement
de version logicielle.

Réponses de Louis le même jour : plafond du SSD 4 To porté à **900 Go** pendant
l’essai, installation sur le SSD système puis transfert vers le 4 To, Docker
dédié, fonds réduit ; pas de jeu prévu dans les jours à venir. **Principe
confirmé : SetupSurvie doit être très utile en cas d’effondrement total et l’on
doit pouvoir s’appuyer dessus.** Louis demande de commencer par une
[ingénierie de tests](../essais/ingenierie-de-tests.md) conduite par l’agent,
sans rien lancer encore. Un refus inutile y compte comme un échec ; une erreur
dangereuse sur un sujet critique bloque la campagne.

Compléments de Louis le même jour : règle validée — sans source précise,
l’assistant répond avec ses connaissances générales en le signalant, avec
prudence et clarification sur les gestes critiques ; **au moins 95 % des
réponses sans refus injustifié ni erreur grave**, « car ça peut sauver la vie » ;
coupure brutale autorisée sur le PC Bazzite ; essais chez Marc lancés par Louis
via TeamViewer avec mise à jour manuelle. Évolution future demandée : contexte
personnel de chaque foyer avec une trame (stock, adultes/enfants, compétences),
inscrite en IDEE-011. Toujours aucune exécution avant feu vert.

## Essais depuis Happier sur le PC Bazzite — 17 novembre 2026

Louis autorise un accès complet par SSH depuis le runner Coolify sur le LAN,
pour développer et tester sur son PC. Les alias `bazzite` (louis) et
`bazzite-root` (root), transferts et tunnels TCP/sockets Unix ont été qualifiés.
La [référence Nexus](https://github.com/Tanchouteur/Nexus/blob/main/infrastructure/runbooks/happier-bazzite.md)
documente configuration, essais et révocation. Cela ne valide pas le produit :
le laboratoire n'était pas monté et aucun LLM n'a été démarré. Les limites de
stockage, la pause d'inférence et les contrôles du laboratoire restent obligatoires.
Les assistants du produit ne reçoivent pas ces accès. Livraison de consignes et
documentation uniquement, sans changement de version logicielle.

## V1 Linux pour les proches — décision de Louis du 20 novembre 2026

La V1 cible Linux. SetupSurvie sera donné à des amis, qui achèteront leur
configuration matérielle. Ce cadrage remplace le projet de vente du PC
préinstallé pour la V1. Louis demande un bureau léger pour préserver la RAM
et la VRAM, ainsi que Firefox avec son traducteur et les langues utiles
téléchargées avant remise. Voir le [cadrage de référence](acces-simple-et-offre.md)
et la [feuille de route](feuille-de-route-v1.md).

## Offre de PC préinstallé — 16 novembre 2026

Louis précise que le code propre de SetupSurvie n'est pas publié en open source
et que l'offre visée est la **vente du PC avec SetupSurvie installé**. Le
[cadrage de référence](acces-simple-et-offre.md) distingue préparation avant
livraison et usage client. Les apports de NOMAD sont à apprécier selon leur gain
pour la machine livrée, sa fiabilité et son entretien. Les tarifs et modalités
d'assistance ne sont pas définis par cette décision ; le pilote reste à qualifier.

## Base conservée et apports de NOMAD — 16 novembre 2026

Louis retient **SetupSurvie comme base** et demande d'identifier les apports utiles
de NOMAD. L'[étude actuelle](apports-nomad.md) recommande de simplifier la
préparation existante, d'étudier un contrôle régulier des liens du catalogue et
de qualifier Kolibri pour les cours/exercices. Ce classement est une proposition
technique ; il ne lance ni développement ni installation et ne remplace pas les
deux objectifs ci-dessous. La comparaison d'octobre reste historique.

## Deux prochains objectifs — décision de Louis du 16 novembre 2026

**Statut : priorités à réaliser et à qualifier, sans validation annoncée par cette
note.** Louis fixe les deux prochains objectifs du projet :

1. **Améliorer réellement l’expérience utilisateur et simplifier l’ensemble du
   site, sans perdre de fonctionnalités.** Repenser les parcours, la navigation,
   les intitulés et la présentation des commandes, au-delà du seul aspect visuel.
   Les fonctions existantes doivent rester accessibles ; les options avancées
   peuvent être regroupées et dépliables. La [refonte de l’assistant en trois
   zones](conversations-trois-zones.md) s’inscrit dans cet objectif global. Vérifier
   les parcours sur ordinateur et téléphone, la conservation des données et
   travaux, ainsi que l’accès aux sources et aux fonctions de secours.
2. **Tester réellement la fiabilité de l’ensemble**, y compris la copie complète
   de l’installation d’un disque physique à un autre et sa restauration autonome
   hors ligne. Couvrir les fonctions, leur interaction, les erreurs, interruptions,
   reprises, mises à jour et sauvegardes, ainsi que la fidélité des réponses,
   traductions et synthèses sur des sources vérifiables. Appliquer le
   [protocole de secours](../exploitation/disque-de-secours-hors-ligne.md#10-recette-dacceptation) :
   vérifier le contenu copié puis restaurer sans Internet ni accès au disque
   source, retrouver les ressources et données personnelles et contrôler le
   fonctionnement après redémarrage et retrait du support de secours.

### Conduite autonome de la campagne de fiabilité

Louis prévoit de laisser GPT travailler de façon autonome pour préparer et
exécuter tous les tests nécessaires, corriger les défauts rencontrés et rejouer
les scénarios concernés. Cette note cadre la future campagne ; elle ne la lance
pas. L’agent doit établir une matrice de couverture à partir des fonctions et
procédures réellement présentes, puis consigner version, machine, supports,
conditions réseau, résultats, preuves et limites de chaque essai.

Les tests simulés préparent la campagne mais ne remplacent pas les essais réels.
Une absence de matériel, de disque distinct ou d’accès à une cible doit rester
signalée comme validation non exécutée. Les tests préservent les originaux et la
dernière sauvegarde saine, utilisent des cibles jetables ou dédiées et respectent
la pause d’inférence et les usages des PC. Les essais physiques et la recette
humaine du manuel restent identifiés séparément lorsqu’ils exigent une
intervention ; aucune réussite n’est déduite du seul déroulement automatique.

## Retour aux anciennes versions — décision de Louis du 17 novembre 2026

Louis retire la demande de préparer un retour aux anciennes versions pour ce
chantier d’interface. Ne plus consacrer de préparation supplémentaire à ce repli.
Les références déjà créées restent historiques ; cette décision ne modifie pas
les données ni les fonctions existantes de navigation.

## Suivi CI et maîtrise du coût — décision de Louis du 17 novembre 2026

Louis demande de confier le suivi de CI à un sous-agent **GPT Luna** lorsque
possible, pour économiser les crédits IA. Le suivi de la PR 22 est délégué à
ce modèle : observation du run existant, résultats et diagnostic ciblé d’échec.
Louis étend ensuite cette préférence aux tâches bien délimitées pour lesquelles
un petit sous-agent peut réduire le coût total, sans multiplier les agents
inutilement. L’agent principal vérifie les preuves et la qualité du travail,
conserve la revue finale et reprend les tâches qui dépassent les capacités du
sous-agent. La décision ne change pas les critères de validation et n’autorise
pas à ignorer un échec.

## Mesures visibles et conservation du modèle — décision de Louis du 17 novembre 2026

Louis demande aussi de reprendre la qualité visuelle générale, la cohérence de la
navigation des cartes et l'intégration des indicateurs de ressources. Ce
[chantier visuel](refonte-ux-evolutive.md#cohérence-et-qualité-visuelle-à-reprendre--demande-de-louis-du-17-novembre-2026) reste à concevoir et à réaliser.

Louis demande un indicateur compact dans la navbar PC pour le modèle réellement
chargé, la RAM et la VRAM, et le maintien de la navigation principale dans les
cartes. Les mesures détaillées doivent être accessibles directement ; un lien
« mémoire » ne doit pas conduire seulement au stockage. Il demande aussi une
lecture de traduction stable, plus large, structurée et dont la progression est
claire depuis la Bibliothèque. Ces évolutions sont implémentées en **0.39.0**.

Louis refuse le déchargement du modèle à l’expiration d’un délai d’inactivité.
La conservation demandée devient sans expiration ; arrêt explicite, mode jeu,
changement de modèle et essais froids volontairement lancés gardent leur rôle.
Le [guide des mesures](../utilisation/mesurer-assistant-et-memoire.md) précise la
portée, la prochaine demande et les événements qui peuvent perdre l’état du moteur.

Louis signale enfin qu’une demande explicite de vidéo renvoie un article puis
une absence non établie. Il demande un filtre vidéo dans la recherche et un
parcours équivalent pour l’assistant : réservé par Louis à un autre agent après ce signalement,
sans confondre vidéo absente, non examinée, non indexée et piste manquante.

> **Suites :** le filtre vidéo et l’outil `find_videos` de l’assistant sont livrés
> en 0.40.0 ([décision](videos-locales-et-recherche.md)) ; la refonte visuelle « Veillée »
> en 0.44.0 ([guide de design](../architecture/guide-design.md)).

## Décisions du 14 au 17 novembre 2026 sur la recherche et les réglages

Décisions prises pendant la fiabilisation de la recherche (lots 0.3.0 à 0.12.0)
et les intégrations suivantes. Elles restent en vigueur sauf mention contraire.

### Recherche : suite du 14 novembre 2026

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

### Comparatif de recherche 0.8.0 — 14 novembre 2026

Le [comparatif volontaire](../utilisation/comparer-recherche-ia.md) est retenu pour
mesurer reformulation bilingue et reclassement sur le modèle local. Les avis humains,
cas réservés, faux positifs, couverture et budget de délai conditionnent la décision.
L’aide reste désactivée dans la recherche ordinaire ; l’index sémantique est reporté
jusqu’au bénéfice établi par R2/R4 réel. Aucun nouveau modèle n’est imposé.

### Dossiers pratiques 0.9.0 — 14 novembre 2026

Six objectifs de lecture sont retenus dans Apprendre par thème. Les
[repères](../utilisation/dossiers-pratiques.md) sont ajoutés explicitement après
examen d’une source, avec localisation et révision ; les points non documentés
restent visibles. Une qualification automatique sur le titre seul est écartée.
L’enrichissement du fonds attend des lacunes confirmées et les droits examinés.

### Corrections prioritaires 0.9.1 — 14 novembre 2026

Les rapports réels ont montré des recherches partielles et des appels IA expirés.
Le budget choisi borne désormais toute la demande ; deux échecs arrêtent l’essai.
Les requêtes Kiwix sont bornées en commun, les erreurs ne déclenchent pas de
sous-requêtes en cascade et les replis sur un mot isolé sont filtrés. Les
[preuves et limites](../essais/2026-11-14-corrections-rapports-recherche.md) restent
distinctes d’une validation sur le fonds réel. Réorganisation des réglages reportée
après fiabilisation (IDEE-006), conformément à la demande de Louis.

### Contrôle de l’indexation 0.9.2 — 14 novembre 2026

La préparation seule par pip n’est plus assimilée à un lecteur vérifié : import
natif et SQLite sont contrôlés dans son environnement isolé. Un échec commun
arrête le travail avant les archives ; les erreurs individuelles restent distinctes.
Le [bilan](../essais/2026-11-14-indexation-isolee.md) conserve les essais Linux et
Windows isolés et la correction du lancement des processus. La cause réelle chez
Marc attend R1, sans nouveau corpus ajouté. La restauration de recherche déclenche
une seule requête après lecture du profil, avec repli public si ce dernier échoue.

### Conservation des index 0.9.3 — 14 novembre 2026

Sauvegarde, remplacement et retour arrière partagent les exclusions des écrivains
CLI/Web, y compris un processus d’extraction restant après son superviseur.
Les verrous OS ne sont pas restaurés comme des données ni supprimés pendant le
nettoyage. Les [preuves et limites](../essais/2026-11-14-index-sauvegarde-et-retour-arriere.md)
restent distinctes d’un essai du fonds de Marc ou d’une restauration physique complète.

### Rapports réels 0.9.3 et corrections 0.9.4

L’indexation réelle est terminée : 134 index natifs et un index local de 120 articles.
Les 31 recherches partielles sur 32 motivent la priorité entre langues, les replis
pratiques précoces, l’isolement des grosses archives et une phase bornée à douze
secondes. Les réponses des outils ne répètent plus le manifeste des 135 archives
dans le contexte du modèle. Les [corrections et leurs limites](../essais/2026-11-14-corrections-rapports-093.md)
restent distinctes d’une nouvelle mesure sur le fonds. La reformulation IA n’a pas
abouti dans les deux essais reçus ; aucun gain ni panne mémoire n’en est conclu.

### Recette d’usage 0.10.0

La [recette R7](../utilisation/verifier-usage-hors-ligne.md) réunit des lectures
sans IA et des observations humaines distinctes. Aucun résultat automatique
ne certifie la coupure Internet ou la qualité documentaire. Le contrôle ne
modifie pas la pause du moteur ; les mesures ne reprennent pas au rechargement.

### Paramètres par usage — 0.12.0

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

> **État actuel (vérifié le 20 novembre 2026 dans `portal/interface/settings-layout.js`) :**
> cinq rubriques — Profils et connexion, Bibliothèque et préparations, Assistant,
> Tests et diagnostics, Entretien et données. Voir le [guide des paramètres](../utilisation/parametres-et-appareil.md).

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

### Intégration du transfert SSD Windows — 17 novembre 2026

À la demande de Louis, la branche `codex/transfert-ssd-windows` est intégrée
avec les correctifs Windows et le suivi/pilotage local du transfert. La livraison
0.42.0 conserve la source et ne déplace pas le disque Docker en service. Voir
le [guide actuel](../exploitation/transfert-installation.md) et le
[bilan d’intégration](../essais/2026-11-17-integration-transfert-ssd-windows.md).
La copie en deux temps avec bascule courte reste une proposition non implémentée.

### Redémarrage Bazzite confirmé — 17 novembre 2026

Après le redémarrage physique effectué par Louis, les services Docker dédié et
SetupSurvie repartent automatiquement (+19 s et +35 s au relevé), sans commande
de démarrage de l’agent. Portail 0.41.0, recherche, lecture, secours et trois
routeurs sont vérifiés ; voir le [bilan réel](../essais/2026-11-17-installation-neuve-bazzite.md#redémarrage-physique-confirmé--17-novembre-2026).
Ce résultat complète la recette Linux ; téléphone réel, chargement de modèle,
transfert entre SSD et coupure électrique brutale restent distincts.
