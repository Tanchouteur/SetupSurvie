# SetupSurvie

Projet de Louis et Marc Tanchou : préparer un serveur de connaissances utilisable sans Internet, avec une bibliothèque illustrée et un assistant IA local, accessible depuis les appareils à proximité.

**État au 30 octobre 2026 : prototype prêt à installer pour essais.** Compose, lanceurs Windows/Linux, portail et jeu d’essai documentaire sont préparés. Les contrôles locaux ne remplacent pas les essais sur le PC Windows de Marc et le PC Linux NVIDIA. Le premier objectif reste un prototype pour Louis et Marc ; la vente viendra ensuite.

## Commencer

Lire le [guide d’installation Windows puis Linux](docs/14-installation.md), installer les prérequis indiqués, puis lancer depuis le dépôt :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Lan
```

Puis, sur le PC Linux préparé pour Docker et NVIDIA :

```bash
./scripts/install.sh --lan
```

Accueil : `http://ADRESSE-IP-DU-PC:8080`. Les données locales et identifiants ne sont pas versionnés. Aucun téléchargement massif de Wikipédia n’est lancé automatiquement.

Le [catalogue des fonctionnalités et user stories](docs/15-fonctionnalites-et-user-stories.md) distingue le socle à tester des développements restants. Le filtre de titres du portail n’est pas une recherche plein texte de tous les guides : Kiwix fournit celle des archives, et une recherche commune reste à développer.

## Documentation

- [Installation et essais](docs/14-installation.md) : commandes, prérequis et fonctionnement hors ligne.
- [Fonctionnalités et user stories](docs/15-fonctionnalites-et-user-stories.md) : besoins, priorités, critères et état réel.
- [Vérifications du paquet](docs/16-verification-prototype.md) : contrôles effectués et validations restantes.

- [Architecture et installation du prototype](docs/13-architecture-et-installation-prototype.md) : proposition concrète à essayer et préparation d’un déploiement reproductible.
- [NOMAD ou assemblage](docs/12-comparaison-nomad-assemblage.md) : comparaison fondée sur la documentation et le code inspecté.

- [Bibliothèque, recherche et images](docs/11-bibliotheque-recherche-et-images.md) : rôles des services, Wikipédia/Kiwix et récupération d’illustrations.

- [Sélection de modèles et outils](docs/08-selection-modeles-et-outils.md) : capacités, résultats publiés et faisabilité sur les deux PC.
- [Machines dédiées](docs/09-machines-dediees.md) : idées autour de 1 000 € et paliers supérieurs.
- [Protocole de comparaison](docs/10-protocole-comparaison-ia.md) : mesurer le gain réel d’un gros modèle lent.

- [Périmètre du prototype](docs/05-perimetre-prototype.md) : synthèse des choix actuels, évolutions et vérifications proposées.
- [Fiabilité et outils spécialisés](docs/06-fiabilite-et-outils.md) : pistes pour les usages sensibles et leur évaluation.
- [Modes IA et travaux longs](docs/07-modes-ia-et-travaux-longs.md) : agents, modèles de plusieurs tailles et dossiers lancés le soir.
- [Cadrage et besoins](docs/01-cadrage.md) : intentions exprimées, usages et périmètre à préciser.
- [État des lieux](docs/02-etat-des-lieux.md) : matériel déclaré, pistes étudiées et inconnues.
- [Rôle et limites de l’IA locale](docs/04-ia-locale.md) : capacités à évaluer et distinction entre texte, documents et images.
- [Questions et décisions](docs/03-questions-et-decisions.md) : entretien de cadrage et suivi des choix.
- [Contexte initial conservé](docs/sources/contexte-initial.md) : texte transmis au démarrage, sans vérification indépendante.

## Méthode

1. Préciser les utilisateurs, les usages prioritaires et le résultat attendu du prototype.
2. Identifier la machine de test et les contraintes pratiques.
3. Comparer les solutions utiles à ces besoins, puis documenter les choix.
4. Construire et tester une installation reproductible, notamment sans Internet et après redémarrage.

Les documents distinguent les besoins exprimés, les propositions et les décisions. Les annonces des projets tiers et les estimations du contexte initial ne constituent pas des résultats de tests.

Le dépôt doit contenir la documentation puis la configuration et les outils d’installation. Les bibliothèques, modèles IA, données personnelles et secrets restent hors de Git.
