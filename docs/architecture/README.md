# Architecture du pilote

Vue de référence documentaire au 11 novembre 2026. Elle décrit les rôles des
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

Le contrat de livraison est dans [release.json](../../deploy/release.json).
Les références des composants tiers sont dans [versions.json](../../deploy/versions.json).
Les catalogues [documentaires](../../deploy/content-catalog.json) et
[cartographiques](../../deploy/map-catalog.json) décrivent les ressources prévues ;
leur présence dans un catalogue ne prouve pas leur téléchargement.

L’installation portable repose sur [setup.py](../../scripts/setup.py), les
lanceurs Windows/Linux et Compose. L’export du kit, les sauvegardes et les mises
à jour ont des outils dédiés, présentés dans les [procédures d’exploitation](../exploitation/README.md).
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
