# Retour à l’installation après un point interrompu

**Bilan du 21 novembre 2026 — 0.80.0.** Dans le menu **Entretien de SetupSurvie**,
**Revenir à mon installation** met la copie incomplète de côté et redémarre
l’installation active, avec ses données actuelles.

- Une régression simule une coupure entre le déplacement de la copie et le
  retrait du verrou. Le deuxième lancement retrouve le même journal, enlève
  le verrou et demande le redémarrage. Le fichier partiel et le document
  récent sont conservés.
- Un point déjà copié reste en place. Un verrou d’un autre transfert et une
  restauration en cours empêchent la bascule. Si un journal de point est
  illisible et qu’aucun verrou ne protège la source, l’installation peut
  redémarrer et le journal est conservé.
- Dans un conteneur Debian 12 sans accès à Internet ni socket Docker, l’entrée
  administrateur d’un SSD récent a exécuté deux fois l’opération avec un
  ancien programme d’entretien épinglé. Le faux service système a démarré
  un serveur HTTP local et le lanceur a reçu la réponse de santé attendue.
  La copie partielle et les données actuelles ont été vérifiées sur disque.

La fenêtre Zenity et le redémarrage système ont été simulés. Rejouer le
[parcours du bureau](../exploitation/transfert-installation.md#revenir-à-mon-installation-après-une-copie-interrompue)
sur le PC Linux de référence avec une vraie coupure.
