# Bibliothèque du Sud, recherche et IA — pilote 0.1.7

> Bilan daté — résultats et limites conservés pour cette étape. Les nombres de ressources, versions et états décrivent la campagne rapportée, sans nouvelle validation lors du classement documentaire.

Vérifié sur le laboratoire Linux de Louis le 11 novembre 2026. Localisation
confirmée : **Solliès-Ville**, avec une couverture du Sud interprétée comme
**PACA, Occitanie et Corse**. Aucun matériel familial précis n’a été inventé.

Voir la [liste complète des ressources téléchargées](../bibliotheque/inventaire-ressources-telechargees.md).

## Contenus réellement ajoutés

Le catalogue passe de 47 à **78 ressources figées**. Les **31 nouveaux fichiers**
sont téléchargés et vérifiés par SHA-256, avec provenance, langue, édition ou
date de collecte et réserve sur les droits :

- DICRIM de la mairie de Solliès-Ville et DDRM du Var, édition 2025.
- Guide du jardinier en climat méditerranéen et guide de production de semences
  potagères biologiques.
- Guides Éduscol pour la lecture/écriture et les nombres/calculs au CP ; cahier
  Sésamath CM2 ; Wikiversité français illustré d’août 2026.
- Manuels ANFR de préparation aux CRR maritime et fluvial de 2025.
- INRS : soudage, brasage, risque électrique et consignation.
- MOOC d’initiation à la botanique de Tela Botanica, proposé par Vigie-Nature ;
  fiches Anses sur les plantes toxiques.
- Introduction et douze chapitres de l’édition 2025 de *Where There Is No Dentist*
  d’Hesperian, avec droits et attributions.
- Guide OMS des premiers secours psychologiques, en français.

Ces fichiers complètent les ressources précédentes : eau, santé MSF, aliments
USDA, abris, jardins FAO, câblage Victron, iFixit, Appropedia, Low-tech Magazine,
Vikidia, Wikipédia et Wikilivres français/anglais.

Les données restent sur le SSD dédié, hors Git. Reprise depuis le catalogue
`deploy/content-catalog.json` :

~~~bash
python3 scripts/content.py download --lab --no-refresh --budget-gb 500 \
  --pack local --pack agriculture --pack education-primary \
  --pack communications --pack crafts --pack nature --pack family-health
~~~

Le guide OMS utilise son lien officiel actuel : l’ancien lien IRIS renvoyait une
page HTML. Une tentative infructueuse ne compte pas comme un fichier disponible.

## Cartes consultables sans Internet

Deux extraits OpenStreetMap/Protomaps du **10 novembre 2026** sont prêts :

| Carte | Emprise | Détail des données | Taille |
| --- | --- | --- | ---: |
| Sud | longitude −1,8 à 9,7 ; latitude 41,3 à 45,3 | Jusqu’au zoom 13 | 598,80 Mo |
| Solliès-Ville et alentours | longitude 5,65 à 6,4 ; latitude 43 à 43,5 | Jusqu’au zoom 15 | 36,64 Mo |

Le lecteur `/cartes.html`, accessible depuis la Bibliothèque, permet déplacement,
zoom, choix de zone et impression de la vue. JavaScript, styles et polices sont
locaux ; licences et empreintes sont dans `portal/vendor/maps/sources.json`.
Les archives restent sous `data/library/maps`. Elles ont passé la vérification
structurelle PMTiles et le SHA-256 local ; le manifeste conserve source, date,
emprise et attribution ODbL.

Les cartes ne calculent pas d’itinéraire, n’affichent pas de relief altimétrique
et ne donnent pas l’état actuel des chemins, ponts ou points d’eau. Zoomer au-delà
du niveau de détail agrandit les données existantes. La recherche retrouve le
guide des cartes ; elle n’analyse pas les géométries pour calculer un trajet.

La préparation reproductible est définie dans `deploy/map-catalog.json` :

~~~bash
python3 scripts/maps.py --lab \
  --tool /run/media/louis/SetupSurvie/tools/pmtiles/pmtiles
~~~

Le CLI PMTiles Linux 1.31.2 provient de sa publication officielle, avec comparaison
à l’empreinte publiée par GitHub. Il extrait uniquement les zones retenues, sans
télécharger la planète entière. L’opération surveille tailles, budget et marge
physique, puis vérifie le fichier avant publication. Le lecteur client Windows/
téléphone ne dépend pas de cet exécutable Linux.
L’export du kit inclut désormais les cartes terminées ; le kit déjà créé n’a
pas été recopié intégralement dans cette tâche.

## Indexation et recherche vérifiées

Le pilote indexe **75 guides**, dont **4 500 pages PDF avec texte**. Aucun document
n’est signalé en échec ou entièrement dépourvu de texte ; aucune page n’atteint
la borne de texte de l’indexeur dans cette collecte. Les **dix archives ZIM** sont
enregistrées dans Kiwix et recherchées par ses index natifs.

