# Demande pratique et résultats de prix

**Bilan du candidat 0.33.1 — 16 novembre 2026.** Correctif compatible de
classement, sans nouvelle fonction d’interface ni migration. Le niveau correctif
correspond à une intention déjà annoncée qui était incomplètement reconnue.

## Défaut et correction

Le [retour Windows](2026-11-16-campagne-windows-marc.md) signale que « réparer un
vélo » remontait d’abord un prix de réparation. Deux exemples fictifs reproduisent
ce comportement dans le moteur 0.33.0 : « Prix de réparation d’un vélo » devant
« Mécanique vélo/Réparer un pneu », et « Bicycle repair costs » devant « Repair a
bicycle tyre ». Cela reproduit un défaut de classement, sans prétendre identifier
l’article exact que Marc avait fermé.

Le titre de prix recevait le bonus d’action directe parce qu’il contenait aussi
« réparation ». Il est désormais traité comme une présentation contextuelle, même
si son titre comporte « guide ». Les formulations explicites d’instructions
restent des pistes pratiques même lorsqu’elles parlent de coûts. Les tarifs ne
sont pas retirés des résultats ; une question de prix les retrouve en priorité.
Le mot « guide » n’est toujours pas une preuve de contenu opératoire.

Une seconde incohérence distinguait les actions reconnues du statut de demande
pratique : « filtrer », « affûtage », « conserver », « remplacer » ou l’anglais
« install » pouvaient perdre cette priorité sans « comment/how ». La détection
réutilise maintenant les mêmes intentions. Les variantes de remplacement sont
aussi reconnues avec celles de réparation, sans exiger le verbe exact dans le texte.
Les questions « pourquoi » seules et les demandes historiques gardent leur traitement.

## Preuves locales

- Douze tests de titres, avec cas français/anglais, prix explicites, instructions
  avec coût, demandes courtes, histoire et pourquoi : **12 tests en 0,014 s**.
- Régressions de recherche : **101 tests en 27,970 s**, avant l’ajout du dernier
  scénario d’index réel décrit ci-dessous.
- Suite de pertinence avec index de guides réellement construit, lecture de la
  source retenue et inversion voulue entre recherche d’action et recherche de
  prix : **9 tests en 2,231 s**. Les textes sont fictifs, aucun modèle ni corpus
  réel téléchargé. Aucun changement de la file IA ou des sources consultées.

La CI finale, l’intégration et le reçu de paquet seront ajoutés après validation.
La [coordination UX](../decisions/coordination-ux-et-videos.md) conserve son périmètre :
le code fonctionnel de ce lot change `pilot/retrieval.py` ; `pilot/app.py` ne change
que la version. Aucun écran, contrôleur hôte, carte ou générateur HTML modifié.

## Limites

Un titre utile ne certifie ni une procédure complète ni la qualité du document.
Pas de nouvel essai sur Marc ni de validation humaine de tous les résultats.
L’inflexion de tous les noms français/anglais n’est pas résolue par cette correction ;
les variantes inconnues peuvent encore limiter le rappel. La transcription des
vidéos internes aux ZIM reste un travail distinct après le parcours 0.33.0.
