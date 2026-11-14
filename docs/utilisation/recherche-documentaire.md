# Retrouver un document utile

**Guide actuel — portail 0.5.0, 14 novembre 2026.** Les essais de développement
utilisent des documents fictifs et un vrai Kiwix sur de petites archives générées.
La pertinence et les délais sur le fonds de Marc restent à vérifier sur son PC.

## Chercher dans la bibliothèque

Dans **Bibliothèque → Rechercher**, décrire le besoin : « allumer un feu »,
« fabriquer un générateur à pédales », « rendre eau potable » ou « réparer un vélo ».
Le choix de langue permet de chercher en français et en anglais. Le sélecteur
**Toutes les collections** permet aussi de cibler une source installée, par exemple
Wikipédia. Ce choix reste dans l’adresse pour le rechargement et Précédent/Suivant.
Une formule comme « faire du feu dans Wikipédia » peut également cibler cette source.

La recherche fonctionne sans modèle IA. Elle combine titres, texte des guides,
articles Kiwix, variantes techniques françaises et anglaises et recherches plus
courtes lorsque la première formulation ne trouve rien. Le classement privilégie
le sujet du titre et du passage ; pour une demande pratique, les mentions de quiz,
d’histoire ou de prévention seules passent après les correspondances plus directes.
Il s’agit d’un classement, pas d’une validation du contenu ni d’un filtre qui cache
les documents de prévention lorsqu’on les recherche précisément.

Les pages d’un même PDF sont regroupées. **Autres passages dans ce document**
permet d’ouvrir les autres pages retenues. **Lire le PDF** conserve les illustrations ;
**Texte et assistant** ouvre l’aperçu pour poser une question.

Un article d’encyclopédie peut expliquer un principe sans donner les pièces,
les dimensions et les étapes nécessaires à une fabrication. Ouvrir la source
et vérifier ces éléments avant de la considérer comme un guide de réalisation.
La taille de la bibliothèque ne prouve pas qu’une telle procédure existe.

Le vocabulaire courant est rapproché des expressions techniques françaises et
anglaises : recoudre/couture, vêtement/clothes, conserves/canning, aiguiser/affûtage,
panneau solaire/solar panel. Ces équivalences aident à retrouver un texte déjà
présent ; elles n’ajoutent aucun contenu et ne couvrent pas toutes les formulations.

## Si un document trouvé ne s’ouvre pas

Le lecteur suit les redirections d’un article vers un autre de la même archive
locale, avec une limite de cinq passages et un délai global de 25 secondes.
Il refuse les redirections vers Internet ou un autre service. Les boucles et
erreurs restent signalées. Les images relatives utilisent l’adresse de la cible.

Si l’aperçu échoue, **Réessayer** relance la lecture ; **Ouvrir le document
d’origine** essaie le lecteur Kiwix ou PDF directement, dans un nouvel onglet.
Ce repli ne garantit pas que l’original existe. Copier l’adresse du portail et le
titre pour signaler un échec persistant ; un résultat trouvé n’est pas encore un
document lu. Les couleurs des liens à l’intérieur des archives dépendent aussi
de la source et ne constituent pas un indicateur fiable de disponibilité.

## Comprendre une recherche partielle

Une collection peut répondre lentement, être indisponible ou ne pas permettre
la recherche plein texte. Le portail conserve les autres résultats et affiche
les limites. Les recherches sont bornées pour éviter une attente indéfinie.

La mention d’index dans le catalogue n’est pas une preuve suffisante : les
archives déclarées sans index sont aussi interrogées dans la limite du budget,
après celles dont l’index est annoncé. Des titres sont cherchés séparément dans
un petit nombre d’archives prioritaires. Un résultat trouvé par son titre doit
encore être ouvert pour vérifier son contenu. Les collections restent ouvrables
directement dans **Collections**, même lorsque la recherche est incomplète.

Aucun résultat ne signifie pas que tout le fonds est dépourvu du sujet. Une
page présente sur Wikipédia aujourd’hui peut aussi différer de l’édition locale.
Les [règles de sources](sources-et-fiabilite.md) distinguent trouvé, lu et cité.

## Utiliser l’assistant

Pour les demandes pratiques ou documentaires reconnues, le portail prépare une
recherche et lit jusqu’à deux premières sources avant le premier appel au modèle.
Cela utilise le même classement que la Bibliothèque. Les recherches et lectures
répétées à l’identique sont réutilisées pendant cette réponse. Les outils du modèle
permettent ensuite d’affiner la recherche ou de poursuivre un passage.

La relance « et dans Wikipédia ? » reprend le dernier sujet renseigné par vous
et cible cette collection. Les modèles gardent la possibilité de choisir des
mots différents ; leurs capacités ne deviennent pas identiques. La préparation
n’est pas systématique pour toute forme de question et ne remplace pas les outils
de calcul ou de géographie. Les demandes sur les favoris gardent leur outil dédié.

