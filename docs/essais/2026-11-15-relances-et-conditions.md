# Relances, conditions de départ et appels d’outils

**Bilan daté — 0.20.0, 15 novembre 2026 ; validation complétée le 16.** Suite du
[guidage pratique 0.19.1](2026-11-15-notices-et-guidage-pratique.md).
La [référence d’usage](../utilisation/sources-et-fiabilite.md#reprendre-une-discussion-et-vérifier-les-conditions-de-départ--0200)
décrit le comportement courant. Les résultats ci-dessous restent limités aux
cas, modèles et machines effectivement essayés.

## Problèmes reproduits

- La bonne page de notice est lue mais la procédure omet une condition de départ.
  Le cas UV‑5R omettait la ligne supérieure de l’écran, pourtant sur la page reçue.
- Une relance peut recopier un ancien numéro `[1]` sans relire le document.
  Le moteur ne recevait que les textes de l’historique, sans pointeurs documentaires.
- Un ancien modèle de code décrit `search_library` en JSON dans le texte,
  sans émettre d’appel natif. La réponse pouvait être marquée terminée malgré zéro
  recherche et lecture. Les modèles plus gros ne sont donc pas retenus par taille.

## Changements retenus

Les sources de la dernière réponse sont des **repères non consultés** pour le
nouvel échange : identifiant, titre, ancienne question, sans anciens numéros ni
extraits hérités. Une relance référentielle relit jusqu’à quatre sources ; une
sélection manuelle ou une demande explicite d’une autre collection reste prioritaire.
Les lectures recréent les références et le suivi. Un changement de sujet ne doit
pas imposer les anciens documents. La détection linguistique reste limitée.

Les références numériques et identifiants de sources non lus sont refusés, même
sans recherche préparatoire. Un appel JSON textuel reconnu déclenche une reprise
native au maximum ; le logiciel ne l’exécute jamais comme une commande. Une sortie
encore inutilisable devient incomplète avec explication, sans preuve inventée.
Les arguments natifs mal formés donnent une erreur d’outil, sans perdre l’échange.

Pour une demande de procédure, une relecture bornée peut proposer des conditions
omises parmi les textes déjà lus. Le modèle choisit des identifiants de segments ;
le serveur affiche **avant les étapes** leurs mots exacts, avec source. Aucun fait
réécrit ni segment inconnu n’est accepté. Le balisage et les crochets du document
restent littéraux : une touche `[2]` citée ne devient pas une fausse référence.
La réponse reste accessible si cette vérification optionnelle échoue. Les appels
complémentaires vérifient aussi que le moteur n’a pas été mis en pause.

## Essais réels et approches corrigées

Essais sur le R7, Ollama natif 0.40.14, modèle déjà présent `gemma4:e4b`, contexte
16k, sortie 4 096 tokens, 32 couches GPU, six threads, réserve 1 536 Mio et maintien
quinze secondes. Aucun poids téléchargé, appareil commandé ou logiciel tiers arrêté.
Les guides réels et rapports restent hors Git ; la notice constructeur correspond
au catalogue figé de la 0.19.1. Aucun déploiement ou essai Windows chez Marc.

1. **Repères seuls, insuffisants.** `report-gemma4-continuity.json` : la procédure
   reçoit bien la condition oubliée, mais la relance copie sa citation sans lire.
   Les lectures explicites automatiques des relances et le contrôle sans recherche
   préalable corrigent ce défaut ; les repères seuls ne sont pas considérés suffisants.
2. **Relecture sans bon contexte, mauvais complément.**
   `report-gemma4-continuity-final.json` : la relance lit réellement la page, mais
   le contrôle des conditions ajoute une condition du mode duplex à une procédure
   simplex. Une citation exacte n’a donc pas suffi à assurer la pertinence.
   Le contrôle reçoit ensuite la question initiale avec la relance. Une demande
   portant déjà sur les conditions ne déclenche plus une deuxième liste de manques.
3. **Rejeu après correction de ce contexte.**
   `report-gemma4-continuity-release.json` : procédure avec la condition de ligne
   supérieure avant les étapes, puis relance lisant la même page et donnant VFO,
   fréquence saisie et ligne supérieure. Durées 22 178 et 12 690 ms.
   `report-gemma4-continuity-steps.json` : une relance demandant les étapes conserve
   le contexte simplex et la condition correcte, 16 857 et 10 337 ms.
   Empreinte Python de ces deux rapports :
   `1e24801ec3621bb5eea749b19744a50af3ac604db3b3265030249395d235c994`.
   Des contrôles de pause complémentaires ont ensuite été ajoutés ; ces durées
   ne sont pas présentées comme celles d’un autre code ou du PC de Marc.
4. **Modèle de comparaison toujours inadapté.** `report-qwen14-protocol.json` :
   `qwen2.5-coder:14b` décrit l’outil, reçoit la reprise, puis ne produit plus de
   texte. Les deux cas solaires deviennent incomplets, zéro lecture, au lieu de
   simuler une réponse accomplie. Ce résultat ne valide pas son aptitude documentaire.
   La livraison distingue aussi cette absence après reprise comme `tool_protocol`.

5. **Code final du moteur**, empreinte Python
   `53e9cd7da7e29c07b1cb9cf67e65369baebe0ee02a910a691bf843ea3b7b51fd` :
   `report-gemma4-0200-radio.json` termine cinq des six demandes. Les dimensions
   sont 51,69 cm à 145 MHz, 34,62 cm au total / 17,31 cm par bras à 433 MHz et
   50,81 cm à 147,5 MHz. La demande de mémorisation échoue une fois au contrôle
   des références, puis le rejeu isolé `report-gemma4-0200-memory-diagnostic.json`
   termine en 21 447 ms avec la bonne condition et les étapes. Ce rejeu n’efface
   pas l’échec initial : la variabilité du modèle reste observable.
   `report-gemma4-0200-followup.json` termine procédure et reprise des étapes,
   17 675 et 13 139 ms, avec relecture propre et condition simplex pertinente.
   `report-gemma4-0200-solar.json` distingue +5 V au démarrage / +1 V en poursuite,
   puis 75 V PV / 15 A de charge batterie, 27 137 et 9 640 ms.
   La recette suivante conserve aussi les réponses refusées dans les rapports
   privés ; elles ne sont ni publiées comme réponse valide ni ajoutées à Git.

Les premiers essais restent conservés. Cette série a servi au réglage, ce n’est
pas une évaluation aveugle. L’exactitude des commandes et prérequis est examinée
sur les réponses, pas déduite du seul statut `done` ou du nombre de sources.

## Vérifications de livraison

Le commit fonctionnel `b9b10517b9c6c0cea850bd22dce7ae1c17cc31b3` réussit
les [huit jobs CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43775005962).
Localement : **742 tests, trois ignorés spécifiques à Windows**, suite complète
réussie. Un ancien test exigeait exactement 40 ms de lecture malgré le temps
supplémentaire réellement cumulé : l’exigence vérifie désormais au moins les
40 ms déjà enregistrées et l’absence de nouvelle lecture réseau, sans faire
passer un résultat d’exécution faux pour une réussite.
Les recettes navigateur vérifient les mesures sans texte privé et le rendu de
l’extrait avec les vraies fonctions de message/citation : 33 contrôles par moteur,
Chromium et WebKit. Le MCP Chromium vérifie aussi 25 contrôles de diagnostic et huit
de rendu. Captures examinées dans les artefacts privés, sans simulation d’iPhone réel.

## Limites et suite

La sélection de conditions n’est ni exhaustive ni une certification du sens.
Elle dépend du texte extrait, de marqueurs français/anglais et du modèle ; elle
peut encore manquer ou répéter une condition, ou choisir un passage non pertinent.
Le contrôle ajoute un appel et peut attendre jusqu’à 60 secondes ; son temps,
son état et le nombre de segments retenus sont mesurés sans exporter leur texte.
Le moteur n’est pas spécialisé avec les menus du Baofeng ou des réponses solaires.

La reconnaissance des relances et des propositions JSON couvre certains formats,
pas tous les discours ni tous les modèles. Les anciennes références ne sont pas
promues en preuves et les historiques ne sont pas réécrits. Les résultats réels
sur le modèle GPT‑OSS conseillé, la bibliothèque Windows de Marc, des procédures
d’autres métiers et des livres très longs restent à obtenir.

Ni traduction intégrale de livre ni récupération/création de sous-titres français
n’est livrée par ce lot. Ces travaux gardent leurs protocoles et limites distincts.
Le passage mineur **0.20.0** correspond aux nouveaux comportements compatibles de
relance et de relecture des conditions ; schéma des données 1 et images tierces
inchangés, sans annonce de version stable.
