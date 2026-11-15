# Recettes progressives sur le PC de Marc

**Protocole actuel et suites prévues — 15 novembre 2026.** Louis et Marc testeront au fil des lots.
Ce document ne prouve aucun essai supplémentaire et ne décrit pas des boutons
qui seraient déjà tous livrés. Référence : [plan des lots](../decisions/plan-ameliorations-marc.md).

## Prochaine validation assistant — 0.15.1

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
| R4 — Assistant et matériel | Après L4, à un moment convenu sans autre charge lourde | Modèle/digest, contexte, attente/chargement/recherche/lecture/rédaction, mémoire, erreurs ; comparer 16k/32k et davantage si admis | Captures 0.15.0 : synthèse sans source consultée et constat de changement de modèle défaillant. Correctifs 0.15.1 à vérifier avec les mesures de réponse ; calibration distincte et volontaire |
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
