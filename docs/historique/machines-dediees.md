# Machines dédiées : enveloppe de 1 000 € et paliers supérieurs

> Archive — document conservé pour retracer les propositions et le prototype initial. Les constats et commandes décrivent cette étape ; pour installer le pilote actuel, suivre le [guide Marc](../installation/pilote-marc.md).

Étude au 30 octobre 2026. Louis accepte le neuf et l’occasion. Il souhaite des ordres de grandeur pour les machines familiales et une perspective plus ambitieuse si Marc constate le bénéfice des gros modèles. Aucun achat décidé.

## Ce qui compte pour le projet

- VRAM : place pour le modèle, le contexte et les calculs sur GPU.
- RAM : marge pour l’hôte, les services et les parties du modèle déportées sur CPU.
- Processeur et bande passante mémoire : importants pour les gros modèles hybrides ; le seul nom Ryzen 5/9 ne suffit pas.
- Stockage : SSD pour modèles et index ; bibliothèque selon les volumes retenus. Une configuration à 1 To n’est pas une garantie d’accueillir le catalogue maximal.

Plus de mémoire permet d’utiliser un modèle plus lourd, une compression moins forte ou un contexte plus grand. Une carte plus rapide exécutant le même modèle ne garantit pas des réponses plus justes. Éviter de dimensionner uniquement d’après les performances en jeu ou les TOPS annoncés.

## Prix observés et prudence sur leur portée

