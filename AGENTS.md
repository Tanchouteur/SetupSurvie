# Contexte et consignes pour les agents

## Projet et utilisateurs

SetupSurvie est le projet de Louis et Marc Tanchou : un serveur familial de
connaissances et un assistant local, utilisables sans Internet depuis les appareils
du réseau local. Il doit servir en situation de services dégradés (électricité,
approvisionnement, Internet, accès aux professionnels), mais aussi au quotidien et
à l'éducation des enfants. Ne pas supposer qu'une catastrophe a effectivement eu lieu.

La première étape est un pilote accompagné chez Marc pour recueillir des retours.
La vente est un objectif ; ne pas présenter le pilote comme un produit commercial
validé. Les utilisateurs peuvent ne rien connaître à l'informatique ni à l'IA :
privilégier un français simple, une navigation évidente, des erreurs compréhensibles
et une utilisation confortable sur ordinateur et téléphone, notamment Safari iOS.

Le logo feu et livre est dans `assets/branding/`, avec ses variantes dans
`portal/branding/`. Conserver les ajouts de l'utilisateur et lire les nouvelles
documentations avant de modifier le produit. Les noms proposés dans les documents
de branding ne constituent pas une décision de renommage du produit.

## Architecture et points d'entrée

- `portal/` : interface HTML, CSS et JavaScript, servie par Caddy.
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
  Les deux interfaces partagent les comptes mais ont des historiques distincts.
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

Louis : Linux Bazzite, Ryzen 9, RTX 2060 **6 Go**, 32 Go de RAM.
Marc : Windows, RTX 5060 **8 Go**, **32 Go de RAM**. Des GPU plus gros pourront
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
   cohérents la version affichée et les réponses API. Une correction documentaire
   seule ne nécessite pas de changer la version des images tierces.
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

Lire en priorité `README.md`, `docs/README.md`, `docs/decisions/choix-actuels.md`, `docs/installation/pilote-marc.md`,
`docs/essais/bilan-pilote-2026-11-11.md`, `docs/decisions/acces-simple-et-offre.md` et
`docs/bibliotheque/plan-bibliotheque-hors-ligne-500go.md`. Ce dernier est un plan, pas la
preuve que les lots proposés sont téléchargés.

Le pilote 0.1.5 fournit `scripts/content.py` pour les lots figés et
`scripts/pilot_update.py` pour les mises à jour compatibles du code, avec sauvegarde
et retour arrière. Lire `docs/exploitation/mises-a-jour-et-bibliotheque-pilote.md`. Les lots
du plan documentaire ne sont pas tous téléchargés ; les changements d’images et
les migrations de données incompatibles demandent encore une procédure dédiée. Ne pas confondre
le kit hors ligne d'environ 160 Go avec un petit installateur en ligne. Les mises
à jour doivent préserver comptes, conversations, réglages et contenus, avec une
sauvegarde et une restauration vérifiées avant toute migration destructive.
Mettre à jour ces constats à mesure que le travail est réellement validé.

Le pilote **0.1.7** ajoute les cartes PMTiles du Sud (PACA, Occitanie, Corse et
Solliès-Ville) et une recette des sources via scripts/audit_library.py.
Lire docs/essais/bibliotheque-sud-recherche-et-ia.md. scripts/maps.py prépare les
extraits ; scripts/lab_refresh_library.py actualise seulement Kiwix et le pilote.
Pour les services de transfert en arrière-plan, utiliser --no-refresh puis
actualiser séparément. L'indexation du pilote et la recherche Kiwix ne signifient
pas que toutes les archives ont été importées dans les collections Open WebUI.

## Tests dans le runner CPU

Le runner de développement est une petite VM sur CPU. Ne jamais y télécharger
de modèle IA, de corpus, de ZIM ou de carte lourde pour les tests. Utiliser des
fixtures minuscules et des services simulés. Les préparations réelles se font sur
les PC cibles ; le test OSRM réel de la CI GitHub utilise uniquement un petit
réseau OSM synthétique et son image épinglée, sans modèle IA.

## Documents associés et traduction (0.1.16)

Lire `docs/utilisation/documents-et-traduction.md` pour la conservation des associations côté serveur et les traductions privées progressives. Les instantanés, passages et exports ne doivent pas rejoindre le fonds public. La reprise reste explicite après redémarrage et respecte le mode jeu. Les tests simulés ne prouvent pas la fidélité d’un modèle réel. Louis souhaite une référence unifiée et simple à maintenir : `main`, avec suppression des branches temporaires de l’agent après intégration vérifiée.
