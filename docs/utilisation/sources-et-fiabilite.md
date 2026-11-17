# Sources, dates et fiabilité des réponses

**Guide actuel — pilote 0.38.2, 17 novembre 2026.** Les règles et la transmission
des métadonnées sont implémentées. Les tests simulés ne certifient pas le respect
de ces règles par les modèles réels.

## Formules dans les articles — 0.37.3

Le lecteur extrait désormais les formules HTML prises en charge en conservant
les groupes, fractions, indices et puissances. Il privilégie l’alternative
fournie par l’auteur, puis la structure mathématique ; il n’invente pas une
formule à partir du nom d’une image. Une structure inconnue devient un
avertissement explicite. Les extraits transmis à l’assistant omettent un bloc
qui ne tient pas entier dans leur budget, plutôt que d’envoyer une demi-fraction.
La limite d’aperçu d’un long article ne coupe pas non plus un bloc de formule.
La lecture reste signalée comme partielle lorsqu’une partie du texte manque.

Ces notations ne constituent ni une lecture visuelle des schémas ni une
vérification du raisonnement. Une traduction techniquement ambiguë peut garder
tous ses chiffres : comparer la source et son original illustré pour les gestes,
branchements et usages importants. Un ancien fichier texte ayant déjà perdu
ses formules ne peut pas les retrouver sans réextraction de son original.

## Aide générale lorsque les sources ne suffisent pas — 0.38.1

Pour une explication, une idée ou une organisation familiale, l’assistant peut
répondre avec ses **connaissances générales**, en le signalant clairement.
Une recherche sans passage utile ne doit pas provoquer un refus automatique.
Il peut proposer un point de départ adaptable et demander l’âge ou le niveau
des enfants ; les horaires et durées proposés sont des exemples, pas des normes.

Les références numérotées restent réservées aux sources effectivement lues.
Une réponse générale n’ajoute pas de document au suivi et ne prouve pas que le
fonds entier a été interrogé. Si la question demande le contenu d’une notice,
une commande exacte ou une preuve, le manque doit être annoncé pour ce point.
Pour un dosage, une décision de potabilité, un branchement ou une structure,
l’absence de données décisives ne permet pas d’inventer une procédure ou une
garantie : l’assistant doit clarifier et donner les principes de prudence utiles.

Cette règle guide le modèle ; elle ne certifie pas la justesse de chaque réponse.
Les refus de moteur, la mémoire et les interruptions gardent leurs messages
techniques : ils ne sont pas remplacés par une réponse générale inventée.

## Commandes tirées d’une notice — 0.38.2

Une question portant explicitement sur une touche, un bouton ou un réglage
présent dans une notice déclenche une recherche locale avant la rédaction.
Lorsqu’une seule référence alphanumérique explicite est donnée (par exemple
`UV-5R`), elle sert à retrouver la notice ; la question complète sert ensuite
à sélectionner les passages. Une notice absente ou illisible reste un manque,
pas une autorisation d’inventer la commande. Un document trouvé doit encore
être lu et correspondre au modèle exact, à son édition et à ses conditions.

Une relance courte comme « Et pour revenir à l’accueil, quelle touche ? » peut
reprendre la référence et la collection de la question utilisateur précédente.
Le logiciel ne prend pas une référence supposée par l’IA et ne remonte pas au-delà
d’un nouveau sujet utilisateur. Plusieurs références ou une référence absente
conservent la question complète au lieu de deviner un appareil unique.

Ce routage améliore l’accès aux notices ; il ne garantit ni leur présence dans
le fonds, ni la fidélité de chaque réponse ou la validité d’une commande réelle.

## Lire une réponse de l’assistant

L’assistant doit distinguer ce qu’un document indique, ce qu’il en déduit et ce
qui reste inconnu. Par exemple : « La notice indique quatre bouteilles de deux
litres [1]. J’en déduis un total de huit litres : 4 × 2. » Le calcul n’est pas
présenté comme une phrase écrite dans la notice.

Les consignes demandent de citer le titre, la date du document et son édition
lorsqu’ils sont disponibles. Les références numérotées ouvrent le document.
Un résultat de recherche n’est pas une source lue : le portail ne conserve parmi
les citations que les sources effectivement ouvertes par les outils ou associées
à la question, puis citées dans la réponse. Une lecture peut rester partielle ;
elle ne prouve pas que le livre entier a été consulté.

Lorsque les documents ne permettent pas de conclure, l’assistant doit dire
**« Je ne sais pas d’après les documents disponibles »** et expliquer ce qui
manque. Il ne doit pas inventer une notice, un chiffre ou une citation. Une
recherche infructueuse ne prouve pas qu’aucun document pertinent n’existe ailleurs.

