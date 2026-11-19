# Volets, transitions et classement des conversations

**Bilan de livraison 0.37.0 — 17 novembre 2026.** Demandes directes de Louis après son
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
  Dépôts externes et dépôts hors dossier sans déplacement ; menu conservé pour clavier
  et téléphone. Conversation ouverte, messages et brouillon restent conservés.

La version mineure correspond au nouveau mode de classement par glisser-déposer.
`data_schema: 1`, API et versions tierces restent identiques. Le correctif de
recherche 0.36.1, livré pendant ce chantier, est intégré sans retirer ses
améliorations de recherche ni l’annulation des appels tardifs. La
[référence des composants](../architecture/composants-interface.md) fixe les
responsabilités ; le [guide utilisateur](../utilisation/portail.md)
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
La recette dédiée passe avec **35 contrôles sur chacun des moteurs Chromium,
WebKit et Firefox**. Les six recettes ciblées passent sur les trois moteurs :
finition (126), volets/dossiers (17), confort de discussion (38), traduction dans
le lecteur (13), paramètres (182) et la recette dédiée. Les tests unitaires du
classement (3) et du générateur HTML (2) passent. Après intégration de 0.36.1,
la suite Python complète passe : **972 tests,
aucun échec, 6 ignorés** (environ 215 s) ; les six recettes repassent sur les
trois moteurs.

