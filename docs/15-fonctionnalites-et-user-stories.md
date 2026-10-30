# Fonctionnalités et user stories

Référentiel du 30 octobre 2026, construit à partir des réponses de Louis et du retour de Marc. Il couvre la cible du projet, pas seulement les fichiers du premier prototype. Voir le [guide d’installation](14-installation.md), le [périmètre](05-perimetre-prototype.md) et le [protocole de qualité](10-protocole-comparaison-ia.md).

## Acteurs et statuts

- Lecteur : membre d’une famille utilisant téléphone, tablette ou ordinateur.
- Administrateurs : Louis et Marc, qui préparent les contenus et les mises à jour au début.
- Installateur : personne préparant ou restaurant un appareil familial.

**À essayer** : configuration/code préparés, validation sur vos deux PC encore nécessaire. **Manuel** : réalisable via une procédure ou un composant existant, sans automatisation complète. **À développer** : besoin identifié, pas livré par les scripts. **Plus tard** : évolution hors premier socle. Ces statuts ne constituent pas un relevé de recette réussie.

Priorité **P0** : socle du prototype ; **P1** : extension importante après preuve du socle ; **P2** : évolution ultérieure. Les critères restent à préciser avec Marc si sa vision change.

## Accès et bibliothèque sans IA

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| LIB-01 | En tant que lecteur, je veux ouvrir un accueil simple depuis mon téléphone sur le LAN. | P0 · À essayer | Adresse du PC accessible, liens utilisables et boutons lisibles sur petit écran. |
| LIB-02 | Je veux consulter la bibliothèque sans lancer l’IA. | P0 · À essayer | Fiches et ZIM lisibles quand aucun modèle n’est chargé. |
| LIB-03 | Je veux lire Wikipédia français avec ses illustrations hors ligne. | P0 · Manuel | Archive maxi choisie, téléchargée et contrôlée ; articles et illustrations ouvrables sans Internet. |
| LIB-04 | Je veux chercher des mots dans les articles de l’encyclopédie. | P0 · À essayer | Kiwix retrouve un article contenant le terme, même s’il n’est pas dans le titre. |
| LIB-05 | Je veux parcourir les guides et filtrer leurs titres par langue. | P0 · À essayer | Catalogue mis à jour, accents et noms de fichiers affichés correctement, filtres explicites. |
| LIB-06 | Je veux retrouver un guide par une information présente dans son contenu, sans IA. | P0 · À développer | Recherche plein texte avec extrait et lien vers la page/source ; ne pas confondre filtre de titre et moteur complet. |
| LIB-07 | Je veux une recherche commune aux guides et encyclopédies, efficace sur téléphone. | P1 · À développer | Résultats compréhensibles, provenance/langue visibles, recherche sensible aux variantes utiles ; mesurer pertinence et délai sur une collection représentative. |
| LIB-08 | Je veux ouvrir un PDF, un livre ou un guide illustré confortablement sur mobile. | P0 · Manuel / à évaluer | Lecture, zoom, retour aux résultats et images utilisables ; ajout d’un lecteur spécialisé si nécessaire. |
| LIB-09 | Je veux une navigation par thèmes. | P1 · À développer | Thèmes et métadonnées cohérents ; catalogue actuel limité aux titres/langues/formats. |
| LIB-10 | Je veux garder accès aux documents pendant un calcul IA long. | P0 · À essayer | Lecture et recherche Kiwix répondent pendant la génération ; délai à mesurer sous charge. |

