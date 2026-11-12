# Installer et tester le prototype

> Archive — document conservé pour retracer les propositions et le prototype initial. Les constats et commandes décrivent cette étape ; pour installer le pilote actuel, suivre le [guide Marc](../installation/pilote-marc.md).

Paquet préparé le 30 octobre 2026. Commencer sur Windows chez Marc, puis répéter sur Linux. Les scripts ne réinstallent pas l’OS, les pilotes ou Docker. Ils ne remplacent pas non plus les essais LAN/GPU sur les machines réelles. Voir le [catalogue fonctionnel](../decisions/fonctionnalites-et-user-stories.md) pour les limites du prototype.

## Ce que fait l’installation

Le lanceur vérifie Docker/Compose, prépare les dossiers, conserve des identifiants uniques, télécharge les images fixées, prépare BGE-M3 puis démarre Open WebUI, Kiwix et le portail. Il prépare le petit modèle Qwen3.5 4B Q4 si absent. Les paquets représentent plusieurs Go : prévoir au moins 40 Gio libres pour ce premier essai, beaucoup plus pour la bibliothèque finale. Le contrôle refuse de continuer sous 20 Gio disponibles.

Les images sont fixées par tag **et empreinte** dans [versions.json](../../deploy/versions.json). La révision BGE-M3 est également fixée. Le modèle de dialogue est téléchargé par nom lors de la première préparation et son digest est relevé ; les installations suivantes le conservent au lieu de le mettre à jour silencieusement. Sauvegarder ses fichiers pour reproduire exactement le même modèle sur une autre machine.

Par défaut les services sont accessibles seulement depuis le PC. L’option LAN publie les ports Web sur les interfaces du PC ; le pare-feu doit laisser passer les appareils du réseau privé. Aucun réglage de box ni accès depuis Internet n’est nécessaire.

## Windows 11 : première installation

Prérequis à installer si absents :

