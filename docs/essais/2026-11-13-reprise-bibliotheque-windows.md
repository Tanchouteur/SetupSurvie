# Reprise de bibliothèque et consoles Windows — 13 novembre 2026

**Bilan daté — correctifs 0.1.24, sur la base de 0.1.23.** Intervention sur le PC
Windows de Marc ; le site actif reste en 0.1.20 avec les correctifs locaux décrits.

## Incidents observés

Le téléchargement indépendant s’est arrêté sur le guide Éduscol de lecture au CP,
avec `CERTIFICATE_VERIFY_FAILED`, après environ 199 Go et 83 contenus vérifiés.
Le client HTTPS natif Windows a validé la chaîne du serveur ; un nouveau contexte
Python a ensuite accepté cette chaîne. Le guide a été téléchargé et son empreinte
attendue vérifiée. Aucune vérification HTTPS n’a été désactivée.

Le contrôleur appelait régulièrement `nvidia-smi` sans `CREATE_NO_WINDOW`, ce qui
pouvait ouvrir une console depuis son processus détaché. La température renvoyée
par le pilote était également décimale (`46.73`), alors que le parseur exigeait un
entier. Le contrôleur est désormais silencieux et accepte cette valeur. Les
commandes du lanceur utilisent le même mode silencieux sur Windows.

La fenêtre de suivi pouvait momentanément garder ouvert `content-progress.json`
et faire échouer son remplacement sur Windows. La publication durable retente
les erreurs de partage Windows pendant au plus cinq secondes, sans supprimer
l’ancien fichier avant le remplacement.

## Reprise

`scripts/content_retry.py` supervise le plan enregistré. Les reçus et tailles des
fichiers déjà vérifiés permettent de les réutiliser sans relire toutes les grosses
archives. Chaque nouveau contenu conserve la vérification de taille et SHA-256
du téléchargeur. Les échecs sont inscrits séparément et ne bloquent plus les
contenus suivants ; ils sont retentés avec un délai croissant.

Après l’intervention, le suivi est passé de 83 à 109 contenus vérifiés et indiquait
à nouveau un téléchargement actif. Un guide sur les plantes toxiques restait en
attente après une réponse incomplète, sans bloquer Wikiversité puis Wikivoyage.
Ces nombres décrivent ce point de contrôle, pas la fin des 753 Go du plan.

Le contrôleur hôte a été rechargé séparément. Aucun arrêt de Docker, des services
Web, d’Ollama ou d’une application de l’utilisateur n’a été demandé. Les anciens
journaux, fichiers complets et partiels ont été conservés.

## Vérifications

Suite applicative sur Windows : **233 tests, 226 réussites et 7 ignorés**, sans
erreur ni échec ; les modules du laboratoire Linux sont exclus. Les tests de
coupure utilisent l’exécutable Python direct avec les dépendances isolées, pour
éviter le processus intermédiaire du lanceur de venv Windows lors des arrêts forcés
de nos seules fixtures.

- Scénarios simulés de reprise : contenu déjà vérifié, reçu modifié, erreur réseau
  suivie de succès sur un autre contenu, nouvelle tentative après contrôle TLS,
  épuisement des tentatives et conservation du partiel.
- Contrat du contrôle HTTPS natif : protocoles HTTPS imposés, absence de `-k` et
  `--insecure`, exécution sans fenêtre.
- Tests du GPU : température décimale et mode de création du processus.
- Publication : verrou Windows transitoire retenté, ancien fichier conservé
  jusqu’à réussite, erreur de permission ordinaire propagée sans attente inutile.
- Sur le PC réel : guide Éduscol obtenu avec la bonne empreinte, un GPU reconnu,
  API du contrôleur disponible et progression du téléchargement observée.

Les essais ne valident pas l’intégrité physique du disque ni la disponibilité
future des serveurs. Les contenus épuisant leurs tentatives restent explicitement
incomplets ; ils ne sont jamais présentés comme téléchargés et vérifiés.

Voir la [reprise supervisée des gros plans](../bibliotheque/bibliotheque-complete-marc.md#reprise-supervisée-des-gros-plans-0124)
pour la commande et les fichiers de suivi.
