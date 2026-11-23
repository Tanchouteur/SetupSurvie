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
