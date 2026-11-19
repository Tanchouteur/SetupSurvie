# Plan de refonte UX du portail

**Statut : plan de référence du 13 novembre 2026, concrétisé par une première interface fonctionnelle en 0.1.32.**

Louis valide la présentation PC et demande son activation normale sur Windows/Linux.
Le [guide actuel](../utilisation/portail.md) décrit ce qui est livré ;
le [bilan](../essais/2026-11-13-interface-fonctionnelle.md) distingue les essais sur
fixtures des validations physiques restantes. Le détail du plan ci-dessous conserve
le contexte de conception ; les passages au futur ne sont pas des résultats d’essai.

La [maquette isolée de 0.1.31](../utilisation/maquette-ux.md) est conservée avec
ses exemples fictifs. Cette étape gardait la classique à la racine ; elle est
remplacée en 0.1.32 par l’entrée fonctionnelle et `/classique/`. Le
[bilan de la maquette](../essais/2026-11-13-maquette-ux.md) conserve ses résultats historiques.

Demandes de Louis : clarifier le site sans perdre ses fonctions, conserver une
interface actuelle utilisable, garder l’ouverture directe des encyclopédies,
réunir les suivis de la machine, rendre la navigation confortable et simplifier
les opérations complexes sur mobile. La structure ci-dessous est une proposition
de mise en œuvre ; les exigences de conservation et de navigation sont demandées.

Base examinée : pilote **0.1.30**, commit `4ea6920`, code du portail, routes du
pilote, contrôleur et scripts de téléchargement. Il s’agit d’un examen du dépôt,
pas d’une observation du PC de Marc ni d’une recette navigateur de la future UI.
Les [choix actuels](choix-actuels.md) décrivent toujours le produit livré.

## 1. Résultat recherché

Une personne novice doit pouvoir répondre à trois questions : « Où trouver ce
que je cherche ? », « Que fait l’appareil ? », « Dois-je faire quelque chose ? ».
L’usage quotidien commence par les documents, les questions et les cartes.
La préparation et l’entretien se trouvent dans un espace identifié.

Règles non négociables :

- Garder toutes les fonctions actuelles sur ordinateur et documenter leur destination.
- Permettre de cliquer sur une encyclopédie ou une collection pour l’ouvrir
  directement dans Kiwix, sans imposer recherche préalable ni passage par l’IA.
- Conserver sources originales, lecture PDF, favoris, traductions et accès de secours.
- Préserver profils, identifiants, conversations, points, parcours et contenus.
- Ne pas introduire de mot de passe ; Famille donne accès à la gestion sans
  constituer une protection entre utilisateurs du réseau.
- Ne pas démarrer l’IA lors de la consultation du site ou des suivis.
- Ne pas interrompre le téléchargement de Marc pour réaliser la refonte.
- Conserver une interface classique fonctionnelle et un retour simple vers elle.

## 2. Navigation principale proposée

| Entrée | Fonction principale | Sous-vues |
| --- | --- | --- |
| Accueil | Commencer ou reprendre un usage | Recherche, reprendre, favoris, raccourcis |
| Bibliothèque | Explorer et lire les contenus présents | Collections, recherche, parcours, favoris, traductions partagées |
| Assistant | Poser des questions et retrouver les échanges | Conversation, historique, document associé et traduction |
| Cartes | Consulter le territoire et ses repères | Recherche, mes repères, itinéraires, affichage |
| Mon appareil | Comprendre et entretenir le serveur | Vue d’ensemble, activité, téléchargements, stockage, réglages |

Sur ordinateur : menu latéral stable ; conversations récentes dans l’espace
Assistant plutôt qu’une longue liste permanente sur toutes les pages.
Sur mobile : navigation compacte avec libellés et accès aux cinq destinations,
sans empiler les sous-onglets dans la barre principale. Tester les libellés et
la place réelle sur petit écran avant de figer barre basse ou menu secondaire.
Le profil choisi reste visible et changeable sans perdre le contexte ouvert.

Aide, retour utilisateur, interface classique, Open WebUI et accès documentaire
de secours restent des liens identifiés dans le menu secondaire. Open WebUI
conserve un lien visible, avec l’explication que ses conversations sont distinctes.

## 3. Contenu des écrans

### Accueil

