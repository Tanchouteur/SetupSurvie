# Composants et règles de présentation du portail

**Référence de développement — 0.37.2, 17 novembre 2026.** Cette organisation
remplace l’empilement de styles de la maquette utilisé en 0.34.0. Elle répond
aux captures de Louis : aides trop grandes, case mal alignée, commandes de volets
redondantes et cartes de paramètres incohérentes. Les tests de fonctionnement
précédents ne validaient pas ces détails visuels.

## Choix de la base

Le portail reste en HTML/CSS/JavaScript local, sans nouvelle dépendance de
fonctionnement et sans ressource distante. Les commandes existantes, leurs IDs,
les événements documentaires/vidéo et les API sont conservés. Le générateur
connaît une seule liste ordonnée de ressources ; les HTML ne se maintiennent pas
séparément. Aucun compilateur frontend n’est nécessaire pour une installation.

Une comparaison documentaire a porté sur [Bootstrap](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
et [Pico](https://picocss.com/docs). Bootstrap fournit des composants, mais son
introduction ici demanderait d’adapter les contrôles et conventions du portail.
Pico applique des styles aux éléments HTML et sa documentation affiche désormais
un arrêt de maintenance. Pour cette correction, une base locale plus petite et
unifiée est retenue ; ajouter une seconde couche globale ne résoudrait pas les
conflits de cascade observés. Il s’agit du choix de ce chantier, pas d’une règle
interdisant une bibliothèque future lorsque son intérêt est démontré.

## Un propriétaire par responsabilité

| Fichier | Responsabilité |
| --- | --- |
| `portal/style.css` | Contrôles historiques, états métier et lecteurs communs ; conservés pour compatibilité (le portail classique qui les partageait est retiré en 0.63.0) |
| `portal/interface/modele.html` | Depuis 0.63.0 : balisage des contrôles et de leurs IDs, source unique de `portal/index.html` ; ne contient ni ressource propre ni lien vers une autre interface |
| `portal/interface/style.css` | Structure du portail et navigation, règles propres aux outils ; ancien thème complet de la maquette retiré |
| `portal/interface/ux-system.css` | Variables, typographie, formulaires, aides, surfaces, bibliothèque et lecteurs : règles communes de présentation |
| `portal/resource-status.css` et `resource-status.js` | Bloc modèle et jauges mémoire dans la navigation PC du portail et des Cartes. Le portail réutilise son actualisation, les Cartes lisent les mesures tant que la barre est visible. |
| `portal/interface/settings.css` | Grilles de cartes, contenu des cartes, formulaires et restrictions mobiles des paramètres |
| `portal/interface/assistant-workspace.css` | Conversation, composition, volets et adaptation aux largeurs ; aucun deuxième thème de navigation |
| `portal/interface/reader-work.css` | Travail de traduction dans le lecteur et fenêtre PDF dédiée |
| `portal/interface/motion.css` et `motion.js` | Transitions et retour visuel ; aucun appel API ni état métier, aucune attente ajoutée aux commandes ; partagés avec cartes/PDF |
| `portal/design/tokens.css` | Depuis 0.44.0 : polices locales, couleurs, rayons, ombres, durées et icônes, partagés par toutes les pages |
| `portal/design/system.css` | Depuis 0.44.0 : apparence du portail, chargée après les feuilles des fonctions, qui gardent leur disposition |
| `portal/design/pages.css` | Depuis 0.44.0 : même identité pour Cartes, PDF, secours et suivi de copie ; ces pages restent utilisables sans elle |
| `portal/design/experience.js` | Depuis 0.44.0 : repères de navigation, progression de lecture et accès rapide, sans API ni état enregistré |
| `portal/interface/ui.js` | Primitives sans API ni données de profil : icônes SVG locales, aide facultative, carte de navigation et en-tête de carte dépliable |
| `portal/interface/ux-system.js` | Reprise, travaux personnels et adaptations communes utilisant les contrôles du portail |
| `portal/interface/layout.js` | Placement initial des contrôles, avant leur raccordement aux actions |
| `portal/interface/assistant-workspace.js` | État et commandes des volets, dossiers, classement et sources consultées |
| `portal/interface/settings-layout.js` | Organisation des rubriques, avec un seul modèle de carte `SurvieUI.cardLink` |
| `portal/interface/work-queue.css`, `work-queue.js` et `portal/work-queue-preview.js` | File d’attente : page, aperçu au survol et raccourci, partagés avec Cartes et PDF |
| `scripts/build_portal.py` | Génère l’entrée unique `portal/index.html` depuis `modele.html` ; ordre explicite des ressources, primitives avant layout, navigation après les modules |

Les scripts repris sont formatés pour la lecture. Les outils de formatage et
l’analyseur CSS utilisés dans le runner ne sont pas des dépendances du logiciel
livré. Les variables de présentation ne doivent pas remplacer un état serveur.

## Direction visuelle « Veillée » — 0.44.0

**Décision du 18 novembre 2026.** Louis demande une refonte du design, sans
changement de fonctions, et laisse le champ libre sur l’expérience à condition de
ne pas dégrader l’existant. L’agent a retenu l’univers du logo : le feu, le livre
et le papier. Le [guide de design Veillée](guide-design.md) est la référence des
prochaines interventions. Cette section conserve les choix du premier lot.

- **Couleurs.** Papier chaud pour les fonds, encre brune pour le texte. Le rouge
  braise est réservé à l’action principale d’un écran et aux repères de position.
  Les boutons ordinaires sont encre, les boutons secondaires papier. Le vert ne
  sert plus qu’aux états « prêt » et « disponible ».
- **Typographie.** Fraunces pour les titres, Atkinson Hyperlegible Next pour le
  texte, choisie pour sa lisibilité. Les deux sont sous licence SIL OFL 1.1,
  embarquées dans `portal/design/fonts/` avec leur licence et sans accès réseau.
- **Mouvement.** Il indique une position ou une conséquence : pastille et
  soulignement qui glissent, cartes qui se soulèvent, entrées courtes. Un bloc
  contenant une aide fixe s’anime en opacité seulement. La réduction du mouvement
  coupe tout, y compris les braises de l’accueil.
- **Accès rapide.** `Ctrl K`, `⌘ K`, `/` ou la loupe ouvrent une fenêtre pour
  chercher, préparer une question ou aller à une page. Une question préparée n’est
  jamais envoyée sans l’action de l’utilisateur.

Le bandeau sous la navigation est retiré sur PC. Depuis 0.48.1, le numéro de
version est aussi visible dans la barre supérieure. Les anciennes feuilles conservent des règles
désormais recouvertes ; leur nettoyage reste à faire, par petites étapes.
Sur mobile, les liens de navigation des Cartes ont une hauteur tactile minimale
de 44 px, avec un bandeau de hauteur inchangée pour conserver la place de la carte.

## Cartes et commandes

Une carte de destination comprend toujours un titre, une courte description et
la même action finale. Les cartes d’un groupe partagent largeur, hauteur, marges,
rayon et hiérarchie de texte. La description occupe l’espace disponible et les
actions s’alignent en bas. Les cartes dépliables partagent aussi un titre et une description visibles dès
leur état fermé via `SurvieUI.describeDisclosure`. Une carte de formulaire conserve la hauteur nécessaire
à ses champs ; on ne coupe pas une commande pour égaliser des contenus différents.

Les éléments interactifs restent explicites et accessibles. Une case et son
libellé sont sur une même ligne ; une aide n’est pas imbriquée dans un libellé.
L’aide est facultative, se ferme avec Échap et n’occupe pas la place d’une
condition importante. La saisie de l’assistant ne contient plus de bouton « i ».

Chaque volet de l’assistant porte son bouton de fermeture. Quand il est fermé,
son bouton d’ouverture apparaît dans l’en-tête, du côté du volet concerné. Sur téléphone, fermer le volet
ramène à la conversation. Le bouton « Discussion » et la rangée de trois faux
onglets sont supprimés. Un seul bouton Nouvelle discussion est déplacé selon
la place disponible ; il n’existe pas de copie indépendante du contrôle.

## Recette de finition

Contrôler une conversation longue avec tableaux, une liste de conversations,
les options ouvertes, un lecteur/travail en pause, des résultats de recherche,
et chaque rubrique des paramètres. Examiner PC 1920/1440/1024, téléphone
390/320 et écran court/paysage. Mesurer aussi les zones réellement cliquables,
l’alignement case/libellé et les cartes de description longue.

La recette `browser_ui_finish.js` couvre les défauts signalés : cartes uniformes,
libellés, volets, commande unique, aides et débordements. Les recettes existantes
restent nécessaires pour la navigation, les profils, brouillons et travaux.
Les captures doivent être regardées en plus des assertions : une absence de
débordement ne prouve ni l’élégance ni la compréhension. Safari sur iPhone et
la perception des utilisateurs restent des validations distinctes. Les captures
utilisateur venant de Firefox sur PC, ses parcours principaux font aussi partie
de la recette. Le repli des cartes en cas d’affichage graphique indisponible
présente une explication française, avec sortie vers la bibliothèque, sans
exposer le rapport interne du pilote graphique.

## Mouvement et classement — demande de Louis du 17 novembre 2026

Louis demande des transitions pour comprendre le résultat des clics et le
classement des conversations par glisser-déposer. La 0.37.0 utilise des transitions
CSS courtes pour les commandes et les colonnes du poste de discussion, et
`Element.animate()` pour révéler les pages, résultats et contenus dépliés.
Les ouvertures de documents et recherches conservent leurs messages d’attente
existants. Une nouvelle navigation annule la précédente animation ; aucune
animation n’est relancée par les mises à jour de texte d’une réponse.

Les transitions durent 140–220 ms. Le focus et les attributs accessibles sont
mis à jour immédiatement ; un volet qui se ferme devient immédiatement `inert`.
Le réglage `prefers-reduced-motion: reduce` coupe les effets CSS et JavaScript,
y compris s’il change pendant une animation. Aucun clone du DOM, état privé
mémorisé ni service supplémentaire n’est nécessaire.

Les dépôts acceptent seulement un glissement commencé dans la liste du profil
courant. La cible est indiquée visuellement ; la commande utilise la même API
que le sélecteur du menu. Le changement est confirmé après enregistrement.
Un dépôt hors dossier, une navigation ou un changement de profil annule le
contexte de glissement. Les erreurs conservent la conversation et le brouillon.
Le menu reste la commande accessible au clavier et sur écran tactile.

Références techniques : [Element.animate()](https://developer.mozilla.org/en-US/docs/Web/API/Element/animate)
et [réduction du mouvement](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion).

Depuis 0.37.2, les révélations génériques animent uniquement l’opacité. Ne pas
transformer une vue contenant des aides ou contrôles fixes : une transformation
change leur repère de positionnement, même pour un déplacement de quelques
pixels. Le déplacement reste réservé aux éléments qui en ont besoin dans leur
propre composant ; les colonnes de l’assistant continuent d’animer leur largeur.
La recette `browser_motion_resilience.js` ouvre une aide pendant la transition
mobile et contrôle son placement avant et après. Voir la
[référence CSS sur le repère créé par transform](https://developer.mozilla.org/en-US/docs/Web/CSS/transform).


## Volet par projets — 0.38.0

Les dossiers existants sont présentés comme projets dépliables. Chaque projet
charge ses conversations et sa pagination à l’ouverture, avec garde de profil
et de génération. Une seule surface verticale défile dans le volet. Les menus
de renommage et le classement restent sur leurs API existantes. La séparation
PC utilise la capture du pointeur et un rôle separator accessible au clavier ;
sa largeur est bornée par l’espace disponible. Aucun changement de schéma.
