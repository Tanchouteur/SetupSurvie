# Première consolidation du moteur de recherche — 0.1.36

**Bilan daté du 14 novembre 2026.** Implémentation issue du
[retour de Marc](2026-11-14-retour-experience-marc.md). Runner Linux CPU, documents
minuscules et moteur conversationnel simulé. Aucun corpus, modèle IA, carte,
conversation ou compte réel de Marc n’a été téléchargé ou modifié.

## Comportement livré

- Plan de requête et classement communs aux guides et archives. Les verbes de
  demande ne sont plus tous exigés dans les documents ; variantes techniques et
  FR/EN, titre, mots du passage et contexte pratique participent au classement.
- Récupération de davantage de candidats avant classement ; les mentions
  incidentes d’un quiz ou d’un règlement ne remplissent plus mécaniquement les
  premières places. Les autres intentions restent recherchables.
- Recherche de titres Kiwix dans quatre archives prioritaires ; recherches plus
  courtes après une première passe vide, avec budget global et limites explicites.
  Le nom d’une collection devient un filtre distinct, plutôt qu’un mot imposé
  dans chaque article. Les pages d’un PDF sont regroupées avec accès aux autres pages.
- Préparation des demandes pratiques/documentaires reconnues avant le premier
  appel au LLM : recherche puis lecture de deux sources au plus, réutilisation
  des appels identiques, relances de collection avec reprise du sujet utilisateur.
- Contexte compacté avant interruption : extraits bornés, échanges anciens
  abrégés et groupes d’appels d’outils conservés ensemble. Le rapide dispose de
  trois tours d’outils puis une réponse finale, les autres modes de six.
- Progression éphémère visible : recherche, lecture, préparation et rédaction.
  Aucune migration de données ni état « modèle chargé » inventé.
- Collections regroupées par source connue ou titre identique, variantes lisibles
  et liens conservés ; groupes ouverts mémorisés. Métadonnées descriptives Kiwix
  reprises lorsqu’elles sont disponibles, noms d’archives conservés en référence.
- « Apprendre par thème » remplace le libellé Parcours, avec explication de son
  rôle. Les modèles Markdown s’affichent avec titres et tableaux assainis.
- Accès à la traduction dédiée en haut d’une source anglaise du lecteur du portail.
  Ce bouton ouvre les commandes existantes ; il ne lance pas automatiquement
  une inférence et ne constitue pas une traduction instantanée de chaque lecteur tiers.
- Recette de huit recherches depuis Réglages, avec résultats et rapport JSON,
  utilisable sur Windows sans terminal. Elle mesure, sans proclamer les documents validés.

## Découvertes du test avec le vrai Kiwix

Le serveur testé est l’image **3.8.1 épinglée dans `deploy/versions.json`**, sans
changer sa version. `tests/kiwix_search_smoke.py` génère cinq archives synthétiques
avec `libzim==3.13.1`, pour environ 280 Ko au total, puis démarre Kiwix dans TEST.
Le service ne voit que ces fichiers en lecture seule, sans port publié, secret,
modèle ou bibliothèque réelle. Les requêtes HTTP sont exécutées dans ce service
via son `wget`, et le code réel `pilot.library` analyse les réponses. Cela ne teste
pas le transport HTTP du pilote vers un service de production.

Deux défauts échappaient à des réponses HTTP entièrement simulées :

1. Un index peut être présent et répondre alors que les tags du catalogue
   annoncent `_ftindex:no`. Ces tags ne servent plus à exclure l’archive ; les
   index annoncés sont prioritaires, les autres sont sondés dans le budget.
2. Les formulations booléennes `OR` essayées ne donnent pas la disjonction attendue
   avec ce serveur. Le repli Kiwix utilise donc des requêtes littérales distinctes,
   après les recherches primaires. SQLite FTS garde sa syntaxe propre.

Le test vérifie aussi les réponses multilingues refusées, le repli par titre
sans index plein texte, le filtrage Wikipédia, les titres sans balises de
surlignage, la lecture réelle de l’article et les requêtes feu, eau, générateur
à pédales et abri, y compris des formulations comportant un mot inconnu.

## Vérifications

- Suite Python complète : **356 tests, trois ignorés** selon les prérequis ;
  contrôles des secrets/gros fichiers et `git diff --check`.
- Pertinence sur passages fictifs : 18 formulations pratiques couvrant plusieurs
  besoins, quatre autres intentions, regroupement de pages, sujet inconnu, syntaxe,
  filtre de collection et fusion titre/plein texte indépendante de leur ordre d’arrivée.
- Orchestration sans modèle réel : préparation avant première inférence,
  citations réellement lues, cache d’appels, limites du rapide, reprise de sujet,
  réduction du contexte et suivi de progression.
- Playwright MCP Chromium et conteneur WebKit : 29 contrôles du nouveau parcours,
  dont groupes, mémoire, filtre/rechargement, bonne page PDF, traduction explicite,
  Markdown, progression, huit recherches, export et arrêt avec rapport partiel. La recette entre aussi en CI.
- Kiwix réel sur archives synthétiques : protocole et lecture ; le test rejoint
  un job CI dédié. Les tests de pertinence rejoignent également Windows.

## Limites et suite du chantier

Le classement reste lexical et explicable, avec un vocabulaire fini. Il ne
comprend pas toutes les intentions, négations, fautes ou langues ; il ne certifie
pas une procédure. Aucune recherche sémantique généralisée n’est ajoutée ni aucun
modèle téléchargé dans le runner. Les quatre archives prioritaires de titres
et le plafond de requêtes ne signifient pas que tous les titres du fonds ont été
interrogés. Les limites sont transmises à l’assistant et affichées au lecteur.

Les 755 Go et les modèles réels de Marc ne sont pas validés par ces essais.
La [recette depuis son site](../utilisation/recherche-documentaire.md#vérification-sur-le-windows-de-marc-depuis-le-site)
sert à établir la pertinence et les délais réels. Le test Windows en CI ne
remplace ni cette recette, ni un essai physique sur iPhone, ni un test complet hors ligne.

Le [chantier suivi](../decisions/fiabilisation-recherche-et-contenus.md) conserve
les suites : qualification éditoriale des véritables guides de fabrication,
présence puis préparation des sous-titres français, traduction de lecture dans
les lecteurs tiers et évaluation d’un complément sémantique sur une base mesurée.
L’espace Maison reste une idée reportée, comme demandé par Louis.