- [Git pour Windows](https://git-scm.com/downloads/win), pour récupérer le dépôt privé avec votre compte GitHub.
- [Python 3](https://www.python.org/downloads/windows/), version 3.10 ou plus récente, avec le lanceur `py` ou Python accessible dans le terminal.
- [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/), WSL2 et conteneurs Linux ; le démarrer et attendre qu’il soit prêt.
- [Ollama pour Windows](https://ollama.com/download/windows), version de référence 0.40.13. Le script relève la version réelle installée. Ne pas confondre cette application native, qui peut se mettre à jour, avec l’image Linux fixée.
- Pilote NVIDIA adapté à la RTX 5060 Ti. Le script ne le change pas.

Rouvrir PowerShell après l’installation des programmes. Récupérer le dépôt :

```powershell
git clone https://github.com/Tanchouteur/SetupSurvie.git
cd SetupSurvie
```

Pour un essai sur le PC seulement :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Pour le tester aussi depuis un téléphone du réseau domestique, choisir dès le départ l’option LAN. Exemple avec données sur D: ; remplacer le chemin si nécessaire :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Lan -DataDir 'D:\SetupSurvie-data'
```

L’option `ExecutionPolicy` s’applique à ce processus, sans modifier la stratégie globale. Le téléchargement des modèles et la première préparation peuvent prendre du temps. En cas d’échec, lire le message puis relancer **la même commande avec les mêmes options et le même dossier** ; les documents et identifiants existants sont conservés.

Le serveur Ollama du prototype est lancé en arrière-plan sur le port **11435**, avec son propre dossier `models`. Il ne remplace pas l’éventuel serveur habituel sur 11434 et ne modifie pas ses réglages utilisateur. Il écoute sur les interfaces Windows pour être joignable par Docker Desktop ; son API n’a pas d’authentification. Ne pas ouvrir son port sur le LAN ou Internet. La règle facultative ci-dessous n’ouvre que les trois ports Web. Vérifier les éventuelles règles Ollama préexistantes si l’application avait déjà été autorisée largement dans le pare-feu.

Si les services marchent sur le PC mais pas sur le téléphone, vérifier que le réseau domestique est classé **Privé** dans Windows. En PowerShell administrateur, ajouter si nécessaire la règle limitée au sous-réseau local et au profil privé :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\open-lan-firewall.ps1
```

Le script ne change pas le profil réseau et n’ouvre rien sur le profil Public. Pour retirer sa règle : `Remove-NetFirewallRule -Name 'SetupSurvie-Web-Private'` dans un terminal administrateur.

## Linux : deuxième installation

Prérequis : Git, Python 3.10+, Docker Engine avec le plugin Compose, accès Docker pour l’utilisateur, pilote NVIDIA et [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). Le redémarrage du moteur Docker nécessaire à sa configuration doit être fait en tenant compte des autres services du PC. Le script ne l’effectue pas automatiquement.

```bash
git clone https://github.com/Tanchouteur/SetupSurvie.git
cd SetupSurvie
./scripts/install.sh --lan --data-dir "$PWD/data"
```

Ollama est ici un conteneur GPU. Aucun port Ollama n’est publié au LAN : 11435 est lié à la boucle locale. Si le GPU Docker n’est pas disponible, corriger le Toolkit ; ne pas considérer un démarrage CPU comme un test GPU réussi. Un mode CPU volontaire existe pour les diagnostics : `./scripts/install.sh --cpu` dans une installation distincte. Il n’a pas les performances attendues du GPU.

## Ouvrir les services

| Service | Depuis le PC | Depuis le téléphone, option LAN activée |
| --- | --- | --- |
| Accueil / guides | `http://localhost:8080` | `http://ADRESSE-IP-DU-PC:8080` |
| Assistant | `http://localhost:3000` | `http://ADRESSE-IP-DU-PC:3000` |
| Kiwix | `http://localhost:8081` | `http://ADRESSE-IP-DU-PC:8081` |

Trouver l’IPv4 domestique avec `ipconfig` sous Windows ou `hostname -I` sous Linux. Choisir l’adresse du réseau domestique, pas celle d’un VPN ou de Docker. Les liens du portail utilisent l’hôte ouvert par le navigateur ; ils ne renvoient pas le téléphone vers son propre `localhost`.

Les identifiants administrateur Open WebUI sont dans **`.local/identifiants.txt`** sur le PC serveur. Ils sont uniques, ignorés par Git et conservés à la relance. Ne pas les partager avec tous les lecteurs. Créer les comptes utilisateurs depuis l’administration si plusieurs personnes doivent discuter. L’espace documentaire est commun, mais les conversations sont celles des comptes ; le prototype n’implémente pas un historique familial partagé. Partager aussi les collections de connaissances en lecture avec les comptes lecteurs selon les permissions Open WebUI, puis vérifier avec un compte non administrateur. La bibliothèque directe reste accessible sans compte. Ne pas placer de données privées dans les guides publics.

Les variables de configuration administrateur d’Open WebUI sont imposées par le paquet (`ENABLE_PERSISTENT_CONFIG=false`) pour éviter une divergence silencieuse avec la configuration. Des modifications administratives de ces paramètres peuvent donc ne pas survivre au redémarrage. Ce choix n’efface pas les documents ou conversations.

## Commandes utiles

Sous Windows, utiliser `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\survie.ps1` suivi des arguments de la dernière colonne. Sous Linux, utiliser `./scripts/survie.sh` suivi des mêmes arguments.

| Action | Arguments |
| --- | --- |
| Contrôler les prérequis et la configuration | `doctor` |
| Redémarrer sans téléchargement implicite | `up` |
| Arrêter les conteneurs, sans supprimer les données | `down` |
| Activer ou désactiver la publication LAN | `configure --lan` ou `configure --no-lan`, puis `up` |
| Régénérer le catalogue des titres | `catalog` |
| Recharger Kiwix après ajout de ZIM | `reload-library` |
| Vérifier les services et les embeddings locaux | `verify` |
| Ajouter un test de génération et enregistrer sa réponse | `verify --inference` |
| Relever versions et digests réellement présents | `record` |
| Télécharger un autre modèle local | `pull-model qwen3.5:9b-q4_K_M` |

Les commandes hors installation utilisent les réglages conservés dans `.local/settings.json`. Ne pas copier ces réglages privés sur le PC suivant : il doit avoir ses propres secrets et projet. Le même dossier de données ne doit jamais être utilisé en écriture par deux installations simultanées.

Le modèle 27B reste un essai ultérieur : `pull-model qwen3.8:27b-q4_K_M`, puis sélection dans l’assistant. Sur 8 Go VRAM, du calcul CPU est probable ; vérifier mémoire et réactivité. Aucune qualité supérieure n’est promise par le téléchargement.

## Premier essai documentaire

L’installation ajoute des fiches de test illustrées dans `library/guides`, sans remplacer un fichier existant. Elles ne constituent pas une bibliothèque de survie. Dans Open WebUI :

1. Ouvrir les connaissances et créer une collection « Essai multilingue ».
2. Importer `library/guides/box.en.txt` depuis le dossier de données du serveur.
3. Attacher cette collection à la conversation.
4. Demander : « Quel est le volume intérieur de la boîte ALPHA ? Peut-on en déduire sa charge maximale ? Réponds en français avec ta source. »
5. Attendre une réponse donnant 72 litres et indiquant que la charge maximale n’est pas connue ; vérifier la citation et ouvrir la fiche illustrée depuis la bibliothèque.

Le bon chiffre seul ne valide pas la recherche : vérifier le passage anglais retrouvé et la limite sur la charge. Le lien vers l’original illustré est fourni dans le document comme référence ; son association automatique avec la citation reste à améliorer.

BGE-M3 est préparé localement sur CPU pour préserver la VRAM. Le script vérifie le chargement et la dimension des embeddings ; cela ne prouve pas à lui seul la pertinence de la recherche. Importer des documents dans Open WebUI reste nécessaire : copier un PDF dans `library/guides` ne le rend pas automatiquement interrogeable par l’IA.

## Ajouter de vrais contenus

Copier les guides dans le dossier de données `library/guides`, puis lancer `catalog`. Les noms contenant `.fr.` ou `.en.` servent au filtre de langue. PDF, HTML, TXT, Markdown et EPUB apparaissent ; certains formats sont téléchargés plutôt que rendus dans le navigateur. L’ergonomie PDF/EPUB sur téléphone doit être évaluée ; un lecteur spécialisé pourra être ajouté.

Télécharger les ZIM depuis le [catalogue Kiwix](https://browse.library.kiwix.org/) et les placer dans `library/zim`. Choisir une archive française avec illustrations pour l’essai, puis l’encyclopédie complète voulue après vérification du volume et de l’empreinte. Ne pas garder de téléchargement incomplet avec l’extension `.zim`. Lancer `reload-library` après ajout pour redémarrer Kiwix et relire les archives.

Le portail offre une recherche plein texte **Kiwix** dans les archives de la langue sélectionnée (français ou anglais), sans traduction automatique des mots saisis. Son filtre de guides porte uniquement sur les titres et chemins. La recherche plein texte commune aux guides et ZIM, indépendante de l’IA, n’est pas encore réalisée. L’IA n’interroge pas encore Kiwix : le connecteur texte/images est une fonctionnalité séparée à développer.

## Hors ligne et kit d’images

Après préparation complète et import de la collection d’essai, débrancher l’accès Internet en conservant le LAN. Lancer `up`, puis `verify --inference`, consulter les fiches, rechercher un article Kiwix et poser la question multilingue. Refaire après redémarrage du PC.

L’option `install --offline` ne télécharge ni images, ni BGE-M3, ni modèle de dialogue : les fichiers doivent déjà être présents. `OFFLINE_MODE` ne constitue pas un pare-feu ; le paquet désactive les fournisseurs IA distants et la recherche Web, mais la déconnexion réelle reste un test indispensable.

Pour exporter les images du système préparé :

```bash
./scripts/survie.sh export-images /chemin/vers/survie-images.tar
```

Copier aussi le fichier `.tar.json`. Le kit est propre à l’architecture du PC exporteur (vos deux cibles sont x86-64 ; un export ARM du Mac ne convient pas). Sur la cible déjà initialisée, `import-images /chemin/vers/survie-images.tar` vérifie l’empreinte puis charge les images et enregistre leurs identifiants locaux immuables. Cela évite de dépendre de `RepoDigests`, qui peuvent être perdus par `docker save/load`.

Ce kit ne contient **ni les modèles, ni le cache BGE-M3, ni les documents, ni les conversations**. Pour une autre machine, préparer ou transférer ces données séparément, en conservant les mêmes versions de logiciels/modèles. L’installation hors ligne d’un OS nu et des pilotes n’est pas automatisée ici.

## Données, arrêt et redémarrage

Le dossier de données conserve `models`, `library`, `catalog` et `state/openwebui`. `.local` conserve paramètres privés, identifiants, relevés de version et rapports. Le stockage natif Windows Ollama du prototype utilise lui aussi `models`, séparé de celui de l’application habituelle.

Sous Windows, `down` arrête les conteneurs puis le serveur natif dédié, uniquement si son PID, son chemin et sa date de création correspondent à ceux enregistrés par le lanceur. Les autres instances Ollama ne sont pas arrêtées. Le PID est dans `.local/native-ollama.json` et les journaux dans `.local/ollama.log`. Si l’identité ne correspond plus, aucun processus natif n’est arrêté et un message le signale. Après redémarrage de Windows, démarrer Docker Desktop puis lancer `up` pour relancer le serveur natif. Le démarrage automatique à l’ouverture de session reste une étape à configurer et valider.

Sous Linux, les conteneurs ont une politique de redémarrage ; Docker doit démarrer avec le système. Un arrêt volontaire via `down` nécessite ensuite `up`. Ne pas mettre le serveur en veille pendant les essais clients.

## Sauvegarde et restauration du petit essai

Arrêter les conteneurs avec `down` et arrêter aussi le serveur Ollama dédié sous Windows avant de copier ses modèles. Copier le dossier de données **et** `.local` vers une sauvegarde privée, en conservant les permissions ; sous Linux, une copie administrateur peut être nécessaire pour les fichiers créés par les conteneurs. Conserver aussi la version du dépôt et le kit d’images. Les données de connexion de `.local` ne doivent pas aller sur GitHub.

Une restauration sur la même installation replace ces fichiers à leurs emplacements après arrêt. Un clone d’essai sur une autre machine doit d’abord être initialisé avec ses propres réglages et chemins ; restaurer les données nécessite de tenir compte des comptes existants dans Open WebUI, et le mot de passe généré par la nouvelle initialisation ne remplace pas celui de la base restaurée. Ne pas faire pointer deux installations actives sur les mêmes fichiers.

Cette procédure est manuelle ; le script n’offre pas encore de restauration automatique. La tester vers un emplacement distinct avant d’affirmer qu’une sauvegarde est restaurable.

## Diagnostic et limites connues

- Conflit de port : ne pas arrêter un service existant au hasard. Identifier son propriétaire ; la configuration initiale utilise les ports fixes 3000/8080/8081/11435.
- Échec Open WebUI → Ollama sous Windows : vérifier le serveur dédié, Docker Desktop et les règles du pare-feu. Ne pas ouvrir publiquement l’API pour contourner le problème.
- BGE-M3 absent : exécuter `prepare` avec Internet avant le premier démarrage hors ligne ; un simple drapeau « offline » ne remplace pas le cache.
- Après ajout de ZIM : lancer `reload-library` pour régénérer son catalogue temporaire.
- `verification.json` dans `.local` distingue contrôles automatiques et essais manuels en attente. `verify --inference` enregistre une réponse et les métriques disponibles, sans certifier sa qualité.

Sources : [Open WebUI — configuration](https://docs.openwebui.com/reference/env-configuration/), [Ollama Windows](https://docs.ollama.com/windows), [Ollama Docker](https://docs.ollama.com/docker), [Kiwix Serve](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html).
