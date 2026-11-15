# Améliorations issues des retours de Marc

**Plan retenu et suivi actuel — 14 novembre 2026.** Louis demande sa mise en
œuvre et la conservation des idées explorées, retenues, reportées ou abandonnées.
La 0.3.0 commence ce plan ; sa présence dans le code ne valide pas le fonds réel.

| Lot | Décision et résultat attendu | État |
| --- | --- | --- |
| Mesurer le fonds réel | Comparer les recherches naturelles aux sources réellement utiles ; distinguer absent, non indexé, mal classé et panne | Rapports jusqu’à 0.10.0 reçus ; encore 31 recherches partielles sur 32 et délai médian 12,3 s ; relecture humaine encore attendue |
| Indexation manquante | Index local SQLite du texte des ZIM dépourvus d’index Kiwix réel, progressif, reprenable et pilotable depuis le site | R1 réel 0.9.3 terminé sans erreur : 134 index natifs, un index local de 120 articles ; pause/reprise et nouveau lot réels restent à vérifier |
| Recherche et CPU | Réserver les titres, prioriser les collections utiles, paralléliser selon les CPU et conserver le site réactif | Implémenté en 0.3.0 ; latence et charge Windows à mesurer |
| Deux espaces | Autonomie et résilience par défaut, Savoirs et culture, et recherche globale ; fichiers conservés une seule fois | Filtres 0.3.0, corrections humaines persistantes 0.6.0 ; catalogue éditorial réel à relire |
| Utilité des résultats | Distinguer une présentation d’une procédure, qualifier étapes, matériel et schémas ; compléter les lacunes confirmées | Intention réparation/conservation/potabilisation améliorée ; qualification humaine des guides et fabrication à faire |
| Collections | Regrouper source/chaîne et nommer les variantes sans casser l’ouverture directe | Regroupement conservé, noms et groupes corrigeables en 0.6.0 ; révision éditoriale de toutes les variantes à faire |
| Assistant et contexte | Recherche commune, citations lues, contexte par modèle et réduction cohérente de l’historique | Réglages 0.3.0, mesures et calibration volontaire 0.7.0 ; délais et mémoire réels à mesurer chez Marc |
| Traduction de lecture | Lire en français / Voir l’original, traduction locale conservée dans les lecteurs | Accès au moteur existant livré ; lecture traduite intégrée Kiwix/PDF à développer |
| Vidéos | Inventorier les pistes, exposer les sous-titres existants, puis transcription/traduction synchronisée locale | À développer et qualifier sur les archives réelles |
| Livres longs | Reprise, contrôles techniques, terminologie et essai progressif jusqu’à 500 pages | Moteur existant par passages ; cohérence et livre réel non validés |
| Apprendre par thème | Objectifs concrets, prérequis, documents, étapes et lacunes | Six dossiers et repères humains livrés en 0.9.0 ; qualification des sources réelles à faire |
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
  La calibration volontaire est implémentée en 0.7.0 ; son résultat reste à
  appliquer explicitement après mesure sur le PC concerné.
- **À évaluer : reformulation ou reclassement IA**, puis recherche sémantique
  multilingue sur un échantillon si le gain est mesurable. Le socle sans IA est
  conservé ; aucun modèle supplémentaire n’est imposé dans cette livraison.
- **Firefox : complément à préparer et tester hors ligne**, sans en faire une
  dépendance de tous les lecteurs. La traduction d’une page ne crée pas les
  sous-titres d’une vidéo.

## Programme complet à exécuter

**Complément demandé par Louis le 14 novembre 2026 après livraison 0.3.0.**
Les tests chez Marc se font progressivement. Leur absence ne bloque pas le
travail indépendant. L’agent prépare des tests manuels exportables et annonce
précisément lorsqu’une mesure réelle devient nécessaire. Ce document planifie
les prochains lots ; il ne les déclare pas implémentés.

