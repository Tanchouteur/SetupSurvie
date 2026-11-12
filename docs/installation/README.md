# Installer SetupSurvie

Guide d’orientation mis à jour le 11 novembre 2026. Les procédures Windows et
les essais sur les appareils de Marc restent à valider sur place.

## Installer le kit hors ligne chez Marc

Le [guide Marc](pilote-marc.md) est la référence : prérequis, vérification du kit,
installation dans des dossiers vides, raccourcis, LAN, certificats et recette.
Le kit contient les services, modèles et contenus sélectionnés ; vérifier son
manifeste avant transfert. Les prérequis système doivent être installés séparément.

## Préparer une installation depuis le dépôt

Ce parcours télécharge ses dépendances et n’équivaut pas à l’installation du kit.
Sous Windows : Python x64 3.11 à 3.15, Docker Desktop avec conteneurs Linux,
Ollama Windows et pilote NVIDIA adapté. Sous Linux : Python 3.11+, Docker avec
Compose et, pour le GPU, pilote NVIDIA et NVIDIA Container Toolkit configurés.
Les versions de référence figurent dans [versions.json](../../deploy/versions.json).
La préparation de l’OS, de Docker et des pilotes reste à la charge de l’opérateur.

Depuis la racine du dépôt, sur Windows :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Lan -DataDir 'D:\SetupSurvie\donnees'
```

Sur un Linux préparé pour Docker et NVIDIA, choisir le disque de données :

```bash
./scripts/install.sh --lan --data-dir /DISQUE/SetupSurvie/donnees
```

Remplacer les chemins d’exemple par les destinations réelles. Les images et caches
nécessaires doivent être préparés avant de couper Internet ; la présence d’un
mode hors ligne ne prouve pas que tous les fichiers sont disponibles. Ne pas
relancer une installation pour mettre à jour une installation existante : suivre
le [guide de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

Le [guide initial du prototype](../historique/installation.md) conserve les
anciennes commandes et le test documentaire de démonstration. Ses descriptions
des fonctions absentes ne représentent plus l’état du pilote actuel.

## Réseau, données et essais

Le [guide Marc](pilote-marc.md) fait référence pour les accès par IP, QR code,
`survie.local`, les ports, le pare-feu et la confiance du certificat local.
La découverte mDNS doit être testée sur chaque client. Les API internes 11435 et
11436 ne doivent pas être exposées aux lecteurs.

Les comptes et données privées restent propres à chaque installation. Avant
transfert ou modification, suivre les [procédures d’exploitation](../exploitation/README.md).
Les résultats Linux sont dans les [bilans d’essais](../essais/README.md) ; ils ne
valident pas le matériel Windows de Marc. Le laboratoire Podman de Louis conserve
ses propres contrôles de montage et de capacité, décrits dans les bilans Linux.