En cas de contradiction, il doit citer les deux sources, expliquer leur désaccord
et leurs conditions connues, puis signaler l’impossibilité de trancher si nécessaire.
La source la plus récente n’a pas automatiquement raison. Une réponse d’IA ne
garantit pas à elle seule l’exactitude ni l’actualité des documents.

La [référence de recherche](recherche-documentaire.md) décrit le classement
commun et la préparation des demandes documentaires depuis 0.1.36. Un classement
élevé ne transforme pas un article général en procédure validée.

## Suivi des recherches et lectures dans l’assistant

Depuis 0.15.0, les nouvelles réponses disposant d’observations documentaires
affichent une ligne dépliable, par exemple **Recherche limitée · 1 source consultée**.
Ce suivi est calculé à partir des appels du logiciel, indépendamment des phrases
du modèle. Il ne corrige pas automatiquement une affirmation erronée de l’IA.

En dépliant, on trouve le périmètre, le nombre de demandes différentes, les
résultats proposés et les éventuelles lectures en échec ou par passages. Les
**Documents consultés** ouvrent les sources effectivement lues par les outils,
même si le modèle ne les a pas citées. Au plus douze liens sont affichés ; les
comptes restent distincts. Les citations numérotées conservent leur rôle : elles
désignent les sources lues auxquelles la réponse fait effectivement référence.

**Recherche effectuée** signifie que ces appels ont terminé dans leur périmètre,
pas que toute la bibliothèque a été lue. **Aucun résultat pour ces recherches**
n’établit pas une absence générale. **Recherche limitée**, **indisponible** et
**Couverture non mesurée** gardent leurs limites visibles. **Aucune source consultée**
permet de distinguer un résultat proposé d’un document dont le texte a été lu.
Une lecture par passages n’est pas une lecture intégrale, ni une validation des
conclusions du modèle ou de la sécurité d’une procédure.

La ligne reste repliée au départ et garde son ouverture pendant la réponse.
Elle est enregistrée avec les nouvelles réponses et revient au rechargement.
Les anciennes conversations restent intactes, sans inventer de suivi a posteriori.
En cas d’annulation ou d’échec, le travail observé peut rester consultable dans
la demande tant qu’elle est conservée ; une réponse finale qui n’a pas été créée
ne reçoit pas de nouveau message inventé. Une panne de cette fonction optionnelle
ne doit pas bloquer conversation, bibliothèque ou lecture.

Ce suivi ne prouve ni que tous les résultats sont pertinents, ni que le modèle
a correctement utilisé les passages. La [recette réelle de l’assistant](../essais/recettes-progressives-marc.md)
et la relecture humaine restent nécessaires.

