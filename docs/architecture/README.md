# Architecture du pilote

Vue de référence documentaire actualisée le 15 novembre 2026. Elle décrit les rôles
des composants ; les [bilans](../essais/README.md) indiquent les validations réalisées.

## Dossiers documentaires — 0.16.0

`pilot/research.py` choisit des passages correspondant aux concepts bilingues de
la question, avec positions dans le texte extrait et budget UTF-8. Il distingue
les documents/pages, élimine les textes identiques et conserve les avertissements
de traduction. `read_sources` est un outil de lecture par lot, limité à douze
candidats et trois lectures simultanées. Le cache de sources est propre à la demande.

La préparation appelle le moteur commun avec le budget documentaire long et
adapte le dossier à la place restante, sans changer modèle ou contexte conseillé.
Le premier tour documentaire spécialise les outils ; les autres outils restent
disponibles aux tours suivants et dès le départ pour une demande géographique.
Une consigne secondaire de réponse reste dans la conversation complète et n’est
pas imposée à la première recherche du sujet principal.

Deux tours sans preuve documentaire nouvelle conduisent à la rédaction. Pour une
synthèse explicite, les références numériques sont contrôlées contre les passages
consultés. `citation_links.py` peut demander une association JSON de fragments
numérotés par le serveur et de sources lues, sans régénération des faits.
Ce contrôle ne vérifie pas le sens. Un échec conserve le texte utile avec avertissement,
ou les extraits si une source inconnue est citée, et l’état incomplet/échoué. Les propositions refusées
restent dans les traces privées, en dehors des mesures numériques.
Les instructions sont regroupées dans le premier message système pour éviter
une fin de conversation système sans marqueur de génération dans certains modèles.
Le lecteur de métadonnées reconnaît aussi les modèles dont le gabarit ne présente
les outils qu’après le dernier message utilisateur ; leurs définitions de confiance
restent alors visibles après les résultats d’outils, sans élever ces résultats au rôle système.

## Sélection documentaire persistante — 0.17.0

`conversation_document_choices` conserve la liste ordonnée privée des références,
avec cascade sur la conversation. La table historique `conversation_sources`
conserve le premier document pour les anciens lecteurs. Aucune conversation ou
traduction existante n’est convertie destructivement ; le schéma de livraison
reste 1. L’absence de la table optionnelle laisse utilisable l’association simple.
Après un retour à un ancien code, une référence principale retirée ou différente
ne ressuscite pas automatiquement la liste multiple précédente.

L’API `POST /api/conversations` crée une conversation avec une sélection sans IA ;
`PUT /api/conversations/{id}/sources` remplace cette liste après contrôle du profil.
Les questions acceptent `source_ids`, et conservent le champ historique `source_id`.
Le serveur refuse les changements et les doubles questions pendant une réponse.
La lecture réelle au moment de la demande reste distincte du titre enregistré.
Les métadonnées et textes documentaires passent par les résultats d’outils, sans
être élevés au rôle système. La traduction choisit son document et conserve les autres.

Pour un PDF entier, `focused_page` interroge uniquement ses passages déjà indexés,
avec le vocabulaire commun, puis conserve l’identité de la page retenue. Le travail
SQLite se fait dans un thread dont l’annulation attend la fermeture. Une page
explicitement associée n’est pas remplacée ; sans résultat, l’aperçu demeure limité.
Cette sélection n’est ni un OCR ni une synthèse exhaustive de toutes les pages.

## Lecture longue et notes reprenables — 0.18.0

`pilot/document_text.py` partage l’extraction complète avec les traductions :
PDF depuis le fichier d’origine, caractères conservés par segments et pages sans
texte explicites. Un changement de fichier détecté pendant la lecture annule son
instantané. Pas d’OCR. Les plafonds sont documentés dans le [guide](../utilisation/synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180).

`pilot/summaries.py` enregistre les tâches, entrées, textes et notes dans quatre
tables optionnelles `summary_*`, sans migration destructive du schéma 1. Le
parcours crée sa propre conversation, contrôle le profil et partage `engine.LOCK`
par étape. Il utilise `model_session` pour charger le modèle choisi et reprendre
un premier échec transitoire ; pas de changement silencieux de modèle/contexte.
L’arrêt du service attend ses tâches avant de fermer le cache documentaire.
Redémarrer marque le travail en pause et ne relance aucune inférence.

Chaque note initiale désigne un passage et un extrait dont le serveur vérifie
la présence exacte, à des différences d’espacement près. Les regroupements
adressent une note précise par `étape:note`, puis transportent seulement ses
sources et pages. Le graphe et les extraits originaux restent exportables ;
aucun raisonnement privé du modèle n’est conservé. Cette vérification de
provenance ne contrôle pas la fidélité sémantique des notes ni de la synthèse.
Le texte final et, au besoin, sa liaison de références utilisent les mêmes
budgets de contexte. Une sortie tronquée, un JSON invalide ou une citation
inventée ne termine pas son étape. Les brouillons sans références restent
incomplets et reprenables.