L’indexeur produit `index-report.json` dans l’état du pilote : caractères, pages
retrouvables, pages bornées et documents nécessitant un OCR ou dépassant les
limites. Le rapport public `GET /api/library/coverage` ne contient aucun compte
ni secret. Un fichier simplement présent n’est plus la seule preuve retenue.

La recherche ajoute du vocabulaire français/anglais pour l’eau, les semences,
l’agriculture, les dents, la botanique, les métiers, la radio et les cartes.
La Bibliothèque cherche par défaut dans les deux langues ; les filtres restent
disponibles. Les consignes de l’outil IA précisent la recherche bilingue et la
lecture des sources avant citation.

Les **16 recherches** de `fixtures/evaluation/library-coverage.json` ont réussi.
La recette utilise `limit=3` et les cinq premiers résultats, comme l’assistant,
puis lit la source et ouvre l’original :

- Risques de Solliès-Ville et inondation dans le Var.
- Jardin méditerranéen et semences potagères.
- Lecture au CP, calcul au CP et fractions au CM2.
- VHF maritime et soudage au chalumeau.
- Botanique et plantes toxiques.
- Question française « douleur dents » retrouvant un chapitre anglais.
- Secours psychologiques ; question française sur la désinfection des puits
  retrouvant une fiche anglaise.
- Cartes locales et modèle de dossier familial/notices.

Les PDF renvoient à la page de l’original illustré. Les textes extraits ne
remplacent pas cet original.

~~~bash
python3 scripts/audit_library.py \
  --data-dir /run/media/louis/SetupSurvie/data \
  --output /run/media/louis/SetupSurvie/results/library-coverage-audit.json
~~~

Ces contrôles portent sur la recherche du portail et les outils de son assistant.
Ils ne signifient pas que les 200 Go ont été importés dans les collections
avancées d’Open WebUI ni vectorisés intégralement.

## Deux essais réels de l’assistant

Le marqueur de pause n’était pas présent. Aucune reprise forcée, aucun nouveau
modèle et aucun changement de réglage n’ont été nécessaires.
Deux questions courtes ont été posées avec un compte lecteur temporaire :

| Essai | Résultat vérifié | Durée |
| --- | --- | ---: |
| DICRIM de Solliès-Ville | Recherche, lecture et citation de la page 1 du nouveau PDF | 19,53 s |
| Guide dentaire anglais, réponse française | Recherche, lecture et citation de la page 11 du chapitre 5 | 13,48 s |

Les traces confirment `search_library` et `read_source`, puis la citation de la
source lue. Le compte et ses conversations de recette ont été supprimés.
Rapport sans identifiants de connexion :
`data/state/pilot/acceptance-library.json` sur le volume.
Ce sont deux vérifications fonctionnelles, pas une mesure générale de fiabilité.
Le programme est `pilot/acceptance_library.py` ; ne pas le lancer lorsqu’une pause
du moteur est demandée.

## Navigateur, tests et stockage

- **77 tests automatisés réussis**, dans un conteneur sans réseau, secrets,
  données réelles ou GPU. Compose a uniquement analysé les configurations.
- Carte dessinée dans Chromium avec rendu logiciel, sans GPU : lectures HTTP
  partielles, polices locales, choix de zone et largeurs 320, 390 et 768 px.
  Toutes les requêtes extérieures étaient bloquées ; aucune n’a été nécessaire.
  Captures et rapport sous `results/maps-*` sur le SSD.
- Le test visuel a permis de corriger le chemin des polices avant validation.
- iPhone réel et Windows de Marc restent à essayer.

La bibliothèque représente environ **200,60 Go**, sur les 500 Go documentaires.
Modèles et caches de comparaison sont exclus ; le kit ne double pas le comptage
des mêmes documents. La marge physique est contrôlée séparément, avec au moins
15 Go réservés. Aucun index vectoriel de Wikipédia entier n’est nécessaire.

L’actualisation du laboratoire se fait séparément des services de transfert :

~~~bash
python3 scripts/lab_refresh_library.py
~~~

Ce script recrée seulement Kiwix et le pilote, en conservant données montées,
comptes et réglages. Il ne démarre pas Ollama et ne modifie pas son marqueur de
pause. Les processus persistants ne doivent pas dépendre de la limite mémoire
du service de transfert.

## Personnalisation et limites

- Les références exactes des pompes, radios, poêles, batteries, véhicules et
  outils restent à fournir. Les guides génériques ne sont pas leurs notices.
- `REF-dossier-familial.fr.md` fournit des tableaux vierges pour notices, stocks
  et organisation. Aucun renseignement privé n’a été inventé ou rendu public.
  Les documents personnels remplis restent hors de la bibliothèque partagée
  et du kit générique.
- Les liens vidéo du MOOC ne sont pas tous des fichiers vidéo conservés.
  Flores, cartes et risques archivés ne certifient pas une récolte ou un trajet.
- OCR générique de tous les scans, programme scolaire complet avec tous les
  corrigés et couches géologiques/altimétriques détaillées restent à compléter.
- Les droits commerciaux restent à examiner. ANFR et Hesperian comportent
  notamment des restrictions de reproduction ; téléchargement personnel et
  autorisation de redistribution sont deux états distincts.
