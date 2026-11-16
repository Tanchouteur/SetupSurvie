# Refonte UX intégrée — 0.34.0

**Bilan technique — 16 novembre 2026.** Livraison préparée sur
`codex/refonte-ux`, après intégration du lot vidéo 0.33.0 (`3dd2409`), puis du correctif de
recherche 0.33.1 (`fafc21e`).
Les preuves ci-dessous portent sur le code et des services de test ; elles ne
constituent pas une mise à jour du PC de Marc ou de Louis ni une validation
humaine de l’ergonomie.

## Résultat

L’assistant dispose de trois zones sur PC : conversations/dossiers, discussion,
documents. Les volets se replient ; les petites largeurs montrent une seule zone.
Le classement est personnel au profil, avec renommage, recherche dans les titres
et messages, déplacement, suppression de dossier conservant ses conversations et
pagination. Les sources consultées proviennent du suivi documentaire enregistré,
séparément des documents simplement choisis.

La traduction reste dans le lecteur portail et dans le PDF dédié. On retrouve
les travaux par original, sans changer la conversation courante ni reprendre un
traitement implicitement. Pages, modèles, termes, comparaison, progression,
avertissements, propositions refusées, pause/reprise/arrêt/suppression, exports
et publication gardent les mécanismes du moteur existant. Le lecteur publié
français et les originaux restent accessibles.

L’accueil propose la reprise mémorisée par profil ; Mon appareil rassemble les
traductions et synthèses personnelles récentes. Navigation PC en haut, lecture
bornée sur grand écran, titres concrets et aides facultatives au survol, clic,
clavier et Échap utilisent des composants communs. Les commandes existantes sont
déplacées sans multiplier les IDs. Les vidéos/ZIM, sous-titres, cartes, profils,
paramètres et diagnostics restent intégrés.

La version mineure **0.34.0** correspond à une évolution fonctionnelle
significative compatible. Le contrat de données reste `data_schema: 1`, les
nouvelles tables d’organisation sont additives et aucune version tierce n’a changé.
Voir l’[inventaire des parcours](../decisions/inventaire-parcours-ux.md) et le
[guide utilisateur](../utilisation/nouvelle-interface.md).

## Vérifications

Environnement : runner Linux CPU, Python isolé, fixtures minuscules, API et
inférence simulées. Aucun modèle, ZIM documentaire ou carte lourde téléchargé.
Le petit média synthétique et l’archive ZIM native de test restent des fixtures.

| Contrôle | Résultat enregistré |
| --- | --- |
| Suite finale `python -m unittest discover -s tests -v` | 947 tests, aucun échec, 6 ignorés, environ 248 s après reprise de 0.33.1 |
| Dernier contrôle API | 32 tests réussis, dont propriétaires des dossiers et métadonnées personnelles |
| Retour volontaire | 19 tests réussis : données récentes conservées, refus identique/plus récent et restauration de la version quittée si échec |
| Compatibilité de stockage avec 0.33.0 | Base SQLite réelle ouverte par l’ancien puis le nouveau code : messages, titres, classement et traduction conservés |
| Fondations UX | 41 contrôles par moteur, Chromium et WebKit : PC 1024/1366/1440/1920, mobile 320/390, clavier et aide |
| Espace assistant | 16 contrôles par moteur, Chromium et WebKit : création, renommage, classement, persistance, recherche, volets et petites largeurs |
| Traduction dans les lecteurs | 13 contrôles par moteur, Chromium et WebKit : lecture en place, conversation préservée, comparaison, pause/rechargement, changement de rubrique, titre visible et PDF dédié |
| Confort conversation | 38 contrôles par moteur, Chromium et WebKit, dont écran court 320×568 et paysage 844×390 |
| Synthèse et traduction ordinaires | Synthèse longue : 19 contrôles par moteur ; cycle association/pause/reprise/export et plage PDF réussi sur les deux moteurs, à quatre tailles |
| Suivi documentaire WebKit | 25 contrôles réussis après correction du repli de conversations pendant le rechargement |
| Portail et paramètres | 29 et 182 contrôles Chromium après réconciliation des modules |
| Génération et Compose | Pages générées et configurations Windows CPU/GPU/routeurs vérifiées ; aucun service cible démarré |
| Analyse statique | Syntaxe JavaScript et `git diff --check` réussis |

La suite Python et la recette ciblée réunie Chromium/WebKit ont réussi. Le
stockage et les dépendances figées de 0.33.1 sont identiques à ceux de 0.33.0. La CI
complète est encore suivie avant l’intégration ; son reçu sera inscrit avant clôture.
Les recettes nouvelles sont incluses dans le lanceur navigateur réellement appelé
par la CI, et pas seulement dans un lanceur local facultatif.

Les premières tentatives ont identifié des recettes dépendant d’un libellé de
traduction devenu variable, ou supposant le formulaire de recherche visible
pendant la lecture. Elles utilisent désormais l’action stable et le retour aux
résultats. Le chargement complet d’un PDF ne se termine pas toujours sous WebKit :
la recette attend le DOM puis les contrôles utiles. Les contrôles de lecture et
de retour restent exécutés. Le parcours complet a aussi révélé un chevauchement
des commandes sur petit écran : le volet Documents défile désormais sans réduire
son contenu sous le bloc des sources. Le retour à un lecteur pendant une recherche
a été corrigé, avec une recette dédiée et conservation du périmètre de recherche.

Le Playwright MCP a servi à la navigation, aux captures et aux essais ciblés.
Les suites locales utilisent ensuite Chromium/WebKit du conteneur TEST
Playwright 1.58.2, avec seulement le code et les fixtures, sans secrets ni GPU.
Le serveur dédié est au port 18769 ; l’adaptation locale des adresses de fixture
est extérieure au dépôt. Les tests CI gardent leur serveur standard au port 8769.

## Paquet logiciel

Le candidat précédant le dernier correctif de recherche a été construit et
audité : 943 fichiers, environ 7,21 Mio, empreintes
du manifeste vérifiées, nouveaux modules et lanceur de retour inclus. Les
dépendances figées sont identiques au paquet 0.33.0. La livraison finale est
reconstruite après clôture documentaire, avec son fichier SHA-256 associé ;
aucune donnée utilisateur ni ressource lourde n’est incluse.

## Retour et limites

Les trois références sont archivées hors Git et leurs tags sont poussés :
`ux-reference-0.32.1` (avant les deux chantiers) et `ux-reference-0.33.0` (avec
les vidéos), puis `ux-reference-0.33.1` (retour recommandé, avec le correctif de recherche). Le [guide de retour](../exploitation/retour-version-avant-refonte.md)
donne empreintes et procédure. Le retour sauvegarde les données actuelles puis
remplace le code ; il ne remet pas d’anciennes conversations à la place des récentes.

Restent à qualifier séparément : installation/retour physique Windows/Linux,
Safari sur iPhone réel, qualité de traduction d’un modèle et ergonomie auprès de
Marc. Le protocole avant/après de l’inventaire prévoit tâches sans indice,
réussite, hésitations et erreurs ; les temps d’inférence sont séparés de la
navigation. Aucun gain humain chiffré n’est inventé. La campagne de fiabilité et
le disque de secours complet restent l’autre objectif prévu, hors de cette refonte.
