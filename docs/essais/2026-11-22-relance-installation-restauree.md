# Relance locale d’une installation restaurée

**Bilan daté — 22 novembre 2026, SetupSurvie 0.97.0.** La version mineure
ajoute un lanceur **Ouvrir SetupSurvie** dans le dossier de destination,
après vérification de la restauration.

Le test déplace le kit et la sauvegarde hors de leurs chemins d’origine et
relance depuis le dossier restauré. Il vérifie le projet, le chemin des
données et la pause de l’IA. Il simule le démarrage et les contrôles Docker.
Le test de fenêtre vérifie l’appel du lanceur installé sans sélection du kit.
Sur Debian 12, le lanceur Desktop Entry a passé le validateur et Gio a
transmis le dossier installé, situé dans un chemin accentué avec espace,
à un script témoin. Une restauration interrompue doit d’abord être terminée
depuis le SSD.

Voir la [procédure](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système).
La recette R15 sur un vrai système redémarré, avec le support retiré et le
réseau coupé, reste à effectuer.