- Une recherche qui conduit à la Bibliothèque et conserve la requête.
- Reprendre la dernière conversation ou lecture accessible pour ce profil.
- Quelques favoris et raccourcis vers Bibliothèque, Assistant et Cartes.
- Un résumé discret d’activité, présent seulement si utile : téléchargement,
  préparation, pause ou problème nécessitant une action.

Pas de graphiques matériels sur l’accueil. Les collections déjà présentes sont
accessibles depuis un raccourci « Voir mes encyclopédies et livres ».

### Bibliothèque

Deux entrées complémentaires : **Explorer les collections** et **Rechercher**.
L’exploration reste utilisable sans saisir de question.

Les cartes de collection montrent titre, langue, description courte et état
réel de disponibilité. L’action principale « Ouvrir l’encyclopédie » ou
« Ouvrir la collection » pointe vers son lecteur local. Une collection présente
mais sans recherche intégrale reste ouvrable, avec cette limite expliquée.
Le lien est un véritable lien : nouvel onglet et copie de l’adresse fonctionnent.

Les résultats de recherche gardent provenance, dates et ouverture de l’original.
Conserver les filtres de langue, favoris personnels, traductions partagées,
parcours par domaine/sujet/niveau, lecture des étapes et préparation d’une question.
Les guides gardent lecture PDF ou texte, téléchargement et question sur le document.
L’ajout de contenus conduit à Mon appareil ; il n’encombre pas la consultation.

### Assistant

Conserver les historiques, nouvelle conversation, suppression, citations,
document associé, dictée, annulation et trois modes de réponse conseillés.
Les choix supplémentaires pour les essais restent accessibles dans un volet
avancé ; la refonte ne choisit pas de modèle gagnant.

La traduction reste liée au document : plage de pages, progression, pause,
reprise explicite, comparaison et avertissements, passages et export. Ne pas
publier de source privée ni de proposition refusée dans un suivi global.
Un changement d’écran ne doit ni effacer le brouillon ni annuler le travail.

### Cartes

Conserver le fond local, recherche, lieux proches, listes et repères, itinéraires,
fiches de trajet, export GPX, relief, mesures, profils du terrain, impression et
choix du départ. Les options de préparation renvoient à Mon appareil.
Distinguer fond de carte, adresses, relief et réseau d’itinéraires disponibles.
Une carte visible ne signifie pas que ces quatre ensembles sont prêts.

### Mon appareil

La première page présente l’état du serveur en langage courant, puis donne
accès aux détails. « Appareil » désigne le PC qui héberge SetupSurvie, même
lorsque cette page est consultée depuis un téléphone.

| Sous-vue | Informations et actions |
| --- | --- |
| Vue d’ensemble | Fonctions disponibles, opérations en cours, espace libre, alertes utiles et dernière observation |
| Activité | Téléchargement, vérification, préparation/recherche et travaux de l’assistant, avec liens vers leur détail |
| Téléchargements | En cours, en attente, à reprendre, terminés ; ajouter des collections et préparer des zones |
| Stockage | Espace libre du volume documentaire, contenus présents par type, tailles connues et éventuelles inconnues |
| Réglages | Profils, lieux de référence, moteur IA, accès téléphone/QR, ajout de guide, contexte assistant et retours |

La vue d’ensemble distingue : bibliothèque et recherche, cartes et couvertures,
assistant prêt/occupé/arrêté/mode jeu, service de commande, opérations documentaires.
Elle indique ce qui reste utilisable lors d’une panne partielle.
Une pause volontaire de l’IA n’est pas une panne globale.

Un volet « Mesures du PC » présente mémoire du PC, mémoire et activité de la
carte graphique, température GPU si disponible, modèles chargés et questions
en cours. Ajouter CPU et débit uniquement après collecte hôte fiable et bornée,
sans prétendre qu’ils existent déjà. Indiquer que les mesures globales incluent
les jeux et autres programmes. L’absence de mesure signifie « indisponible »,
jamais zéro. Pas de promesse de santé du disque, d’autonomie électrique ou de
consommation sans capteur réellement disponible.

Chaque état porte la date de son observation ; une valeur ancienne est signalée
comme telle. Une déconnexion du suivi ne transforme pas une opération en échec.
La première version n’implique pas de courbes historiques : les définir seulement
si elles aident à comprendre un problème, avec rétention bornée.

