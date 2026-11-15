# Notices et guidage pratique — 0.19.1

**Bilan en cours — 15 novembre 2026.** Correction compatible du parcours documentaire,
avec une notice supplémentaire et une fiche française : version corrective 0.19.1,
schéma de livraison 1, images tierces et profils conseillés inchangés.
L’objectif d’utilité réelle n’est pas clôt par les seuls tests techniques.

## Demande et périmètre

Louis demande une notice Baofeng UV‑5R présenté comme 8 W, et un essai de guidage,
notamment le dimensionnement d’une antenne selon la fréquence. Il confirme ensuite
l’étiquette UV‑5R. Il précise que cet équipement est un exemple : le logiciel doit
être utile sur d’autres besoins, pas lire des articles sans rapport ou contenir
une réponse codée spécialement pour la radio.

Le [guide d’ajout](../bibliotheque/baofeng-et-antennes.md) donne le PDF vérifié,
sa partie française, ses variantes et sa préparation séparée sur le poste client.
Il ne prétend pas que le logiciel mis à jour télécharge tous les anciens plans.
La fiche d’antenne est une rédaction originale avec références BIPM/ARRL et calculs
reproductibles ; aucun fichier de manuel lourd n’est versionné ni copié au runner.

## Premier essai réel : défauts constatés

R7, vrai Gemma4 E4B sur le moteur 0.19.0, vraie notice multilingue et fiche d’antenne.
Recherche SQLite réelle, aucun texte fictif de commande. La recette ne contrôle
aucun poste radio et ne transmet pas d’onde. Les cinq réponses initiales terminent,
mais cela ne valide pas leur qualité :

- Verrouillage : réponse correcte sur `#` et les touches latérales, mais elle
  reprend le seul extrait de recherche ; zéro passage réellement ouvert, aucune
  référence conservée avec la réponse. Ce n’est pas une lecture valide.
- Canal simplex : aucune recherche, réponse générique avec commandes hypothétiques
  et demande de fournir une notice pourtant présente. Échec d’utilité.
- Quart d’onde à 145 MHz : valeur approchée 51,72 cm, puis justification erronée
  de l’effet diélectrique et marge de coupe non documentée. Aucun passage lu.
- Dipôle à 433 MHz : confusion entre demi-onde totale et demi-onde par bras,
  donc longueur totale doublée. Échec technique malgré une réponse structurée.
- Antenne sans fréquence : bons paramètres manquants repérés, mais proposition
  d’effectuer une recherche au lieu de la faire. Aucun passage lu.

Rapport initial privé : `report-gemma4-radio-initial.json`. Ces résultats restent
conservés et ne sont pas remplacés par les futurs cas favorables.

## Corrections générales retenues

1. Préparer aussi les demandes ordinaires « comment… » et de dimensions,
   sans inventaire de modèles ni liste exhaustive de verbes d’utilisation.
   Une seconde question reste transmise à l’IA sans imposer tous ses mots à la
   recherche du premier sujet. Les décimales et abréviations restent intactes.
2. Après une recherche demandée par le modèle, lire au maximum
   quatre candidats pertinents dans le budget avant sa rédaction. Une recherche
   seule reste marquée non consultée ; la lecture réelle passe par l’outil commun.
3. Garder accessibles les autres pages PDF regroupées sous le même résultat,
   après la priorité aux documents distincts. Elles ne deviennent pas des pages
   lues avant transmission de leurs passages. Les liens restent dans le même PDF.
4. Si une page ou un texte tient entièrement dans son allocation, le transmettre
   sans le couper artificiellement en deux extraits disjoints. Les petits budgets
   et gros documents gardent les passages, positions et limites visibles. Les
   questions sans fréquence ou sans type d’antenne doivent rester des demandes
   de précision, sans taille universelle.
5. Contrôler aussi les références des réponses documentaires ordinaires.
   Une citation vers un résultat non lu ne valide plus une réponse terminée.
   Les commandes sont demandées en code littéral, pour distinguer une touche
   numérique d’une référence documentaire.
6. Répartir les passages courts entre plusieurs sources selon le budget réel.
   Conserver les refus et omissions : cinq documents choisis ne prouvent pas cinq
   livres intégralement lus. Aucun agrandissement silencieux du contexte.

La consigne d’apprentissage approfondi n’impose plus quatre niveaux pédagogiques
à toute question de commande simple. Les notices, paramètres décisifs et calculs
restent distincts d’une explication générale. Aucun nom de touche ou résultat
numérique de radio n’est ajouté dans le moteur.

## Essai intermédiaire et limite de lecture

La première correction fait réellement lire une page, mais le verrouillage est
encore manqué : la page 38 sur la double veille est retenue, alors que la page 34
correcte fait partie des passages groupés. L’expansion de ces pages est donc
nécessaire, pas un changement arbitraire du nombre de résultats.

La lecture de la bonne page 41 de mémorisation perdait aussi le milieu de la liste
d’instructions : les deux fenêtres retenues s’arrêtaient dans `MEM-CH`, puis
reprenaient dans la procédure duplex. Le modèle fusionnait alors les deux modes.
Les contrôles de référence rejettent cette réponse qui contient aussi des touches
numériques prises pour des références. Le texte final incomplet conserve les extraits.
La transmission entière d’un texte qui tient dans le budget corrige cette coupure ;
la fidélité de la nouvelle réponse doit encore être examinée sur le modèle réel.