La [CI du code final `d36b0ca`](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44033257585)
termine avec **huit jobs réussis** : Linux, Windows, trois versions Python du
lecteur isolé, Kiwix, itinéraires hors ligne et navigation des cartes/portail.
Ce dernier job rejoue la régression complète Chromium/WebKit puis les parcours
ciblés Firefox, dont les 35 nouveaux contrôles. Les commits suivants modifient
uniquement la documentation. La [PR nº 15](https://github.com/Tanchouteur/SetupSurvie/pull/15)
est fusionnée sur `main` au commit `01edd4376e3614d57cb78b024587f5a883cf8683`.
Le code applicatif est identique à `d36b0ca`. Après intégration, les deux tests
du générateur HTML, les trois tests du classement et les 35 nouveaux contrôles
sur chacun des trois navigateurs repassent. Le paquet logiciel 0.37.0 est construit
et son manifeste, ses empreintes et son extraction sont vérifiés à part des
installations réelles.

Safari sur iPhone physique et usage sur les PC réels restent des validations
séparées. Aucun PC cible n’est mis à jour par cette livraison.

Louis retire ensuite la demande de préparation de retour aux anciennes versions.
Les références créées avant ce retour restent historiques ; aucun travail
supplémentaire de repli n’est poursuivi pour ce chantier.


## Audit complémentaire et correctif 0.37.2 — 17 novembre 2026

La première recette complémentaire compte 14 contrôles, réussis sur Chromium,
WebKit et Firefox et via le MCP Playwright. Un essai supplémentaire pendant
l’animation a ensuite reproduit une régression mobile : à 390 × 844, l’aide
ouverte au clavier avait son bas vers 910 px, puis revenait à 754 px après le
mouvement. Le déplacement de toute la vue changeait le repère de ses descendants
fixes, avant de le rétablir à la fin.

Le correctif **0.37.2** garde un fondu de la vue et retire sa transformation.
Les aides et autres éléments fixes conservent donc leurs coordonnées pendant
l’effet. Les colonnes de l’assistant et les indicateurs de dépliement gardent
leurs transitions propres. Il s’agit d’une correction compatible, d’où le niveau
patch ; API, données et dépendances restent inchangées.

La recette finale comprend **16 contrôles par moteur**, réussis localement sur
les trois moteurs : elle ouvre aussi une aide pendant le changement de page et
vérifie sa visibilité au-dessus de la navigation ainsi que sa position stable
à la fin de l’effet.

| Critère de l’objectif | Preuve directement adaptée |
| --- | --- |
| Le clic produit son effet sans attendre l’animation | Nouvelle recette : rubrique et adresse changées immédiatement, animation de durée bornée |
| Le mouvement indique le changement de contexte | Recette de navigation, état des volets et revue des captures PC/téléphone ; recettes des lecteurs et recherches dans la CI complète |
| Clics rapides et clavier utilisables | `browser_motion_and_drag.js` : dernière route active et focus de réouverture ; audit : navigation au clavier, aide et Échap |
| Réduction du mouvement, y compris en cours | Audit : animation réelle retenue en pause, annulée par le seul changement de préférence ; effets CSS coupés, réactivation sans rechargement |
| Navigation robuste sans l’API d’animation | Audit : retrait temporaire de `Element.animate`, commandes de navigation toujours actives et API restaurée ensuite |
| Précédent/Suivant sans perte ni étape parasite | Audit : brouillon conservé, rubrique retrouvée, taille d’historique stable et focus dans une zone visible |
| Aucun traitement lancé par une transition | Audit : aucune commande serveur de modification pendant la consultation ; recettes de diagnostic, recherche et lecteurs sans lancement implicite |
| Fonctions existantes et erreurs préservées | CI complète : profils, recherche, sources, traductions, lecteurs, vidéos/audio et classements ; dépôt refusé, extérieur ou annulé dans les 35 contrôles dédiés |
| Éléments fixes stables pendant le mouvement | Audit : aide ouverte dès le changement de rubrique à 390 × 844, visible et sans saut à la fin du fondu |
| Tailles d’écran et confort de lecture | Finition (126) et confort (38), réponses longues/tableaux, largeurs PC et téléphone ; contrôles de débordement et commandes accessibles |

L’animation retenue pour le contrôle de réduction du mouvement ne peut pas
terminer naturellement avant le test : son annulation doit venir du réglage,
sans nouvelle navigation qui pourrait masquer un défaut. WebKit propage le
retour au réglage normal de manière asynchrone ; la recette attend le retour
effectif d’une animation (borne de 3 s), sans délai fixe ni retrait d’assertion.
Les aides et commandes de navigation de cet audit ne transmettent aucune commande
serveur après la sélection initiale du profil de fixture.

Ces contrôles sont ajoutés aux lanceurs de navigation Chromium/WebKit/Firefox.
Le résultat de leur CI sera enregistré à la clôture. Ils complètent les preuves
existantes ; ils ne constituent pas une promesse d’absence de tout bogue ni une
recette physique sur iPhone ou sur les PC des utilisateurs.


### Lecteur PDF : focus pendant l’initialisation

La première CI de l’audit échoue sur Firefox en attendant « Traduire ce PDF ».
Le défaut est reproduit séparément en retenant la réponse `/api/status` puis en
redonnant le focus : le profil de référence encore absent est comparé au profil
courant et la commande devient « Profil modifié » à tort. Le lecteur attend
maintenant la fin de son initialisation avant cette comparaison.

La recette renforcée vérifie aussi un vrai changement de profil après chargement.
Elle révèle que la lecture de l’identité courante portait l’ancien en-tête de
profil et recevait un refus 409, ignoré par le contrôle. La découverte d’identité
lit désormais le profil du cookie sans cet en-tête ; les lectures de données et
les commandes conservent leur contrôle d’appartenance. Un vrai changement ferme
le travail et demande de recharger, sans reprendre une traduction ni modifier
les données. La recette du lecteur passe de 13 à 15 contrôles.

Ces corrections compatibles rejoignent 0.37.2. Aucun contrôle n’est supprimé et
la CI complète est relancée après la correction, sans compter l’exécution échouée
comme une validation réussie.

La livraison moteur 0.37.1 est intégrée pendant cet audit. Le correctif d’interface
est livré en 0.37.2, en conservant ses changements de recherche et de sous-titres.


### Vérification de la version réunie 0.37.2

Après intégration du moteur 0.37.1, la suite locale complète compte **979 tests
Python, aucun échec, 6 ignorés sur Linux**, en environ 213 s. Les sept recettes
locales passent sur Chromium, WebKit et Firefox : audit (16), glisser-déposer (35),
finition (126), volets/dossiers (17), confort (38), lecteur renforcé (15) et
paramètres (182), soit **429 contrôles par moteur**. La [CI finale du code `cc97c47`](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44042839118)
termine avec **huit jobs réussis** : Linux, Windows, lecteurs isolés Python,
Kiwix, itinéraires et navigation complète. Les journaux du job navigateur
confirment les 16 contrôles d’audit, 35 de glisser-déposer et 15 du lecteur pour
chacun des trois moteurs. Les commits suivants ne changent que la documentation.
La livraison passe par la [PR nº 16](https://github.com/Tanchouteur/SetupSurvie/pull/16).
L’échec Firefox de la première CI est conservé comme preuve du défaut PDF ;
il n’est pas compté comme une validation réussie.


La PR nº 16 est intégrée au commit `f5959c1b9bfa0609e78126b16616995c4a9691ab`.
La comparaison avec `cc97c47` ne montre aucun changement applicatif ni de test :
seule la documentation diffère. Après intégration, les deux tests du générateur,
les contrôles de syntaxe et les 16 contrôles d’audit sur chacun des trois moteurs
repassent. Le paquet logiciel 0.37.2 est construit puis son manifeste, ses
empreintes et son extraction sont vérifiés, avec les ressources animées et le
lecteur PDF portant leur version de cache 0.37.2. Ce paquet n’est pas appliqué
aux PC réels par cet audit.
