# Périmètre du prototype

> Archive — document conservé pour retracer les propositions et le prototype initial. Les constats et commandes décrivent cette étape ; pour installer le pilote actuel, suivre le [guide Marc](../installation/pilote-marc.md).

Synthèse au 30 octobre 2026 des réponses de Louis. Les besoins ci-dessous sont confirmés, sauf indication de proposition ou de point ouvert. Aucun composant n’est encore installé ou retenu.

## Résultat recherché

Un prototype utilisable par Louis et Marc pour consulter une grande bibliothèque illustrée et dialoguer en français avec une IA locale, sans Internet après préparation. L’assistant doit exploiter à la fois ses connaissances apprises et les documents locaux, notamment en français et en anglais.

Les usages cités sont la médecine, la réflexion en ingénierie, les recettes et la comparaison de champignons. La qualité des réponses reste à évaluer ; aucune validation médicale ou de comestibilité n’est promise.

## Conditions de la première version

| Sujet | Périmètre actuel |
| --- | --- |
| Accès | Navigateur sur les appareils du réseau local de la maison ; toute la bibliothèque consultable directement sans IA, utilisation pratique sur téléphone |
| Réseau | LAN domestique maintenu opérationnel, même sans accès Internet |
| Alimentation | Prise électrique |
| Utilisateurs | Plusieurs personnes ; nombre précis à fixer pour les essais |
| Attente IA | Une à deux minutes acceptables ; délai réel à mesurer sous charge |
| Organisation | Espace commun ; gestion des documents et mises à jour par Louis et Marc |
| Bibliothèque | Aussi large que possible dans les deux langues, avec illustrations ; capacité et contenus à sélectionner |
| IA | Dialogue, réflexion et exploitation des documents ; modèle non choisi |
| Photos | Essai facultatif proposé selon la délégation de Louis ; report si complexité ou résultats insuffisants |
| Installation | Reproductible ; Docker et probablement Compose lorsque pertinents, avec préparation de l’hôte à définir |

## Machines et étapes

Le PC Linux avec RTX 2060 et Ryzen 9, dans la chambre de Louis, sert pendant le développement. Louis confirme 32 Go de RAM et 8 Go de VRAM ; la référence GPU exacte, la distribution et le stockage restent à inventorier.

Chez Marc, le système doit fonctionner sur son PC Windows 11 en conservant ses usages habituels. Configuration déclarée : RTX 5060 Ti, 32 Go de RAM, probablement Ryzen 5 et environ 4 To de stockage. Louis confirme 8 Go de VRAM ; références exactes et espace libre restent à vérifier.

À terme, chaque famille possède son appareil. L’objectif est un coût matériel réduit pour une qualité IA suffisante, avec une enveloppe indicative autour de 1 000 €, à ajuster selon les essais. Ce montant n’est pas un prix de vente. Une machine dédiée, éventuellement allumée seulement au besoin, est envisagée ensuite chez Marc ; son OS n’est pas choisi.

## Évolutions ultérieures

- Routeur et point d’accès Wi-Fi dédiés pour s’affranchir du réseau domestique.
- Batterie et étude de l’autonomie électrique.
- Éventuelle commercialisation après validation du prototype et examen des droits de distribution.

Les espaces personnels et la gestion autonome des contenus par les familles ne sont pas demandés au prototype. La traduction intégrale préalable et l’indexation exhaustive de tous les formats ne sont pas décidées.

## Vérifications proposées

Cette liste est une proposition de recette à préciser pendant l’étude technique, pas un relevé de tests réussis.

| Essai | Ce qu’il doit permettre de vérifier |
| --- | --- |
| Accès depuis un téléphone et un ordinateur du LAN | Ouverture de l’interface et consultation d’un document illustré |
| Dialogue en français | Compréhension des demandes représentatives et qualité des explications |
| Recherche documentaire | Réponse appuyée sur les bons passages et accès aux originaux cités |
| Question française sur une source anglaise | Recherche multilingue et restitution fidèle en français |
| Réponse absente de la bibliothèque | Absence de référence documentaire inventée et distinction avec les explications générales du modèle |
| Coupure d’Internet, LAN conservé | Consultation et IA disponibles sans service distant nécessaire |
| Redémarrage sans Internet | Retour au service sans téléchargement ni connexion externe obligatoire |
| Plusieurs demandes simultanées | Mesure du délai et comportement de l’attente ; charge exacte à fixer |
| Coexistence sur le PC Windows de Marc | Accès GPU et effet sur ses usages habituels |
| Installation ou restauration sur une autre machine | Réutilisation de la configuration et des contenus sans préparation manuelle non documentée |

Une bibliothèque volumineuse demande de suivre séparément les contenus stockés, consultables et réellement indexés pour l’IA. Les premiers essais peuvent utiliser un échantillon limité sans réduire l’ambition de la bibliothèque finale.

## Études complémentaires

Étudier la [fiabilité et les outils spécialisés](fiabilite-et-outils.md), ainsi que les [modes IA et travaux longs](modes-ia-et-travaux-longs.md). Louis accepte des traitements d’environ une heure pour des demandes approfondies lancées volontairement, si cela améliore réellement la qualité. Le délai habituel d’une à deux minutes reste distinct. Ces études n’imposent pas encore leur implémentation dans le premier prototype.

## Prochain travail documentaire

1. Inventorier les machines réellement accessibles.
2. Vérifier les projets et composants candidats, leur compatibilité Windows/Linux et leurs licences actuelles.
3. Proposer une architecture et un protocole d’essai répondant à ce périmètre.
4. Dimensionner ensuite le matériel familial à partir des résultats.
