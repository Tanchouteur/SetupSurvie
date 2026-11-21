# Préparation locale du kit Windows

**Bilan du 21 novembre 2026 — 0.81.0.** Le lanceur sélectionne le kit avant
la préparation du PC. Depuis le dossier du kit, il le détecte au double-clic.
La reprise reprend l’emplacement consigné dans le journal d’installation.

Les tests PowerShell simulent les appels système. Ils vérifient que le kit
sélectionné est transmis aux deux étapes, qu’une dépendance absente arrête le
parcours avant DISM ou MSI, et que DISM est demandé avec la restriction aux
sources locales. Le MSI est lu sur le support. Deux redémarrages simulés
couvrent l’activation de la fonctionnalité Windows puis l’installation de
WSL. Les tests couvrent aussi l’absence de pilote NVIDIA et la préparation
du support sans exécuter d’installateur.

Le MSI x64 WSL 3.0.5 et son empreinte ont été vérifiés dans les métadonnées
officielles. Les paquets restent hors de Git. Les simulations n’installent
aucun composant système. La recette complète sur Windows 11 24H2 x64 ou
ultérieur, sans Internet, avec Docker Desktop et les données d’un vrai kit,
reste à faire. Voir la [procédure](../installation/deux-etapes-windows.md#préparer-un-kit-pour-windows-sans-internet)
et la [publication de Microsoft](https://github.com/microsoft/WSL/releases/tag/3.0.5).
