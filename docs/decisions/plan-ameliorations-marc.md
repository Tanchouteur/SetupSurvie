# Améliorations issues des retours de Marc

**Plan retenu et suivi actuel — 14 novembre 2026.** Louis demande sa mise en
œuvre et la conservation des idées explorées, retenues, reportées ou abandonnées.
La 0.3.0 commence ce plan ; sa présence dans le code ne valide pas le fonds réel.

| Lot | Décision et résultat attendu | État |
| --- | --- | --- |
| Mesurer le fonds réel | Comparer les recherches naturelles aux sources réellement utiles ; distinguer absent, non indexé, mal classé et panne | Premier rapport reçu le 14 novembre, version 0.2.0 ; nouvelle comparaison chez Marc à effectuer |
| Indexation manquante | Index local SQLite du texte des ZIM dépourvus d’index Kiwix réel, progressif, reprenable et pilotable depuis le site | Implémenté en 0.3.0 sur petites archives réelles générées ; création sur le fonds de Marc non exécutée |
| Recherche et CPU | Réserver les titres, prioriser les collections utiles, paralléliser selon les CPU et conserver le site réactif | Implémenté en 0.3.0 ; latence et charge Windows à mesurer |
| Deux espaces | Autonomie et résilience par défaut, Savoirs et culture, et recherche globale ; fichiers conservés une seule fois | Filtres par article implémentés en 0.3.0 ; classement automatique provisoire, catalogue éditorial complet à faire |
| Utilité des résultats | Distinguer une présentation d’une procédure, qualifier étapes, matériel et schémas ; compléter les lacunes confirmées | Intention réparation/conservation/potabilisation améliorée ; qualification humaine des guides et fabrication à faire |
| Collections | Regrouper source/chaîne et nommer les variantes sans casser l’ouverture directe | Regroupement 0.1.36 conservé ; révision éditoriale de toutes les variantes à faire |
| Assistant et contexte | Recherche commune, citations lues, contexte par modèle et réduction cohérente de l’historique | Défaut 16k et réglages 8/16/32/64k en 0.3.0 ; calibration RAM/VRAM et délais réels à faire |
| Traduction de lecture | Lire en français / Voir l’original, traduction locale conservée dans les lecteurs | Accès au moteur existant livré ; lecture traduite intégrée Kiwix/PDF à développer |
| Vidéos | Inventorier les pistes, exposer les sous-titres existants, puis transcription/traduction synchronisée locale | À développer et qualifier sur les archives réelles |
| Livres longs | Reprise, contrôles techniques, terminologie et essai progressif jusqu’à 500 pages | Moteur existant par passages ; cohérence et livre réel non validés |
| Apprendre par thème | Objectifs concrets, prérequis, documents, étapes et lacunes | Libellé clarifié ; contenu guidé à construire et relire |
| Maison de Solliès-Ville | Équipements réels, notices, entretien ; stocks éventuels | Reporté, IDEE-001 |

## Choix retenus et pistes écartées

- **Retenu : deux espaces dans le même produit**, classification par article,
  lien permanent vers toute la bibliothèque et conservation des documents.
  **Écarté : deux installations ou un partage physique par éditeur** ; Wikipédia
  et Appropedia mélangent informations techniques et culturelles.
- **Retenu : vérifier l’index réel**, conserver les index Kiwix fonctionnels et
  compléter ceux qui manquent. Une étiquette `_ftindex:no` ne constitue pas une
  preuve suffisante. Le nouvel outil lit `has_fulltext_index` dans le ZIM.
- **Retenu : plusieurs cœurs, accès disque bornés et tâches annulables**.
  **Écarté : lancer toutes les requêtes ou charger tout le fonds en RAM** ; cela
  ne rendrait pas les archives plus pertinentes et pourrait saturer le disque.
- **Retenu : augmenter le contexte utilisable**, avec réglage par modèle et
  comparaison 16k/32k sur Windows. **Écarté : imposer le maximum théorique à tous
  les modèles ou prétendre qu’occuper toute la RAM améliore la vitesse**.
  L’ajustement automatique selon mesures matérielles reste à réaliser.
- **À évaluer : reformulation ou reclassement IA**, puis recherche sémantique
  multilingue sur un échantillon si le gain est mesurable. Le socle sans IA est
  conservé ; aucun modèle supplémentaire n’est imposé dans cette livraison.
- **Firefox : complément à préparer et tester hors ligne**, sans en faire une
  dépendance de tous les lecteurs. La traduction d’une page ne crée pas les
  sous-titres d’une vidéo.

## Ordre et validation

1. Recette réelle, indexation manquante et pertinence des résultats.
2. Affinage des deux espaces, collections et qualification des savoir-faire.
3. Mesure de l’assistant et calibration du contexte par modèle.
4. Traduction de lecture, sous-titres et parcours réellement guidés.

Constituer environ 30 demandes de Marc et identifier les sources attendues.
Objectif : source utile parmi les cinq premiers résultats, variantes proches
cohérentes, quiz accessoire derrière une procédure disponible et absence annoncée
avec prudence. Les délais cibles sont à fixer sur la référence Windows réelle.
Chaque lot met à jour ce suivi et ses guides ; conserver les bilans datés.
