# Installation du kit public par double-clic sous Linux

**Bilan daté — 22 novembre 2026, SetupSurvie 0.99.0.** Cette évolution
ajoute un lanceur graphique Linux au kit public. Le lanceur choisit un
nouveau dossier sur le disque sélectionné, installe en mode CPU et ouvre
le site après vérification des services. L’IA reste en pause au premier
démarrage.

Les essais contrôlent la sélection du disque et le mode CPU, l’ouverture
des ressources copiées et l’indépendance du lanceur installé après retrait
du kit de son chemin. Les services sont simulés dans ces essais. Sur Debian 12, le lanceur a
passé `desktop-file-validate`. Gio a transmis le chemin du kit, qui
contenait des espaces, à un script témoin.

Voir [l’installation depuis le kit](../installation/pilote-marc.md#installer-à-partir-du-kit).
La préparation de Python, Tkinter et Docker reste préalable pour ce parcours.
La recette avec Docker et un disque physique sans réseau reste à faire.
