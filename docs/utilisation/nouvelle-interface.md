# Utiliser le portail sur ordinateur et téléphone

**Guide actuel — 0.49.0, 18 novembre 2026.**

La nouvelle organisation est l’entrée habituelle du portail, sur Windows comme
sur Linux. Elle utilise les mêmes données et API que l’interface classique.
Les données de production ne sont pas remplacées par les exemples de la maquette.
La maquette fictive reste séparée sous `/maquette/`.

## Se repérer

Le numéro de la version installée apparaît dans la barre supérieure.
Sur ordinateur, la jauge **RAM / VRAM** ouvre l’état de l’appareil. Elle se
compacte sur un écran plus étroit.

Quand vous ouvrez un document depuis une recherche sur ordinateur, le volet
des résultats défile à côté du lecteur et indique le résultat ouvert. Sur
téléphone, utilisez **Résultats** pour retrouver la liste.

| Rubrique | Usage |
| --- | --- |
| Accueil | Rechercher, ouvrir une collection, aller à l’assistant ou aux cartes |
| Bibliothèque | Collections réellement présentes, recherche, parcours, favoris et traductions |
| Assistant | Conversations, documents associés, traduction, dictée, sources et modes de réponse |
| Cartes | Accès direct à la carte réelle, aux repères et aux itinéraires existants |
| Mon appareil | Vue d’ensemble, travaux en cours et paramètres par usage |

Dans Bibliothèque → Collections, **Ouvrir cette collection** ouvre directement
son lecteur Kiwix local, sans question ni recherche préalable. Les guides gardent
leur lecture, leur PDF, leurs favoris et la possibilité de poser une question.

Depuis 0.45.1, **Tout**, **Vidéos**, **Guides** et **Livres et encyclopédies**
sont accessibles en haut de Collections. Choisissez **Vidéos** pour afficher
directement les vidéos locales et celles des archives. Les guides dont les
titres commencent par le même nom de série suivi d’un tiret long sont regroupés
en séries, par exemple *Where There Is No Dentist*. Depuis 0.48.1, les séries
de guides et les groupes de collections apparaissent en tête de leur rubrique
sous forme de cartes. Une carte indique le nombre de ressources et s’ouvre sur
toute la largeur pour les afficher. Le filtre
ouvre les groupes correspondant à ses mots et chaque chapitre reste ouvrable.
Vous pouvez aussi déplier ou replier chaque grande rubrique par son titre.
**Effacer le filtre** efface les mots saisis dans la rubrique courante.
Depuis 0.47.1, le navigateur retrouve vos rubriques et groupes ouverts ou repliés
pour le profil sélectionné. Un filtre peut ouvrir provisoirement les groupes
correspondants. Le titre de la rubrique en cours reste sous la navigation pendant
le défilement et permet toujours de la replier. Depuis 0.48.0, les titres
détachés de la navigation restent dans leur rubrique et se distinguent des
cartes par un fond et une ombre. Les vidéos séparent la lecture, les commandes
de sous-titrage et l’entretien de la vidéothèque.

Sur PC, **Outils** donne accès à **Open WebUI**, aux fonctions avancées et au
secours documentaire. Sur téléphone, les liens restent dans la navigation.
Open WebUI conserve son historique distinct. Les sources originales et l’accès de secours restent disponibles.

Depuis 0.1.36, les archives d’une source connue ou de même titre sont regroupées
avec des variantes et leurs liens directs conservés. Les groupes ouverts sont
mémorisés. **Apprendre par thème** indique l’usage de l’ancien onglet Parcours.
La [recherche documentaire](recherche-documentaire.md) explique le classement,
les filtres et **Mon appareil → Paramètres → Entretien et diagnostics → Vérifier la recherche**.

Depuis 0.1.34, le champ **Chercher une ressource installée** filtre les
encyclopédies, livres et guides de Collections par nom, nom de fichier,
description et langue, sans tenir compte des accents ou majuscules. Plusieurs
mots peuvent être saisis dans un ordre différent. Les boutons d’ouverture restent
ceux des cartes habituelles. Le compteur
distingue les correspondances de celles réellement disponibles à la lecture.

