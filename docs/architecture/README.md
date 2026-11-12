# Architecture du pilote

Vue de référence documentaire au 12 novembre 2026. Elle décrit les rôles des
composants ; les [bilans](../essais/README.md) indiquent les validations réalisées.

| Composant | Responsabilité | Entrées du dépôt |
| --- | --- | --- |
| Portail servi par Caddy | Navigation, assistant, bibliothèque, cartes et accès aux autres interfaces | [portal](../../portal/), [Caddyfile](../../deploy/Caddyfile) |
| Passerelle FastAPI | Comptes via Open WebUI, conversations du portail, recherche, lecture, calcul et suivi | [pilot](../../pilot/) |
| Open WebUI | Comptes natifs, dossiers, conversations avancées et collections propres | [compose.yaml](../../compose.yaml) |
| Kiwix | Consultation illustrée et recherche native des archives ZIM | [Point d’entrée Kiwix](../../deploy/kiwix-entrypoint.sh) |
| Ollama et contrôleur hôte | Inférence locale, état et commandes d’administration du moteur | [Profils](../../deploy/model-profiles.json), [contrôleur](../../scripts/control.py) |

Le portail et Open WebUI partagent les comptes, mais ont des historiques distincts.
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

Le contrat de livraison est dans [release.json](../../deploy/release.json).
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

`pilot/translations.py` extrait l’original PDF dans un thread, borne la préparation puis traite les passages avec un schéma de réponse Ollama. Le contenu à traduire est fourni comme message utilisateur ; l’historique d’un refus précédent n’est pas réinjecté. Le worker partage `engine.LOCK` avec le chat et vérifie le contrôleur avant chaque passage. Il enregistre le résultat seulement si la traduction est toujours active. Le redémarrage du pilote met les travaux actifs en pause ; aucune inférence ne reprend au démarrage. Les exports sont authentifiés et les traductions ne rejoignent pas le fonds public.

Le [guide d’utilisation](../utilisation/documents-et-traduction.md) précise les limites de texte, la pagination, les images et les validations restantes.
