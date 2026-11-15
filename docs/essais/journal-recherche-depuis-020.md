# Journal de fiabilisation depuis la 0.2.0

**Suivi actuel — 14 novembre 2026.** Demandé par Louis pour préparer le résumé
final. Ce journal suit les livraisons, décisions, preuves et limites ; les bilans
liés conservent leurs détails et résultats historiques. Une ligne livrée ne
signifie pas que le fonctionnement sur tout le fonds de Marc a été validé.

## Livraisons et différences

Les commits ci-dessous introduisent la version ; leurs bilans donnent les
corrections et la CI finales de chaque lot. Toutes ces livraisons sont sur `main`.

| Version | Ce qui a été fait et pourquoi | Preuves et limites conservées |
| --- | --- | --- |
| 0.2.0 · `aead6b0f` | Point de départ : nouvelle interface en service et premier rapport de recherche réel | Le [bilan de départ et de 0.3.0](2026-11-14-recherche-index-et-espaces.md) distingue les résultats réels des petites fixtures |
| 0.3.0 · `064a44f1` | Index ZIM complémentaire manuel et reprenable, recherche partagée, titres réservés, classement pratique, deux espaces, contexte réglable | CI Windows/Linux et navigateurs ; le fonds de Marc n’est pas répliqué ni indexé dans le runner |
| 0.4.0 · `bffc3956` | File d’indexation après installation/téléchargement, pause/créneau nocturne, diagnostic Kiwix/catalogue et index réels | [Bilan](2026-11-14-indexation-automatique-et-diagnostic.md), 399 tests et CI ; validation réelle initialement attendue |
| 0.5.0 · `1d6b40ef` | Référence de 32 demandes, avis humains exportables, vocabulaire FR/EN et lecture des redirections | [Bilan](2026-11-14-reference-recherche-et-lecture.md), 408 tests et CI ; une attente de test a été corrigée, sans prétendre expliquer une ancienne capture sans URL |
| 0.6.0 · `db1f1778` | Domaines/type/examen corrigibles par document, noms et regroupements de collections modifiables, ouverture directe conservée | [Bilan](2026-11-14-classement-et-collections.md), 420 tests et CI ; la relecture éditoriale du fonds reste humaine |
| 0.7.0 · `382cc85f` | Mesures des phases de réponse, budget de contexte, limite native du modèle, calibration mémoire volontaire et retour au réglage précédent | [Bilan](2026-11-14-mesures-assistant-et-contexte.md), 435 tests et CI ; aucun grand contexte recommandé sans mesure du PC cible |
| 0.8.0 · `6828201e` | Comparatif facultatif : moteur actuel, reformulation bilingue et reclassement local ; questions réservées et avis humains | [Bilan](2026-11-14-comparatif-recherche-ia.md), 447 tests et CI ; aide désactivée par défaut et gain réel non établi |
| 0.9.0 · `5dfce5dc` | Six dossiers pratiques avec objectifs, repères de sources, révision et lacunes visibles | [Bilan](2026-11-14-dossiers-pratiques.md), 459 tests et CI ; deux courses de chargement WebKit corrigées, sources réelles à qualifier |
| 0.9.1 · `3b73822d` | Corrections après rapports 0.8.0 : appels Kiwix partagés et bornés, cache court, erreurs détaillées, moins de replis sur un seul mot ; budget IA appliqué à toute la demande et arrêt après deux échecs | [Bilan](2026-11-14-corrections-rapports-recherche.md), 469 tests et CI ; ne prouve pas la correction de l’indexation réelle |
| 0.9.2 · `8427aad0` | Vérification du lecteur dans son Python isolé, causes d’erreur catégorielles, correction du pool Windows et d’une recherche déclenchée trois fois au chargement | [Bilan](2026-11-14-indexation-isolee.md), 478 tests et CI dont Python Windows 3.11 à 3.14 ; erreurs de fixture UTF-8/création ZIM distinguées du défaut de lancement réel reproduit |
| 0.9.3 · `faaa6f16` | Exclusions entre indexation, sauvegarde et mise à jour ; verrous par archive pour les processus restants ; conservation des verrous et des index au retour arrière | [Bilan](2026-11-14-index-sauvegarde-et-retour-arriere.md), 486 tests et CI ; un chemin temporaire Windows du test a été corrigé ; première mise à jour depuis une ancienne version à faire après pause effective |
| 0.9.4 · `c70aabc` | Priorités entre langues et collections pratiques, isolement des grosses archives, replis anticipés, annulation des requêtes sans lecteur, filtrage des faux candidats et contexte des outils allégé | [Bilan](2026-11-14-corrections-rapports-093.md), 495 tests et huit tâches de CI réussies ; filtre corrigé après un refus trop strict sur le Kiwix réel synthétique ; nouveau R2 et relecture humaine attendus chez Marc |
| 0.10.0 · `85aeeb6` | Contrôle R7 guidé depuis le site : lectures sans IA, observations par profil/version et export distinct, arrêt et conservation des mesures reçues ; préparation de la validation hors ligne | [Bilan](2026-11-14-recette-usage-hors-ligne.md), 495 tests et huit tâches de CI réussies, 32 vérifications par navigateur ; scénario de changement de profil corrigé ; coupure Internet et usage physique non déduits des fixtures |
| 0.11.0 · `fcef6dc` | Chantier cartes d’un autre agent : relief transparent et choix d’accès aux itinéraires, intégré sur main avant la suite recherche | [Bilan cartes](2026-11-14-cartes-et-acces.md), validations et limites propres ; les essais sur les deux PC et iPhone physique restent distincts |
| 0.11.1 · `1836d63` | Complément local pour les index natifs aux langues incompatibles, arrêt des appels natifs voués au refus, traces détaillées réservées au contrôle explicite | [Bilan](2026-11-14-index-multilingues-et-diagnostic.md), 508 tests et huit tâches de CI réussies ; 35 contrôles Kiwix réels synthétiques ; nouvelle préparation et mesure chez Marc attendues |

