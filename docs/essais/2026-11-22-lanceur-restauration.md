# Lanceur de restauration des données personnelles

**Bilan daté — 22 novembre 2026, SetupSurvie 0.95.0.** La version mineure
emballe deux lanceurs de restauration avec le kit public. Ils demandent de
choisir la sauvegarde et le disque cible, affichent l’étape en cours et
proposent d’ouvrir le site après la vérification du démarrage.

Les essais automatisés contrôlent le choix d’un nouveau dossier sur le disque
sélectionné, l’appel au moteur de restauration et les quatre combinaisons
Windows/Linux avec services simulés. Les deux fichiers de lancement sont
autorisés par l’audit du kit. Le script shell a passé son contrôle de
syntaxe et le script Windows a été relu par l’analyseur PowerShell.

Le [guide](../installation/pilote-marc.md#restaurer-les-données-personnelles-sur-lautre-système)
précise les prérequis. L’ouverture en session graphique sur un PC neuf, la
préparation des prérequis depuis le support et les essais Docker réels sans
réseau restent à qualifier.
