# Architecture — interface du portail

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Interface et organisation — 0.34.0

Les trois zones de `assistant-workspace` déplacent les contrôles existants sans
dupliquer leurs IDs ; les événements vidéo/document/profil restent partagés.
`ux-system` fournit l’aide facultative, les variables de présentation, la reprise
et les travaux personnels. Les commandes sont repérées par ID ou `data-*`, jamais
par le titre traduit d’un panneau. Le générateur produit les deux entrées HTML.

`reader-work` utilise un même contrôleur pour le lecteur du portail et le PDF
dédié. Il observe les travaux du profil et ne remplace pas `S.conversation` pour
préparer une traduction. Les API existantes restent responsables de l’inférence,
de la qualité, des interruptions et de la publication. Quitter la page arrête
l’observation ; revenir ne reprend pas le traitement. Un module optionnel absent
doit laisser la lecture, la recherche et les conversations utilisables.

`conversation_organization.py` ajoute paresseusement deux tables (dossiers et
classement) sans modifier les colonnes historiques de conversations. Un titre
manuel utilise les réglages existants. Les nouvelles routes dossiers/titre/
classement vérifient toujours le propriétaire ; supprimer un dossier ne supprime
pas ses conversations. La recherche échappe les métacaractères LIKE et pagine
par 100. Sans paramètres, l’ancienne liste reste disponible en repli si le module
optionnel manque. Le contrat de données demeure `data_schema: 1`.

`document_workspace.py` expose uniquement les métadonnées des travaux du profil
via `/api/document-work?source_id=...` et `/api/my-work`. Les instantanés privés et
les propositions refusées ne deviennent pas des documents publics par ces routes.
Voir l’[inventaire des parcours](../decisions/inventaire-parcours-ux.md).

## Plan de refonte du portail — 13 novembre 2026

Le [plan UX](../decisions/plan-refonte-ux.md) propose une nouvelle répartition des
écrans, un suivi commun des opérations et une navigation mémorisée, avec une
interface classique conservée et utilisable. Il définit aussi les différences
ordinateur/téléphone et les critères de non-régression. Ce plan ne décrit pas
une refonte déjà livrée ; les composants et procédures actuels restent inchangés.

En 0.1.31, une [maquette navigable](../utilisation/maquette-ux.md) isolée permettait d’essayer cette organisation sans appels API. Elle a été retirée du paquet en 0.59.0.

## Interface fonctionnelle — 0.1.32

> **Remplacé en partie par 0.63.0 (19 novembre 2026).** L’interface classique est
> retirée et `portal/nouveau/` est renommé `portal/interface/`. Le balisage des
> contrôles vit désormais dans `portal/interface/modele.html` ;
> `scripts/build_portal.py` en génère la seule entrée, `portal/index.html`.
> `/classique/` et `/nouveau/` ne contiennent plus qu’une page de redirection
> vers la racine. Le paragraphe ci-dessous décrit l’organisation de 0.1.32.

En 0.1.32, l’entrée principale et `/nouveau/` servaient la nouvelle organisation,
avec les API existantes, et `/classique/` conservait ses propres scripts/styles.
`scripts/build_portal.py` générait alors les entrées modernes à partir du balisage
classique ; il part aujourd’hui de `portal/interface/modele.html`. `layout.js` déplace les contrôles
existants avant leur liaison ; `navigation.js` adapte historique et contexte.
Depuis 0.12.0, `settings-layout.js` s’exécute après la création des panneaux
fonctionnels et avant la navigation : il déplace une seule fois les nœuds existants,
sans les cloner, en conservant IDs, événements, ancêtres `article`/`details` et
`view-settings` attendus par les contrôleurs. `settings.css` complète la charte.
Les nouvelles sous-rubriques restent des présentations de `view-settings`, sans
nouvelle API. La route demandée est conservée pendant la lecture du profil ; un
rechargement retire le marqueur d’un dialogue qui n’est plus ouvert. Le contrôleur
commun ne réécrit pas les adresses historiques dans cette interface ; les
écritures de position identiques sont évitées et celles du défilement espacées
de 250 ms pour préserver la navigation WebKit.
Voir la [correspondance des commandes](../utilisation/parametres-et-appareil.md).

`GET /api/activity` passe par la route interne authentifiée `/activity` du
contrôleur. `scripts/library_monitor.py` associe identité, plan, reçus et progrès
sans ouvrir de base ni prendre de verrou. Un cache hôte de cinq secondes borne
les lectures concurrentes ; aucune erreur brute, chemin ou PID n’est publié.
Le téléchargeur enregistre aussi un petit plan courant pour les transferts directs
Windows/Linux. Aucune commande indépendante n’est ajoutée par cet endpoint.
Voir le [guide](../utilisation/portail.md) et le
[bilan](../essais/2026-11-13-interface-fonctionnelle.md).

Depuis 0.1.34, `portal/interface/collections.js` filtre uniquement les cartes de
l’inventaire déjà affichées ; leurs actions restent attachées aux mêmes éléments.
Le routeur mémorise le filtre et ouvre directement la page native Cartes.
Le relief repose sur les tuiles locales existantes, sans nouvelle source réseau.
