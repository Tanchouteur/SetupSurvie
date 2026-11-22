# Restauration avec un kit plus récent

**Bilan du 22 novembre 2026 — SetupSurvie 0.108.0.** La version mineure
permet de restaurer une sauvegarde créée par une version antérieure de
SetupSurvie lorsque le format des données et l’image Open WebUI sont
identiques. Le kit doit être de même version ou plus récent.

Le test recrée la destination à partir d’une sauvegarde au format de
la 0.94.0 et d’un kit plus récent. Il relit la conversation SQLite
et un guide personnel après la copie. Un kit trop ancien et un format
différent sont refusés avant la création de la destination. Les services
et le contrôle des dépendances du kit sont simulés. La recette de
bout en bout avec des modèles et des images réels reste à faire.
Voir [le guide de restauration](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système).
