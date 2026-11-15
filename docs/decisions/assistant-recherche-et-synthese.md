# Recherche assistée, synthèse de sources et illustrations

**Besoin confirmé et programme retenu — 15 novembre 2026.** Louis veut pouvoir
décrire un besoin à l’assistant, obtenir une synthèse utile de plusieurs documents
et retrouver leurs schémas. Le nombre de cinq sources est un exemple, pas une
limite produit ni une promesse d’utilité de chaque document. Il propose aussi une
boucle de travail plus agentique si elle améliore la cohérence.

## Ce que les nouveaux éléments établissent

Le R2 sans IA **0.15.0**, créé à 11:15:41 UTC, annonce les 32 recherches complètes,
sans archive en erreur ni reformulation omise. Première réception médiane 268 ms,
fin médiane 2 112,5 ms. Le feu atteint notamment Wikilivres et Wikipédia.
**1 099 traces sur 1 155** réutilisent le cache : ces temps ne sont pas un essai
à froid et n’isolent pas l’effet d’une seule correction. Aucun avis humain n’est
encore enregistré ; couverture complète ne signifie pas contenu qualifié.

Deux captures montrent ensuite la même demande de synthèse avec GPT-OSS 20B et
Gemma4 E4B : affirmation d’absence, mais suivi « recherche limitée, aucune source
consultée ». Le texte du modèle ne permet pas de conclure à des documents absents
ou à une indexation manquante. Ces captures ne mesurent pas la fréquence ni la
cause des réponses qui n’aboutissent pas ; les durées de ces demandes manquent.

La phrase exacte « Fait un synthese sur les info des document sur comment faire
du feux » produit dans le code 0.15.0 les groupes obligatoires `synthese`, `info`,
`feu`. Le moteur peut donc écarter le sujet avant la première génération. La
relance sur « allumage au frottement (comme le feu de bois) » conserve aussi
`comme` et n’est pas préparée automatiquement comme lecture documentaire.
Ce défaut reproduit ne dépend pas du modèle choisi. Il ne prouve pas à lui seul
le détail exact des outils exécutés sur les deux conversations de Marc.

## Socle actuel et premier correctif

**Évolution 0.16.0 :** le [dossier documentaire](../utilisation/synthese-documentaire.md)
remplace la prélecture limitée décrite ci-dessous par des passages de plusieurs
sources adaptés au contexte. Il ajoute lecture par lot, arrêt des répétitions,
une liaison structurée des références et la conservation des réponses incomplètes.
Les essais réels R7 portent sur un corpus fictif ; le [bilan](../essais/2026-11-15-synthese-multi-sources-et-essais-reels.md)
distingue les faits retrouvés des erreurs de conclusion encore possibles.
La 0.17.0 ajoute la sélection manuelle multiple persistante et la lecture d’une
page pertinente dans les PDF choisis. La 0.18.0 ajoute une lecture longue explicite, des instantanés et notes
intermédiaires reprenables, puis une synthèse hiérarchique. La 0.19.0 propose les illustrations originales et pages PDF ; vision et
fidélité sur un corpus représentatif restent à qualifier. Les paragraphes 0.15.x conservent le point de départ daté.

Le moteur d’assistant dispose déjà d’une boucle d’outils : trois étapes en mode
rapide, six dans les autres modes. La préparation documentaire lit automatiquement
au plus deux premiers documents, avec des passages de début limités à 2 200
caractères. Le portail associe manuellement un seul document à la conversation.
Les résultats proposés à l’assistant et cette association sont deux choses
différentes : il peut appeler l’outil de lecture sur plusieurs sources, mais
l’usage multi-document n’est pas encore un parcours de synthèse fiable.

Le JSON des outils conserve un budget natif de douze secondes et 32 appels,
alors que le portail progressif dispose de 60 secondes et d’un plafond adapté.
L’algorithme documentaire est partagé, mais les budgets et le texte de demande
peuvent donc expliquer des résultats différents. La 0.15.1 corrige la demande
conversationnelle et la préparation des relances pratiques ; elle ne déclare pas
livré le programme complet ci-dessous et ne change pas ces budgets.

Le retour supplémentaire de Louis décrit un premier envoi qui échoue lors d’un
changement de modèle, puis un second qui fonctionne. Sans mesures, le déchargement
seul reste une hypothèse. Le correctif 0.15.1 ajoute une préparation explicite du
modèle cible lorsqu’un autre est chargé et une reprise bornée avant toute sortie,
avec état visible, conservation de la question et respect de la pause. La
[mesure des réponses](../utilisation/mesurer-assistant-et-memoire.md) en précise les
limites ; l’essai réel du changement de modèle reste à faire.

## Suite à réaliser : un travail documentaire contrôlé

1. **Comprendre le besoin.** Séparer sujet, action et format demandé. « Fais une
   synthèse sur… » est une instruction de réponse ; « synthèse chimique » reste
   un vrai sujet. Garder filtres, langue, intention et sujet des relances.
2. **Chercher et sélectionner.** Utiliser le moteur commun, compléter une recherche
   limitée lorsque cela est utile, réunir des sources pertinentes et diverses,
   éviter les doublons. Montrer ce qui est trouvé pendant l’attente et permettre
   aussi à l’utilisateur de sélectionner plusieurs documents.
