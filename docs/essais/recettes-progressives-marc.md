# Recettes progressives sur le PC de Marc

**Protocole actuel et suites prévues — 16 novembre 2026.** Louis et Marc testeront au fil des lots.
Ce document ne prouve aucun essai supplémentaire et ne décrit pas des boutons
qui seraient déjà tous livrés. Référence : [plan des lots](../decisions/plan-ameliorations-marc.md).

## Prochaine validation ciblée — 0.33.0

Après la mise à jour habituelle, choisir une collection connue contenant des
vidéos. Dans **Bibliothèque → Collections → Vidéos de la bibliothèque → Vidéos
dans les collections**, lancer **Examiner ou reprendre les collections**. L’outil
d’archives doit déjà être préparé dans **Paramètres → Bibliothèque**. Attendre la
fin de l’examen puis celle de la mise à jour du lecteur, ou mettre en pause et
reprendre à votre convenance. Télécharger le rapport des collections en cas
d’interruption ; les index texte déjà existants ne remplacent pas cet examen.

Lire une vidéo incluse et vérifier un passage d’une piste existante. Rechercher
un mot de ces paroles, confirmer l’horodatage et l’ouverture de l’article d’origine.
Sur une piste non française, essayer une courte préparation française puis
comparer le texte et les temps. Une vidéo seulement liée à Internet ou un lecteur
JavaScript peut rester non couvert ; la transcription audio des médias internes
n’est pas encore raccordée. Un titre trouvé ne prouve pas la connaissance des paroles.

Les contrôles assistant/traduction documentaire de la recette précédente restent
utiles au fil de l’usage. Inutile de refaire un R2 ou tous les benchmarks pour
chaque vidéo. Cette procédure n’annonce aucun nouvel essai réalisé sur Marc.

## Prochaine validation ciblée — 0.32.0

**Étape précédente conservée.** Le parcours 0.33.0 ci-dessus complète maintenant
les vidéos ZIM ; les limites de la 0.32.0 ci-dessous décrivent cette version antérieure.

La recherche classique, l’indexation, les lectures et les modèles disposent déjà
de rapports ; le R2 0.25.0 n’a aucun avis humain de pertinence et garde une couverture
partielle. Les essais R7 0.32.0 complètent les petits corpus et un chapitre réel,
sans remplacer le PC Windows de Marc. Inutile de relancer tous les diagnostics
ou une indexation complète pour chacun des contrôles suivants.

1. Après mise à jour habituelle, choisir deux ou trois documents connus et utiles,
   puis demander une comparaison. Ouvrir une référence et confirmer qu’elle soutient
   réellement une information de la réponse. Une source sélectionnée n’est pas
   automatiquement une source lue, ni un livre entier.
2. Après cette réponse, passer à un mode utilisant un autre modèle et poser une
   petite question. La première demande doit aboutir sans renvoi manuel. En cas
   d’erreur, noter l’heure et le mode puis exporter **Voir les durées** si disponible.
   Dans **Paramètres → Entretien et diagnostics → Tests et diagnostics → Mémoire
   et contexte**, **Télécharger le diagnostic de démarrage** fournit l’état actuel
   en lecture seule. Les refus enregistrés de tests sont distincts de cette demande
   réelle : le diagnostic ne reconstitue pas un échec ancien de conversation.
3. Sur un document familier, traduire quelques pages avec un ou deux mots choisis
   facultativement, mettre en pause puis reprendre. Comparer début, milieu et fin,
   chiffres, noms de touches et avertissements à l’original. Exporter les passages
   si une erreur de sens est repérée ; les contrôles limités ne certifient pas la fidélité.
4. Pour les MP4 présents dans `library/video/`, actualiser les vidéos depuis les
   Collections. Utiliser une piste existante, la récupération YouTube avec Internet
   ou la création depuis l’audio déjà préparée. Lire quelques passages et contrôler
   mots/temps/français, puis retrouver un mot des paroles dans la recherche. Les
   vidéos des ZIM ne sont pas encore couvertes par ce parcours.