Les routes `/api/summaries` créent le travail ; `/{id}` consulte son suivi,
`/{id}/pause`, `/{id}/resume` le contrôlent et `/{id}/export` exporte le Markdown.
`GET /api/conversations/{id}` ajoute `summary_jobs`. La création accepte `question`,
`mode`, `conversation_id` et/ou `source_ids` ; les références sont copiées au départ.
Une tâche active par profil et quatre au total sont admises. Les questions,
changements de sélection et suppressions sont refusés dans sa conversation
active ; une reprise attend aussi la fin des autres travaux de cette conversation.
Les calibrations et comparatifs IA cèdent la priorité. Une panne du module
optionnel ne désactive pas la recherche, la lecture ni les autres conversations.

## Illustrations originales et références — 0.19.0

`pilot/illustrations.py` extrait les légendes HTML5 et anciennes vignettes,
conserve les images locales de la même archive et prépare des candidats issus
des seules sources lues. Les PDF proposent les pages retenues, pas un recadrage
de schéma. Le classement des légendes par sujet et la diversité des sources
précèdent le plafond de contexte. Les métadonnées non retenues restent hors des
paquets de lecture et des réponses API ; elles sont gardées dans l’instantané
privé pour une synthèse longue. Plafonds dans le [guide](../utilisation/illustrations-et-references.md).

Une demande visuelle prépare la sélection avant la rédaction via un petit JSON
sans pixels ; `source_illustrations` permet aussi au modèle de la demander après
ses autres lectures. Le serveur valide les identifiants candidats, conserve la
provenance et refuse les identifiants inventés. Le contrôle ne juge pas le sens
d’une légende ni le contenu d’une image. Les échecs restent locaux à la fonction.
Les champs `figures` et `figure_status` sont ajoutés au JSON des sources de
conversation, sans table ni migration destructive ; schéma de livraison 1.

`portal/source-figures.js` affiche les originaux avec légende et liens. Le rendu
PDF utilise PDF.js existant, un worker partagé, une file de rendu et des aperçus
limités à un million de pixels. Les URL temporaires sont libérées au retrait des
messages ; les ressources se chargent près de la zone visible. Aucun OCR ni
modèle vision. Les erreurs de ressource n’interrompent pas le portail.
`GET /api/illustrations/document` vérifie la référence/page et l’empreinte connue
avant/après le rendu. `/api/media` accepte aussi `source_id` et `revision` pour
les images d’article : même archive, type image et contrôle de version avant/après
lecture. Les paramètres historiques sans source restent compatibles.

`research.citation_spans` reconnaît les références simples, groupées et avec page
hors du code. Les mêmes formes deviennent des boutons dans le portail ; seules
les pages effectivement retenues bénéficient d’un lien direct vers cette page.
Une référence inconnue garde le contrôle d’échec. La validité du numéro ne certifie
ni l’affirmation ni l’usage de la pagination imprimée.

## Procédures ordinaires — 0.19.1

Les demandes « comment… » et de dimensions préparent aussi le moteur commun,
sans liste de modèles d’appareils. La première question sert de sujet de recherche ;
une seconde question garde sa place dans la demande complète mais ne devient pas
une contrainte lexicale de la première. Décimales/abréviations restent intactes.

Si le modèle demande une recherche sans lire aucun résultat, le moteur prépare
un premier paquet de quatre passages candidats au maximum, classés par le moteur
commun, avant sa rédaction. Les appels/résultats restent des paires complètes ;
les lectures explicites suivantes, périmètre et budgets restent disponibles.
Une référence dans une réponse documentaire ordinaire est contrôlée comme dans
une synthèse ; un résultat de recherche ne devient jamais implicitement une lecture.
Pour une lecture préparatoire automatique, les pages d’un même PDF sont comparées
sur le sujet et le début de section, en écartant les mots du titre répétés partout.
La meilleure page de chaque document reçoit la priorité ; les pages explicitement
choisies restent littérales. Les autres passages demeurent accessibles aux outils.
Le contexte produit est condensé pour garder plus de place aux textes utiles,
sans changer modèle ou taille de contexte.
L’allocation répartit les extraits courts entre plusieurs sources selon le budget ;
les omissions et lectures partielles restent explicites.

## Composants

| Composant | Responsabilité | Entrées du dépôt |
| --- | --- | --- |
| Portail servi par Caddy | Navigation, assistant, bibliothèque, cartes et accès aux autres interfaces | [portal](../../portal/), [Caddyfile](../../deploy/Caddyfile) |
| Passerelle FastAPI | Profils locaux sans mot de passe, conversations du portail, recherche, lecture, calcul et suivi | [pilot](../../pilot/) |
| Open WebUI | Comptes natifs, dossiers, conversations avancées et collections propres | [compose.yaml](../../compose.yaml) |
| Kiwix | Consultation illustrée et recherche native des archives ZIM | [Point d’entrée Kiwix](../../deploy/kiwix-entrypoint.sh) |
| Ollama et contrôleur hôte | Inférence locale, état et commandes d’administration du moteur | [Profils](../../deploy/model-profiles.json), [contrôleur](../../scripts/control.py) |

