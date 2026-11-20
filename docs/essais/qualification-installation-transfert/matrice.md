# Matrice des essais

Les résultats sont associés à une version, à l'état du système de départ et
au dispositif d'essai. Les contrôles de portabilité des outils ne qualifient
pas une installation complète.

| Scénario | Configuration et version | Éléments observés |
| --- | --- | --- |
| Bazzite, installation après nettoyage | Bazzite x86-64, RTX 2060, Docker rootless dédié | 0.69.6 et 0.70.0. Reprise après interruption des images et d'une archive. Recherche, PDF et Kiwix. [Bilan](../2026-11-20-reinstallation-bazzite.md) |
| YouTube de la première installation | Bazzite 0.69.6 et 0.70.0, films Blender | Soumission automatique, téléchargement, transcription, traduction, lecture et recherche dans les pistes. Rejeu avec doublon, liste refusée et vidéo indisponible. |
| Transfert du fonds réel et reprise | Crucial 4 To vers Samsung 1 To, Bazzite 0.70.0 | Arrêt forcé avec 100 663 296 octets déjà écrits. Reprise et contrôle de 1 359 fichiers. Deuxième copie avec iFixit. [Bilan](../2026-11-20-restauration-linux-hors-ligne.md) |
| Restauration automatique hors ligne | VM Debian 13.7 x86-64 sur le Samsung, 0.71.0 | 3 862 fichiers. Outils de la copie, Docker neuf, support démonté, WAN inaccessible. Portail, contrôleur, lecture et reboot validés. |
| Anciens systèmes, outils hors ligne | Debian 12.15 et Ubuntu 22.04.5 LTS minimales, 0.72.0 | Aucun Docker ni nftables global. Outils vérifiés depuis la copie, import d'une image BusyBox locale et réponse HTTP d'un conteneur. Sortie WAN indisponible. |
