# Référence de pertinence et lecture des articles trouvés

**Bilan daté — 0.5.0, 14 novembre 2026.** Suite de l’objectif de première
version fiable du moteur. Les deux photos reçues pendant ce lot sont consultées
sans copie dans Git. Elles concernent, selon Louis, l’usage de la 0.3.0.

## Observations de Marc et distinction des causes

Une photo montre un sommaire avec des intitulés noirs et des liens bleus/violets.
Elle ne permet pas de déterminer pour chaque intitulé si un lien existe, a été
visité, manque dans l’archive ou n’est qu’un texte. Le besoin de clarification
reste tracé comme IDEE-005, reporté à la demande de Louis.

L’autre montre des résultats feu Wikipédia/Wikilivres et l’erreur **Document
indisponible** après ouverture. Marc a fermé la page ; Louis indique pouvoir
transmettre l’adresse lors d’un prochain incident. Ni l’identifiant exact ni le
statut HTTP du cas réel ne sont donc établis.

Un défaut est reproduit dans le lecteur : tout statut HTTP différent de 200,
y compris une redirection valide, était transformé en indisponibilité. Le navigateur
peut suivre cette redirection alors que l’aperçu et l’assistant échouent. Cela
explique un cas possible, pas la preuve de la cause de cette photo.

## Changements

- Référence de **32 demandes** dans `portal/nouveau/search-reference.json`,
  réutilisée par le contrôle complet du site et par les tests. Attentes de sources
  distinctes dans `tests/search_reference_fixtures.json`, exclusivement fictives.
- 24 demandes de réglage, huit de vérification ; vérification du premier résultat
  et de sa présence dans les cinq premiers, puis maintien sous filtre résilience
  lorsqu’adapté. Cas négatif et savoir général conservés.
- Avant correction, quatre demandes de réglage échouaient malgré les textes
  présents : vêtement à recoudre, panneau solaire, conserves de légumes et outil
  à aiguiser. Équivalences FR/EN et intentions complétées dans le moteur commun,
  y compris les requêtes Kiwix et le domaine pratique.
- Contrôle court de dix cas conservé ; contrôle complet optionnel et annulable,
  avis humain distinct de la mesure, résultat utile/rang exportés, autres cas
  explicitement à vérifier. Aucun appel IA ni téléchargement de bibliothèque.
- Redirections HTTP suivies seulement à l’intérieur de la même archive locale,
  cinq au plus, délai global borné. Images relatives résolues depuis la cible ;
  identifiants historiques conservés. Boucles, sorties d’archive et gros aperçus
  restent refusés avec un message compréhensible.
- Un aperçu échoué propose retour aux résultats, nouvel essai et ouverture directe
  de l’original. Une ancienne erreur de lecture ne remplace pas une lecture plus récente.

## Contrôles et limites

Les 32 demandes passent sur 22 petits documents fictifs après correction ; ce
constat ne prouve pas la présence ni la qualité de ces documents chez Marc. Les
tests HTTP exercent le vrai lecteur avec un transport simulé : cinq statuts de
redirection, chaînes relatives, boucle, limite, cible externe, autre archive,
catalogue, taille et chemin des images.

Chromium via MCP : 45 contrôles de recherche, dont contrôle complet, avis exportés,
repli de lecture et présentation 1366/390/320 pixels. Une capture du contrôle
complet à 390 pixels a aussi été examinée.

La [CI du code livré](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43603751860)
est réussie : Linux (408 tests, trois exclus), Windows (dont nouvelle référence
et lecteur HTTP), Kiwix, routage hors ligne et interface. Chromium **et** WebKit
passent chacun les 45 contrôles de recherche et les 14 de réglages. Le paquet
logiciel est construit par la CI ; versions API/manifeste/interface cohérentes.

Kiwix 3.8.1 réel : 29 contrôles sur cinq ZIM générés, 282 587 octets. Les quatre
nouveaux besoins FR retrouvent leur véritable texte indexé anglais en premier
avec le filtre adapté, sans se limiter à une suggestion de titre. Un alias ZIM
rejoint son texte cible ; les tests HTTP distincts vérifient le suivi sécurisé
par le lecteur Python. Aucun fonds ni modèle n’a été téléchargé pour ces tests.
Ces résultats ne valident pas le débit du disque de Marc ni Safari sur iPhone.

La CI 0.4.0 relancée sur `main` a révélé une course dans l’attente du test de
filtrage : `S` pouvait être lu avant son initialisation après navigation. L’attente
vérifie maintenant son existence avant les mêmes assertions ; aucune assertion
fonctionnelle n’a été supprimée.

**Version mineure 0.5.0** : contrôle complet et relecture exportable nouveaux,
compatibles avec les données existantes. Pas de changement d’image tierce, de
corpus réel, de droits ni de lancement de modèle. R1/R2 sur Windows, classements
corrigeables L3 et mesures assistant L4 restent distincts et à poursuivre.
