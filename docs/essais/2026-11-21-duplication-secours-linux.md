# Duplication d’un SSD de secours depuis un autre

**Bilan du 21 novembre 2026 — 0.78.0.** Le lanceur **Dupliquer le SSD de
secours** crée sur un deuxième disque une copie vérifiée, qui contient à son
tour les lanceurs d’installation et de duplication. Le logiciel et les données
transportés gardent la version et l’inventaire du premier support.

L’entrée administrateur a été essayée sur trois systèmes de fichiers distincts
en mémoire, dans un conteneur Debian 12 sans réseau ni socket Docker. Le support
fictif comptait 482 fichiers, dont une base SQLite, un document et les fichiers
du logiciel. La copie sur le volume d’origine a été refusée. La chaîne A → B → C
a réussi alors que le chemin du support A était devenu indisponible. Les
manifestes sont identiques et les réglages privés sont restés protégés sur C.

Les tests ciblés injectent une interruption au milieu d’un fichier, remontent
le support à un autre emplacement et contrôlent la reprise au même dossier.
Ils vérifient aussi le refus d’un fichier corrompu et la préservation d’un
dossier existant. Le test du bootstrap extrait uniquement Python alors que les
installateurs Docker sont absents.

Cette recette ne fait pas démarrer les images d’une copie réelle et ne couvre
pas le montage des SSD physiques, le double-clic et la fenêtre d’autorisation
du bureau cible. Voir le
[guide de duplication](../exploitation/transfert-installation.md#dupliquer-le-ssd-de-secours).
