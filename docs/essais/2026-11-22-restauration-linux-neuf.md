# Restauration depuis le kit sur Linux sans Python ni Docker

**Bilan du 22 novembre 2026 — SetupSurvie 0.107.0.** La version mineure
raccorde la restauration de sauvegarde privée au moteur Linux dédié
du kit. Le chemin graphique sélectionne la sauvegarde et le disque
puis demande l’autorisation administrateur.

Les tests simulent la fenêtre, le moteur Docker et systemd. Ils
vérifient la reprise sur la copie et la relance depuis l’installation.
Dans Debian 12 sans réseau, les vrais installateurs du kit ont extrait
les outils et le script administrateur a transmis la sauvegarde choisie
au programme de restauration simulé. Une deuxième exécution réutilise
les outils extraits et un manifeste de sauvegarde modifié est refusé.

La recette avec les services réels, SSD retiré après restauration puis
redémarrage, reste à exécuter. Voir le
[guide de restauration](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système).
