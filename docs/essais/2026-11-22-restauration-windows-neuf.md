# Préparation Windows depuis le lanceur de restauration

**Bilan du 22 novembre 2026 — SetupSurvie 0.106.0.** La version mineure
permet au lanceur **Restaurer mes données SetupSurvie** de préparer les
outils manquants sur un PC Windows avec les installateurs du SSD. Un
redémarrage demandé par Windows interrompt la préparation. Le même
lanceur reprend ensuite la procédure.

Les essais PowerShell simulent la préparation, le démarrage de Docker
et la détection de Python. Ils vérifient leur ordre, le cas où Python
seul doit être installé, l’annulation avant préparation et le message
de reprise après une demande de redémarrage. Le test n’exécute aucun
installateur Windows réel. La recette de bout en bout sur Windows 11
neuf avec SSD et réseau coupé reste à effectuer. Voir [le guide de
restauration](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système).
