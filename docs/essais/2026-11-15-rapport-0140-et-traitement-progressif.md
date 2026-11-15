# Rapport réel 0.14.0 et coût du traitement progressif

**Suite :** la [0.14.2](2026-11-15-budget-reformulations.md) adapte ensuite le
plafond des reformulations du flux long. Les budgets conservés décrits ici
correspondent au correctif 0.14.1, pas à une promesse sur les versions suivantes.

**Bilan daté — 15 novembre 2026 ; correction 0.14.1.** Le rapport de Louis est
analysé avant modification du moteur. Les mesures du PC de Marc et les essais
synthétiques du runner ci-dessous restent distincts. Aucun modèle, gros corpus
ou carte n’est téléchargé ; aucune connexion distante au PC de Marc n’est supposée.

## Rapport reçu

Export sans IA 0.14.0, créé le **15 novembre à 07:49:29 UTC**, 943 472 octets,
empreinte SHA-256 `0fe2b0bede9489f78b049a4df152d2264338ae44f6e142059c60442eaeb55acf`.
Le JSON brut reste privé. Les 32 recherches sont terminées ; aucun avis humain
n’est enregistré : zéro résultat déclaré utile ne signifie pas zéro résultat utile.

| Mesure | Constat sur le PC réel |
| --- | --- |
| Préparation | 135 archives, 120 index natifs et 15 compléments locaux ; 3 238 articles locaux |
| Premiers documents | Médiane **311 ms** sur les 31 cas avec résultat ; 27 arrivent avant une seconde |
| Fin de recherche | Médiane **36 239,5 ms**, minimum 2 444, maximum 47 231 |
| Couverture | Neuf recherches complètes, 23 partielles ; toutes les collections sélectionnées sont tentées dans les 32 cas |
| Plein texte principal | Toutes les collections sélectionnées réussissent dans 31 cas ; un lot de 12 archives expire à dix secondes sur la réparation du vélo |
| Budget global | Aucun dépassement des 60 secondes, aucune partie principale laissée sans tentative |
| Titres | Neuf expirations dans sept cas ; pas d’erreur HTTP 400 |
| Reformulations | 150 reformulations non exécutées, principalement après épuisement des 32 appels plein texte ; 16 recherches sont partielles pour cette seule raison |

Les index manquants et l’ancien budget global de douze secondes n’expliquent donc
plus ces mêmes observations. Le plafond de 32 appels reste distinct du délai :
les recherches larges font généralement 28 appels principaux, puis au plus quatre
reformulations. Augmenter seulement les secondes ne résout pas cette limite.

Le feu atteint « Techniques de production de feu » et le guide Wikilivres ;
le générateur trouve un article de fabrication Low-tech Lab. Ces titres sont des
pistes, pas une validation humaine des instructions. D’autres premiers titres
restent discutables : écran d’autoradio Mazda pour « réparer un poste radio »,
question de tableau électrique pour « installer un panneau solaire ». Le classement
et l’utilité sur ces besoins restent à qualifier, sans fabriquer de faux guides
ni limiter la bibliothèque à quelques thèmes.

## Lenteur reproduite hors des appels natifs

« faire du feux » prend encore **19 621 ms** avec 32 réponses en cache et des délais
d’appel tous arrondis à zéro ; la variante naturelle du générateur prend
**15 822 ms** avec 36 réponses réutilisées. Cela motive l’examen du travail autour
des appels : les traces ne mesurent ni occupation CPU globale ni activité HDD.
Un HDD peut ralentir les lectures d’index ; ce rapport ne suffit pas à l’accuser.

Chaque arrivée relançait la classification, les vérifications des fichiers sources
et la normalisation du texte de tous les candidats déjà reçus. La reproduction
sur 400 candidats et 20 arrivées entraîne **4 200 vérifications de source**.
Le profil local repère surtout la normalisation répétée, puis les métadonnées.
Ce défaut est une cause reproduite ; il n’explique pas à lui seul tous les délais
du Windows réel, où le nouveau traitement n’est pas encore mesuré.

## Correction conservée

- Réutiliser pendant une seule recherche les annotations des candidats inchangés
  et la révision de chaque fichier physique. Recalculer si le texte change ;
  revérifier les sources à la fin pour ne pas garder une correction humaine
  attribuée à une édition remplacée pendant la recherche.
- Mémoriser temporairement les textes normalisés, avec éviction, 4 096 entrées
  et 32 Mo de charge textuelle au plus. Ce budget inclut les textes et résultats
  normalisés, pas le surcoût des objets Python. Un essai de passages de 20 000
  caractères montre qu’un budget de 8 Mo évince trop tôt des textes encore utiles.
  Ce cache disparaît en fin de demande et reste distinct du cache Kiwix persistant.
- Exécuter sélection et métadonnées dans un thread attendu à l’annulation.
  Le serveur peut continuer à répondre pendant les accès fichiers ; cela ne
  transforme pas le classement Python en utilisation de tous les cœurs.
