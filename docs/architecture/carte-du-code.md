# Carte du code

**Guide de référence — 0.66.0, 20 novembre 2026.** Établi à partir des en-têtes
des modules et des fichiers réellement présents dans le dépôt. Il dit **où se
trouve quoi** ; le comportement détaillé est dans les guides cités et dans
l’[architecture](README.md). Mettre cette carte à jour quand un module est
ajouté, renommé ou supprimé.

## Repères rapides

| Je cherche… | Aller voir |
| --- | --- |
| La version du logiciel | `pilot/app.py` (`VERSION=`) et `deploy/release.json` — les garder identiques |
| Toutes les routes HTTP du portail | `pilot/routes/` : un `APIRouter` par domaine, assemblés dans `pilot/app.py` |
| La page du portail | `portal/interface/modele.html` → `scripts/build_portal.py` → `portal/index.html` (généré, ne pas éditer) |
| Le contexte donné à l’assistant | `deploy/assistant-system.fr.txt` + consignes d’outils dans `pilot/engine.py` |
| Les modèles et modes de réponse | `deploy/model-profiles.json` |
| Les versions figées des composants tiers | `deploy/versions.json` (ne pas modifier sans vérification réelle) |
| Les services et ports | `compose.yaml`, `compose.gpu.yaml`, `compose.linux.yaml`, `deploy/Caddyfile` |
| Ce qui tourne sur l’hôte (hors conteneurs) | `scripts/control.py`, `scripts/library_tasks.py`, `scripts/library_monitor.py` |
| Les tests | `tests/` (≈ 240 fichiers) ; CI : `.github/workflows/tests.yml` (Linux + Windows) |

Commande de test : `python3 -m unittest discover -s tests -v` après installation de
`tests/requirements-kiwix.txt`. Les points d’entrée des recettes navigateur et des
autres jobs figurent dans le [guide des tests et de la CI](tests-et-ci.md).

## Vue d’ensemble des processus

```text
Navigateur ──► Caddy (deploy/Caddyfile) ──► portal/ (fichiers statiques)
                    │                    └► pilot (FastAPI, pilot/app.py) ──► Ollama (11435, interne)
                    │                                   │                 └► Kiwix (8081)
                    │                                   └► scripts/control.py sur l’hôte (11436, interne)
                    └► Open WebUI (3000/8444, profil transmis par en-tête)
```

Le pilote ne lance jamais de commande système : il demande des actions fixes au
contrôleur hôte (`pilot/operations.py` → `scripts/control.py`). Les ports 11435
et 11436 ne sont pas exposés aux lecteurs.

## `pilot/` — passerelle FastAPI

### Socle, profils et stockage

| Module | Rôle |
| --- | --- |
| `app.py` | Application FastAPI : version, cycle de vie, contrôle d’origine, assemblage des routeurs de `routes/` |
| `routes/deps.py` | Dépendances communes (profil courant, droits d’administration, fonctions optionnelles) et modèles partagés ; ré-exportés par `app.py` |
| `routes/status.py` | Routes de statut, santé, réseau et moteur d’inférence |
| `routes/profiles.py` | Routes des profils, favoris, utilisateurs et retours |
| `routes/library.py` | Routes de la bibliothèque, recherche, sources, dossiers pratiques et lecture de documents |
| `routes/maps.py` | Routes de géographie, carnet de cartes et itinéraires |
| `routes/conversations.py` | Routes des conversations, dossiers et questions à l’assistant |
| `routes/videos.py` | Routes des vidéos, sous-titres, transcriptions, acquisitions et téléchargements YouTube |
| `routes/work.py` | Routes de la file de travail et du suivi des tâches |
| `routes/documents.py` | Routes des résumés, traductions et mesures de tâches |
| `routes/admin.py` | Routes d’administration : réglages, mise à jour, performance, calibrage, contexte et modèles |
| `profiles.py` | Profils locaux sans mot de passe ([guide](../utilisation/profils-locaux.md)) |
| `accounts.py` | Opérations sur les comptes natifs Open WebUI (internes) ; `POST /api/auth/{action}` répond 410 |
| `configure.py` | Profils Open WebUI partagés, versionnés, sans copier les poids |
| `store.py` | Petit stockage persistant de l’application (SQLite) |
| `durable.py` | Publication durable des petits fichiers d’état ([coupures](../exploitation/coupures-et-redemarrage.md)) |
| `operations.py` | Pont authentifié vers le contrôleur hôte |
| `console.py` | Accès de secours physique au serveur, jamais exposé publiquement |
| `network.py` | Carte de connexion publique (IP, nom, QR code) |
| `work_queue.py` | File d’attente des travaux du portail ([guide](../utilisation/file-attente.md)) |

### Assistant et conversations

