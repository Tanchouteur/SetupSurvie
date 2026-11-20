# Documentation SetupSurvie

**Index général — revu le 20 novembre 2026 pour la version 0.66.0.**
Chaque document indique son statut et la version qu’il décrit. Les liens de cet
index vont vers les références actuelles ; les étapes passées sont dans les
[bilans datés](essais/README.md) et l’[historique](historique/README.md).

## Par où commencer

| Je veux… | Lire |
| --- | --- |
| Comprendre le produit et son état | [README du dépôt](../README.md), puis les [choix actuels](decisions/choix-actuels.md) |
| Utiliser le serveur en famille | [Utilisation](utilisation/README.md) |
| Installer depuis le kit ou le dépôt | [Installation](installation/README.md) |
| Sauvegarder, restaurer, mettre à jour, transférer | [Exploitation](exploitation/README.md) |
| Comprendre une panne sans IA | [Manuel de secours](exploitation/manuel-de-secours.md) |
| Savoir quel fichier fait quoi dans le code | [Carte du code](architecture/carte-du-code.md) |
| Comprendre les composants et les données | [Architecture](architecture/README.md) |
| Modifier l’interface | [Guide de design](architecture/guide-design.md) et [composants](architecture/composants-interface.md) |
| Connaître les contenus et lots documentaires | [Bibliothèque](bibliotheque/README.md) |
| Savoir ce qui a réellement été testé | [Essais et résultats](essais/README.md) |
| Connaître les priorités vers la V1 | [Feuille de route V1](decisions/feuille-de-route-v1.md) (proposition) |

### Pour un agent de développement

1. Lire [AGENTS.md](../AGENTS.md) : règles du dépôt, Git, versions, tests, données privées.
2. Repérer les fichiers concernés dans la [carte du code](architecture/carte-du-code.md).
3. Lire le guide de référence du sujet (tableaux ci-dessous) et la décision correspondante.
4. Après le changement : mettre à jour ce guide de référence dans la même livraison,
   ajouter un bilan daté dans `essais/` et l’inscrire dans l’[index des essais](essais/README.md).

## Lire les statuts

- **Guide de référence** : procédure ou description à entretenir avec le logiciel.
  Sa version en tête indique la dernière révision, pas forcément la version courante.
- **Décision** : choix de Louis, daté ; une décision remplacée reste visible avec son remplaçant.
- **Plan ou proposition** : objectif et pistes ; aucune réalisation implicite.
- **Bilan daté** : constat d’une campagne, avec sa version, sa machine et ses limites.
- **Archive** : étape conservée, dont les commandes et affirmations peuvent être dépassées.

Distinguer prévu, implémenté, téléchargé, indexé et réellement testé. Les constats
Linux, Windows, mobiles et hors ligne restent distincts.

## Guides de référence

### Utilisation

Voir l’[index d’utilisation](utilisation/README.md) pour la liste complète, classée
par sujet : portail, paramètres, profils, file d’attente, recherche, classement,
sources, documents et traduction, synthèse, illustrations, vidéos, YouTube, cartes
et itinéraires, mesures facultatives.

### Installation

- [Parcours d’installation](installation/README.md) — Windows, Linux, kit hors ligne, vidéos de première installation.
- [Installation Windows avec un seul lanceur](installation/deux-etapes-windows.md) — `Installer-SetupSurvie.cmd`, reprise, mises à jour Git ; PC vierge encore à valider.
- [Pilote chez Marc](installation/pilote-marc.md) — kit, réseau local, HTTPS, sauvegarde et restauration.
- [Préparer et vérifier le kit hors ligne](installation/preparer-kit-hors-ligne.md) — environ 160 Go, manifeste et dépendances.
- [Configuration matérielle cible](installation/configuration-materielle-cible.md) — orientations de Louis et mesures à compléter.

### Exploitation

Voir l’[index d’exploitation](exploitation/README.md) : mises à jour et contenus,
coupures et redémarrage, transfert vers un SSD, diagnostics, cache de recherche,
journal des incidents Windows, manuel de secours et protocole du
[disque de secours complet](exploitation/disque-de-secours-hors-ligne.md) (plan, à réaliser).

### Architecture

- [Carte du code](architecture/carte-du-code.md) — modules, scripts, configuration : où se trouve quoi.
- [Architecture](architecture/README.md) — vue d’ensemble des composants, puis un document par domaine :
  [interface](architecture/interface.md), [recherche et index](architecture/recherche.md),
  [assistant et lecture](architecture/assistant.md), [traduction](architecture/traduction.md),
  [vidéos](architecture/videos.md), [mesures](architecture/mesures.md), [cartes](architecture/cartes.md).
