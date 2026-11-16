# Retrouver un document utile

**Guide actuel — portail 0.33.1, 16 novembre 2026.** Les essais de développement
utilisent des documents fictifs et un vrai Kiwix sur de petites archives générées.
La pertinence et les délais sur le fonds de Marc restent à vérifier sur son PC.

Pour examiner une lenteur, le [diagnostic complet](../exploitation/diagnostic-complet-performances.md)
ajouté en 0.22.0 mesure recherche, assistant et ressources depuis un seul bouton
dans Paramètres → Tests et diagnostics → Lenteurs. Le rapport de pertinence ci-dessous
reste distinct : des mesures rapides ne prouvent pas qu’un résultat est utile.

## Chercher dans la bibliothèque

Dans **Bibliothèque → Rechercher**, décrire le besoin : « allumer un feu »,
« fabriquer un générateur à pédales », « rendre eau potable » ou « réparer un vélo ».
Le choix de langue permet de chercher en français et en anglais. Le sélecteur
**Toutes les collections** permet aussi de cibler une source installée, par exemple
Wikipédia. Ce choix reste dans l’adresse pour le rechargement et Précédent/Suivant.
Le rechargement relance une seule fois la recherche mémorisée avec ses filtres.
Une formule comme « faire du feu dans Wikipédia » peut également cibler cette source.

**« Recherche en cours — aucun résultat pour le moment »** signifie que les
collections sont encore interrogées. Ce n'est pas une conclusion d'absence de
document. Les résultats arrivent progressivement ; on peut déjà les lire.
La fin est annoncée explicitement : recherche terminée, ou terminée mais incomplète
si certaines sources n'ont pas pu être interrogées. Un arrêt ou une erreur conserve
les résultats reçus et retire le message d'attente, même si la liste est encore vide.

La recherche fonctionne sans modèle IA. Elle combine titres, texte des guides,
articles Kiwix, variantes techniques françaises et anglaises et recherches plus
courtes lorsque la première formulation ne trouve rien. Le classement privilégie
le sujet du titre et du passage ; pour une demande pratique, les mentions de quiz,
d’histoire ou de prévention seules passent après les correspondances plus directes.
Les titres de guide, de manuel, de bricolage « DIY… » et les formulations « comment… » peuvent mieux
orienter une demande pratique ; les questions sur un détail et les aperçus de
risques restent accessibles. Un titre bien classé ne garantit pas des instructions
complètes. Une demande générale identique à un titre conserve aussi ses mots de
liaison pour la correspondance exacte, par exemple « Histoire du vélo ».

Depuis 0.33.1, une demande d’action telle que « réparer un vélo » privilégie les
titres pratiques devant les aperçus de prix ou de tarifs. Les documents de prix
restent recherchables ; « prix de réparation d’un vélo » peut donc les placer en
premier. Une formulation expliquant « comment… » peut aussi parler de coût : elle
ne devient pas automatiquement un simple tarif. Les actions courtes reconnues,
comme « filtrer l’eau » ou « affûtage d’un couteau », gardent leur intention sans
exiger « comment » au début. Cela reste un indice de classement ; ouvrir le texte
pour vérifier qu’il contient bien les étapes cherchées.

Depuis 0.15.1, une demande explicite comme « Fais une synthèse des documents sur
comment faire du feu » garde le sujet recherché : elle n’exige plus qu’un article
contienne aussi les mots « synthèse » ou « info ». Les vrais sujets « synthèse
chimique » restent recherchables. Cette correction ne crée pas automatiquement
une synthèse de plusieurs livres ; le [parcours assistant](../decisions/assistant-recherche-et-synthese.md)
est développé séparément de la recherche sans IA.
Il s’agit d’un classement, pas d’une validation du contenu ni d’un filtre qui cache
les documents de prévention lorsqu’on les recherche précisément. Les extraits
natifs conservent depuis 0.13.1 les mots surlignés et le texte qui les suit ; ils
ne sont plus coupés au premier mot en gras de la réponse Kiwix.

Depuis 0.13.1, pour une tâche pratique, un titre qui associe le sujet recherché
et l’action demandée passe plus facilement devant un texte général qui ne fait
que mentionner cette action. Les textes généraux restent consultables. Une demande
« pourquoi » cherche une explication, tandis que « pourquoi et comment » conserve
son intention pratique. Ce repère ne certifie pas qu’un article contient toutes
les étapes, ni qu’il constitue une procédure vérifiée.