| Module | Rôle |
| --- | --- |
| `engine.py` | Conversations bornées et harnais d’outils en lecture seule |
| `tool_protocol.py` | Reconnaissance des propositions d’outils dans le texte du modèle |
| `model_session.py`, `model_runtime.py` | Modèle choisi, reprise bornée ; métadonnées en lecture seule |
| `model_downloads.py` | Téléchargement des modèles depuis le portail via Ollama |
| `conversation_context.py`, `conversation_organization.py` | Dernier échange ; dossiers des conversations |
| `documentary.py` | Suivi des recherches et lectures réellement effectuées |
| `citation_links.py`, `procedure_review.py` | Liens vers les sources ; conditions de départ citées mot pour mot |
| `associations.py`, `document_workspace.py` | Sélection de documents ; travaux personnels par original |
| `summaries.py` | Lecture longue et synthèse hiérarchique ([guide](../utilisation/synthese-documentaire.md)) |
| `illustrations.py` | Illustrations d’origine choisies par légende ([guide](../utilisation/illustrations-et-references.md)) |
| `video_requests.py` | Demandes de vidéos faites à l’assistant |
| `calibration.py`, `performance.py`, `assistant_metrics.py`, `startup_diagnostic.py` | Essais de contexte, mesures, délais, diagnostic après refus de démarrage |
| `acceptance*.py` | Contrôles réels avec comptes jetables (recettes) |

### Bibliothèque et recherche

| Module | Rôle |
| --- | --- |
| `library.py` | Outils documentaires en lecture seule et index des guides |
| `retrieval.py`, `research.py` | Planification et classement déterministes ; passages ciblés |
| `search_stream.py`, `search_cache.py` | Résultats progressifs ; cache reconstructible ([guide](../exploitation/cache-et-recherche-progressive.md)) |
| `search_experiment.py` | Comparatif facultatif d’aide IA ([guide](../utilisation/comparer-recherche-ia.md)) |
| `kiwix_catalog.py`, `kiwix_queries.py` | Catalogue Kiwix et requêtes bornées |
| `archive_index.py`, `category_index.py` | Index SQLite des archives ; index du fonds principal par espace ([guide](../utilisation/indexation-archives.md)) |
| `archive_media.py`, `html_text.py`, `math_text.py`, `wiki_structure.py` | Lecture HTTP des archives, texte, formules, structure Wikipédia |
| `catalogue.py`, `collection_sort.py` | Noms et types corrigibles ; sélection des collections ([guide](../utilisation/classement-et-collections.md)) |
| `source_metadata.py` | Dates et éditions issues des métadonnées ([guide](../utilisation/sources-et-fiabilite.md)) |
| `practical.py`, `learning.py` | Dossiers pratiques ; parcours d’apprentissage |
| `document_text.py`, `favorites.py`, `publications.py` | Texte complet, favoris, publication des traductions |
| `inventory.py` | Inventaire des fichiers sur disque |

### Traduction

`translations.py` (travaux privés et reprise), `translation_quality.py` (contrôles,
seuils : lire le [guide](../utilisation/documents-et-traduction.md) avant de les
changer), `translation_terms.py` (terminologie personnelle), `translation_reader.py`
(lecture des versions publiées), `translation_benchmark.py` (essai 40 pages).

### Vidéos et sous-titres

| Module | Rôle |
| --- | --- |
| `videos.py`, `video_inventory.py` | Index local des médias et sous-titres ; inventaire en lecture seule |
| `archive_videos.py`, `zim_video_inventory.py` | Vidéos contenues dans les archives ZIM |
| `captions.py`, `caption_acquisition.py`, `caption_fetch_worker.py`, `provider_subtitles.py` | Préparation et acquisition des sous-titres |
| `transcriptions.py`, `speech_worker.py` | Reconnaissance vocale locale (CPU par défaut) |
| `youtube_downloads.py`, `youtube_list.py`, `youtube_pipeline.py` | Listes YouTube : côté site, analyse, pont avec l’hôte |

### Cartes

`maps.py` (archives PMTiles vérifiées), `geography.py` (lieux, adresses, relief HGT),
`routing.py` (OSRM local, jamais de service Internet), `map_notebook.py` (carnets
de points partagés). Guides : [cartes](../utilisation/parametres-et-cartes.md),
[itinéraires](../utilisation/points-et-itineraires.md).

## `portal/` — interface

- `interface/modele.html` : gabarit de la page unique ; `scripts/build_portal.py`
  y injecte les feuilles et scripts dans l’ordre et produit `index.html`.
  Depuis 0.70.0, il remplace chaque `?v=` local de `index.html` et des pages
  autonomes (`cartes.html`, `pdf.html`, `secours.html`, `suivi-copie.html`,
  `maintenance.html`) par l’empreinte SHA-256 du fichier chargé ; aucun numéro
  n’est plus incrémenté à la main. La navigation principale et le pied de page
  (version, état de connexion) sont écrits dans le gabarit.
