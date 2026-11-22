# Point protégé lors de l’installation du kit public Linux

**Bilan daté — 22 novembre 2026, SetupSurvie 0.102.0.** Le parcours système
qui installe Python et Docker depuis le SSD propose le point protégé par
défaut. Il conserve les installateurs pour lancer l’entretien sans le
SSD, y compris lorsqu’on choisit de créer le point plus tard.

Les tests simulent l’autorisation graphique, les services et la copie
de maintenance. Ils vérifient le choix de créer ou de différer le point
et une reprise qui passe directement par l’entretien après un échec.
Sur Debian 12 sans réseau, le script a extrait les outils du kit et
conservé le choix lors d’une relance, avec un démarrage simulé.
Le stockage du point et le retour dans une nouvelle copie réutilisent
le parcours Linux déjà éprouvé sur une copie de secours, documenté
dans le [bilan 0.77.0](2026-11-21-installation-point-restauration-linux.md).

Le test d’ensemble de ce nouveau raccordement sur une cible neuve,
avec moteur et SSD réels puis redémarrage hors ligne, reste à effectuer.
Le chemin du kit sur une machine déjà préparée avec Docker conserve
son lanceur utilisateur.