Le portail permet de [choisir plusieurs documents](documents-et-traduction.md#choisir-les-documents-dune-conversation--0170)
et de préparer une [synthèse par passages ou une lecture longue](synthese-documentaire.md).
Les [illustrations originales](illustrations-et-references.md) peuvent être proposées
sous la réponse. Le modèle reçoit textes et légendes, pas les pixels des images.
Ces fonctions ne garantissent ni une lecture intégrale ni la fidélité de la réponse.

## Reprendre une discussion et vérifier les conditions de départ — 0.20.0

Une relance telle que « et les conditions pour cette procédure ? » peut faire
relire jusqu’à quatre documents effectivement consultés dans l’échange précédent.
Leur ancien numéro n’est pas réutilisé comme une preuve : la nouvelle réponse
reçoit ses propres lectures et références. Les titres/identifiants historiques
servent seulement de repères. Une nouvelle question sur un autre sujet continue
à utiliser la recherche ; la sélection manuelle explicite garde la priorité.
La détection de relance est limitée : si elle n’est pas reconnue, le modèle peut
encore relire ces repères avec les outils. Aucun ancien historique n’est réécrit.

Pour une procédure, une courte relecture peut sélectionner jusqu’à trois
conditions de départ oubliées, parmi les passages déjà lus. Le portail les montre
**avant la réponse**, sous « À vérifier avant de commencer — extraits des documents ».
Le logiciel reprend les mots du document, avec leur source ; le modèle choisit
des segments disponibles et ne peut pas inventer le texte de ce complément.
Cette vérification peut ajouter du temps, omettre une condition ou répéter une
condition déjà reformulée. Elle n’est ni exhaustive ni une certification du sens,
du matériel réel ou de la sécurité de la procédure. Son échec laisse la réponse
et les documents accessibles ; le rapport des durées en conserve l’état.

Si le modèle décrit une commande JSON sans appeler l’outil, une seule reprise
lui demande d’utiliser l’interface déclarée. Le texte JSON n’est pas exécuté par
le logiciel. Si cela échoue encore, la réponse est signalée incomplète avec une
explication. Les exemples de code/JSON explicitement demandés restent du texte.
Une référence numérique sans source lue est également refusée, même en l’absence
de recherche préalable. Cela contrôle la provenance ; une référence valide ne
prouve toujours pas que l’affirmation est fidèle.

## Quand une recherche est incomplète

Depuis 0.1.35, une erreur Kiwix ne se transforme plus silencieusement en absence
de résultat. Les résultats des guides et des encyclopédies qui répondent sont
conservés. Un message signale les recherches en échec, interrompues ou les
collections dont l’index de texte n’est pas annoncé. Depuis 0.1.36, ces tags ne
suffisent pas à exclure une archive : elle est aussi sondée dans la limite du budget.
La lecture directe reste disponible dans Collections.
L’assistant reçoit les mêmes limites avec ses résultats de recherche.

Une recherche complète signifie que les archives sélectionnées ont répondu,
pas que chaque passage a été lu ni que les mots choisis couvrent tout le sujet.
Le filtre de langue restreint cette sélection. Des synonymes français/anglais
aident notamment pour « feu », mais ne traduisent pas arbitrairement toute question.
Pour une procédure pratique, l’assistant doit lire une référence directement
pertinente : un document de prévention des incendies ne suffit pas à justifier
une méthode d’allumage. Les consignes ne garantissent pas le comportement d’un modèle.

## Comprendre les dates affichées

Le lecteur, les résultats de recherche et les boutons de citation distinguent :

| Mention | Signification |
| --- | --- |
| Document | Date déclarée de publication ou de révision du document |
| Édition | Référence d’édition fournie par les métadonnées ; elle peut préciser une incertitude |
| Collecte locale | Date d’ajout ou de téléchargement local, lorsqu’elle est connue |
| Archive (catalogue) | Date `updated` annoncée par le catalogue Kiwix pour la collection ; elle ne date pas l’article consulté |

Une date de document absente s’affiche **« Date du document inconnue »**. Le
programme ne la déduit pas de la date du fichier, du nom d’une archive ni de sa
collecte. Les anciens téléchargements indiquaient parfois explicitement une
édition dans leur provenance : cette édition est conservée, sans devenir une
date de publication supposée.

Les dates enregistrées avec une réponse restent celles disponibles lors de cette
réponse. Les anciennes conversations sans métadonnées restent lisibles et
affichent une date inconnue ; la mise à jour ne réécrit pas leur historique.
Ouvrir leur référence montre le document actuellement disponible, qui a pu évoluer.

## Ajouter un document daté

Dans **Paramètres → Ajouter un guide**, un administrateur peut renseigner
**Date du document, si connue** et **Édition, si connue**. Les formats acceptés
sont `2020`, `2020-05` ou `2020-05-12`. Une date impossible est refusée. Laisser
le champ vide lorsque le document ne fournit pas cette information.

La collecte est enregistrée séparément au moment de l’ajout ; elle ne remplit
jamais la date du document. Pour les lots téléchargés, le catalogue conserve
l’édition déclarée. Une nouvelle collecte est datée ; un fichier ancien déjà
présent sans date de collecte reste sans date de collecte connue.

Les métadonnées de date sont conservées dans la base privée du pilote et dans
les sauvegardes correspondantes. Le fichier `metadata.json` des guides publics
peut également porter `document_date`, `edition` et `collected_at`. La réindexation
conserve les dates connues lorsqu’un ancien fichier de métadonnées ne les fournit
pas. Aucun document familial n’est exporté automatiquement vers un kit public.

## Actualiser et vérifier

Pour une installation portable, appliquer le [paquet de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#petites-mises-à-jour-du-logiciel),
puis recharger le navigateur. Les comptes, conversations et documents sont
conservés. La table de dates ajoutée est compatible avec les anciennes métadonnées
à cinq colonnes ; aucune migration destructive ni changement des images tierces.

Sur le laboratoire de Louis, après récupération du code et vérification du
montage SSD, utiliser `python3 scripts/lab_refresh_library.py`. Cette commande
actualise le contexte du portail et tente de republier les profils partagés dans
Open WebUI, sans démarrer Ollama. Si Open WebUI est indisponible, le message
indique de relancer la commande quand le service est accessible. La bibliothèque
reste indépendante de l’inférence et une pause du moteur n’est pas levée.

Les consignes textuelles sont communes aux profils SetupSurvie d’Open WebUI.
Le transport des dates et les boutons décrits ici concernent le portail ; cela
n’ajoute pas ses outils documentaires à Open WebUI. Les traductions progressives
conservent leur protocole propre de fidélité au texte et leurs limites.

La [recette de fiabilité](../essais/protocole-fiabilite-ia.md) fournit huit scénarios
fictifs pour comparer les réponses réelles. Un modèle peut encore ignorer une
consigne, mal interpréter un passage ou produire une référence injustifiée dans
son texte ; le filtrage des boutons de citation ne contrôle pas la vérité de la réponse.