## Portée de validation

Les essais unitaires protègent les comportements communs sur d’autres formulations
et des passages synthétiques ; ils ne contiennent pas une procédure Baofeng copiée
comme réponse attendue par le logiciel. Le script réel `tests/real_radio_check.py`
reste volontaire, hors CI, avec une notice préparée séparément et vérifiée par hash.
Rapports privés : réponses, outils, références, modèle, contexte et empreintes de
code/politique/recette. La relecture du contenu reste nécessaire.

Aucun résultat R7 ne valide matériellement le poste, la puissance annoncée,
l’accord d’une antenne construite, les performances Windows ou le corpus de Marc.
Ce cas ne suffit pas à qualifier tous les savoir-faire : la suite doit élargir les
procédures et situations, avec échecs, sources insuffisantes et demandes ambiguës.


## Essai des pages complètes : préparation encore trop large

Le premier rejeu avec expansion des pages trouve bien la page 34, mais répartit
le budget entre trop de pages du même manuel. Les passages deviennent minuscules
et le contexte échoue avant la génération du cas verrouillage. Le cas mémoire
ne reçoit toujours pas toute sa procédure et mélange encore simplex/duplex.
Les dimensions, maintenant documentées, sont mieux traitées dans ce rejeu ; cela
ne valide pas les autres cas. Rapport privé `report-gemma4-radio-complete-pages.json`.

Le choix retenu compare donc les sections d’un même PDF sur les mots du sujet,
en écartant les mots du titre répétés sur toutes les pages et en privilégiant
le début de section. Une lecture préparatoire donne priorité à la meilleure
page de chaque document, pas à six pages quelconques du même manuel. Les autres
pages restent accessibles ; une sélection explicite de pages n’est pas remplacée.
Les consignes générales sont condensées, avec les exigences de sources, limites,
ressources, apprentissage et précautions conservées. La place libérée sert aux
textes : aucune hausse implicite du contexte ou de la mémoire du client.

Les premiers essais demandaient huit couches GPU ; le rejeu suivant en demande
32 sur le R7 libre, après contrôle des autres modèles et de la réserve vidéo.
L’occupation observée était environ 3 361 Mio, avec 12 582 Mio libres. Il ne s’agit
pas d’un réglage proposé au PC Windows, ni d’une comparaison isolée de vitesse :
le code, les consignes et les allocations documentaires changent également.


## Limites de la source et extension des recettes

La bonne page entière permet de restituer `MEM-CH`, le canal vide et `VFO/MR`,
sans mélanger le mode duplex. Le modèle omet encore parfois un prérequis : le
manuel demande la ligne supérieure de l’écran pour la mémorisation. Cette omission
reste un défaut de complétude à corriger de façon générale, pas par une commande
UV‑5R codée dans le moteur. Les numéros corrects ne suffisent pas à valider le guide.

La recette accepte aussi un manifeste de documents/cas vérifiés par empreinte,
pour élargir à d’autres besoins. Deux pages originales du constructeur Victron
sont préparées sur le R7 pour distinguer démarrage/poursuite de charge et signification
des caractéristiques du régulateur. Ce ne sont pas des références ajoutées
implicitement chez Marc. La source HTML complète est conservée, y compris sa
navigation ; les essais doivent révéler une éventuelle pollution des passages.

Un manuel Brother public a aussi été repéré pour la couture. Sa lecture PDF sur
le R7 demande le module cryptographique absent et le lecteur long refuse encore
les PDF protégés ; les deux pages HTML d’assistance essayées refusent la requête
(HTTP 403). Aucun accès n’est forcé et aucun texte de remplacement n’est inventé.
Cette limite documentaire reste à traiter ; elle ne devient pas une procédure validée.


## Extraction HTML et premier contrôle Windows

Le premier essai Victron utilise bien les documents réels, mais les passages
reçus proviennent surtout du sommaire/navigation. La différence démarrage/poursuite
reste donc incomplète. La réponse sur 75/15 retrouve les nombres sans expliciter
assez que 75 V est la limite photovoltaïque. Aucun de ces cas n’est déclaré validé.

Le lecteur distingue maintenant le contenu sémantique (`article`, sinon `main`)
des menus et du panneau de recherche ; titre/langue restent conservés. Les documents
anciens sans ces balises gardent leur lecture, et les traductions générées à
plusieurs articles gardent toutes les pages. Le plus grand article est une
heuristique, pas une garantie d’extraction de tout contenu web.
Les résultats de recherche transmis à l’IA gardent une couverture compacte ;
les diagnostics techniques n’occupent plus la place des passages. Le périmètre
reste conservé, avec un test de suivi documentaire ciblé.

La première CI du candidat `4152045` passe Linux mais révèle un défaut de test
Windows : comparaison du chemin temporaire court `RUNNER~1` à son chemin canonique.
Le contrôle compare maintenant les chemins résolus, sans changer la validation
du manifeste ou du dossier autorisé. Le résultat défavorable reste historique.