## Dialogue, français/anglais et preuves

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| IA-01 | Je veux poser une question et recevoir une réponse en français. | P0 · À essayer | Modèle local disponible, français compréhensible sur les cas retenus. |
| IA-02 | Je veux que ma question française retrouve aussi les documents anglais. | P0 · À essayer | Guide anglais pertinent retrouvé et réponse fidèle, pas seulement texte français fluide. |
| IA-03 | Je veux faire traduire ou expliquer un passage anglais. | P0 · À essayer | Original conservé ; unités, restrictions et termes importants restitués correctement. |
| IA-04 | Je veux combiner connaissances générales du modèle et documents locaux. | P0 · À essayer | Les documents pertinents sont utilisés ; aucune référence inventée quand ils ne répondent pas. |
| IA-05 | Je veux consulter les sources utilisées. | P0 · Manuel / à améliorer | Citation ou document visible ; lien vers l’original local et, à terme, la bonne page/section. |
| IA-06 | Je veux choisir un modèle adapté à ma demande. | P0 · À essayer | Modèles téléchargés sélectionnables ; absent/chargement/échec compréhensibles. |
| IA-07 | Je veux que plusieurs personnes puissent utiliser l’appareil. | P0 · À essayer | Comptes lecteurs créés, requêtes traitées sans perte ; délai visé d’une à deux minutes pour l’usage courant, à mesurer. |
| IA-08 | Je veux conserver mes conversations. | P0 · À essayer | Historique conservé après redémarrage ; périmètre des comptes documenté. |
| IA-09 | Je veux interroger les archives Kiwix depuis l’assistant. | P1 · À développer | Connecteur recherche/lecture, passages pertinents et liens locaux ; pas d’indexation automatique présumée. |

## Images, outils et fiabilité

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| IMG-01 | Je veux voir les illustrations des documents originaux. | P0 · À essayer | Images présentes et liées au bon texte dans le lecteur, sans ressource distante nécessaire. |
| IMG-02 | Je veux demander une explication accompagnée des illustrations retrouvées. | P1 · À développer | Images locales réelles, légendes, contexte et provenance ; pas d’adresse inventée. |
| IMG-03 | Je veux envoyer une photo à un modèle compatible. | P1 · Essai facultatif | Modèle compatible testé, délai/mémoire mesurés ; pas de garantie d’identification sensible. |
| IMG-04 | Je veux rechercher par ressemblance visuelle. | P2 · À étudier | Cas d’usage et index visuel évalués séparément de la recherche textuelle. |
| OUT-01 | Je veux des calculs et conversions vérifiables dans les réponses. | P1 · À développer | Outils ciblés, unités et hypothèses explicites, résultats contrôlés. |
| FIA-01 | Je veux que l’assistant demande les informations indispensables manquantes. | P0 · À évaluer | Cas incomplets identifiés ; aucune mesure ou observation inventée. |
| FIA-02 | Je veux distinguer observations, sources et hypothèses. | P1 · À développer / évaluer | Présentation traçable sur les cas sensibles, passages précis et réserves pertinentes. |
| FIA-03 | Je veux des comparaisons guidées plutôt qu’un verdict automatique. | P1 · À développer | Plusieurs hypothèses et critères manquants visibles ; procédure relue par une personne compétente. |
| FIA-04 | Je veux connaître les limites de l’outil sur les sujets sensibles. | P0 · Documenté ; comportement à tester | Pas de diagnostic ni feu vert de consommation promis ; pas de score de certitude non calibré. |

## Modes approfondis et dossiers du soir

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| LONG-01 | Je veux une réflexion approfondie avec recherches et outils successifs. | P1 · À développer | Boucle bornée, outils locaux et trace des sources/calculs, gain comparé au dialogue seul. |
| LONG-02 | Je veux lancer une demande le soir et retrouver le rapport plus tard. | P1 · À développer | File persistante, navigateur fermable, statut et rapport enregistrés. |
| LONG-03 | Je veux annuler une tâche et limiter son coût. | P1 · À développer | Budgets de temps/étapes, annulation et résultat incomplet signalé. |
| LONG-04 | Je veux reprendre ou comprendre un échec. | P1 · À développer | Étapes et erreurs conservées ; reprise après redémarrage effectivement testée. |
| LONG-05 | Je veux vérifier qu’un gros modèle lent améliore vraiment les résultats. | P0 · Protocole prêt, essais à faire | Comparaison mêmes questions/documents/outils ; noter qualité, erreurs, mémoire et délai. |

