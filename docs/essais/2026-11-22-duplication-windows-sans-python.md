# Duplication du kit sur Windows sans Python

**Bilan du 22 novembre 2026 — SetupSurvie 0.104.0.** Le lanceur propose
d’installer Python avec Tcl/Tk pour le compte courant si nécessaire. Il
utilise l’installateur vérifié du kit. La version mineure ajoute ce parcours
sans modifier le format des kits.

Les essais PowerShell simulent l’exécution de l’installateur. Ils vérifient
les options de Python, l’absence d’appel réseau et le refus d’un catalogue
ou d’un installateur modifié avant exécution. La confirmation et
l’installation de Python avec son vrai exécutable restent à essayer sur un
Windows neuf sans réseau. Suivre la
[procédure de préparation](../installation/preparer-kit-hors-ligne.md).