- [Guide de design « Veillée »](architecture/guide-design.md) — navigation, lecture, vidéo, recette visuelle.
- [Composants de l’interface](architecture/composants-interface.md) — organisation CSS/JS et règles de présentation.

### Bibliothèque

- [Index de la bibliothèque](bibliotheque/README.md)
- [Savoirs et savoir-faire durables](bibliotheque/savoirs-durables.md) — référence unique des besoins de Marc.
- [Bibliothèque complète de Marc et laboratoire réduit](bibliotheque/bibliotheque-complete-marc.md)
- [Sélection automatique Kiwix par thème](bibliotheque/selection-kiwix-par-theme.md)
- [Plan de bibliothèque hors ligne 500 Go](bibliotheque/plan-bibliotheque-hors-ligne-500go.md) — plan, pas une preuve de téléchargement.
- [Inventaire des ressources téléchargées — 11 novembre 2026](bibliotheque/inventaire-ressources-telechargees.md) — constat daté.
- [Where There Is No Doctor](bibliotheque/where-there-is-no-doctor.md) et [notice Baofeng et antennes](bibliotheque/baofeng-et-antennes.md).

## Décisions

### Référence courante

- [Choix et contraintes actuels](decisions/choix-actuels.md) — décisions en vigueur, les plus récentes en premier.
- [Offre de PC préinstallé et accès simple](decisions/acces-simple-et-offre.md) — direction commerciale confirmée, offre à qualifier.
- [Feuille de route vers la V1](decisions/feuille-de-route-v1.md) — bilan et proposition du 17 novembre 2026.
- [Boîte à idées](decisions/boite-a-idees.md) — évolutions reportées, sans engagement.

### Par sujet

| Sujet | Documents |
| --- | --- |
| Recherche et contenus | [Fiabilisation de la recherche](decisions/fiabilisation-recherche-et-contenus.md), [plan des améliorations de Marc L1–L9](decisions/plan-ameliorations-marc.md), [assistant : recherche et synthèse](decisions/assistant-recherche-et-synthese.md), [diagnostic des lenteurs](decisions/diagnostic-lenteurs-en-un-clic.md) |
| Interface | [Refonte UX évolutive](decisions/refonte-ux-evolutive.md), [inventaire des parcours](decisions/inventaire-parcours-ux.md), [conversations en trois zones](decisions/conversations-trois-zones.md), [file d’attente des travaux](decisions/file-attente-travaux.md), [plan de refonte du 13 novembre](decisions/plan-refonte-ux.md) |
| Vidéos | [Vidéos locales et recherche](decisions/videos-locales-et-recherche.md), [vidéos dans les ZIM](decisions/inventaire-videos-zim.md), [audio des vidéos ZIM](decisions/audio-videos-zim.md), [acquisition des sous-titres](decisions/acquisition-sous-titres.md), [téléchargement YouTube](decisions/telechargement-videos-youtube.md) |
| Produit | [Apports de NOMAD](decisions/apports-nomad.md) |

### Consignes de chantier et coordination (historique de travail)

[Prompt de refonte des conversations](decisions/prompt-refonte-conversations.md),
[prompt de refonte des paramètres](decisions/prompt-refonte-parametres.md),
[prompts vidéos et performances](decisions/prompts-agents-videos-et-performances.md),
[coordination UX et vidéos](decisions/coordination-ux-et-videos.md),
[coordination transfert et vidéos](decisions/integration-transfert-et-videos.md).

### Besoins initiaux (30 octobre 2026)

[Questions et décisions](decisions/questions-et-decisions.md) et
[fonctionnalités et user stories](decisions/fonctionnalites-et-user-stories.md).

## Essais et historique

- [Essais et résultats](essais/README.md) — tous les bilans datés, protocoles et recettes, par date.
- [Nouveautés documentées par livraison](historique/nouveautes-par-livraison.md) — ancien index chronologique (0.3.0 → 0.66.0).
- [Livraisons détaillées](historique/livraisons.md) — notes de livraison retirées des choix actuels.
- [Historique et anciens chemins](historique/README.md) — études, prototype et table de correspondance des chemins.

## Entretenir cette documentation

- Ne pas ajouter de journal de livraison en tête de cet index : inscrire le bilan
  dans l’[index des essais](essais/README.md) et mettre à jour le guide concerné.
- Après création, déplacement ou renommage d’un document : actualiser cet index,
  l’index du dossier, les liens et la [table des anciens chemins](historique/README.md).
- Vérifier les liens et ancres locaux avant de livrer.
