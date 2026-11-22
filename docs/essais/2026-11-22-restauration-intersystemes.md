# Restauration des données personnelles entre Windows et Linux

**Bilan daté — 22 novembre 2026, SetupSurvie 0.94.0.** La version mineure
ajoute un parcours de restauration avec un kit public complet de même version.
Les anciennes sauvegardes restent utilisables sur leur système d’origine.

Les tests automatisés simulent les deux systèmes et les services. Ils vérifient
la lecture d’une ligne SQLite après copie, le maintien du secret d’installation,
la priorité d’un guide personnel homonyme, les empreintes de la sauvegarde,
la pause du moteur et l’adaptation des réglages de la machine. Les tests
injectent un fichier corrompu sur la destination et vérifient que le démarrage
n’a pas lieu. Ils contrôlent aussi le refus avant écriture en cas de système,
d’espace, de version d’Open WebUI ou de noms incompatibles.

La [procédure](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système)
utilise la ligne de commande sur une machine préparée. L’intégration dans le
lanceur graphique et les recettes R03/R04 sur deux systèmes avec Docker et SSD
réels restent à faire. Il reste aussi à rejouer les pannes et redémarrages
du [protocole de secours](../exploitation/disque-de-secours-hors-ligne.md#10-recette-dacceptation).