- Exporter les temps de sélection et de CPU du thread, le nombre d’annotations,
  de vérifications de source et de réemplois du texte, sans chemins privés.

Les budgets natifs, le nombre de voies, le score, les filtres et les règles de
pertinence sont conservés. Le problème des reformulations et les neuf expirations
de titres ne sont pas masqués par une déclaration de couverture complète.

## Essais de développement

`tests/search_processing_smoke.py` compare l’ancien travail répété et le nouveau
sur les mêmes candidats et chaque résultat intermédiaire. Il vérifie l’identité
des résultats et les appels de révision, sans imposer un seuil chronométrique CI.
Mesure locale sans charge maîtrisée, sur textes entièrement fictifs :

| Charge | Ancien traitement | Traitement conservé | Vérifications de source |
| --- | --- | --- | --- |
| 400 candidats, 400 caractères, 20 arrivées | 1 928 ms ; CPU 1 886 ms | 340 ms ; CPU 340 ms | 4 200 → 12 |
| 200 candidats, 20 000 caractères, dix arrivées | 9 604 ms ; CPU 9 552 ms | 1 910 ms ; CPU 1 895 ms | 1 100 → 12 |

Pour la seconde charge, le premier essai avec seulement 8 Mo prend 4 397 ms,
contre 1 910 avec 32 Mo ; la charge textuelle conservée atteint environ 15,9 Mo.
Ces durées ne prédisent pas le gain sur les 755 Go, ni les temps Windows.

Les tests ciblés couvrent texte modifié, source remplacée pendant un flux,
classement identique, limites de mémoire, Unicode et fermeture après annulation.
Le Kiwix épinglé réussit **54 contrôles** sur cinq petites archives ; la recette
de 135 archives fictives, **8 280 525 octets**, réussit **36 contrôles**, dont
progression, mesures, cache mémoire et cache disque après fermeture.
Les huit besoins y retrouvent leur source ; tous les fonds sélectionnés sont
examinés. Leur taille ne simule pas le débit d’un HDD lisant le fonds de Marc.

La suite locale finale passe à **568 tests, trois ignorés** en 80,051 secondes.
Les recettes Chromium via Playwright MCP réussissent **68 assertions** : recherche
50, flux progressif 18. Elles couvrent arrêt, lecture pendant le flux, clavier,
rechargement, exports et largeurs 1366/390/320 ; données et délais y sont fictifs.
Un flux HTTP supplémentaire de l’API 0.14.1 vérifie les nouveaux compteurs et leur
absence sur le JSON ordinaire, sans interception du moteur par le navigateur.
WebKit et Safari iPhone ne sont pas rejoués par ces essais Chromium.

Les liens locaux des documents modifiés et leurs ancres sont vérifiés,
`git diff --check` passe. Paquet et CI sont consignés ci-dessous après exécution ;
aucune validation Windows de cette correction n’est encore revendiquée.
La mise à jour conserve le schéma 1 et les composants tiers.

Le code livré est `aa389f1`. Le [passage CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43695594332)
ne lance aucun des huit jobs : GitHub signale des paiements échoués ou un plafond
de dépenses à relever. Ce refus intervient avant les tests et ne vaut pas
validation Windows, lecteurs Python isolés, routage ou WebKit de cette version.
Les preuves locales ci-dessus sont conservées sans contourner ce réglage du compte.

Le paquet local est déballé par le lecteur normal : **745 fichiers**, 6 650 131
octets, version 0.14.1 et schéma 1. Chaque fichier est comparé au commit `aa389f1`
avec les filtres de checkout Git, dont les fins de ligne CRLF imposées aux scripts
PowerShell. Aide des deux outils exécutée depuis la copie déballée ; aucun ZIM,
modèle, cache ou état privé inclus. SHA-256 :
`641965b67d2b704718f05a7b199d9935fbb5d21c3b95ef8c7b0c2d530cafcee8`.

## Suite et décision matérielle

Après mise à jour normale, relancer le même R2 sans IA en 0.14.1, puis lire les
résultats prioritaires. Les compteurs `coverage.processing` permettent de confronter
temps de traitement et appels natifs ; ils ne mesurent toujours pas les ressources
internes Kiwix. Le [guide](../exploitation/cache-et-recherche-progressive.md) décrit
les champs et leur portée. Pas de réindexation intégrale imposée par ce correctif.

Si le traitement baisse mais que les appels Kiwix restent longs, comparer une
archive puis sa répétition avec le [diagnostic ciblé](../exploitation/diagnostic-performances-kiwix.md).
Une décision SSD, CPU ou davantage de concurrence demande ensuite des mesures
sur ce PC. Le moteur utilise déjà plusieurs voies réseau et jusqu’à huit threads
pour les compléments SQLite ; « multithread » ne prouve pas que tous les cœurs
ou le disque sont saturés. L’objectif reste ouvert pour les contrôles humains
et les anomalies non encore reproduites sur le fonds réel.
