# Préparation du kit sur un Linux sans Python ni Docker

**Bilan daté — 22 novembre 2026, SetupSurvie 0.100.0.** Le kit public peut
embarquer les outils Linux et en vérifier les empreintes. La duplication
propage les installateurs et refuse une préparation incomplète. La version
mineure raccorde ces outils au lanceur d’installation qui prévoit une
autorisation graphique et un moteur Docker dédié à la destination.

Le téléchargement des fichiers épinglés du projet, environ 200 Mo, a
réussi. Dans un conteneur Debian 12 sans réseau ni Python ni Docker au
départ, le script du kit a extrait puis exécuté Python 3.13.18, le client
Docker 29.9.3, Compose 5.8.0 et nftables 1.0.6. L’exécution de Python a
aussi vérifié l’import de SQLite. La mise en service du démon Docker,
le passage de l’autorisation et la relance avec systemd étaient simulés
dans les tests automatisés. Ces tests contrôlent un démarrage indépendant
du SSD et l’arrêt du seul moteur de cette copie après un échec simulé.

Voir [Préparer et vérifier le kit](../installation/preparer-kit-hors-ligne.md#ajouter-les-installateurs-linux).
La recette sur un PC ou une VM avec systemd et un SSD réseau coupé, le
point protégé dans ce parcours et la reprise de la première copie restent
à qualifier ou à implémenter.