Une page d’annonces Leboncoin consultée affiche un PC Ryzen 7 5800X, RTX 3060 **12 Go**, 32 Go de RAM et SSD 2 To à **900 €**, ainsi qu’un ensemble RTX 3060 12 Go / i5-12400F à 700 € dont les autres caractéristiques doivent être vérifiées. Ce sont des prix demandés, pas des transactions ni des machines inspectées. [Annonces consultées](https://www.leboncoin.fr/ck/ordinateurs/rtx-3060-12-gb).

Un indicateur d’occasion affiche une cote d’environ 455 € pour la RTX 4060 Ti **16 Go**. C’est un agrégat d’annonces, pas une carte réservable à ce prix. [Indicateur consulté](https://www.racingtech.fr/fr/gpu).

À titre de contre-exemple neuf, TopAchat affiche une Asus RTX 5060 Ti **16 Go** à **979,99 € pour la carte seule** au relevé. Des pages anciennes ou agrégateurs donnent moins : leur existence ne permet pas d’annoncer un PC complet neuf à 1 000 €. Aucun panier neuf complet adapté à ce budget n’a été confirmé dans cette étude. [Catalogue marchand consulté](https://www.topachat.com/pages/produits_cat_est_micro_puis_rubrique_est_wgfx_pcie.html).

Les offres indexées de PC neufs autour de 900–1 100 € n’ont pas été retenues comme preuve d’une configuration 16 Go : certaines redirigent vers un accueil, d’autres concernent une carte 8 Go ou ne permettent pas de confirmer les caractéristiques. Vérifier à nouveau prix, variante et disponibilité avant tout achat.

## Idée A : tour d’occasion équilibrée, autour de 1 000 €

Configuration à rechercher : Ryzen 5 5600 ou Ryzen 7 5700X/5800X, ou Core i5-12400/12400F ; RTX 3060 **12 Go** ; 32 Go de RAM au départ, carte mère pouvant accueillir 64 Go ; SSD 1 à 2 To ; alimentation de qualité compatible avec la carte.

Le PC 5800X / 3060 12 Go / 32 Go / 2 To annoncé à 900 € est un exemple de cette classe, sans recommandation du vendeur ni validation de son état. Ne pas confondre RTX 3060 12 Go, RTX 3060 8 Go, RTX 3060 Ti et variantes portables.

Capacités estimées : Qwen3.5 4B et 9B Q4 comme modèles courants, avec meilleure marge pour le 9B qu’avec 8 Go VRAM. GPT-OSS 20B et Qwen3.8 27B demanderaient encore du calcul hybride. Un 27B n’entrera pas intégralement sur ce GPU.

C’est la piste dont la faisabilité budgétaire est la mieux étayée par les exemples de tours complètes relevés. Le budget restant n’assure pas automatiquement une extension RAM, une sauvegarde et tous les accessoires.

## Idée B : tour mixte avec 16 Go VRAM, objectif de budget

Configuration visée : Ryzen 5 5600 ou Core i5-12400, RTX 4060 Ti **16 Go** d’occasion, 32 à 64 Go de RAM et SSD 1 To extensible. Enveloppes de recherche proposées, pas devis ni prix vérifiés de chaque pièce :

| Poste | Plafond cible pour essayer de tenir 1 000 € |
| --- | --- |
| RTX 4060 Ti 16 Go d’occasion | 450 € |
| CPU, carte mère, refroidissement | 200 € |
| 32 Go de RAM compatibles | 100 € |
| SSD 1 To | 80 € |
| Boîtier et alimentation adaptés | 140 € |
| Marge | 30 € |
| Total cible | 1 000 € |

Ce tableau est une contrainte de recherche : il ne prouve pas la disponibilité d’un assemblage à ce tarif. Si les offres dépassent les plafonds, augmenter le budget ou privilégier l’idée A ; ne pas sacrifier l’alimentation pour tenir la somme. Il exclut écran, clavier, licence Windows, montage rémunéré, sauvegarde externe, livraison et rémunération du projet. Linux serait une possibilité pour une machine dédiée, encore à choisir.

Capacités estimées : 4B/9B Q4 confortables à contexte modéré ; GPT-OSS 20B est candidat à un usage principalement GPU avec contexte limité, à vérifier car son paquet de 14 Go laisse peu de marge. Les 27B Q4 de 17–18 Go restent hybrides avec 16 Go VRAM, même si la part CPU peut être réduite. Ne pas promettre tous les modèles 27B entièrement sur GPU.

## Idée C : tour avec beaucoup de RAM pour le traitement long

Spécification à chiffrer : processeur de bureau moderne 6 à 12 cœurs, RAM 64 Go en double canal, SSD 1–2 To, GPU 8–12 Go réutilisé si disponible. Objectif : disposer de marge pour des modèles 27–35B en hybride, sans financer immédiatement 24 Go VRAM.

Autour de 1 000 €, cette piste dépend fortement de la réutilisation et du prix réel de la RAM ; aucun panier complet n’est validé. Avec le GPU actuel, passer de 32 à 64 Go de RAM peut améliorer la marge et éviter la pagination sans accélérer fortement une génération déjà limitée par le CPU. Plus de RAM ne remplace pas la vitesse mémoire et la puissance GPU.

Elle permettrait d’étudier la qualité des gros modèles avant d’acheter une carte coûteuse ; elle ne constitue pas le meilleur choix démontré pour servir plusieurs utilisateurs rapidement.

## Paliers si Marc veut aller plus loin

Ces spécifications sont des cibles d’étude. Les budgets supérieurs doivent être chiffrés par paniers actuels ; ils ne sont pas présentés comme des devis autour de 1 000 €.

| Palier | Ordre de grandeur matériel | Modèles et usage envisageables |
| --- | --- | --- |
| Entrée adaptée | GPU 12 Go, RAM 32–64 Go, CPU 6–8 cœurs, SSD 1–2 To | 4B/9B Q4 sur GPU à contexte modéré ; 20–27B en hybride |
| Intermédiaire | GPU 16 Go, RAM 64 Go, CPU 6–12 cœurs, SSD 2 To | 9B, certains modèles autour de 12–20B selon compression ; 27B hybride |
| Gros modèles domestiques | GPU 24 Go, RAM 64 Go, CPU 8–12 cœurs, SSD 2 To | Qwen3.8 27B Q4 et Gemma 4 26B Q4 candidats au chargement GPU complet à contexte modéré ; 31–35B selon paquet et marge |
| Plus ambitieux | GPU 32–48 Go, RAM 96–128 Go, CPU moderne, SSD 2–4 To | Contexte plus large ou compression moins forte des 27–35B ; classe 70B Q4 envisageable selon capacité exacte, notamment 48 Go ; mesure indispensable |

Pour un 70B dense en 4 bits, le calcul minimal des poids est d’environ 35 milliards d’octets, avant tables de quantification, couches gardées à précision supérieure et mémoire de fonctionnement. Ce calcul ne promet pas qu’un paquet donné rentrera dans 48 Go ni qu’il répondra assez vite. Ce n’est pas notre premier candidat aux essais.

Une RTX 3090 d’occasion donne 24 Go VRAM, mais les annonces sont très dispersées : une page consultée affiche plusieurs cartes seules à 1 200 € et une tour avec 64 Go à 2 300 €. Ne pas construire le budget familial sur une hypothèse générale de 3090 à 400–500 €. [Annonces consultées](https://www.leboncoin.fr/ck/ordinateurs/rtx3090). Une bonne affaire ponctuelle reste possible, à vérifier individuellement.

Pour la classe 24 Go, vérifier alimentation, boîtier, refroidissement, consommation et état de la carte ; relever la consommation réelle plutôt que déduire le coût d’usage du seul TDP. Une carte récente et une 3090 ont des compromis différents. Aucun achat de station professionnelle ou double GPU n’est recommandé à ce stade.

## Ordre de décision proposé

1. Mesurer petit et gros modèle sur les machines actuelles, sans nouvel achat.
2. Si le gain de qualité du 27B est faible, optimiser sources et outils avant le matériel.
3. Si le gain est net mais le délai excessif, chiffrer une tour 24 Go VRAM / 64 Go RAM.
4. Si la principale limite est la marge mémoire plutôt que la vitesse, chiffrer d’abord l’extension RAM.

Pour Marc, le palier 24 Go / 64 Go est donc un candidat concret à étudier après démonstration du gain. Le palier 48 Go / 128 Go ne se justifie que par des tâches et modèles testés ou un besoin documenté.
