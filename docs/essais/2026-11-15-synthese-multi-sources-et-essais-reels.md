# Dossier multi-source et premiers essais IA réels

**Bilan daté du 15 novembre 2026 — livraison 0.16.0.** Ce lot améliore le parcours
de synthèse. Il ne clôt pas l’objectif d’un assistant fiable sur le fonds de Marc.
Les résultats défavorables restent consignés ; `done` ne signifie pas juste.

## Différence concrète et causes corrigées

La prélecture de deux débuts de documents ne suffisait pas à une synthèse de
plusieurs sources. Le nouvel outil `read_sources` prépare des passages liés au
sujet, avec leurs positions d’origine, en répartissant la place réellement
disponible. Douze candidats au maximum, trois lectures simultanées ; les doublons
et les sources illisibles ne bloquent pas les suivants. Cinq sources sont possibles,
sans fixer ce nombre pour toutes les questions. Le cache reste propre à la demande.

La première recherche reprend le budget long de 60 s du moteur commun et annonce
le nombre de résultats pendant l’attente. Une consigne après le sujet, telle que
« Compare les notices et cite leurs valeurs », reste transmise au modèle mais
ne devient plus une condition textuelle obligatoire pour trouver le sujet.

Les modèles disposent de la lecture par lot et de lectures supplémentaires ;
deux tours sans source ou passage nouveau arrêtent la répétition. Les appels
réellement exécutés et leurs résultats restent équilibrés dans la conversation.
Le budget de contexte inclut outils, historique, sortie et marge de format.

Le R7 a aussi exposé un gabarit de modèle pour lequel un message système final
pouvait supprimer le marqueur de génération de réponse. Les instructions de
confiance sont réunies au début. Pour les gabarits qui n’affichent les définitions
d’outils qu’après le dernier message utilisateur, ces définitions restent visibles
après les résultats. Les textes des outils ne deviennent pas des instructions système.

Pour une synthèse sans références reconnues, une étape JSON peut associer des
fragments numérotés par le serveur aux sources réellement lues. Elle ajoute des
liens sans réécrire les faits. Un échec conserve le texte utile avec avertissement ;
une source inconnue conduit au repli sur les extraits. Pannes, limites de temps et
annulations conservent le texte réellement reçu avec l’état correspondant.
Les mesures distinguent préparation, lecture et liaison des sources ; aucun
raisonnement privé n’est enregistré.

## Essais réels sur le R7

Louis a autorisé ce laboratoire et l’utilisation de VRAM libre même pendant la
location. Les autres tâches n’ont pas été arrêtées. Code et Python isolés, aucun
compte ni corpus réel ; cinq notices fictives avec une longue introduction avant
les faits. La [recette reproductible](assistant-modele-reel.md) précise les options
et limites. Ollama natif **0.40.14**, distinct du **0.40.13** épinglé dans le pilote.
Aucune version tierce du projet n’a changé.

Le digest des fichiers `pilot/*.py` du candidat testé est
`903ce5fd3fb07b13088db489613a24c08250b36e458fc34f5fd35fdb04102adf`.
Les rapports sont privés ; les temps ci-dessous incluent préparation et inférence.
Le candidat testé après les corrections de fermeture du cache a pour digest
`a01cdd1fb0d602f8e7a759dcc91f3b302ded96ad517206734128ed8195c26bfd`.

| Code et modèle | Résultat observé | Limites |
| --- | --- | --- |
| 0.15.1, Gemma4 E4B, formulation avec comparaison | 30 807 ms ; zéro notice lue, aucune des cinq valeurs ; affirmation d’absence | Même corpus et options que l’essai partiel 0.16.0 ; un seul passage par formulation, pas un benchmark statistique |
| 0.16.0, Gemma4 E4B, demande simple | 45 102 ms ; cinq notices lues et cinq associations valeur/notice correctes, références directes | GPU complet ; la marge vidéo a refusé le lancement du cas suivant. Texte trop verbeux et dates non rappelées ; pas une réussite de tous les critères éditoriaux |
| 0.16.0, Gemma4 E4B, formulation avec comparaison | 70 027 ms ; cinq notices et valeurs correctes, tableau et références directes, nature fictive conservée | Huit couches GPU, six threads, contexte 16k, réflexion activée, sortie maximale 4 096 tokens. Dates non rappelées ; corpus étroit |
| Candidat 0.16.0 après correction du cache, Gemma après préchargement réel de Llama | 83 606 ms ; passage à Gemma préparé en 4 076 ms, aucune reprise, cinq valeurs, références, dates et éditions correctes | Première demande après changement ; Linux/R7, pas Windows. Ce passage a fourni directement ses références |
| 0.16.0, Llama3.1 8B, deux formulations | 58 465 / 44 755 ms ; cinq notices lues et cinq valeurs présentes, références ajoutées par l’étape structurée | **Échec de fidélité sur la demande simple** : obsolescence et absence de précision inventées, attribution groupée trop large. La demande avec comparaison associe correctement les cinq valeurs, mais ajoute du texte technique inutile |

