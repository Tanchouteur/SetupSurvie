# Installation neuve et transfert entre SSD sur Bazzite

**Statut : protocole préparé le 17 novembre 2026.** Voir le [bilan de
l’installation neuve](2026-11-17-installation-neuve-bazzite.md) et le
[journal du transfert réel](2026-11-18-transfert-ssd-bazzite.md).
Demande de Louis du même jour : installer SetupSurvie **de zéro** sur son PC
Bazzite, avec téléchargement de la bibliothèque, des cartes et des modèles,
noter et corriger chaque problème, puis transférer l’installation d’un SSD à
l’autre, sans dépasser **300 Go** (le SSD système ne doit pas être surchargé),
et enfin tout nettoyer. Aucun code n’est modifié à ce stade ; le protocole vaut
pour le projet en général et sera exécuté sur la version de `main` du jour de
l’essai. Il s’inscrit dans la [feuille de route V1](../decisions/feuille-de-route-v1.md)
(V1-D01, V1-D02) et le [protocole de secours](../exploitation/disque-de-secours-hors-ligne.md).

> Ce scénario est distinct du laboratoire Podman (`scripts/lab.sh`). Le
> 17 novembre, Louis avait d’abord demandé de terminer l’objectif assistant avant
> une installation neuve ; la présente demande ouvre ce chantier, sans
> annoncer de résultat.

## 1. Machine observée (lecture seule, 17 novembre 2026)

