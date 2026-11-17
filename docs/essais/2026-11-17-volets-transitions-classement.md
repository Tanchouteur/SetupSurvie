# Volets, transitions et classement des conversations

**Candidat 0.37.0 — 17 novembre 2026.** Demandes directes de Louis après son
essai de 0.36.0 : commande Documents près du volet droit, transitions pour rendre
les clics compréhensibles et classement par glisser-déposer dans les dossiers.

## Comportement

- Réouverture Documents à droite de l’en-tête ; focus rendu à cette commande à
  la fermeture, état accessible et commandes au clavier conservés.
- Colonnes du poste de discussion animées sur PC ; révélation courte des pages,
  résultats, documents, fenêtres, aides et contenus dépliés. Retour visuel partagé
  avec le lecteur PDF et les cartes, sans changer leurs moteurs.
- Préférence système de réduction des animations respectée, y compris pendant
  une animation. Les clics rapides annulent les animations précédentes ; aucun
  effet ne retarde une commande ni ne prétend qu’elle a réussi.
- Glisser-déposer natif des conversations vers un dossier ou Sans dossier : cible
  mise en évidence, déplacement enregistré par l’API existante puis confirmé.
  Dépôts externes et dépôts hors dossier sans effet ; menu conservé pour clavier
  et téléphone. Conversation ouverte, messages et brouillon restent conservés.

La version mineure correspond au nouveau mode de classement par glisser-déposer.
`data_schema: 1`, API et versions tierces restent identiques. La
[référence des composants](../architecture/composants-interface.md) fixe les
responsabilités ; le [guide utilisateur](../utilisation/nouvelle-interface.md)
donne les commandes.

## Recette et limites

La nouvelle recette `browser_motion_and_drag.js` vérifie les gestes réels du
navigateur et l’état sauvegardé côté API : dépôt, rechargement, retrait du dossier,
dépôt externe, annulation et erreur de service. Elle couvre aussi le brouillon,
la commande à droite, l’ouverture au clavier, les transitions, les clics rapides,
la réduction du mouvement et les largeurs 1440/1024/390/320.

Les tests utilisent un runner Linux CPU, des profils et documents jetables et
une inférence simulée. Aucun modèle ni gros contenu n’est téléchargé. Captures
Playwright MCP examinées pour la commande Documents et la cible du glissement.
Les résultats finaux de la recette et de la CI seront ajoutés après exécution.
Safari sur iPhone physique et usage sur les PC réels restent des validations
séparées. Aucun PC cible n’est mis à jour par cette livraison.