3. **Lire les bons passages.** Chercher les sections répondant au besoin au lieu
   de fournir systématiquement le début. Conserver page, position, lecture
   partielle et parties non examinées. Faire varier le nombre et la longueur des
   passages selon la question et le contexte réellement disponible.
4. **Compléter les manques.** Le modèle peut demander une recherche ciblée ou une
   lecture supplémentaire, puis constater si elle apporte un élément nouveau.
   Caches, temps, nombre d’actions et répétitions sont bornés. Une boucle sans
   progrès s’arrête avec une limite explicite. Les faits reçus des outils et un
   état d’avancement sont vérifiables ; une auto-évaluation du modèle ne vaut pas
   validation et son raisonnement privé n’est pas publié comme une preuve.
5. **Synthétiser.** Produire une réponse structurée, en français, de longueur
   demandée, avec références aux passages lus, accords/désaccords et points
   manquants. Si les textes dépassent le contexte, préparer des synthèses
   intermédiaires conservant leur provenance avant la synthèse commune.
   Ne pas prétendre avoir lu cinquante pages quand seuls des extraits ont été lus.
6. **Rester utilisable en échec.** Montrer les sources et le travail déjà effectué
   si le modèle dépasse sa durée, manque de mémoire ou ne produit pas de texte.
   Mesurer recherche, lecture, préparation et génération séparément. Ne pas
   remplacer une erreur par « aucun document disponible ».

Cette suite porte sur l’utilité de l’assistant. Elle ne remplace pas la recherche
sans IA, ne nécessite pas une activation de l’aide IA dans le classement ordinaire
et ne doit pas faire attendre une recherche pour charger un modèle.

## Schémas et illustrations originales

**Afficher un schéma existant est possible sans modèle vision.** Le logiciel doit
retrouver l’illustration ou la page d’origine, l’afficher avec sa légende et son
lien, et préserver mesures, unités et avertissements. La recherche du bon schéma
et son extraction restent à implémenter et tester ; le seul fait qu’un lecteur
affiche une image ne prouve pas sa sélection pertinente.

**Depuis 0.19.0**, le [parcours des illustrations](../utilisation/illustrations-et-references.md)
propose les images d’articles ZIM et les pages PDF effectivement retenues, avec
légendes, sources et accès à l’original. La sélection est préparée avant la
rédaction et peut être complétée après une lecture supplémentaire. Le modèle
choisit des identifiants délivrés par le serveur ; une page est conservée entière,
sans extraction automatique du seul dessin. Le [bilan](../essais/2026-11-15-illustrations-originales.md)
conserve les essais infructueux et les limites. La sélection pertinente n’est
pas garantie sur tout le fonds ; pages scannées, autres formats et vision restent
à éprouver ou développer.

Pour **interpréter** une image — repérer des composants, expliquer une flèche ou
lire les valeurs d’un diagramme — il faut fournir cette image à un modèle adapté
et vérifier le résultat. Le parcours actuel ne lui envoie pas ces images.
Une illustration générée ne doit pas remplacer silencieusement un schéma technique
source. Les droits, limites d’accès local et sources de l’image restent conservés.

## Modèle et matériel : décision après mesures

Le besoin est compatible avec une architecture locale par passages et étapes.
Il ne demande pas de charger toute la bibliothèque ou cinq livres entiers en
mémoire à chaque question. Avec les 8 Go de VRAM et 32 Go de RAM rapportés chez
Marc, choisir le modèle, le contexte et les budgets après mesure réelle ; aucune
cadence ou qualité d’une configuration précise n’est certifiée par cette étude.

Un modèle mieux adapté peut améliorer fidélité, français et usage des outils.
Il ne corrige pas automatiquement les mots obligatoires imposés par le logiciel
ou une extraction vide. Un contexte plus grand augmente la mémoire demandée ;
une répartition CPU/GPU défavorable peut ralentir l’inférence. La multiplication
des tours de réflexion peut aussi augmenter l’attente sans apporter de preuve.
Ni achat GPU ni changement des profils conseillés n’est décidé sans R4 exploitable.

Références officielles consultées le 15 novembre 2026 :
[contexte et placement mémoire Ollama](https://docs.ollama.com/context-length),
[transmission des images à un modèle vision](https://docs.ollama.com/capabilities/vision).
La configuration épinglée et les profils locaux restent les références du pilote ;
les valeurs par défaut d’une documentation récente ne prouvent pas celles de son
installation ni les capacités effectivement chargées d’un modèle.

## Validation demandée pour cette suite

Conserver les formulations réelles, les noms de sources attendues et les relances
dans les régressions, sans textes de conseils pratiques inventés. Tester demande
de synthèse, ambiguïté technique, cinq sources disponibles ou moins, faux doublon,
passage utile loin du début, document illisible, contradiction, contexte réduit,
arrêt, boucle répétée, absence de texte final et illustration source.

Les cas observés servent au réglage ; prévoir aussi des besoins distincts pour
la vérification, sans les présenter comme une évaluation aveugle une fois utilisés
pour modifier le moteur. Tester avec HTTP et modèles simulés dans le runner,
puis avec un modèle réel volontairement lancé sur le PC cible. Le rapport
**Voir les durées** et une lecture des réponses sont nécessaires pour expliquer
les échecs réels ; pas d’inférence forcée en mode jeu.
