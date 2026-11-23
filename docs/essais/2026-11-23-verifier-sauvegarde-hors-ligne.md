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
