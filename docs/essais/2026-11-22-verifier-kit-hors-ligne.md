# Contrôle graphique du kit hors ligne

**Bilan du 22 novembre 2026 — SetupSurvie 0.111.0.** La version mineure
ajoute un lanceur de contrôle graphique pour les fichiers du kit et les
installateurs présents. Le résultat distingue les systèmes avec et sans
installateurs embarqués.

Les tests lisent un kit de test, vérifient que le contrôle ne modifie pas
la source et refusent un fichier altéré sans changement de taille. Un
conteneur Debian 12 sans réseau ni Python système a exécuté le contrôle avec
le Python embarqué. Les vrais installateurs Linux étaient présents et
l’absence d’installateurs Windows a été signalée. Zenity était simulé. Le
double-clic sur les deux systèmes et l’essai d’installation complète
restent à qualifier. Voir la
[procédure](../installation/preparer-kit-hors-ligne.md#vérifier-le-ssd-avant-de-partir).
