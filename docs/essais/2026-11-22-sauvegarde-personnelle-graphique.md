# Sauvegarde personnelle depuis l’assistant

**Bilan du 22 novembre 2026 — SetupSurvie 0.109.0.** La version mineure
ajoute un bouton de sauvegarde personnelle dans l’assistant de transfert
et le menu d’entretien Linux. Le bouton crée une sauvegarde séparée que
le lanceur de restauration peut retrouver sur le SSD.

Les tests contrôlent la transmission de la destination et le refus
de sauvegarder pendant une mise à jour ou un transfert. Le test du menu
Linux simule Zenity et la demande d’administration. Les tests de sauvegarde
écrivent des fichiers de test avec des services simulés. Le choix d’un SSD
physique et la sauvegarde d’une installation réelle restent à essayer.
Voir [le guide de sauvegarde](../installation/pilote-marc.md#sauvegarder-et-restaurer).
