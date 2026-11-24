# Installation Linux et point de restauration immuable

**Bilan de recette du 21 novembre 2026 — candidat 0.77.0.** Deux invités Debian
13.7 x86-64 sous KVM sur Bazzite, avec ext4 et systemd. L’accès sortant était
bloqué dès le démarrage. Bazzite a servi d’hôte. Aucun changement de sa version,
de l’installation en service ou des réglages d’IA.

## Installation avec le point activé et remise en service

La première VM disposait de 6 Gio de mémoire et d’un disque de 110 Gio. Elle a
lu une copie 0.72.0 vérifiée en lecture seule. Le nouvel assistant a recopié
1 341 fichiers, installé ses outils hors ligne et préparé le point local puis
une copie active. Le portail et le catalogue Kiwix ont répondu.

- Sur ext4 dans la VM, une écriture avec l’UID 0 dans le manifeste du point a
  été refusée. Sur le SSD Btrfs de l’hôte, un point de test a refusé l’écriture
  et le renommage par root tant que l’attribut immuable était actif.
- La recette a arrêté SetupSurvie, déplacé son script de démarrage pour simuler
  une panne, et démonté le support. Le lanceur d’entretien déjà installé a
  remis en service une nouvelle copie. L’inode du dossier actif a changé.
- Le manifeste du point a conservé son SHA-256. Un fichier créé après le point
  est resté dans l’ancienne installation mise à l’abri. Le portail et Kiwix ont
  de nouveau répondu après un redémarrage de la VM, support toujours démonté.

Le premier démarrage a révélé que l’installateur des services détectait le
`nft` des outils d’entretien au lieu de vérifier sa présence sur le système.
Le démarrage a abouti après isolation de ces chemins et reprise de la copie
existante. Un test unitaire couvre ce cas.

## Ajout du point sur une installation déjà en service

La deuxième VM disposait de 5 Gio de mémoire et d’un disque de 76 Gio. Le
support de recette combinait le logiciel 0.77.0 et les images et données
compatibles d’une copie antérieure, avec 5,74 Go de fichiers inventoriés
hors archive Docker et un fonds réduit sans LLM. L’installation avec l’option
décochée a démarré et n’a créé aucun point. Après démontage du support,
**Créer un point de restauration** a copié l’installation locale, exporté ses
images, scellé le point et redémarré la même installation 0.77.0.

Une seconde panne injectée a rendu le script de démarrage inutilisable.
Le point créé après l’installation a permis de repartir d’une nouvelle
copie 0.77.0 sans SSD externe. Le portail a annoncé un état sain et Kiwix
a rendu son catalogue. Le manifeste du point a gardé la même empreinte.
Le fichier ajouté après sa création a été retrouvé dans l’installation
précédente mise à l’abri.

La reprise de cette installation a aussi vérifié la correction d’un dossier
logiciel exporté avec droit d’écriture de groupe. La nouvelle copie retire
ce droit avant de démarrer le service système. Le support conserve ses droits
d’origine.

## Interface et limites

Le fichier de lancement a passé `desktop-file-validate` sur Bazzite et
`gio launch` a transmis le bon emplacement, dont le nom contenait des
espaces. Les tests Python et shell simulent le choix du disque, la désactivation
du point, la progression et le passage à l’autorisation graphique. La recette
en VM a appelé le moteur privilégié directement. La fenêtre PolicyKit et le
parcours sans aide restent à essayer sur le bureau Linux retenu. La recette
complète du nouveau parcours n’a porté ni sur Debian 12 ni sur Ubuntu 22.04.
Aucun tag de référence de restauration n’est attribué par ce bilan.
