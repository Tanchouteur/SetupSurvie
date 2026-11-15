# SetupSurvie

<p align="center">
  <img src="portal/branding/logo.png" width="160" height="160" alt="Logo SetupSurvie : un feu de camp et un livre ouvert">
</p>

SetupSurvie est le projet de Louis et Marc Tanchou : une bibliothèque illustrée
et un assistant IA local, accessibles depuis les appareils du réseau domestique,
même sans Internet. Il sert au quotidien, à l’éducation familiale et à la
préparation aux périodes de services dégradés.

## État du projet

Au **15 novembre 2026**, le pilote **0.19.1** propose une recherche locale avec
indexation automatique, deux espaces documentaires et diagnostic exportable.
Les résultats arrivent progressivement ; un cache local réutilise les réponses
valides pour le même état du fonds, avec budget disque ajustable. Des outils
volontaires permettent aussi d’inventorier les vidéos/sous-titres locaux et de
mesurer les délais Kiwix, sans IA ni modification des contenus.
Le traitement progressif réutilise aussi les textes et métadonnées déjà préparés
pendant la demande ; le diagnostic sépare ce coût des appels aux encyclopédies.
Le nombre d’appels autorisés s’adapte aux lots d’archives dans le flux long,
avec une durée et une concurrence bornées.
Le tri distingue les titres de tâche, les questions périphériques et les sujets
généraux, sans certifier le contenu à partir du seul titre.
Les nouvelles réponses de l’assistant conservent aussi un suivi des recherches
et lectures réellement effectuées, indépendant du texte du modèle, avec accès
aux documents consultés même lorsqu’ils ne sont pas cités.
On peut [choisir plusieurs documents](docs/utilisation/documents-et-traduction.md#choisir-les-documents-dune-conversation--0170)
pour une même question ; leur sélection est conservée et les PDF peuvent fournir
une page pertinente au-delà de leur aperçu de début. Une
[synthèse longue](docs/utilisation/synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180)
peut aussi lire les textes choisis par étapes, avec suivi, pause et reprise.
L’assistant peut proposer les [illustrations originales](docs/utilisation/illustrations-et-references.md)
des sources consultées, selon leurs légendes, avec accès aux pages PDF entières.
Il ajoute un contrôle complet de 32 demandes, la relecture des résultats et la
prise en charge des redirections d’articles. Les espaces, types de documents et
noms de collections sont corrigibles et exportables. Des rapports de délais et un
essai mémoire volontaire complètent le contexte IA réglable par modèle. Un
comparatif facultatif permet de mesurer une aide IA à la recherche, conservée
désactivée dans l’usage habituel en attendant les résultats réels. Six dossiers
pratiques facultatifs donnent quelques repères, sans limiter les sujets recherchables.
Un [contrôle d’usage hors ligne](docs/utilisation/verifier-usage-hors-ligne.md)
réunit les mesures sans IA et les observations humaines dans un rapport.
L’outil d’indexation vérifie ses prérequis isolés avant le parcours des archives.
Les données existantes restent compatibles et conservées. La qualité sur le fonds
réel, l’installation complète sur PC vierge, Safari réel et la recette complète
hors ligne restent à qualifier ; consulter les [bilans datés](docs/essais/README.md).
Le pilote n’est pas une offre commerciale validée.

La bibliothèque reste accessible quand le moteur IA est arrêté. Le portail et
Open WebUI partagent les comptes, avec des historiques de conversations distincts.
Les [bilans datés](docs/essais/README.md) précisent ce qui a réellement été essayé.

Les cartes proposent désormais un [choix d’accès aux itinéraires](docs/utilisation/points-et-itineraires.md), avec relief transparent et liaisons hors réseau distinguées. La recette sur les deux PC reste à réaliser.

Les [paramètres sont regroupés par usage](docs/utilisation/parametres-et-appareil.md),
avec suivi des travaux et options techniques dépliables.

## Commencer

Le portail **0.17.0** propose une [nouvelle organisation](docs/utilisation/nouvelle-interface.md)
sur Windows et Linux, avec les données réelles. La présentation précédente reste
conservée sous `/classique/`, sans bouton dans les menus ; la maquette fictive reste séparée.

- **Installer sur Windows** : double-cliquer sur `Installer-SetupSurvie.cmd`, qui prépare le PC puis poursuit l’installation. Lire le [parcours Windows](docs/installation/deux-etapes-windows.md), ses validations et ses limites.
- **Mettre à jour sur Windows** : utiliser le raccourci **Mettre à jour SetupSurvie** ou `Mettre-a-jour-SetupSurvie.cmd` dans le dossier d’installation. Le [guide de mise à jour](docs/exploitation/mises-a-jour-et-bibliotheque-pilote.md) décrit la récupération Git, la sauvegarde et le retour arrière.
- **Choisir les collections Kiwix** : utiliser la [sélection automatique par thème](docs/bibliotheque/selection-kiwix-par-theme.md), avec inventaire local et budget de téléchargement.
- **Installer le kit chez Marc** : suivre le [guide du pilote](docs/installation/pilote-marc.md). Le kit hors ligne représente environ 160 Go ; vérifier son manifeste, il n’est pas un petit installateur en ligne.
- **Préparer une installation depuis le dépôt** : lire les [parcours d’installation](docs/installation/README.md), leurs prérequis et leurs limites.
- **Trouver un document utile** : lire le [guide de recherche et de vérification depuis le site](docs/utilisation/recherche-documentaire.md).
- **Utiliser le serveur** : consulter le [guide d’utilisation](docs/utilisation/README.md).
- **Entretenir une installation existante** : suivre les [sauvegardes, restaurations et mises à jour](docs/exploitation/README.md).
- **Comprendre une panne et préparer le secours** : lire le [manuel humain](docs/exploitation/manuel-de-secours.md) et le [protocole du disque de secours complet](docs/exploitation/disque-de-secours-hors-ligne.md), dont l’installateur autonome reste à réaliser.
- **Comprendre ou développer le projet** : partir de l’[architecture](docs/architecture/README.md) et des [choix actuels](docs/decisions/choix-actuels.md).

Sur le serveur, le portail est accessible à `http://localhost:8080`, Open WebUI à
`:3000` et Kiwix à `:8081`. Depuis un autre appareil, utiliser l’IP du serveur ou
le QR code. Le nom demandé est `survie.local` ; sa résolution dépend du réseau et
du client. Le [guide Marc](docs/installation/pilote-marc.md) détaille le LAN et le
HTTPS local, nécessaire pour la dictée et les connexions protégées.

## Se repérer dans le dépôt

| Dossier | Rôle |
| --- | --- |
| `portal/` | Interface du portail et lecteur de cartes |
| `pilot/` | Passerelle FastAPI : comptes, conversations, recherche et outils locaux |
| `deploy/` | Configurations, catalogues, profils et références des composants |
| `scripts/` | Installation, livraison, maintenance et outils du laboratoire de Louis |
| `tests/` | Tests automatisés et scénarios de navigation |
| `docs/` | Guides de référence, plans, décisions et bilans datés |
| `assets/branding/` | Source du logo ; variantes utilisées dans `portal/branding/` |
| `fixtures/` | Exemples et cas d’évaluation, distincts du fonds documentaire pratique |

Les documents volumineux, modèles, caches, comptes et secrets restent hors de Git.
Les outils `lab*` et `linux_lab.py` concernent le PC de Louis ; ils ne sont pas des
prérequis pour les clients Windows/Linux.

L’[index de documentation](docs/README.md) indique les références par sujet.
Les [archives et anciens chemins](docs/historique/README.md) conservent le parcours
du projet. Les consignes de contribution et de maintenance sont dans [AGENTS.md](AGENTS.md).
