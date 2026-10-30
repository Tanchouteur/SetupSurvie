# Cadrage et besoins

Date de référence : 30 octobre 2026. Document de travail fondé sur le contexte initial ; à préciser avec Louis et Marc.

## Intention

Pouvoir consulter une réserve de connaissances lors d’une coupure d’Internet, y compris prolongée. L’appareil doit donner accès aux documents eux-mêmes et à un assistant IA exécuté localement.

Louis et son oncle Marc portent le projet. Louis confirme le 30 octobre 2026 que la première étape est un prototype complet pour eux deux. La vente sera envisagée ensuite ; elle ne constitue pas le premier livrable. Le positionnement commercial et les engagements associés restent à définir.

## Cible familiale et développement

Louis précise qu’à terme chaque famille aura son propre appareil. Le PC Linux situé dans sa chambre servira pendant le développement ; ce n’est pas un serveur permanent commun aux familles.

Il faut déterminer une configuration reproductible qui minimise le coût tout en faisant fonctionner des modèles suffisamment capables pour les usages retenus. Aucun budget, modèle minimal ou matériel de série n’est encore arrêté. Les machines disponibles servent aux essais et ne fixent pas la configuration finale.

La contrainte de conservation de Windows 11 concerne le PC existant. Elle ne détermine pas encore l’OS des futurs appareils familiaux.

## Besoins exprimés

- Fonctionner sans Internet une fois le système préparé.
- Donner accès à une bibliothèque aussi large que possible, comprenant des photos, schémas et illustrations. La limite de stockage et la sélection des ressources restent à définir.
- Permettre à l’assistant de combiner les connaissances apprises par le modèle avec les informations retrouvées dans les documents locaux.
- Permettre une utilisation en français, même avec certaines sources anglaises.
- Être accessible depuis un navigateur sur téléphone, tablette ou ordinateur à proximité.
- Être simple à utiliser pour une personne peu technique.
- Préparer un premier système, le tester et reproduire ensuite son installation sur d’autres PC.
- Utiliser Docker, probablement Compose, pour les services lorsque cela convient.

Ces besoins ne valent pas encore critères de recette : les conditions et seuils de réussite doivent être définis.

## Usages à hiérarchiser

Les domaines évoqués incluent l’encyclopédie générale, l’eau et l’hygiène, les premiers secours, l’agriculture, l’alimentation, les plantes et champignons, la réparation, l’énergie, les cartes et l’enseignement.

Louis a précisé les usages recherchés le 30 octobre 2026 :

- Médecine : consulter des connaissances et références médicales ; les situations exactes restent à préciser.
- Ingénierie : réfléchir à un problème, comprendre un sujet et explorer des solutions.
- Cuisine : trouver ou élaborer des recettes.
- Champignons : comparer et différencier des espèces à l’aide de ressources adaptées.

Ces exemples expriment un besoin d’assistant généraliste associé à une bibliothèque pratique. Leur ordre de priorité n’est pas fixé. Louis souhaite inclure l’analyse de photos si elle ne complexifie pas trop le prototype et délègue cet arbitrage. Proposition de travail : la tester comme fonction facultative, sans bloquer le socle documentaire et conversationnel. Différencier des espèces dans des guides et identifier une photo sont deux fonctions distinctes.

Il reste à transformer ces usages en cas de test précis. Les exemples de test proposés par l’assistant ne valent pas validation du périmètre.

## Fonctions proposées, à valider

- Consulter la bibliothèque indépendamment de l’IA.
- Poser des questions en français et obtenir des réponses accompagnées de sources consultables.
- Rechercher dans des documents français et anglais.
- Traduire ou expliquer un passage à la demande en conservant les originaux.
- Disposer d’une administration distincte et d’une restauration sans téléchargement.

## Limites à préciser

Fonctionner sans Internet ne signifie pas fonctionner sans électricité. Batterie, solaire et durée d’autonomie ne sont pas définis. Le réseau local et sa portée restent ouverts. Plusieurs personnes doivent pouvoir utiliser le système ; Louis accepte une attente d’une à deux minutes pour une réponse IA. Le nombre exact, la gestion des requêtes et le délai sous charge doivent être précisés et mesurés.

La traduction complète de la bibliothèque, l’indexation de tous les ZIM et une couverture réseau de quartier ne sont pas des engagements pris.

Pour les usages à risque, notamment médicaux ou liés à la consommation de champignons, une réponse IA ou une comparaison de photos ne constitue pas une validation suffisante. Le comportement attendu de l’assistant sur ces sujets doit être cadré.

## Validation du prototype à construire

Les futurs tests devront au minimum couvrir l’accès depuis un appareil client, la consultation de documents illustrés, une question en français avec consultation des sources, le redémarrage sans Internet et la reproduction ou restauration du système. Les documents utilisés, le matériel, les délais acceptables et les résultats attendus restent à fixer.

## Contraintes confirmées lors du cadrage

- Le PC principal est sous Windows 11 ; conserver son système et ses usages habituels.
- Le PC Linux avec RTX 2060 et Ryzen 9 est prévu pour la période de développement, dans la chambre de Louis ; ses caractéristiques exactes et modalités d’accès restent à confirmer.
- Un espace commun suffit au prototype ; les espaces personnels ne sont pas demandés pour cette première étape.
- L’analyse de photos peut être reportée si son intégration complique sensiblement le prototype.