Gemma : digest
`dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c` ;
Llama : `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.
Gemma est ajouté au R7 pour ces essais ; les trois modèles préexistants restent
intacts. Aucun téléchargement de modèle dans le runner CPU.

Empreintes SHA-256 des rapports privés :

| Essai | Empreinte |
| --- | --- |
| Gemma 0.15.1 | `5dfdcd8e5610678cb0f362834b02a61e4943cec94ad0408a2211affb14ee369f` |
| Gemma simple 0.16.0 | `b2020d955b6b7e9ba33445205fa10c30848d06a7e2c01f6df148f8d27d62590a` |
| Gemma comparaison 0.16.0 | `c91d9680b8b2cfc5072113d309df19c0da3523209663193a50e5701a72a1eb42` |
| Llama, fragments 0.16.0 | `f5e7f5179a94d69a304a8c2fc7c0d7e68b43fe8a49bd20e24f99fa66685977ad` |
| Gemma, changement de modèle final | `d364a105b864f6a633c9bb42aa5d1828d7033fa42398c520cbee2648e2fdf137` |
| Liaison Gemma sans réflexion, étape isolée | `865f7d36bc00730dbc836014aa41818400d79b2700b6d02c881c6c12ae20c6a0` |

Un autre passage après changement de modèle avait correctement rédigé les cinq
faits et dates mais épuisé les 2 048 tokens de liaison en réflexion : **155 336 ms,
état incomplet**. Le texte utile restait conservé. La liaison conserve désormais
le modèle et réduit uniquement sa réflexion (désactivée ou `low`, selon le profil).
L’étape isolée sur ce brouillon réel et les extraits lus du même corpus a terminé
en **13 343 ms**, 190 tokens, huit liens admis, zéro rejet. Ce n’est pas un nouvel
essai complet de conversation. Le contrôle de l’affichage a ensuite repéré que
des liens ajoutés après le dernier `|` d’un tableau étaient masqués par Markdown :
ils sont maintenant insérés dans sa dernière cellule. Rejeu de la même proposition
JSON : cinq lignes, trois cellules chacune, un lien visible par notice. Ce dernier
correctif serveur ne change ni les fragments transmis au modèle ni leurs identifiants.

## Pistes explorées, conservées ou abandonnées

- **Conservé :** sélection déterministe de passages, cache de lecture, préparation
  avant le modèle, adaptation aux gabarits et boucle d’outils avec arrêt sans progrès.
- **Conservé avec limite explicite :** liaison structurée par identifiants de fragments.
  Le serveur vérifie l’existence des fragments et des sources lues, pas la fidélité
  de toutes les affirmations. Le résultat Llama en montre la limite réelle.
- **Abandonné :** régénérer toute la réponse uniquement pour obtenir des citations.
  Lors d’un essai R7, cela a remplacé des faits corrects par une affirmation d’absence.
- **Abandonné :** demander de recopier exactement une phrase pour l’identifier.
  Les propositions ne correspondaient pas exactement au texte : cinq ou douze
  liens rejetés selon le cas. Les identifiants serveur évitent cette copie fragile.
- **Insuffisant comme seule validation :** CPU/deux threads, jusqu’à environ treize
  minutes dans un essai initial. Le placement partiel utilise les ressources libres
  autorisées ; aucune cadence du R7 ne prédit celle du Windows de Marc.

## Vérifications automatisées et livraison

Runner Linux Python 3.13 : **649 tests, trois ignorés**, avant le dernier contrôle
de cellule de tableau, puis cinq tests ciblés de liaison réussis. Aucun modèle réel
n’est exécuté dans ces tests. Ils
couvrent notamment passages tardifs, procédures face à l’historique, UTF-8,
contexte réduit, cinq sources, doublons, échec de lecture, provenance des
traductions, annulation, références fictives et outils répétés.

Chromium et WebKit : **85 contrôles par navigateur** (confort 37, suivi documentaire
25, mesures 23), tailles ordinateur et téléphone. Aucun essai physique iPhone.
JavaScript vérifié, HTML régénéré ; recherche sans IA, cartes, comptes et schéma
de données compatible 1 conservés. Aucun modèle conseillé remplacé.

La première CI du candidat `bf0dca1` a passé sept jobs puis échoué sous Windows :
`poll()` sur un canal fermé levait `BrokenPipeError` après une réponse du processus
de diagnostic. Le lecteur conserve maintenant le résultat reçu et distingue
fermeture prématurée et échéance. Deux simulations reproduisent ces situations.

La seconde CI sur `f2e4594` a ensuite exposé un accès SQLite encore ouvert après
annulation : le résultat réseau n’était plus mutualisé, mais son thread disque
n’avait pas terminé. Le suivi conserve maintenant ces accès jusqu’à fermeture,
et l’arrêt du pilote ferme le cache après les travaux de l’assistant. Un nouveau
test reproduit ce défaut sous Linux aussi : il échoue avant, réussit après.
Le résultat de la CI finale et le reçu du paquet sont ajoutés après vérification.

**Version mineure 0.16.0 :** nouveau parcours fonctionnel de lecture multi-source,
sans migration du schéma ni rupture de l’installation. Aucun déploiement chez Marc.

## Ce qui reste nécessaire

Relire des synthèses sur des sujets variés, contradictions et sources réalistes,
avec les modèles recommandés, puis mesurer le Windows de Marc. Les deux demandes
de ce corpus ont servi au développement ; elles ne constituent pas un examen
aveugle ni une validation du sens de toutes les réponses. Les dates et la concision
doivent encore être améliorées côté modèle.

Association manuelle de plusieurs documents, longues synthèses intermédiaires,
schémas originaux et interprétation des images restent à réaliser. Traduction et
acquisition/création des sous-titres restent les lots suivants du
[programme retenu](../decisions/plan-ameliorations-marc.md).