Ces contrôles se font au fil de l’usage, pas tous en même temps. Garder le mode
jeu et ne lancer une préparation d’IA qu’au moment souhaité. Le déplacement réel
vers SSD, la restauration complète sans source et la refonte générale appartiennent
aux prochains objectifs documentés ; ils ne sont pas déclarés exécutés ici.
Le [guide des rapports](../utilisation/mesurer-assistant-et-memoire.md) et le
[guide vidéo](../utilisation/videos-locales.md) portent les commandes actuelles.

## Validation assistant — 0.17.0 (historique)

**Étape conservée avec sa date ; les recettes 0.33.0 et 0.32.0 ci-dessus portent la suite.**

Le dossier multi-source et sa sélection manuelle sont livrés. Les [essais R7](2026-11-15-synthese-multi-sources-et-essais-reels.md)
confirment des lectures multiples et le changement de modèle sur de petits textes
fictifs ; ils ne remplacent pas le Windows de Marc. Le développement peut continuer
sans nouveau R2 complet. Lors d’un usage volontaire après la mise à jour habituelle :

1. Dans la Bibliothèque, choisir deux ou trois documents utiles avec **Choisir
   pour l’assistant**, puis **Poser une question**. Demander une comparaison,
   ouvrir une référence et recharger la conversation : la liste doit être conservée.
   Pour un PDF, vérifier la page effectivement lue ; un livre choisi n’est pas
   annoncé comme entièrement lu. Retirer une source doit conserver les messages.
2. Demander une synthèse sur un sujet connu du fonds, par exemple la formulation
   réelle de Marc sur le feu, puis « Compare les méthodes et cite les documents ».
   Vérifier quelles sources sont réellement lues, ouvrir un passage et noter une
   affirmation correctement soutenue ou une extrapolation. Plusieurs sources sont
   possibles, sans exiger cinq si le fonds utile ou le contexte en fournissent moins.
3. Après une réponse, changer pour un mode utilisant un autre modèle, puis poser
   une petite question. La première demande doit aboutir sans la renvoyer à la main.
4. Exporter **Voir les durées → Télécharger le rapport** pour un cas lent, incomplet
   ou faux. Préciser le texte de la demande, le mode et la source mal utilisée :
   le rapport numérique ne contient pas ces textes. Documents préparés, lectures,
   reprises et liaison des références sont mesurés séparément.

Prévoir plusieurs minutes possibles par question selon le modèle et le contexte ;
le plafond est quinze minutes, l’annulation reste disponible. Ne pas lever le mode
jeu ni lancer de réindexation ou calibration pour ce contrôle. Illustrations et
longues synthèses intermédiaires restent à développer. La fidélité de chaque conclusion reste un critère humain, même si les références sont présentes.

## Prochaine validation assistant — 0.15.1

**Recette historique ; le protocole 0.17.0 ci-dessus est la suite actuelle.**

Le R2 **0.15.0 est reçu** : les 32 recherches sont complètes, médiane finale
2,11 s avec cache déjà chaud. Ne pas le refaire immédiatement pour poursuivre
le développement. Les avis humains et la validation de l’assistant restent distincts.

Après mise à jour habituelle en **0.15.1**, lors d’un usage volontaire de l’IA :

1. Demander **« Fait un synthese sur les info des document sur comment faire du
   feux »**, puis **« Des méthodes d’allumage au frottement (comme le feu de bois) ? »**
   et **« Et dans Wikipédia ? »**. Vérifier les sources réellement consultées,
   ouvrir une source et dire si la réponse s’en sert correctement.
2. Après une réponse terminée, choisir un autre mode utilisant un autre modèle et
   poser une petite question. Le chargement/changement doit être indiqué et la
   réponse doit arriver sans renvoi manuel. Alterner ensuite dans l’autre sens.
   Si le modèle est déjà chargé, le changement peut ne pas être nécessaire.
