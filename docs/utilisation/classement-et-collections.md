# Classer les documents et nommer les collections

**Guide actuel — actualisé pour la 0.67.0, 20 novembre 2026.** Ces corrections se font depuis le
profil **Famille**, librement accessible sur le réseau local. Elles sont communes
aux lecteurs et à l’assistant. Aucun modèle IA n’est nécessaire.

## Organiser les collections

Depuis la **0.65.0**, le tri a sa propre page : **Mon appareil → Paramètres →
Bibliothèque et préparations → Organiser les collections**. On le fait en
général une fois, après l’installation. **Bibliothèque → Collections** n’affiche
plus qu’une ligne de résumé (combien de collections dans chaque fonds) et le
raccourci **Organiser les collections →**. Les cartes rangées dans Autre portent
l’étiquette **Rangée dans Autre**.

La page rappelle en haut les trois choix possibles :

- **Fonds principal** : consulté en premier par la recherche et l’assistant.
  Il alimente **Autonomie et résilience** et **Savoirs et culture**. Les deux
  espaces appliquent le classement documentaire à la recherche générale.
- **Autre** : la collection reste sur l’appareil et se lit normalement. La
  recherche ne la consulte que si l’on choisit **Autre** ou **Toute la
  bibliothèque**. L’assistant applique les mêmes choix.
- **Supprimer** : efface les fichiers du PC serveur et exclut la collection des
  prochains téléchargements, éditions suivantes et plans repris compris.

Les collections sont regroupées par famille (Wikipédia, Gutenberg…, puis
**Vidéos téléchargées**), des plus volumineuses aux plus petites. Depuis la
**0.65.1**, chaque famille est repliée à l’ouverture : son en-tête donne le
nombre d’éléments, le volume et où ils sont rangés, avec un interrupteur
**Principal / Autre** qui range toute la famille d’un coup. Un clic sur le nom
la déplie ; **Tout déplier / Tout replier** agit sur toutes. Une recherche par
nom déplie les familles trouvées. Depuis la **0.65.2**, l’en-tête d’une famille
repliée liste aussi ses collections (cinq au plus, puis « et N autres »), une
collection seule s’affiche directement sans dépliage, et les familles qui ne
diffèrent que par la casse (« wiktionary » et « Wiktionary ») sont réunies. Quand plusieurs archives d’une famille portent
le même nom (« Project Gutenberg Library »), la ligne affiche leur sujet tiré du
catalogue (« Fine arts », « Science »…). Chaque ligne
montre le nom lisible, le type, la taille, la description du catalogue quand
elle existe, le nom du fichier et un lien **Aperçu ↗** qui ouvre la collection
dans Kiwix pour vérifier ce qu’elle contient. L’interrupteur **Principal / Autre**
de chaque ligne enregistre le choix immédiatement. Pour agir sur plusieurs
collections, cochez-les (ou cochez la famille entière) : une barre en bas de page
propose **Fonds principal**, **Autre** ou **Supprimer…**. La suppression passe
par une confirmation qui nomme les collections, le volume libéré et les fichiers
concernés, y compris les fichiers partiels. Dès la confirmation, la page
indique l’envoi de la demande, puis affiche son acceptation ou son refus.
Pendant l’opération, elle distingue l’effacement des fichiers et
l’actualisation du catalogue. Le redémarrage du portail peut interrompre
brièvement le suivi, qui se reconnecte automatiquement. La page affiche
ensuite le résultat et actualise la liste. Vous pouvez aussi suivre
**Suppression de collections** dans la **File d’attente** ou rouvrir la
page d’organisation pour consulter l’état de la dernière préparation
si c’est encore cette suppression.

Les vidéos dans une archive suivent le classement de cette archive ; les guides
individuels font partie du Fonds principal. Les vidéos YouTube d’un groupe exclu
sont écartées dès que le téléchargeur connaît leur chaîne ou leur dossier.

Un changement entre Fonds principal et Autre est réversible et s’applique à
la recherche suivante. **Exporter ce classement** produit un fichier
`SetupSurvie-tri.json` avec les listes **Autre** et **Exclues**.
Pour l’importer, choisissez ce fichier lors de l’installation Windows,
ou à la préparation de la sélection dans **Mon appareil → Téléchargements**.
Vérifiez le volume et le classement proposés avant de lancer le transfert.
Les éditions sont reconnues par la référence de collection, langue comprise.

Avant la 0.65.0, ce tri et l’index Wikipédia occupaient deux panneaux dans
**Bibliothèque → Collections** ; Louis les a jugés inutilisables le 20 novembre
2026 (on ne comprenait pas quelle collection était laquelle ni l’effet des
boutons), d’où cette page.

## Préparer la recherche du fonds principal par espace

Le classement du fonds principal se lance dans **Mon appareil → Paramètres →
Bibliothèque et préparations → Préparer la recherche dans les archives**. La
recherche utilise chaque archive classée dès que son index est prêt. Elle continue
d’interroger l’archive habituelle pendant la préparation et utilise les index
habituels pour **Toute la bibliothèque**.

Les archives rangées dans **Autre** sont écartées de la préparation. Si une
archive revient dans le fonds principal, elle est immédiatement recherchable.
Son classement est réutilisé si l’édition et les corrections correspondent
encore. Sinon, la prochaine plage d’indexation autorisée reprend la préparation.
Le panneau affiche les archives prêtes et la progression dans l’archive en cours.

Les gros fichiers sont lus et analysés par plusieurs processus. Un seul processus
écrit l’index dans l’ordre et enregistre le point de reprise. Les nouveaux index
stockent chaque passage une seule fois avec ses espaces. Un index déjà engagé
dans l’ancien format reprend depuis son dernier point enregistré.

