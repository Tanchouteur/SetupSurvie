# Architecture du pilote

Vue de référence documentaire au 13 novembre 2026. Elle décrit les rôles des
composants ; les [bilans](../essais/README.md) indiquent les validations réalisées.

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
