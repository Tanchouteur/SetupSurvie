# Conserver les faits documentaires à côté de la réponse

**Bilan de livraison — 0.15.0, 15 novembre 2026.** Suite du moteur 0.14.3.
Le chantier fiabilité doit distinguer recherche effectuée, document trouvé,
passage consulté et source citée. Les tests d’orchestration sont simulés ; aucun
LLM, corpus ou téléchargement lourd n’est lancé dans le runner CPU.

## Problème constaté et portée du changement

Les outils transmettaient déjà `coverage` au modèle, et les citations finales
conservaient seulement les sources lues puis citées. Cependant, une erreur de
rédaction du modèle pouvait encore annoncer l’absence de documents sans que
l’utilisateur voie un état documentaire indépendant. Les sources lues mais non
citées n’avaient pas non plus d’accès dans cette réponse terminée.

Un test reproduit ce cas : recherche partielle avec résultat et texte de source
effectivement transmis, puis réponse fictive disant qu’aucun document n’existe.
La nouvelle ligne conserve les faits observés même si ce texte est faux. Elle ne
réécrit pas la réponse, ne garantit pas son exactitude et ne transforme pas les
consignes du système en validation automatique du modèle.

## Ce qui est livré

Les nouvelles réponses avec opérations documentaires proposent une ligne
repliée **Recherche limitée · 1 source consultée**, ou un état adapté. Son détail
indique périmètre, demandes différentes, résultats proposés, lectures échouées et
consultation par passages. Les compteurs distinguent les recherches réutilisées
et les sources uniques ; relire la même source n’augmente pas ce nombre.

Les documents effectivement consultés disposent de leurs propres boutons, même
sans citation du modèle. Les références numérotées restent les citations de la
réponse : les deux listes ont un rôle différent. Au plus douze liens documentaires
sont conservés, avec identifiant et titre bornés. Aucun lien de recherche seul
n’est présenté comme une source lue. Les titres sont insérés comme texte.
Un texte d’extraction vide n’est plus enregistré comme source consultée ou citée,
y compris pour un document associé. Une extraction vide ne déclare pas ce document
absent : le modèle reçoit cette limite et le suivi conserve la lecture échouée.

Les demandes complètes sans résultat disent **Aucun résultat pour ces recherches**
et rappellent que cela n’établit pas une absence générale. Une recherche ciblant
une collection, les favoris ou l’espace résilience conserve cette portée.
Une panne ou une couverture inconnue ne devient pas une réussite. Une lecture
par passages reste signalée sans compter un livre comme entièrement lu.

L’ouverture et le focus clavier du suivi restent stables pendant les mises à
jour de la réponse. Après enregistrement et rechargement, les mêmes faits et liens
reviennent. Les anciennes conversations restent sans observations inventées.
Les fonctions de recherche, cartes et paramètres ne sont pas réorganisées.

## Données, compatibilité et échecs optionnels

`pilot/documentary.py` collecte les observations d’outils ; le texte de la réponse
ne peut pas lui attribuer un résultat. `engine.DOCUMENTARY` fournit l’état vivant.
La table optionnelle `documentary_evidence` garde un résumé versionné, associé
à la conversation, à la demande et au message final. Les anciens champs de
`messages` et `jobs` restent identiques ; le schéma global compatible reste 1.

La liaison à une conversation et au message assistant est vérifiée. Les mêmes
contrôles du profil s’appliquent aux API de conversation et de demande ; cette
isolation range les données mais ne change pas le choix libre des profils locaux.
La suppression de conversation supprime son suivi. Un nettoyage des demandes
terminées ne supprime pas celui déjà lié au message.

Les observations sont écrites dans la transaction de la réponse finale, sans
écritures synchrones supplémentaires à chaque outil. En cas d’annulation ou
d’échec, un résumé des opérations déjà observées est conservé avec la demande,
sans fabriquer de message assistant final. Le redémarrage ne reconstruit pas
un suivi vivant perdu avant cet enregistrement ; une coupure physique reste
distincte d’un arrêt logiciel testé.

