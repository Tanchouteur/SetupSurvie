# Cadrage et besoins

Date de référence : 30 octobre 2026. Document de travail fondé sur le contexte initial ; à préciser avec Louis et Marc.

## Intention

Pouvoir consulter une réserve de connaissances lors d’une coupure d’Internet, y compris prolongée. L’appareil doit donner accès aux documents eux-mêmes et à un assistant IA exécuté localement.

Louis et son oncle Marc portent le projet. Une vente de quelques appareils est envisagée, mais le positionnement commercial et les engagements associés ne sont pas définis.

## Besoins exprimés

- Fonctionner sans Internet une fois le système préparé.
- Donner accès à une bibliothèque comprenant des photos, schémas et illustrations.
- Permettre une utilisation en français, même avec certaines sources anglaises.
- Être accessible depuis un navigateur sur téléphone, tablette ou ordinateur à proximité.
- Être simple à utiliser pour une personne peu technique.
- Préparer un premier système, le tester et reproduire ensuite son installation sur d’autres PC.
- Utiliser Docker, probablement Compose, pour les services lorsque cela convient.

Ces besoins ne valent pas encore critères de recette : les conditions et seuils de réussite doivent être définis.

## Usages à hiérarchiser

Les domaines évoqués incluent l’encyclopédie générale, l’eau et l’hygiène, les premiers secours, l’agriculture, l’alimentation, les plantes et champignons, la réparation, l’énergie, les cartes et l’enseignement.

La présence d’un domaine dans cette liste ne signifie pas qu’il fait partie de la première version. Il faut choisir quelques situations concrètes pour guider la sélection des contenus et les tests.

## Fonctions proposées, à valider

- Consulter la bibliothèque indépendamment de l’IA.
- Poser des questions en français et obtenir des réponses accompagnées de sources consultables.
- Rechercher dans des documents français et anglais.
- Traduire ou expliquer un passage à la demande en conservant les originaux.
- Disposer d’une administration distincte et d’une restauration sans téléchargement.

## Limites à préciser

Fonctionner sans Internet ne signifie pas fonctionner sans électricité. Batterie, solaire et durée d’autonomie ne sont pas définis. Le réseau local, sa portée et le nombre d’utilisateurs simultanés restent également ouverts.

La traduction complète de la bibliothèque, l’indexation de tous les ZIM et une couverture réseau de quartier ne sont pas des engagements pris.

Pour les usages à risque, notamment médicaux ou liés à la consommation de champignons, une réponse IA ou une comparaison de photos ne constitue pas une validation suffisante. Le comportement attendu de l’assistant sur ces sujets doit être cadré.

## Validation du prototype à construire

Les futurs tests devront au minimum couvrir l’accès depuis un appareil client, la consultation de documents illustrés, une question en français avec consultation des sources, le redémarrage sans Internet et la reproduction ou restauration du système. Les documents utilisés, le matériel, les délais acceptables et les résultats attendus restent à fixer.
