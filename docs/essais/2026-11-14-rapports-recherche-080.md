# Rapports réels de recherche 0.8.0 transmis par Louis

**Bilan de diagnostic — 14 novembre 2026, PC Windows de Marc.** Deux exports
du site, puis une capture d’une tentative d’indexation. Ce constat ne clôture
pas la fiabilisation ; il réoriente les corrections vers des échecs réels.

## Contrôle sans IA

Le contrôle complet compte 32 demandes, toutes marquées `partial`. Le catalogue
répond : 135 collections annoncées et 102 guides indexés. L’état complémentaire
est `not_prepared`, sans index local utilisé dans ces demandes ; 64 collections
n’annoncent pas d’index de texte. Cette étiquette ne prouve pas à elle seule que
leur ZIM est effectivement dépourvu d’index natif.

**30 demandes sur 32 ne comptent aucune recherche d’archive aboutie.** Les autres
montrent des sources repérables, notamment sur le feu et les générateurs à pédales.
Les résultats changent fortement entre formulations et entre les deux exports.
Des pages de guides sans rapport direct apparaissent lorsque les archives ne
répondent pas ; même le cas négatif remonte des résultats.

La médiane mesurée est 313 ms, mais beaucoup de ces demandes n’ont reçu aucun
résultat d’archive. Ce nombre ne valide donc pas une recherche complète rapide.
Les rapports actuels comptent les échecs sans identifier assez précisément leurs
causes HTTP ou délais. Surcharge, requête refusée, timeout et défaut de classement
restent à départager ; aucune cause unique n’est certifiée à partir de ces exports.

Les avis humains sont tous `unreviewed` : les titres et extraits permettent de
repérer des anomalies, sans établir un taux de procédures réellement utiles.

## Comparatif avec IA

32 demandes planifiées, budget choisi de 15 secondes, mode rapide `gpt-oss:20b`.
**Huit demandes ont commencé**, sept reformulations expirent autour de 30 secondes,
puis la huitième est interrompue avec `hardware_unavailable`. Aucun reclassement
n’a été exécuté, aucune demande du groupe réservé n’a été mesurée et aucun avis
humain n’a été enregistré. Il n’existe donc pas de comparatif de qualité terminé.

Le code 0.8.0 utilise les 15 secondes comme critère d’évaluation, avec un timeout
technique de 30 secondes dans ce cas. Louis l’utilise comme une attente maximale :
ce décalage doit être corrigé, sans enchainer des appels déjà en échec.
L’indisponibilité finale du suivi matériel ne démontre pas une RAM épuisée ; les
dernières marges mesurées sont encore au-dessus des réserves. Une interruption
du contrôleur ou de son accès doit rester distincte d’une pression mémoire.
L’aide reste désactivée dans la recherche habituelle.

## Tentative d’indexation ensuite

Louis précise que les exports précédents ont été faits **avant** son clic sur
Préparer l’outil, puis Créer ou reprendre les index. La capture suivante indique
une erreur, **135 / 135 archives examinées et 0 article indexé**. Elle n’affiche pas
les motifs par archive. Le rapport d’indexation est nécessaire pour distinguer
les archives utilisant leur index natif des erreurs de lecture ou de préparation.
Zéro article ajouté ne signifie pas que les index natifs sont absents.

## Suite prioritaire

- Examiner le rapport d’indexation réel et reproduire son erreur sur petites données.
- Rendre les causes d’échec de recherche exploitables sans journaux privés.
- Éviter les replis hors sujet, y compris les cas négatifs, sans annoncer le fonds absent.
- Corriger le budget temporel du comparatif et arrêter les répétitions vouées à l’échec.
- Refaire R1 puis une recette R2 courte après correction ; garder les critères de
  qualité et les mesures complètes distincts de la présence de fichiers.

Les originaux des exports et la capture restent dans les pièces jointes privées ;
aucun corpus, texte complet ou historique n’est ajouté au dépôt pour ce diagnostic.