Les mesures exportables de l’assistant contiennent seulement état, périmètre et
compteurs. Leurs champs documentaires sont filtrés : pas de question, réponse,
texte source, titre, identifiant ou chemin documentaire dans cette partie des
mesures. Les liens et titres restent privés dans la conversation. Les traces
privées d’outils existantes restent distinctes de ces exports numériques.

L’absence ou la panne de la table optionnelle ne bloque pas la réponse. Le suivi
historique manque alors, mais un repli numérique de la demande peut rester dans
ses mesures. Une version antérieure peut lire les conversations sans connaître
cette table. Le paquet conserve images, index et données documentaires ; aucune
réindexation n’est requise. Le cache Web du JavaScript et du CSS est actualisé par
le générateur, sans modifier les contrôles de l’ancienne présentation conservée.

## Vérifications exécutées

Les tests ciblés couvrent erreur et absence de résultat, contexte restreint,
recherche réutilisée, source non lue, lecture échouée puis reprise, liens bornés,
confidentialité des mesures, accès par profil, conversation ancienne, table absente,
suppression et conservation après nettoyage des demandes. L’orchestration réelle
du logiciel avec HTTP simulé vérifie une réponse fausse du modèle, un échec de
lecture automatique, l’annulation et la persistance sans message inventé.

Le nouveau parcours navigateur vérifie 25 assertions : suivi indépendant, sources
non citées ouvrables, conservation au rechargement, ouverture/focus pendant les
mesures, absence de débordement à 1366/390/320 pixels et titres non interprétés
comme HTML. Sur l’image Playwright déjà en cache, **Chromium et WebKit réussissent
chacun 130 assertions ciblées** : suivi 25, recherche 50, flux 18 et confort du
chat 37. Le parcours du suivi est aussi exécuté avec le Playwright MCP.

Les sources et modèles de ces essais sont fictifs. WebKit émulé ne valide pas
Safari sur un iPhone réel ; ces quatre recettes ne sont pas une campagne complète
de toutes les fonctions du site. Le moteur documentaire lui-même reste celui
validé en 0.14.3 sur petites archives ; cette livraison ne prétend pas refaire une
mesure sur le fonds Windows de Marc.

La suite locale finale réussit **593 tests, trois ignorés**, en 85,947 secondes,
dont onze tests propres au suivi et vingt-sept d’orchestration après les nouveaux
cas d’extraction vide. Les pages générées correspondent au générateur, le JavaScript
est syntaxiquement vérifié et les liens documentaires modifiés sont contrôlés.
`git diff --check` passe. Le paquet et la CI sont consignés après leur exécution.

Le code `496083b` est poussé. La [CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43705794886)
est refusée avant les huit jobs : GitHub signale des paiements échoués ou une
limite de dépenses à relever. Aucun test Windows, lecteur Python isolé ou routage
n’est exécuté par cette campagne. Les 130 assertions par navigateur ci-dessus
sont des essais locaux, distincts de cette CI non démarrée ; pas de contournement
de la restriction ni de relance répétée.

Le paquet est déballé par le lecteur normal : **753 fichiers**, 6 681 313 octets,
version 0.15.0 et schéma compatible 1. Tous les fichiers correspondent au commit
avec ses filtres de checkout, notamment CRLF pour PowerShell. Aucun modèle,
archive ZIM, cache, index ou état privé n’est inclus. SHA-256 :
`88da041ec5e32b1e3fe7fbe52eb6530fe86e302e498f438e8e6721209aff3f45`.

## Recette réelle restant nécessaire

Mettre à jour normalement vers **0.15.0**. Le prochain R2 sans IA mesure le moteur
0.14.1–0.14.3 conservé. Le R4 volontaire doit observer une réponse de modèle réel :
recherche de documents, lecture, limites affichées, source citée et document non
cité ouvert depuis le suivi. Le mode jeu reste respecté ; le logiciel ne démarre
pas de modèle pour remplir ce suivi à l’avance.

Le [guide des sources](../utilisation/sources-et-fiabilite.md) explique le sens
des mentions. Le suivi ne ferme pas l’objectif de fiabilité sans lecture humaine,
mesures réelles et contrôle hors ligne ; il rend les limites examinables.
