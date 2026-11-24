# Architecture du pilote

**Vue d’ensemble — revue le 20 novembre 2026 (0.67.0).** Ce fichier présente les
composants et renvoie aux documents par domaine. Chaque document de domaine décrit
un mécanisme au moment de sa livraison ; il reste valable sauf note de remplacement.

| Pour… | Lire |
| --- | --- |
| Savoir où se trouve un fichier, une route, un script | [Carte du code](carte-du-code.md) |
| Règles visuelles et composants de l’interface | [Guide de design](guide-design.md), [composants](composants-interface.md) |
| Tests reproductibles et artefacts GitHub Actions | [Tests automatisés et CI](tests-et-ci.md) |
| Organisation du portail, génération de la page unique | [Interface](interface.md) |
| Index, Kiwix, recherche progressive, cache | [Recherche et index](recherche.md) |
| Outils de l’assistant, sélection, lecture longue, illustrations | [Assistant, lecture et synthèse](assistant.md) |
| Traductions, contrôles, lecture française | [Traduction](traduction.md) |
| Vidéos, sous-titres, transcription | [Vidéos et sous-titres](videos.md) |
| Calibration, diagnostics, recette d’usage | [Mesures et diagnostics](mesures.md) |
| Cartes hors ligne et itinéraires | [Cartes et itinéraires](cartes.md) |

Non couverts ici (voir les guides) : file d’attente des travaux
([décision](../decisions/file-attente-travaux.md)), organisation des collections et
classement du fonds principal ([guide](../utilisation/classement-et-collections.md),
[préparations](../utilisation/preparations-bibliotheque.md)), téléchargement YouTube
([guide](../utilisation/telecharger-videos-youtube.md)), transfert vers un SSD
([guide](../exploitation/transfert-installation.md)), téléchargement des modèles
([portail](../utilisation/portail.md#télécharger-un-modèle-pour-lassistant)).

Toutes les routes HTTP sont déclarées dans `pilot/app.py` sous le préfixe `/api/`.

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

## Compression, cache du portail et catalogue Kiwix — 0.115.0

Caddy compresse en gzip (préféré, plus compact ici) ou zstd les réponses textuelles du portail et de l’API
(HTML, CSS, JavaScript, JSON, SVG, Markdown, texte) à partir de 1 Ko. Les flux
`text/event-stream`, les PDF, les tuiles, les médias et les plages d’octets sont
exclus. Les fichiers appelés avec `?v=` reçoivent `Cache-Control: public,
max-age=31536000, immutable` : `scripts/build_portal.py` y écrit l’empreinte du
contenu, l’adresse change donc avec le fichier. Les pages et les fichiers sans
`?v=` restent en `no-cache`. Mesure au laboratoire Bazzite du 24 novembre 2026 :
premier chargement du portail (69 fichiers) de 983 Ko à 304 Ko transférés en gzip, 318 Ko en zstd, puis
plus aucune revalidation des fichiers versionnés. Open WebUI et Kiwix compressent
déjà leurs propres réponses ; leurs routes ne changent pas.

`deploy/kiwix-entrypoint.sh` ajoute toutes les archives au catalogue en un seul
appel `kiwix-manage` : 3 s pour 205 archives au lieu de 42 à 59 s quand chaque
ajout réécrivait le catalogue. Si une archive est illisible, l’appel groupé
n’enregistre rien ; le script reprend alors archive par archive et ignore la
seule archive illisible, signalée dans le journal du conteneur. Auparavant,
`set -e` empêchait Kiwix de démarrer dans ce cas. Les délais de santé Compose
gardent leur marge pour les disques lents.
