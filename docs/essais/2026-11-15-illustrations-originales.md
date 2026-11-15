# Illustrations originales et références — 0.19.0

**Bilan de développement — 15 novembre 2026.** Nouvelle fonctionnalité compatible,
donc version mineure 0.19.0 ; schéma de livraison 1, profils conseillés et images
tierces inchangés. L’objectif reste actif pour la fidélité des synthèses et la suite
traduction/sous-titres. Aucun déploiement sur les PC clients par ce lot.

## Comportement retenu

L’assistant peut sélectionner les illustrations des articles effectivement lus
et les pages originales des PDF retenues. Le portail les présente sous la réponse,
avec légende, référence, dates connues et accès à l’original agrandi. Les limites
et plafonds sont dans le [guide actuel](../utilisation/illustrations-et-references.md).
La sélection fonctionne aussi dans les synthèses longues, avant la rédaction finale.

Les légendes et extraits sont des données, pas des instructions système. Le modèle
choisit des identifiants fournis par le serveur : aucune URL inventée, recadrage,
traduction des pixels ni dessin généré ne remplace un original. Une page PDF est
proposée entière, ce qui conserve son contexte mais peut nécessiter un zoom.
Les aperçus sont chargés à l’approche de la lecture. Les références enregistrées
ne sauvegardent pas les fichiers ; les originaux doivent rester disponibles.

Les références groupées et avec page deviennent cliquables : `[1, 2]`, `[1, p. 21]`.
Le contrôle de citations reconnaît aussi les numéros inconnus dans ces groupes.
Un lien de page vise une page réellement retenue, sinon la source ; il ne valide
pas le sens d’une phrase ou une page annoncée à tort par le modèle.

Une version de fichier connue est vérifiée avant/après lecture de l’image ou
rendu PDF. Le contrôle repose sur taille/date de modification, pas sur une empreinte
du contenu. Un changement refuse l’aperçu ancien sans effacer la réponse.
Un échec de sélection ou de chargement conserve les textes et références.

## Choix revus pendant les essais

La première sélection intervenait après la rédaction. Le vrai modèle choisissait
correctement deux visuels, mais écrivait quand même qu’il ne pouvait pas les montrer.
Le choix intervient désormais avant la rédaction, avec un résultat d’outil indiquant
ce que le portail peut afficher. La synthèse longue suit la même séquence.

Les articles peuvent contenir beaucoup d’icônes avant un schéma utile. Le parcours
examine au plus 200 images locales et classe les légendes par rapport au sujet,
avec diversification des sources, avant de présenter au plus 24 candidats réduits
selon le contexte. Un test place le schéma après 80 logos. Ce classement ne garantit
ni la meilleure sélection ni la compréhension des pixels.

Le paquet de lecture du modèle ne reçoit pas les 200 candidats privés de chaque
source. Un appel explicite à `source_illustrations` conserve une paire d’appel/résultat
unique ; il ne crée pas un second appel implicite imbriqué. Les mesures exportées
restent numériques : compteurs et durée de sélection, sans légende ou texte privé.

## Essais avec le vrai modèle

R7, vrai `gemma4:e4b`, contexte 16k, huit couches GPU demandées, six threads,
maintien quinze secondes et réserve de 1 536 Mio. Ollama natif 0.40.14 ; l’image
épinglée du pilote reste 0.40.13. Aucun autre modèle/processus arrêté et aucun
nouveau modèle téléchargé pour ce lot. Les rapports restent privés hors Git.

`tests/real_illustrations_check.py` utilise un PDF fictif de 21 pages, avec valeur
17 et dessin vectoriel à la page 21, et un article HTML fictif Boreal, valeur 59,
avec schéma légendé et logo. Le vrai moteur lit et sélectionne ; le lecteur Kiwix
est simulé pour l’article. Le modèle reçoit les légendes, pas les images.

- Référence 0.18.0 : 88 904 ms, deux sources lues, aucun visuel proposé ; le modèle
  annonce l’impossibilité de montrer les images.
- Première sélection après rédaction : 94 244 ms, bons PDF/image et logo écarté,
  mais la prose annonce encore cette impossibilité. Approche remplacée.
- Sélection préparée avant rédaction : 75 279 ms, mêmes bons visuels ; le modèle
  annonce les originaux proposés sous la réponse.
- Rejeu avec contrôles de paquets/outils et consigne de concision : **70 536 ms**,
  deux sources et les deux visuels corrects, logo exclu. Le modèle annonce leur
  disponibilité. Les chiffres 17 et 59 sont bien attribués ; la formulation
  « total d’unités » dépasse toutefois le libellé exact de la fixture et les dates
  restent omises dans la prose. Les références gardent leurs métadonnées.

