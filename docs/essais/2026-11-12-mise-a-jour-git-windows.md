# Mise à jour Git fournie sur Windows — 12 novembre 2026

**Bilan daté — pilote 0.1.21.** Intégration au dépôt du lanceur d’abord créé
localement chez Marc, avec adaptation aux nouvelles installations.

## Livraison

- `Mettre-a-jour-SetupSurvie.cmd` est livré avec les sources et les kits.
- `setup.py` appelle `windows_update.py` lors de la création des raccourcis Windows.
  Le générateur place un second lanceur dans le dossier d’installation et les
  scripts nécessaires dans `maintenance`, hors du logiciel qui sera remplacé.
- Le Bureau reçoit **Mettre à jour SetupSurvie**, pointant vers le script stable.
- Le dossier privé vient des réglages de l’installation, y compris s’il est
  extérieur au dossier applicatif. Python est détecté via les outils portables ou
  les installations usuelles ; aucun chemin propre à Marc n’est imposé.
- Git est ajouté aux prérequis Windows. La référence x64 est épinglée avec son
  SHA-256 issu de l’API officielle Git for Windows. Un Git existant reste conservé.

## Parcours de mise à jour

Le lanceur synchronise `main` dans `maintenance/source`, construit un petit ZIP
local, contrôle son empreinte puis appelle le mécanisme de sauvegarde, remplacement
et retour arrière déjà existant. Il refuse un mauvais dépôt distant, les modifications
locales et les commits non publiés, sans reset ou push.

`-Check` ne remplace pas l’application et une version déjà installée ne redémarre
aucun service. `-Recover` utilise le journal existant et la copie précédente si
le script applicatif est absent. Les fichiers stables sont rafraîchis après une
mise à jour réussie, avec remplacement atomique et sans réécrire inutilement le
fichier `.cmd` en cours d’utilisation.

Les scripts et leur générateur figurent dans les paquets logiciels. Les quatre
lanceurs racine `.cmd` restent exclus de ces paquets pour que le lecteur 0.1.16
les accepte ; ils restent inclus dans les sources et les exports/rafraîchissements
de kits. Le générateur recrée le lanceur stable pour les installations existantes.

## Vérifications et limites

Suite applicative Windows : **196 tests, 190 réussites et 6 ignorés**, sans erreur
ni échec, en environ 73 secondes. Les quatre modules spécifiques au laboratoire
Linux sont exclus de cette recette Windows. Les scénarios PowerShell supplémentaires
passent également. Les tests COM utilisent uniquement des dossiers temporaires.

- Scénarios PowerShell 5.1 : préparation de Git manquant simulée, consultation des
  versions, construction/application simulées, contrôle d’empreinte, dépôt modifié,
  commits locaux et récupération sans application.
- Tests Python : génération et rafraîchissement du lanceur, préservation d’un
  fichier utilisateur homonyme et des données du dépôt de maintenance, installation
  depuis un kit et distribution des scripts/lanceurs.
- Tests réels COM Windows dans des dossiers temporaires : raccourcis, arguments,
  noms distincts entre installations et cible stable hors de l’application.
- UTF-8 explicite pour les réglages et scripts compatibles Windows PowerShell 5.1,
  avec essais de chemins contenant des espaces et accents.

Les tests ne téléchargent ni Git ni modèle ni bibliothèque et ne redémarrent
aucun service installé. L’installation réelle de Git sur un Windows vierge reste
à valider. Les tests du kit utilisent des données minuscules, pas une nouvelle
livraison de la bibliothèque complète. L’installation 0.1.20 de Marc et son
téléchargement ne sont pas remplacés par ces essais.

Le [guide courant de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)
décrit le double-clic et la récupération ; le [guide Windows](../installation/deux-etapes-windows.md)
décrit les prérequis et la première installation.
