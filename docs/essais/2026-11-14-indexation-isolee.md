# Vérifier l’outil isolé avant l’indexation

**Bilan daté — 0.9.2, 14 novembre 2026.** Suite du diagnostic L1, après
la capture de Marc indiquant 135 archives examinées, zéro article ajouté et
une erreur. Son rapport détaillé n’est pas encore reçu ; aucune cause exacte
de cet incident n’est revendiquée par cette livraison.

## Vérification de l’hypothèse

Les anciens tests lançaient le lecteur avec le Python de développement, qui
contient aussi FastAPI et les dépendances Web. Un environnement neuf sans ces
paquets, contenant uniquement les fichiers installés de `libzim==3.13.1`, a été
créé sur le runner Linux. Le lecteur y crée l’index d’une petite archive réelle
générée : une dépendance Web manquante n’a pas été reproduite.

La nouvelle recette automatisée effectue le même essai sur un chemin contenant
des espaces et accents. Elle vérifie d’abord le refus sans lecteur, puis copie
uniquement la distribution libzim installée, confirme l’absence de FastAPI et
lance la vraie commande d’indexation avec deux processus. Une archive sans index
reçoit son index local, une archive native est réutilisée, puis une relance ne
réécrit pas l’index publié. Aucun paquet, modèle ou corpus lourd n’est téléchargé
par cette recette.

## Correction de la préparation et du diagnostic

- Avant de déclarer une préparation terminée, exécuter dans son propre Python
  un petit contrôle isolé (`-I`) : version de libzim, import et API attendue,
  création/interrogation SQLite FTS5 en mémoire. Le rapport conserve seulement
  versions, architecture, résultat et motif catégoriel, sans chemin privé ni log brut.
- Répéter ce contrôle au début de chaque indexation, avant le pool de processus.
  Il couvre donc aussi les anciens marqueurs « prêt ». Un échec produit un rapport
  à zéro archive parcourue, avec une cause commune, sans répéter la panne 135 fois.
- Conserver les anciens SQLite et leur manifeste. Retirer le marqueur « outil prêt »
  si cette vérification échoue ; le message propose la vérification/réparation
  appropriée. La récupération d’un superviseur interrompu conserve ce diagnostic.
- Distinguer ensuite les erreurs par archive : réserve disque, disque plein,
  fichier absent, accès refusé, source modifiée, SQLite et lecture de l’archive.
  Les anciens types d’erreur restent présents pour compatibilité, sans leur
  message brut. Les erreurs inconnues ne sont pas transformées en disque plein.

Le contrôle ne lit pas le fonds réel, ne certifie pas les archives et ne garantit
pas l’absence d’erreur pendant leur extraction. Une panne SQLite ne se résout pas
forcément par la réinstallation du seul lecteur. La réparation reste explicite,
sans installation système ni téléchargement automatique supplémentaire.

## Vérifications et limites

Tests ciblés locaux : contrôles préalables, préparation, superviseur et reprise,
ainsi que huit essais sur petites archives réelles incluant le nouvel environnement
isolé. Un test simule 135 fichiers avec contrôle préalable en échec : aucun
processus d’extraction ne démarre, les anciens index sont conservés.
La recette navigateur vérifie le message, le bouton de lancement désactivé et
l’export du contrôle préalable. Les 478 tests locaux passent avec trois tests
ignorés. La [CI du code livré](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43623186637),
sur `6c35df8`, réussit ses huit travaux : Linux, Windows Python 3.12, lecture isolée
Windows 3.11/3.13/3.14, Kiwix réel synthétique, calcul de trajet synthétique et
navigation Chromium/WebKit. Les 251 liens locaux des documents modifiés et
`git diff --check` sont vérifiés. Aucun modèle ni fonds réel n’est chargé.
La première recette Windows a échoué dans le décodage de son propre chemin
accentué, avant le lecteur : le mode isolé ignore la variable `PYTHONUTF8`.
La recette et la commande de lancement demandent maintenant explicitement UTF-8.
Cet échec de test n’est pas attribué à la panne réelle de Marc.
La recette suivante a atteint le générateur de fixtures : le créateur ZIM natif
Windows refuse le dossier accentué. Les deux archives sont donc générées dans
un dossier temporaire séparé, puis déplacées par Python vers le chemin accentué
pour éprouver la vraie lecture et l’indexation. SetupSurvie ne crée pas les ZIM
téléchargés ; ce résultat sur leur création ne prouve pas une panne de lecture.

Une fois ces deux obstacles de recette levés, les quatre versions Windows
reproduisent un blocage de la vraie commande dans son environnement isolé.
`index_archives.py` remplaçait l’exécutable des processus par le `pythonw.exe`
du venv. Ce remplacement empêche d’emprunter le démarrage prévu par
[CPython pour les environnements Windows](https://github.com/python/cpython/blob/main/Lib/multiprocessing/popen_spawn_win32.py)
(`bpo-35797`) : les processus fils ne prennent pas le travail et le parent attend.
La correction conserve le choix d’exécutable de Python ; le superviseur garde
son lancement Windows masqué. La recette à deux processus est relancée telle
quelle, sans agrandir le délai ni contourner le dossier accentué. En cas de
dépassement, elle termine seulement son propre arbre de processus de test.
La recette corrigée réussit sur les quatre versions Windows, avec les deux
processus et la réutilisation de l’index. Ce défaut reproduit en CI ne suffit
pas à attribuer l’erreur de Marc sans son rapport.

## Recherche restaurée une seule fois

La recette navigateur a ensuite détecté un message de recherche partielle effacé
par une relance au chargement. Avec la réponse de profil retenue volontairement,
l’essai Playwright reproduit deux demandes avant cette réponse, puis une troisième
après. La restauration automatique attend désormais cette réponse et déclenche
une seule demande avec les filtres mémorisés. Si le profil échoue, le repli anonyme
déclenche quand même la recherche publique. La recette vérifie ces trois cas,
sans supprimer l’avertissement de couverture ni allonger son attente.
Chromium et WebKit passent chacun 48 contrôles de recherche et 16 contrôles de
préparation/indexation, ainsi que les recettes existantes du portail.

**Version corrective 0.9.2** : vérification et diagnostic d’un outil déjà prévu,
sans changement de version de libzim, d’image tierce ni de schéma de données.
Le [guide actuel](../utilisation/indexation-archives.md) décrit les nouvelles causes.
L’incident sur le PC de Marc attend toujours son rapport R1 ; un essai Linux ou
Windows de CI ne constitue pas sa résolution mesurée.
