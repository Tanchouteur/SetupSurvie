# Savoirs et savoir-faire durables

**Guide actuel — pilote 0.1.19, 12 novembre 2026.** Besoins transmis par Marc,
intégrés aux thèmes, aux parcours et aux règles de l’assistant. Le corpus reste
à enrichir et à examiner : une collection repérée ne valide pas chaque procédé.

Le cap est de pouvoir comprendre, fabriquer, réparer, soigner, cultiver et
enseigner, au quotidien et sur une longue durée. Les principes doivent permettre
d’adapter une méthode aux conditions et au matériel disponibles. Aucun sinistre
n’est présumé et l’autonomie matérielle complète n’est pas garantie.

## Les besoins retenus

| Domaine | Contenu recherché |
| --- | --- |
| Sciences fondamentales | Arithmétique, géométrie, algèbre, physique, chimie, biologie, écologie et géologie ; cours progressifs et exercices |
| Mesure et contrôle | Unités, conversions, proportions, balances, volumes, température, pression, humidité, pH, étalonnage, essais de matériaux et contrôle qualité |
| Matériaux | Bois, argile, pierre, minerais, fibres, peaux, chaux et métaux ; briques, verre, charbon de bois, mortier, papier, cordages et colles |
| Outils et machines | Outils à main et affûtage ; engrenages, poulies, pompes, moulins, tours, forges, roues hydrauliques et transmissions ; plans cotés et tolérances |
| Métallurgie | Production et travail du fer et des métaux courants, traitements thermiques, fonderie et corrosion |
| Chimie pratique | Savons, chaux, céramiques, colles, peintures, encres et entretien ; conditions, protections et limites des procédés |
| Textile et entretien | Couture, vêtements, chaussures, cuir, fibres, cordages et objets simples ; entretien et réparation des outils |
| Agriculture durable | Sols, compost, rotations, fertilité à long terme, irrigation, drainage, sélection et conservation des semences, multiplication, greffage, cultures de base, maladies et ravageurs |
| Santé et santé publique | Anatomie, physiologie, hygiène, diagnostic différentiel, infections, santé maternelle et infantile, soins dentaires, chirurgie documentée, pharmacologie, préparation et conservation des remèdes ; références datées et traçables |
| Transmission | Lecture, écriture, calcul, enseignement, apprentissage des métiers, documentation d’une méthode et vérification de la compréhension |
| Organisation collective | Règles communes, conflits, biens partagés, comptabilité, répartition du travail, coopération et conservation des archives |
| Histoire des techniques et sociétés | Production de nourriture, énergie, outils, soins et institutions ; conditions de réussite et d’échec des méthodes |

Pour chaque réalisation, rechercher les prérequis, matériaux, outils, instruments,
plans, conditions, mesures de contrôle, limites, entretien et alternatives. Les
actes de soin et procédés à risque doivent préciser les compétences et moyens
nécessaires. Les [règles de fiabilité](../utilisation/sources-et-fiabilite.md)
s’appliquent aussi à ces domaines.

## Ce qui est intégré au logiciel

- **Bibliothèque → Explorer les savoir-faire** : 13 parcours, dont réparation,
  avec des sujets concrets. **Chercher les documents** utilise la recherche locale
  bilingue. **Préparer une question à l’assistant** remplit une demande adaptée au
  niveau, aux exercices et aux sources ; l’utilisateur choisit de l’envoyer.
- Une méthode commune : **comprendre → mesurer → réaliser → contrôler →
  entretenir → transmettre**. Les parcours et la recherche restent accessibles
  sans modèle chargé ; une question n’est générée qu’après envoi et disponibilité
  du moteur. Une pause IA n’est pas levée.
- **Données locales → Enrichir la bibliothèque** : 38 thèmes. Les nouveaux thèmes
  couvrent sciences, mesure, textile, matériaux, machines, métallurgie, chimie
  pratique, organisation et histoire des techniques. Les axes existants sont
  approfondis. Les anciennes sélections conservent leurs choix : cocher les
  nouveaux thèmes puis préparer une nouvelle sélection.