| 0.12.0 | Paramètres répartis en quatre usages, options avancées dépliables, suivi et arrêt accessibles au téléphone ; contrôles existants déplacés avec leurs événements | [Inventaire](../utilisation/parametres-et-appareil.md), [bilan avec captures](2026-11-14-parametres-ux.md), 508 tests runner et huit jobs CI réussis sur `32dbed5` ; moteurs et cartes 0.11.0/0.11.1 conservés, Safari physique et recette chez Marc distincts |

Les nombres de tests incluent trois tests ignorés sous Linux ; les bilans
précisent les plateformes réellement essayées. Aucun de ces nombres ne mesure
la pertinence du fonds réel, la traduction d’un livre ou la tenue physique du disque.

## Retours réels et changements de priorité

- Rapports 0.8.0 : recherches partielles, index non préparés, comparatif IA expiré,
  puis capture d’échec d’indexation. [Analyse datée](2026-11-14-rapports-recherche-080.md).
- Rapports 0.9.3 reçus ensuite : indexation terminée sans erreur, mais 31 recherches
  partielles sur 32 et nouveau comparatif IA interrompu. L’indexation manquante ne
  suffit plus à expliquer les résultats. [Analyse datée](2026-11-14-rapports-recherche-093.md).
- Après les corrections prioritaires 0.9.4, le brouillon R7 est repris en 0.10.0 :
  [contrôle d’usage exportable](2026-11-14-recette-usage-hors-ligne.md), lectures
  bornées, observations par profil/version et absence de reprise automatique.
  Livré avec CI réussie ; aucune recette physique chez Marc n’en est déduite.
