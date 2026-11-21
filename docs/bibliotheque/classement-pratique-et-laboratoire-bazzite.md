# Guides pratiques et laboratoire documentaire sur Bazzite

**Décision de Louis du 21 novembre 2026 et plan de recette.** La priorité de
la bibliothèque est **Autonomie et résilience**. Louis valide un classement par
rôle des sources, un laboratoire représentant l’installation de Marc sur Bazzite
et un tri initial réglable à partir de son export.

## Ce que montrent les premiers essais

Chez Marc, le filtre « Autonomie et résilience » appliqué à « eau potable »
fait remonter un article sur la salinisation en mer d’Aral, une encyclopédie
et le thésaurus du Wiktionnaire. « Water Purification Systems », provenant
d’iFixit en anglais, apparaît avec l’étiquette Français. La recherche doit
aider à trouver une méthode d’un organisme identifiable et vérifier que le
passage ouvert répond à la question.

Sur l’installation Bazzite en service (0.71.0, fonds réduit), deux pages à
titre anglais de la collection iFixit française arrivent en tête en mode
français. Leurs extraits mêlent les deux langues. Wikilivres propose un
chapitre sur la potabilisation en troisième position.
Le résultat obtenu chez Marc inclut d’autres collections. Les deux relevés
orientent la recette de classement et de filtrage.

## Rôle des sources et tri d’installation

| Rôle | Sources de départ | Usage dans la recherche |
| --- | --- | --- |
| Guide pratique | Fiches OMS, manuels Hesperian, Appropedia, tutoriels iFixit, guides de premiers secours | Candidats à Autonomie et résilience. Vérifier que l’article ou la fiche propose une méthode utile pour la requête. |
| Référence | Wikipédia, encyclopédies | Savoirs et culture et enrichissement de la recherche générale. Un article qui contient une méthode peut être proposé à l’examen humain pour Autonomie. |
| Langue | Dictionnaires et Wiktionnaire | Recherche de définitions et de vocabulaire. |
| Culture | Gutenberg et autres fonds littéraires ou culturels | Consultation culturelle et recherche générale. |

Une page de navigation, un catalogue d’appareils ou une table des matières
peut servir d’accès à la bonne procédure dans une collection pratique.
Les contrôles de recette distinguent ces pages des fiches qui expliquent
quoi faire. Les corrections humaines déjà enregistrées restent prioritaires.

Le fichier [de tri fourni avec l’installateur](../../deploy/collection-sort-default.json)
reprend les 24 collections rangées dans **Autre** et les 20 références exclues
par Louis. Ce réglage initial porte sur les collections et leurs éditions,
langue comprise. Les quatre rôles concernent la nature des sources et
guideront le classement et la recherche. Comparer plusieurs réglages sur le
même fonds et garder un export par configuration mesurée.
[Guide des classements](../utilisation/classement-et-collections.md)

## Fonds comparable sur Bazzite

1. Faire l’inventaire des éditions et des tailles chez Marc à partir d’un
   manifeste ou d’un export d’inventaire. Utiliser les mêmes sources vérifiées
   quand elles tiennent dans le laboratoire. La comparaison porte sur les
   collections et les ressources publiques.
2. Utiliser le montage dédié du SSD de 4 To. Respecter les 600 Go globaux,
   le plafond documentaire de 500 Go et les marges d’indexation. Si le fonds
   complet dépasse la capacité, conserver en priorité les guides pratiques,
   puis prendre des éditions encyclopédiques ou littéraires plus petites.
   Consigner pour chaque écart la collection, l’édition et le volume.
3. Vérifier les fichiers à la copie ou au téléchargement. Recréer le catalogue
   et les index localement. Utiliser des profils d’essai et laisser l’inférence
   en pause jusqu’à sa reprise explicite par Louis.
4. Partager les chemins, ports, moteurs et budgets avec les sessions qui
   travaillent sur Bazzite. Des ports distincts permettent de garder
   l’installation 0.71.0 disponible pendant les comparaisons.