- `core/` (0.70.0) : `net.js` (enveloppe unique de `fetch` pour `/api/` :
  erreurs en français, détection de perte de connexion et nouvel essai),
  `feedback.js` (bandeau `#connection-banner`, état du pied de page, boutons
  occupés) et `core.css` (bandeau, messages, boutons occupés, silhouettes de
  chargement). `net.js` est le premier script chargé.
- `design/tokens.css` : seule source des couleurs, chargée en premier ;
  `tests/test_portal_design_budget.py` empêche l’ajout de couleurs ou de tailles
  de police brutes.
- Racine : `app.js` (application principale), `documents.js`, `settings.js`,
  lecteurs (`pdf.*`, `bilingual-reader.*`, `translation-text.*`), cartes
  (`cartes.html`, `cartes-*.js`), suivi de transfert (`suivi-copie.*`),
  page de secours statique (`secours.*`), suivi des mises à jour et copies
  (`maintenance-view.*`, partagé avec la page temporaire `maintenance.html`).
- `interface/` : un script par domaine (`videos.js`, `captions.js`,
  `work-queue.js`, `maintenance.js` (entrée Mises à jour, mode maintenance), `collection-sort.js`, `catalogue.js`, `search-*.js`,
  `assistant-workspace.*`, `reader-work.*`, `navigation.js`, `layout.js`…).
  Ajouts 0.70.0 : `assistant-status.js` (état de l’assistant près de la saisie,
  étapes d’une réponse), `device-summary.js` (« Tout fonctionne » ou points à
  regarder dans Mon appareil), `search-start.js` (écran de départ de Rechercher,
  dernières recherches, filtres repliés sur téléphone). Ajout 0.76.0 :
  `home.js` (ligne « Sur cet appareil » de l’accueil) ; `motion.js` porte les
  transitions directionnelles et l’apparition en cascade des cartes.
- `design/` : jetons et système visuel « Veillée » ; `vendor/` : bibliothèques
  locales (marked, DOMPurify, PDF.js…) ; `classique/` et `nouveau/` : simples
  redirections vers `/`.
- Règles : [guide de design](guide-design.md) et
  [composants de l’interface](composants-interface.md).

## `scripts/` — installation, hôte et outils

### Installation, démarrage et mise à jour