3. Exporter **Voir les durées → Télécharger le rapport** pour les demandes lentes,
   sans réponse finale ou avec erreur. Signaler modèle/mode, résultat observé et
   état des sources. Les nouvelles mesures de préparation/reprise du modèle sont
   incluses ; le rapport ne contient pas le texte de la conversation.

Ne pas lever le mode jeu, lancer de calibration ou réindexer tout le fonds pour
ces essais. Une synthèse de cinq documents, la sélection manuelle de plusieurs
sources et les schémas restent la suite à développer, pas la promesse de ce correctif.
Relire progressivement les résultats du R2 déjà reçu (feu, eau, pédales, vélo,
radio, solaire) ; les avis non donnés restent inconnus.

## Prochaine validation ciblée — 0.15.0

**Recette historique : le R2 demandé ci-dessous est maintenant reçu.** Pour la
suite, utiliser les étapes assistant ci-dessus ; conserver ce protocole pour un
prochain changement important du moteur et les contrôles hors ligne distincts.


Faire ces étapes progressivement, sans tout lancer en même temps. La
[clôture actuelle](2026-11-15-audit-recherche-0150.md) distingue ce qui est déjà
testé et ce qui nécessite le PC de Marc.

1. Appliquer la mise à jour habituelle et vérifier **0.15.0**. Avec **Famille**,
   aller dans **Mon appareil → Paramètres → Entretien et diagnostics → Vérifier
   la recherche → Contrôle complet · 32 recherches**. Ce R2 ne lance pas l’IA et
   n’exige pas de réindexation intégrale pour ces corrections. Il attend au plus
   90 secondes par demande ; réserver jusqu’à une cinquantaine de minutes au
   maximum théorique pour les 32, généralement moins. On peut arrêter et exporter.
2. Ouvrir les premiers résultats de **feu, eau potable, générateur à pédales,
   réparation vélo**, puis **radio et installation solaire** qui avaient un tri
   discutable. Noter seulement ce qui a été lu avec le menu d’avis ; les autres
   restent à vérifier. Donner le titre et l’adresse complète après clic si un
   document ne s’ouvre pas. **Télécharger le rapport** avant fermeture. Si les
   six demandes ne peuvent pas toutes être relues, retourner les avis déjà faits
   et préciser le reste ; aucun taux de pertinence global n’en est déduit.
3. À un autre moment, quand l’IA peut être utilisée volontairement, demander
   **« Comment faire du feu ? »**, puis **« Et dans Wikipédia ? »**. Examiner la
   ligne de suivi documentaire et ouvrir une source. Le nombre trouvé, la lecture
   et la citation restent distincts. Exporter **Voir les durées → Télécharger le
   rapport**, selon le [guide assistant](../utilisation/mesurer-assistant-et-memoire.md).
   Préciser si la réponse utilise réellement le document ; le rapport numérique
   ne contient pas son texte. Ne pas lancer de calibration mémoire ou lever le
   mode jeu pour ce seul essai. La durée d’une réponse réelle reste inconnue.
4. Quand cela est pratique, faire R7 avec **Vérifier l’usage hors ligne → Tester
   l’usage hors ligne**, au même endroit. Suivre le [guide](../utilisation/verifier-usage-hors-ligne.md)
   pour conserver le réseau local, arrêter l’IA et déclarer la coupure Internet.
   Marquer uniquement les étapes effectuées puis exporter le rapport d’usage.

R2 avec avis humains est le premier retour nécessaire pour juger les dernières
corrections. R4 mesure le vrai modèle, R7 l’usage effectivement hors ligne. Une
mesure encore partielle ne prouve pas une panne matérielle : comparer couverture,
premiers documents, fin, appels natifs et `processing`. Les cas ralentis peuvent
ensuite faire l’objet du [diagnostic ciblé](../exploitation/diagnostic-performances-kiwix.md),
sans effacer les caches ni prétendre à un départ froid non établi.

