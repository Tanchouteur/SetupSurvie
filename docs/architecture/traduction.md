# Architecture — traduction

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Association documentaire et traduction — 0.1.16

Les associations sont stockées dans `conversation_sources`, sans modifier les anciennes lignes des conversations. `translations` et `translation_parts` conservent les travaux privés, le texte source de chaque passage, son numéro de page et le modèle qui l’a traduit. Ces ajouts SQLite sont non destructifs ; le contrat de données reste 1. Les associations anciennes absentes ne sont pas reconstruites à partir de citations ambiguës.

`pilot/translations.py` extrait l’original PDF dans un thread, borne la préparation puis traite les passages avec un schéma de réponse Ollama. Le contenu à traduire est fourni comme message utilisateur ; l’historique d’un refus précédent n’est pas réinjecté. Le worker partage `engine.LOCK` avec le chat et vérifie le contrôleur avant chaque passage. Il enregistre le résultat seulement si la traduction est toujours active. Le redémarrage du pilote met les travaux actifs en pause ; aucune inférence ne reprend au démarrage. Les exports restent rattachés au profil choisi, librement sélectionnable depuis 0.1.29. Depuis 0.1.25, les nouvelles traductions terminées rejoignent le fonds public sous forme de HTML identifié, sans texte de conversation ; les anciennes restent privées jusqu’à publication explicite.

Le [guide d’utilisation](../utilisation/documents-et-traduction.md) précise les limites de texte, la pagination, les images et les validations restantes.

## Lecture et défaillances partielles — 0.1.25

`pilot/publications.py` publie les traductions sans garder le verrou d’inférence.
Une intention dans `settings`, enregistrée avec la traduction, permet de reprendre
une publication interrompue ; `translation_publications` conserve la provenance
indépendamment des conversations. Le fichier est écrit durablement, l’index est
mis à jour dans une transaction, puis la publication est marquée terminée. Un
nouvel essai identique ne réécrit pas le fichier. Les erreurs conservent le texte
privé et ne font pas échouer une traduction déjà terminée.

`pilot/favorites.py` gère les favoris par propriétaire. La recherche filtre les
sources avant la limite de résultats ; les articles Kiwix ont un instantané FTS
personnel. Les routes optionnelles chargent leur module à la demande et renvoient
une erreur 503 localisée en cas de panne. L’état `/api/health` expose les noms des
fonctions dégradées. La réindexation et la récupération des publications ont des
délais de démarrage bornés ; SQLite et le système de fichiers restent communs.

`portal/documents.js` enrichit le portail séparément. `pdf.html` et PDF.js ont leur
propre contexte JavaScript ; les fichiers PDF sont chargés depuis le serveur
statique, indépendamment de l’API. Un petit script distinct conserve les liens
d’ouverture et de téléchargement si le rendu échoue. `secours.html` consulte une
liste statique de fichiers publics, sans comptes ni favoris. Une panne de génération
de cette liste ne fait pas échouer l’indexation de recherche.


