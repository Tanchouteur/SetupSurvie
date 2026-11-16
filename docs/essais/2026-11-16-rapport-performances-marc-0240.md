# Performances réelles de Marc en 0.24.0

**Bilan du rapport reçu le 16 novembre 2026.** Campagne 0.24.0, protocole 1,
onze étapes terminées en 395 551 ms, 132 échantillons matériels. Le rapport brut
reste privé, hors Git. Le statut « terminé » décrit l'exécution des mesures ;
il ne certifie ni une couverture documentaire complète ni la qualité des réponses.

## Ce qui fonctionne dans cette campagne

GPT‑OSS 20B utilise un contexte demandé, transmis et chargé de **32 768 tokens**
(limite native annoncée : 131 072). Ollama annonce 0.40.16. Les trois réponses
documentaires terminent après lecture de sources :

| Étape | Durée totale | Première sortie | Sources lues | Lectures échouées |
| --- | ---: | ---: | ---: | ---: |
| Question documentaire, premier passage | 106,6 s | 33,5 s | 9 | 1 |
| Même question, répétition | 55,4 s | 17,5 s | 10 | 0 |
| Trois documents sélectionnés | 66,0 s | 9,8 s | 3 | 0 |

Le blocage `context_budget` des deux questions naturelles du rapport 0.22.0
n'apparaît plus. Le code et le contexte ont changé ensemble : cette comparaison
ne sépare pas l'effet du correctif 0.23.1 de celui du passage de 16k à 32k.
Les estimations gardent respectivement 434 et 1 621 tokens de marge après
réserve de réponse et de format ; les entrées réelles annoncées sont 12 070
et 11 557 tokens. Le contexte chargé de 32k est observé, mais une entrée remplissant
toute cette fenêtre n'est pas testée ici.

Les lectures sont majoritairement partielles : sept, neuf et deux sources
respectivement. Deux candidats supplémentaires sont écartés du dossier de chacune
des questions naturelles. Le premier dossier comporte aussi une lecture échouée.
La campagne exporte des mesures numériques, sans texte des réponses : l'utilité,
la fidélité et le détail de cet échec ne sont donc pas vérifiés par ce fichier.

## Recherche classique : cache utilisé dès le premier passage

| Recherche | Premier passage | Répétition | Première réception observée |
| --- | ---: | ---: | ---: |
| Faire du feu | 3,19 s | 3,07 s | 0,17–0,19 s |
| Panneau solaire / batterie | 6,48 s | 6,48 s | 0,19–0,23 s |
| Révolution française | 4,13 s | 4,11 s | 0,12 s |

Chaque recherche renvoie 24 candidats. Les compteurs annoncent 120 archives
interrogées nativement et quinze par les index locaux, sans échec, archive omise,
index local périmé ni dépassement de délai. Les appels natifs conservés dans
la trace utilisent tous le cache ; celui-ci n'a pas été vidé. Les premiers passages
ne sont donc pas des recherches à froid et ne se comparent pas directement aux
62–72 secondes initiales de la campagne 0.22.0.

Le classement des résultats consomme environ 2,3, 5,7–5,8 et 3,5 secondes de CPU
dans le fil qui effectue les sélections. Il représente une part importante du
temps restant lorsque les réponses Kiwix sont déjà en cache. Les médianes d'activité
disque par recherche sont ici de 3 à 7 %, avec seulement un ou deux échantillons
par étape : aucune conclusion fine sur toutes les lectures ne s'en déduit.

La couverture globale reste `partial`. Le diagnostic 0.24.0 n'exporte pas les
états détaillés des vidéos, du catalogue et des annotations ; ses seuls compteurs
d'archives ne permettent pas d'identifier la cause restante. Par exemple, une
recherche vidéo non préparée peut rendre ce statut partiel dans le moteur, mais
le présent rapport ne prouve pas que c'est le cas. Ne pas interpréter « zéro
échec d'archive » comme une preuve que tout le fonds est entièrement interrogeable.

## Disque au chargement ; coût du modèle pendant la rédaction

Première rédaction seule : **122,0 s**, dont **111,4 s de chargement** annoncées
par Ollama. Pendant cette étape, le disque des données est actif à 98 % en médiane
et lit environ 133 Mo/s. La répétition dure **11,3 s**, avec seulement 2 ms de
chargement annoncé et environ 26 tokens/s de génération. Le chargement initial
reste donc un délai majeur ; il était de 107,9 s dans le rapport 0.22.0.

Pendant la répétition et les synthèses, le CPU total médian est autour de 56 %,
certains cœurs atteignent 96–98 %, et l'utilisation GPU médiane est de 22–24 %.
La génération atteint généralement 25–26 tokens/s, contre 21,7 pour le premier
appel documentaire plus long. L'allocation annoncée par Ollama est d'environ
14,1 milliards d'octets, dont 5,39 milliards en VRAM : le modèle n'est pas placé
entièrement en mémoire vidéo. Ces observations justifient d'examiner le placement
et le travail CPU ; elles ne mesurent pas isolément la limite de la carte graphique.

Le PC a environ 32 Go de RAM et une RTX 5060 Ti 8 Go. Pendant les trois synthèses,
il reste au minimum **7,06–7,33 Gio de RAM disponibles**, et l'occupation vidéo
totale atteint environ 7,54 Gio. Aucun échec mémoire n'est enregistré. Les ressources
couvrent tout le PC et les pics courts peuvent échapper aux mesures.

Le temps documentaire se répartit notamment ainsi :

| Phase | Premier passage | Répétition | Trois documents choisis |
| --- | ---: | ---: | ---: |
| Recherche | 3,27 s | 3,18 s | Sans recherche |
| Lecture | 9,06 s | 0,37 s | 0,17 s |
| Préparation du modèle | 20,61 s | 13,53 s | 9,07 s |
| Rédaction visible | 36,33 s | 37,06 s | 40,64 s |
| Liaison complémentaire des citations | 35,99 s | Non requise | 14,75 s |

La liaison des citations est un second appel contraint au modèle lorsque la
première réponse ne relie pas suffisamment son texte aux sources réellement lues.
Elle préserve les faits proposés mais ajoute des références vérifiées syntaxiquement ;
elle ne certifie pas leur vérité. Réduire ce coût demande d'améliorer les citations
dès le premier appel, sans supprimer leur contrôle.

Louis indique séparément un HDD et un processeur de la famille Core Ultra 5 ;
le rapport ne détermine pas le type du disque ni la référence exacte du CPU.
Un SSD est une piste forte pour le chargement initial et les archives non cachées,
avec modèles, index et contenus concernés placés dessus. Il ne garantit pas une
réduction équivalente des 55–107 secondes de synthèse une fois le modèle chargé.
Il reste à comparer des campagnes dans des conditions proches avant et après
changement, sans annoncer de facteur d'accélération non mesuré.

Références : [rapport 0.22.0 et correction](2026-11-16-rapport-performances-marc-0220.md),
[diagnostic complet](../exploitation/diagnostic-complet-performances.md),
[essai mémoire](../utilisation/mesurer-assistant-et-memoire.md).
