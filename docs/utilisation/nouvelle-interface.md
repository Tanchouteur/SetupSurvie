# La nouvelle interface et l’interface classique

**Candidat UX 0.33.0 :** titres directs, aides facultatives au clic/survol/clavier,
lecture prioritaire et collections plus proches sur PC et téléphone. Le travail
complet (traduction dans le lecteur et assistant en trois zones) reste en cours :
voir le [suivi UX](../decisions/refonte-ux-evolutive.md).

**Guide actuel — 0.12.0, 14 novembre 2026.**

La nouvelle organisation est l’entrée habituelle du portail, sur Windows comme
sur Linux. Elle utilise les mêmes données et API que l’interface classique.
Les données de production ne sont pas remplacées par les exemples de la maquette.
La maquette fictive reste séparée sous `/maquette/`.

## Se repérer

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
Le lien Open WebUI reste visible pour les fonctions avancées et ses historiques
distincts. Les sources originales et l’accès de secours restent disponibles.

Depuis 0.1.36, les archives d’une source connue ou de même titre sont regroupées
avec des variantes et leurs liens directs conservés. Les groupes ouverts sont
mémorisés. **Apprendre par thème** indique l’usage de l’ancien onglet Parcours.
La [recherche documentaire](recherche-documentaire.md) explique le classement,
les filtres et **Mon appareil → Paramètres → Entretien et diagnostics → Vérifier la recherche**.

Depuis 0.1.34, le champ **Chercher une ressource installée** filtre les
encyclopédies, livres et guides de Collections par nom, nom de fichier,
description et langue, sans tenir compte des accents ou majuscules. Plusieurs
mots peuvent être saisis dans un ordre différent. Les boutons d’ouverture restent
ceux des cartes habituelles ; **Tout afficher** retire le filtre. Le compteur
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

**Mon appareil → Paramètres** propose quatre entrées : **Profils et connexion**,
**Bibliothèque et préparations**, **Assistant**, **Entretien et diagnostics**.
Les options avancées se déplient ; le suivi reste dans **Travaux en cours**.
Le [guide des paramètres](parametres-et-appareil.md) donne les chemins et la
correspondance complète des commandes. Le profil Famille propose la gestion ;
chacun peut le sélectionner sans mot de passe.

## Suivre le serveur et les téléchargements

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

Depuis 0.1.35, **Conversations** ouvre l’historique et les dossiers dans une
fenêtre dédiée. Choisir une conversation ferme cette fenêtre et conserve son
adresse pour Précédent/Suivant. La réponse occupe une colonne de lecture limitée,
avec un texte de 16 pixels et une saisie compacte qui reste accessible.
L’accueil propose **Qu’avez-vous envie d’apprendre ?**.

## Téléphone

La barre du bas donne accès aux cinq rubriques. Recherche, documents, assistant,
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

Les vérifications de cette organisation sont dans le [bilan 0.12.0](../essais/2026-11-14-parametres-ux.md).
Le [bilan 0.1.36](../essais/2026-11-14-moteur-recherche-utile.md) conserve les
constats de la précédente évolution documentaire.