Ce filtre n’ouvre pas le contenu des archives et ne lance ni IA ni téléchargement.
Aucune correspondance dans les titres ne prouve l’absence d’un sujet dans les
articles. **Chercher aussi à l’intérieur des documents** reprend les mots saisis
dans l’onglet Rechercher. Le filtre est conservé par profil et figure dans
l’adresse, pour le retour navigateur et le rechargement.

L’onglet **Cartes** ouvre désormais directement la page cartographique. Le relief
est affiché par défaut lorsque des altitudes locales sont disponibles. On peut
le masquer ou le réactiver dans Affichage. Une zone dépourvue d’altitudes garde
son fond de carte ; aucune préparation ou connexion Internet n’est déclenchée.
Le lien de retour mène à l’accueil, sans écran intermédiaire ni boucle vers la carte.
Si le navigateur ne peut pas afficher la carte, une explication apparaît dans
son espace de lecture avec un retour à la bibliothèque. Cela ne signifie pas
que vos lieux ou trajets enregistrés sont perdus.

**Mon appareil → Paramètres** propose quatre entrées : **Profils et connexion**,
**Bibliothèque et préparations**, **Assistant**, **Entretien et diagnostics**.
Les options avancées se déplient ; les détails apparaissent sur la carte correspondante dans **File d’attente**.
Le [guide des paramètres](parametres-et-appareil.md) donne les chemins et la
correspondance complète des commandes. Le profil Famille propose la gestion ;
chacun peut le sélectionner sans mot de passe.

## Suivre le serveur et les téléchargements

