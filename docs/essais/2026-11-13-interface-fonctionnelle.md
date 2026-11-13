# Interface fonctionnelle Windows/Linux — 13 novembre 2026

**Bilan daté — 0.1.32.** Voir le [guide actuel](../utilisation/nouvelle-interface.md).

## Périmètre

Après validation de la maquette PC, Louis demande la mise en place normale de la
nouvelle interface, le téléchargement de Marc étant déclaré terminé. L’entrée
principale est la nouvelle présentation ; la classique est conservée séparément
avec ses scripts/styles et les mêmes API. `/nouveau/` est un alias explicite et
`/maquette/` reste une démonstration fictive.

Les contrôles existants sont réorganisés avant le chargement de leurs gestionnaires,
sans deuxième moteur de conversations ni migration. Le générateur
`scripts/build_next_portal.py` produit les deux entrées modernes à partir du
balisage conservé de la classique ; un test contrôle leur cohérence et leurs IDs.
Les nouvelles pages lisent l’inventaire et les profils réels, ouvrent les collections
Kiwix directement, et réutilisent lecture, recherche, favoris, assistant, dictée,
traduction, lieux, réglages et préparations existantes.

Le suivi hôte en lecture seule ne démarre/arrête aucun processus, ne prend aucun
verrou documentaire, ne calcule aucune empreinte de gros fichier et n’ouvre pas
SQLite. Il vérifie identité du processus, association au plan, reçus et date de
progression. Les réponses filtrées ne contiennent ni PID, chemin privé, journal,
erreur fournisseur brute, conversation ni coordonnées personnelles.
Un cache hôte de cinq secondes évite de répéter ces lectures pour chaque navigateur.
Les tailles Windows des partiels sont demandées par handle partagé ; la recette
réelle sur HDD Windows n’est pas remplacée par les fixtures.

## Vérifications

- Tests unitaires du suivi : transfert web/Linux, reprise indépendante Windows,
  poignée de fichier simulée, réutilisation de PID, état inconnu, vieux progrès,
  plan étranger, doublons/empreinte de reçu, vérification et absence de fuite.
- Tests de génération et conservation des contrôles dans les deux interfaces.
- Playwright MCP Chromium : parcours fonctionnel sur le serveur API de fixtures,
  avec vrais documents minuscules et conversations persistées dans la base jetable.
  Les modèles, matériels, transferts et identités de ces essais sont simulés.
- Contrôles : nouvelle interface par défaut, lecture, adresses de document et
  conversation, historique classique partagé, brouillon/rechargement, Retour,
  suivi API, commandes conservées sur ordinateur, refus de préparation concurrente,
  consultation mobile et absence de débordement de 320 à 1440 pixels.
- La recette classique conserve les anciennes campagnes ; la CI les exécute
  désormais explicitement sous `/classique/`, puis exécute la recette moderne
  sous Chromium et WebKit. Les résultats distants doivent être lus sur le commit livré.

La première exécution de la suite retrouvait les six erreurs déjà documentées
en 0.1.31. Les fixtures de test sont corrigées sans modifier les protections du
produit : disque fictif dans les tests de supervision, scripts stables ajoutés au
kit synthétique et assertions de raccourcis adaptées au suivi introduit en 0.1.30.
Le test vérifie toujours que la seconde installation ne modifie aucun raccourci
de la première. Les limites de capacité réelles restent inchangées.

La suite Python complète passe localement : **321 tests, 3 ignorés**, dont les
11 contrôles du moniteur (handle partagé compris). La recette Chromium fonctionnelle passe
avec 26 contrôles. Syntaxe JavaScript, `git diff --check` et construction du
paquet logiciel 0.1.32 sont vérifiés. Une recette supplémentaire vérifie aussi la nouvelle interface avec document
associé et traduction ouverte : restauration, pause/reprise, export et saisie
accessible à 1366×900, 768×900, 390×844 et 320×568. Un conteneur de contexte
défilant empêche le panneau de traduction de pousser le composeur hors écran.
La CI Windows a aussi révélé la différence entre alias 8.3 et chemin long du
répertoire temporaire : les chemins de plan sont désormais normalisés après
refus des composants liés, avant comparaison aux racines autorisées.
Les résultats CI finaux sont consignés avant publication.

## Limites réelles

Aucun déploiement sur le PC de Marc, démarrage d’IA, gros téléchargement ou
modification réseau n’est effectué dans cette livraison de code. La recette
Windows/Linux physique, les usages Kiwix avec grand catalogue et Safari iPhone
restent distincts. Les tests Windows de CI sont des tests de fichiers/processus
et d’installation simulée, pas une installation complète sur PC vierge.

Le suivi lit les preuves déjà enregistrées, sans garantir qu’un fichier vérifié
anciennement est encore présent. Un transfert direct ancien sans métadonnées
ne devient pas observable par supposition. La présence, l’ouverture par Kiwix et
la recherche sont toujours distinctes ; la consommation électrique, la santé
matérielle et la durée restante ne sont pas annoncées sans mesure.