**Démarrage vérifié le 21 novembre.** La session GPT « Installateur Linux et
point de restauration » a confirmé la fin de sa recette en VM. Le montage du
laboratoire a été recréé dans l’image de 590 Go sur le SSD de 4 To.
La copie initiale comprend 18 ressources publiques et 5 343 024 423 octets
vérifiés par SHA‑256, depuis l’installation d’essai Bazzite 0.71.0.
L’ajout des lots pratiques porte le fonds à **100 ressources vérifiées**
(**6 ZIM, 94 PDF**, 10 406 371 992 octets). Le fichier sur les plantes
toxiques reste en attente après interruption et échec de reprise.
L’enrichissement suivant a démarré avec les lots éducatifs et locaux,
Wikilivres et Wikipédia en français et en anglais. Le transfert du
catalogue figé est plafonné à 215 Go documentaires pour cette tranche.
L’[audit de Marc du 13 novembre](../essais/2026-11-13-audit-fonds-marc.md)
recensait 753,34 Go, dont 241,56 Go de Gutenberg et 43,05 Go de jeux de
société Alexandria. Ce fonds historique dépasse à lui seul le plafond
documentaire du laboratoire de 253,34 Go. Ses éditions et les volumes
actuels restent à comparer après le tri de Louis et les téléchargements
ultérieurs. Pour la comparaison, l’inventaire des archives avec tailles
et éditions peut être relevé via le [catalogue local](../utilisation/inventaire-local.md),
sans copier les comptes, vidéos privées ou historiques.

Le portail documentaire 0.76.3 répond sur la boucle locale de Bazzite
(port 18080), avec Kiwix (18081), Open WebUI (13000) et le pilote (18000).
L’installation existante répond sur 8080. Le volume conserve le lanceur de
recette dans `private/demarrer-recherche.py` et son marqueur de pause
d’inférence. Sur Bazzite, après vérification du montage dédié, exécuter
`python3 /run/media/louis/SetupSurvie/private/demarrer-recherche.py`
depuis `/var/mnt/data/AI/.setupsurvie-biblio-code`. Le transfert en cours
se suit avec `systemctl --user status setupsurvie-biblio-enrichissement`
et le catalogue du laboratoire. L’accès SSH distant demande un montage du
volume séparé quand UDisks refuse l’autorisation de la session.

## Mesurer avant chaque changement

Reprendre le [protocole de mesure existant](../essais/mesurer-classement-documentaire.md)
et ajouter un relevé côté portail pour les recherches en français, en anglais
et mixtes. Noter la version, les éditions, le rang, la langue affichée et
la langue du passage lu, les résultats partiels, le délai et la source
réellement ouverte. Mesurer le nombre de requêtes avec un guide pertinent
dans les trois premiers résultats, les résultats sans rapport dans
Autonomie et les erreurs de filtre de langue. Relire les extraits en aveugle
sur un lot réservé avant de retenir un réglage.

| Famille | Trois recherches de départ |
| --- | --- |
| Eau | Eau potable à la maison après une coupure, stockage d’eau, hygiène avec peu d’eau |
| Premiers secours et santé | Premiers secours citoyen, trousse familiale, hygiène en hébergement partagé |
| Alimentation | Aliments après une panne du réfrigérateur, conservation des légumes, cuisiner avec peu d’énergie |
| Abri et risques | Fixation d’une bâche, information officielle en cas d’inondation, préparer le domicile à une coupure |
| Énergie et éclairage | Batterie de secours, besoins électriques du foyer, éclairage sans réseau |
| Agriculture | Semis, arrosage économe, compost |
| Réparation | Crevaison vélo, réparation d’une fermeture, entretien d’une pompe manuelle |
| Communications et orientation | Écouter les informations locales, organiser les contacts d’urgence, lire une carte hors ligne |
| Enseignement | Activité de lecture CP, exercices de mesure, calcul de consommation |
| Témoins de référence | Salinisation de la mer d’Aral, définition de « potable », littérature de Gutenberg |