| Élément | Observation |
| --- | --- |
| Système | Bazzite 45 (`bazzite-nvidia-open`, image du 12 novembre), système immuable rpm-ostree |
| GPU / RAM | RTX 2060 6 Go (≈ 1 Go utilisé au relevé) ; 32 Go de RAM, zram 15 Go |
| SSD système | Samsung 990 PRO 1 To, btrfs, `/var` et `/var/home` : **≈ 866 Go libres** |
| SSD données | Crucial P3 Plus 4 To, btrfs, `/var/mnt/data` : ≈ 2,6 To libres ; contient l’image du laboratoire `storage.img` de **590 Go** (plafond SetupSurvie de 600 Go sur ce disque) |
| Outils présents | Docker 29.9.3 rootless dans `~/bin` (service **inactif**), Docker Compose 5.7.1, `nvidia-ctk`, Python 3.15.2, Git, Podman 6.1.3 ; pas d’Ollama natif |
| Accès agent | `ssh bazzite` / `ssh bazzite-root` depuis le runner ([référence Nexus](https://github.com/Tanchouteur/Nexus/blob/main/infrastructure/runbooks/happier-bazzite.md)) |

Ces relevés seront refaits au début de l’essai ; l’espace libre peut avoir changé.

## 2. Objectif et règle de réussite

1. Installer SetupSurvie par le parcours Linux normal (`scripts/install.sh`),
   comme sur un PC neuf, sans réutiliser le laboratoire ni ses données.
2. Télécharger un fonds réduit, les cartes et les modèles conseillés, puis
   indexer, dans une limite **de 300 Go tout compris** (documents, cartes,
   modèles, images de conteneurs, index, caches, marge temporaire).
3. Vérifier le fonctionnement : portail, recherche, lecture, assistant,
   traduction courte, cartes et itinéraires, accès depuis un téléphone.
4. Transférer avec `scripts/transfer.py` (copy → prepare → verify → activate)
   vers l’autre SSD, puis vérifier la destination après redémarrage, source
   rendue inaccessible et Internet coupé.
5. Nettoyer entièrement et revenir à l’état initial du PC.

**Réussite** : chaque étape a une preuve datée ; chaque problème rencontré est
dans le journal (section 7) avec sa cause, sa correction et l’essai rejoué.
Un problème contourné à la main sans correction du produit reste **ouvert**.

## 3. Décisions à obtenir avant de commencer

**Réponses de Louis du 17 novembre 2026 :** Q1 accepté — plafond SetupSurvie du
SSD 4 To porté à **900 Go** pendant l’essai ; Q2 sens validé (SSD système → SSD
4 To) ; Q3 Docker rootless dédié validé ; Q4 Louis ne prévoit pas de jouer dans
les jours à venir (le marqueur de pause reste à vérifier avant chaque essai IA) ;
Q5 fonds réduit validé. Q6 à Q8 restent des propositions. Louis demande de
**ne rien lancer** et de commencer par préparer l’[ingénierie de tests](ingenierie-de-tests.md),
qui utilisera cette installation comme banc d’essai.


| N° | Question | Proposition de l’agent |
| --- | --- | --- |
| Q1 | **Plafond du SSD 4 To** : le laboratoire occupe déjà 590 Go sur 600 Go. Une installation ou une copie de 300 Go sur ce disque dépasse la règle | Autoriser un dépassement **temporaire** jusqu’à 900 Go pendant l’essai, dans un dossier séparé, supprimé au nettoyage. Sinon, impossible de transférer vers ce disque |
| Q2 | **Sens du transfert** | Installer sur le **SSD système** (cas d’un PC neuf à un seul disque, Docker à son emplacement par défaut), puis transférer vers le **SSD 4 To** (cas de Marc qui ajoute un disque). Le sens inverse reste possible |
| Q3 | **« De zéro » et Docker** : utiliser le Docker rootless existant de Louis ou un démon dédié | Démon Docker rootless **dédié à l’essai** (socket et `data-root` propres), pour ne rien mélanger avec les conteneurs de Louis et tout supprimer ensuite. Le pilote NVIDIA de l’image Bazzite est considéré comme prérequis système déjà présent |
| Q4 | **Mode jeu et IA** : quand l’agent peut-il charger un modèle sur la RTX 2060 ? | Téléchargements et indexation autorisés à tout moment ; essais IA seulement sur créneaux donnés par Louis, pause respectée sinon |
| Q5 | **Contenu du fonds réduit** | Catalogue sans Wikipédia anglais (127 Go) : ≈ 73 Go de documents, + cartes Sud, + modèles `gpt-oss:20b` et `gemma4:e4b`, + Whisper small |
| Q6 | **Laboratoire existant** pendant l’essai | Le laisser démonté et arrêté pour éviter les conflits de ports et de GPU ; aucune donnée du laboratoire touchée |
| Q7 | **Coupure d’Internet** pour l’essai hors ligne | Bloquer seulement la sortie des conteneurs de l’essai (pare-feu dédié), sans couper le PC de Louis ; une vraie coupure de la box reste un essai séparé |
| Q8 | **Téléphone** pour l’accès LAN | Louis fait l’essai QR code depuis son téléphone à un moment convenu |

## 4. Budget de stockage prévisionnel

Estimations à **mesurer** pendant l’essai ; les chiffres réels remplacent ce tableau.

| Poste | Estimation | Source |
| --- | --- | --- |
| Documents (catalogue sans Wikipédia EN) | ≈ 73 Go | `deploy/content-catalog.json` |
| Cartes Sud (PMTiles) et routage OSRM | à mesurer | `deploy/map-catalog.json`, `scripts/maps.py` |
| Modèles IA conseillés + Whisper | ≈ 25 Go | à confirmer après téléchargement |
| Images de conteneurs | ≈ 10–20 Go | à mesurer (`docker system df`) |
| Index, caches, temporaires | à mesurer | indexation après téléchargement |
| Marge de sécurité | ≥ 15 Go | règle de `content.py` |

**Arrêt** : si le total mesuré approche 280 Go avant la fin des téléchargements,
s’arrêter et demander à Louis quoi retirer. Ne jamais dépasser 300 Go.

## 5. Déroulement

### Phase 0 — État initial et sauvegardes

- Relever espace libre des deux SSD, conteneurs et services actifs, ports
  ouverts, règles de pare-feu, état du laboratoire et du marqueur de pause.
- Ouvrir un **manifeste de l’essai** listant chaque dossier, service, volume,
  règle de pare-feu et unité systemd créé, pour le nettoyage final.
- Ne rien modifier aux applications ouvertes de Louis.

### Phase 1 — Installation de zéro

- Clone propre de `main` dans un dossier dédié à l’essai (pas le clone de Louis).
- Préparer le démon Docker dédié (Q3) et vérifier l’accès GPU depuis un conteneur
  (`nvidia-ctk`, CDI) ; consigner tout prérequis manquant comme problème du
  parcours Linux, pas comme réglage personnel.
- Lancer `scripts/install.sh --lan --data-dir …` vers le dossier choisi (Q2).
- Mesurer : durée, téléchargements d’images, messages, erreurs ; capture du
  portail au premier lancement (installation sans contenu).

### Phase 2 — Bibliothèque, cartes, modèles

- `scripts/content.py download` avec la sélection retenue (Q5) et `--budget-gb`
  cohérent avec le plafond ; reprise après interruption volontaire au moins une fois.
- Cartes Sud et routage via `scripts/maps.py` ; vérifier une recherche
  d’adresse et un itinéraire.
- Modèles conseillés ; contrôler empreintes et espace après chaque étape.
- Indexation automatique : durée, CPU, espace des index.

### Phase 3 — Recette fonctionnelle

Sur PC puis téléphone : accueil, recherche courante (feu, eau, soins), ouverture
de sources, PDF, vidéo, carte, profils, assistant (si créneau Q4) avec sources
citées, courte traduction, dictée, `/secours.html`, Open WebUI. Moteur IA
arrêté : la bibliothèque doit rester accessible. Redémarrage du PC (avec accord)
puis vérification du démarrage automatique.

### Phase 4 — Corrections

Pour chaque problème : reproduire, noter dans le journal, corriger dans une
branche `codex/…` avec tests, livrer selon les règles du dépôt (version, CI,
documentation), puis **rejouer l’étape concernée**. Les corrections de code ne
commencent qu’avec l’accord de Louis (consigne du 17 novembre : pas de code pour
l’instant).

### Phase 5 — Transfert SSD → SSD

- `transfer.py copy` vers un nouveau dossier absent sur l’autre SSD ;
  interrompre volontairement une fois puis reprendre.
- `prepare`, `verify`, `activate` ; lire `Rapport-transfert.json` et
  `LISEZ-MOI.html`.
- Rendre la source inaccessible (arrêt et renommage du dossier source, sans
  suppression), bloquer la sortie Internet des conteneurs (Q7), redémarrer, puis
  refaire la recette de la phase 3 sur la destination.
- `rollback` vers la source puis retour à la destination, pour vérifier les deux sens.

**Limite connue** : le stockage interne de Docker n’est pas déplacé par le
transfert ; la destination dépend encore du démon Docker sur le SSD système.
Un SSD interne ne peut pas être débranché à distance : l’essai simule
l’absence de la source et ne vaut pas le scénario R05 complet.

### Phase 6 — Nettoyage

- Arrêter puis supprimer les conteneurs, volumes, images et le démon Docker
  dédiés, les dossiers source et destination, les règles de pare-feu et unités
  ajoutées, les raccourcis créés.
- Comparer l’espace libre et les services avec l’état initial (phase 0).
- Conserver l’image du laboratoire, le Docker de Louis, ses applications et données.
- Garder hors Git les rapports privés ; ne conserver dans le dépôt que le bilan.

### Phase 7 — Bilan

Créer `docs/essais/AAAA-MM-JJ-installation-neuve-et-transfert-bazzite.md` avec
versions, mesures réelles, journal des problèmes, corrections livrées, limites,
puis mettre à jour la [feuille de route V1](../decisions/feuille-de-route-v1.md)
et les guides concernés (installation Linux, transfert).

## 6. Ce que cet essai ne prouvera pas

Installation Windows, PC de Marc, restauration Windows ↔ Linux, retrait
physique d’un disque, coupure électrique réelle, iPhone si non testé, qualité
des réponses au-delà des cas essayés, installation sans aucun accès Internet.

## 7. Journal des problèmes (modèle)

| N° | Phase | Constat | Gravité | Cause | Correction (branche, commit, version) | Rejoué |
| --- | --- | --- | --- | --- | --- | --- |
| P01 | | | bloquant / gênant / cosmétique | | | oui / non |