L’état distingue **Recherche dans la bibliothèque**, **Lecture des documents**,
**Préparation par le modèle** et **Rédaction**, avec les nombres réellement connus.
Préparation peut inclure un chargement du modèle ; ce n’est pas une mesure exacte
de ce chargement. Le mode rapide limite les allers-retours d’outils, mais aucun
délai de réponse n’est garanti sans mesure sur le PC cible. Les extraits et
anciens échanges sont réduits si nécessaire pour préserver le contexte courant,
sans modifier les conversations enregistrées.

## Vérification sur le Windows de Marc, depuis le site

1. Appliquer la [mise à jour habituelle](../exploitation/mises-a-jour-et-bibliotheque-pilote.md),
   puis recharger la page et vérifier **0.5.0** en haut. Un pull du dépôt de maintenance
   seul ne met pas à jour le logiciel installé.
2. Choisir **Famille**, puis **Mon appareil → Réglages → Vérifier la recherche**.
3. Choisir **Contrôle court · 10 recherches** ou **Contrôle complet · 32 recherches**,
   puis lancer. Le contrôle complet peut prendre plusieurs minutes. Ils interrogent les documents réels,
   sans démarrer le modèle, préparer de contenu ni modifier la bibliothèque.
   **Arrêter la vérification** conserve les résultats déjà reçus.
4. Ouvrir les résultats dans leurs onglets et, après lecture, choisir celui qui
   répond réellement au besoin dans le menu sous la recherche. **Aucun de ces résultats**
   et **Je ne peux pas encore juger** restent possibles. Les autres recherches restent
   **À vérifier** ; terminer la mesure ne les valide pas automatiquement.
5. **Télécharger le rapport** conserve la version du serveur, les requêtes, les
   délais et les titres/identifiants des cinq premiers résultats, avec les limites
   signalées. Le contrôle complet ajoute la version de sa liste et les besoins
   visés ; les avis humains et leurs rangs sont conservés séparément des mesures.
   Le rapport ne contient pas l’historique des conversations. Le télécharger avant
   de fermer ou relancer : les avis ne sont pas enregistrés sur le serveur.
6. Lors d’un usage volontaire de l’assistant, comparer une nouvelle question en
   rapide et sa relance sur Wikipédia. Noter quelle étape prend du temps et les
   sources lues. Ne pas lever le mode jeu ni forcer un démarrage pour cette recette.

Louis confirme pouvoir faire ces essais depuis le site avec Marc sur Windows.
Il dispose de TeamViewer pour son propre accès ; aucun accès distant de l’agent
n’est configuré ou testé par cette livraison.

## Indexation et espaces depuis 0.3.0

Choisir Autonomie et résilience, Savoirs et culture ou Toute la bibliothèque. Le classement utilise le texte disponible ; élargir au fonds complet permet de retrouver les documents non classés. La sélection et les filtres figurent dans l’adresse et sont restaurés au retour. Les favoris et traductions gardent leurs sélections personnelles.

Le [guide d’indexation](indexation-archives.md) explique la préparation du texte des ZIM non recherchables et la pause. Le [bilan du rapport de Marc](../essais/2026-11-14-recherche-index-et-espaces.md) distingue les améliorations du moteur de leurs validations sur son fonds.

Famille → Mon appareil → Réglages → Mémoire de l’assistant permet de régler le contexte de chaque modèle : 16k par défaut, 8k pour revenir à une petite allocation, puis 32k et 64k pour les essais. Le contexte ne charge pas toute la bibliothèque et n’augmente pas automatiquement selon la RAM disponible. Un grand contexte peut demander plus de mémoire et de temps ; comparer sur le PC cible avant de conserver le réglage. Ce réglage concerne les conversations ; la traduction par passages conserve son budget propre.

## Diagnostic depuis 0.4.0

Le contrôle court comporte dix recherches, dont « faire du feux » avec Toute la bibliothèque puis Autonomie et résilience, ainsi qu’un diagnostic préalable sans IA. Il distingue Kiwix joignable, catalogue en direct/en cache/ancien/indisponible et les raisons d’échec. L’ancien catalogue utilisé en repli est daté ; sa présence ne prouve pas la disponibilité de toutes les archives. Le diagnostic prépare parfois le cache : son temps est séparé des requêtes suivantes. Depuis 0.5.0, le contrôle complet étend cette recette à 32 demandes versionnées, sans prolonger obligatoirement le contrôle court.

Un avertissement visible précède les résultats incomplets. Une « mention du sujet dans le texte » n’est pas une preuve que le document explique sa réalisation. La couverture porte sur les textes disponibles, pas sur les paroles de vidéos, les scans sans OCR ni la qualité d’une procédure. Voir le [guide d’indexation automatique](indexation-archives.md).
