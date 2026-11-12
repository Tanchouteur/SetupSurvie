# Kit Marc et contrôles hors ligne — 12 novembre 2026

**Bilan daté du pilote 0.1.14, Linux Bazzite de Louis.** Procédures actuelles :
[préparer le kit](../installation/preparer-kit-hors-ligne.md) et
[installer chez Marc](../installation/pilote-marc.md).

## Contenu effectivement ajouté

Le dossier SSD `livraison-marc` passe d’environ 160,08 à **160,94 Go décimaux**
(environ 149,88 Gio). Les sept modèles, cinq ZIM et guides déjà sélectionnés sont
conservés ; aucun nouveau téléchargement documentaire n’est implicite.

- Deux PMTiles : Sud (PACA, Occitanie et Corse) et Solliès-Ville, édition du 10 novembre.
- Zone publique de 10 km autour de 6,04° E / 43,18° N : 1 042 lieux,
  6 118 adresses, deux tuiles de relief HGT et attribution, environ 53 Mo.
- Trois graphes OSRM : marche, moto et voiture, 78 fichiers, environ 95,52 Mo.
- Image OSRM figée ajoutée aux quatre images de services : cinq images dans
  l’archive transportable. Aucun changement des versions tierces.

Le parcours de mise à jour n’exporte que les fichiers référencés des zones
choisies et les fonds recensés, sans état privé. Sa publication dispose d’un
journal et d’une récupération après interruption. Les empreintes sont recalculées.
Une incompatibilité de représentation des identifiants d’images Podman/Docker
(sans/avec préfixe `sha256:`) est corrigée pour l’import Windows.

## Contrôles exécutés

- Relecture complète des empreintes des quelque 161 Go du kit ; conformité.
- Contrôle des couches des sept modèles, caches BGE-M3 / Whisper / tokenisation,
  douze paquets de découverte, versions, cinq images et références cartographiques.
- Import réel de l’archive d’images depuis le kit, sans registre.
- Nouveaux conteneurs OSRM et client de contrôle, réseau interne sans passerelle
  Internet, données cartographiques copiées depuis le kit. Deux cartes reconnues,
  zone et relief lus (242 m au point public de test).
- Trajets entre deux points publics rapprochés des voies : marche 2 011 m / 1 810 s ;
  moto et voiture 3 165,4 m / 285 s. Ces chiffres ne prouvent pas la praticabilité
  des voies ni les conditions réelles de déplacement.
- 142 tests unitaires : 141 réussites, un test COM Windows ignoré sur Linux.
  Configuration Compose vérifiée dans cette suite ; aucun service lancé par ce test.
- Aucun LLM ou benchmark lancé, aucun état utilisateur réel monté dans la recette,
  aucun GPU demandé, aucune pause levée. Réserve du SSD conservée, environ 120 Gio libres.

Rapports conservés sur le SSD, hors Git : `results/kit-offline-0.1.14/`, fichiers
`verification.txt`, `isolation.json`, `isolation.log` et `tests.txt`.

## Limites et première installation

Deux tentatives de stockage d’images entièrement neuf ont échoué faute de place
pour les nombreux petits fichiers (inodes) du volume du laboratoire. Le test
réussi importe l’archive dans le **cache Podman existant**, puis utilise des
conteneurs et un réseau jetables ; il ne valide pas une machine vierge. Les
images partagées sont conservées, seuls les objets du test sont supprimés.

Marc a précisé qu’aucun prérequis n’est installé sur son Windows. Le parcours
recommandé est de préparer Windows/WSL 2, pilote NVIDIA, Python, Docker Desktop
et Ollama avec Internet, puis installer le kit hors ligne. Ces installateurs
système ne sont pas inclus. Aucun nouveau bootstrap système hors ligne n’est
annoncé comme développé.

Restent à exécuter chez Marc : installation Windows depuis le kit, assistant et
GPU, ouverture de session, raccourcis, redémarrage hors ligne, accès réseau et
Safari iOS. Les tests Linux ne valident pas sa RTX 5060. Les routes et lieux
préparés concernent cette zone, pas toute la France. Les droits de redistribution
commerciale des différentes sources restent à examiner avant une offre vendue.
