# Reprise de restauration privée après interruption

**Bilan daté — 22 novembre 2026, SetupSurvie 0.96.0.** Le lanceur propose la
reprise après une interruption. Cette évolution ajoute un journal de
restauration et réutilise la destination après contrôle du kit et de la
sauvegarde.

Le test automatisé arrête de force un processus jetable après l’écriture
d’un fichier partiel, puis relance la restauration. Le fichier partiel est
recopié et la base SQLite déjà vérifiée est conservée. Le deuxième arrêt suit
une écriture simulée des services. La reprise relance le même projet et
conserve cette modification. Les deux cas vérifient que la sauvegarde reste
intacte et que la réussite est enregistrée après les contrôles. Le test du
lanceur simule le choix de reprendre dans la même destination.

Voir la [procédure de restauration](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système).
Les tests utilisent des données fictives et des services simulés. La recette
R09 avec Docker, coupure électrique réelle et SSD physique reste à effectuer.
