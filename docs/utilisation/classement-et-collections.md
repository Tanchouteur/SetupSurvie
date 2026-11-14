# Classer les documents et nommer les collections

**Guide actuel — 0.6.0, 14 novembre 2026.** Ces corrections se font depuis le
profil **Famille**, librement accessible sur le réseau local. Elles sont communes
aux lecteurs et à l’assistant. Aucun modèle IA n’est nécessaire.

## Corriger le classement d’un document

1. Ouvrir le document depuis les résultats, puis **Corriger le classement** au
   bas de l’aperçu.
2. Choisir **Autonomie et résilience**, **Savoirs et culture**, ou les deux.
   Sans espace choisi, le document reste retrouvable dans **Toute la bibliothèque**.
3. Indiquer ce qu’il contient surtout : présentation, explication, procédure,
   exercice ou notice technique. Garder **Type à vérifier** si son contenu n’est
   pas suffisamment connu.
4. Cocher **J’ai examiné le contenu pour ce classement** seulement après lecture,
   puis enregistrer. La prochaine recherche utilisera la correction.

Le résultat distingue classement **corrigé**, classement **examiné** et indication
automatique. Une procédure classée comme telle n’est pas certifiée correcte ou
sûre. Le simple titre « guide » ne suffit pas à classer automatiquement une page
comme procédure. Un quiz explicite peut être repéré comme exercice à vérifier.

La correction s’applique à l’article ZIM ou au document entier ; les pages d’un
même PDF partagent le classement. Elle ne modifie ni le fichier ni ses liens.
**Revenir au classement automatique** supprime seulement cette correction.
Une réindexation des guides conserve les corrections.

## Si le fichier change

La correction est liée à la référence et à la version locale du fichier. Une
nouvelle édition portant une autre référence ne reçoit pas l’ancien examen.
Si le fichier est remplacé sous le même nom, une modification de taille ou de date
de modification invalide la correction ; le site demande de la revoir et utilise
l’indication automatique. Un formulaire ouvert sur une ancienne version refuse
d’enregistrer avant réouverture du document.

Cette reconnaissance rapide par taille/date ne relit pas les centaines de Go
d’une archive et ne constitue pas son contrôle d’intégrité cryptographique. Les
vérifications de téléchargement et d’indexation restent distinctes.

## Nommer et regrouper les collections

Dans **Bibliothèque → Collections**, ouvrir le groupe si nécessaire puis choisir
**Modifier les noms** sur une collection.

- **Groupe ou source** réunit les collections portant le même nom.
- **Sujet ou titre de cette collection** distingue leur contenu, par exemple
  Alimentation ou Équipement.
- **Référence d’origine** conserve le nom de l’archive et son titre initial.

Les fichiers, éditions, langues et boutons d’ouverture restent inchangés. Les
noms corrigés sont utilisés par le filtre local et le sélecteur de recherche.
Les anciens liens visant la source d’origine restent acceptés. Les groupes
ouverts et filtres restent mémorisés au retour et au rechargement.

Le regroupement automatique utilise la source et les variantes connues du nom
d’archive ; pour un sujet inconnu, il garde le titre disponible ou la référence
au lieu d’inventer une traduction. Les libellés insuffisants peuvent donc encore
demander une relecture. **Revenir aux noms automatiques** retire la correction.
Un fichier modifié demande aussi de revoir ses noms corrigés.

## Conserver les corrections

**Mon appareil → Paramètres → Entretien et diagnostics → Conserver les classements et les dossiers pratiques → Classements et noms corrigés → Exporter les métadonnées**
télécharge les références, états et corrections. Il ne contient ni texte des
documents, ni conversations, ni identité de l’auteur des corrections. Les références
et noms saisis figurent bien dans ce fichier. L’import de cet export n’est pas
encore proposé ; il sert à conserver et examiner les corrections.

Les corrections sont enregistrées dans `settings` de `state/pilot/pilot.db`,
avec le préfixe `catalogue:v1:`. La sauvegarde habituelle de l’état les conserve,
sans nouvelle migration. Dix mille corrections au total sont admises ; les
autres documents restent recherchables par le classement automatique. Cette
limite ne plafonne pas le téléchargement ni la taille de la bibliothèque.

Si une correction est illisible, la recherche garde les autres corrections et
utilise l’indication automatique pour le document concerné, en signalant le
problème. Une erreur de ce module ne supprime aucun document du fonds global.

La relecture du fonds de Marc reste nécessaire : l’outil permet les corrections,
il ne prouve pas que toutes les ressources sont déjà qualifiées ou bien nommées.