## Administration et installation

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| ADM-01 | En tant qu’administrateur, je veux ajouter les documents et modèles. | P0 · Manuel + scripts | Copie des guides/ZIM, import des guides dans Open WebUI et téléchargement explicite des modèles, sans effacer l’existant. |
| ADM-02 | Je veux identifier les contenus stockés, consultables et indexés. | P1 · Partiel | Le prototype catalogue les guides et expose les collections du chat ; registre transversal de versions/licences/indexation à réaliser. |
| ADM-03 | Je veux réserver l’administration à Louis et Marc. | P0 · À essayer | Compte admin unique par appareil, inscription désactivée, comptes lecteurs séparés ; bibliothèque directe publique sur LAN. |
| INS-01 | En tant qu’installateur, je veux démarrer le prototype sous Windows sans remplacer le système. | P0 · Scripts prêts à tester | Docker Desktop et serveur natif Ollama dédié, diagnostics et réglages conservés. |
| INS-02 | Je veux reproduire l’installation sur Linux avec GPU. | P0 · Scripts prêts à tester | Compose commun + complément GPU ; vérifier NVIDIA depuis le conteneur. |
| INS-03 | Je veux relancer l’installation sans perdre les données. | P0 · Tests automatisés | Secrets et documents conservés ; changement de dossier ou système non appliqué silencieusement. |
| INS-04 | Je veux fonctionner sans Internet après préparation. | P0 · À essayer | Images, modèles et embeddings présents, aucune dépendance distante nécessaire à la recette. |
| INS-05 | Je veux redémarrer le PC et retrouver le service. | P0 · À essayer / procédure manuelle Windows | Docker prêt et `up` relancé ; automatisation complète du démarrage Windows à ajouter si nécessaire. |
| INS-06 | Je veux connaître les versions réellement utilisées. | P0 · À essayer | Digests images fixés, modèle de recherche figé, version native et digests des modèles enregistrés. |
| INS-07 | Je veux sauvegarder et restaurer sans retélécharger. | P0 · Manuel, recette à faire | Copie cohérente après arrêt, kit d’images exporté/importé, restauration vers une cible distincte vérifiée. |
| INS-08 | Je veux mettre à jour sans effacer la bibliothèque ou les conversations. | P1 · À développer | Version précédente conservée, sauvegarde, migration/indexation maîtrisées et retour arrière testé. |
| INS-09 | Je veux installer un PC nu entièrement sans Internet. | P2 · À étudier | Supports OS, pilotes, Docker et dépendances inclus ; distinct du simple redémarrage hors ligne. |

## Appareil familial et évolutions

| ID | User story | Priorité / état | Critère d’acceptation |
| --- | --- | --- | --- |
| MAT-01 | En tant que famille, je veux mon propre appareil reproductible. | P1 · À dimensionner | Machine de référence issue des essais, contenus communs et secrets distincts. |
| MAT-02 | Je veux un coût adapté autour de 1 000 € si les performances conviennent. | P1 · À évaluer | Devis actuel et résultats sur modèles retenus ; aucun prix de vente confondu avec coût matériel. |
| MAT-03 | Je veux un appareil plus puissant si les gros modèles apportent un gain net. | P1 · À évaluer | Mesures justifiant VRAM/RAM supplémentaires, coût et consommation relevés. |
| EVO-01 | Je veux un Wi-Fi dédié indépendant de la box. | P2 · Plus tard | Routeur/point d’accès et démarrage sans box testés. |
| EVO-02 | Je veux étudier la batterie et l’autonomie électrique. | P2 · Plus tard | Consommation réelle, autonomie et budget ; prototype actuel sur prise. |
| EVO-03 | Je veux envisager la vente après validation du prototype. | P2 · Plus tard | Droits logiciels/modèles/contenus vérifiés, maintenance et engagements définis. |

## Décisions ouvertes

La recherche plein texte transversale doit réutiliser un moteur existant ou fédérer les recherches des lecteurs, pas être présentée comme résolue par un filtre JavaScript sur les titres. Choisir sa solution après mesure sur guides et ZIM représentatifs. La traduction complète préalable de tous les documents, un espace familial unique de conversations et l’indexation visuelle de toute la bibliothèque ne sont pas des engagements pris.

Ce catalogue doit être mis à jour avec les résultats de recette : préciser les machines, versions, essais réussis et limites observées avant de passer une fonctionnalité à un statut « validé ».
