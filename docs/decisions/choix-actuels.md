# Choix et contraintes actuels

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
[composants et présentation](../architecture/composants-interface.md#direction-visuelle--veillée--0440).
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

## Livraisons disponibles

La **0.58.0** met les commandes et la progression de traduction au-dessus
du fil, et affiche les passages traduits dans la discussion dès qu’ils sont
disponibles. Évolution fonctionnelle compatible (`y`).
[Décision de Louis du 19 novembre](conversations-trois-zones.md#traduction-dans-le-fil--décision-du-19-novembre-2026).

Le **19 novembre 2026**, Louis demande que la première installation traite la
sélection YouTube maintenue dans le dépôt et indexe les vidéos des encyclopédies.
La **0.54.0** soumet la liste YouTube en ligne au traitement existant, y compris
la transcription et la traduction lorsque nécessaires, et programme l’inventaire
des vidéos ZIM aussi depuis un kit hors ligne. La sélection initiale reste à
renseigner. Nouvelle fonctionnalité compatible (`y`).
[Guide d’installation](../installation/README.md#préparer-les-vidéos-à-la-première-installation).


La **0.43.6** corrige le faux message « Suivi momentanément indisponible » : un ancien
transfert terminé qui désigne un disque précédent n’est plus pris pour une activité
inconnue. Le suivi affiche aussi les téléchargements YouTube, et leur liste rejoint
**Paramètres → Bibliothèque et préparations**, à la demande de Louis du 18 novembre 2026.
Testé par fixtures et navigateur ; cause non confirmée directement sur le PC de Marc.
Correction compatible (`z`).

La **0.43.4** corrige les demandes de vidéos après un essai réel sur le R7 : lecture
préalable des sous-titres, questions longues, liens mal formés ou perdus. Gemma et
Llama réussissent la recette sur vidéos fictives ; GPT-OSS et le PC de Marc restent à
essayer. Voir le [bilan](../essais/2026-11-18-demandes-videos-modele-reel.md). Elle fiabilise
aussi le téléchargement après trois vraies vidéos sur Bazzite : H.264 prioritaire et vidéo
conservée si ses sous-titres sont refusés ; Windows est contrôlé en CI avec les vrais outils,
sans YouTube. Voir l’[essai](../essais/2026-11-18-youtube-reel-bazzite-windows.md).
Correction compatible (`z`), données et composants tiers inchangés.

La **0.43.0** ajoute dans Collections, pour le profil Famille, le bouton demandé par
Louis le 17 novembre 2026 : liste YouTube collée ou déposée, vérification, suivi,
pause et reprise. Le contrôleur de l’hôte télécharge ; le service du site garde
`library/video` en lecture seule. Testé avec un contrôleur simulé, sans vidéo réelle
ni essai Windows. Voir le [guide](../utilisation/telecharger-videos-youtube.md) et le
[bilan](../essais/2026-11-18-bouton-liste-youtube.md). Nouvelle fonctionnalité
compatible (`y`), données et composants tiers inchangés.

La **0.42.0** inclut les outils du téléchargement YouTube dans l’installation, à
la demande de Louis du 17 novembre 2026 (« on ne doit rien avoir à faire », y
compris lors d’une copie de stockage à stockage). yt-dlp 2026.10.26, Deno 2.9.8 et
FFmpeg 8.1.3 LGPL sont figés et vérifiés par empreinte. Ils sont préparés par
l’installation en ligne et par le kit hors ligne (l’export y ajoute lui-même les
fichiers Windows et Linux), recréés hors ligne après un transfert, et réparés au
premier téléchargement si besoin. Un échec ne bloque jamais l’installation.
Vérifié réellement dans le runner Linux : préparation, détection par yt-dlp et
recréation hors ligne après copie ; archive FFmpeg Windows téléchargée et extraite.
Pas encore essayé sur Windows. Voir le [guide](../utilisation/telecharger-videos-youtube.md).
Nouvelle fonctionnalité compatible (`y`).

La **0.41.0** ajoute `scripts/youtube_videos.py` : une liste texte d’adresses
YouTube (une par ligne, sections `[thème]` facultatives) est téléchargée en 480p
avec `.info.json` et sous-titres fr/en, puis rangée dans
`library/video/youtube/<thème ou chaîne>/`. Le téléchargement passe par un dossier
de travail, sait reprendre et ignore les vidéos déjà présentes ; aucun
contournement de blocage. Demande de Louis du 17 novembre 2026 ; choix par défaut
de l’agent à confirmer (dossier `library/video/`, ligne de commande d’abord,
vidéos hors de l’offre). Voir le [guide](../utilisation/telecharger-videos-youtube.md)
et la [décision](telechargement-videos-youtube.md). Nouvelle fonctionnalité
compatible (`y`) ; aucun téléchargement réel encore effectué.

La **0.40.0** rend les vidéos trouvables. Demande de Louis du 17 novembre 2026,
après un essai de sous-titrage chez Marc où ni la recherche ni l’assistant ne
trouvaient de vidéo. Ajouts : filtre **Vidéos uniquement / Documents uniquement**
dans Rechercher, avec liste complète si la recherche est vide ; actualisation
automatique du répertoire des vidéos locales au démarrage et quand le dossier
change ; outil `find_videos` de l’assistant, recherche préparée quand la question
parle de vidéo, et liens vers le lecteur ajoutés si le modèle les oublie. Voir le
[guide vidéo](../utilisation/videos-locales.md) et le
[bilan](../essais/2026-11-17-recherche-videos.md). Nouvelle fonctionnalité
compatible (`y`) : API `/api/search` étendue par `kind`, données et composants
tiers inchangés. Le même jour, Louis demande un outil qui télécharge une liste
d’adresses YouTube dans la bibliothèque. Seul son
[plan](telechargement-videos-youtube.md) est livré, à valider ; il pose la
question du dossier (`library/video/` actuel ou `library/videos/`) et des droits.

La **0.39.0** apporte les mesures visibles, la lecture de traduction stable et
la conservation du modèle sans expiration. Son bilan distingue les tests de
développement d’un nouvel essai chez Marc.

La **0.38.3** complète la préservation des formules : réduction du contexte et
lecture explicite de la suite utilisent des limites de blocs entiers. Une
formule trop longue est omise et signalée, sans augmenter les budgets. Les
positions restent celles du texte source. Voir le
[bilan ciblé](../essais/2026-11-17-formules-contexte-et-suite.md).
Correction compatible (`z`), données et dépendances inchangées.


La **0.38.2** corrige les demandes explicites de commandes dans une notice :
recherche préalable sur la référence unique fournie, puis lecture avec la question
complète. Les relances reprennent uniquement la dernière référence utilisateur,
sans emprunter une supposition du modèle ou un ancien sujet. Voir le
[bilan ciblé](../essais/2026-11-17-recherche-notices-commandes.md).
Correction compatible (`z`), données et composants tiers inchangés.


La **0.38.1** applique la règle validée par Louis : une question générale reste
traitable sans source précise, avec connaissances générales annoncées et exemples
adaptables. La préparation ne présente plus un lot vide comme des documents lus.
Les commandes exactes et gestes critiques gardent leurs exigences de sources,
paramètres et prudence ; aucun faux document n’est ajouté au suivi.
Voir le [bilan ciblé](../essais/2026-11-17-aide-generale-sans-source.md).
Correction compatible (`z`), schéma personnel et composants tiers inchangés.

La **0.38.0** reprend le volet des conversations selon la demande de Louis du
17 novembre : projets dépliables avec conversations imbriquées, défilement
vertical et séparation redimensionnable sur PC. Les menus permettent de renommer
projets et conversations ; les anciens dossiers et messages restent conservés.

La **0.37.3** conserve les formules extractibles dans les articles lus et leurs
traductions. Le [bilan ciblé](../essais/2026-11-17-formules-documentaires.md)
distingue extraction, contrôle de copie et sens technique restant à relire.
Les blocs sont protégés pendant traduction, les extraits de recherche ne coupent
pas une formule. Les anciens instantanés ne sont pas réécrits. Correction
compatible : niveau `z`, mêmes données personnelles et composants tiers.

La **0.37.2** corrige une aide mobile qui changeait de position pendant le
mouvement d’une vue. Le fondu conserve les éléments fixes à leur place ;
l’[audit de navigation](../essais/2026-11-17-volets-transitions-classement.md#audit-complémentaire-et-correctif-0372--17-novembre-2026)
ajoute les tests d’interruption, de clavier, d’historique et de repli sans API
d’animation. Le lecteur PDF distingue aussi le focus pendant son chargement
d’un vrai changement de profil, qui reste bloquant pour les commandes périmées. Les limites des essais simulés restent explicites.

La **0.37.1** corrige deux défauts reproduits sur Bazzite : les consignes de résumé
devenant des mots de recherche, puis un refus contradictoire de traduction des
sous-titres. Les [essais réels](../essais/2026-11-17-assistant-bibliotheque-bazzite.md)
séparent lectures, bascule de modèle, traduction, reconnaissance et limites de
fidélité. **Recadrage explicite de Louis, 17 novembre :** terminer cet objectif
avant installation neuve, transfert de disque ou autre chantier. Les préparatifs
de ce scénario distinct sont supprimés ; aucune installation utilisateur remplacée.

La **0.37.0** répond au retour de Louis du 17 novembre : réouverture des documents
à droite, transitions courtes pour comprendre les clics et glisser-déposer des
conversations vers les dossiers. Les menus de classement restent disponibles,
les données ne changent pas de schéma et la réduction des animations est respectée.
Voir le [bilan de navigation](../essais/2026-11-17-volets-transitions-classement.md).

**Consigne durable de Louis, confirmée le 16 novembre 2026 :** continuer à garder
la rigueur des choix de design au fil des évolutions. La
[règle d’extension](refonte-ux-evolutive.md#extension-des-fonctions) précise son
application : destination cohérente, commandes compréhensibles, lecture confortable
et suivi explicite. Les prochains ajouts utilisent les composants et parcours
existants ; les propositions nouvelles restent distinguées des décisions validées.

La **0.36.1** corrige les [formes courantes des mots](../essais/2026-11-16-recherche-formes-de-mots.md)
dans la recherche et les passages lus, avec repli par titres borné. Les mesures
comptent les tentatives supplémentaires. Les appels tardifs pendant la fermeture
d’une page sont aussi annulés, avec reprise possible après retour navigateur.
Les essais ciblés et la CI ne remplacent pas la qualification du fonds de Marc.

La version **0.36.0** reprend la [base et la finition de l’interface](../essais/2026-11-16-finitions-interface.md)
après les captures utilisateur : volets, cases et aides corrigés, cartes unifiées,
styles de maquette retirés et composants communs explicites. Les fonctions audio
0.35.0 et les données sont conservées ; les tests de fonctionnement précédents
ne suffisaient pas à valider le rendu.

La **0.35.0** raccorde l’[audio des vidéos incluses](audio-videos-zim.md) au suivi
existant : portions Kiwix, pause/reprise, piste source puis français optionnel et
recherche. Un média absent, sans audio ou d’une autre édition reste explicite.
Les [preuves](../essais/2026-11-16-audio-videos-collections.md) ne certifient pas
les sous-titres de tout le fonds de Marc.

La **0.34.0** réalise la [refonte UX](refonte-ux-evolutive.md) : assistant en trois
zones sur PC, dossiers et recherche de conversations, traduction dans les lecteurs
portail/PDF, reprise et travaux personnels, aides facultatives et composants
évolutifs. Les fonctions vidéo 0.33.0 et les données existantes sont conservées.
Le [bilan](../essais/2026-11-16-refonte-ux.md) distingue recette technique, usage
humain restant à mesurer et PC physiques non mis à jour par cette livraison.

La **0.33.1** corrige le [classement des actions et des prix](../essais/2026-11-16-intention-pratique-et-prix.md),
avec demandes courtes et variantes de remplacement. Les titres restent des pistes
à lire, jamais un certificat de procédure.

La **0.33.0** ajoute l’[examen des vidéos des collections](inventaire-videos-zim.md),
leur lecture et les pistes internes dans la recherche commune, puis leur
préparation française. Audio interne et qualification réelle de chaque vidéo
restent ouverts. Louis autorise la [refonte UX en parallèle](coordination-ux-et-videos.md),
avec branches séparées et intégrations successives.

La **0.32.1** reprend les [corrections de la recette Windows](../essais/2026-11-16-integration-corrections-windows.md) : reconfiguration des routeurs pendant une mise à jour et réponses de refus du contrôleur. Le [bilan sur le PC de Marc](../essais/2026-11-16-campagne-windows-marc.md) distingue installation active, environnements isolés et limites physiques.

La **0.32.0** ajoute le [vocabulaire facultatif et le repère entre passages](../utilisation/documents-et-traduction.md#garder-les-mêmes-mots-dans-un-document--0320), conservés par travail. Les termes restent des préférences à relire ; le contrôle des nombres reconnaît les libellés PDF joints.

La **0.31.0** ajoute la [récupération des sous-titres YouTube](../utilisation/videos-locales.md#récupérer-les-pistes-youtube--0310), à la demande avec Internet, puis lecture/recherche hors ligne et traduction locale optionnelle. La référence doit correspondre au média ; les ZIM et la qualification des vidéos de Marc restent ouverts.

La **0.30.0** conserve les [refus de tests avant lancement](../essais/2026-11-16-diagnostic-refus-demarrage.md)
et fournit un diagnostic exportable en lecture seule. Les états contrôleur/API
et les marges mémoire sont distingués ; les anciennes pannes non enregistrées
ne sont pas reconstituées. Ni reprise forcée ni baisse des réserves mémoire.

La **0.29.0** ajoute [arrêt et suppression des travaux de traduction](../utilisation/documents-et-traduction.md#gérer-une-traduction--0290),
avec reprise volontaire et conservation des originaux, conversations et guides
déjà partagés. Les contrôles sont accessibles aussi pendant la lecture dédiée.

La **0.28.0** améliore la [lecture pendant une traduction](../utilisation/documents-et-traduction.md#lire-pendant-que-le-document-se-traduit--0280) :
progression par pages/passages, texte stable pendant les actualisations et groupe
de lecture retrouvé après rechargement. La direction de refonte en [trois zones](conversations-trois-zones.md) est validée ;
ses détails de dossiers, profondeur et parcours attendent le cadrage de Louis. Le brouillon n’est pas publié avant la fin.

Le [transfert vers SSD](../exploitation/transfert-installation.md) rejoint la
base vidéo 0.26.1 dans la 0.27.0. Inventaire, reprise, adaptation et
bascule locale sont testés sur fixtures ; Windows réel, secours autonome sur PC
vierge et conversion Windows/Linux restent à qualifier. La revue ajoute les
contrôles de routage et le refus du retour pendant une maintenance.

La **0.26.1** corrige le délai de calibration mémoire et rend les noms de rapports
versionnés et horodatés. Les [cinq rapports Windows 0.25.0](../essais/2026-11-16-rapports-marc-0250.md)
distinguent chargement lent, pression mémoire et recherche vidéo non préparée ;
ils ne valident pas tous les démarrages du moteur. Le contexte reste inchangé.

La [0.26.0 de transcription](../essais/2026-11-16-transcription-audio-videos.md)
réutilise Whisper small préparé pour la dictée, sur CPU, puis la traduction
locale existante. Les fichiers vidéo restent intacts et les étapes sont reprenables.
L’acquisition en ligne, les vidéos des ZIM et les essais Windows réels restent
à réaliser.

Le **16 novembre 2026**, Louis ouvre une [configuration matérielle cible évolutive](../installation/configuration-materielle-cible.md) :
NVIDIA **16 Go de VRAM**, probablement RTX **5060 Ti 16 Go** ; **32 Go de RAM
au moins**, puis **64 Go selon les prix**, DDR4 ou DDR5 selon la plateforme ;
**SSD NVMe de 2 To au moins, PCIe 4.0 minimum**. Le processeur reste à déterminer
après mesures. Ce sont des orientations de la future cible, sans achat ni
validation matérielle annoncés ; les configurations observées ci-dessous restent
distinctes. La fiche relie les relevés de Marc et les limites d’interprétation.

La 0.25.0 regroupe les vérifications dans **Paramètres → Tests et diagnostics**,
avec un [essai de traduction sur 40 pages](../exploitation/test-traduction-40-pages.md).
Le document fictif est extrait/traduit réellement, avec reprise et mesures
numériques ; il n’est pas publié dans la bibliothèque. Les réglages courants
de mémoire restent dans Assistant. Le besoin vidéo porte aussi sur des MP4 seuls
et des médias des ZIM ; transcription/récupération restent à développer.

La 0.24.0 prépare en français une piste locale déjà présente, par segments
reprenables, sans changer ses temps ni l’original. Les pistes complètes passent
au lecteur et à la recherche ; les refus restent dans le rapport. Voir le
[guide vidéo](../utilisation/videos-locales.md). Acquisition, transcription des
manques et relecture du fonds réel restent distinctes et non achevées.

La 0.23.1 corrige le [budget des dossiers documentaires](../essais/2026-11-16-rapport-performances-marc-0220.md)
après le rapport Windows 0.22.0 : des sources trouvées et lues ne tenaient plus
dans le message final. L’encodage et les identifiants sont réservés avant lecture,
sans changer le contexte de Marc. Le diagnostic distingue fenêtre demandée,
transmise/chargée et marge estimée. L’essai 16k/32k reste à mesurer sous Windows.

La 0.23.0 ajoute les [vidéos locales](../utilisation/videos-locales.md) à la recherche
commune et au lecteur. L’indexation est volontaire après téléchargement, sans
modifier les originaux ; une piste absente n’est pas une parole lue. L’assistant
peut comparer sous-titres et documents, avec leurs références et limites, sans
voir les gestes. Acquisition, transcription et traduction synchronisée restent
distinctes ; la validation de chaque vidéo de Marc n’est pas déclarée réalisée.

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
décrivent l’application de ces choix. Le modèle de vente du PC préinstallé est
confirmé dans [Connexion simple et direction du produit](acces-simple-et-offre.md) ;
les modalités commerciales et la piste du routeur dédié restent à qualifier.

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
commande explicite. Cette ancienne valeur automatique est migrée en 0.43.1 selon
la demande de Louis du 18 novembre ; les pauses explicites restent conservées.
Les modifications de pare-feu et le créneau Windows Update
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

## Intégration du transfert SSD Windows — 17 novembre 2026

À la demande de Louis, la branche `codex/transfert-ssd-windows` est intégrée
avec les correctifs Windows et le suivi/pilotage local du transfert. La livraison
0.42.0 conserve la source et ne déplace pas le disque Docker en service. Voir
le [guide actuel](../exploitation/transfert-installation.md) et le
[bilan d’intégration](../essais/2026-11-17-integration-transfert-ssd-windows.md).
La copie en deux temps avec bascule courte reste une proposition non implémentée.

## Redémarrage Bazzite confirmé — 17 novembre 2026

Après le redémarrage physique effectué par Louis, les services Docker dédié et
SetupSurvie repartent automatiquement (+19 s et +35 s au relevé), sans commande
de démarrage de l’agent. Portail 0.41.0, recherche, lecture, secours et trois
routeurs sont vérifiés ; voir le [bilan réel](../essais/2026-11-17-installation-neuve-bazzite.md#redémarrage-physique-confirmé--17-novembre-2026).
Ce résultat complète la recette Linux ; téléphone réel, chargement de modèle,
transfert entre SSD et coupure électrique brutale restent distincts.