Depuis 0.9.4, une demande pratique écarte les correspondances dont l’action
n’est pas étayée, notamment un exercice de prix de vélo proposé pour une réparation.
Les collections spécialisées et les reformulations utiles sont interrogées tôt.
Depuis 0.13.0, les premiers documents apparaissent pendant la recherche et restent
consultables. **Arrêter la recherche** conserve ce qui a déjà été reçu. La phase
native peut durer jusqu’à 60 secondes ; les autres préparations peuvent s’ajouter.
Le [guide de recherche progressive et du cache](../exploitation/cache-et-recherche-progressive.md)
précise les délais, la réutilisation et les réglages de taille. Un avertissement de couverture
partielle reste significatif, même si des documents utiles ont déjà été trouvés.

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
document lu. Depuis 0.13.1, les suggestions contenant des apostrophes ou des
esperluettes sont décodées avant de construire leur lien. Si une ancienne référence
reste indisponible, relancer la recherche pour obtenir le lien corrigé. Cette
correction ne garantit pas l’ouverture de toute archive ou source manquante. Les couleurs des liens à l’intérieur des archives dépendent aussi
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
   puis recharger la page et vérifier **0.15.1** en haut. Un pull du dépôt de maintenance
   seul ne met pas à jour le logiciel installé.
2. Choisir **Famille**, puis **Mon appareil → Paramètres → Tests et diagnostics → Recherche → Vérifier la recherche**.
3. Choisir **Contrôle court · 10 recherches** ou **Contrôle complet · 32 recherches**,
   puis lancer. Les résultats arrivent progressivement ; le contrôle attend au maximum
   90 secondes par demande. Le contrôle complet peut prendre plusieurs dizaines de minutes. Ils interrogent les documents réels,
   sans démarrer le modèle, préparer de contenu ni modifier la bibliothèque.
   **Arrêter la vérification** conserve les résultats déjà reçus.
4. Ouvrir les résultats dans leurs onglets et, après lecture, choisir celui qui
   répond réellement au besoin dans le menu sous la recherche. **Aucun de ces résultats**
   et **Je ne peux pas encore juger** restent possibles. Les autres recherches restent
   **À vérifier** ; terminer la mesure ne les valide pas automatiquement.