Les sauvegardes, mises à jour et disque de secours ont leur place future dans
cet espace, mais aucun bouton ne doit annoncer une capacité non livrée. Distinguer
« guide disponible », « copie effectuée », « vérifiée » et « restauration testée ».
Le [protocole de secours](../exploitation/disque-de-secours-hors-ligne.md) reste
un plan pour les parties non réalisées.

## 4. Téléchargements : un suivi commun et fidèle

### Présentation

Commencer par une phrase d’état, le volume du plan, le volume vérifié, les
transferts actifs et la prochaine action éventuelle. Séparer les octets partiels
des fichiers reçus et vérifiés : un pourcentage réseau n’est pas un pourcentage
de disponibilité. Présenter une progression globale et, au second niveau, celle
des fichiers simultanés. Ne pas additionner deux fois un fichier déjà présent.

États : préparation de la sélection, téléchargement, vérification, attente d’une
nouvelle tentative, pause demandée, en pause, interrompu, préparation pour la
recherche, terminé et suivi indisponible. Expliquer une vérification longue sur
HDD sans la présenter comme un blocage. Une erreur réseau récupérable peut
indiquer la prochaine tentative plutôt que demander immédiatement une action.

La durée restante et le débit ne sont affichés que si leur mesure est fiable.
L’interface dit « estimation indisponible » si nécessaire. La fin du transfert,
la consultation directe et la disponibilité en recherche restent distinctes.

### Intégration technique à réaliser

Le gestionnaire web lit son état `library-web/state.json`, puis les octets de
`catalog/content-progress.json` lorsque sa propre tâche est en téléchargement.
Le moniteur Windows rapproche aussi `diagnostics/bibliotheque-transfer.json`,
le plan, `catalog/downloaded-content.json`, les fichiers partiels et le processus.
Ces deux vues doivent converger sans créer un deuxième téléchargement.

- Produire côté hôte un état commun identifié par opération, origine et plan,
  avec dates d’observation, phases, volumes, fichiers actifs et capacités de commande.
- Rattacher les reprises et tentatives à la même opération ; rapprocher les
  anciens fichiers sans attribuer un état périmé au nouveau processus.
- Vérifier l’identité du processus, pas seulement l’existence de son PID.
  Prévoir l’adaptation des transferts déjà actifs chez Marc.
- Conserver les verrous, reçus, reprises partielles, contrôles d’intégrité et
  de capacité ; ne pas analyser les journaux texte comme source principale d’état.
- Fournir au portail une réponse filtrée via le pilote et le contrôleur interne.
  Ne pas publier les ports de contrôle, chemins privés, jetons ou journaux bruts.
- Commencer par la lecture du transfert existant. Exposer pause/reprise seulement
  si elles sont réellement prises en charge par ce processus et ses reprises Windows.
- Mutualiser les mesures entre clients, borner les lectures et réduire le rythme
  sur les pages masquées. Ne pas parcourir toute la bibliothèque toutes les secondes.
- Ne pas tester Internet périodiquement sans besoin ; distinguer connexion au
  serveur local et problème réseau constaté pendant un transfert.

L’activité globale ne divulgue ni conversations ni brouillons/traductions privés.
Afficher les détails personnels seulement dans le contexte du profil concerné,
sans présenter les profils comme une barrière de confidentialité.

## 5. Navigation confortable et mémoire de l’interface

### Historique et liens directs

Chaque écran et sous-vue importante possède une adresse stable. Filtres de
recherche non sensibles, collection, document et conversation peuvent être
adressables. Ne pas placer de brouillon, coordonnées privées ou texte personnel
dans l’URL. Garder les liens existants, notamment `#library`, `#data`,
`#settings`, `#monitor`, `#connect` et les liens de documents ; les traduire
vers leur destination si leur structure change.

- Précédent et Suivant restaurent l’écran, la sous-vue, les filtres et la position.
- Ouvrir un résultat puis revenir retrouve la liste précédente au même endroit.
- Une recherche validée et une navigation volontaire créent une étape d’historique.
  Les frappes, mesures, sondages et mises à jour de progression n’en créent pas.
- Les liens directs, rechargement et ouverture dans un nouvel onglet fonctionnent.
- Les dialogues se ferment avec Retour avant de quitter leur écran ; Échap,
  fermeture visible, focus et historique doivent rester cohérents.
- Les navigations restaurent un focus pertinent ; un suivi automatique ne vole
  jamais le focus ni la position de lecture.

### Ce qui est mémorisé

