# Titres de tâche, questions périphériques et sujets exacts

**Bilan daté — 0.14.3, 15 novembre 2026.** Suite du
[R2 réel 0.14.0](2026-11-15-rapport-0140-et-traitement-progressif.md), après les
correctifs de traitement et de plafond 0.14.1/0.14.2. Aucun accès au PC de Marc,
modèle ou corpus lourd n’est utilisé. Les titres observés motivent les tests ;
les extraits de reproduction sont fictifs, pas des copies d’articles lus.

## Ce qui est reproduit

Le rapport classe une question sur le changement de tableau électrique avant
l’installation solaire, une réparation d’écran d’autoradio avant un titre de
diagnostic radio, et un vélo de collection avant « Histoire du vélo ».
Ces sujets restent dans le besoin général ; l’anomalie concerne l’ordre proposé,
pas une preuve d’inutilité de tous ces documents.

Trois mécanismes sont reproduits avec les mêmes titres et des extraits fictifs
identiques, pour isoler le poids du titre :

- Le mot « installation » dans une question périphérique recevait le même bonus
  qu’un titre d’installation. « How many… » était traité comme « How to… ».
- Un titre expliquant comment diagnostiquer ou réparer n’avait pas de préférence
  face à un cas très spécifique citant le même sujet et le même verbe.
- La comparaison exacte utilisait les mots de requête sans mots de liaison :
  `histoire velo` ne correspondait pas au titre `histoire du velo`.

Les quatre cas en échec dans la première campagne ciblée passent après correction.
Leurs scénarios restent des cas observés, pas une nouvelle évaluation aveugle.
La référence de 32 besoins est conservée ; aucune source n’est ajoutée à une liste
spéciale et aucun nom de site, de marque ou identifiant réel n’est privilégié.

## Comportement conservé

Pour une demande pratique, le bonus de tâche directe distingue maintenant les
questions « should I… », « how many… », « combien… », les risques et les aperçus
historiques. Les titres « comment… », « how to… », guide ou manuel disposent
d’un petit bonus supplémentaire s’ils portent déjà sur l’action et le sujet.
Un titre commençant par « DIY… » peut aussi recevoir ce bonus, en conservant
la distinction des contextes : la présence de « DIY » au milieu d’une question
périphérique ne suffit pas à la faire passer pour une procédure.
Une explication « pourquoi et comment… » garde sa dimension pratique.

La comparaison exacte accepte aussi la requête originale normalisée, avec ses
mots de liaison. « Histoire du vélo » et « Les fractions » retrouvent ainsi leur
bonus de sujet exact. Le cache de normalisation 0.14.1 réutilise cette comparaison.

Les questions périphériques et les aperçus de risques restent dans les résultats.
Des demandes qui les citent explicitement continuent de les trouver. Une
correspondance de titre reste une piste de lecture : aucun type de document,
validation humaine ou statut de sécurité n’est créé par ces points de classement.
Une question dont le titre commence par « how to » peut avoir un contenu pauvre ;
la présente correction ne remplace pas sa lecture.

## Vérifications et limites

Les douze tests de titres/intention passent : les huit précédents et quatre
nouveaux, avec variantes françaises/anglaises, questions et risques explicitement
demandés, manuels, conservation des sources et métadonnées toujours non validées.

Le Kiwix épinglé passe **63 contrôles** sur cinq archives générées totalisant
**290 378 octets**. Les neuf nouveaux contrôles retrouvent les sources fictives
attendues pour solaire, radio et histoire, conservent leurs contextes et ouvrent
les trois sources sélectionnées. Ils complètent les lectures de chemins spéciaux,
alias, plein texte, titres seuls et compléments multilingues déjà présents.

La suite complète finale réussit **575 tests, trois ignorés**, en 81,835 secondes dans
le runner Linux. La recette de 135 archives fictives (8 280 525 octets) passe
également ses **36 contrôles** de sources, couverture, progression et caches.
Les huit besoins y retrouvent leurs sources. Les liens et ancres modifiés sont
vérifiés, `git diff --check` passe. Paquet et CI sont consignés après exécution.
Les titres du rapport de Marc ne suffisent pas à reproduire ses extraits complets,
leur rang natif ou l’intégralité des candidats ; le nouvel ordre réel reste donc
à mesurer. Aucun guide réel n’est déclaré relu ou qualifié par cette campagne.

Les budgets 0.14.2, cache et compteurs 0.14.1, schéma privé 1, composants et fichiers
Web restent inchangés. Pas de nouvelle indexation requise pour corriger ces scores.

Le code `44c280d` est poussé. Le [passage CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43699180773)
ne lance aucun de ses huit jobs : même restriction de facturation GitHub que
les deux livraisons précédentes. Aucune relance répétée ou intervention sur le
compte n’est faite ; Windows et WebKit de cette version ne sont pas déclarés validés.

Le paquet est déballé par le lecteur normal : **749 fichiers**, 6 663 741 octets,
version 0.14.3 et schéma 1. Tous correspondent au commit avec les filtres de
checkout Git, dont CRLF des scripts PowerShell. Aucun corpus, modèle, index ou
état privé n’est inclus. SHA-256 :
`6dae70a26dbdf29ed5e50b7733f29f5e4439824ef235500228c8ac16b6dea046`.

## Prochaine mesure

La prochaine recette R2 porte sur **0.14.3**, qui inclut les trois correctifs.
Comparer les premiers titres, délais, couverture et compteurs de traitement.
Lire les sources avant de choisir les avis humains, encore absents du R2 0.14.0.
Les besoins radio et solaire sont désormais explicitement à examiner, en plus
de feu, eau, générateur et vélo. Le [guide de recherche](../utilisation/recherche-documentaire.md)
reste la procédure courante ; pas de traitement de modèle imposé en mode jeu.
