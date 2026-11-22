# Duplication du kit sur Linux sans Python

**Bilan du 22 novembre 2026 — SetupSurvie 0.105.0.** La version mineure ajoute
au lanceur Linux un parcours avec Zenity et le Python du kit. Il extrait
Python dans un dossier temporaire, sans installer Docker ni modifier le
système. Les contrôles, la reprise de la copie et l’inventaire restent ceux
de la duplication du kit public.

Un conteneur Debian 12 sans réseau et sans Python ni Docker au départ a
exécuté ce chemin sous un compte sans droits administrateur. La sélection
du dossier et les fenêtres Zenity étaient simulées. Le vrai Python fourni
par le kit a dupliqué le manifeste, les ressources d’exemple et les vrais
installateurs Linux. La recette a comparé le manifeste et l’archive Python
entre les deux dossiers et vérifié le retrait des outils temporaires.
Le double-clic depuis un bureau physique et la copie vers un second SSD
restent à essayer. Voir [Préparer et vérifier le kit hors ligne](../installation/preparer-kit-hors-ligne.md#dupliquer-un-kit-public).
