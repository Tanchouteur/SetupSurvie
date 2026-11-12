# SetupSurvie

<p align="center">
  <img src="portal/branding/logo.png" width="160" height="160" alt="Logo SetupSurvie : un feu de camp et un livre ouvert">
</p>

Projet de Louis et Marc Tanchou : préparer un serveur de connaissances utilisable sans Internet, avec une bibliothèque illustrée et un assistant IA local, accessible depuis les appareils à proximité.

**État au 11 novembre 2026 : paquet pilote préparé et essais Linux effectués.** Le laboratoire Podman de Louis utilise un volume isolé sur le SSD de 4 To, plafonné sous 600 Go. Voir les [commandes et résultats des essais Linux](docs/17-essais-linux-2026-11-11.md). Compose et les lanceurs Docker Windows/Linux restent disponibles ; les essais Windows chez Marc restent à faire. Le premier objectif reste un prototype pour Louis et Marc ; la vente viendra ensuite.

Suite des essais : [dictée locale, trois tailles de modèles, Wikipédia illustré et accueil simplifié](docs/18-dictee-modeles-bibliotheque.md).

Pour cette livraison : [guide du pilote Marc](docs/22-pilote-marc.md), [résultats, modèles retenus et réserves](docs/23-bilan-pilote-2026-11-11.md), [connexion simple et direction du produit](docs/24-acces-simple-et-offre.md). La [liste initiale des travaux](docs/19-avant-premiere-installation-marc.md) conserve le contexte de préparation.

Recherche en cours : [sept modèles, contexte, outils, corpus bilingue et protocole de reprise](docs/20-campagne-modeles-contexte-et-corpus.md). Les calculs IA sont actuellement suspendus en mode jeu ; les téléchargements documentaires sont terminés.

Le pilote **0.1.5** ajoute les [mises à jour du logiciel et les téléchargements documentaires reprenables](docs/26-mises-a-jour-et-bibliotheque-pilote.md), avec application séparée du kit et restauration en cas d’échec.

Le pilote **0.1.7** ajoute les [ressources du Sud et les contrôles de recherche et d’IA](docs/28-bibliotheque-sud-recherche-et-ia.md) : cartes hors ligne de Solliès-Ville/PACA/Occitanie/Corse, risques locaux, nouveaux manuels, recherche bilingue et suivi de l’indexation.

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

Le [catalogue des fonctionnalités et user stories](docs/15-fonctionnalites-et-user-stories.md) distingue le socle à tester des développements restants. Le site réunit la recherche plein texte des guides lisibles et celle des archives Kiwix. Open WebUI reste accessible pour ses dossiers et conversations ; les historiques des deux interfaces sont distincts.

## Documentation

- [Where There Is No Doctor : téléchargement et recette](docs/bibliotheque/where-there-is-no-doctor.md) : édition 2025 complète, indexation et essai réel de l’assistant.
- [Sélection automatique Kiwix par thème](docs/bibliotheque/selection-kiwix-par-theme.md) : inventaire local, plan de sélection et téléchargement contrôlé.

- [Inventaire complet des ressources téléchargées](docs/29-inventaire-ressources-telechargees.md) : les 10 archives, 68 PDF et 2 cartes réellement présents.
- [Bibliothèque du Sud, recherche et IA](docs/28-bibliotheque-sud-recherche-et-ia.md) : contenus réellement ajoutés, cartes, recette des sources et limites.
- [Plan de bibliothèque hors ligne — 500 Go](docs/25-plan-bibliotheque-hors-ligne-500go.md) : inventaire des téléchargements actuels, ressources à ajouter, priorités et budget complet.
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
