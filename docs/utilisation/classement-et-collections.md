# Classer les documents et nommer les collections

**Guide actuel — actualisé pour la 0.65.0, 20 novembre 2026.** Ces corrections se font depuis le
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
  Il alimente **Autonomie et résilience** et **Savoirs et culture** ; ce dernier
  applique aussi le classement documentaire.
- **Autre** : la collection reste sur l’appareil et se lit normalement. La
  recherche ne la consulte que si l’on choisit **Autre** ou **Toute la
  bibliothèque**. L’assistant applique les mêmes choix.
- **Supprimer** : efface les fichiers du PC serveur et exclut la collection des
  prochains téléchargements, éditions suivantes et plans repris compris.

Les collections sont regroupées par famille (Wikipédia, Gutenberg…, puis
**Vidéos téléchargées**), des plus volumineuses aux plus petites. Chaque ligne
montre le nom lisible, le type, la taille, la description du catalogue quand
elle existe, le nom du fichier et un lien **Aperçu ↗** qui ouvre la collection
dans Kiwix pour vérifier ce qu’elle contient. L’interrupteur **Principal / Autre**
de chaque ligne enregistre le choix immédiatement. Pour agir sur plusieurs
collections, cochez-les (ou cochez la famille entière) : une barre en bas de page
propose **Fonds principal**, **Autre** ou **Supprimer…**. La suppression passe
par une confirmation qui nomme les collections, le volume libéré et les fichiers
concernés, y compris les fichiers partiels. Elle est suivie dans la file
d’attente sous le titre **Suppression de collections**.

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

## Classer Wikipédia par espace

Le **classement de Wikipédia par espace** (appelé « index par catégorie » en
0.64) se trouve dans **Mon appareil → Paramètres → Bibliothèque et préparations
→ Préparer la recherche dans les archives**. Il range chaque article de Wikipédia
en français dans **Autonomie et résilience** ou **Savoirs et culture**, puis la
recherche interroge l’index de l’espace choisi. **Toute la bibliothèque**
continue de consulter l’archive complète. Pendant la préparation ou après une
modification, l’archive complète répond.

Le panneau indique le pourcentage d’articles examinés et le nombre d’articles
trouvés pour chaque espace, puis le temps écoulé et la place occupée. La file
d’attente suit la même tâche sous le titre **Classement de Wikipédia :
Autonomie et Savoirs**, avec ce pourcentage ; en 0.64 elle apparaissait à tort
comme « Téléchargement de la bibliothèque ». Le titre de la carte ramène à ce
panneau.

Une nouvelle édition ou une correction de catégorie rend le classement à
refaire. SetupSurvie le relance pendant la plage d’indexation configurée. Une
interruption reprend au dernier lot enregistré si l’archive et les corrections
correspondent toujours. Un échec ponctuel de connexion au PC serveur n’efface
plus l’état affiché ; un message clair n’apparaît qu’après plusieurs échecs.

## Comprendre le classement automatique

Pour Wikipédia, le classement tient compte du titre, des sections principales
et des catégories d'article quand elles sont présentes dans l'archive locale.
Un article peut appartenir aux deux espaces. L'indication peut évoluer à la
fin d'une recherche progressive, après lecture de la structure. Si un résultat
attendu manque, élargir à **Toute la bibliothèque** puis corriger son
classement si nécessaire.

Le [protocole de mesure](../essais/mesurer-classement-documentaire.md) permet
de comparer deux versions sur les mêmes documents et vidéos.

## Corriger le classement d’un document

1. Ouvrir le document depuis les résultats, puis **Corriger le classement** au
   bas de l’aperçu.
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

La correction s’applique à l’article ZIM ou au document entier ; les pages d’un
même PDF partagent le classement. Elle ne modifie ni le fichier ni ses liens.
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

**Mon appareil → Paramètres → Entretien et diagnostics → Conserver les classements et les dossiers pratiques → Classements et noms corrigés → Exporter les métadonnées**
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
