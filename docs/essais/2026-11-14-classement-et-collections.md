# Classements persistants et collections corrigibles

**Bilan daté — 0.6.0, 14 novembre 2026.** Lot L3 du
[plan retenu](../decisions/plan-ameliorations-marc.md), dans l’objectif de première
version fiable du moteur. Aucun nouveau corpus ni modèle n’est téléchargé.

## Résultat implémenté

- Classement par article/document, appartenance possible aux deux espaces,
  correction humaine prioritaire et type éditorial explicite ou à vérifier.
- État automatique, corrigé ou examiné visible ; une indication de procédure
  n’est jamais une certification de sécurité.
- Corrections liées à une révision locale taille/date. Fichier modifié ou
  formulaire périmé : l’ancien examen n’est pas repris implicitement.
- Libellés et groupes de collections modifiables depuis Famille, regroupement
  générique par source et variantes connues. Identifiants, chemins, langues,
  éditions et originaux conservés. Filtre par groupe corrigé également appliqué
  à Kiwix et aux index SQLite complémentaires.
- Export des métadonnées sans textes, historique, identité de profil ni chemin
  absolu. Retour explicite aux noms/classements automatiques. Pas d’import ajouté.

L’approche retenue ajoute une surcouche dans les réglages existants. Elle conserve
les fichiers en un exemplaire et évite de modifier les ZIM. Le type automatique
reste prudent : pas de procédure supposée à partir du seul mot « guide ». Une
qualification réelle du fonds ou une labellisation IA globale n’est pas annoncée.

## Défauts supplémentaires reproduits et corrigés

Le nettoyage lexical supprimait les apostrophes typographiques avant de séparer
les mots : « l’eau » devenait « leau » pour le classement et le score. La
normalisation garde maintenant la séparation des mots et enlève les accents.

Au rechargement d’une lecture adressable, le document pouvait être chargé avant
le profil, puis masqué lors de l’activation finale. Le lecteur attend désormais
la fin du choix automatique du profil et se rouvre si nécessaire. Les commandes
de noms de collections s’actualisent également à l’arrivée du profil.

## Vérifications

Tests sur petits fichiers fictifs : correction conservée après réindexation,
deux espaces, aucun espace sans disparition globale, pages PDF, édition modifiée,
formulaire ancien, références dangereuses, correction illisible et export filtré.
Un petit ZIM réel généré vérifie que le groupe corrigé filtre aussi l’index SQLite,
même lorsque Kiwix ne propose pas cette archive.

API simulée : droits Famille, validation des champs, refus de révision périmée,
lecture des corrections et noms de collections sans changement d’identifiants.
Chromium MCP : 19 contrôles, édition réelle dans la base de fixture, rechargement
avec profil volontairement retardé, filtres, navigation arrière, groupes mémorisés,
export, dialogue de noms avec Précédent/Suivant et absence de débordement à 1366/390/320 pixels.

Suite locale : 420 tests, trois exclusions signalées ; Kiwix 3.8.1 réel : 29 contrôles
sur cinq ZIM générés (282 587 octets). Les recettes existantes Chromium de recherche
(45 contrôles) et de réglages (14) passent aussi.

La [CI du code livré](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43606964502)
est réussie : Linux (420 tests, trois exclusions), Windows, Kiwix réel, routage
hors ligne et interface. Chromium et WebKit passent chacun les 19 contrôles
de classement, les 45 de recherche et les 14 de réglages. Le paquet logiciel
est construit par la CI. Une course d’observation de l’ancien test d’indexation
a été corrigée : il attend désormais la réponse de la commande avant de vérifier
qu’elle a été transmise, sans supprimer l’assertion.

Les essais ne
valident pas une qualification éditoriale du fonds de Marc, Safari sur iPhone,
la vitesse de son disque ou le comportement des modèles réels.

**Version mineure 0.6.0** : nouvelles commandes et métadonnées compatibles ;
schéma de données 1 et composants tiers inchangés. R3 sur le fonds réel reste à
faire. L4 (mesures assistant et mémoire) et les autres suites du plan restent ouvertes.
