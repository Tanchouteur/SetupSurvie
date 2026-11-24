# Vérification de la sauvegarde personnelle avant le départ hors ligne

**Bilan du 23 novembre 2026 — SetupSurvie 0.112.0.** La version mineure
ajoute au lanceur **Vérifier le kit SetupSurvie** un contrôle facultatif de
la sauvegarde personnelle, ainsi que la commande `pilot_backup.py verify`.
La restauration réutilise les mêmes contrôles de manifeste, de périmètre et de
compatibilité, désormais regroupés dans `read_backup` et `check_kit_identity`.

Testé sur le runner CPU, avec fixtures minuscules :

- une sauvegarde Windows est déclarée lisible et compatible avec le kit, sans
  écriture dans la sauvegarde ni dans le kit, Docker et réseau interdits ;
- une sauvegarde plus récente que le kit, un guide altéré sans changement de
  taille et un dossier sans `backup.json` sont refusés avec un message clair ;
- une sauvegarde sans identité de version est signalée comme restaurable
  seulement sur le même système ;
- le repli Zenity enchaîne contrôle du kit puis de la sauvegarde avec le Python
  temporaire du SSD, et la fenêtre Tk affiche les deux résultats (Tk et Zenity
  simulés).

Non vérifié : double-clic sur un vrai bureau Windows ou Linux, sauvegarde
réelle de grande taille, cohérence interne des bases SQLite. Voir la
[procédure](../installation/preparer-kit-hors-ligne.md#vérifier-le-ssd-avant-de-partir).

## Recette sur deux VM Debian 12

Le kit réduit de recette (19 Go) a servi à installer le PC A et à préparer son
point de restauration. Le PC B, initialement sans Python ni Docker système,
a reçu une sauvegarde personnelle du PC A depuis les deux disques de recette.
Après arrêt et redémarrage du PC B avec les deux disques retirés, le portail,
Kiwix et Open WebUI ont répondu en HTTP 200 et le guide personnel de test
était présent. Le réseau virtuel était isolé et le PC B n’avait pas de route
par défaut.

Sur le PC A, le retour au point de restauration s’est arrêté à l’activation.
Un verrou d’indexation exclu de la copie était confondu avec un environnement
Python à reconstruire. Le correctif correspond au nom exact du dossier
d’environnement. Pour reprendre la recette, seuls le script et son empreinte
dans le journal de la copie de travail jetable ont été ajustés. Le point
protégé a conservé son attribut immuable et l’empreinte de son manifeste.
La copie de travail corrigée a démarré et l’ancienne installation est restée
archivée. Le test de transfert couvre le verrou résiduel.

Périmètre restant pour la [recette d’acceptation](../exploitation/disque-de-secours-hors-ligne.md#10-recette-dacceptation) :
rejouer le retour au point avec un kit intégralement reconstruit, les essais
sur un SSD physique, les combinaisons avec Windows et le parcours graphique
sur un bureau réel.


Une troisième VM Debian 12 a installé le kit réduit 0.112.0 reconstruit depuis
le commit `54e14e2`, avec le correctif déjà dans le kit. La VM disposait d’un
Python système au départ, sans Docker. L’installateur a utilisé les outils
embarqués. L’assistant d’entretien a restauré le point sans SSD de secours ni
route par défaut. Il a conservé une ancienne copie et l’empreinte du manifeste
du point protégé. Après le redémarrage suivant, le portail et Kiwix répondaient.
Open WebUI renvoyait encore HTTP 502 au dernier contrôle. Le fichier témoin
attendu dans l’ancienne copie n’a pas été retrouvé. La perte de connexion à
Bazzite a interrompu le deuxième retour au point, lancé avec un nouveau
fichier témoin.

Les cinq installateurs Windows (WSL, Python, Docker Desktop, Git et Ollama)
ont été téléchargés dans une copie de préparation du kit sur Bazzite.
Leurs empreintes ont été vérifiées avec `prepare-windows --verify-only`.
La VM Windows reste à préparer.

## Vérificateur graphique sur Windows 11 hors ligne

Dans une VM Windows 11 Enterprise LTSC 24H2 sans carte réseau, Python et
Docker étaient absents au début de l’essai. Le double-clic sur le lanceur du
kit réduit 0.113.0, monté en lecture seule, a proposé l’installation de Python
3.13.17 pour le compte courant. Elle s’est terminée avec les fichiers locaux.
Après fermeture de l’installateur, la question sur la sauvegarde était derrière
l’Explorateur. Il a fallu revenir à la fenêtre SetupSurvie pour continuer.

Le vérificateur graphique a contrôlé les 1 274 fichiers du kit et les cinq
fichiers d’une sauvegarde Linux fictive. Il a indiqué que cette sauvegarde
était compatible avec le kit sur Windows et Linux. Cette recette a contrôlé
la lecture et le message de compatibilité.

La correction 0.113.1 affiche la fenêtre de SetupSurvie avant la première
question et lance une installation de Python avec affichage de l’avancement
quand Python est absent. Les tests automatisés contrôlent l’ordre d’ouverture
des fenêtres, les arguments du programme d’installation et le cas où un
Python déjà installé doit être modifié pour obtenir Tcl/Tk. La recette du
premier double-clic avec cette correction reste à effectuer sur Windows.

## Copie Windows relue sous Linux

Le 24 novembre 2026, le lanceur **Dupliquer le kit SetupSurvie** a copié
le kit réduit 0.113.0 depuis son support en lecture seule, en VM Windows 11
sans carte réseau. La destination choisie dans l’assistant était un
second disque virtuel USB formaté en exFAT. Après l’arrêt de la VM, ce
disque a été monté en lecture seule sous Linux. Le vérificateur a contrôlé
les 1 274 fichiers, y compris les installateurs Windows et Linux. Le
manifeste final était présent et le marqueur de copie en cours avait
disparu. La recette couvre le passage du kit public de Windows à Linux,
avec des supports virtuels.
