# Aide générale sans source précise

**Bilan ciblé — 17 novembre 2026, candidat 0.38.1.** Suite de l’objectif
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
Les résultats sont relus par l’agent ci-dessous ; ils ne constituent pas un avis professionnel.


Suite complète locale : **1 005 tests en 208,384 s, 6 ignorés, aucun échec**.
Premier cas réel terminé en **66 908 ms**, zéro source consultée et aucune
citation inventée. La réponse demande âge/niveau et propose activités, régularité,
exemples d’horaires adaptables. Elle commence encore par « Je ne peux pas te
donner un programme précis » avant d’aider : amélioration réelle de l’utilité,
mais formulation initiale encore négative, pas une preuve d’absence de sur-refus
sur une banque complète.

Avec les âges fournis, **164 941 ms**, réponse terminée et semaine différenciée
7/11 ans (géographie, sciences, histoire, arts, langues, atelier, lecture libre).
Les suggestions sont explicitement attribuées aux connaissances générales ; les
contenus et procédures demandant une documentation sont distingués. Aucune
citation documentaire n’est fabriquée. La relecture de l’agent constate une aide
concrète, sans certifier un programme scolaire, ses durées ou tous ses principes.

Pour l’appareil explicitement fictif TQ-917, **35 767 ms**, aucune touche inventée :
le modèle demande une notice réelle et borne son aide aux principes généraux.
Ce cas vérifie une limite de commande exacte, pas la capacité à identifier une
référence réelle mal orthographiée ni les gestes critiques de la banque V1.
Les deux demandes éducatives ont une recherche préparatoire puis un paquet vide ;
la demande d’appareil fictif ne lance aucun outil. Les trois réponses gardent
zéro source lue et zéro référence numérotée : aucune recherche supplémentaire
n’est déduite du seul texte du modèle.

Les temps reflètent le R7 avec huit couches GPU et un autre traitement actif ;
ce ne sont ni des objectifs de latence ni une prévision pour le PC de Marc.
Aucun processus tiers arrêté. Le dossier temporaire et ses données fictives sont
supprimés après conservation privée du rapport et de la recette : archive locale
`setupsurvie-0374-aide-generale-prive.tgz`, **7 389 octets**, SHA-256
`2be0b4e7ff9047c2b3f2826f504bfd074f9019c3f4ea07f1b37942bb52fdc0d8`.
Les empreintes moteur/contexte observées correspondent aux fichiers candidats.
Le modèle préexistant et les services restent intacts ; son maintien est 15 s.
La CI complète reste en cours avant livraison.


## Intégration avec les travaux parallèles

Candidat préparé en 0.37.4 ; la refonte du volet des projets est ensuite fusionnée
en 0.38.0 sur main. La livraison corrective devient **0.38.1** après fusion
normale, sans modification des composants UX. Les essais réels conservent leurs
empreintes initiales ; moteur et contexte restent identiques après cette fusion,
la version API change. La CI doit valider l’état réuni avant livraison.


## Paquet candidat vérifié

Source `65c3758c980dddb0eec5dfaca3a53537961c8d6d` : **976 fichiers**, **17 252 598 octets**
décompressés, ZIP **7 716 960 octets**, SHA-256
`994e83f0630fbce5ee0c10f2e7015b98dc38d3a30e042ef18984dc4d772f0beb`.
Chaque octet du paquet est comparé à Git avec ses filtres, ainsi qu’aux tailles
et empreintes du manifeste. Version API/manifeste 0.38.1 et schéma personnel 1.
Ce reçu est postérieur au paquet, donc non prétendu inclus dans son contenu.
Les **1 271 liens locaux et ancres Markdown** sont contrôlés sans cible manquante.
Le paquet vérifié ne prouve pas un déploiement sur un PC client ; la CI réunie
et la fin de la seconde suite locale restent attendues avant fusion.