- Les thèmes peuvent sélectionner des manuels déjà référencés : mathématiques,
  lecture, semences, jardin scolaire, mesure du chlore, santé et prévention en
  atelier. Un guide commun à plusieurs thèmes est téléchargé une seule fois.
- La sélection affiche les **besoins restant à vérifier** pour chaque parcours.
  Les références sont repérées dans les métadonnées ; la présence locale au moment
  de la sélection ne certifie ni l’intégrité, ni l’indexation, ni la couverture.

Le fichier `deploy/kiwix-themes.json` est la référence commune des thèmes et
parcours ; ces listes ne sont pas recopiées dans plusieurs guides. Aucun menu
principal supplémentaire ni suivi scolaire automatique n’est ajouté.

## Sources repérées et limites

Le [catalogue officiel Kiwix](https://opds.library.kiwix.org/catalog/v2/entries?count=-1) consulté le **12 novembre 2026** contient **3 657
entrées**. Les règles ajoutent notamment les collections LibreTexts de
mathématiques, physique, chimie, biologie, géosciences, statistiques, ingénierie,
éducation, médecine, gestion, sciences sociales et humanités ; des collections
de questions-réponses complètent la recherche. Les correspondances de logiciel
pur sont exclues des nouveaux axes matériels et de mesure.

Les Metalinks officiels de LibreTexts mathématiques, ingénierie et gestion ont
été contrôlés : nom du fichier, taille et SHA-256 fournis. Aucun ZIM n’a été
téléchargé dans le runner. Le téléchargeur vérifiera les fichiers lors de leur
préparation sur le PC cible. Les illustrations, cours, exercices et plans précis
restent à examiner dans les contenus réellement acquis.

Les collections générales et forums peuvent aider sans fournir un manuel complet
de cordonnerie, métrologie, métallurgie, fabrication de médicaments ou gouvernance
locale. Ces besoins restent visibles dans la grille ; aucun document, plan coté
ou résultat d’essai n’est inventé pour les combler. Les ouvrages historiques
doivent conserver leur époque et leurs limites.

Les droits de redistribution commerciale restent à examiner par contenu,
notamment chez LibreTexts dont les [conditions](https://www.libretexts.org/terms-conditions)
renvoient aux licences applicables. Les références sélectionnées conservent le
marqueur de revue commerciale. Cette intégration n’annonce aucune nouvelle
collection téléchargée chez Marc ou dans le laboratoire.

## Examiner et compléter le fonds

Pour produire une grille datée à partir du catalogue officiel, sans télécharger
de documents ni lancer de modèle :

```bash
python scripts/audit_learning.py --output /CHEMIN/NEUF/savoirs.json
```

`--feed catalogue.xml` réutilise un catalogue sauvegardé. `--data-dir DOSSIER`
relève aussi la présence des fichiers ; sans cette option, elle reste inconnue.
Le rapport distingue références repérées, fichiers présents et sujets à examiner.
Il conserve l’adresse et l’empreinte du catalogue. Choisir un nouveau rapport à
chaque audit ; aucun fichier existant n’est remplacé.

Compléter ensuite sur le PC cible par les [sélections de collections](selection-kiwix-par-theme.md)
et le [fonds complet de Marc](bibliotheque-complete-marc.md). Vérifier le plan et
la place libre avant de transférer. Le laboratoire garde son plafond physique et
ses contrôles de montage ; il n’a pas à recopier tout le fonds de Marc.

Les tests CPU utilisent de minuscules fixtures : sélection, dédoublonnage,
langues, présence distincte de la validation, recherche bilingue, parcours et
préparation de questions. Les recettes navigateur couvrent les écrans de 320 à
1 366 pixels. La qualité pédagogique réelle, les procédés, les droits par document
et Safari sur iPhone restent à évaluer.
