# Installateur Windows simplifié — 12 novembre 2026

**Bilan daté — pilote 0.1.20, basé sur 0.1.19 (`6cee086`).** Essais sur le PC Windows de Marc,
RTX 5060 Ti 8 Go. Le code a été récupéré et corrigé dans une copie de travail
séparée ; l’installation 0.1.16 et son téléchargement documentaire restent en service.

## Comportement livré

`Installer-SetupSurvie.cmd` enchaîne la préparation du PC et l’installation.
Le code de redémarrage 3010 est conservé et arrête le parcours avant la seconde
étape. Une erreur d’une étape est transmise au lanceur ; `-Check` ne lance jamais
l’installation. Les anciens lanceurs restent utilisables.

Les chemins du processus, de l’utilisateur et de Windows sont regroupés sans
perdre les outils portables. Docker Desktop est recherché aux emplacements
usuels, à côté du client Docker ou parmi les processus Desktop déjà ouverts.
Un moteur Docker déjà accessible évite une réinstallation inutile. Le démarrage
par raccourci réutilise les mêmes fonctions de détection et vérifie le mode Linux.

Le choix du dossier propose une valeur par défaut, modifiable. Avant la copie,
l’audit du kit et les téléchargements, le parcours vérifie les ports communs.
Une installation existante entraîne un message permettant de l’ouvrir ou de
suivre sa procédure de mise à jour, sans arrêter de service. La reprise reconnaît
ses ports publiés par Compose et vérifie l’identité de ses processus natifs.

Les raccourcis d’une autre installation sont conservés. Un suffixe propre aux
réglages est utilisé si le nom est déjà pris. Désactiver le démarrage de la seconde
installation conserve celui de la première.

Le lanceur unique est inclus dans les copies applicatives, exports et
rafraîchissements de kits, et accepté par leur audit. Les trois fichiers racine
`.cmd` restent exclus des paquets de mise à jour pour conserver la compatibilité
avec le lecteur 0.1.16. Les scripts d’installation sont inclus dans ces paquets.

## Vérifications

- Analyse et scénarios PowerShell 5.1 : réussis. Détection de Docker portable,
  conservation du PATH du processus, moteur accessible sans Desktop standard,
  préparations interrompues, redémarrage, diagnostic seul et transmission des options.
- `Installer-SetupSurvie.cmd -Check` réel : code 0. Python, Docker et Ollama
  présents sont conservés ; la RTX 5060 Ti est identifiée sans charger de modèle.
  Le même diagnostic en 0.1.18 échouait à tort avec « docker manque ».
- Lanceur réel avec une destination d’essai et la 0.1.16 active : conflit des
  ports signalé, code 1 attendu, destination non créée, aucun téléchargement
  ou démarrage applicatif supplémentaire.
- Raccourcis COM réellement créés dans des dossiers temporaires : création,
  démarrage, arrêt, désactivation et préservation des raccourcis d’une autre
  installation vérifiés. Aucun accès au Bureau ou au démarrage utilisateur réel.
- Tests de reprise et de copie de l’assistant d’installation : sources/options
  modifiées, données occupées, place insuffisante, verrou concurrent et processus
  natif périmé refusés ; ports propres à l’installation repris.
- Copie réelle de 239 fichiers avec contrôle SHA-256, initialisation du logiciel
  copié et reprise avec conservation des réglages et d’un document ajouté : réussies.
  Pour ce contrôle de copie uniquement, les ports sont simulés libres ; l’exécution
  s’arrête volontairement avant l’installation des services. Le diagnostic Docker/Compose est réel.
- Suite applicative Windows hors quatre modules du laboratoire Linux : **190 tests,
  184 réussites et 6 ignorés**, aucune erreur ni assertion en échec, en environ 76 secondes.
  Les deux tests COM des raccourcis sont inclus. Les comparaisons de chemins sont normalisées ;
  les permissions POSIX restent vérifiées sur POSIX et la lecture sur Windows.
  Les tests de liens symboliques sans privilège Windows sont explicitement ignorés.

La suite finale a tourné hors sandbox, avec tous les temporaires dirigés vers le
dossier d’essai. Un essai précédent dans la sandbox avait subi une coupure de
connexion HTTP locale Windows ; les six tests du contrôleur puis la suite entière
ont été vérifiés hors sandbox sans modification du contrôleur applicatif.

Les essais n’utilisent que des données temporaires et des services simulés, sauf
les diagnostics explicitement indiqués comme réels. Les temporaires et journaux
restent dans le dossier d’essai local, hors dépôt partagé.

## Limites

L’installation de prérequis manquants sur un Windows vierge, les redémarrages
réels, la recette complète d’un kit et le démarrage d’une nouvelle instance
0.1.20 n’ont pas été exécutés. Le PC héberge déjà la 0.1.16 ; la nouvelle protection
empêche justement de lancer une seconde instance sur ses ports. Les tests ne
valident pas le LAN sur téléphone, la confiance HTTPS ou l’autonomie hors ligne.

La procédure courante est le [guide Windows](../installation/deux-etapes-windows.md).
