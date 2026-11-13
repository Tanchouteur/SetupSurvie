# Préparer et vérifier le kit de transport

Guide de référence du pilote 0.1.14 — 12 novembre 2026.

Le kit transporte l’application, les images de services, sept modèles et les
contenus sélectionnés. Les prérequis Windows restent séparés : suivre le
[guide Marc](pilote-marc.md#avant-de-copier-le-kit). Préparer ces logiciels avec
Internet une première fois ; un Windows vierge ne peut pas être installé avec
ce seul kit. Les commandes ci-dessous préparent le kit sur le laboratoire de
Louis ; elles ne sont pas des prérequis à installer chez Marc.

Le besoin de reconstruction complète sur une autre machine, Windows ou Linux, sans aucun téléchargement est formalisé dans le [protocole du disque de secours](../exploitation/disque-de-secours-hors-ligne.md), daté du 13 novembre 2026. Il inclut prérequis, fonds réel complet, états personnels et manuel humain. Il reste à développer et qualifier : les résultats du kit ci-dessous conservent leur périmètre historique.

## Actualiser les cartes sans recopier les modèles

Le volume dédié doit être monté et validé par le laboratoire. Depuis le dépôt :

```bash
python3 scripts/pilot_kit.py refresh-maps-lab /run/media/louis/SetupSurvie/livraison-marc --geography 1a387fb055b0ff8888bf --routing
python3 scripts/pilot_kit.py refresh-app /run/media/louis/SetupSurvie/livraison-marc
python3 scripts/pilot_kit.py verify /run/media/louis/SetupSurvie/livraison-marc
```

L’identifiant ci-dessus désigne la zone publique préparée autour de Solliès-Ville
(centre 6,04° E / 43,18° N, rayon 10 km). Pour une autre zone, utiliser son
identifiant de manifeste après préparation. Répéter `--geography` pour plusieurs
zones. La commande copie les fonds PMTiles recensés et seulement les fichiers
référencés des zones explicitement choisies. Aucun domicile, point personnel,
compte ou réglage privé n’est exporté par ce parcours.

`--routing` ajoute le réseau courant marche/moto/voiture et l’image OSRM figée.
Si la liste des images change, l’archive est reconstruite à partir des images
locales sans registre. Les modèles et documents existants restent en place.
Une réserve de 15 Go et l’espace de préparation sont exigés. Les anciens lots
cartographiques déjà présents ne sont pas supprimés implicitement.

La publication remplace les fichiers avec un journal et un marqueur bloquant
l’installation. En cas d’interruption signalée, conserver le kit et lancer :

```bash
python3 scripts/pilot_kit.py recover-maps /run/media/louis/SetupSurvie/livraison-marc
```

Cette commande restaure la publication cartographique précédente ; elle ne
récupère pas d’autres types d’export interrompus. Relancer ensuite l’actualisation
et la vérification. Une erreur avant publication laisse l’ancien kit utilisable.

## Contrôler le contenu avant transfert

`verify` relit les empreintes de tous les fichiers, puis contrôle les dépendances
hors ligne : couches des modèles, caches de recherche et dictée, paquets de
découverte réseau, images annoncées et présentes dans l’archive, versions du code,
cartes, relief, lieux et graphes. Un kit conforme doit être revérifié après copie
sur le support de transport. Ce contrôle ne lance aucun modèle et ne constitue
pas une installation Windows réussie.

Pour refaire une recette réelle des cartes à partir du kit sur Linux :

```bash
python3 scripts/audit_kit_lab.py /run/media/louis/SetupSurvie/livraison-marc --output /run/media/louis/SetupSurvie/results/kit-offline-0.1.14/isolation.json
```

Cette recette importe les images dans le cache Podman existant du laboratoire,
emploie un réseau interne sans passerelle Internet, et calcule les trois types
de trajet avec les seules données du kit. Aucun compte réel, modèle ou GPU
n’est monté. Seuls les conteneurs, le réseau et les copies temporaires de la recette sont retirés
ensuite ; le cache partagé est conservé. Ce test ne reconstitue pas une machine vierge. Le rapport
et les limites de la campagne sont dans le [bilan daté](../essais/2026-11-12-kit-marc-hors-ligne.md).

## Recette finale chez Marc

Après préparation des prérequis, couper Internet en conservant le réseau local,
vérifier et installer depuis le kit, ouvrir la bibliothèque et les cartes,
calculer un trajet dans la zone couverte, puis essayer l’assistant. Redémarrer
Windows, tester les deux icônes et l’accès depuis un autre appareil. Refaire ces
essais après retrait du support de transport. La présence de fichiers ne valide
ni les performances de la RTX 5060, ni Safari iOS, ni la praticabilité des voies.

Les conditions de redistribution commerciale de chaque source restent à examiner ;
le transport familial pour le pilote ne vaut pas validation d’une offre vendue.

## Fonds complet depuis 0.1.15

Le kit constaté en 0.1.14 reste à environ 161 Go ; aucune taille nouvelle n'est annoncée sans préparation réelle. Les nouveaux exports `export-lab` incluent Wikipédia anglais par défaut si présent. L'option `--no-english-wikipedia` conserve la possibilité d'un support réduit. `refresh-library KIT --data-dir DONNEES` complète aussi un ancien kit marqué sans Wikipédia anglais et ajoute les collections publiques enregistrées par le téléchargeur, avec contrôle des sources.

Le laboratoire ne doit pas reproduire tout le fonds de Marc : préparer les compléments directement sur son installation, sans plafond documentaire, selon le [guide actuel](../bibliotheque/bibliotheque-complete-marc.md). La copie du kit sur le volume limité de Louis conserve tous ses contrôles de capacité.
