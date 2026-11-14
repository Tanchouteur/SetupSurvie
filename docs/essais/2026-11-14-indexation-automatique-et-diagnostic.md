# Indexation automatique et diagnostic de recherche

**Bilan en cours — 0.4.0, 14 novembre 2026.** Suite de l’objectif utilisateur
« Finir cette première version fiable du moteur de recherche ». Ce bilan couvre
le lot L1 et une partie de L2 ; il ne clôt pas les autres lots ni la recette réelle.

## Changements

- Téléchargements vérifiés et copies contrôlées de kit alimentent une file durable.
  Le contrôleur enchaîne l’indexation après libération des verrous, avec reprise
  explicite des interruptions, pause volontaire prioritaire et créneau nocturne.
- Outil séparé préparé à l’installation en ligne, cache de roues vérifiées pour
  les kits et commande de préparation d’une autre cible. Aucun modèle supplémentaire.
- Processus indexeur enfant identifié, publication par archive, manifeste cumulatif,
  CPU/RAM disponibles pris en compte. Un nouveau lot ne fait pas oublier les anciens.
- Catalogue Kiwix partagé pendant 30 secondes entre les requêtes, lecture simultanée
  regroupée et dernier instantané valide daté si le catalogue devient indisponible.
  Les erreurs de délai, connexion, HTTP et format restent distinctes.
- Diagnostic exportable : accès Kiwix depuis le pilote, état du catalogue, index,
  dix recherches dont comparaison « faire du feux » globale et filtrée. La préparation
  du diagnostic est mesurée séparément des recherches, qui peuvent bénéficier du cache.
- Avertissement de recherche partielle plus visible ; mentions du sujet distinguées
  des correspondances directes dans le titre. Aucun type de procédure n’est certifié.
- Index locaux périmés ou illisibles signalés ; index correspondant à un ZIM supprimé
  ignoré. Les limites d’indexation des vidéos, images et gros articles restent explicites.

## Éléments réellement vérifiés pendant le développement

Tests du catalogue : lecture concurrente unique, cache, instantané conservé après
échec et redémarrage, catalogue vide distinct d’une panne, réponse HTML invalide,
raison sûre sans recopier le corps HTTP. Petits ZIM réels générés : création,
interruption/reprise, index enfant à deux processus, publication puis acquittement
de la sélection dans la file, source supprimée et SQLite corrompu.

Tests de file : seulement les ZIM publiés après vérification, rejet d’une empreinte
fausse, dédoublonnage, protection contre l’acquittement d’une nouvelle édition par
un ancien travail, conservation de pause et de sélection, mode jeu distinct d’une
IA arrêtée, plages traversant minuit et processus enfant vivant.

Kiwix 3.8.1 réel : vingt contrôles sur cinq ZIM générés, environ 280 Ko, sans corpus
ni modèle. Les tests d’interface et la CI de livraison doivent être consignés après
leur exécution. Une simulation ne valide ni la vitesse du HDD ni les modèles réels.

## Recette à demander chez Marc

Après mise à jour, préparer l’outil si nécessaire puis lancer une première fois
**Créer ou reprendre les index** pour le fonds existant. Exporter le rapport
d’indexation et **Vérifier la recherche** (dix cas). Ajouter ensuite un petit lot
pour vérifier l’enchaînement automatique et une relance sans nouvelle extraction.
Le diagnostic peut révéler l’incident intermittent ; aucune cause spécifique n’est
attribuée à la première capture sans ce résultat.

**Version mineure 0.4.0** : nouvelles fonctions compatibles et fichiers d’état
séparés ; schéma existant 1 et images tierces conservés. Le plein fonds Windows,
la préparation réelle du kit hors ligne, la vitesse et la fidélité des réponses
restent à mesurer ; l’objectif global demeure actif tant que les critères du
[plan](../decisions/plan-ameliorations-marc.md) applicables au moteur ne sont pas prouvés.