Depuis la 0.43.2, le bloc **Modèle chargé** et les jauges **RAM** et **VRAM**
tiennent dans la ligne de navigation sur ordinateur, y compris dans les Cartes.
Sur écran étroit, ouvrir **Mon appareil → Vue d’ensemble**. La barre supérieure
des Cartes conserve les cinq destinations visibles sur téléphone. Voir les
[mesures de l’assistant](mesurer-assistant-et-memoire.md#voir-le-modèle-chargé-la-ram-et-la-vram).

Les mesures décrivent le PC serveur, pas le téléphone qui consulte la page.
Mémoire, GPU, modèles chargés, espace libre et questions utilisent les mesures
existantes du contrôleur, sans démarrer de modèle. Une mesure absente reste
indisponible ; l’arrêt volontaire ou le mode jeu ne signifie pas panne de lecture.

Le suivi documentaire rassemble les opérations web et les transferts indépendants
qui enregistrent leur identité et leur plan. Il fonctionne sur les deux systèmes :

- Tâches web Windows/Linux : état du gestionnaire documentaire et son plan.
- Reprise Windows déjà configurée : métadonnées du superviseur existant.
- Nouveaux transferts directs Windows/Linux : petit état commun écrit au lancement
  par le téléchargeur, sous `diagnostics/content-transfer.json` et
  `catalog/active-content-plan.json`. Ces fichiers ne contiennent pas de jetons ni de journaux.

Un ancien transfert direct Linux sans métadonnées d’identité/plan ne peut pas être
reconstitué avec certitude ; la page ne prétend pas le suivre. Les préparations
sont toujours lancées explicitement. Fermer ou ouvrir une page ne les relance pas.

Le volume **vérifié d’après les reçus** désigne le contrôle enregistré pour le
plan suivi. Le site ne relit pas des centaines de Go pour refaire les empreintes
à chaque actualisation. Un reçu n’établit pas à lui seul qu’un fichier a été
conservé, qu’il est ouvert par Kiwix ou que sa recherche est prête. Les états de
lecture se trouvent dans Collections ; les étapes reçues, vérifiées et disponibles
pour la recherche restent distinctes.

Les fichiers actifs affichent leur volume et la vérification lorsque le volume
attendu est atteint. Sous Windows, la taille est lue via un handle partagé pour
éviter les tailles d’annuaire périmées, sans bloquer l’écrivain. La lecture n’ouvre
aucune base SQLite, ne lit pas de gros contenu et ne touche pas aux verrous.

Le suivi indépendant reste **en lecture seule**. Pendant un transfert Windows
indépendant actif, la nouvelle interface refuse de lancer une préparation concurrente.
Pour les tâches web, les préparations restent sur ordinateur ; leurs commandes
de pause restent aussi accessibles sur téléphone.
Un état trop ancien ou un service absent est signalé, sans conclure que le processus
est arrêté. Aucune durée restante ni mesure CPU n’est inventée.

## Retour visuel des commandes — 0.37.0

Le bouton **Documents** de réouverture reste à droite, près de son volet.
Les volets se replient et s’ouvrent progressivement ; les changements de page,
les résultats de recherche, les documents, les menus et les fenêtres ont des
transitions courtes. Les aides ouvertes pendant un changement de page gardent
leur position. Les commandes restent immédiates : une animation n’attend
pas avant de lancer une action et ne remplace pas un message de réussite ou
d’erreur. Le réglage système de réduction des animations est respecté, y compris
dans les cartes et le lecteur PDF.

## Navigation confortable

Précédent/Suivant suivent les changements de rubrique, les recherches, les documents
et les conversations. Les adresses peuvent être copiées et ouvertes dans un
nouvel onglet. Les anciens liens `#library`, `#chat`, `#data`, `#settings`,
`#monitor`, `#connect` et `#users` restent compris par le nouveau portail.

Les sous-rubriques, requêtes/filtres, volets de lecture existants et brouillons
sont conservés selon leur contexte. La navigation et les brouillons de la nouvelle
interface sont mémorisés dans ce navigateur, par profil, avec expiration après
sept jours sans mise à jour ; les conversations et favoris restent sur le serveur.
Le contexte courant d’historique reste propre à l’onglet navigateur. Une adresse
explicite reste prioritaire sur le dernier écran mémorisé.

Le brouillon n’est jamais envoyé automatiquement. Pendant le chargement d’une
conversation, la saisie attend le bon contexte pour ne pas mélanger les brouillons.
La suppression de la mémoire locale, dans Paramètres → Entretien et diagnostics, ne supprime pas les données
du serveur. Un profil ou document supprimé ne peut pas être recréé depuis cette
mémoire. Les contrôles de changement de profil et d’onglets périmés restent actifs.

## L’assistant sur ordinateur

La barre de navigation principale est en haut. L’assistant utilise l’espace disponible :

- **Conversations** à gauche : nouvelle discussion, recherche dans les titres et messages, dossiers personnels et liste paginée. Sur ordinateur, glissez une conversation sur un dossier pour l’y ranger : la cible est mise en évidence et le déplacement est confirmé. Déposez-la sur **Sans dossier** pour retirer son classement. Le menu d’une conversation permet aussi de la renommer, de la déplacer ou de la supprimer, notamment au clavier et sur téléphone. Supprimer un dossier conserve ses conversations.
- **Discussion** au centre : messages, dictée, saisie et temps de réponse. Les trois modes conseillés restent proposés ; les modèles de comparaison sont disponibles dans les options de réponse.
- **Documents** à droite : documents choisis pour travailler, traduction et synthèse ; une zone séparée donne les sources réellement consultées quand ce suivi est disponible.

Chaque volet porte une flèche de fermeture dans son en-tête. Son bouton
**Conversations** ou **Documents** apparaît dans l’en-tête de la page quand il est
fermé. Sur téléphone, fermer le volet ramène à la discussion. La commande
**Nouvelle discussion** reste disponible et n’apparaît qu’une seule fois. Les choix documentaires ne sont
pas une preuve de lecture par l’IA ; un ancien échange sans suivi ne reçoit pas
une liste de lectures inventée. La commande **Traduire** ouvre la bibliothèque
pour choisir un document, sans lancer le moteur.

À l’accueil, **Reprendre** donne accès au dernier document ouvert dans ce
navigateur et à la discussion mémorisée, pour le profil courant. Dans **Mon
appareil → File d’attente**, les traductions et synthèses à suivre rejoignent les autres
tâches. Les travaux récents terminés se retrouvent dans **Historique récent**.

## Lire et traduire sur place

Dans un document anglais, **Traduire en français** ouvre la préparation à côté
du texte. Si des travaux existent, le bouton devient **Traduction : ouvrir ou
reprendre**. Choisir un travail existant ou une nouvelle traduction, vérifier
les pages et le mode, puis démarrer explicitement. Les passages terminés restent
lisibles pendant le travail, avec **Comparer avec l’original**, les avertissements,
la pause, la reprise, l’arrêt et le téléchargement. La conversation courante
reste inchangée ; un lien ouvre celle du travail si nécessaire.

Dans le lecteur PDF dédié, **Traduire ce PDF** ouvre les mêmes commandes et
**Revenir au PDF** retrouve le fichier en place. **Lire en français** conserve
son rôle : lire une version déjà publiée, sans relancer une traduction. Voir le
[guide documentaire](documents-et-traduction.md) pour publication, confidentialité
et limites des contrôles automatiques.

## Téléphone

La barre du bas donne accès aux cinq rubriques. Dans l’assistant, les boutons
Conversations et Documents ouvrent le volet correspondant ; sa flèche de fermeture
ramène à la discussion. Recherche, documents, assistant,
cartes réelles et suivis restent accessibles. La sélection documentaire, les
préparations de zones et les commandes complexes restent sur ordinateur, avec
une indication dans la page. Les restrictions existantes des cartes pour la
création de repères/trajets sur petit écran sont conservées.

Les pages natives PDF et Cartes gardent un lien de retour vers l’interface dont
elles proviennent. La dictée conserve ses prérequis HTTPS et navigateur.
Safari iPhone réel reste à essayer ; les tests WebKit ne le remplacent pas.

## Présentation précédente conservée

Les boutons de retour à l’interface classique et **Faire un retour** ont été
retirés de la nouvelle interface à la demande de Louis. Pour comparer
ponctuellement, ouvrir directement `/classique/` sur le même serveur.
Elle conserve ses propres HTML, CSS et scripts. Les lecteurs tiers volumineux et
les API sont partagés ; profils, conversations, favoris et données ne sont pas
copiés. Une bascule n’arrête aucune opération et ne restaure aucune base.
La nouvelle présentation reste aussi accessible explicitement sous `/nouveau/`.

## Installer et mettre à jour

Les pages font partie du logiciel portable : aucune dépendance Windows, aucun
service frontend supplémentaire et aucun téléchargement de ressources externes.
Une nouvelle installation Windows ou Linux les sert avec le Caddy existant.
Pour une installation existante, utiliser la
[mise à jour normale](../exploitation/mises-a-jour-et-bibliotheque-pilote.md),
puis recharger la page. Un `git pull` d’un dépôt de maintenance ne remplace pas
le logiciel installé. Attendre la fin ou la pause effective des transferts avant
la procédure normale ; le téléchargement de Marc a été déclaré terminé par Louis,
mais ce guide n’en fait pas un contrôle de machine.

Les vérifications de la refonte sont dans le [bilan 0.34.0](../essais/2026-11-16-refonte-ux.md).
Le [bilan 0.12.0](../essais/2026-11-14-parametres-ux.md) conserve les résultats historiques des paramètres.
Le [bilan 0.1.36](../essais/2026-11-14-moteur-recherche-utile.md) conserve les
constats de la précédente évolution documentaire.


## Projets dans le volet Conversations — 0.38.0

Dépliez un projet pour afficher ses conversations juste dessous. Les anciens
dossiers restent conservés. Le menu à côté du projet permet de le renommer ;
celui de chaque conversation propose aussi **Renommer**. Le classement par
glisser-déposer et par menu reste disponible. Les conversations sans projet
restent dans la liste générale ; la recherche porte aussi sur les projets.

Sur PC, faites glisser la séparation à droite du volet pour ajuster sa largeur.
Au clavier, sélectionnez la séparation et utilisez Gauche/Droite, Début ou Fin.
Le volet défile verticalement quand les projets et conversations dépassent.
Les projets ouverts restent mémorisés dans cet onglet, par profil.


Les vérifications et leurs limites figurent dans le
[bilan du volet par projets](../essais/2026-11-17-projets-assistant.md).