Ce ne sont pas des mesures comparatives de vitesse : code, consignes et cache
peuvent différer. Ni vision, ni sens des unités, ni fidélité générale ne sont certifiés.
L’empreinte Python du dernier rejeu ordinaire est
`87ccf6677f625927b81a50fd27e1152607c05ac002f2ed092dc385e74b2c2a79`, celle du contexte produit
`c0b2ee3a3c08b9f7220739aff6038fa3176c8004b266ef280f76e51ac01bc734`.
Les changements suivants du moteur concernent uniquement la préparation des visuels
de la synthèse longue ; son rejeu est consigné séparément ci-dessous.

Un essai réel de changement précharge le modèle d’essai installé `llama3.1:8b`,
puis envoie une seule demande vers Gemma. Il termine au premier envoi en **62 361 ms**,
avec préparation du modèle cible en 4 097 ms et quatre PDF/pages effectivement lus.
La cinquième notice reste omise selon le budget ; ce n’est pas une lecture exhaustive.
Les valeurs 17, 23, 31 et 43 et leurs références sont correctes sur cette réponse.
La mesure constate un autre modèle avant et aucun autre après la préparation.
Cela confirme ce scénario Linux contrôlé, pas tous les cas Windows de Marc.

## Vérifications et limites

Les tests simulés couvrent légendes HTML anciennes/nouvelles, parcours hors archive,
identifiants inventés, pages lues, budget insuffisant, échec optionnel, conservation
des choix, citations composées, version changée pendant la lecture, et accès aux
originaux sans moteur IA. La synthèse longue vérifie que les originaux sont connus
avant sa rédaction et que les candidats privés ne gonflent pas son paquet final.

La recette navigateur rend réellement un PDF et un SVG synthétiques. Elle ouvre
la référence de page, recharge la conversation, provoque un changement de PDF,
et vérifie l’absence de débordement à 1 366, 390 et 320 pixels. Les autres parcours
protègent choix multiples, synthèse longue, confort et mesures. Les émulations
Chromium/WebKit ne remplacent pas un vrai essai iPhone.

Pas de corpus lourd dans le runner, pas d’OCR, de vision, de lecture de vrai livre
de 500 pages ni de validation des schémas du fonds Windows de Marc. Les légendes
peuvent manquer et le modèle peut se tromper de schéma ou de sens. L’interprétation
visuelle et l’extraction d’illustrations EPUB/HTML locaux restent prévues séparément.
Aucun sous-titre acquis ou traduit par cette livraison.


## Rejeu de la synthèse longue et vérifications finales

Le candidat final traite les deux PDF de 21 pages avec `--illustrations` en
**80 012 ms** : 42/42 passages, sept étapes enregistrées, synthèse terminée,
valeurs 17 et 59 correctement attribuées, non-extrapolation, dates, éditions et
références `[1, p. 21]` / `[2, p. 21]` conservées. Les deux pages 21 figurent dans
les sources enregistrées et la réponse annonce leur disponibilité. Les notes
regroupées attribuent chaque valeur uniquement à sa source. Ce cas favorable
sur fixtures n’efface pas les limites des autres essais.
Empreinte Python `2f3b19de6969ea714cbc873ef933b2bc6e8aa0f4cc09da4968cdb8fdb87285b3`,
contexte produit inchangé par rapport au rejeu ordinaire ci-dessus.

- 704 tests unitaires réussis, trois ignorés propres à Windows sur le runner Linux.
- 113 contrôles ciblés par navigateur : synthèse longue 19, sélection multiple 19,
  confort 37, mesures 23 et illustrations 15, dans Chromium et WebKit.
- Rejeu Chromium via MCP : 15 contrôles d’illustrations. Captures privées
  `setupsurvie-0190-figures-desktop.png` et `setupsurvie-0190-figures-mobile.png`,
  examinées ; page PDF entière et image d’article lisibles après ouverture en grand.
- `git diff --check` sans erreur ; liens et ancres des documents concernés contrôlés.
- Aucune recette physique Windows/iPhone ni nouvelle indexation du fonds de Marc.


## Reçu de livraison

Code **`67ab419a8e01fe0ea83d27fe4cb0c34256c492f5`**, huit jobs de la
[CI complète](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43763945216)
réussis, dont Windows, navigateurs, Kiwix, routage et lecteurs d’index isolés.
Le paquet est décompressé réellement puis ses **791 fichiers** comparés au commit
avec les filtres Git : 15 272 123 octets décompressés, ZIP de 6 823 644 octets,
SHA-256 `ad146503d2cc1a089970f7cb4f1583394a89c2f0459cdd2e16225527d803910e`.
Ce reçu est ajouté ensuite par un commit documentaire ; le paquet correspond
au code fonctionnel indiqué. Aucun déploiement client effectué.