| État | Portée et règle proposée |
| --- | --- |
| Dernier écran, sous-onglets et volets ouverts | Par navigateur et profil ; restauration à la réouverture sans primer sur un lien explicite |
| Filtres et position de liste/lecture | Par vue, document et profil ; retour exact tant que la ressource existe |
| Carte : centre, zoom, fond et affichage | Par navigateur et profil ; ouvrir un trajet explicite reste prioritaire |
| Conversation sélectionnée et brouillon | Par profil et conversation ; brouillon local sauvegardé avec délai court, sans envoi automatique |
| Favoris, conversations, points et listes | Données existantes côté serveur ; pas de duplication dans un nouveau stockage |
| Préférence classique/nouvelle interface | Par navigateur ; choix explicite et lien de bascule toujours accessible |

Séparer le contexte propre à chaque onglet du navigateur pour éviter que deux
onglets ouverts s’écrasent ; partager seulement les préférences qui doivent l’être.
Au changement de profil, ne jamais restaurer le brouillon ou la conversation de
l’autre profil. Préserver les contrôles d’onglets périmés et de profil des pages
PDF et cartes. Définir une rétention bornée des brouillons et une commande
« Effacer la mémoire de navigation sur cet appareil », distincte des données serveur.

Ne pas restaurer aveuglément formulaire de suppression, commande en attente,
transfert à lancer, micro actif ou action destructive. Une réouverture ne relance
ni téléchargement ni inférence ni traduction. En cas de ressource supprimée,
expliquer et revenir à sa liste. Si le stockage navigateur est indisponible,
la navigation reste fonctionnelle avec une mémoire limitée à la session.

## 6. Mobile : consultation et suivi avant préparation complexe

Louis autorise une interface mobile simplifiée. Retirer des commandes complexes
sur téléphone ne supprime pas leur disponibilité sur ordinateur. La largeur ne
doit pas être assimilée à un système d’exploitation : vérifier aussi orientation,
tablette, clavier et possibilités de pointage.

| Fonction | Téléphone | Ordinateur |
| --- | --- | --- |
| Collections, encyclopédies, recherche, lecture et favoris | Complets | Complets |
| Assistant, historique, sources, dictée si compatible | Complets, composition adaptée au clavier | Complets |
| Traduction | Consultation, progression et commandes simples dans le document | Réglages et comparaison approfondie |
| Carte, recherche, repères et trajets existants, fiche de trajet | Consultation confortable | Consultation et gestion |
| Création/édition de listes, points, trajets complexes et préparation des cartes | Renvoi expliqué vers ordinateur | Disponibles |
| État machine, stockage et transferts | Résumé et détails utiles en lecture | Résumé, détails et gestion |
| Ajouts massifs, configuration avancée, maintenance | Explication et accès au guide | Gestion dans le profil Famille |
| QR d’accès, choix de profil et liens de secours | Accessibles | Accessibles |

Pour les commandes non proposées sur mobile : phrase courte « Préparez cette
zone depuis un ordinateur », sans bouton inactif sans explication. Le téléphone
conserve l’accès aux données déjà préparées. La pause/reprise documentaire mobile
pourra être retenue après validation du contrôle commun ; elle n’est pas nécessaire
à la première version de consultation. Les anciennes restrictions réellement
liées au serveur, et non au téléphone, doivent être expliquées précisément.

Tester clavier ouvert, zones sûres iPhone, orientation, zoom texte, défilement
et retour depuis une encyclopédie. Pas de fonction reposant exclusivement sur
survol, glisser-déposer ou icône sans libellé. Ne pas rendre la lecture dépendante
des nouveaux panneaux de suivi. La dictée garde ses prérequis HTTPS et navigateur.

## 7. Style et langage communs

Conserver le logo feu/livre, les tons verts et un fond clair. Unifier espacements,
titres, cartes, boutons, formulaires et états dans des styles partagés.
Réduire les grandes accroches décoratives sur les écrans d’usage répété au profit
d’un titre concret et d’une action principale claire. Ne pas renommer le produit.

- Taille de texte confortable, largeur de lecture limitée, zones tactiles d’au
  moins 44 pixels comme cible de conception, contraste et focus visibles.
- États écrits en toutes lettres ; la couleur est un complément.
- Chargement, absence de contenu, pause, panne et mesure inconnue ont chacun
  leur message et, si utile, une action possible.
