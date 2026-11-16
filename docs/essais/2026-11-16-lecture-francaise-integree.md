# Lire en français depuis le document original

**Bilan daté — candidat 0.21.0, 16 novembre 2026.**
Le [guide documentaire](../utilisation/documents-et-traduction.md#lire-une-version-française-déjà-terminée--0210)
décrit l’usage ; la [traduction 0.20.1](2026-11-16-traduction-contexte-et-reprise.md)
reste le bilan du cycle du modèle.

## Comportement

Les lecteurs du portail et le lecteur PDF retrouvent une traduction déjà terminée
et publiée. « Lire en français » ne lance pas d’IA ; l’original reste accessible.
Le PDF conserve sa pagination et ses images quand on y revient. Les pages hors
plage restent annoncées non traduites. Les avertissements suivent le texte et
le choix français peut être retrouvé au rechargement.

Le lecteur ne lit que le fichier partagé. Il n’expose ni les instantanés sources,
ni les brouillons, candidats refusés ou identités. La suppression de la conversation
ne retire pas le texte publié. L’association avec l’original est vérifiée ; une
ancienne correspondance inconnue ou modifiée demande un choix explicite.
Le repère d’origine est taille/date du fichier, pas un hash de tout un ZIM/PDF.
L’empreinte du fichier français est contrôlée lorsqu’elle a été enregistrée.

Les versions sont listées par leurs métadonnées sans parser tous les livres à
chaque ouverture. Le texte partagé est chargé à la demande, avec un cache borné
et reconstructible. Aucune mise à jour d’archive, transcription, nouvelle traduction
ou modification du document original ne résulte du bouton de lecture.

## Vérifications

La suite locale de 759 tests a réussi (trois ignorés spécifiques à Windows).
Neuf tests du lecteur couvrent publication indépendante, originaux modifiés,
texte publié modifié, correspondance croisée refusée, brouillons privés, anciennes
révisions inconnues, article d’archive, API sans modèle et liste sans lecture de livres.
Les lectures longues et traductions existantes sont également rejouées.

Les recettes Chromium/WebKit vérifient 28 contrôles chacune : lecture française,
page correspondante, absence d’inférence, aller/retour PDF, rechargement, plages
incomplètes, source changée, conservation après suppression, article Kiwix, texte
non interprété comme HTML, panne de l’option et largeurs 1366/390/320. Le MCP
Chromium a aussi exécuté le parcours et produit des captures examinées. Une erreur
PDF.js observée lorsque le conteneur original était caché a conduit à différer
ses opérations de défilement jusqu’au retour à l’original ; les pages restent
synchronisées. L’émulation WebKit ne remplace pas un essai iPhone réel.

La lecture française a été intégrée dans la livraison 0.22.0 avec le diagnostic
commun. Les 28 contrôles passent dans Chromium et WebKit ; les
[huit jobs finaux](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43818175933)
sont réussis. Les candidats 0.21.0 ont révélé un débordement WebKit ensuite corrigé ;
aucune version 0.21.0 n’a été intégrée séparément dans `main`.

## Essai réel

`report-gemma4-bilingual.json`, R7, modèle préexistant `gemma4:e4b`, contexte 16k,
32 couches GPU, six threads, Ollama natif 0.40.14. Une page réelle de la notice
Baofeng/Radioddity est traduite puis publiée, en 38 285 ms. Le lecteur retrouve
la page 14, sa correspondance inchangée et tous les passages français identiques
à ceux publiés, avec l’avertissement des touches manquantes.
Empreinte Python du code testé :
`aa7f2b27e66aa461ef33a18c965f16e85e93c1cf0b3f335ff9deed6d9357abf2`.
Les fichiers et le rapport restent privés ; aucun poids téléchargé ni autre
application arrêtée. Aucun essai sur le PC Windows de Marc.

## Limites

Le texte n’a pas la mise en page ni les illustrations traduites de l’original.
Une correspondance de taille/date ne certifie pas l’identité du contenu ; les
anciennes traductions peuvent rester à comparer. La sélection manuelle est conservée
pour ces cas, sans déclarer une nouvelle édition couverte par l’ancienne.
La lecture française concerne Kiwix ouvert dans le portail, pas son interface
native directe. Le glossaire, la déduplication des nouvelles demandes de traduction,
la fidélité d’un vrai livre de 500 pages et les sous-titres restent à développer
ou qualifier. Le diagnostic des goulots en un clic demandé ensuite par Louis
reste [un chantier séparé](../decisions/diagnostic-lenteurs-en-un-clic.md).

Le niveau mineur **0.21.0** correspond à une nouvelle fonction de lecture compatible.
Schéma 1, originaux, profils conseillés et versions des images tierces conservés.
