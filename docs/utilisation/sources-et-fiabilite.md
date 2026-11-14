# Sources, dates et fiabilité des réponses

**Guide actuel — pilote 0.1.35, 14 novembre 2026.** Les règles et la transmission
des métadonnées sont implémentées. Les tests simulés ne certifient pas le respect
de ces règles par les modèles réels.

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

## Quand une recherche est incomplète

Depuis 0.1.35, une erreur Kiwix ne se transforme plus silencieusement en absence
de résultat. Les résultats des guides et des encyclopédies qui répondent sont
conservés. Un message signale les recherches en échec, interrompues ou les
collections sans index de texte. Ces dernières restent ouvrables dans Collections.
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