Une pause manuelle se reprend depuis le panneau. Une pause automatique liée à
la plage d’indexation ou au mode jeu peut reprendre à la prochaine plage autorisée.
Les guides et les pages de PDF reçoivent leur classement pendant l’indexation
documentaire. Le catalogue des vidéos prépare le classement à partir du titre,
de la description et du début des pistes exploitables du fonds principal.
Les corrections de classement enregistrées gardent la priorité. Voir
[les préparations et leur suivi](preparations-bibliotheque.md).

## Comprendre le classement automatique

Pour Wikipédia, le classement tient compte du titre, des sections principales
et des catégories d'article quand elles sont présentes dans l'archive locale.
Un article peut appartenir aux deux espaces. L'indication peut évoluer à la
fin d'une recherche progressive, après lecture de la structure. Si un résultat
attendu manque, élargir à **Toute la bibliothèque** puis corriger son
classement si nécessaire.

Le [protocole de mesure](../essais/mesurer-classement-documentaire.md) permet
de comparer deux versions sur les mêmes documents et vidéos.

## Corriger le classement d’un document ou d’une vidéo

1. Avec le profil **Famille**, ouvrir le document ou la vidéo dans le lecteur
   SetupSurvie depuis **Bibliothèque → Rechercher**. Les espaces s'affichent
   sous le titre, avec l'indication automatique ou humaine. Ouvrir **Corriger
   le classement** juste en dessous.
2. Choisir **Autonomie et résilience**, **Savoirs et culture**, ou les deux.
   Sans espace choisi, le document reste retrouvable dans **Toute la bibliothèque**.
3. Indiquer ce qu’il contient surtout : présentation, explication, procédure,
   exercice ou notice technique. Garder **Type à vérifier** si son contenu n’est
   pas suffisamment connu.
4. Cocher **J’ai examiné le contenu pour ce classement** seulement après lecture,
   puis enregistrer. La prochaine recherche utilisera la correction.

Le résultat distingue classement **corrigé**, classement **examiné** et indication
automatique. Une procédure classée comme telle n’est pas certifiée correcte ou
sûre. Le simple titre « guide » ne suffit pas à classer automatiquement une page
comme procédure. Un quiz explicite peut être repéré comme exercice à vérifier.

Pour une vidéo, le formulaire utilise la même indication automatique que la
recherche, même si le lecteur est ouvert sur un passage précis.

La correction s’applique à l’article ZIM, au document entier ou à la vidéo
entière, quel que soit le passage ouvert. Elle ne modifie ni le fichier ni ses liens.
**Revenir au classement automatique** supprime seulement cette correction.
Une réindexation des guides conserve les corrections.

## Si le fichier change

La correction est liée à la référence et à la version locale du fichier. Une
nouvelle édition portant une autre référence ne reçoit pas l’ancien examen.
Si le fichier est remplacé sous le même nom, une modification de taille ou de date
de modification invalide la correction ; le site demande de la revoir et utilise
l’indication automatique. Un formulaire ouvert sur une ancienne version refuse
d’enregistrer avant réouverture du document.

Cette reconnaissance rapide par taille/date ne relit pas les centaines de Go
d’une archive et ne constitue pas son contrôle d’intégrité cryptographique. Les
vérifications de téléchargement et d’indexation restent distinctes.

## Nommer et regrouper les collections

Dans **Bibliothèque → Collections**, ouvrir le groupe si nécessaire puis choisir
**Modifier les noms** sur une collection.

- **Groupe ou source** réunit les collections portant le même nom.
- **Sujet ou titre de cette collection** distingue leur contenu, par exemple
  Alimentation ou Équipement.
- **Référence d’origine** conserve le nom de l’archive et son titre initial.

Les fichiers, éditions, langues et boutons d’ouverture restent inchangés. Les
noms corrigés sont utilisés par le filtre local et le sélecteur de recherche.
Les anciens liens visant la source d’origine restent acceptés. Les groupes
ouverts et filtres restent mémorisés au retour et au rechargement.

Le regroupement automatique utilise la source et les variantes connues du nom
d’archive ; pour un sujet inconnu, il garde le titre disponible ou la référence
au lieu d’inventer une traduction. Les libellés insuffisants peuvent donc encore
demander une relecture. **Revenir aux noms automatiques** retire la correction.
Un fichier modifié demande aussi de revoir ses noms corrigés.

## Conserver les corrections

**Mon appareil → Paramètres → Entretien et données → Conserver les classements et les dossiers pratiques → Classements et noms corrigés → Exporter les métadonnées**
télécharge les références, états et corrections. Il ne contient ni texte des
documents, ni conversations, ni identité de l’auteur des corrections. Les références
et noms saisis figurent bien dans ce fichier. L’import de cet export n’est pas
encore proposé ; il sert à conserver et examiner les corrections.

Les corrections sont enregistrées dans `settings` de `state/pilot/pilot.db`,
avec le préfixe `catalogue:v1:`. La sauvegarde habituelle de l’état les conserve,
sans nouvelle migration. Dix mille corrections au total sont admises ; les
autres documents restent recherchables par le classement automatique. Cette
limite ne plafonne pas le téléchargement ni la taille de la bibliothèque.

Si une correction est illisible, la recherche garde les autres corrections et
utilise l’indication automatique pour le document concerné, en signalant le
problème. Une erreur de ce module ne supprime aucun document du fonds global.

La relecture du fonds de Marc reste nécessaire : l’outil permet les corrections,
il ne prouve pas que toutes les ressources sont déjà qualifiées ou bien nommées.