Le portail et Open WebUI reprennent le profil choisi sans mot de passe, mais ont des historiques distincts.
Le pilote indexe les guides et interroge Kiwix ; cela ne crée pas automatiquement
de collections dans Open WebUI. La bibliothèque reste utilisable avec l’IA arrêtée.

Le contexte produit de l’assistant est dans
[assistant-system.fr.txt](../../deploy/assistant-system.fr.txt).
[engine.py](../../pilot/engine.py) ajoute les consignes d’outils, l’historique et
les passages consultés. Ce contexte est distinct d’[AGENTS.md](../../AGENTS.md),
qui guide le développement.

Depuis 0.1.18, les [métadonnées de source](../utilisation/sources-et-fiabilite.md)
séparent date du document, édition, collecte et date du catalogue d’archive.
Une table privée `guide_dates` complète `guide_meta` sans modifier ses cinq
colonnes. Recherche, lecture, contexte du modèle et références enregistrées
transportent ces informations ; le portail distingue une date inconnue.
Les références exposées comme lues sont filtrées avant affichage et conservation.

Les [parcours de savoir-faire](../bibliotheque/savoirs-durables.md) de 0.1.19
utilisent les mêmes règles que la sélection Kiwix : `deploy/kiwix-themes.json`,
monté en lecture seule dans le pilote. L’API publique `/api/library/learning`
fournit uniquement le catalogue des parcours ; la préparation d’une question
reste locale au navigateur jusqu’à son envoi. La grille du sélecteur est un
relevé de métadonnées et de présence, sans validation éditoriale automatique.

Le contrat de livraison est dans [release.json](../../deploy/release.json).

Depuis 0.1.23, [durable.py](../../pilot/durable.py) est partagé par le service et
les scripts hôtes pour publier les fichiers après synchronisation. Les opérations
hôtes utilisent des verrous du système d’exploitation, avec fichier `.lease`
persistant. SQLite conserve WAL et impose FULL ; les états interrompus ne relancent
pas implicitement l’inférence. Voir [la reprise après coupure](../exploitation/coupures-et-redemarrage.md)
pour les limites Windows, les services tiers et les essais matériels restant à faire.
Les références des composants tiers sont dans [versions.json](../../deploy/versions.json).
Les catalogues [documentaires](../../deploy/content-catalog.json) et
[cartographiques](../../deploy/map-catalog.json) décrivent les ressources prévues ;
leur présence dans un catalogue ne prouve pas leur téléchargement.

L’installation portable repose sur [setup.py](../../scripts/setup.py), les
lanceurs Windows/Linux et Compose. L’export du kit, les sauvegardes et les mises
à jour ont des outils dédiés, présentés dans les [procédures d’exploitation](../exploitation/README.md).
Depuis 0.1.17, les [deux lanceurs Windows](../installation/deux-etapes-windows.md)
ajoutent une préparation PowerShell sans Python et une première installation
journalisée dans des dossiers séparés. Le catalogue des installateurs système
est distinct des références des images tierces ; ces dernières ne changent pas.
Le laboratoire Podman de Louis utilise `scripts/linux_lab.py` et `scripts/lab.sh` ;
il reste distinct des installations clients.

