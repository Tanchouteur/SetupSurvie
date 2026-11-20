# Reproduire la campagne

1. Préparer des machines ou VM jetables avec un disque de travail distinct
   du support de copie. Relever l'image de distribution, son empreinte, le
   noyau, la mémoire, le stockage, le commit SetupSurvie et les outils déjà
   installés. Masquer le Python du système seulement sur une cible jetable et
   rétablir la commande après le test.
2. Sur une image propre, lancer l'[installation automatique](../../installation/README.md#installation-automatique-linux)
   avec une sélection figée. Relever les outils réellement utilisés et les
   fichiers téléchargés. Couper le seul processus d'installation pendant une
   écriture, conserver le partiel puis relancer la même commande. Vérifier que
   la modification des lots est refusée sans remplacer les données.
3. Vérifier l'apparition des collections et documents dans la recherche. Ouvrir
   un PDF et un article. Si une liste YouTube de recette est prévue, attendre
   la publication des pistes, puis rechercher un passage par son texte.
4. Produire la copie sur le second disque avec le [guide de transfert](../../exploitation/transfert-installation.md).
   Pendant la campagne de panne, interrompre la copie et relever la taille
   d'un fichier partiel. Relancer, puis contrôler le manifeste et les empreintes.
5. Mettre la copie à disposition de la VM cible. Utiliser un disque vierge de
   SetupSurvie. Le chemin de la source doit être absent dans la VM. Établir
   l'absence de sortie Internet par un témoin TCP et vérifier que l'hôte reste
   accessible. Détacher le support avant le lancement.
6. Restaurer avec le [lanceur de la copie](../../exploitation/transfert-installation.md#restaurer-sur-une-autre-machine-linux-hors-ligne).
   Contrôler les binaires employés, la présence des fichiers Docker et
   l'import des images. Après le démarrage, contrôler santé, recherche et
   lecture. Rejouer la même commande, puis redémarrer la VM et recommencer
   les contrôles sans reconnecter le support.
7. Conserver les résultats anonymisés avec le code de retour, la version, la
   date, les empreintes et le statut. Garder les journaux bruts et les données
   privées hors du dépôt.
