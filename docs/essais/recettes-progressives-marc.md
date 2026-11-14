# Recettes progressives sur le PC de Marc

**Protocole actuel et suites prévues — 14 novembre 2026.** Louis et Marc testeront au fil des lots.
Ce document ne prouve aucun essai supplémentaire et ne décrit pas des boutons
qui seraient déjà tous livrés. Référence : [plan des lots](../decisions/plan-ameliorations-marc.md).

## Ce qui est utilisable maintenant

Depuis 0.3.0 : **Famille → Mon appareil → Réglages → Vérifier la recherche**, puis
**Télécharger le rapport**. Depuis 0.4.0, les dix recherches n’appellent aucun modèle et le
rapport exporte version, délais, couverture, résultats et extraits. Pour les ZIM
sans index réel, la [création/reprise manuelle](../utilisation/indexation-archives.md)
est disponible au même endroit. Ces deux opérations sont distinctes.

Depuis 0.5.0, **Contrôle complet · 32 recherches** élargit R2. Après lecture,
choisir les résultats utiles ou indiquer qu’aucun ne répond ; laisser les autres
à vérifier puis exporter. La [procédure actuelle](../utilisation/recherche-documentaire.md#vérification-sur-le-windows-de-marc-depuis-le-site)
distingue mesures et avis humains. Aucun résultat fictif n’est attendu sur le PC réel.

Les futurs diagnostics ci-dessous doivent être livrés avec une commande ou un
bouton explicite, un arrêt possible et un export JSON lisible par l’agent. Ne pas
exiger TeamViewer ni un accès distant de développement pour lancer les recettes.

## Rapports à fournir progressivement

| Rapport | Quand le demander | Ce qu’il doit mesurer | État de l’outil |
| --- | --- | --- | --- |
| R1 — Préparation des index | Après L1, premier examen puis nouveau petit lot | Téléchargé/vérifié/indexé, fichiers ignorés, temps, volume des index, erreurs, pause et reprise ; relance inchangée sans nouvelle extraction | Rapport d’indexation disponible en 0.4.0 |
| R2 — Recherche et incident | Maintenant avec le bouton existant, puis après L2 et chaque changement important | Requêtes, résultats et couverture ; état Kiwix/catalogue, essais à froid/à chaud, comparaison Toute la bibliothèque / Résilience, requêtes feu et générateur | Dix cas courts et diagnostic depuis 0.4.0 ; 32 cas versionnés et avis humains exportables en 0.5.0 ; mesure du fonds réel attendue |
| R3 — Collections et utilité | Après L3 puis L7 | Noms compréhensibles, accès direct, type réel du document, présence des étapes/plans/matériel ; signalement des lacunes | Corrections et export de métadonnées disponibles en 0.6.0 ; relecture humaine du fonds attendue |
| R4 — Assistant et matériel | Après L4, à un moment convenu sans autre charge lourde | Modèle/digest, contexte, attente/chargement/recherche/lecture/rédaction, mémoire, erreurs ; comparer 16k/32k et davantage si admis | Réglages et certaines traces existent ; rapport et calibration à développer |
| R5 — Traduction | Après L5, page puis chapitre puis livre long | Langue, volume, pages, progression/reprise, erreurs de contrôle, durée et relecture de passages choisis ; original et traduction comparables | Traduction par passages existante ; rapport de recette à développer |
| R6 — Vidéos | Inventaire au début de L6, lecture à sa fin | Pistes réellement présentes, langues, lecture, décalage, petits extraits reconnus/traduits et erreurs ; aucune copie automatique de la vidéo complète | Inventaire/export et lecteur à développer |
| R7 — Usage hors ligne | À chaque livraison pertinente, puis L9 | Navigation, données conservées, fonctions avec IA arrêtée et Internet coupé, reprise, téléphone ; chaque vérification marquée exécutée ou non | Scénario intégré/export à développer |

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
