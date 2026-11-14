# Vérifier l’outil isolé avant l’indexation

**Bilan en cours — 0.9.2, 14 novembre 2026.** Suite du diagnostic L1, après
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
l’export du contrôle préalable. CI finale et nombre de tests à consigner.
Le travail Windows principal couvre Python 3.12 ; une recette isolée supplémentaire
est prévue en CI pour les cibles de kit 3.11, 3.13 et 3.14, sans multiplier toute
la suite applicative. Ces résultats restent à consigner avant publication.

**Version corrective 0.9.2** : vérification et diagnostic d’un outil déjà prévu,
sans changement de version de libzim, d’image tierce ni de schéma de données.
Le [guide actuel](../utilisation/indexation-archives.md) décrit les nouvelles causes.
L’incident sur le PC de Marc attend toujours son rapport R1 ; un essai Linux ou
Windows de CI ne constitue pas sa résolution mesurée.