| Fichier | Rôle |
| --- | --- |
| `setup.py` | Lanceur principal (Python 3.11+, bibliothèque standard) : `up`, `down`, `doctor`, `prepare`, `prepare-maps`, `pull-model`, `configure`, `certificate`, `shortcuts`, `recover-account`… |
| `library_monitor.py`, `lab_activity.py` | Relevé des préparations du PC et publication en lecture seule pour le laboratoire isolé ([file d’attente](../utilisation/file-attente.md)) |
| `install_wizard.py`, `install*.ps1`, `prepare-windows.ps1`, `install.sh` | Première installation Windows/Linux ([Windows](../installation/deux-etapes-windows.md), [dépôt](../installation/README.md)) |
| `survie.ps1`, `survie.sh` | Points d’entrée en ligne de commande |
| `start-*.ps1`, `stop-*.ps1`, `startup-windows.ps1`, `windows_autostart.py`, `windows_background.py`, `register-startup-windows.ps1` | Démarrage et arrêt Windows |
| `linux_host.py`, `discovery.py`, `fix-linux-local-name.sh` | Docker rootless, démarrage Linux, nom `.local` |
| `linux_offline_tools.py`, `installer-outils-linux-hors-ligne.sh` | Collecte vérifiée et extraction des prérequis Linux pour le transfert hors ligne |
| `linux_offline_restore.py`, `restaurer-linux-hors-ligne.sh` | Activation et démarrage autonome sur Linux systemd depuis une copie hors ligne |
| `linux_recovery.py`, `linux_recovery_admin.sh`, `linux_recovery_gui.sh`, `installer-depuis-le-ssd.desktop` | Installation graphique depuis une copie Linux, duplication de SSD de secours, point immuable et préparation d’une nouvelle copie de travail ([guide](../exploitation/transfert-installation.md#installer-depuis-le-ssd-de-secours)) |
| `linux_auto_install.py`, `installer-systeme-linux.sh` | Préparation des systèmes Linux pris en charge depuis Bash, installation initiale et reprise de la sélection |
| `pilot_update.py`, `windows_update.py`, `update-windows.ps1`, `rollback-windows.ps1`, `delivery_paths.py` | Mises à jour avec sauvegarde et retour arrière ([guide](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)) |
| `maintenance_site.py` | Suivi commun `catalog/maintenance.json` et page temporaire sur les ports du portail pendant l’arrêt des conteneurs |
| `update_watch.py` | Vérification de `main` et lancement du lanceur Windows depuis le portail (dans le contrôleur hôte) |
| `windows_resume.py`, `register-windows-resume.ps1` | Reprise du téléchargement après coupure : tâche de démarrage Windows, contrôleur sous Linux depuis 0.86.0 ([guide](../exploitation/coupures-et-redemarrage.md)) |
| `pilot_kit.py`, `kit_audit.py`, `kit_maps.py` | Kit hors ligne ([guide](../installation/preparer-kit-hors-ligne.md)) |
| `kit_duplicate.py`, `kit_duplicate_gui.py`, `dupliquer-kit-windows.ps1` | Duplication du kit public hors ligne avec empreintes, reprise et conservation des installateurs locaux |
| `windows_kit_installers.py` | Préparation et contrôle des prérequis Windows sur un kit même depuis Linux ([guide](../installation/preparer-kit-hors-ligne.md#ajouter-les-installateurs-windows-depuis-linux)) |
| `pilot_backup.py` | Sauvegarde des données privées |
| `transfer.py`, `transfer_*.py`, `transfer-*.ps1` | Transfert vers un autre SSD ([guide](../exploitation/transfert-installation.md)) |

### Contrôle hôte et bibliothèque

| Fichier | Rôle |
| --- | --- |
| `control.py` | Contrôleur hôte authentifié : actions fixes (moteur, travaux), aucune exécution libre |
| `library_tasks.py`, `library_monitor.py`, `collection_tasks.py` | Travaux Kiwix et collections côté hôte ; vue bornée des travaux |
| `content.py`, `content_mirrors.py`, `content_retry.py`, `content-monitor.ps1` | Téléchargement des lots figés ([guide](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)) |
| `kiwix_select.py`, `audit_selection.py` | Sélection Kiwix par thème ([guide](../bibliotheque/selection-kiwix-par-theme.md)) |
| `library_reference.py` | Manifeste du fonds de référence figé (`deploy/library-reference.json`) : construction et vérification d’une installation ([guide](../bibliotheque/bibliotheque-complete-marc.md#fonds-de-référence-figé)) |
| `index_archives.py`, `index_categories.py`, `search_index_*.py`, `index_locks.py`, `index_reader_probe.py` | Indexation des archives et du fonds principal |
| `inventory_zim_videos.py`, `library_videos.py`, `youtube_videos.py`, `youtube_tools.py` | Vidéos ZIM et YouTube ([guide](../utilisation/telecharger-videos-youtube.md)) |
| `maps.py`, `map_install.py`, `geography_data.py`, `routing_prepare.py` | Cartes, adresses, relief et graphes OSRM |
| `runtime_resources.py`, `host_performance.py`, `gpu_windows.py` | Dimensionnement et compteurs matériels |
| `diagnose_kiwix.py` | Diagnostic des délais Kiwix ([guide](../exploitation/diagnostic-performances-kiwix.md)) |

### Évaluation et audits

`audit_library.py`, `audit_learning.py`, `audit_kit_lab.py`, `evaluate_domains.py`,
`evaluation_report.py`, `compare_models.py`, `prepare_reliability_cases.py`.

### Laboratoire de Louis (Bazzite uniquement)

`lab.sh` (enveloppe de `linux_lab.py`), `lab_*.py`. Ne jamais en faire une
dépendance des installations clientes. Respecter les contrôles de montage, le
plafond SSD et `private/inference-paused.json`.

## `deploy/` — configuration

| Fichier | Rôle |
| --- | --- |
| `release.json` | Version publiée et schéma de données |
| `versions.json` | Images et caches tiers figés (empreintes) |
| `model-profiles.json` | Modes de réponse, modèles et contextes |
| `assistant-system.fr.txt` | Contexte produit de l’assistant |
| `Caddyfile` | Proxy, HTTPS local, en-têtes de profil pour Open WebUI |
| `content-catalog.json`, `kiwix-themes.json`, `library-templates/` | Catalogue documentaire, thèmes et parcours, guides modèles |
| `map-catalog.json`, `routing/`, `routing-engine.json`, `compose.routing-windows.yaml`, `terrain-attribution.txt` | Cartes et itinéraires |
| `windows-installers.json`, `discovery-packages.json` | Installateurs Windows et paquets de découverte réseau |
| `youtube-tools.json`, `youtube-installation.txt` | Outils et liste YouTube de la première installation |
| `kiwix-entrypoint.sh` | Démarrage du conteneur Kiwix |

## Données hors Git

Modèles, ZIM, cartes, vidéos, caches, comptes, conversations, sauvegardes et
`private/` restent hors du dépôt. Les états d’exécution du pilote sont sous
`state/pilot/` sur l’installation ; voir l’[inventaire local](../utilisation/inventaire-local.md)
et le [manuel de secours](../exploitation/manuel-de-secours.md).
