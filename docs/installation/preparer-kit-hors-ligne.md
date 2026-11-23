# Préparer et vérifier le kit de transport

**Guide de référence — revu le 20 novembre 2026 pour la 0.67.0.** Les commandes
sont celles de `scripts/pilot_kit.py` ; les mesures et la recette citées restent
celles du kit 0.1.14 (12 novembre 2026). La recette finale chez Marc reste à faire.

Le kit transporte l’application, les images de services, les modèles et les
contenus sélectionnés. Les installateurs Windows peuvent être ajoutés depuis
Linux ou Windows avant de partir hors ligne. Le pilote NVIDIA et les composants
Windows propres à la machine restent à préparer selon le
[guide Windows](deux-etapes-windows.md#préparer-un-kit-pour-windows-sans-internet).
Les commandes propres au laboratoire se lancent sur le PC de Louis.

Le kit et une sauvegarde personnelle permettent de reconstruire SetupSurvie
hors ligne sur un système compatible. Les résultats et les essais restant à
mener figurent dans le [protocole du disque de secours](../exploitation/disque-de-secours-hors-ligne.md#10-recette-dacceptation).

Depuis la 0.98.0, l’export et le rafraîchissement du kit ajoutent
**LISEZ-MOI.html** à sa racine. La notice est contrôlée par le manifeste et
conservée lors d’une duplication. Ouvrez-la directement dans un navigateur
avant de remettre le SSD.


Depuis la 0.104.0, le bouton de duplication Windows peut aussi démarrer sur
un PC dépourvu de Python. Il propose dans une fenêtre l’installation de
Python avec Tcl/Tk pour le compte courant depuis les fichiers vérifiés
du kit. La duplication utilise uniquement Python et le kit, sans
préparer WSL ni démarrer Docker.


## Ajouter les installateurs Linux

Depuis la 0.101.0, préparer les outils Linux sur un ordinateur connecté,
Windows ou Linux, avec le logiciel du kit à jour. Depuis le dossier `app`
du kit, lancer la commande suivante sous Linux.

```sh
python3 scripts/pilot_kit.py prepare-linux ..
python3 scripts/pilot_kit.py prepare-linux .. --verify-only
```

Sous Windows, utiliser `py -3 scripts\pilot_kit.py prepare-linux ..`.
La préparation ajoute les installateurs vérifiés au dossier
`installateurs-linux` du kit. Le contrôle hors ligne et la duplication y
incluent Python, Docker, Compose et les paquets réseau. Prévoir environ
200 Mo supplémentaires. Sur le PC cible, suivre **LISEZ-MOI.html** et
ouvrir **Installer-Kit-SetupSurvie.desktop**. Le lanceur graphique demande
l’autorisation administrateur et déploie les outils dans la destination
choisie. Il utilise les paquets du support pour Debian 12, Debian 13 ou
Ubuntu 22.04 x86-64. Le bureau doit proposer Zenity et PolicyKit.


## Sous-commandes de `pilot_kit.py`

| Commande | Rôle |
| --- | --- |
| `export-lab DESTINATION` | Crée un kit depuis le laboratoire ; Wikipédia anglaise incluse par défaut si présente (`--no-english-wikipedia` pour un support réduit) |
| `refresh-app KIT` | Remplace le logiciel du kit par la version courante |
| `refresh-library KIT --data-dir DONNEES` | Ajoute les contenus publics épinglés ou téléchargés, avec contrôle des sources ; complète aussi un ancien kit sans Wikipédia anglaise |
| `refresh-maps-lab KIT [--geography ID]… [--routing]` | Actualise les cartes sans recopier les modèles |
| `recover-maps KIT` | Restaure la publication cartographique précédente après une interruption |
| `verify KIT` | Contrôle les empreintes et les dépendances hors ligne |
| `duplicate KIT DESTINATION` | Duplique un kit public complet sans accès réseau, avec reprise |
| `prepare-windows KIT [--verify-only]` | Prépare les installateurs Windows sur le kit ou les vérifie sans accès réseau |
| `install KIT --target windows --data-dir … --work-dir …` | Installe depuis le kit : voir le [guide Marc](pilote-marc.md#installer-à-partir-du-kit) |

Le kit constaté en 0.1.14 fait environ 161 Go ; aucune taille nouvelle n’est
annoncée sans préparation réelle. Le laboratoire ne reproduit pas tout le fonds
de Marc : les compléments se préparent sur son installation, sans plafond
documentaire, selon la [préparation du fonds complet](../bibliotheque/bibliotheque-complete-marc.md).
La copie du kit sur le volume limité de Louis garde tous ses contrôles de capacité.

## Vérifier le SSD avant de partir

Depuis la 0.111.0, ouvrir **Verifier-Kit-SetupSurvie.cmd** sous Windows ou
**Verifier-Kit-SetupSurvie.desktop** sous Linux, dans le dossier `app` du
kit. Le lanceur indique les fichiers endommagés ou manquants et vérifie
les installateurs présents. L’absence d’installateurs d’un système indique
qu’il faudra un PC déjà préparé ou ajouter ces fichiers avant de partir.

Le contrôle fonctionne sans Docker et ne modifie aucun fichier du kit.
Les mêmes prérequis graphiques que pour le bouton de duplication
s’appliquent.

Depuis la 0.112.0, le même lanceur propose de vérifier aussi une sauvegarde
personnelle : répondre **Oui**, puis choisir son dossier daté. Le contrôle
relit chaque fichier listé dans `backup.json`, refuse un fichier hors
périmètre et indique le système d’origine. Pour une sauvegarde créée depuis
la 0.94.0, il applique la règle de restauration : même format des données,
même image Open WebUI, kit de même version ou plus récent et noms de fichiers
compatibles entre les deux systèmes. Sur Linux, évitez les noms réservés par
Windows, comme `COM¹.txt`, et les caractères de contrôle. Une sauvegarde
plus ancienne est signalée comme restaurable seulement sur le même système.
En ligne de commande :

```bash
python3 app/scripts/pilot_backup.py verify /chemin/sauvegarde --kit /chemin/kit
```

Ce contrôle ne démarre ni Docker ni les services et n’écrit rien. Il ne vérifie
pas la cohérence interne des bases SQLite et ne remplace pas un essai de
restauration. Pour la restauration elle-même, suivre le
[manuel de secours](../exploitation/manuel-de-secours.md#7-restaurer-une-sauvegarde-personnelle).


## Dupliquer un kit public

Depuis la 0.92.0, sur Windows équipé de Python avec Tcl/Tk, ouvrir
**Dupliquer-Kit-SetupSurvie.cmd** dans le dossier **app** du kit. Choisir un
dossier sur le second disque et confirmer. Une fenêtre suit la copie. Le
nouveau kit apparaît dans **SetupSurvie-Kit** sous le dossier choisi. Il
contient à son tour le lanceur.

Depuis la 0.93.0, sur Linux équipé de Python 3.11 ou ultérieur avec Tkinter,
ouvrir **Dupliquer-Kit-SetupSurvie.desktop** dans le même dossier **app**.
Depuis la 0.105.0, un bureau avec Zenity permet aussi de dupliquer le kit
sans Python préinstallé si les installateurs Linux sont sur le support.
Le lanceur extrait Python dans un dossier temporaire et le retire à la
fin. Avec Python 3.11 ou ultérieur et Tkinter, la fenêtre habituelle
reste disponible.
Si le bureau demande de faire confiance au lanceur, l’autoriser pour ce kit.
Choisir un dossier accessible en écriture sur le second disque. L’assistant
utilise les droits de la session et reprend une copie interrompue vers la
même destination.

Les postes Linux ou Windows équipés de Python peuvent aussi utiliser la
commande suivante. Exemple sur Linux.

```bash
python3 scripts/pilot_kit.py duplicate /media/SSD-A/SetupSurvie /media/SSD-B/SetupSurvie
```

Le parent de la destination doit déjà exister. Choisir un dossier vide sur
le second disque. Le lanceur copie les éléments du manifeste, puis publie
le manifeste du second support après contrôle des empreintes. Les
installateurs Windows préparés sont vérifiés et inclus, avec les paquets
CAB éventuellement fournis dans `installateurs-windows/sxs`. Si la préparation
des installateurs a commencé sur A, la terminer avant la duplication.
Les fichiers hors inventaire restent sur la source.

Après une interruption, relancer la même commande vers le même dossier.
Si le système a remonté le support source sous un autre chemin, indiquer ce
nouveau chemin. Le deuxième support peut servir à son tour de source.
Cette commande concerne le kit public. Les profils, conversations et autres
données privées utilisent le [disque de secours](../exploitation/disque-de-secours-hors-ligne.md).

## Ajouter les installateurs Windows depuis Linux

Depuis un poste connecté avec Python 3.11 ou ultérieur, utiliser un kit dont
le dossier **app** est en 0.82.0 ou ultérieur.

```bash
python3 scripts/pilot_kit.py prepare-windows /chemin/du/kit
python3 scripts/pilot_kit.py prepare-windows /chemin/du/kit --verify-only
```

La première commande utilise le catalogue du kit et reprend les téléchargements
interrompus. Elle prévoit environ 2,8 Go pour les cinq installateurs. Seuls les
fichiers ayant la taille et l’empreinte attendues sont publiés dans
`installateurs-windows`. Relancer avec `--verify-only` après copie sur
le SSD pour tout vérifier sans téléchargement. Sur le PC Windows déconnecté,
ouvrir le lanceur habituel dans le dossier **app** du kit.

## Actualiser les cartes sans recopier les modèles

Le volume dédié doit être monté et validé par le laboratoire. Depuis le dépôt :

```bash
python3 scripts/pilot_kit.py refresh-maps-lab /run/media/louis/SetupSurvie/livraison-marc --geography 1a387fb055b0ff8888bf --routing
python3 scripts/pilot_kit.py refresh-app /run/media/louis/SetupSurvie/livraison-marc
python3 scripts/pilot_kit.py verify /run/media/louis/SetupSurvie/livraison-marc
```

- `--geography` prend l’identifiant d’une zone préparée, c’est-à-dire un dossier de
  `library/maps/geography/` du volume de données. L’exemple est la zone publique
  autour de Solliès-Ville telle qu’elle était en 0.1.14 (rayon 10 km) ;
  `deploy/map-catalog.json` déclare aujourd’hui un rayon de 25 km, donc une zone
  préparée maintenant a un autre identifiant. Répéter l’option pour plusieurs
  zones. Seuls les fichiers référencés des zones choisies et les fonds PMTiles
  recensés sont copiés ; aucun domicile, point personnel, compte ou réglage privé
  n’est exporté.
- `--routing` ajoute le réseau marche/moto/voiture et l’image OSRM figée ; si la
  liste des images change, l’archive est reconstruite depuis les images locales
  sans registre. Modèles et documents existants restent en place, les anciens lots
  cartographiques ne sont pas supprimés implicitement.
- Une réserve de 15 Go libres et l’espace de préparation sont exigés.

La publication remplace les fichiers avec un journal et un marqueur qui bloque
l’installation. Après une interruption signalée, conserver le kit et lancer :

```bash
python3 scripts/pilot_kit.py recover-maps /run/media/louis/SetupSurvie/livraison-marc
```

Cette commande ne restaure que la publication cartographique précédente (pas les
autres types d’export interrompus) ; relancer ensuite l’actualisation et la
vérification. Une erreur avant publication laisse l’ancien kit utilisable.

## Contrôler le contenu avant transfert

`verify` relit les empreintes de tous les fichiers, puis contrôle les dépendances
hors ligne : couches des modèles, caches de recherche et de transcription, paquets
de découverte réseau, images annoncées et présentes dans l’archive, versions du
code, cartes, relief, lieux et graphes. Revérifier le kit après copie sur le
support de transport. Ce contrôle ne lance aucun modèle et ne vaut pas une
installation Windows réussie.

Recette réelle des cartes à partir du kit, sur Linux :

```bash
python3 scripts/audit_kit_lab.py /run/media/louis/SetupSurvie/livraison-marc --output /run/media/louis/SetupSurvie/results/kit-offline-0.1.14/isolation.json
```

Elle importe les images dans le cache Podman existant du laboratoire, emploie un
réseau interne sans passerelle Internet et calcule les trois types de trajet avec
les seules données du kit. Aucun compte réel, modèle ni GPU n’est monté ; seuls
les conteneurs, le réseau et les copies temporaires de la recette sont retirés
ensuite (le cache partagé est conservé). Elle ne reconstitue pas une machine
vierge. Rapport et limites : [bilan daté](../essais/2026-11-12-kit-marc-hors-ligne.md).

## Recette finale chez Marc (à faire)

Après préparation des prérequis : couper Internet en gardant le réseau local ;
vérifier et installer depuis le kit ; ouvrir la bibliothèque et les cartes ;
calculer un trajet dans la zone couverte ; essayer l’assistant ; redémarrer
Windows ; tester les deux icônes et l’accès depuis un autre appareil ; refaire
ces essais après retrait du support de transport. La présence des fichiers ne
valide ni les performances de la RTX 5060 Ti, ni Safari iOS, ni la praticabilité
des voies. Les conditions de redistribution commerciale de chaque source restent
à examiner : le transport familial du pilote ne vaut pas validation d’une offre
vendue.