- Erreur : ce qui s’est passé, ce qui reste utilisable et quoi faire ensuite.
- Unités cohérentes et explicites ; ne pas mélanger Go et Gio dans une même jauge.
- Actualisation discrète, sans déplacer les cartes ni annoncer chaque mesure
  au lecteur d’écran ; limiter les animations et respecter leur réduction.
- Remplacer les mentions obsolètes de connexion, comptes ou administrateur par
  le vocabulaire des profils et du profil Famille, sans faux sentiment de protection.

## 8. Conserver l’interface actuelle et revenir en arrière

Une capture d’écran ou l’historique Git ne suffisent pas : Louis doit pouvoir
réutiliser l’ancienne interface avec ses données.

Avant la première modification fonctionnelle :

1. Identifier et conserver par un tag Git poussé le commit de référence réellement
   retenu (actuellement `4ea6920`, à revalider si le produit évolue avant les travaux).
2. Garder un ensemble autonome des pages, scripts, styles et ressources propres
   de cette interface, accessible par une route stable, proposée `/classique/`.
   Auditer les chemins absolus et partager les gros lecteurs tiers sans les dupliquer.
3. Conserver les liens vers cartes, PDF, secours et Kiwix. Une route d’entrée
   seule ne suffit pas si elle charge les nouveaux scripts à la place des anciens.
4. Maintenir les contrats API nécessaires aux deux interfaces ; adapter les
   données à la frontière au lieu de maintenir deux moteurs métier concurrents.
5. Fournir « Utiliser l’interface classique » et « Essayer la nouvelle interface ».
   Le choix est mémorisé localement ; l’URL explicite permet toujours d’ouvrir l’autre.
6. Garder la classique comme entrée par défaut pendant les essais. Le passage
   par défaut à la nouvelle vient après la recette avec Louis/Marc ; conserver
   ensuite le retour classique jusqu’à décision explicite de retrait.

Les deux interfaces utilisent les mêmes données et les mêmes opérations. Une
bascule ne copie, ne supprime et ne migre pas les conversations. Elle ne met pas
les travaux en pause et ne les lance pas en double. Une incompatibilité future
bloque la livraison tant que le retour classique promis n’est pas assuré.

Le retour d’interface doit être possible sans restauration de base ni retour
arrière du serveur. Un retour arrière logiciel complet reste une autre procédure,
avec sauvegarde et compatibilité vérifiées ; jamais un simple pull dans le dossier actif.

## 9. Correspondance des fonctions actuelles

Cette grille est le minimum de non-régression ; lors de l’implémentation, relever
les actions et liens précis des pages, scripts et API dans une liste de recette.

| Aujourd’hui | Destination proposée et éléments à préserver |
| --- | --- |
| Accueil | Accueil : recherche, exemples, accès lecture et assistant |
| Bibliothèque | Bibliothèque : langues, résultats, sources, parcours, favoris et traductions |
| Données locales : encyclopédies, livres et guides | Bibliothèque → Collections : ouverture directe Kiwix et lecture des guides |
| Données locales : modèles | Mon appareil → Stockage et Réglages IA : inventaire distinct du modèle chargé |
| Données locales : sélection et téléchargement | Mon appareil → Téléchargements : thèmes, langues, volume, compléments, aperçu, limites, reprise |
| Données locales : géographie et routage | Mon appareil → Téléchargements → Préparer une zone, avec contraintes et commandes existantes |
| État de l’appareil | Mon appareil → Vue d’ensemble et Mesures du PC : moteur, GPU, RAM, disque, modèles et questions |
| Assistant et documents associés | Assistant : historique, suppression, modes, dictée, annulation, citations, lecture et traduction |
| Paramètres : lieux et moteur | Mon appareil → Réglages : domicile/départ, recherche locale/IGN, arrêt et reprise explicite |
| Paramètres : guide, contexte et retours | Mon appareil → Réglages : ajout et métadonnées, contexte exact, retours |
| Profils | Sélecteur permanent ; création et liste dans Mon appareil → Réglages |
| Autre appareil | Mon appareil → Ouvrir sur un téléphone : IP, QR, impression, copie et aide HTTPS |
| Page Cartes | Cartes : fonctions conservées sur ordinateur, consultation adaptée au téléphone |
| Lecteur PDF | Lien stable : original, téléchargement, favoris, question et lecture de secours |
| Open WebUI | Lien visible : profil partagé, conversations distinctes et fonctions avancées |
| Accès documentaire de secours | Lien permanent et `/secours.html` inchangé dans son rôle |
| Suivi PowerShell de Marc | Mon appareil → Téléchargements ; conserver le terminal en solution de diagnostic |