5. **Télécharger le rapport** conserve la version du serveur, les requêtes, les
   délais et les titres/identifiants des cinq premiers résultats, avec les limites
   signalées. Depuis 0.13.0, le délai des premiers documents reçus et le nombre de
   mises à jour progressives sont séparés de la durée finale ; aucun premier résultat
   reste une valeur vide. Le contrôle complet ajoute la version de sa liste et les besoins
   visés ; les avis humains et leurs rangs sont conservés séparément des mesures.
   Le rapport ne contient pas l’historique des conversations. Le télécharger avant
   de fermer ou relancer : les avis ne sont pas enregistrés sur le serveur.

   Depuis 0.11.1, ce contrôle demande les détails des appels : collections,
   langues annoncées, formulation, délai client, cache, nombre de résultats,
   taille de réponse et cause catégorielle d’erreur. Le journal est borné à
   quarante appels par demande, sans texte brut de réponse d’erreur. Le délai
   comprend l’attente ; il ne mesure pas le CPU ou le temps interne de Kiwix.
   La recherche habituelle et les outils de l’assistant ne demandent pas ces
   détails. Les compléments d’index restant à préparer sont identifiés séparément.

   Depuis 0.14.1, le rapport conserve aussi `coverage.processing` : temps de
   sélection, CPU des threads de sélection et réemplois des textes/métadonnées.
   Ces mesures servent au diagnostic ; elles ne mesurent pas le CPU de Kiwix ni
   l’activité du disque. Leur [définition](../exploitation/cache-et-recherche-progressive.md#traitement-des-résultats-et-mesures--depuis-0141)
   permet de comparer les rapports sans confondre appel rapide et recherche rapide.
6. Lors d’un usage volontaire de l’assistant, comparer une nouvelle question en
   rapide et sa relance sur Wikipédia. Noter quelle étape prend du temps et les
   sources lues. Ne pas lever le mode jeu ni forcer un démarrage pour cette recette.

Louis confirme pouvoir faire ces essais depuis le site avec Marc sur Windows.
Il dispose de TeamViewer pour son propre accès ; aucun accès distant de l’agent
n’est configuré ou testé par cette livraison.

## Indexation et espaces depuis 0.3.0

Choisir Autonomie et résilience, Savoirs et culture ou Toute la bibliothèque. Le classement utilise le texte disponible ; élargir au fonds complet permet de retrouver les documents non classés. La sélection et les filtres figurent dans l’adresse et sont restaurés au retour. Les favoris et traductions gardent leurs sélections personnelles.

Depuis 0.6.0, le profil Famille peut [corriger ces espaces et le type du document](classement-et-collections.md),
ainsi que les noms des collections. Une correction humaine conservée prime sur
l’indication automatique pour la même révision ; le document reste toujours dans
la bibliothèque globale. Les types de procédure/notice ne sont pas devinés sur
le seul titre et ne constituent pas une validation de sécurité.

Le [guide d’indexation](indexation-archives.md) explique la préparation du texte des ZIM non recherchables et la pause. Le [bilan du rapport de Marc](../essais/2026-11-14-recherche-index-et-espaces.md) distingue les améliorations du moteur de leurs validations sur son fonds.

Famille → Mon appareil → Paramètres → Assistant → Options avancées : mémoire et essai du modèle → Mémoire de l’assistant permet de régler le contexte de chaque modèle : 16k par défaut, 8k pour revenir à une petite allocation, puis 32k et 64k pour les essais. Le contexte ne charge pas toute la bibliothèque et n’augmente pas automatiquement selon la RAM disponible. Un grand contexte peut demander plus de mémoire et de temps ; comparer sur le PC cible avant de conserver le réglage. Ce réglage concerne les conversations ; la traduction par passages conserve son budget propre.

Depuis 0.7.0, **Voir les durées** permet de distinguer recherche, lecture et modèle.
L’[essai mémoire volontaire](mesurer-assistant-et-memoire.md) prépare une proposition
par paliers, sans remplacer automatiquement le réglage courant. Il respecte la
pause, les réserves et les demandes prioritaires ; R4 réel reste à exécuter.

## Diagnostic depuis 0.4.0

Le contrôle court comporte dix recherches, dont « faire du feux » avec Toute la bibliothèque puis Autonomie et résilience, ainsi qu’un diagnostic préalable sans IA. Il distingue Kiwix joignable, catalogue en direct/en cache/ancien/indisponible et les raisons d’échec. L’ancien catalogue utilisé en repli est daté ; sa présence ne prouve pas la disponibilité de toutes les archives. Le diagnostic prépare parfois le cache : son temps est séparé des requêtes suivantes. Depuis 0.5.0, le contrôle complet étend cette recette à 32 demandes versionnées, sans prolonger obligatoirement le contrôle court.

Un avertissement visible précède les résultats incomplets. Une « mention du sujet dans le texte » n’est pas une preuve que le document explique sa réalisation. La couverture porte sur les textes disponibles, pas sur les paroles de vidéos, les scans sans OCR ni la qualité d’une procédure. Voir le [guide d’indexation automatique](indexation-archives.md).

## Comparatif facultatif depuis 0.8.0

Famille peut [comparer une aide IA à la recherche](comparer-recherche-ia.md),
avec reformulations bilingues, reclassement et relecture humaine. Cette expérience
n’ajoute aucun appel au modèle dans la recherche habituelle ; l’intégration reste
reportée jusqu’à une mesure réelle favorable et répétée.

## Un objectif pratique depuis 0.9.0

Dans **Apprendre par thème**, les [six dossiers pratiques](dossiers-pratiques.md)
sont des raccourcis facultatifs vers quelques objectifs et leurs pages ou sections
réellement examinées. Ils ne limitent ni le fonds ni les sujets de recherche. Chaque
point sans référence reste explicitement à documenter. Les repères ne remplacent
ni la lecture de l’original ni la qualification du fonds réel.

## Replis et erreurs depuis 0.9.1

Les résultats élargis sur une partie des mots doivent couvrir au moins deux tiers
des concepts de la demande. Les résultats natifs complets peuvent rester sans
extrait ; le document doit être ouvert pour vérifier son contenu. Un quiz n’est
pas proposé pour réaliser une tâche pratique, sauf s’il est explicitement demandé.
Les termes crevaison, fuite et filtration relient aussi français et anglais.

Les requêtes Kiwix partagent deux voies pour le texte et deux pour les titres,
même avec plusieurs recherches en cours. Le rapport conserve les causes bornées
(délai, HTTP, connexion ou format), les collections et la limite de temps atteinte.
Depuis 0.13.0, seules les réponses réussies et valides sont réutilisées cinq minutes
en mémoire et jusqu’à 24 heures sur disque pour le même état de la bibliothèque,
avec un compteur explicite. Un timeout ou une surcharge ne provoque plus une
multiplication de sous-requêtes. Les CPU de l’indexation restent réglables séparément.

Les [rapports réels 0.8.0](../essais/2026-11-14-rapports-recherche-080.md) ont déclenché
ces corrections. Leur cause finale et le gain sur le fonds Windows restent à
vérifier avec de nouveaux rapports ; un résultat partiel n’est pas une preuve d’absence.

## Outils complémentaires — 0.14.0

Le [diagnostic de performances Kiwix](../exploitation/diagnostic-performances-kiwix.md)
mesure une archive choisie et sa répétition, sans IA, en séparant premier résultat,
fin, cache et couverture. Il ne supprime pas les caches et ne prouve pas un départ
à froid. L’[inventaire vidéo](inventaire-videos.md) recense médias et pistes locales
sans modifier les fichiers. Il prépare le futur index vidéo ; il ne rend pas encore
les paroles recherchables et ne crée pas de sous-titres. Les guides donnent les
commandes Windows/Linux et les limites des rapports.
