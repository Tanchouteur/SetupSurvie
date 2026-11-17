# Aide générale sans source précise

**Bilan ciblé — 17 novembre 2026, candidat 0.37.4.** Suite de l’objectif
recherche et assistant. Applique la règle validée par Louis dans
l’[ingénierie de tests](ingenierie-de-tests.md#2-cas-fondateur--la-capture-de-marc-du-17-novembre-2026).
La campagne V1 complète, le fonds de Marc et les essais d’installation restent
distincts de ce contrôle ciblé.

## Défaut constaté et correction

Le contexte produit et son complément moteur demandaient « Je ne sais pas
d’après les documents disponibles » sans préciser assez qu’une aide générale
restait possible. Après une recherche vide ou des ouvertures toutes en échec,
le moteur ajoutait aussi « Les passages de plusieurs documents ont été préparés ».
Cette consigne contredisait les résultats réellement transmis dans le paquet vide.

La préparation annonce maintenant qu’elle n’a fourni aucun passage. Si elle en
fournit, la rédaction documentaire conserve ses références et lectures partielles.
Les consignes communes autorisent explicitement une aide générale signalée :
exemple adaptable, âge/niveau des enfants et durées non normatives. Une commande
exacte d’un appareil, un contenu demandé dans une notice ou un geste critique
ne peut pas être remplacé silencieusement par une procédure générale inventée.
Le suivi continue de compter seulement les sources effectivement lues ; il n’est
pas remplacé par le texte du modèle. Les erreurs moteur restent des erreurs.

Le premier texte de consigne ajouté était trop long : le test de budget 16k
retenait seulement deux des trois sources minimales attendues. La rédaction est
réduite sans baisser le test ni augmenter le contexte : le scénario de trois
sources passe à nouveau. La version `z` correspond à la correction compatible
d’une règle de réponse et d’un message documentaire contradictoire ; données
personnelles et références des composants tiers inchangées.

## Vérifications

**58 tests d’orchestration passent en 14,553 s**. Deux nouveaux cas traversent le
moteur réel avec HTTP simulé : bibliothèque vide pour l’organisation culturelle,
puis résultat proposé dont l’ouverture échoue. Ils vérifient les consignes
transmises, le paquet sans passage et zéro source prétendument consultée.
Ils ne prouvent pas qu’un modèle réel respecte toutes ces règles.

Un essai réel séparé utilise le R7, Gemma4 E4B préexistant, contexte 16 384,
4 threads et 8 couches GPU. Bibliothèque fictive vide, pas de vrais comptes ni
corpus client. Une réserve VRAM est vérifiée ; aucun autre modèle ou traitement
n’est déchargé, aucune dépendance ni modèle téléchargé. Maintien modèle 15 s.
Les trois cas portent sur la question de Marc avec ses fautes, une organisation
pour deux âges précisés et une commande d’appareil fictif absente du fonds.
Résultats, relecture de l’agent et limites à consigner après leur fin effective.


Suite complète locale : **1 005 tests en 208,384 s, 6 ignorés, aucun échec**.
Premier cas réel terminé en **66 908 ms**, zéro source consultée et aucune
citation inventée. La réponse demande âge/niveau et propose activités, régularité,
exemples d’horaires adaptables. Elle commence encore par « Je ne peux pas te
donner un programme précis » avant d’aider : amélioration réelle de l’utilité,
mais formulation initiale encore négative, pas une preuve d’absence de sur-refus
sur une banque complète. Les deux autres réponses et la CI restent en cours.