## 10. Lots de réalisation et critères de sortie

| Lot | Livraison | Validation avant le suivant |
| --- | --- | --- |
| 1. Inventaire et conservation | Liste complète des actions/liens, référence Git, interface classique autonome | Classique utilisable depuis sa nouvelle route, mêmes profils et données |
| 2. Maquette navigable | Écrans ordinateur/mobile, sous-vues, langage, états fictifs clairement signalés | Parcours novice, liens directs, Retour/Suivant, clavier et mémoire de navigation |
| 3. État commun en lecture | Adaptateurs du suivi web et Windows, résumé machine, transfert existant visible | Fixtures : vérification, reprise, état périmé, erreur, plusieurs fichiers, contrôleur absent |
| 4. Bibliothèque et assistant | Collections directement ouvrables, recherche, documents, conversations et traductions | Grille de non-régression et retour exact depuis un document |
| 5. Mon appareil et cartes | Gestion déplacée, détails machine, commandes compatibles, mobile simplifié | Pas de double commande ; contraintes serveur, mode jeu et opérations en cours respectés |
| 6. Pilote accompagné | Essais Windows de Marc, téléphone réel, bascule facultative et guides actualisés | Retours traités, classique accessible, décision de changement d’entrée par défaut |

La maquette et les tests runner utilisent de minuscules fixtures et des services
simulés : pas de modèle, archive ou carte lourde. Chaque livraison fonctionnelle
incrémente la version affichée et API ; ce plan documentaire ne la change pas.
Ne pas multiplier les branches permanentes : intégration vérifiée sur `main`,
puis suppression des branches temporaires.

## 11. Recette attendue

Parcours à faire réaliser à Marc et, si possible, à une personne novice :

1. Ouvrir une encyclopédie directement depuis sa carte de collection.
2. Rechercher un sujet, ouvrir un résultat, puis revenir aux mêmes résultats et
   à la même position avec Précédent ; tester aussi Suivant.
3. Retrouver un favori, lire un PDF et ouvrir la source originale d’une réponse.
4. Rédiger une question, changer d’écran, revenir et retrouver le brouillon.
5. Fermer/réouvrir le navigateur et retrouver ses sous-onglets sans relancer une action.
6. Changer de profil avec deux onglets ouverts, vérifier l’absence de mélange
   des brouillons et historiques ; supprimer une ressource précédemment mémorisée.
7. Comprendre depuis le téléphone ce que télécharge le serveur et distinguer
   transfert, vérification et disponibilité ; fermer le site sans arrêter le travail.
8. Lire une carte et un trajet préparés sur téléphone ; retrouver sur ordinateur
   les fonctions de création/édition volontairement retirées du mobile.
9. Comprendre que l’IA en mode jeu laisse les documents utilisables ; aucune
   consultation ni restauration de session ne la redémarre.
10. Ouvrir classique/nouvelle interface alternativement et retrouver les mêmes
    contenus, profils et conversations, y compris après rechargement et lien direct.
11. Simuler une panne du contrôleur ou du pilote : mesures signalées inconnues,
    absence de blocage de lecture, accès Kiwix/PDF/secours conservés selon le service atteint.
12. Tester sans Internet mais avec réseau local, puis rupture/rétablissement du
    lien au serveur : aucun faux état « terminé » ni action répétée à la reconnexion.

Prévoir tests unitaires des adaptateurs et agrégations, tests API de compatibilité
et tests navigateur des parcours ci-dessus, avec fixtures privées jetables.
Exécuter les tests adaptés, la suite Python avant livraison et `git diff --check`.
La recette classique doit aussi être exécutée, pas seulement celle de la nouvelle UI.
Windows réel, Safari iPhone réel, dictée et fonctionnement hors ligne sont des
validations distinctes. Une émulation ou une maquette ne les prouve pas.

**Décision de conception proposée :** commencer par préserver la classique et
valider la navigation, puis raccorder les suivis réels avant le déplacement complet
des écrans. La réalisation et le déploiement feront l’objet d’un travail ultérieur ;
ce document ne modifie ni le site ni l’installation active de Marc.