Étendre la grille à chaque thème actif du catalogue. Pour chaque besoin,
distinguer guide trouvé et lu, guide présent mais difficile à retrouver,
absence de guide dans la langue choisie et absence de source dans le fonds.
La première recette « eau potable » vise la fiche OMS sur le traitement au
point d’utilisation dans les trois premiers résultats en français et anglais,
avec sa langue réelle. En français uniquement, elle doit être filtrée tant
qu’une édition française correspondante manque. Les témoins encyclopédiques
et lexicaux restent accessibles par une recherche plus large.

Comparer dans cet ordre le résultat initial, le rôle des sources et la langue
au niveau des contenus, puis l’ajout de requêtes bilingues et la priorité aux
guides. Faire les ajouts documentaires en fonction des manques observés.
Vérifier provenance, édition, illustrations et droits avant diffusion.
Pour l’assistant, mesurer les documents effectivement ouverts et cités
lorsque Louis autorise l’inférence. Conserver les essais Windows et iPhone
comme validations sur les appareils cibles.

## Premier relevé sur le fonds pratique — 21 novembre 2026

Quatorze recherches API portent sur douze formulations avant modification du
moteur. Le scénario principal confirme que le PDF OMS sur le traitement au
point d’utilisation s’ouvre depuis le portail. La recherche bilingue « eau
potable » renvoie trois pages d’Appropedia dans les trois premiers résultats
et le chapitre Wikilivres arrive dixième. Le PDF attendu ne figure pas dans
les seize résultats rendus. En français, Wikilivres arrive premier. Le
parcours a aussi été ouvert avec Chromium à 1 366 et 390 pixels. Le
portail signalait des index d’archives et de vidéos incomplets lors de cette
recette.

La fiche de premiers secours citoyen arrive deuxième sur sa requête. La
recherche de crevaison renvoie d’abord un tutoriel pour une chambre à air.
« Batterie de secours » commence par le remplacement d’une batterie
d’appareil photo. « Arrosage économe » et « écouter les informations locales »
ne donnent aucun résultat dans Autonomie. Ces constats décrivent ce que la
recherche fait remonter sur le fonds initial. La couverture et la qualité
de chaque guide restent à apprécier après lecture et comparaison des éditions.

### Relevé étendu et premiers correctifs en essai

Le relevé initial a couvert les **38 thèmes** du catalogue, pendant
l’enrichissement. Kiwix servait six ZIM au début et à la fin. Parmi les 32
réponses de recherche partielles, dix requêtes ne renvoyaient aucun résultat.
Six relevés ont dépassé le délai du client de mesure. Ces chiffres décrivent
la recherche sur ce fonds intermédiaire. Ils restent à comparer à ceux du fonds
enrichi, avant de conclure sur les documents manquants.

Sur le scénario bilingue « eau potable », la fiche OMS sur le traitement au
point d’utilisation passe du **12e au 2e rang** lorsque les mêmes 411 candidats
sont reclassés avec la formulation bilingue et la priorité aux guides
documentaires. L’essai isole l’effet du classement. La couverture de la
requête en production et la lecture des résultats sur tous les thèmes
restent à mesurer.

Dans l’archive iFixit anglaise de décembre 2025, le HTML de la page
« Water Purification Systems » indique le français, tandis que le contenu
et le reste de l’édition sont anglais. Le candidat test reconnaît l’anglais
sur le fichier réel et conserve l’indication française sur la page mixte
de l’édition française. Les essais unitaires couvrent le passage dans le filtre
et l’absence de requête Kiwix vers le Wiktionnaire rangé dans Autre.

La recette se rejoue depuis le dépôt avec la liste des 38 thèmes et les
variantes linguistiques du cas OMS.

```sh
python3 scripts/evaluate_domains.py scan-library tests/fixtures/domain-evaluation/autonomie-38-themes.json rapport.json --portal http://127.0.0.1:18080
```

Le rapport conserve la couverture, l’ordre et les titres. Il indique si le
lecteur a renvoyé du texte. L’analyse de la pertinence et la lecture humaine
des passages restent à ajouter. Conserver chaque rapport dans un dossier de
recette hors du dépôt.
