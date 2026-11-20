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
| Installation en ligne et reprise de téléchargement | Debian 13.7, version de travail 0.72.0 | Arrêt forcé au milieu de Wikilivres, reprise du fichier partiel et refus d'une sélection de lots différente. Première installation terminée et services actifs après redémarrage. |
| Installation en ligne sur images minimales | Debian 12.15 et Ubuntu 22.04.5 LTS, 0.72.0 | Installation sans Docker, nftables ni commande Python système. Contrôles intégrés, rejeu du lanceur et changement d'identifiant de démarrage vérifiés. Portail, Open WebUI, recherche, PDF, carte et collection Wikilivres disponibles après redémarrage. |
| Restauration complète du transfert 0.72.0 | Debian 13.7, Debian 12.15 et Ubuntu 22.04.5 LTS, trois VM vierges et isolées | Copie de 24,6 Go et 1 341 fichiers inventoriés, images Docker importées, outils YouTube contrôlés. Support démonté et sortie WAN bloquée avant lancement. Rejeu et redémarrage réussis. Portail, contrôleur, Open WebUI, PDF, PMTiles et recherche puis lecture dans Wikilivres vérifiés. |
