# Contexte et consignes pour les agents

## Démarrage rapide pour un agent

- **Version actuelle** : `VERSION` dans `pilot/app.py` et `deploy/release.json`
  (identiques). Ne pas déduire la version des documents : leurs en-têtes donnent
  la version de leur dernière révision.
- **Trouver le code** : [carte du code](docs/architecture/carte-du-code.md)
  (module → rôle, routes, scripts, configuration).
- **Trouver la doc** : [index général](docs/README.md), puis l’index du dossier
  concerné ; décisions en vigueur dans les [choix actuels](docs/decisions/choix-actuels.md).
- **Lecture ciblée** : ouvrir le guide du sujet traité. Pour l’installation chez
  Marc, partir du [guide du pilote](docs/installation/pilote-marc.md). Pour le
  fonds documentaire, partir de la [préparation du fonds complet](docs/bibliotheque/bibliotheque-complete-marc.md).
  Le [plan des 500 Go](docs/bibliotheque/plan-bibliotheque-hors-ligne-500go.md)
  décrit les lots envisagés pour le laboratoire. Le [premier bilan du pilote](docs/essais/bilan-pilote-2026-11-11.md)
  sert de repère historique. Pour les arbitrages produit, consulter
  [l’offre](docs/decisions/acces-simple-et-offre.md) et la [feuille de route](docs/decisions/feuille-de-route-v1.md).
- **Interface** : modifier `portal/interface/modele.html` et les scripts ;
  incrémenter le paramètre `?v=` d’un fichier modifié là où il est déclaré
  (`modele.html` ou la liste ordonnée de `scripts/build_portal.py`), puis
  régénérer `portal/index.html` avec `python3 scripts/build_portal.py`.
- **Tests** : voir « Vérifications et suivi » ; la CI est `.github/workflows/tests.yml`.

## Projet et utilisateurs

SetupSurvie est le projet de Louis et Marc Tanchou : un serveur familial de
connaissances et un assistant local, utilisables sans Internet depuis les appareils
du réseau local. Il doit servir en situation de services dégradés (électricité,
approvisionnement, Internet, accès aux professionnels), mais aussi au quotidien et
à l'éducation des enfants. Ne pas supposer qu'une catastrophe a effectivement eu lieu.

La première étape est un pilote accompagné chez Marc pour recueillir des retours.
La vente est un objectif ; ne pas présenter le pilote comme un produit commercial
validé. Louis précise le 16 novembre 2026 que le code propre de SetupSurvie n'est
pas publié en open source et que l'offre visée est la vente d'un PC avec
SetupSurvie préinstallé. Distinguer la préparation avant livraison du parcours
client ; ne pas supposer que celui-ci installe et assemble les services. Lire
`docs/decisions/acces-simple-et-offre.md` ; les composants tiers gardent leurs
licences et aucun tarif ou service après-vente n'est déduit de cette orientation.
Les utilisateurs peuvent ne rien connaître à l'informatique ni à l'IA :
privilégier un français simple, une navigation évidente, des erreurs compréhensibles
et une utilisation confortable sur ordinateur et téléphone, notamment Safari iOS.

Le logo feu et livre est dans `assets/branding/`, avec ses variantes dans
`portal/branding/`. Conserver les ajouts de l'utilisateur et lire les nouvelles
documentations avant de modifier le produit. Les noms proposés dans les documents
de branding ne constituent pas une décision de renommage du produit.

## Architecture et points d'entrée

- `portal/` : interface HTML, CSS et JavaScript, servie par Caddy.
  Pour toute modification de l’interface, consulter le [guide de design](docs/architecture/guide-design.md).
  Interface unique depuis 0.63.0 : `portal/index.html` est généré par
  `scripts/build_portal.py` à partir de `portal/interface/modele.html` ; ne pas
  l’éditer à la main. `/classique/` et `/nouveau/` ne sont que des redirections.
- `pilot/` : passerelle FastAPI, comptes, conversations, outils documentaires,
  recherche, inventaire local et monitoring.