## Ce qui est utilisable maintenant

Le contrôle de recherche est disponible depuis 0.3.0. Le chemin actuel est
**Famille → Mon appareil → Paramètres → Entretien et diagnostics → Vérifier la recherche**,
puis **Télécharger le rapport**. Les recherches de ce contrôle n’appellent aucun
modèle ; le rapport exporte version, délais, couverture, résultats et extraits.
La [création/reprise des index](../utilisation/indexation-archives.md) est une
opération distincte, dans **Paramètres → Bibliothèque et préparations → Préparer
la recherche dans les archives**.

Depuis 0.5.0, **Contrôle complet · 32 recherches** élargit R2. Après lecture,
choisir les résultats utiles ou indiquer qu’aucun ne répond ; laisser les autres
à vérifier puis exporter. La [procédure actuelle](../utilisation/recherche-documentaire.md#vérification-sur-le-windows-de-marc-depuis-le-site)
distingue mesures et avis humains. Aucun résultat fictif n’est attendu sur le PC réel.

Depuis 0.11.1, ce même contrôle exporte aussi les détails des appels et les
compléments d’index manquants. Le rapport 0.12.0 confirme maintenant les 135 archives
examinées, dont 15 compléments locaux prêts. Ne pas refaire cette extraction pour
la seule mise à jour en 0.15.0 : mesurer d’abord le flux progressif et le cache avec le
contrôle complet. Il peut attendre 90 secondes par demande et reste annulable.
Une autre préparation est nécessaire si un contenu ou son édition change.

Depuis 0.8.0, le [comparatif facultatif IA](../utilisation/comparer-recherche-ia.md)
prépare la décision L8 avec trois méthodes, huit ou 32 demandes et avis humains
conservés. Il charge explicitement un modèle local ; le contrôle sans IA reste
distinct. Exporter ce rapport après relecture pour compléter R2/R4.

Les futurs diagnostics ci-dessous doivent être livrés avec une commande ou un
bouton explicite, un arrêt possible et un export JSON lisible par l’agent. Ne pas
exiger TeamViewer ni un accès distant de développement pour lancer les recettes.

Depuis 0.10.0, **Tester l’usage hors ligne** au même endroit fournit R7 :
[mesures sans IA et étapes humaines](../utilisation/verifier-usage-hors-ligne.md).
Arrêt et export sont disponibles ; les étapes non faites restent non effectuées.

## Rapports à fournir progressivement

| Rapport | Quand le demander | Ce qu’il doit mesurer | État de l’outil |
| --- | --- | --- | --- |
| R1 — Préparation des index | Après L1, premier examen puis nouveau petit lot | Téléchargé/vérifié/indexé, fichiers ignorés, temps, volume des index, erreurs, pause et reprise ; relance inchangée sans nouvelle extraction | R1 0.12.0 et état 0.14.0 : 135 archives, 120 index natifs et 15 compléments prêts ; pause/reprise et nouveau petit lot restent à vérifier |
| R2 — Recherche et incident | Maintenant avec le bouton existant, puis après L2 et chaque changement important | Requêtes, résultats et couverture ; état Kiwix/catalogue, répétitions, comparaison Toute la bibliothèque / Résilience, requêtes feu et générateur ; un départ froid doit être établi séparément | Rapport 0.15.0 reçu : 32 recherches complètes, première réception médiane 268 ms, fin 2,11 s avec cache largement chaud ; avis humains attendus |
| R3 — Collections et utilité | Après L3 puis L7 | Noms compréhensibles, accès direct, type réel du document, présence des étapes/plans/matériel ; signalement des lacunes | Corrections/export en 0.6.0, six dossiers et repères exportables en 0.9.0 ; relecture humaine du fonds attendue |
| R4 — Assistant et matériel | Après L4, à un moment convenu sans autre charge lourde | Modèle/digest, contexte, attente/chargement/recherche/lecture/rédaction, mémoire, erreurs ; comparer 16k/32k et davantage si admis | Captures 0.15.0 : synthèse sans source consultée et constat de changement de modèle défaillant. Dossier 0.16.0 et essais R7 réalisés sur corpus fictif ; contrôle Windows ci-dessus encore à faire. Calibration distincte et volontaire |
| R5 — Traduction | Après L5, page puis chapitre puis livre long | Langue, volume, pages, progression/reprise, erreurs de contrôle, durée et relecture de passages choisis ; original et traduction comparables | Traduction par passages existante ; rapport de recette à développer |
| R6 — Vidéos | Inventaire au début de L6, lecture à sa fin | Une ligne par vidéo : piste française récupérée ou créée, couverture, synchronisation/lecture hors ligne, contrôles et relecture ; erreurs et vidéos non traitées visibles | [Inventaire/export local](../utilisation/inventaire-videos.md) livré en 0.14.0 ; recette réelle et traitements/lecteur du [protocole cible](protocole-sous-titres-videos.md) restent à faire |
| R7 — Usage hors ligne | À chaque livraison pertinente, puis L9 | Navigation, données conservées, fonctions avec IA arrêtée et Internet coupé, reprise, téléphone ; chaque vérification marquée exécutée ou non | Recette et export en 0.10.0 ; rapport réel attendu, état IA mesuré et coupure Internet déclarée restent distincts |

Les recettes longues annoncent leur charge et leur possibilité de pause avant
lancement. Aucun mode jeu n’est levé pour un test. La calibration et la traduction
réelles demandent une action explicite ; les rapports de recherche n’en lancent pas.
Les rapports n’incluent ni secrets, conversations complètes ni fichiers personnels.
Une relecture peut être retournée comme réponse textuelle ; un export ne certifie
pas automatiquement que le document trouvé est bon.

## Incident du 14 novembre : recherche feu intermittente

Louis transmet deux captures après la 0.3.0. Première recherche « faire du feux »,
filtre Autonomie et résilience : guides secondaires et message indiquant que les
encyclopédies n’ont pas pu être interrogées. Il confirme que Wikipédia s’ouvre
par Collections, puis que la recherche globale et un nouvel essai **avec le filtre**
retrouvent les documents pertinents. La seconde capture montre notamment
« Techniques de production de feu » (Wikipédia) et « Guide de survie/Faire du feu »
(Wikilivres), mais conserve un avertissement de recherche partielle et 64 collections
n’annonçant pas d’index texte.

Ces observations confirment une réussite réelle avec filtre et un échec temporaire
d’accès lors du premier essai. Elles ne permettent pas d’identifier sa cause,
d’affirmer que le filtre exclut Wikipédia, ni d’attribuer le défaut à une archive
absente ou au seul manque d’indexation. Aucun nouveau fonds n’est ajouté pour
masquer cet incident. L2 doit conserver les raisons techniques dans R2.

Si l’incident revient avant cet outil : exporter **Vérifier la recherche**, noter
la version, l’heure, le mode de recherche, si Wikipédia s’ouvre directement et si
une relance suffit. L’agent doit distinguer cette observation de la reconstitution
simulée dans le runner ; le rapport ne remplace pas les journaux d’état manquants.

## Quand un test devient bloquant

L’agent doit préciser le lot et la décision bloqués, la raison, les étapes exactes,
la charge/durée estimée ou inconnue, le fichier à retourner et les travaux qui
continuent en parallèle logique. Il ne demande pas de tout tester d’un seul coup.

Une absence de rapport ne bloque pas le développement d’une interface, sa reprise
ou ses tests simulés. Elle peut bloquer un réglage automatique de mémoire, une
conclusion de performance, l’intégration d’un format réel non accessible ou une
validation linguistique. Les derniers réglages mesurés et fonctions stables restent
proposés ; les états non validés sont annoncés comme tels.
