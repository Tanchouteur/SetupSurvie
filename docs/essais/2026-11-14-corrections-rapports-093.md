# Corrections après les rapports réels 0.9.3

**Bilan daté — version corrective 0.9.4, 14 novembre 2026.** Répond aux
[trois rapports reçus](2026-11-14-rapports-recherche-093.md). L’indexation réelle
est terminée ; les recherches partielles et les correspondances faibles restent
le problème à traiter. Aucune mesure de pertinence sur le fonds complet n’est
déduite des tests ci-dessous.

## Ce qui bloquait et ce qui change

L’ancien ordonnanceur rangeait les lots par groupe de langue : plusieurs lots
français pouvaient précéder les premières collections pratiques anglaises. Le
vrai index d’une archive était pris en compte après le tri, trop tard pour
corriger sa priorité lorsqu’un ancien tag l’annonçait absent. La 0.9.4 trie avec
le résultat d’indexation réel, entrelace les lots selon leur priorité et tient
compte du sujet pour les collections spécialisées.

Les lots passent de six à douze archives compatibles. Une archive connue de
10 Go ou plus, ainsi que Wikipédia, reçoit sa propre requête : son expiration
ne fait plus échouer les petites archives associées. Les quatre recherches de
titres privilégient plusieurs familles avant de remplir les places restantes ;
trois variantes Wikipédia ne prennent plus systématiquement trois places.

Les reformulations littérales d’un lot pratique vide sont prioritaires dans la
file, au lieu d’attendre toutes les collections générales. Une formulation
identique à la première n’est pas répétée. Les autres replis attendent la fin
du premier passage. Les limites restent explicites : 32 requêtes, deux appels
plein texte et deux appels de titres partagés ; pas de multiplication après
une expiration. La phase d’interrogation des archives reçoit un maximum de
douze secondes au lieu de six. Cela peut allonger une recherche difficile ;
ce plafond ne certifie pas la couverture du fonds ni le temps total du portail.

Les appels partagés comptent désormais leurs lecteurs. Le départ d’un seul ne
coupe pas la demande d’un autre ; le dernier départ annule le travail client,
y compris une attente de créneau. Un ancien essai ne conserve plus sa propre
file de requêtes abandonnées. Ce résultat ne prouve pas qu’un calcul natif déjà
commencé sur le serveur s’interrompt instantanément lors de la fermeture HTTP.

## Correspondances et contexte de l’assistant

Une requête complète envoyée à Kiwix ne constitue plus une preuve que son extrait
visible couvre les mots demandés. Les correspondances partielles sont vérifiées,
l’action pratique doit être étayée et les modèles d’inventaire sans rapport
direct avec le sujet ne sont pas proposés comme méthodes de réparation.
Les documents techniques nommés sans extrait restent possibles : un titre tel
que « Pedal powered generator » n’est pas supprimé faute de paragraphe visible.
Une procédure examinée humainement garde son rôle ; cette sélection ne certifie
pas automatiquement la qualité d’une fabrication.

L’intention d’allumage distingue « Fire We Make » d’une méthode de production de
feu. Le vocabulaire de fixation rapproche fixer/fixing/attaching, pour conserver
le cas de la bâche malgré le filtrage plus strict. Si le modèle raccourcit la
recherche préparatoire à son seul sujet, l’assistant réutilise l’intention de la
question courante ; une nouvelle action explicite reste une nouvelle recherche.

Chaque résultat de recherche contenait auparavant la progression complète des
135 archives dans `coverage.local_index`, également transmise aux outils de
l’assistant. Sur le premier cas du rapport réel, une sortie équivalente
`results + coverage` représente 28 010 caractères et une estimation interne de
15 340 jetons. Sans répéter le manifeste, elle représente 4 590 caractères et
2 548 jetons estimés. Ce ne sont ni des mesures du tokenizer du modèle ni des
durées de génération. Le rapport R1 complet reste disponible ; seuls les compteurs,
le contrôle du lecteur et les catégories d’erreur accompagnent chaque recherche.
Ce défaut de volume n’est pas attribué à l’expiration du comparatif de
reformulation : celui-ci envoie au modèle la question, sans ce manifeste.

## Piste éprouvée et non retenue

Un essai sur le Kiwix épinglé et quatre articles synthétiques compare espaces,
`AND`, guillemets et préfixes `+`. Les deux mots littéraux retrouvent leur article,
mais l’ajout de `AND` ne convient pas à ce parseur. La correction n’impose donc
pas de syntaxe booléenne supposée fonctionner. La CI garde une vérification de
ce comportement avec des archives générées, sans corpus téléchargé.

## Vérifications et limites

Les nouveaux tests couvrent un catalogue simulé de 134 collections, les tags
contredits par l’index réel, les langues prioritaires, l’isolement des grosses
archives, les reformulations avant les lots généraux, l’annulation partagée,
les faux candidats, le volume de réponse et le cache d’intention de l’assistant.
La référence de 32 demandes est conservée.
Le premier essai Kiwix réel a également refusé « inconnu eau potable » : le filtre
exigeait tous les concepts pour les demandes non pratiques. Le seuil conserve
désormais une majorité de concepts concrets, sans rétablir la confiance aveugle
dans le marqueur de requête native. Ce cas positif et le cas négatif de propulsion
restent vérifiés séparément. Les 31 contrôles Kiwix passent ensuite sur cinq ZIM
générés de 283 260 octets au total, sans modèle ni corpus réel.

La suite locale termine **495 tests, dont trois ignorés sous Linux**, sans échec.
Les huit tâches de la [CI sur `dd108e8`](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43630834195)
réussissent : Linux, Windows, lecteurs isolés Windows Python 3.11/3.13/3.14,
Kiwix réel synthétique, routage OSRM synthétique et navigateurs. Le contrôle
d’interface comprend 48 vérifications de recherche et 18 de ses outils sur
chacun des navigateurs Chromium et WebKit ; il ne remplace pas Safari sur iPhone.
Le premier passage de routage a échoué au téléchargement de l’image épinglée
avec une connexion réinitialisée ; la relance sur le même code réussit, sans
modification du routage. Les liens documentaires locaux et `git diff --check`
sont vérifiés avant publication.

**Niveau 0.9.4 retenu :** corrections compatibles du moteur existant, sans nouvel
écran, changement d’image tierce ni migration de données. Le comparatif IA reste
désactivé par défaut et respecte les quinze secondes choisies dans le rapport.
Le [journal depuis 0.2.0](journal-recherche-depuis-020.md) prépare le futur résumé.
La nouvelle mesure R2 et la lecture humaine des sources restent à faire chez Marc.