- `deploy/assistant-system.fr.txt` : contexte produit transmis à l'assistant.
  `pilot/engine.py` ajoute les consignes d'outils, l'historique et les extraits lus.
  Ce contexte est distinct des instructions de l'agent de développement.
- `deploy/model-profiles.json` : profils, modèles et limites de contexte.
  Les modes conseillés sont « réponse rapide », « réponse moyenne » et
  « réponse approfondie ». Conserver les choix supplémentaires pour les essais
  de Marc ; ne pas choisir les gagnants selon la seule taille des modèles.
- Open WebUI conserve les comptes natifs, dossiers et conversations avancées.
  Depuis 0.1.29, les deux interfaces reprennent le profil librement choisi, sans mot de passe ; leurs historiques restent distincts.
  Conserver un lien visible vers Open WebUI.
- Kiwix sert les archives ZIM illustrées ; les guides sont également indexés par
  le pilote. La bibliothèque doit rester accessible quand le moteur IA est arrêté.
- `scripts/setup.py`, les lanceurs PowerShell et `compose*.yaml` : installation
  portable Windows/Linux. `scripts/linux_lab.py` et `scripts/lab.sh` : laboratoire
  Podman propre au PC de Louis ; ne pas en faire une dépendance des clients.
- `scripts/pilot_kit.py` : export et installation du kit hors ligne.
  `scripts/pilot_backup.py` : sauvegarde des états et réglages privés.
- `deploy/versions.json` : références figées des composants tiers et des caches.
  Ne pas changer leurs versions ou empreintes sans vérification réelle.

Ports par défaut : portail HTTP `8080`, Open WebUI `3000`, Kiwix `8081` ; HTTPS
local `8443`, `8444`, `8445`. Le nom demandé est **`survie.local`**, sans prénom.
Le nom mDNS dépend du réseau et du système : conserver l'accès par IP et QR code.
Ne pas annoncer une résolution du nom validée sans l'avoir testée sur le client.
Les API Ollama `11435` et de contrôle `11436` ne doivent pas être exposées aux lecteurs.

## Matériel, stockage et données privées

### Accès des agents Happier au PC de Louis — 17 novembre 2026