Les données, modèles, ZIM, caches et états privés restent hors du code. Les ports
Web par défaut sont 8080/3000/8081 et 8443/8444/8445 pour HTTPS. Les ports internes
11435/11436 ne sont pas destinés aux lecteurs. Voir le [guide réseau](../installation/pilote-marc.md#accès-depuis-tout-le-réseau-local).

La [proposition initiale](../historique/architecture-et-installation-prototype.md)
et la [comparaison NOMAD](../historique/comparaison-nomad-assemblage.md) restent
archivées pour expliquer le cheminement des choix.

La [sélection Kiwix par thème](../bibliotheque/selection-kiwix-par-theme.md) passe
par les routes administrateur du pilote puis le contrôleur hôte authentifié.
Celui-ci lance uniquement les tâches documentaires prévues, avec paramètres
bornés. Leur processus et leur état persistent indépendamment du navigateur et
du contrôleur. Les téléchargements utilisent les vérifications du préparateur ;
ils n’ajoutent aucun outil Internet à l’assistant et ne démarrent aucun modèle.

Le pilote 0.1.10 ajoute les [lieux de référence et outils géographiques locaux](../utilisation/parametres-et-cartes.md) : réglages privés dans SQLite, données OSM/HGT dans `library/maps/geography`, préparation par le contrôleur hôte, recherche et relief sans Internet après préparation.

Le pilote 0.1.11 ajoute les [listes de points et itinéraires hors ligne](../utilisation/points-et-itineraires.md), avec consultation mobile et préparation sur ordinateur.

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

## Profils locaux sans mot de passe — 0.1.29

À la demande de Louis, `pilot/profiles.py` remplace l’authentification du portail
par des identités librement sélectionnables, persistées dans `profiles`. Un cookie
`survie_profile` mémorise un identifiant public, sans secret et utilisable sur
HTTP comme HTTPS ; son absence ou une ancienne valeur revient
au profil Famille. Les lectures de l’ancienne base Open WebUI sont en lecture
seule ; les identifiants existants gardent leurs conversations et favoris.
Le rôle sert à présenter les outils, sans protection entre personnes : chacun
peut sélectionner Famille et ses réglages. Les anciens mots de passe et données
ne sont pas effacés. Les anciennes routes de connexion/récupération renvoient
une invitation à recharger le nouveau portail.

Caddy sert désormais aussi HTTP `3000` et HTTPS `8444` pour Open WebUI. Il retire
les en-têtes `X-Survie-*` entrants puis copie l’identité renvoyée par le pilote.
Open WebUI utilise les variables `WEBUI_AUTH_TRUSTED_*_HEADER` de sa version
épinglée ; le port natif n’est plus publié. La dictée et la configuration des
modèles obtiennent une session native en interne par ce même mécanisme, sans
mot de passe demandé à l’utilisateur. L’API locale continue de fonctionner sans
Open WebUI ; l’accès avancé dépend du proxy, du pilote et du service natif.

Un en-tête de profil attendu permet de refuser une action d’un onglet devenu
périmé ; les onglets partagent aussi une notification de changement, complétée par un
contrôle du profil toutes les dix secondes sur les pages visibles, avec délai
de réponse borné à quatre secondes. Il s’agit
de cohérence d’identité, pas d’une authentification. Les contrôles d’origine des
mutations sont conservés. Voir le [guide des profils](../utilisation/profils-locaux.md).


Le démarrage Windows 0.1.30 persiste les chemins d’outils via
`scripts/windows_autostart.py` et installe un lanceur dans le dossier stable
`maintenance/`. Deux tâches interactives limitées surveillent indépendamment le
site et le transfert : le premier a une durée bornée, le second n’a aucune limite
de durée. Les verrous du superviseur et du transfert empêchent les écrivains
concurrents. La reprise web réutilise l’identifiant et le gestionnaire de tâche
existant ; le dernier plan autorisé est figé par son empreinte. Ce mécanisme ne
remplace ni une ouverture de session Windows ni la récupération d’une mise à jour
interrompue. Voir le [guide Windows](../installation/deux-etapes-windows.md#démarrage-automatique-windows-depuis-0130).

## Plan de refonte du portail — 13 novembre 2026

Le [plan UX](../decisions/plan-refonte-ux.md) propose une nouvelle répartition des
écrans, un suivi commun des opérations et une navigation mémorisée, avec une
interface classique conservée et utilisable. Il définit aussi les différences
ordinateur/téléphone et les critères de non-régression. Ce plan ne décrit pas
une refonte déjà livrée ; les composants et procédures actuels restent inchangés.

Depuis 0.1.31, une [maquette navigable](../utilisation/maquette-ux.md) isolée
dans `portal/maquette/` permet d’essayer cette organisation sans appels API.
Le portail actuel reste à la racine ; le suivi commun réel n’est pas encore raccordé.

## Interface fonctionnelle — 0.1.32

L’entrée principale et `/nouveau/` servent la nouvelle organisation, avec les
API existantes. `/classique/` conserve ses propres scripts/styles et les mêmes
données ; `/maquette/` reste fictif. `scripts/build_next_portal.py` génère les
entrées modernes à partir du balisage classique. `layout.js` déplace les contrôles
existants avant leur liaison ; `navigation.js` adapte historique et contexte.
Depuis 0.12.0, `settings-layout.js` s’exécute après la création des panneaux
fonctionnels et avant la navigation : il déplace une seule fois les nœuds existants,
sans les cloner, en conservant IDs, événements, ancêtres `article`/`details` et
`view-settings` attendus par les contrôleurs. `settings.css` complète la charte.
Les nouvelles sous-rubriques restent des présentations de `view-settings`, sans
nouvelle API. La route demandée est conservée pendant la lecture du profil ; un
rechargement retire le marqueur d’un dialogue qui n’est plus ouvert. Le contrôleur
commun ne réécrit pas les adresses historiques dans cette interface ; les
écritures de position identiques sont évitées et celles du défilement espacées
de 250 ms pour préserver la navigation WebKit.
Voir la [correspondance des commandes](../utilisation/parametres-et-appareil.md).

`GET /api/activity` passe par la route interne authentifiée `/activity` du
contrôleur. `scripts/library_monitor.py` associe identité, plan, reçus et progrès
sans ouvrir de base ni prendre de verrou. Un cache hôte de cinq secondes borne
les lectures concurrentes ; aucune erreur brute, chemin ou PID n’est publié.
Le téléchargeur enregistre aussi un petit plan courant pour les transferts directs
Windows/Linux. Aucune commande indépendante n’est ajoutée par cet endpoint.
Voir le [guide](../utilisation/nouvelle-interface.md) et le
[bilan](../essais/2026-11-13-interface-fonctionnelle.md).

Depuis 0.1.34, `portal/nouveau/collections.js` filtre uniquement les cartes de
l’inventaire déjà affichées ; leurs actions restent attachées aux mêmes éléments.
Le routeur mémorise le filtre et ouvre directement la page native Cartes.
Le relief repose sur les tuiles locales existantes, sans nouvelle source réseau.

## Socle de recherche Kiwix

Depuis 0.1.35, `pilot/library.py` sélectionne explicitement les archives par
identifiant Kiwix ou par nom en repli. Les lots sont homogènes par langue et les
archives multilingues ou sans langue connue restent isolées. Un lot refusé est
retenté archive par archive, sans masquer les succès reçus. Cela n’implique pas
que chaque archive multilingue soit prise en charge en plein texte par Kiwix.

`/api/search` et l’outil `search_library` transmettent `coverage`, avec les archives
interrogées, en échec ou non interrogées. Le compteur historique `without_fulltext`
désigne les tags d’index négatifs, pas une preuve physique d’absence d’index.
Depuis 0.1.36, ces tags servent à prioriser les sondages ; titres et reformulations
ont aussi leurs compteurs. Les recherches limitées aux favoris ou traductions
gardent leur périmètre. Le classement commun remplace l’alternance guide/article
utilisée en 0.1.35. Les états décrivent une recherche, pas une validation ou une lecture.

## Consolidation documentaire 0.1.36

`pilot/retrieval.py` prépare la requête, le périmètre et le classement lexical
commun. `library.search` rassemble des candidats FTS et Kiwix avant classement,
regroupe les pages et transmet `coverage`. `collection` filtre séparément les
archives. Les titres sont interrogés dans quatre collections prioritaires ;
32 appels plein texte au plus sont autorisés, avec trois requêtes simultanées
et dix secondes pour l’ensemble après le catalogue (trois secondes au plus).
Les reformulations Kiwix utilisent des recherches littérales distinctes, après
la première passe, et non une syntaxe OR supposée. Les métadonnées d’index
ordonnent les sondages sans exclure les archives.

`engine.document_request` prépare certaines demandes documentaires avant le
premier appel au modèle, puis conserve les outils pour affiner. Les caches sont
propres à une réponse et au périmètre, pas un index sémantique global. Le contexte
est compacté sans modifier l’historique stocké. `engine.PROGRESS` expose un suivi
éphémère par demande, renvoyé seulement après contrôle du propriétaire dans
`/api/jobs/{id}` ; aucun schéma de base n’est changé.

La vérification depuis le site utilise uniquement santé et recherche en GET,
et produit un rapport côté navigateur. Elle ne proclame pas le fonds validé.
Le [bilan](../essais/2026-11-14-moteur-recherche-utile.md) détaille le vrai Kiwix
sur archives générées et les limites de transfert au fonds de Marc.

## Index complémentaires — 0.3.0

Les ZIM restent en lecture seule. `scripts/index_archives.py` extrait leur texte avec libzim 3.13.1 dans un environnement hôte optionnel, publie un SQLite FTS5 par archive sous `state/pilot/archive-index` et reprend les curseurs validés. Le pilote requête ces fichiers en lecture seule en parallèle de Kiwix ; les requêtes n’importent pas libzim. Les opérations passent par les mêmes droits Famille, service de contrôle, verrous et suivi que les préparations documentaires. Voir le [guide](../utilisation/indexation-archives.md).

## Préparation automatique et catalogue — 0.4.0

Les producteurs de fichiers vérifiés écrivent la file `catalog/search-index-queue.json` sous verrou. Le contrôleur lance un seul travail documentaire lorsque publication et téléchargement sont libres. Les pauses volontaires et interruptions restent explicites ; les reports horaires et le mode jeu gardent leur logique propre. Le manifeste cumulatif des index conserve les résultats des lots précédents. Le catalogue Kiwix utilise un cache court partagé entre appels et un instantané daté, sans masquer les erreurs derrière une liste vide valide. Les diagnostics exposent des codes sûrs, pas les corps HTTP ni les secrets.

## Référence de recherche et lecture — 0.5.0

Le contrôle complet lit une référence JSON statique versionnée ; ses sources
attendues fictives restent dans les tests, sans être imposées à la bibliothèque
réelle. Les avis de pertinence sont conservés dans le rapport côté navigateur,
sans écriture dans les comptes ni les documents. Le contrôle court reste distinct.
Le lecteur HTTP suit les redirections de contenu à origine et archive identiques,
au plus cinq, sans suivre les catalogues ni les liens externes. Sa réponse conserve
le chemin final pour résoudre les images, tout en préservant l’identifiant demandé.

## Métadonnées corrigibles — 0.6.0

`pilot/catalogue.py` conserve une surcouche JSON versionnée dans `settings`, sous
les clés `catalogue:v1:`. Identité canonique par article ZIM ou document guide,
sans suffixe de page PDF ; révision locale par référence, taille et date de
modification. Une nouvelle révision invalide l’ancien classement humain et les
noms corrigés, sans effacer leur enregistrement avant retour explicite.

Le moteur commun applique les espaces corrigés avant filtrage et transmet le
type/état à l’assistant. Les groupes corrigés filtrent Kiwix et les index SQLite.
Les libellés originaux et identifiants restent inchangés ; l’export ne lit que
les clés de la surcouche et une liste autorisée de champs. Les erreurs de lecture
de métadonnées sont signalées sans supprimer les candidats de recherche globale.

## Mesures et calibration — 0.7.0

`assistant_metrics.py` conserve des mesures numériques par travail sous
`assistant-metrics/`, sans contenu documentaire ou conversationnel. La requête
transmet son instantané de source et ses durées préparatoires par une mémoire
éphémère indexée par l’identifiant accepté ; le travail n’effectue pas une seconde
lecture identique. Les mesures finales sont écrites même après erreur/annulation
commencée. L’accès et l’export vérifient le propriétaire du travail ; la suppression
d’une conversation enlève ses mesures. Les traces d’outils existantes restent séparées.

`model_runtime.py` lit les métadonnées locales, jamais `/api/pull`. Le budget réserve
sortie, schéma des outils et marge de format avant de compacter les messages. La
limite native de l’architecture principale est distinguée des limites d’un éventuel
encodeur d’image. Le contexte et placement effectivement chargés restent observés
séparément du réglage demandé.

`calibration.py` partage le verrou d’inférence avec réponses et traductions. Après
action Famille, il calibre la taille du texte synthétique puis vérifie froid/chaud,
volume réellement traité, mémoire et contexte alloué. Une demande normale est
prioritaire ; pause/pression/annulation interrompent le test sans reprise forcée.
L’application du résultat est explicite et liée au digest, à la limite native et
au matériel observé. Les rapports privés restent sous `calibration/`, le réglage
précédent et le dernier contexte mesuré dans `settings`, sans migration destructive.

## Comparatif facultatif de recherche (0.8.0)

`pilot/search_experiment.py` utilise le moteur documentaire commun puis deux appels
structurés au modèle local présent. Il est accessible uniquement par actions Famille
`/api/admin/search-experiment`, `/start`, `/stop` et `/review`. Le verrou moteur,
les réserves et la priorité des conversations sont partagés avec la calibration ;
la recherche normale ne dépend pas de ce module optionnel. Rapports durables privés
dans `search-experiments/`, pas de reprise automatique ni de réglage modifié.
`pilot/search-reference.json` est la référence embarquée ; le générateur de portail
produit sa copie statique. Voir le [guide](../utilisation/comparer-recherche-ia.md).

## Dossiers de lecture pratique (0.9.0)

`pilot/practical.py` lit les six objectifs et points dans `deploy/kiwix-themes.json`.
Les API publiques `/api/library/dossiers` et `/{id}` sont indépendantes de l’IA ;
`/{id}/search` déclenche seulement les recherches documentaires explicites.
Famille modifie les références via `/api/admin/library/dossiers/{id}/references`,
avec révision du dossier et du fichier source. `settings`, préfixe `dossier:v1:`,
conserve les notes communes sans migration. Export via `/api/admin/library/dossiers-export`.
Une erreur du module optionnel laisse les autres chemins accessibles. Le
[guide](../utilisation/dossiers-pratiques.md) décrit la reprise et les limites.

## Corrections de recherche 0.9.1

`pilot/kiwix_queries.py` partage deux sémaphores texte/titres de capacité deux,
regroupe les appels identiques et garde uniquement les réponses valides réussies
pendant quinze secondes (64 réponses, huit millions d’octets au maximum). Le
service annule les appels restants à son arrêt. `library.search_archives` conserve
les causes bornées et ne redécoupe un lot qu’après rejet de sélection 400/404/413.
Le budget du comparatif IA porte sur toute la demande, puis une série de deux
échecs est interrompue. Les nouvelles observations sont numériques ou catégorielles,
sans réponse brute, jeton ni raisonnement privé. Voir le
[bilan](../essais/2026-11-14-corrections-rapports-recherche.md).

## Vérification du lecteur isolé (0.9.2)

`scripts/index_reader_probe.py` reste indépendant de la passerelle Web. Il vérifie
libzim et SQLite FTS5 sans archive ni réseau. `search_index_tools.py` l’appelle
dans le Python dédié avant de publier le marqueur prêt ; `index_archives.py` le
répète avant son pool et enregistre `reader_probe` dans la progression.
Le superviseur retire le marqueur en cas d’échec, y compris pendant sa récupération.
Les erreurs d’archives ont un motif borné sans message natif privé. Voir le
[guide actuel](../utilisation/indexation-archives.md).
Le pool conserve la sélection d’exécutable de CPython : substituer le `pythonw.exe`
du venv Windows empêche son démarrage adapté aux environnements isolés. La recette
exécute le vrai CLI à deux processus dans un venv sans dépendances Web.
La restauration automatique d’une recherche par `navigation.js` attend le résultat
du profil, y compris son repli anonyme, pour éviter les trois requêtes au démarrage.

## Maintenance et écrivains d’index (0.9.3)

`pilot_backup.maintenance` exclut les tâches Web, publications, transferts et
écrivains d’index avant l’arrêt des services. `pilot_update` garde ce contexte
pendant le remplacement et le retour arrière ; sa récupération explicite le reprend.
`index_locks.py` enregistre les verrous par archive avant toute soumission au pool,
et `index_archives.build_one` les détient pendant chaque extraction. La maintenance
acquiert aussi ces verrous pour exclure les processus restants et les départs tardifs.
Les instantanés excluent les `.lease` des états ; le retour arrière conserve les
inodes existants, y compris ceux détenus par son propre contexte de maintenance.

## Ordonnancement et volume des recherches (0.9.4)

`library.search_archives` ordonne les lots entre langues après correction des tags
par les index réels, isole les grosses archives et limite les lots compatibles à
douze. Deux consommateurs prennent les reformulations des collections pratiques
avant les lots généraux restants ; l’échéance est de douze secondes, 32 appels au
maximum. Les titres privilégient la diversité des familles. `kiwix_queries`
annule un appel partagé seulement au départ de son dernier lecteur.
`coverage.local_index` résume les compteurs et diagnostics sans répéter le manifeste
par archive ; l’API d’administration et le rapport d’indexation gardent le détail.
Le cache d’une question de l’assistant réutilise son intention préparée si le modèle
la raccourcit au seul sujet, sans confondre deux actions explicites.

## Recette d’usage depuis le navigateur (0.10.0)

`portal/nouveau/usage-recipe.js` utilise uniquement les API de lecture existantes,
sans commande d’inférence/préparation. Le contrôle comprend au maximum deux
recherches et deux aperçus, quinze secondes par lecture et 90 secondes au total.
Le profil, la génération et le contrôleur d’exécution isolent les réponses tardives.
La version est contrôlée avant/après. Le brouillon local ne persiste pas les
mesures, qui restent à relancer après rechargement. Le JSON R7 sépare observations
humaines et mesures, sans texte de source ni manifeste complet. La coupure réseau
est une déclaration de l’opérateur ; voir le [guide](../utilisation/verifier-usage-hors-ligne.md).


## Cartes et accès aux itinéraires — 0.11.0

La route protégée `/api/geography/shade/{z}/{x}/{y}.png` sert un
ombrage RGBA prêt à superposer (et non des hauteurs Terrarium). L’ancien endpoint
`/api/geography/terrain/` conserve son format DEM pour les lecteurs déjà ouverts.
Les mesures et profils d’altitude gardent les HGT originaux. Le cache mémoire est limité à 128
tuiles compressées, avec déduplication des générations identiques, concurrence
limitée à deux et invalidation par manifestes/fichiers. Le cache HTTP reste privé,
revalidé par ETag, après vérification du profil ; les autres API restent no-store.

`POST /api/admin/map-notebook/accesses` propose jusqu’à trois accès OSRM du profil
choisi dans les 1 000 m ; `near: [latitude, longitude]` restreint la recherche aux
100 m autour d’un clic manuel. Le calcul accepte un `access_token` facultatif par
étape. Les jetons signés sont liés au point, mode, évitements, graphe et délai de
quinze minutes ; ils deviennent invalides après redémarrage. Les erreurs de routage
conservent `detail` textuel et ajoutent un champ `code` stable ; le portail lit
aussi les réponses structurées `detail.code` / `detail.message` des essais. Les limites restent 12 calculs et 30 recherches d’accès par
minute et par profil.

Les instantanés JSON des nouveaux trajets ajoutent `connectors` et
`access_selected` ; aucune table n’est migrée. Les jetons et hints OSRM ne sont pas
conservés dans les trajets. Les versions anciennes restent lisibles. L’export GPX
n’ajoute pas les raccordements non vérifiés dans la trace routée.


## Index multilingues et traces explicites (0.11.1)

L’extraction distingue `has_fulltext_index` et `kiwix_language_compatible` dans le
manifeste existant. Plusieurs langues ou leur absence nécessitent un complément
SQLite, sans changer son format. Toute archive `ready` est interrogée localement ;
une archive incompatible non préparée reste signalée et ne consomme pas d’appel
natif voué au refus. Une métadonnée `mul` unique n’est pas exclue par son nom.
`/api/search?diagnostic=true` ajoute au maximum quarante événements et les
compléments nécessaires. Seul le contrôle explicite de recherche le demande ;
les réponses normales aux outils IA n’embarquent pas ces journaux. Les délais
rapportés incluent l’attente client et ne sont pas une mesure CPU du serveur.

## Recherche progressive et cache — 0.13.0

`pilot/search_stream.py` diffuse des instantanés SSE sur `/api/search?stream=true`,
à partir du même moteur et des mêmes filtres que le JSON existant. La file garde
uniquement le dernier instantané en attente. La fermeture du flux annule le travail
client. Le budget natif est de 60 secondes sur ce parcours, de 12 sur l’ancien JSON.
`diagnostic=true` utilise également 60 secondes ; le journal reste borné à 40 appels.
Le portail conserve la lecture ouverte et les résultats lors d’un arrêt.

`pilot/search_cache.py` complète les requêtes mutualisées de `kiwix_queries.py` :
SQLite reconstructible sous `state/pilot/cache/search`, réponses valides seulement,
invalidation par état des ZIM/catalogue/manifeste, quotas et réserve disque.
Aucune migration des données privées ni changement d’image tiers. Voir le
[guide d’exploitation](../exploitation/cache-et-recherche-progressive.md).
La traduction et l’indexation des [vidéos locales](../decisions/videos-locales-et-recherche.md)
restent un chantier distinct ; le flux actuel ne cherche pas dans leurs paroles.

Depuis 0.14.1, `catalogue.SearchAnnotations` conserve les annotations des candidats
inchangés pendant une demande et mutualise les révisions par fichier physique,
avec nouvelle vérification à la sélection finale. `retrieval.NormalCache` borne
le réemploi du texte normalisé à 4 096 entrées et 32 Mo de charge textuelle.
Ces caches sont locaux à la demande et ne modifient ni le cache de réponses
Kiwix ni les scores. La sélection utilise le thread attendu par `disk_io`, y
compris lors d’une annulation. `coverage.processing` mesure cette phase seulement ;
le [guide](../exploitation/cache-et-recherche-progressive.md) précise les limites
des durées réelles, du CPU du thread et des compteurs. Les deux voies plein texte,
deux voies titres et jusqu’à huit threads SQLite ne sont pas un parallélisme CPU
illimité ; les contraintes de Kiwix et du stockage restent à mesurer sur la cible.

Depuis 0.14.2, le plafond d’appels plein texte du parcours long s’adapte aux lots
natifs et à leurs deux termes de reformulation au plus, avec plancher 32. Le
parcours court conserve 32 appels. Le budget temporel, les sémaphores et les
conditions de reformulation restent inchangés. `coverage.request_limit` contient
la valeur effective ; les 40 traces bornées ne comptent pas tous les appels lorsque
le plafond dépasse 40. Voir la [reproduction](../essais/2026-11-15-budget-reformulations.md).

Depuis 0.14.3, le bonus d’action distingue aussi quantité, question périphérique
et risques, avec marqueurs de guide, manuel et « how to » au lieu du seul « how ».
Les demandes contextuelles restent cherchables. La comparaison de titre exact
accepte la requête originale normalisée et ses mots de liaison ; ces règles ne
modifient aucune classification humaine. Le [bilan](../essais/2026-11-15-questions-peripheriques-et-titres-exacts.md)
conserve les cas observés et les limites du classement sans lecture du contenu.

## Suivi documentaire de l’assistant — 0.15.0

`pilot/documentary.py` observe les sorties de recherche et de lecture, sans analyser
la prose du modèle. Les appels réutilisés partagent leur clé, les résultats et
sources sont comptés par identifiant. Le résumé versionné borne états et compteurs ;
les liens consultés sont filtrés séparément et restent privés à la conversation.
`engine.DOCUMENTARY` sert les observations vivantes sur l’API de demande.

La table optionnelle `documentary_evidence` conserve résumé et liens avec index de
conversation, référence de message et suppression en cascade. Le message et son
suivi final partagent la transaction ; la table ne dépend pas d’une clé étrangère
vers les demandes nettoyables. Les colonnes existantes et le schéma global 1 sont
conservés. Une table absente n’empêche ni réponse ni lecture d’ancien historique.
`assistant_metrics` garde seulement les nombres filtrés, utilisables en repli sur
la demande. L’annulation persiste les observations sans créer de faux message.

Le portail rend un élément `details` replié, mis à jour sans détruire son ouverture
ou le bouton focalisé. Les sources lues mais non citées restent ouvrables sans
être ajoutées aux références numérotées. Le [guide](../utilisation/sources-et-fiabilite.md#suivi-des-recherches-et-lectures-dans-lassistant)
et le [bilan](../essais/2026-11-15-suivi-documentaire-assistant.md) précisent les
limites : des opérations terminées ne prouvent ni exhaustivité ni bonne réponse.

## Préparation des demandes de synthèse — 0.15.1

`retrieval.search_subject` distingue une commande explicite de résumé de son sujet,
sans bannir « synthèse » des recherches techniques. `library.search_terms` l’utilise
sur le chemin commun ; la demande originale reste dans `Plan.original` et dans
la conversation. Les prépositions internes du sujet et les périmètres sont gardés.
Le concept frottement/friction est bilingue ; le mot de liaison « comme » n’est
plus un groupe obligatoire. `engine.document_request` prépare aussi les demandes
pratiques avec action reconnue, après ses exclusions géographiques/calculatoires.

Budget court de l’assistant, lecture de deux premiers documents et association
unique restent inchangés. Le [programme retenu](../decisions/assistant-recherche-et-synthese.md)
sépare ce correctif du travail multi-source, de la sélection de passages et de
la boucle d’outils contrôlée. Aucun modèle ni schéma de données ne change ici.

La session de modèle (`pilot/model_session.py`) prépare le modèle cible par un
appel local sans messages lorsqu’un autre est chargé ou qu’un contexte connu
change. Le planificateur Ollama garde la responsabilité du déchargement. La
session dispose d’une seule reprise pour préparation/flux vide/erreur transitoire
avant toute sortie, partagée entre tours d’outils ; elle ne rejoue jamais un outil
et vérifie l’état volontaire du moteur avant préparation/reprise. Les sorties
partielles et erreurs restent distinctes d’une absence documentaire. Voir le
[guide des mesures](../utilisation/mesurer-assistant-et-memoire.md).
