# Transfert fiable : vérifications et limites

**Bilan daté du 16 novembre 2026 — branche `codex/transfert-fiable`, intégration
sur main et version finale en attente de coordination avec le chantier vidéo.**
Le [guide utilisateur](../exploitation/transfert-installation.md) fait référence.

## Résultats locaux

Petites fixtures dans le runner CPU, aucun téléchargement de modèle, carte ou
corpus, aucune inférence. Les tests `tests/test_transfer.py` exercent :

- arrêt brutal de notre processus jetable puis reprise avec fichiers publiés
  réutilisés ; partiels comparés avant ajout ; disque plein simulé ;
- refus de destination existante, chevauchement et lien ; corruption de copie
  et incohérence de clés étrangères SQLite ; source changée depuis le gel ;
- conservation d’identifiants de profil, favoris, base d’index inchangée et
  dates nanosecondes disponibles sur le système ; chemin avec espaces/accents ;
- SQLite WAL actif et WAL laissé par un processus terminé brutalement : données
  validées retrouvées sans connexion encore ouverte à la source ;
- adaptation interrompue puis reprise ; déplacement supplémentaire de la copie
  avant activation ; activation échouée, garde-fou conservé puis reprise ;
- refus de montage extérieur et retour à la source depuis une copie qui ne
  contient pas encore le runtime destination.

Les services et leurs échecs sont **simulés** dans ces tests : ils ne valident pas
Docker Desktop ni le démarrage réel du site Windows. Le contrôle de corruption
refuse la reprise ; il ne répare pas le fichier défectueux et garde le diagnostic.

La première suite globale a révélé quatre fixtures omettant le nouveau script
PowerShell, corrigées dans la même livraison. Un passage lancé pendant les
éditions a aussi mélangé une ancienne fixture à un processus enfant rechargeant
le code modifié ; le passage final doit être exécuté sur code figé.

Suite générale sur code figé : **828 tests, aucun échec, 16 ignorés** sous Python 3.13 dans un environnement isolé. Après adaptation du choix du Python portable, les tests ciblés de transfert sont réexécutés. Le paquet logiciel de recette est construit avec la liste racine historique ; ce paquet de développement ne constitue pas une livraison numérotée à installer chez Marc.

## Interface locale et guide hors ligne

Tk n’est pas disponible dans le runner actif ni sur le R7 : la vérification R7
s’est limitée à cette disponibilité, sans démarrer de service ni d’IA.
Une image de test isolée, fondée sur Playwright 1.58.2 Noble avec `python3-tk`,
a servi à exécuter `tests/transfer_ui_smoke.py` sous Xvfb : fenêtre réelle,
sept actions, tâche en arrière-plan et fin d’opération réussies, réseau désactivé.
Cette image n’est ni un composant livré ni une modification du runner.

Le MCP Playwright refuse le protocole `file:`. Le test du manuel local a donc
été exécuté avec Playwright dans le conteneur TEST, sans modifier cette règle.
`tests/transfer_browser_smoke.js` vérifie Chromium et WebKit à 390 et 1 280 pixels :
guide lisible, aucun débordement horizontal et **zéro requête HTTP/HTTPS**.
Une émulation WebKit ne valide pas Safari sur iPhone.

Reproduction des deux recettes graphiques : image de test avec Python/Tk, Xvfb,
Node et Playwright 1.58.2 ; monter uniquement le worktree en lecture seule,
écrire les fixtures dans `/tmp`, désactiver le réseau. Commandes internes :

```text
xvfb-run -a python3 tests/transfer_ui_smoke.py
node tests/transfer_browser_smoke.js
```

Le test Node attend le paquet Playwright sous `/opt/transfer-test/node_modules`.
Aucun accès Docker, secret ou état réel n’est monté dans ce conteneur.

## Recette Windows restant à réaliser chez Marc

1. Relever version installée, lettres des volumes, disque physique, type du
   volume destination, place libre, emplacement Docker actif et démarrage choisi.
2. Conserver un compte rendu privé avant transfert : nombres de profils,
   conversations, favoris, travaux et index ; choisir les documents à ouvrir.
3. Appliquer la livraison intégrée, lancer le parcours graphique, puis exercer
   une interruption volontaire sur une petite copie de test distincte avant
   l’opération volumineuse. Ne pas interrompre une installation de prérequis.
4. Contrôler source arrêtée, montages destination, recherche, documents originaux,
   vidéos, cartes, profils, historique et travaux en pause. Exporter le rapport.
5. Redémarrer Windows, couper Internet en gardant le LAN, essayer depuis un
   téléphone réel et vérifier le retour à la source sur une copie de recette.
6. Comparer ensuite les mêmes recherches sur HDD/SSD à version, fonds et contexte
   identiques ; aucune amélioration chiffrée n’est affirmée avant ces mesures.

Les tests PowerShell du diagnostic de volumes et de syntaxe sont ajoutés à la
CI Windows. Une réussite de cette CI ne vaut pas transfert réel de Marc.
Le cache d’installateurs ne couvre pas encore tous les prérequis d’un PC vierge.
La restauration Windows/Linux croisée est refusée. Le disque SSD de travail ne
remplace pas une sauvegarde séparée et débranchée.
