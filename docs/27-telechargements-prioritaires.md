# Ressources prioritaires : téléchargements du 11 novembre 2026

Livraison logicielle **0.1.6**, sans changement d’image tierce ni migration de données.

Budget confirmé par Louis : **500 Go décimaux de bibliothèque documentaire**.
Les modèles IA et caches d’essai sont exclus ; le kit de transport n’est pas
compté une seconde fois. Le plafond physique du laboratoire de 590 milliards
d’octets et une marge libre d’au moins 15 Go restent contrôlés séparément.
Aucun modèle n’est supprimé et le mode jeu reste actif.

## Collections sélectionnées

Le catalogue figé `deploy/content-catalog.json` contient 47 entrées, dont 23
compléments sélectionnés dans cette session, pour **7,96 Go supplémentaires** :

- Santé : guides MSF français, clinique et thérapeutique, médicaments essentiels.
  Ce sont des références professionnelles. Le PDF clinique est en retard sur
  les mises à jour du site ; conserver cette réserve dans la provenance.
- Conservation alimentaire : introduction et sept parties du guide USDA/NCHFP,
  révision 2015, en anglais.
- Eau et hygiène : dix notes OMS/WEDC supplémentaires de 2013 sur puits, forages,
  réservoirs, réseaux, traitement, déchets, hygiène, transport et assainissement.
- Réparation : iFixit français de mars 2026 et anglais de décembre 2025.
- Énergie et techniques sobres : Low-tech Magazine multilingue, janvier 2025.

Les lots existants restent sélectionnés et vérifiés sans nouveau téléchargement
si le fichier est conforme : premiers secours PSC/GQS, préparation SGDSN, abris
IFRC/UNHCR, eau OMS, latrines Croix-Rouge française, agriculture FAO, câblage
Victron, Appropedia, Vikidia et manuels Sésamath de la 6e à la 3e.
Les quatre archives Wikipédia/Wikilivres déjà présentes ne sont pas retéléchargées.

Chaque nouvelle entrée possède taille et SHA-256 vérifiés : empreinte publiée
dans le Metalink Kiwix pour les ZIM ; empreinte calculée sur une collecte HTTPS
du producteur pour les PDF, puis contrôlée de nouveau avant publication locale.
La seconde méthode contrôle la stabilité du fichier, pas son contenu éditorial.
Les éditions, langues, notes de contexte et droits restent dans le catalogue.

## État de lancement et reprise

Service utilisateur démarré : `setupsurvie-priority-content.service`, avec priorité
CPU/disque réduite, sans GPU ni inférence. Les 20 nouveaux PDF ont été téléchargés
et vérifiés avant le début des trois ZIM ; les ZIM restent à considérer en cours
tant que le fichier de progression n’indique pas `done`.

```bash
python3 scripts/content.py download --lab --budget-gb 500 \
  --pack health --pack food --pack water --pack repair \
  --pack survival --pack education

systemctl --user status setupsurvie-priority-content.service
journalctl --user -u setupsurvie-priority-content.service -n 20 --no-pager
```

Le suivi local est `data/catalog/content-progress.json` sur le volume du laboratoire.
Une relance reprend les `.part` ; une taille ou une empreinte incorrecte bloque
la publication. Ne pas démarrer deux commandes concurrentes : un verrou les exclut.
Les transferts contrôlent le budget avant le lot et avant chaque écriture.
Le budget compte `data/library` une seule fois, y compris les transferts partiels ;
la marge physique considère aussi les modèles, caches, conteneurs et kit présents.

À la fin, seuls Kiwix et le pilote sont redémarrés pour actualiser les collections,
sans démarrage du moteur IA. La présence sur disque et le SHA-256 ne prouvent pas
encore la qualité des recherches ni une validation hors ligne de chaque guide.

## Droits et lacunes

Collecte pour le pilote personnel de Louis et Marc : ne pas interpréter l’ajout
au catalogue comme une autorisation commerciale. Les guides MSF et les contenus
iFixit imposent notamment un examen des droits avant redistribution ; les notices
et attributions doivent rester jointes aux originaux.

Le téléchargement du manuel Sphère français a reçu HTTP 403 ; la note OMS n°8
a reçu HTTP 404 à l’adresse essayée. Ces deux ressources ne sont pas annoncées
comme téléchargées. Le rapport est `results/priority-source-check.json` sur le SSD.
Les cartes utilisables dans le portail, les atlas naturalistes régionaux, les
notices du matériel exact et le dossier familial restent à préparer. Les communes
de vie/repli ne sont pas connues dans ce travail.

## Vérifications

Dix tests ciblés couvrent reprise, fichier existant préservé, intégrité, dépassement
de taille, chemins, montage absent, plafond documentaire, exclusion des modèles et
du kit, marge physique et arrêt avant écriture si le budget change en cours de transfert.
Ils utilisent des contenus simulés et n’appellent aucun modèle IA.

La suite complète a ensuite réussi : **72 tests**, dans l’image du service, sans
réseau, secrets, données réelles ni GPU. Le binaire Compose déjà présent a servi
uniquement à analyser les configurations, sans démarrage de moteur Docker.
`git diff --check` est également passé. Ces contrôles ne valident pas le Windows
de Marc, un iPhone réel ni la pertinence de chaque réponse documentaire.
