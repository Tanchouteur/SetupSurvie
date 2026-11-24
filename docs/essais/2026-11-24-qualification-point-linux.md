# Recette du point de restauration Linux

**Bilan du 24 novembre 2026 — SetupSurvie 0.115.1, Debian 12 x86-64.**

## Correctifs issus de la recette

Sur la 0.115.0, le catalogue Kiwix était vide malgré une archive ZIM
installée. Le lanceur administrateur copiait l’archive en mode `0600`
dans un dossier `0700`, inaccessible au compte non privilégié de Kiwix.
Un premier kit préparé avec des permissions restrictives avait aussi
révélé un défaut de lecture du script Kiwix. La copie donne désormais
au conteneur les droits de lecture nécessaires, y compris à la reprise
d’une copie interrompue.

Le premier montage de la 0.115.1 a révélé un second défaut. Les services
démarraient, puis la création du point échouait avec le code 126 lorsque
les fichiers du kit n’avaient pas conservé leur droit d’exécution.
La copie rétablit maintenant ce droit sur les trois scripts appelés
directement pendant l’entretien ou la restauration. La 0.115.1 est une
correction compatible. [PR 131](https://github.com/Tanchouteur/SetupSurvie/pull/131)

## Matériel et support de recette

Deux VM KVM sur Bazzite, Debian 12 x86-64, noyau `6.1.0-56-amd64`, 3 vCPU,
6 Gio de RAM, disque système ext4 de 150 Gio. Les cibles démarrent sans
SetupSurvie ni Docker, avec Python 3.11.2 fourni par Debian, sans route
Internet et avec un réseau QEMU restreint. Le kit est monté en lecture
seule sur un disque virtuel distinct. La recette appelle le moteur
administrateur utilisé par le lanceur graphique.

Le kit réduit a 1 281 fichiers listés, dont un guide, un ZIM, les images
Docker et les prérequis locaux. Ses 1 232 fichiers applicatifs ont été
comparés au commit `ea29f5c5f6ae10aabe3c9f72a79e1286a074512c`. Le seul
écart de contenu est la configuration des profils, réduite au modèle
déjà présent dans le kit. Le SHA‑256 du manifeste est
`a602837922945ca243cf33da0ac6ddef4b2274017a73cbf9555f890154e1abe0`.

## Résultats

Le premier essai a repris la création du point après application du
correctif à la copie jetable. Le second a installé le kit final dès
le départ sur une autre VM vierge. Les deux essais ont vérifié les étapes
suivantes.

| Étape | Résultat |
| --- | --- |
| Installation et création du point | Outils installés depuis le kit. Portail, Kiwix et Open WebUI disponibles. Le point reçoit l’attribut immuable et refuse une écriture, même par root. |
| Simulation d’une panne | Après ajout d’un guide et d’une conversation témoins, le script de démarrage est déplacé. Le service échoue au démarrage et le portail devient inaccessible. |
| Restauration interrompue | VM démarrée sans le support. Arrêt forcé du processus avant la bascule. L’installation de travail est encore présente et les empreintes du point restent intactes. |
| Reprise et redémarrage | Retour au point, puis redémarrage sans le support. Portail, Kiwix et Open WebUI répondent en HTTP 200. Un guide est trouvé et lu, et le ZIM s’ouvre. L’IA reste en pause. |
| Vérification des données | Le témoin, le guide et la conversation postérieurs au point sont retrouvés dans l’ancienne installation archivée. La base réussit `PRAGMA quick_check`. |

Les 30 tests de livraison et les 22 tests de restauration Linux passent
sur le runner. La suite locale de la 0.115.0 avait échoué sur la marge
de stockage requise pour les tests de mise à jour. Les 28 tests de ce
module sont repassés dans la VM avec la marge nécessaire. La CI du
correctif a réussi ses 11 tâches, dont 1 411 tests Python avec
7 ignorés sur Linux. Les empreintes des deux paquets ont été vérifiées,
puis les 1 221 fichiers du paquet de mise à jour ont été relus.
[CI de la PR 131](https://github.com/Tanchouteur/SetupSurvie/actions/runs/45417923847)

## Référence conservée

Le tag désigne `d883c704fa3c7cdbc4cc940b19219f28ef9fd3c8` sur `main`.
L’arbre Git est identique à celui du commit qui a servi à construire le
kit final. [Tag restauration-debian12-vm-0.115.1](https://github.com/Tanchouteur/SetupSurvie/tree/restauration-debian12-vm-0.115.1)

| Fichier du point final | SHA‑256 avant et après restauration |
| --- | --- |
| `transfer.json` | `b18443d9c2790c73e0365d5e61dc6ded05133c3e7dedb7b6d197dd4cb2b40ae8` |
| `point-de-restauration.json` | `2f8ae2994164f0ee7969d5cda5ba3a7fe7169be70ba6c9a37b61c0860c40f1e7` |

Sur Bazzite, le dossier `/var/mnt/data/AI/SetupSurvie-qualification-01151-finale`
conserve le kit `vm/kit.img` et le disque de la VM `vm/debian12.qcow2` dans
lequel se trouve le point protégé.

## Limites

La qualification couvre une VM Debian 12, un support virtuel et un fonds
réduit. Un SSD physique séparé, le parcours graphique suivi par un proche,
l’accès depuis le réseau local réel et le fonds complet restent à essayer.
Windows physique, les transferts entre systèmes et l’inférence réelle
ont leurs propres recettes.
