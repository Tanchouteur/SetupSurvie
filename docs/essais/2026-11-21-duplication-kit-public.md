# Duplication du kit public hors ligne

**Bilan du 21 novembre 2026 — 0.84.0.** Un kit public peut copier ses fichiers
inventoriés sans la machine d’origine. Le contrôle du kit dupliqué a réussi
dans un conteneur sans réseau, avec une petite bibliothèque fictive et les
quatre images Docker représentées par des métadonnées de test.

Les tests couvrent une interruption au milieu d’un fichier, la reprise alors
que le support a changé de point de montage, et une nouvelle copie produite
à partir du second kit. Un fichier altéré de même taille empêche la publication.
Les cinq faux installateurs Windows et un paquet CAB local sont conservés sur
le second support. Les fichiers hors inventaire et les transferts privés
restent à part.

La recette n’installe ni Windows ni des images Docker et n’écrit sur aucun
SSD réel. L’assistant sans terminal, la migration des comptes entre systèmes
et la restauration Windows restent à valider séparément. Voir le
[guide du kit](../installation/preparer-kit-hors-ligne.md#dupliquer-un-kit-public).