Depuis 0.1.26, `scripts/content_mirrors.py` classe les miroirs Kiwix à partir du
Metalink vérifié par taille et SHA-256. `scripts/content.py` possède un seul
verrou de lot et jusqu’à trois transferts réseau ; un verrou de métadonnées
protège les reçus et un verrou d’écriture associe contrôle de capacité et
écriture. Les commandes et l’installateur utilisent deux transferts par défaut.
Voir le [guide des transferts](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#miroirs-et-transferts-simultanés-depuis-0126).

## Contrôles de traduction — 0.1.28

`pilot/translation_quality.py` compare les occurrences de nombres normalisés et
les associations avec une liste limitée d’unités. Ces anomalies bloquent le passage ;
les écarts de longueur et négations non retrouvées sont des avertissements. Le
worker enregistre contrôle, résultat accepté ou proposition refusée et état dans
une même transaction. La table additive `translation_checks` conserve un rapport
versionné par passage et la proposition rejetée, avec suppression en cascade de
la traduction. Les anciennes lignes restent explicitement sans contrôle.

Le contrôle intervient avant de compter le passage comme terminé. Son exception
interrompt uniquement cette traduction ; la recherche et les documents restent
accessibles. La publication recontrôle les passages ayant un rapport, sans
réécrire les anciens fichiers. Les avertissements sont échappés comme texte dans
le HTML partagé et conservés dans l’export. L’API propriétaire expose aussi le
texte source pour comparaison ; celui-ci n’est pas ajouté au HTML public.
Aucun moteur supplémentaire ni contrat de données incompatible n’est introduit.

## Cycle du modèle de traduction — 0.20.1

`translations.translate` utilise désormais les métadonnées locales fraîches,
le contexte configuré limité par le modèle, le budget d’entrée/sortie commun et
`model_session.Session` pour la préparation et la reprise bornée. Le texte du
passage reste inchangé lors d’un essai supplémentaire. La file commune reste
libérée entre fragments ; une pause observée pendant la préparation laisse le
travail en pause, sans le transformer en traduction terminée.
La recette réelle peut observer des mesures numériques par rappel local ; ce
n’est pas un nouvel export de mesures de traduction dans le produit.
Les contrôles de fidélité conservent leurs seuils et comparaisons ; leur version 2
ajoute un avertissement pour certains blancs de touches/valeurs et caractères de
remplacement du texte source. Les rapports historiques ne sont pas recalculés.

## Lecture française intégrée — 0.21.0

`translation_reader.py` propose deux API publiques de lecture seule :
`GET /api/library/french-reading?original_id=…` liste au plus douze versions
publiées ; `GET /api/library/french-page?id=…&original_id=…&page=…` lit une page.
La seconde vérifie le lien traduction/original et ne lit que le fichier HTML
partagé, jamais `translation_parts`, les brouillons, candidats refusés ou comptes.
Les réponses ne contiennent ni identité ni conversation. Les API et le client
refusent la réutilisation d’un cache HTTP périmé.

L’extraction conserve un repère `stat-v1` stable avant/après lecture ; un changement
observé refuse l’instantané. Le repère d’origine, les pages publiées et le SHA-256
du fichier partagé sont ajoutés aux métadonnées JSON existantes, sans migration
des anciennes données. Une source modifiée ou une ancienne correspondance inconnue
reste explicite. Ce repère taille/date n’est pas un hash de tout le fonds.
La publication reste indépendante de la conversation et garde les règles de
partage/annulation de la version précédente.

Lister les versions ne parse pas les livres. À l’ouverture d’une page française,
le module contrôle chemin, absence de liens symboliques, taille bornée, stabilité
du fichier et empreinte publiée lorsqu’elle existe. Il extrait uniquement les
paragraphes français et avertissements des sections. Un cache reconstructible
conserve au plus seize fichiers et 64 millions d’octets de fichiers lus, avec
chemin/taille/date/empreinte comme clé ; ce n’est pas une limite mesurée de RAM.
Un fichier modifié ne devient pas silencieusement une traduction validée.

`bilingual-reader.js` s’ajoute aux événements de lecture du portail et à la page
PDF, avec CSS séparée. Le texte est rendu par `textContent`, sans interprétation
HTML des documents. L’original reste accessible en échec. La pagination PDF et
les pages françaises se synchronisent sans appeler l’IA. Le choix de langue est
mémorisé dans le navigateur ; le routeur existant conserve la navigation documentaire.
Aucune intégration dans l’interface native Kiwix, traduction d’image, glossaire ou
transcription vidéo n’est ajoutée par ce lot.

## Essai de traduction longue — 0.25.0

`translation_benchmark.py` génère un PDF fictif, partage `document_text.pdf_texts`,
`chunks`, `translations.translate` et les contrôles ordinaires. L’état privé est
séparé des conversations/traductions publiables ; rapport numérique, texte de
travail et PDF sont conservés séparément. Les écritures sont durables et les
passages acquis ne sont pas regénérés lors d’une reprise explicite. Le thread
d’extraction est rejoint à l’annulation et le verrou d’inférence est partagé
par passage. Une garde contrôlée pendant l’appel donne priorité à l’usage normal
et au mode jeu. Le dernier rapport contient les mesures après chaque tentative.
Le sous-menu Tests déplace les nœuds existants dans `view-settings`, avec liens
de requête pour ouvrir une rubrique précise, état mémorisé et historique conservés.

## Lecture pendant une traduction — 0.28.0

`translations.status()` conserve l’accès par propriétaire et la pagination de dix
passages ; ses compteurs ajoutent pages entièrement terminées, pages partielles,
pages illisibles, page en attente et dernière position traduite. Un passage ou
une page illisible ne compte pas comme traduit. Aucun texte ne passe au modèle
pour produire ces compteurs.

Le portail conserve les éléments DOM inchangés pendant le rafraîchissement. Le
lecteur dédié déplace les mêmes éléments `translation-parts` et leurs commandes
vers `translation-reading-content`, puis les remet à leur place à la fermeture ;
il ne faut pas cloner leurs IDs lors d’une future refonte. Depuis 0.58.0,
le bandeau de l’Assistant héberge les commandes et les passages reviennent
dans le fil après fermeture de la fenêtre. Le repère local par
profil/traduction contient seulement offset, ouverture et date, avec cent entrées
au maximum. Une seule restauration d’ouverture par chargement évite une course
avec la fermeture. Les travaux et textes restent côté serveur ; la mémoire du
navigateur ne commande jamais une reprise d’inférence.

Les requêtes de la page et du lecteur bilingue sont annulées dès `beforeunload`,
puis à `pagehide`. Depuis 0.36.1, `PAGE_CLOSING` empêche aussi un minuteur de
relancer un appel `api()` pendant cette fermeture : il reçoit localement
`AbortError`, sans nouvelle requête. `pageshow` réautorise les appels après
restauration. L’annulation connue d’un contrôleur conserve ce type d’erreur ;
une autre panne réseau reste propagée. L’aperçu PDF possède son port Worker dès sa création, attend
le signal de disponibilité avant de le confier à PDF.js et peut donc le terminer
même pendant son chargement. Le traitement reste dans un Worker natif ; ni
PDF.js ni ses composants épinglés ne sont modifiés. La file d’aperçus abandonne
sa génération précédente après navigation. Les lecteurs savent repartir après
`pageshow` persistant quand le navigateur réutilise la page. Les annulations du
port connu sont prises en charge localement ; les erreurs du composant actif
ne sont pas filtrées globalement. Les recettes simulent ces états et conservent
les essais natifs de rendu et les assertions d’erreur.

## Contrôle des traductions — 0.29.0

Les routes pause, stop, resume et DELETE d’un travail partagent `CONTROL_LOCK`.
L’arrêt conserve `stopped`, repris seulement explicitement ; l’initialisation ne
le réécrit pas comme une tâche à reprendre automatiquement. La suppression rejoint
le worker avant de supprimer la ligne et ses enfants, et garde les publications
indépendantes. Le verrou de publication est acquis pour éviter une écriture
concurrente. La publication attend aussi son thread après annulation avant de
relâcher ce verrou : une coroutine annulée n’est pas une preuve d’arrêt du thread.
Les contrôles principaux se déplacent avec le lecteur ; leurs IDs restent uniques.

## Cohérence des traductions — 0.32.0

`translation_terms.py` conserve les termes par profil dans `settings`, puis une
copie immuable dans `translation_guidance` (clé étrangère à `translations`,
suppression en cascade). Les anciennes lignes sans copie n’adoptent pas les
nouveaux réglages. GET/PUT `/api/translation-terms` lisent seulement le profil choisi ;
ils ne lancent ni modèle ni traduction.

Chaque fragment reçoit ses termes présents et au plus les 600 derniers caractères
source/français du fragment immédiatement précédent terminé. Les données sont
séparées du passage courant dans le message utilisateur ; aucune substitution
de mots après génération. Ce contexte est retiré avant appel s’il dépasse le
budget. Le contrôle conserve les termes proposés, la position précédente proposée
et l’usage effectif du repère rapporté par l’appel (inconnu si non mesuré).
Les mesures numériques ne contiennent pas les termes ou extraits.

Une forme française non repérée produit un avertissement, sans certifier une erreur
sémantique. Les nombres/unités restent bloquants. Le contrôle version 3 inclut les
nombres joints à des lettres, pour ne pas rejeter l’espace rétabli dans `Chapter4`.
Les rapports antérieurs et les publications existantes restent conservés. La file,
la pause, l’arrêt et la publication complète gardent leurs contrats.
