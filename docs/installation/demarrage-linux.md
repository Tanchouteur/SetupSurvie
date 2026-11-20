# Démarrage automatique sous Linux et Docker rootless

**Guide de référence pour une installation Linux avec Docker.** Revenir au
[parcours d’installation](README.md#préparer-une-installation-depuis-le-dépôt)
pour les prérequis et la commande.

Premier essai d’installation Linux de zéro sur Bazzite le 17 novembre 2026 ;
voir le [bilan](../essais/2026-11-17-installation-neuve-bazzite.md).

- **Démarrage avec le PC.** Sous Linux, l’installation crée et démarre le
  service utilisateur systemd `setupsurvie-<projet>.service`
  (`~/.config/systemd/user/`). Il lance `survie.sh up` au démarrage : services
  Web, contrôleur local, annonce `survie.local` et indexation automatique. Ces
  processus ne dépendent plus du terminal de l’installation. Le service réessaie
  après 15 secondes si Docker n’est pas encore prêt. Les chemins comportant
  des espaces sont conservés. Sans session
  ouverte, il faut le « linger » de l’utilisateur : l’installation l’active si
  le système le permet, sinon elle affiche `sudo loginctl enable-linger UTILISATEUR`.
  `--no-startup` n’installe pas ce service. Le retirer :
  `systemctl --user disable --now setupsurvie-<projet>.service`, puis supprimer
  le fichier du service.
- **Docker rootless** (cas des systèmes immuables comme Bazzite) : détecté
  automatiquement. Les conteneurs joignent alors le contrôleur par la boucle
  locale de l’hôte (`10.0.2.2`) et le contrôleur n’écoute que sur `127.0.0.1`.
  Cela exige `DOCKERD_ROOTLESS_ROOTLESSKIT_DISABLE_HOST_LOOPBACK=false` : si
  Docker rootless tourne par le service standard `docker.service` de
  l’utilisateur, l’installation ajoute ce réglage et redémarre Docker ; sinon,
  elle s’arrête avec la commande à appliquer. Avec Docker système, le contrôleur
  reste sur toutes les interfaces, protégé par son jeton : bloquer le port
  11436 au pare-feu du réseau local.
- **GPU avec Docker rootless** : le runtime NVIDIA doit être enregistré dans
  le `daemon.json` de ce Docker et `no-cgroups = true` réglé dans la
  configuration `nvidia-container-runtime` lue par ce démon (fichier système
  ou `$XDG_CONFIG_HOME/nvidia-container-runtime/config.toml`). L’installation
  ne modifie pas ces prérequis système ; `docker info` doit lister le runtime
  `nvidia`.
- **Python 3.15** : l’outil d’indexation complémentaire utilise libzim 4.1.0 ;
  jusqu’à Python 3.14, libzim 3.13.1 reste utilisé, sans changement pour les
  installations existantes.
- La fin de l’installation indique l’état du démarrage automatique et si le
  portail joint le contrôleur local.