Louis autorise les agents du runner Happier sur Coolify (`192.168.1.40`) à
développer et tester sur son PC Bazzite (`192.168.1.171`) : `ssh bazzite` pour
le compte louis, `ssh bazzite-root` pour l'administration complète. Ces alias
sont installés dans le runner, pas implicitement dans chaque autre environnement.
Les transferts et tunnels TCP/sockets Unix ont été testés ; consulter la
[référence Nexus](https://github.com/Tanchouteur/Nexus/blob/main/infrastructure/runbooks/happier-bazzite.md)
pour les commandes, la portée et la révocation. Le socket Podman général du PC
n'est pas le laboratoire : conserver `scripts/lab.sh`, les contrôles de montage,
les limites SSD et le respect du mode jeu. Préserver les travaux locaux et les
applications ouvertes. Cet accès concerne les agents de développement ; il
n'ajoute aucun outil ni privilège à l'assistant du portail.

La [configuration matérielle cible](docs/installation/configuration-materielle-cible.md)
rassemble les orientations de Louis du 16 novembre 2026 et les observations à
compléter. La cible future reste distincte des machines observées ci-dessous ;
le processeur n’est pas encore choisi. Mettre cette référence à jour avec les
nouveaux bilans matériels, sans convertir une hypothèse en résultat validé.

Louis : Linux Bazzite, Ryzen 9, RTX 2060 **6 Go**, 32 Go de RAM.
Marc : Windows, RTX 5060 Ti **8 Go**, **32 Go de RAM** (GPU détecté dans les
rapports du 14 novembre 2026, auparavant noté RTX 5060). Des GPU plus gros pourront
suivre. Les mesures Linux ne prédisent pas les performances Windows de Marc.

Sur le PC de Louis, toute donnée volumineuse doit rester sur le SSD de 4 To,
avec un plafond total de **600 Go** et un nettoyage simple. Le laboratoire utilise
`/var/mnt/data/AI/SetupSurvie/storage.img`, de 590 milliards d'octets, monté sur
`/run/media/louis/SetupSurvie`. Respecter les contrôles de montage et capacité de
`linux_lab.py` ; ne pas télécharger dans un point de montage absent ni utiliser
le stockage Podman par défaut sur le disque système.

Louis a confirmé le **12 novembre 2026** : aucun plafond documentaire logiciel chez Marc ; le laboratoire peut conserver un fonds réduit. Le téléchargement complet se prépare directement chez Marc sans imposer sa réplication au laboratoire. Lire `docs/bibliotheque/bibliotheque-complete-marc.md`.

Dans le laboratoire, les **500 Go documentaires** excluent les modèles et caches
d'essai ; le kit ne compte pas deux fois les mêmes documents. Le plafond
physique du laboratoire et sa marge libre restent distincts et obligatoires.

Respecter le marqueur `private/inference-paused.json` et les demandes de mode jeu.
Ne pas lancer de LLM, benchmark ou action de démarrage forcé tant que la pause
n'a pas été explicitement levée. Les tests unitaires simulés restent possibles.
Ne pas arrêter les applications de l'utilisateur pour gagner de la VRAM.

Ne jamais versionner modèles, ZIM, caches, images de conteneurs, sauvegardes,
comptes, conversations, mots de passe, jetons ou clés privées. Les gros contenus
restent séparés du code, transférables ou téléchargeables. Ne pas afficher les
secrets pendant les diagnostics. Préserver les données utilisateur à chaque
installation, récupération de compte, mise à jour et restauration.

## Bibliothèque, assistant et qualité

La bibliothèque doit couvrir les besoins pratiques : eau, alimentation, santé,
abri, agriculture, énergie, réparation, communications et enseignement familial.
Wikipédia seul et les fixtures de démonstration ne constituent pas un corpus
pratique suffisant. Ne pas confondre un document téléchargé, indexé, trouvé et lu.
Les réponses doivent citer les sources réellement consultées et signaler les
informations manquantes ; ne pas inventer de document ou d'outil disponible.

L'assistant du portail a des outils de recherche, lecture, calcul et conversion.
Il n'a pas implicitement Internet, le calendrier, les fichiers du PC ni les outils
de Codex. L'éducation doit s'adapter à l'âge et au niveau, avec explications et
exercices. Ne pas certifier la potabilité, la sécurité d'une construction ou une
conduite médicale sur la seule base d'une réponse du modèle.

Vérifier provenance, édition, intégrité, illustrations et conditions de
redistribution commerciale des contenus. Un accès public n'autorise pas forcément
leur revente. Documenter les lacunes et les droits restant à examiner.

## Git et versions

1. Avant de coder, lire `git status`, identifier la branche et synchroniser avec
   `git pull --ff-only`. Si des modifications locales empêchent la synchronisation,
   préserver le travail et examiner le distant avec `git fetch` ; ne pas utiliser
   de reset, stash ou écrasement automatique pour forcer le passage.
2. Incrémenter la version du logiciel pour chaque livraison fonctionnelle ; garder
   cohérents la version affichée et les réponses API. Choisir logiquement le niveau
   dans `x.y.z` selon la portée de la livraison, sans incrémenter systématiquement
   `z` : `z` pour une correction compatible, `y` pour une nouvelle fonctionnalité
   compatible ou une évolution fonctionnelle significative, `x` pour une rupture
   de compatibilité majeure ou le passage assumé à une version stable `1.0.0`.
   Lorsqu'un niveau augmente, remettre les niveaux inférieurs à zéro. Tant que le
   projet reste en `0.y.z`, utiliser aussi `y` pour les ruptures de compatibilité
   et les documenter explicitement ; ne pas annoncer une version stable sans
   validation correspondante. Justifier le niveau choisi dans le bilan de livraison.
   Une modification des seules consignes ou de la documentation ne change ni la
   version du logiciel ni les versions des images tierces. Ne pas renuméroter les
   anciennes livraisons pour appliquer cette règle rétroactivement.
3. Vérifier les fichiers inclus, les secrets et les gros fichiers, puis créer des
   commits explicites et pousser la branche concernée. Louis demande que le travail
   soit commité et poussé ; ne pas laisser des changements terminés uniquement en
   local. Sur une nouvelle branche, utiliser le préfixe `codex/`.
4. Ne jamais forcer un push ou réécrire l'historique partagé. Préserver les commits
   de l'utilisateur, notamment ceux du logo et de la documentation.
5. Vérifier que le commit est présent sur le distant et annoncer la branche,
   le commit, les vérifications effectuées et les limites restantes.

## Documentation : organisation et maintenance

- Partir de `docs/README.md` pour trouver les guides de référence. Classer les
  documents par usage : utilisation, installation, exploitation, architecture,
  bibliothèque, décisions, essais et historique. Le README racine reste une
  présentation courte avec les parcours essentiels ; éviter d’y accumuler les
  comptes rendus de livraison.
- Pour chaque changement de comportement, commande, configuration, prérequis ou
  procédure, mettre à jour dans la même livraison le guide de référence concerné
  et ses renvois. Réviser aussi les choix actuels et l’architecture si nécessaire.
  Ne pas laisser une nouvelle procédure uniquement dans un bilan de livraison.
- Consigner toute décision durable prise avec Louis dans le document de référence
  concerné, même sans développement immédiat, avec sa date, son auteur, son contenu
  et ses conséquences. Distinguer une décision confirmée d’une proposition de
  l’agent. Si elle remplace une décision antérieure, conserver celle-ci et indiquer
  ce qui la remplace. Mettre à jour les choix actuels et les renvois utiles, puis
  commiter et pousser conformément aux règles Git ci-dessus.
- Indiquer le statut des documents : guide actuel, plan/proposition, bilan daté
  ou archive. Distinguer prévu, implémenté, téléchargé, indexé et réellement testé.
  Préciser les validations non exécutées, les machines et les limites restantes.
- Conserver les anciens bilans, décisions et sources avec leur date et leur
  contexte. Ajouter une note de remplacement ou un lien vers la référence actuelle
  lorsqu’une ancienne affirmation devient trompeuse ; ne pas réécrire un résultat
  historique comme si un nouvel essai avait eu lieu.
- Après création, déplacement ou renommage d’un document, actualiser l’index et
  les liens Markdown, chemins cités dans les consignes et renvois des scripts.
  Vérifier les cibles locales et les ancres ; conserver la correspondance des
  anciens chemins dans `docs/historique/README.md` lors d’un reclassement.
- Ne pas empiler de journal de livraison en tête de `docs/README.md`, du README
  racine ou des choix actuels : mettre à jour le guide de référence, inscrire le
  bilan daté dans `docs/essais/README.md` et, pour un module ou script ajouté,
  renommé ou supprimé, la [carte du code](docs/architecture/carte-du-code.md).
- Une réorganisation documentaire seule ne change ni la version du logiciel ni
  les références des composants tiers. Ne pas toucher aux changements de code
  en cours pour faire correspondre artificiellement la documentation.

## Vérifications et suivi

Tests automatisés : `python3 -m unittest discover -s tests -v`. Le Python choisi
doit disposer des dépendances FastAPI/httpx du service. Le test Compose a besoin
de `docker compose config`, qui ne démarre pas les services. Ne pas installer
globalement des dépendances sur Bazzite pour exécuter les tests ; utiliser un
environnement isolé sur le SSD ou l'image du service. Ne pas donner à un conteneur
de test les secrets, la VRAM ou les données réelles s'il n'en a pas besoin.

Exécuter les tests adaptés, `git diff --check`, et des essais de navigation pour
les changements d'interface. Une émulation WebKit ne remplace pas un essai réel
sur iPhone. Distinguer tests unitaires, essais Linux, essais Windows et validations
hors ligne ; ne pas présenter un résultat non exécuté comme acquis.

## Tests dans le runner CPU

Le runner de développement est une petite VM sur CPU. Ne jamais y télécharger
de modèle IA, de corpus, de ZIM ou de carte lourde pour les tests. Utiliser des
fixtures minuscules et des services simulés. Les préparations réelles se font sur
les PC cibles ; le test OSRM réel de la CI GitHub utilise uniquement un petit
réseau OSM synthétique et son image épinglée, sans modèle IA.

## Règles par domaine fonctionnel

Règles durables issues des livraisons ; la version indique leur origine, pas une
limite de validité. Le guide cité en tête de chaque règle est la référence.

### Installation et mise à jour Windows (depuis 0.1.17 et 0.1.21)

Lire `docs/installation/deux-etapes-windows.md`. Le lanceur unique `Installer-SetupSurvie.cmd`
(0.1.20), les deux anciens lanceurs racine et leur
catalogue d’installateurs doivent rester inclus dans les exports et rafraîchissements
de kit. Les mises à jour transportent les scripts d’installation mais excluent les
fichiers racine `.cmd`, refusés par la liste autorisée des lecteurs 0.1.16.
La reprise d’une première installation est explicite et
refuse les sources/options modifiées ; elle ne remplace pas la mise à jour d’une
installation terminée. Le kit système hors ligne et la recette Windows réelle
restent à réaliser. Le diagnostic réel sur le PC Windows de Marc, les conflits
avant copie et les raccourcis isolés sont testés ; voir `docs/essais/2026-11-12-installateur-windows-simple.md`.
Ne pas arrêter l’installation en service pour la recette. Aucun téléchargement lourd ni installation système dans le runner.

Depuis **0.1.21**, `scripts/windows_update.py` prépare le lanceur de mise à jour
stable dans le dossier d’installation et `scripts/update-windows.ps1` synchronise
un dépôt Git de maintenance séparé avant d’appeler `pilot_update.py`. Le raccourci
de mise à jour et Git font partie des nouvelles installations. Préserver les
quatre lanceurs racine dans les kits ; les exclure des paquets logiciels compatibles
avec les lecteurs 0.1.16. Les scripts et le générateur restent dans ces paquets.
Ne jamais remplacer une application par un simple pull dans son dossier actif.

### Mises à jour et lots de contenus (depuis 0.1.5)

Depuis le pilote 0.1.5, `scripts/content.py` sert aux lots figés et
`scripts/pilot_update.py` aux mises à jour compatibles du code, avec sauvegarde
et retour arrière. Lire `docs/exploitation/mises-a-jour-et-bibliotheque-pilote.md`. Les lots
du plan documentaire ne sont pas tous téléchargés ; les changements d’images et
les migrations de données incompatibles demandent encore une procédure dédiée. Ne pas confondre
le kit hors ligne d'environ 160 Go avec un petit installateur en ligne. Les mises
à jour doivent préserver comptes, conversations, réglages et contenus, avec une
sauvegarde et une restauration vérifiées avant toute migration destructive.
Mettre à jour ces constats à mesure que le travail est réellement validé.

### Cartes du Sud et recette des sources (depuis 0.1.7)

Le pilote **0.1.7** ajoute les cartes PMTiles du Sud (PACA, Occitanie, Corse et
Solliès-Ville) et une recette des sources via scripts/audit_library.py.
Lire docs/essais/bibliotheque-sud-recherche-et-ia.md. scripts/maps.py prépare les
extraits ; scripts/lab_refresh_library.py actualise seulement Kiwix et le pilote.
Pour les services de transfert en arrière-plan, utiliser --no-refresh puis
actualiser séparément. L'indexation du pilote et la recherche Kiwix ne signifient
pas que toutes les archives ont été importées dans les collections Open WebUI.

### Coupures et reprise (depuis 0.1.23)

Lire `docs/exploitation/coupures-et-redemarrage.md`. Les fichiers `.lease` des verrous
OS restent présents : ne pas les supprimer ni contourner un propriétaire inconnu.
Utiliser `pilot/durable.py` pour les publications critiques et synchroniser les
copies avant de valider le journal. Le démarrage refuse une mise à jour inachevée ;
sa récupération est explicite. Les tests tuent seulement nos processus jetables,
sans Docker réel ni arrêt du PC, et ne prouvent pas la tenue physique du stockage.

### Profils locaux (depuis 0.1.29)

Louis demande explicitement l’absence de mot de passe et de code de secours.
Lire `docs/utilisation/profils-locaux.md`. Les profils rangent les données sans
protéger leur confidentialité entre utilisateurs du réseau. Préserver les IDs
importés et les anciens historiques. Famille donne accès aux réglages et peut
être choisi librement. Ne pas réintroduire de connexion dans le portail ou les
cartes. Open WebUI utilise les en-têtes de profil fournis par Caddy sur 3000/8444 ;
ne pas publier son port interne. Les clés natives existantes restent internes.
Vérifier changement de profil, onglets périmés, dictée et repli documentaire.
Le laboratoire a une commande `refresh-access` qui recrée seulement les deux
services Web sans relancer l’IA ni supprimer les volumes.

### Sources et fiabilité (depuis 0.1.18)

Lire `docs/utilisation/sources-et-fiabilite.md` et `docs/essais/protocole-fiabilite-ia.md`.
Ne pas confondre date du document, édition, collecte et date du catalogue Kiwix.
`guide_dates` complète les anciennes métadonnées sans changer les cinq colonnes
de `guide_meta` ; conserver la compatibilité et les anciennes conversations.
Les fixtures de fiabilité sont fictives et réservées à une installation d’essai.
Les tests simulés et la préparation des scénarios ne valident pas les modèles réels.

### Savoirs durables (depuis 0.1.19)

Lire `docs/bibliotheque/savoirs-durables.md`, référence unique des besoins de Marc.
Thèmes et parcours partagent `deploy/kiwix-themes.json` ; préserver son montage
dans le pilote portable et le laboratoire. La grille repère des références et
des besoins à examiner, sans certifier la couverture. Les tests restent sur
fixtures ; les gros contenus se préparent sur les PC cibles.

### Documents associés et traduction (depuis 0.1.25)

Lire `docs/utilisation/documents-et-traduction.md` pour les associations, favoris personnels et traductions progressives. Louis autorise les nouvelles traductions terminées dans les documents locaux partagés ; les anciennes restent privées jusqu’à publication explicite. Les instantanés sources, brouillons, conversations et exports restent privés. Préserver les documents publiés après suppression de conversation. Les fonctions optionnelles doivent échouer localement, sans bloquer recherche, lecture ou conversations ; conserver le repli statique `/secours.html`. La reprise reste explicite après redémarrage et respecte le mode jeu. Les tests simulés ne prouvent pas la fidélité d’un modèle réel. Louis souhaite une référence unifiée et simple à maintenir : `main`, avec suppression des branches temporaires de l’agent après intégration vérifiée.

### Contrôles de traduction (depuis 0.1.28)

Lire le guide documentaire avant de changer les seuils et unités de
`pilot/translation_quality.py`. Les anomalies bloquantes ne doivent jamais être
comptées comme passages traduits ou publiées. Conserver source, rapport versionné,
proposition refusée et avertissements ; aucune validation automatique du sens
n’est revendiquée. Les anciens passages restent sans contrôle enregistré. La
comparaison et les propositions refusées restent privées ; les avertissements
suivent les traductions partagées et exports. Ne pas relancer d’inférence réelle
pour un test dans le runner CPU.

### Disque de secours complet et documentation humaine (protocole du 13 novembre 2026)

Lire `docs/exploitation/disque-de-secours-hors-ligne.md` avant de modifier export, sauvegarde, réparation ou restauration. Louis demande une copie sur un autre disque physique couvrant l’installation réelle complète, ses prérequis Windows/Linux et ses ressources, pour reconstruire un autre PC sans Internet ni accès au disque source. La documentation doit être compréhensible par un humain sans IA ni portail ; `docs/exploitation/manuel-de-secours.md` est le premier guide actuel. Le protocole définit les états vérifiables, la conservation de la dernière copie saine, l’adaptation entre systèmes et la recette humaine. Il reste un plan : ne pas annoncer un installateur autonome, une documentation exportée complète ou une restauration intersystèmes validés avant réalisation et essais. Préserver la séparation entre kit public et données personnelles ; le fonds de Marc n’est pas plafonné par celui du laboratoire. Une formalisation documentaire seule ne change pas la version logicielle.
