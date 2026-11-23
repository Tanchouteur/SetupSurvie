# SetupSurvie

<p align="center">
  <img src="portal/branding/logo.png" width="160" height="160" alt="Logo SetupSurvie : un feu de camp et un livre ouvert">
</p>

SetupSurvie est le projet de Louis et Marc Tanchou : une bibliothèque illustrée
et un assistant IA local, accessibles depuis les appareils du réseau domestique,
même sans Internet. Il sert au quotidien, à l’éducation familiale et à la
préparation aux périodes de services dégradés.

La **V1 vise Linux**. Louis fournit gratuitement SetupSurvie à ses proches, qui
achètent leur matériel. À terme, l’offre envisagée est un PC vendu avec
SetupSurvie préinstallé. Le code propre n’est pas publié en open source.
Le [cadrage de l’offre](docs/decisions/acces-simple-et-offre.md) précise ces étapes.

## État du projet

Version **0.113.0** (23 novembre 2026), pilote accompagné chez Marc ; ce n’est pas
une offre commerciale validée. Fonctions disponibles :

- **Bibliothèque hors ligne** (Kiwix, guides, PDF) avec recherche locale indexée,
  deux espaces documentaires, [organisation des collections](docs/utilisation/classement-et-collections.md)
  et documents de secours lisibles sans IA. Elle reste accessible quand le moteur IA est arrêté.
- **Assistant local** qui cherche et lit les documents, garde la trace des
  sources réellement consultées, peut [lire plusieurs documents](docs/utilisation/documents-et-traduction.md)
  ou un [livre entier par étapes](docs/utilisation/synthese-documentaire.md) et proposer les
  [illustrations d’origine](docs/utilisation/illustrations-et-references.md).
  Les [modèles se téléchargent depuis les paramètres](docs/utilisation/portail.md#télécharger-un-modèle-pour-lassistant).
- **Traduction** progressive des documents, avec contrôles et publication partagée.
- **Vidéos** des encyclopédies et [listes YouTube](docs/utilisation/telecharger-videos-youtube.md),
  avec [sous-titres et transcription locale](docs/utilisation/videos-locales.md).
- **Cartes** hors ligne avec [points et itinéraires locaux](docs/utilisation/points-et-itineraires.md)
  et [zone téléchargeable sur téléphone](docs/utilisation/parametres-et-cartes.md#télécharger-une-zone-sur-le-téléphone).
- **File d’attente** commune des [travaux du portail](docs/utilisation/file-attente.md).
- **Profils locaux sans mot de passe**, partagés avec Open WebUI (historiques distincts).
- **Exploitation** : mises à jour avec retour arrière, reprise après coupure,
  [transfert vers un autre SSD](docs/exploitation/transfert-installation.md), diagnostics exportables.

Pour la V1, restent notamment à qualifier l’installation Linux sur disque vide,
la qualité sur le fonds livré, Safari sur iPhone réel et la restauration hors
ligne. La [liste de clôture V1](docs/essais/2026-11-20-audit-v1.md#liste-de-clôture-v1)
relie le travail restant aux [bilans datés](docs/essais/README.md).

## Commencer

Le [portail](docs/utilisation/portail.md) a une interface unique sur Windows et
Linux. L’ancienne présentation « classique » est retirée depuis la 0.63.0 (les
adresses `/classique/` et `/nouveau/` renvoient vers la racine) et la maquette
fictive depuis la 0.59.0.

- **Installer sur Windows** : double-cliquer sur `Installer-SetupSurvie.cmd`, qui prépare le PC puis poursuit l’installation. Lire le [parcours Windows](docs/installation/deux-etapes-windows.md), ses validations et ses limites.
- **Mettre à jour sur Windows** : utiliser le raccourci **Mettre à jour SetupSurvie** ou `Mettre-a-jour-SetupSurvie.cmd` dans le dossier d’installation. Le [guide de mise à jour](docs/exploitation/mises-a-jour-et-bibliotheque-pilote.md) décrit la récupération Git, la sauvegarde et le retour arrière.
- **Choisir les collections Kiwix** : utiliser la [sélection automatique par thème](docs/bibliotheque/selection-kiwix-par-theme.md), avec inventaire local et budget de téléchargement.
- **Installer le kit chez Marc** : suivre le [guide du pilote](docs/installation/pilote-marc.md). Le kit hors ligne représente environ 160 Go ; vérifier son manifeste, il n’est pas un petit installateur en ligne.
- **Préparer le matériel** : consulter la [configuration cible évolutive](docs/installation/configuration-materielle-cible.md), ses choix provisoires et les mesures encore nécessaires.
- **Préparer une installation depuis le dépôt** : lire les [parcours d’installation](docs/installation/README.md), leurs prérequis et leurs limites.
- **Trouver un document utile** : lire le [guide de recherche et de vérification depuis le site](docs/utilisation/recherche-documentaire.md).
- **Utiliser le serveur** : consulter le [guide d’utilisation](docs/utilisation/README.md).
- **Entretenir une installation existante** : suivre les [sauvegardes, restaurations et mises à jour](docs/exploitation/README.md).
- **Installer ou remettre en service hors ligne sur Linux** : suivre le [parcours depuis le SSD de secours](docs/exploitation/transfert-installation.md#installer-depuis-le-ssd-de-secours), [créer un second SSD](docs/exploitation/transfert-installation.md#dupliquer-le-ssd-de-secours) ou ouvrir le [manuel humain](docs/exploitation/manuel-de-secours.md).
- **Comprendre ou développer le projet** : lire [AGENTS.md](AGENTS.md), la [carte du code](docs/architecture/carte-du-code.md), l’[architecture](docs/architecture/README.md) et les [choix actuels](docs/decisions/choix-actuels.md).

Sur le serveur, le portail est accessible à `http://localhost:8080`, Open WebUI à
`:3000` et Kiwix à `:8081`. Depuis un autre appareil, utiliser l’IP du serveur ou
le QR code. Le nom demandé est `survie.local` ; sa résolution dépend du réseau et
du client. Le [guide Marc](docs/installation/pilote-marc.md) détaille le LAN et le
HTTPS local pour protéger les connexions sur le réseau.

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
