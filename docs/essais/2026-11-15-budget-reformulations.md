# Couvrir les reformulations d’une grande bibliothèque

**Bilan daté — 0.14.2, 15 novembre 2026.** Suite du
[rapport réel 0.14.0](2026-11-15-rapport-0140-et-traitement-progressif.md), après
réduction du retraitement progressif en 0.14.1. Ce changement traite une autre
limite ; il ne promet pas une durée finale plus courte lorsqu’il exécute davantage
de recherches utiles. Aucun contenu ni modèle n’est téléchargé.

## Cause et reproduction

Le R2 réel contient 16 cas partiels pour les seules reformulations non exécutées.
Avec 28 appels principaux, le plafond fixe de 32 ne laisse que quatre appels
supplémentaires, même si le budget global de 60 secondes n’est pas épuisé.
Les index prêts ne corrigent pas cette limite et rallonger seulement le délai
ne permet pas d’envoyer les formulations restantes.

La reproduction utilise un catalogue fictif de 135 archives : 19 Wikipédia isolées,
101 archives anglaises en neuf lots et 15 compléments multilingues, soit 28 lots
natifs. Les réponses HTTP sont simulées. Un article de la dernière archive ne
répond qu’à la reformulation courte du sujet ; il reste accessible au même moteur
de classement, sans modifier score, mots-clés ou source attendue.

Avant correction, le test échoue parce que le document n’est jamais demandé :
28 appels principaux, quatre reformulations, puis plafond atteint. Après
correction, les 28 appels principaux et les 56 reformulations prévues peuvent
terminer et le document est trouvé. Toutes les collections sont prises en compte,
sans en déduire que le fonds réel ou les 15 index locaux ont été recréés dans ce test.

## Décision conservée

Pour le flux long du portail et le diagnostic, le plafond devient
`max(32, nombre_de_lots × (1 + nombre_de_termes_de_reformulation))`, avec au plus
deux termes, comme auparavant. La valeur effective reste dans `coverage.request_limit`.
Il s’agit d’une autorisation maximale : une réponse principale utile ne déclenche
pas automatiquement des variantes supplémentaires. Les mêmes conditions de
reformulation et les mêmes priorités s’appliquent.

Les deux voies plein texte et deux voies titres partagées, lots de douze,
délais par appel et budget natif global de 60 secondes sont conservés. Pas de
nouveau réglage ni de multiplication automatique des threads. Les erreurs ou
échéances peuvent encore laisser une couverture partielle, explicitement signalée.
Les replis isolant les erreurs HTTP continuent de consommer le même plafond ;
ce calcul ne garantit pas leur achèvement pour une bibliothèque en panne.

L’ancien JSON court et les outils de l’assistant gardent leur plafond de 32 appels
et leur budget de douze secondes. Les traces restent limitées à 40 entrées : le
nombre d’entrées exportées peut donc être inférieur aux appels exécutés. Les
compteurs de couverture ne sont pas limités à ces 40 entrées.

## Vérifications et limites

Trois tests vérifient la source auparavant manquée, le réemploi à chaud de plus
de 32 réponses, la conservation du plafond court et la fermeture des appels lors
de l’échéance. Le scénario long ne dépasse jamais deux lectures plein texte en
parallèle ; la répétition retrouve les mêmes résultats sans nouvelle lecture HTTP.
La durée du scénario d’échéance est raccourcie uniquement par une horloge de test,
pas dans le logiciel livré.

La suite complète du runner Linux réussit **571 tests, trois ignorés**, en
80,640 secondes. Le Kiwix épinglé réussit ses **54 contrôles** sur cinq archives
fictives et la recette de **135 archives, 8 280 525 octets**, ses **36 contrôles** :
sources attendues, couverture, progression et réutilisation mémoire/disque.
Les huit recherches y terminent avec toutes leurs collections examinées ; ce
petit fonds ne mesure pas les performances du HDD ou des 755 Go réels.

Le score, le schéma de données 1, les composants tiers et les fichiers Web restent
inchangés. Les recettes navigateur de 0.14.1 ne sont pas présentées comme rejouées
sur ce correctif sans changement Web. Paquet et CI sont ajoutés après exécution.
Aucune mesure Windows 0.14.2, relecture humaine ou validation de tous les documents
de Marc n’est revendiquée.

## Prochaine comparaison réelle

Mettre à jour normalement vers 0.14.2 ; aucun nouvel extrait intégral des archives
n’est nécessaire pour ce changement. Le même R2 sans IA permettra de comparer :

- temps des premiers documents et fin, en tenant compte des appels supplémentaires ;
- `primary_requests`, `refinement_attempted`, `refinement_not_searched`, couverture
  et valeur effective de `request_limit` ;
- coût `processing` de sélection, séparé des traces natives ;
- résultats effectivement ouverts et jugés utiles, surtout les besoins encore
  discutables comme le poste radio et le panneau solaire.

Une recherche peut durer davantage pour examiner des variantes qu’elle abandonnait
auparavant ; les premiers documents restent lisibles et l’arrêt conserve les
résultats reçus. Les expirations de titres et l’éventuel goulot CPU/HDD du PC réel
restent à mesurer. Le [guide actuel](../exploitation/cache-et-recherche-progressive.md)
décrit les budgets et les compteurs sans attribuer ces délais au matériel.
