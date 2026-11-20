# Dossier de qualification de SetupSurvie

Ce dossier réunit les preuves d'installation et de restauration observées, avec
les limites de chaque essai. Une version est qualifiée pour un parcours et
une configuration précis quand le scénario correspondant a réussi sur cette
configuration. Les simulations et les essais sur une machine préparée sont
identifiés séparément.

- [Matrice des essais](matrice.md)
- [Procédure de reproduction](reproduction.md)
- [Résultats datés, défauts et reprises](resultats.md)
- [Relevés des redémarrages Linux 0.72.0](preuves-linux-0.72.0.tsv)

La [matrice](matrice.md) documente les réussites du lanceur en ligne et de la
restauration sans Internet sur Debian 12, Debian 13 et Ubuntu 22.04 x86-64.
Elle indique aussi les versions testées sur Bazzite et le scénario antérieur
qui couvre la copie et la recherche de vidéos avec leurs sous-titres.

## Bilans antérieurs

- [Premier essai Linux avec Docker, 17 novembre](../2026-11-17-installation-neuve-bazzite.md)
- [Transfert physique entre SSD, 18 novembre](../2026-11-18-transfert-ssd-bazzite.md)
- [Réinstallation, indexation et YouTube, 20 novembre](../2026-11-20-reinstallation-bazzite.md)
- [Premières restaurations autonomes sur Debian 13, 20 novembre](../2026-11-20-restauration-linux-hors-ligne.md)

## Critères d'acceptation

Une installation neuve démarre sur un système pris en charge sans Docker ni
Compose. Le lanceur prépare les outils, installe le logiciel et redémarre après
reboot. La recette vérifie la recherche, la lecture des contenus attendus et les
fichiers d'outils destinés à la copie. Une interruption peut être reprise avec
la même sélection, et une sélection modifiée est refusée.

La copie se prépare sur un autre espace de stockage. Un fichier partiel peut
être repris et vérifié. Sur l'invité de restauration, les outils viennent de
la copie, le démon démarre vide, le chemin source n'existe pas et Internet
est rendu inaccessible. Après démontage du support et redémarrage, les services
et le contenu annoncé restent disponibles. Une vérification documentaire
couvre un PDF, un article ZIM, une carte et une vidéo avec sous-titres.

La restitution réserve l'inférence, les pilotes GPU, les autres architectures
et le démarrage depuis un disque sans système aux scénarios qui les ont
effectivement vérifiés. Les rapports publics écartent les comptes, historiques,
clés, secrets et journaux techniques privés.
