# Six dossiers de lecture pratique

**Bilan en cours — 0.9.0, 14 novembre 2026.** Lot L7 du
[plan des retours de Marc](../decisions/plan-ameliorations-marc.md).

Les objectifs feu, eau, abri, générateur à pédales, vélo et graines disposent
d’une adresse, de recherches complémentaires explicites et de six points à
documenter. Le lecteur permet à Famille de relier une source réellement ouverte,
sa page ou section, une note et les points examinés. Les liens et fichiers
d’origine sont conservés. Aucun mode opératoire ni document présent n’est inventé.

Le classement général d’une source et son utilité pour un point de ce dossier
restent distincts. Les points non documentés affichent leur prochaine action.
Une modification de fichier retire l’ancien repère de la couverture actuelle,
en conservant la note pour relecture. Les modifications concurrentes sont refusées
par révision, sans écraser le travail de l’autre onglet. Export et préparation
pédagogique volontaire sont disponibles sans inférence automatique.

Les tests utilisent de petits textes fictifs et des services simulés. Ils
vérifient les six dossiers, lecture et datation des références, persistance,
révision changée pendant la lecture, absence de source, conflit d’édition,
retrait local, limite des notes, corruption isolée, recherche partielle et
conservation de l’original. La recette Chromium MCP vérifie les parcours,
19 contrôles de navigation, relecture et disposition de 320 à 1 366 pixels,
avec un sélecteur compact sur téléphone.

La première CI a exposé une erreur WebKit lors d’un rechargement rapide du lecteur :
l’éditeur de repères chargeait ses données alors qu’il était replié. Ces lectures
sont maintenant déclenchées seulement à l’ouverture explicite de cet éditeur ;
la recette de classement vérifie l’absence de ces requêtes pendant une lecture
et un classement ordinaires. La nouvelle CI reste nécessaire avant intégration.

La version mineure 0.9.0 ajoute cette fonction compatible ; le schéma de données
et les images tierces restent inchangés. Les validations finales seront consignées
après la CI. Le [guide actuel](../utilisation/dossiers-pratiques.md) distingue
les commandes livrées et la relecture réelle R3 encore attendue. Le corpus de Marc
n’a pas été copié, enrichi ni qualifié par ces essais.
