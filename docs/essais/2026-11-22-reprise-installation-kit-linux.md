# Reprise de l’installation du kit public Linux

**Bilan daté — 22 novembre 2026, SetupSurvie 0.101.0.** La version mineure
permet de poursuivre l’installation depuis le même kit et le même disque.
Le lanceur choisit le dossier SetupSurvie-Kit et vérifie le journal avant
d’y écrire.

Deux arrêts brutaux d’un processus jetable couvrent la copie et
l’activation simulée. Dans le premier cas, le fichier partiel est
recopié et les réglages existants sont conservés. Dans le deuxième cas,
la reprise vérifie les services du même projet et conserve le fichier
modifié après leur démarrage. Dans les deux cas, le kit initial reste
intact et un manifeste différent est refusé.

Sur Debian 12 sans réseau, le script administrateur a extrait les vrais
outils Linux depuis le kit. Une seconde exécution a réutilisé ce dossier
puis un manifeste modifié a été refusé. Le démarrage du moteur était simulé.

Voir le [parcours documenté](../installation/pilote-marc.md#installer-à-partir-du-kit).
Le test d’ensemble avec un moteur réel, un SSD et une machine redémarrée
sans réseau reste à effectuer.
