# Libérer de la place pour une restauration Linux

**Bilan du 23 novembre 2026, SetupSurvie 0.113.0.** Cette version mineure
ajoute une action à l’assistant d’entretien Linux. Elle redonne un moyen de
continuer lorsqu’une nouvelle copie du point protégé dépasserait l’espace
disponible sur le disque. Le détail figure dans le [guide du
transfert](../exploitation/transfert-installation.md#utiliser-le-point-de-restauration-linux).

Les tests automatisés vérifient le message de manque d’espace, la sélection
et la confirmation explicite dans le lanceur, la reprise d’une suppression
interrompue et le refus d’un volume monté dans une ancienne copie. Ils
vérifient que la copie réservée à une restauration en cours reste disponible
et que les autres copies sélectionnées peuvent être supprimées.

L’interface Zenity a été simulée. Les tailles sont des estimations des blocs
occupés et l’espace libéré affiché est la variation mesurée sur le volume.
La recette sur un vrai bureau et un volume presque plein reste à effectuer.