Le socle **L0 est livré en 0.3.0** : recherche commune, premières corrections de
classement, index ZIM manuel reprenable, filtres de domaine, contexte réglable et
rapport de huit recherches. La [recette vérifiée](../essais/2026-11-14-recherche-index-et-espaces.md#recette-finale-de-la-livraison)
conserve ses limites. Les lots ci-dessous complètent ce socle.

| Ordre | Lot | Livrable attendu | Dépendance principale | État |
| --- | --- | --- | --- | --- |
| L1 | Indexation automatique | Installation et nouveaux téléchargements alimentent une préparation persistante et visible | Socle 0.3.0 | Implémenté et corrigé jusqu’à 0.9.3 ; terminaison réelle reçue, nouveau lot et reprise réels à vérifier |
| L2 | Recherche fiable et diagnostic | Couverture réelle, échecs expliqués, comparaison de pertinence et délais | L1 pour la couverture complète ; diagnostic développable immédiatement | R1/R2 0.12.0 : 135 archives préparées, 15 compléments utilisables ; 32 recherches partielles surtout par délai. Flux/cache 0.13.0 et priorité des titres de tâches 0.13.1 ; nouvelle mesure Windows et avis humains attendus |
| L3 | Espaces et collections | Classement corrigeable, titres explicites et ouverture directe préservée | L2, catalogue existant | Commandes et export 0.6.0 ; relecture R3 du fonds réel attendue |
| L4 | Assistant, ressources et contexte | Mesures par phase et réglages adaptés au modèle et au PC | L2 ; indépendant des traductions | Rapports, budgets et calibration explicite implémentés en 0.7.0 ; R4 réel attendu |
| L5 | Lecture française et livres longs | Traduction dans le lecteur, reprise et cohérence des passages | Moteur documentaire et traductions existants ; L4 pour le réglage | À développer |
| L6 | Vidéos et sous-titres | Pistes locales puis transcription/traduction synchronisées | L5 pour le traitement de traduction ; inventaire indépendant | Inventaire local/rapports intégré en 0.14.0 ; recette réelle, acquisition et traitements suivants à faire |
| L7 | Savoir-faire et apprentissage | Dossiers par objectif, sources qualifiées et lacunes visibles | L2 et L3 ; traduction facultative | Six dossiers et repères humains implémentés en 0.9.0 ; qualification réelle R3 attendue |
| L8 | Complément IA de recherche | Comparaison reproductible et décision conserver/écarter | Référence L2 ; mesure matérielle L4 | Comparatif volontaire implémenté en 0.8.0 ; décision réelle R2/R4 attendue, aide désactivée |
| L9 | Recette intégrée et livraison | Windows/Linux, navigation mobile, hors ligne, reprise et documentation cohérente | Tous les lots ; contrôles effectués aussi à chaque livraison | CI par lot, conservation des index 0.9.3, scénario/export R7 livré en 0.10.0 et paquet vérifié ; recette réelle intégrée encore à faire |

### L1 — Installation, téléchargements et indexation automatique

- Préparer le lecteur d’archives lors de l’installation en ligne ; inclure ses
  dépendances compatibles et leurs empreintes dans le kit applicatif hors ligne.
  Réutiliser les index Kiwix réellement présents, sans dupliquer leur contenu.
- Après **un lot téléchargé et vérifié**, enregistrer les archives nouvelles ou
  modifiées dans une file durable, puis démarrer l’indexation une fois le verrou
  de téléchargement libéré. Couvrir installation, interface Web, commandes de
  maintenance et reprise Windows ; un fichier `.part` n’entre jamais dans la file.
- Dédupliquer par identité/édition/empreinte du contenu disponible. Une relance
  sans changement ne refait pas l’extraction ; une mise à jour de l’outil peut
  demander une reconstruction, en gardant le dernier index utilisable.
- Activer cette préparation automatique par défaut pour les nouveaux lots ;
  permettre désactivation, lancement manuel et plage horaire nocturne dans Famille.
  Une simple mise à jour du code ne déclenche pas rétroactivement un gros travail
  sur tout le fonds : proposer son premier examen dans les réglages.
- Conserver pause volontaire et arrêt après coupure. Au redémarrage, proposer la
  reprise explicite du travail interrompu ; aucune reprise d’inférence implicite.
  Différer une nouvelle préparation lourde en mode jeu et expliquer ce report.
- Afficher séparément téléchargement, vérification, indexation et disponibilité
  dans la recherche, avec progression, erreurs et espace disque. Adapter les
  processus au CPU, à la RAM et au stockage ; préserver les réserves physiques du
  laboratoire et la réactivité du portail. Une préparation nocturne est admise.

**Fin technique :** tous les chemins de téléchargement produisent les mêmes
événements ; interruption, relance, nouveau lot et version modifiée sont testés ;
les index validés restent utilisables pendant la reconstruction. Rapport **R1**.

### L2 — Recherche, couverture et diagnostic de l’intermittence

- Ajouter au diagnostic l’accès au serveur Kiwix **depuis le pilote**, l’accès et
  le temps du catalogue, les erreurs HTTP/délai/format, l’état des index et les
  parties non interrogées. Conserver seulement des champs utiles, sans journaux
  bruts, secrets, historique personnel ni chemins privés du PC.
- Examiner les appels concurrents au catalogue, son délai et sa taille avant de
  modifier les seuils. Prévoir réutilisation bornée du dernier catalogue valide
  et regroupement des appels si la reproduction montre leur utilité. Une vue
  ancienne doit être datée et signalée ; un catalogue vide valide reste distinct
  d’un catalogue inaccessible.
- Montrer clairement une panne ou une recherche partielle avant les résultats.
  Conserver les sources utiles, identifier les correspondances faibles et proposer
  relance ou ouverture directe. Ne jamais transformer une panne en document absent.
- Constituer environ **30 demandes naturelles** avec sources attendues, variantes,
  pluriels/fautes, langues, relances et cas négatifs. Séparer les cas de réglage des
  cas de vérification ; comparer les résultats avant/après chaque changement.
- Fusionner titres, redirections, index Kiwix, index complémentaires et pages des
  guides. Conserver intention, langue réelle, page et extrait expliquant le lien.
  Corriger le score ou l’accès identifié avant d’ajouter de nouvelles ressources.
- Rapporter les scans, vidéos sans transcription, articles trop grands et extraits
  tronqués. Une reconnaissance de texte ciblée est une suite à préparer sur les
  documents réellement nécessaires, pas une OCR globale annoncée comme faite.

**Fin technique :** référence automatisée sans régression, source pertinente dans
les cinq premiers résultats des cas documentés, mêmes sources attendues avec et
sans filtre adapté ; les erreurs restent explicites. Le gain réel et les délais
sur le fonds de Marc sont mesurés par **R2**, sans les déduire de petites fixtures.

**Livré en 0.5.0 :** 32 demandes versionnées, dont huit de vérification séparées
des 24 cas de réglage, sources attendues uniquement dans les fixtures fictives,
contrôle complet optionnel sur le site et choix humain du résultat utile exporté.
Quatre lacunes de vocabulaire FR/EN ont été reproduites puis corrigées. Les
redirections d’articles sont prises en charge ; la capture « Document indisponible »
de Marc reste sans adresse précise, donc sa cause réelle n’est pas certifiée.

### L3 — Deux espaces, collections et noms compréhensibles

- Conserver un logiciel et un exemplaire des fichiers. Classer au niveau de
  l’article/document avec appartenance possible aux deux espaces ; toute la
  bibliothèque conserve les ressources non classées et les liens historiques.
- Enregistrer méthode et état du classement : automatique, corrigé ou examiné.
  Une correction humaine persistante prime ; une nouvelle édition ne reçoit pas
  automatiquement une validation qui concernait une ancienne version.
- Affiner les domaines pratiques au-delà des quelques mots actuels. Distinguer
  présentation générale, explication, procédure, exercice et notice lorsque les
  métadonnées ou une lecture le permettent ; sinon afficher « type à vérifier ».
- Compléter le regroupement de toutes les collections concernées, pas seulement
  Canadian Prepper : source/chaîne, sujet, langue et édition vérifiés. Garder
  référence originale, ouverture directe, filtrage et groupes mémorisés.
- Prévoir une correction simple des libellés et domaines depuis Famille, exportable
  comme métadonnées sans contenu volumineux ni données personnelles.

**Fin technique :** corrections conservées après actualisation, liens inchangés,
pas de disparition globale d’un document, cas techniques Wikipédia et Appropedia
retrouvés ; navigation retour/rechargement vérifiée. Relecture réelle **R3**.

**Implémenté en 0.6.0 :** corrections communes par document, deux espaces possibles,
type inconnu par défaut, révision locale et état d’examen ; noms et groupes
modifiables, filtres des archives et index complémentaires, export sans contenu.
Le [guide actuel](../utilisation/classement-et-collections.md) précise les limites.
La relecture des libellés et procédures réellement présents ne devient pas acquise
par la seule livraison de ces commandes.

### L4 — Assistant, rapidité et mémoire utile

- Garder les mêmes outils pour tous les modèles et le moteur commun à la
  bibliothèque. Relances avec sujet et périmètre, cache des recherches/lectures,
  citations de passages réellement lus et limites de couverture conservées.
- Mesurer attente, chargement, recherche, lecture, premier texte et rédaction,
  avec version/digest du modèle, contexte et placement mémoire lorsqu’ils sont
  disponibles. Le mode rapide réduit les étapes inutiles et reste explicite
  lorsqu’un modèle ou une file d’attente le ralentit.
- Compléter le budget d’entrée : question actuelle, historique utile, outils,
  extraits, réflexion et sortie. Lire les limites du modèle local et conserver
  ensemble les appels/réponses d’outils lors de la réduction du contexte.
- Ajouter une calibration **lancée explicitement**, sur modèles déjà présents,
  à 16k puis 32k et davantage si supportés. Mesurer à froid et à chaud ; interrompre
  en cas d’erreur mémoire ou pression excessive. Conserver au moins 4 Go de RAM
  disponible par défaut, seuil réglable en maintenance et réserve vidéo du bureau.
  Ne pas imposer le remplissage de toute la mémoire ni charger un modèle en pause.
- Conserver un réglage par modèle et un retour au dernier réglage fonctionnel.
  Choisir le plus grand contexte stable compatible avec la réactivité souhaitée ;
  une hausse de contexte sans mesure ne devient pas une recommandation validée.

**Fin technique :** orchestration et budgets testés sans LLM réel dans le runner,
rapport matériel **R4** disponible ; recommandations automatiques de grande
allocation activées seulement après mesure correspondante sur le PC cible.

**Implémenté en 0.7.0 :** mesures séparées, export sans contenu privé, lecture associée
réutilisée, outils inclus dans le budget, limite native, essais synthétiques
froid/chaud avec marges et volume réellement traité. Le résultat reste une
proposition à appliquer explicitement, avec retour au réglage précédent. Le
[guide actuel](../utilisation/mesurer-assistant-et-memoire.md) donne R4 ; les performances
et la qualité réelles restent à mesurer chez Marc avant de recommander une allocation.

### L5 — Lecture traduite et livres de 500 pages

- Intégrer « Lire en français / Voir l’original » au lecteur du portail, puis aux
  articles Kiwix ouverts via celui-ci. Pour les PDF, proposer une vue textuelle
  française liée aux pages originales ; conserver l’original illustré accessible.
- Réutiliser la traduction par passages : progression, annulation/pause, reprise
  explicite, traitement équitable avec les conversations et respect du mode jeu.
  Dédupliquer par contenu source, langue, réglages et version du traitement ; une
  édition changée n’utilise pas silencieusement une ancienne traduction.
- Améliorer découpage par sections, glossaire technique réutilisable et contexte
  borné entre passages. Conserver contrôles des chiffres/unités, propositions
  refusées et avertissements ; ne pas présenter ces contrôles comme une preuve du sens.
- Préserver les règles actuelles de publication : originaux intacts, brouillons
  privés, nouvelles traductions terminées partagées selon le guide, anciennes
  privées sans publication explicite. Suppression de conversation et export ne
  doivent pas détruire un document déjà publié.
- Mesurer sur une page, un chapitre, puis un livre long ; essai synthétique de
  500 pages avec inférence simulée, puis essai réel progressif. Signaler pages
  scannées, images non traduites, limites de taille et passages non traités.
  Documenter Firefox comme complément facultatif préparé et essayé hors ligne.

**Fin technique :** lecture bilingue, reprise et conservation testées ; aucune
traduction partielle/refusée présentée comme complète. Durée et fidélité d’un livre
réel restent distinctes de l’essai synthétique ; rapport **R5**.

### L6 — Vidéos et sous-titres français hors ligne

**Extension confirmée le 14 novembre :** inclure les vidéos YouTube 480p ajoutées
par Marc dans `library/video/`, leurs métadonnées puis leurs transcriptions
horodatées, dans une recherche commune avec les documents. Voir le
[besoin tracé](videos-locales-et-recherche.md). L’inventaire ne se limite plus aux ZIM.

**Précision de Louis du 14 novembre :** valider la récupération ou la création
des sous-titres français **pour chaque vidéo**, pas seulement quelques exemples.
Le [protocole R6 cible](../essais/protocole-sous-titres-videos.md) définit les
preuves, les exceptions visibles et la différence entre contrôle technique et
relecture humaine. L’outillage vidéo reste à développer.

- Inventorier médias et pistes réellement présents dans les ZIM, avec langue et
  format ; fournir ce relevé avant de présumer qu’il faut tout transcrire.
- Exposer d’abord les VTT/SRT existants dans un lecteur local avec sélection de
  langue, désactivation et retour à l’original. Garder les liens des collections.
- Pour les pistes manquantes, permettre une préparation choisie : transcription
  locale avec le modèle de dictée déjà disponible, puis traduction des segments
  synchronisés. Si la ressource manque, afficher la préparation nécessaire ;
  aucun service distant ni téléchargement de modèle implicite dans le runner.
- Conserver horodatages, original, provenance et statut humain/automatique ;
  corriger/reprendre un segment sans refaire toute la vidéo. Lire les sorties
  locales sans IA et sans Internet une fois préparées.
- Indexer les transcriptions disponibles avec mention de leur origine automatique
  lorsqu’elle s’applique et lien vers le passage temporel du média. Une transcription
  ne certifie ni la fidélité de la voix reconnue ni la qualité d’une procédure.

**Fin technique :** piste existante, piste manquante, interruption, reprise,
synchronisation et lecture sans moteur testées sur petits médias. Compatibilité
avec les archives de Marc et compréhension réelle vérifiées par **R6**.
Le rapport du fonds réel doit rendre compte de toutes les vidéos inventoriées :
piste française récupérée/créée, état des contrôles et de la relecture, ou motif
d’indisponibilité. Une archive non examinée et une vidéo en erreur ne disparaissent
pas du bilan ; une seule piste générée n’établit pas la fin du lot.

### L7 — Savoir-faire pratiques et apprentissage

- Construire d’abord six dossiers : feu, eau, abri, générateur à pédales, réparation
  de vélo, conservation des graines. Ils organisent les ressources existantes,
  avec objectif, prérequis, matériel, plans, étapes et contrôles **si documentés**.
- Distinguer contexte historique et mode opératoire. Afficher clairement les
  éléments manquants plutôt qu’inventer des instructions ou une couverture complète.
  Compléter la bibliothèque lorsque l’absence est confirmée, avec provenance,
  édition, illustrations et droits examinés ; pas de corpus lourd dans le runner.
- Relier les dossiers à « Apprendre par thème », à la recherche et à l’assistant.
  La consultation ne dépend pas du chargement d’un modèle. Adapter les explications
  à l’âge/niveau pour l’usage familial, sans prétendre à une validation technique
  ou médicale indépendante.

**Fin technique :** six dossiers navigables, liens contrôlés et statut de chaque
ressource explicite. Un dossier peut rester incomplet si une source manque,
mais doit nommer la lacune et sa prochaine action. Utilité réelle : **R3**.

**Implémenté en 0.9.0 :** six dossiers adressables, recherche ciblée volontaire,
repères humains avec source/page/section, dates et révision, lacunes et prochaine
action. Les anciennes notes sont à revoir après changement du fichier ; conflit
d’édition refusé, retrait et export sans modification des originaux. Le
[guide](../utilisation/dossiers-pratiques.md) précise la relecture réelle R3 :
aucun guide complet, présence locale ni acquisition supplémentaire n’est présumé.

### L8 — Évaluer une aide IA à la recherche

- Comparer au moteur L2 : reformulation bilingue puis reclassement d’un petit lot
  de candidats, avec le modèle déjà disponible ; jamais lecture de tout le fonds
  dans une seule fenêtre de contexte ni inférence requise pour une recherche simple.
- Mesurer succès parmi cinq résultats, faux positifs, cas sans réponse, délai
  médian et cas lents, RAM/VRAM et coût de préparation. Réserver des questions qui
  n’ont pas servi au réglage. Préparer un rapport exécutable chez Marc.
- Conserver l’option seulement si elle retrouve davantage de sources utiles sans
  perdre les cas prioritaires réussis et respecte le budget de délai choisi dans
  la recette. Tant que ce budget matériel n’est pas établi, rester expérimental
  et désactivé par défaut. Enregistrer aussi une décision d’abandon si elle échoue.
- Étudier un index sémantique multilingue seulement après ce comparatif ; garder
  son ajout séparé et désactivé tant que gain, espace, durée et reprise ne sont pas
  établis. La fin de ce lot exige une décision motivée ou une mesure précisément
  attendue, pas l’installation systématique d’un nouveau modèle.

**Fin technique :** comparatif reproductible, rapport **R2/R4**, décision et coûts
consignés ; le moteur sans IA reste disponible. L’absence de mesure bloque
l’activation par défaut de l’option, pas les autres lots.

**Implémenté en 0.8.0 :** comparatif des trois méthodes, référence embarquée,
avis humains persistants, indicateurs séparés et budget choisi. Aucun appel IA
n’est ajouté à la recherche ordinaire. Le [guide](../utilisation/comparer-recherche-ia.md)
définit la recette ; la décision d’intégration attend le rapport réel R2/R4.
L’index sémantique est reporté tant que ce bénéfice n’est pas établi.

### L9 — Recette commune, documentation et publication

- À chaque lot : tests ciblés, CI Windows/Linux, navigation Chromium/WebKit pour
  l’interface, version cohérente, paquet logiciel et intégration vérifiée sur main.
  Aucun lot terminé ne reste seulement dans une branche locale.
- Recette finale : recherche IA arrêtée, Internet coupé, catalogue indisponible,
  index ancien/corrompu ou disque presque plein, pause/coupure/reprise, deux onglets,
  changement de profil et conservation des comptes, conversations, favoris et sources.
- Revoir zoom normal, petit écran, clavier mobile, retour/avance du navigateur,
  filtres et brouillons mémorisés ; Safari physique reste un essai utilisateur distinct.
- Inclure les nouveaux prérequis dans le kit applicatif et vérifier sauvegarde/
  restauration de leurs états sur petites données. Le chantier complet de disque
  de secours intersystèmes garde son [protocole propre](../exploitation/disque-de-secours-hors-ligne.md).
- Entretenir guides, architecture, index et décisions dans la même livraison.
  Mettre à jour chaque lot avec commit, preuves, limites et rapport réel attendu.
  Conserver les anciens bilans, même lorsqu’une piste est finalement abandonnée.

**Fin technique :** matrice des lots renseignée, CI et livraisons vérifiées,
aucun échec connu sans décision explicite ; rapport intégré **R7**. Ne pas déclarer
validé chez Marc ce qui n’a été essayé que sur données simulées ou en CI.

**Outillage R7 en 0.10.0 :** [contrôle d’usage](../utilisation/verifier-usage-hors-ligne.md)
depuis le site, mesures bornées et observations humaines exportables, brouillon
par profil/version sans reprise automatique. Il prépare la recette réelle ;
il ne clôt ni celle-ci ni les lots de traduction et de sous-titres encore prévus.

## Recettes progressives et conditions de blocage

Les [rapports réels 0.8.0](../essais/2026-11-14-rapports-recherche-080.md) sont reçus :
32 recherches partielles, comparatif IA interrompu et tentative d’indexation en
erreur ensuite. Ils rouvrent des corrections prioritaires L1/L2/L8. La livraison
des commandes ou une CI verte ne suffit pas à clore ces lots. Les
[corrections 0.9.1](../essais/2026-11-14-corrections-rapports-recherche.md) traitent
les budgets, la concurrence commune, les replis hors sujet et les diagnostics.
L’erreur d’indexation et la qualité réelle demandent toujours leurs rapports.
Le [contrôle isolé 0.9.2](../essais/2026-11-14-indexation-isolee.md) complète L1 :
prérequis vérifiés dans le Python du lecteur avant les archives, arrêt anticipé
et diagnostic catégoriel, ainsi que correction du lancement des processus dans
le venv Windows reproduit en CI, sans présumer la cause réelle de l’incident.
La [conservation des index 0.9.3](../essais/2026-11-14-index-sauvegarde-et-retour-arriere.md)
complète L1/L9 : exclusion des écrivains pendant sauvegarde et retour arrière,
processus d’extraction restants et fichiers de verrou conservés.
Les [rapports réels 0.9.3](../essais/2026-11-14-rapports-recherche-093.md) confirment
ensuite l’indexation terminée sans erreur. Les recherches restent partielles et
le comparatif IA expire après deux tentatives. Les
[corrections 0.9.4](../essais/2026-11-14-corrections-rapports-093.md) ciblent ces
faits ; le [journal depuis 0.2.0](../essais/journal-recherche-depuis-020.md) trace
les livraisons et les décisions pour le résumé final demandé par Louis.

La [procédure des rapports manuels](../essais/recettes-progressives-marc.md)
définit R1 à R7, leur disponibilité actuelle et la façon de demander un essai.
Les boutons non livrés y sont signalés comme prévus.

- Un retour matériel manquant n’arrête pas un lot indépendant : développer sur
  petits documents et services simulés, publier les tests et préparer la recette.
- Un échec reproductible de développement, risque de perte de données ou contrat
  incompatible bloque la livraison concernée jusqu’à correction.
- Si l’accès à un vrai ZIM, une mesure RAM/VRAM ou une relecture linguistique
  devient indispensable, annoncer **le point bloqué**, pourquoi, le test exact,
  sa durée/charge attendue et le rapport à retourner. Continuer le reste.
- Ne pas choisir un gros réglage par défaut, certifier une traduction ou annoncer
  une couverture complète faute de résultat utilisateur. Marquer « implémenté,
  validation réelle attendue » ; cela ne signifie pas « définitivement validé ».

## Hors des lots actifs

Maison de Solliès-Ville reste reportée (IDEE-001). Refonte complète des cartes,
changement de matériel, nouvel installateur système autonome et préparation du
disque de secours complet ne sont pas ajoutés implicitement à ce programme.
Les possibilités existantes et leurs données sont préservées.

Louis demande également, le 14 novembre, une **réorganisation des réglages et de
leurs écrans après la fiabilisation complète** : IDEE-006 dans la
[boîte à idées](boite-a-idees.md). Après la demande de préparation parallèle, la [0.12.0](../essais/2026-11-14-parametres-ux.md)
implémente ce regroupement après intégration de la recherche 0.11.1 ; elle ne
remplace pas le traitement des échecs de recherche observés.

La [livraison 0.4.0](../essais/2026-11-14-indexation-automatique-et-diagnostic.md) couvre l’indexation automatique et le diagnostic. Les essais matériels restent distincts ; les autres exigences du plan ne sont pas clôturées par cette seule livraison.

## Complément du travail nocturne — 0.13.0

Les [rapports 0.12.0](../essais/2026-11-14-recherche-0120-et-travail-nocturne.md)
confirment la préparation multilingue et identifient les délais encore insuffisants.
Le [cache et la recherche progressive](../exploitation/cache-et-recherche-progressive.md)
donnent plus de temps sans masquer les premiers documents. Deux Go est un exemple
de budget, pas une limite fonctionnelle ; une évolution matérielle reste envisageable
après mesure. Les six dossiers sont facultatifs, la recherche générale reste centrale.
Les [vidéos locales 480p](videos-locales-et-recherche.md) ajoutées par Marc dans
`library/video/` sont à intégrer aux documents avec passages horodatés et sous-titres.

Deux chantiers parallèles ont été proposés à Louis le 15 novembre :
[prompts vidéo et performances](prompts-agents-videos-et-performances.md), fichiers
réservés et branches séparées. Louis confirme leur lancement ; leurs livrables restent à examiner après
réception des comptes rendus. L’agent principal garde le moteur.

Les deux outils parallèles sont intégrés en 0.14.0 : inventaire vidéo local et
[diagnostic des délais](../exploitation/diagnostic-performances-kiwix.md).
Leur [bilan commun](../essais/2026-11-15-integration-outils-validation-videos.md)
conserve les preuves, ajustements et limites. Ils ne constituent pas une validation
du fonds réel ni une livraison de la traduction ou de l’indexation des paroles.
