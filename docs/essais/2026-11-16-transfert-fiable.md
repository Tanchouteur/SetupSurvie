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

Premier passage CI Windows : trois échecs de fixtures, dus à l’alias court
`RUNNER~1` et à une injection d’erreur utilisant un séparateur `/` sur Windows.
Les chemins des fixtures sont normalisés et l’injection utilise les composants
de `Path`. L’adaptateur conserve aussi les alias de chemins source et compare
leur casse selon Windows. Ces échecs sont distincts d’un transfert réel sur SSD.

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

## Résultat CI après correction Windows

Au commit `c9f3789`, les **17 tests de transfert** et les **deux tests Windows de
syntaxe/diagnostic de volumes** réussissent sur le runner Windows GitHub. Le
travail Linux, les lecteurs isolés 3.11/3.13/3.14, Kiwix et le routage réussissent.
Le travail Windows global s’arrête ensuite sur le test existant
`test_kiwix_diagnostic.test_global_budget_stops_following_steps` (deux étapes au
lieu d’une avec des délais réels de 20/30 ms). Aucun moteur de recherche ni ce
test hors périmètre n’a été modifié pour obtenir un passage vert. Ce résultat
n’est donc pas annoncé comme une CI entièrement réussie.

Après le contrôle final de stabilité de l’inventaire : **18 tests ciblés
réussis**, dont un ajout manuel pendant la copie refusé avant publication.
La recette Tk et les quatre ouvertures Chromium/WebKit locales ont été
réexécutées avec succès. La synchronisation du retrait du garde-fou utilise
également `durable.sync_directory` lorsque le système le permet.

## Revue complémentaire avant intégration

Le rejeu indépendant des dix-huit tests ciblés réussit. Deux cas supplémentaires
échouent d'abord : OSRM ne possède pas de HEALTHCHECK Docker dans l'image et le
Compose épinglés, mais la validation l'exigeait pour tous les services ; un retour
à la source pouvait aussi retirer son garde-fou pendant une opération source.

Le contrôle vérifie désormais les quatre services principaux sains, les trois
routeurs attendus en fonctionnement lorsque le graphe est préparé, l'absence de
service manquant ou en double et les montages. Le pilote vérifie ensuite une
réponse `nearest` de chacun des trois moteurs locaux ; aucun serveur distant
n'est utilisé. Un routeur arrêté ou sans graphe exploitable refuse la bascule.

Le retour acquiert les verrous d'opération destination et de maintenance/transfert
source avant de retirer le garde-fou. Un verrou détenu refuse le retour ; aucun
propriétaire inconnu n'est arrêté. Les nouveaux tests vérifient ces deux défauts,
les réponses locales de routage et la copie conjointe des états vidéo 0.26.0 :
base de transcription en pause, IDs, pistes source/française et cache Whisper.

Le test de budget global Kiwix utilise maintenant une horloge contrôlée pour
exercer la même échéance. Il ne repose plus sur un sommeil de 30 ms contre une
limite de 20 ms, sensible à l'ordonnanceur Windows. Aucune limite moteur n'est
modifiée et le contrôle de budget n'est pas retiré. La recette physique chez Marc
et la reconstruction d'un Windows vierge restent non exécutées.
