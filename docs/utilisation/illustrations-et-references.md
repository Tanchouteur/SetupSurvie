# Illustrations et références de l’assistant

**Guide actuel — 0.19.0, 15 novembre 2026.** Le [bilan des essais](../essais/2026-11-15-illustrations-originales.md)
distingue sélection sur modèle réel, rendu navigateur et limites restantes.

Dans une conversation, demander par exemple : « Compare ces documents et montre
les schémas originaux utiles. » On peut aussi choisir les documents dans la
Bibliothèque avant la question. Les visuels retenus apparaissent dans
**Illustrations originales**, sous la réponse, avec leur source et leur légende.
Ce panneau peut être replié pour poursuivre la lecture.

Une illustration d’article reste l’image originale de l’archive locale. Pour un
PDF, le portail propose **la page entière** correspondant au passage retenu :
le texte, les dessins, les mesures et les avertissements restent ensemble.
Cliquer sur l’aperçu ou **Ouvrir l’original en grand** pour le lire en détail.
**Consulter cette page** ou **Consulter le document source** revient au lecteur
de la Bibliothèque. Le lecteur PDF permet de zoomer et de chercher dans le texte.
Les petits aperçus n’offrent pas la lisibilité du fichier original agrandi.

La sélection se fonde sur les légendes et les textes effectivement transmis.
**Le modèle ne reçoit pas les pixels et n’interprète pas les flèches, composants
ou valeurs d’une image.** Un dessin sans légende peut donc être mal choisi ou
manqué. La présence d’une page proposée ne certifie pas qu’elle contient le
schéma recherché. Le logiciel ne redessine pas le schéma et ne traduit pas les
libellés de l’image. Les légendes originales et les informations bibliographiques
connues restent affichées ; les droits détaillés restent à vérifier dans l’original.

Les références simples `[1]`, groupées `[1, 2]` et accompagnées d’une page
`[1, p. 21]` sont reconnues. Pour une page PDF effectivement retenue, le bouton
ouvre cette page. Une référence à un numéro de source inconnu ne valide pas la
synthèse. Ces contrôles ne certifient pas le sens de chaque phrase ni la justesse
d’une page annoncée par le modèle. Le code littéral reste du code.

Le lecteur vérifie la version locale du fichier lorsqu’une empreinte est connue.
Si le document a changé depuis la réponse, le visuel n’est pas remplacé
silencieusement : un message permet de revenir à l’original actuel. Cette
vérification utilise taille et date de modification, pas une analyse du contenu.
Si la version n’est pas vérifiable, cela reste indiqué pour les aperçus PDF.
Une erreur d’image ou de sélection conserve la réponse textuelle et ses références.

Les choix de visuels sont enregistrés avec la conversation et retrouvés sans
nouvelle inférence au rechargement. Les aperçus se chargent à l’approche de la zone
de lecture ; le rendu PDF utilise les composants déjà fournis localement.
Les visuels enregistrés restent des références aux originaux, pas une sauvegarde
de leurs fichiers. Le fonctionnement hors ligne demande donc que ces originaux
soient toujours présents.

Le parcours examine au plus 200 images par article, privilégie les légendes liées
au sujet et plusieurs sources, puis présente au modèle au plus 24 candidats
réduits selon son contexte. Il retient au plus quatre visuels par réponse.
Les pages PDF viennent des passages consultés ; il ne parcourt pas tous les
schémas de chaque livre. Les images seules sans texte/OCR et les illustrations
d’EPUB ou de guides HTML locaux ne sont pas encore extraites par ce parcours.
La lecture intégrale et reprenable reste décrite dans le [guide de synthèse](synthese-documentaire.md).
