# Demande pratique et résultats de prix

**Bilan de la 0.33.1 — 16 novembre 2026.** Correctif compatible de
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

Le code `636cff2ffd908e201a3d2108427e27f06b275c19` passe les **huit jobs** de la
[CI complète](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43938878549),
dont Windows et les recettes Chromium/WebKit existantes. Linux : **939 tests en
89,239 s, 6 ignorés**. Les tests d’API locaux passent également : **31 tests en
11,123 s**. Les seuls ajouts après ce code validé concernent les bilans et le reçu
de paquet ; aucun nouveau résultat humain ni inférence n’est revendiqué.

L’intégration sur main est par avance rapide, sans réécriture de l’historique.
La [coordination UX](../decisions/coordination-ux-et-videos.md) conserve son périmètre :
le code fonctionnel de ce lot change `pilot/retrieval.py` ; `pilot/app.py` ne change
que la version. Aucun écran, contrôleur hôte, carte ou générateur HTML modifié.

## Reçu du paquet logiciel

Source : `0562bb1a56827500c16cfd444280087941367deb`, après validation du code
ci-dessus. **925 fichiers**, **7 514 828 octets** compressés, **16 711 777 octets**
décompressés. SHA-256
`49f12934eaa0acfb1b1980910e8ea7456475b7e5da615118c7df2cacfad05b8b`.
Chaque entrée a été comparée au même commit Git avec ses filtres puis aux
tailles/empreintes du manifeste. Le reçu désigne le commit source, pas son propre
ajout ; aucun contenu privé, modèle ou corpus n’est embarqué.

## Limites

Un titre utile ne certifie ni une procédure complète ni la qualité du document.
Pas de nouvel essai sur Marc ni de validation humaine de tous les résultats.
L’inflexion de tous les noms français/anglais n’est pas résolue par cette correction ;
les variantes inconnues peuvent encore limiter le rappel. La transcription des
vidéos internes aux ZIM reste un travail distinct après le parcours 0.33.0.

**Suites datées :** l’[audio des vidéos incluses](2026-11-16-audio-videos-collections.md)
est raccordé en 0.35.0 ; les [formes courantes de nombre](2026-11-16-recherche-formes-de-mots.md)
sont ajoutées en 0.36.1, sans résoudre toute la morphologie ni qualifier le fonds réel.