- Audit du paquet 0.10.0 de cette CI : 697 fichiers acceptés par le lecteur de
  mise à jour réel, nouveau script et code de recherche identiques à `main` ;
  transport vérifié, installation chez Marc non vérifiée. Le
  [bilan](2026-11-14-recette-usage-hors-ligne.md#audit-du-paquet-livré) conserve la preuve.
- Rapport réel 0.10.0 reçu ensuite : encore 31 recherches partielles sur 32,
  médiane 12,3 s ; des titres utiles remplacent plusieurs faux candidats, sans
  avis humain enregistré. [Analyse](2026-11-14-rapport-recherche-0100.md).
  Le refus natif d’une archive multilingue pourtant indexée est reproduit.
  La [correction 0.11.1](2026-11-14-index-multilingues-et-diagnostic.md) prépare son
  complément local et un diagnostic plus détaillé, sur la base des cartes intégrées.
- Paquet 0.11.1 vérifié avec le lecteur de mise à jour : 708 fichiers acceptés,
  code identique à main et détail du diagnostic présent. Le
  [bilan du paquet](2026-11-14-index-multilingues-et-diagnostic.md#paquet-de-mise-à-jour-vérifié)
  distingue ce contrôle de l’installation et des mesures encore attendues chez Marc.

## Décisions conservées ou reportées

Les deux espaces partagent un même fonds ; les archives directement ouvrables
et leurs index natifs sont conservés. L’index local complète les manques, sans
extraire systématiquement tout Wikipédia une seconde fois. Les réserves mémoire,
pause du moteur et reprise explicite restent appliquées.

L’aide IA reste expérimentale : les rapports reçus ne démontrent pas son intérêt
dans le budget choisi. Un nouvel index sémantique est reporté jusqu’à une base
comparative exploitable. Le contexte n’est pas porté au maximum théorique sans
mesure de stabilité et de réactivité.

La traduction de lecture, les sous-titres et les livres longs restent des lots
du [plan](../decisions/plan-ameliorations-marc.md), pas des fonctions déclarées
terminées par ce journal. Maison de Solliès-Ville et réorganisation générale des
réglages sont tracées pour plus tard dans la [boîte à idées](../decisions/boite-a-idees.md).

Louis précise ensuite que la récupération ou la création des sous-titres français
doit être validée pour chaque vidéo : le [protocole R6 cible](protocole-sous-titres-videos.md)
exige un inventaire et un état par média, contrôles de lecture/synchronisation
hors ligne, relecture humaine à portée explicite et exceptions visibles. Ce
complément ne déclare pas l’outillage vidéo ou ces validations déjà réalisés.

Louis demande ensuite un [prompt de refonte des paramètres](../decisions/prompt-refonte-parametres.md)
pour un autre agent : préparation parallèle, fonctions conservées, worktree dédié
et coordination des fichiers partagés. Cette consigne actualise l’attente initiale
« après la fiabilisation » ; elle ne déclare pas la refonte déjà réalisée.

## Pour clore la première version fiable de la recherche

L’outillage livré et les tests de développement ne clôturent pas l’objectif.
Le rapport R1 réel 0.12.0 confirme les 135 archives examinées et les 15 compléments
locaux prêts, dont les archives multilingues. Son R2 reste partiel dans les 32 cas,
avec 31 échéances atteintes et une médiane de 12,586 s. Le prochain R2 doit mesurer
la correction progressive et le cache 0.13.0, sans refaire toute l’extraction pour
ce seul changement. Il faut encore ouvrir humainement les résultats prioritaires
feu, eau, générateur et vélo. Toute anomalie reproduite
doit être corrigée ou faire l’objet d’une décision explicite, sans transformer
une erreur d’accès en absence de source.

Le contrôle R7 prépare la lecture/navigation sans IA et sans Internet ; son
exécution physique reste à faire sur le PC cible. La qualité réelle, l’accès aux
originaux et la conservation des données ne sont pas déduits de ses réponses
simulées. Les choix de grande allocation mémoire et d’aide IA restent limités
aux mesures disponibles, sans activation par défaut faute de gain démontré.
Les lots de traduction et de vidéos restent dans le plan global, avec leur
propre validation ; le présent objectif n’en revendique pas la livraison.

## Règle de mise à jour

Pour chaque suite : ajouter différence concrète, cause vérifiée ou hypothèse,
tests exécutés et non exécutés, choix retenu/reporté/abandonné et lien vers la
livraison. Le résumé final s’appuiera sur ces preuves et séparera développement,
déploiement chez Marc et validation humaine des documents.

## Rapports réels 0.12.0 et correction nocturne 0.13.0

L’UX des paramètres a été intégrée séparément sur main (PR #10, `5508740`) ; ses
contrôleurs, les cartes et leurs recettes sont conservés. Le travail nocturne reste
sur le moteur et son affichage de résultats, sans nouvelle refonte des paramètres.

Les deux nouveaux rapports réels confirment 135 archives examinées sans erreur,
120 index natifs compatibles et 15 compléments locaux, totalisant 3 238 articles.
La recherche multilingue locale fonctionne ; les anciens HTTP 400 ont disparu.
La médiane des 32 recherches reste 12,586 secondes et 31 atteignent l’échéance :
le délai et les expirations d’appels constituent encore un problème observable.
Aucun avis humain n’est enregistré ; ces mesures ne qualifient pas la pertinence.

La 0.13.0 ajoute premiers résultats progressifs, lecture pendant la recherche,
arrêt conservant les résultats et budget natif de 60 secondes sur le portail.
Le JSON des outils garde douze secondes. Le cache passe de quinze secondes en
mémoire à cinq minutes, avec complément disque de 24 heures invalidé par l’état
des archives et des index. Les erreurs ne sont pas mémorisées comme absence.
Le budget initial de 2 Go est ajustable, sans plafond produit à 2 Go ; les réserves
et les limites d’accès disque restent distinctes. Les résultats ne sont pas des
réponses IA mises en cache. Voir le [guide actuel](../exploitation/cache-et-recherche-progressive.md).

Louis confirme la priorité à un outil utile et pourra faire évoluer le matériel
après mesure. Les six dossiers sont facultatifs. Le nouveau dossier
`library/video/` et les vidéos YouTube 480p sont rapportés, sans inventaire distant
par l’agent. L’[étude traduction et vidéos](../decisions/videos-locales-et-recherche.md)
précise acquisition des pistes, transcriptions horodatées et progression proposée.
Elle distingue la traduction française de la transcription et de la fonction
Whisper traduisant vers l’anglais ; aucune vidéo réelle n’est déclarée traitée.

Le [bilan du travail nocturne](2026-11-14-recherche-0120-et-travail-nocturne.md)
conserve les essais exécutés et les limites. La validation finale du fonds Windows,
les ouvertures prioritaires et les observations hors ligne restent nécessaires.

La CI nocturne a également révélé un accès SQLite encore ouvert après annulation
sous Windows. Les écritures du cache sont désormais sérialisées en arrière-plan,
avec file bornée et fermeture attendue ; le résultat natif ne les attend plus.
Des tests bloquent volontairement le thread pour vérifier la fin correcte.
Les durées des premières réponses restent celles de la réception, y compris
lorsque plusieurs paquets arrivent ensemble. Voir le même bilan pour les preuves
et les écarts entre première campagne et correction finale.

La [CI finale 0.13.0](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43652127671)
réussit les huit jobs sur `a8efbdc` : Windows, Linux, archives, lecteurs isolés,
routage et navigateurs. Les recettes ciblées comptent 452 assertions par navigateur,
dont recherche 50, flux 18 et paramètres 175 ; la campagne locale termine à 521 tests,
trois ignorés. Les 729 fichiers du paquet CI sont déballés et comparés au commit.
Le nouveau R2 réel et les avis humains restent nécessaires pour fermer l’objectif.

## Précision des titres de tâches — 0.13.1, 15 novembre 2026

L’audit après 0.13.0 reproduit un autre défaut : sur « réparer un vélo » ou
« installer un panneau solaire », un titre général et un extrait mentionnant
l’action pouvaient dépasser un titre correspondant directement à la tâche.
La correction adapte ce poids sans cacher le texte général ni qualifier
l’article de procédure. Les questions « pourquoi » restent explicatives ;
« pourquoi et comment » peut conserver une intention pratique. Les preuves et
limites sont dans le [bilan](2026-11-15-classement-titres-et-intention.md).

Louis propose de faire travailler d’autres agents ; deux
[prompts coordonnés](../decisions/prompts-agents-videos-et-performances.md)
séparent inventaire vidéo/sous-titres et diagnostic des délais, sur leurs propres
branches. Aucun de ces chantiers n’est déclaré livré. L’agent principal garde
le moteur et son intégration. Le prochain R2 et les avis humains restent nécessaires.

La même 0.13.1 corrige aussi un défaut reproduit avec le Kiwix épinglé réel :
les suggestions JSON encodent les apostrophes et esperluettes en HTML dans leur
chemin. Elles créaient un faux doublon et un lien illisible, alors que le plein
texte fournissait la bonne référence. Le décodage unique avant validation réunit
les identifiants et les liens ; titres seuls et plein texte sont testés en lecture
réelle. La cause historique des indisponibilités de Marc reste non certifiée sans
son URL précise. Louis confirme ensuite le lancement des deux agents ; worktrees
`setupsurvie-videos-inventaire` et `setupsurvie-diagnostic-kiwix` constatés, avec
périmètres distincts. Le moteur et son intégration restent à la session principale.

La lecture des extraits natifs est également corrigée : les éléments XML de
surbrillance faisaient perdre les mots trouvés et la suite de la description.
Ce cas est reproduit sur le vrai Kiwix, puis protégé avec XML mixte et HTML échappé.
Le classement reçoit maintenant le passage disponible, sans qualifier son utilité
pratique automatiquement. Le cache brut reste réutilisable avec le parseur corrigé.

La validation 0.13.1 conserve les écarts au lieu de les masquer : 532 tests Python,
54 contrôles Kiwix réels et sept jobs CI réussis ; le job navigateur global échoue
sur WebKit. La relance GitHub est refusée avant exécution. En local, Chromium
réussit ses 452 assertions ciblées et quatre recettes isolées WebKit leurs 275
assertions ; la campagne WebKit globale n’est pas déclarée réussie. Les 732 fichiers
du paquet CI sont déballés et comparés au code `557ef73`. Le
[bilan détaillé](2026-11-15-classement-titres-et-intention.md) porte les limites et
la validation Windows réelle restant à faire. Les outils des deux agents sont
reçus sur leurs branches, avec tests ciblés revérifiés : inventaire vidéo 20,
diagnostic Kiwix 8. Leur intégration suit séparément cette correction du moteur.

## Intégration des deux outils — 0.14.0, 15 novembre 2026

Les commits `233ecdb` (diagnostic) et `cbec193` (inventaire vidéo) sont fusionnés
sur la base du moteur 0.13.1, sans réécrire leur historique. Les outils restent
volontaires, en lecture seule, sans nouveau bouton ni inférence. Le diagnostic
conserve mesures et traces utiles dans un export filtré ; l’inventaire fournit un
état par média et ses annexes, sans modifier les originaux ni prétendre valider
la langue ou la synchronisation. Les paroles ne sont pas encore indexées et aucun
sous-titre n’est créé par cette étape. Voir le
[bilan d’intégration](2026-11-15-integration-outils-validation-videos.md).

Les vingt tests vidéo et les neuf tests de diagnostic passent dans la campagne
locale de 561 tests, trois ignorés. Les guides et index sont actualisés ; les bilans
initiaux des agents restent datés. La CI et Windows réels des nouveaux outils
restent non validés à cause du blocage de relance GitHub, distinct des contrôles
Windows du moteur déjà exécutés. Le prochain rapport réel et les avis humains
restent nécessaires pour clore l’objectif de fiabilité sur le fonds de Marc.

Le paquet 0.14.0 est vérifié : 741 fichiers acceptés, identiques au code `ba33e8a`,
avec aide des deux scripts exécutée depuis la copie déballée. Le passage GitHub
`43689514723` ne lance aucun de ses huit jobs à cause de la restriction du compte ;
il ne donne aucun résultat d’essai supplémentaire. Les commandes Windows et la
recette sur le fonds réel restent nécessaires, sans réindexation intégrale imposée.
