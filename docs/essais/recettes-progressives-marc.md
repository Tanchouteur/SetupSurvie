# Recettes progressives sur le PC de Marc

**Protocole actuel et suites prévues — 15 novembre 2026.** Louis et Marc testeront au fil des lots.
Ce document ne prouve aucun essai supplémentaire et ne décrit pas des boutons
qui seraient déjà tous livrés. Référence : [plan des lots](../decisions/plan-ameliorations-marc.md).

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
la seule mise à jour en 0.14.0 : mesurer d’abord le flux progressif et le cache avec le
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
| R1 — Préparation des index | Après L1, premier examen puis nouveau petit lot | Téléchargé/vérifié/indexé, fichiers ignorés, temps, volume des index, erreurs, pause et reprise ; relance inchangée sans nouvelle extraction | Terminaison réelle 0.9.3 reçue : 135/135 sans erreur ; pause/reprise et nouveau petit lot restent à vérifier |
| R2 — Recherche et incident | Maintenant avec le bouton existant, puis après L2 et chaque changement important | Requêtes, résultats et couverture ; état Kiwix/catalogue, essais à froid/à chaud, comparaison Toute la bibliothèque / Résilience, requêtes feu et générateur | Rapport 0.12.0 reçu : 32 recherches partielles, 31 échéances atteintes, compléments locaux sans erreur ; correction progressive/cache 0.13.0 à mesurer, avis humains attendus |
| R3 — Collections et utilité | Après L3 puis L7 | Noms compréhensibles, accès direct, type réel du document, présence des étapes/plans/matériel ; signalement des lacunes | Corrections/export en 0.6.0, six dossiers et repères exportables en 0.9.0 ; relecture humaine du fonds attendue |
| R4 — Assistant et matériel | Après L4, à un moment convenu sans autre charge lourde | Modèle/digest, contexte, attente/chargement/recherche/lecture/rédaction, mémoire, erreurs ; comparer 16k/32k et davantage si admis | Comparatif IA 0.9.3 reçu : deux expirations de budget avant premier fragment ; calibration mémoire et phases d’une réponse réelle restent à mesurer |
| R5 — Traduction | Après L5, page puis chapitre puis livre long | Langue, volume, pages, progression/reprise, erreurs de contrôle, durée et relecture de passages choisis ; original et traduction comparables | Traduction par passages existante ; rapport de recette à développer |
| R6 — Vidéos | Inventaire au début de L6, lecture à sa fin | Une ligne par vidéo : piste française récupérée ou créée, couverture, synchronisation/lecture hors ligne, contrôles et relecture ; erreurs et vidéos non traitées visibles | [Protocole cible](protocole-sous-titres-videos.md), précision de Louis du 14 novembre ; inventaire/export et lecteur à développer |
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
