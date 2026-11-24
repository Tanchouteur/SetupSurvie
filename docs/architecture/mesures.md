# Architecture — mesures et diagnostics

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Mesures et calibration — 0.7.0

`assistant_metrics.py` conserve des mesures numériques par travail sous
`assistant-metrics/`, sans contenu documentaire ou conversationnel. La requête
transmet son instantané de source et ses durées préparatoires par une mémoire
éphémère indexée par l’identifiant accepté ; le travail n’effectue pas une seconde
lecture identique. Les mesures finales sont écrites même après erreur/annulation
commencée. L’accès et l’export vérifient le propriétaire du travail ; la suppression
d’une conversation enlève ses mesures. Les traces d’outils existantes restent séparées.

`model_runtime.py` lit les métadonnées locales, jamais `/api/pull`. Le budget réserve
sortie, schéma des outils et marge de format avant de compacter les messages. La
limite native de l’architecture principale est distinguée des limites d’un éventuel
encodeur d’image. Le contexte et placement effectivement chargés restent observés
séparément du réglage demandé.

`calibration.py` partage le verrou d’inférence avec réponses et traductions. Après
action Famille, il calibre la taille du texte synthétique puis vérifie froid/chaud,
volume réellement traité, mémoire et contexte alloué. Une demande normale est
prioritaire ; pause/pression/annulation interrompent le test sans reprise forcée.
L’application du résultat est explicite et liée au digest, à la limite native et
au matériel observé. Les rapports privés restent sous `calibration/`, le réglage
précédent et le dernier contexte mesuré dans `settings`, sans migration destructive.

## Comparatif facultatif de recherche (0.8.0)

`pilot/search_experiment.py` utilise le moteur documentaire commun puis deux appels
structurés au modèle local présent. Il est accessible uniquement par actions Famille
`/api/admin/search-experiment`, `/start`, `/stop` et `/review`. Le verrou moteur,
les réserves et la priorité des conversations sont partagés avec la calibration ;
la recherche normale ne dépend pas de ce module optionnel. Rapports durables privés
dans `search-experiments/`, pas de reprise automatique ni de réglage modifié.
`pilot/search-reference.json` est la référence embarquée ; le générateur de portail
produit sa copie statique. Voir le [guide](../utilisation/comparer-recherche-ia.md).

## Recette d’usage depuis le navigateur (0.10.0)

`portal/interface/usage-recipe.js` utilise uniquement les API de lecture existantes,
sans commande d’inférence/préparation. Le contrôle comprend au maximum deux
recherches et deux aperçus, quinze secondes par lecture et 90 secondes au total.
Le profil, la génération et le contrôleur d’exécution isolent les réponses tardives.
La version est contrôlée avant/après. Le brouillon local ne persiste pas les
mesures, qui restent à relancer après rechargement. Le JSON R7 sépare observations
humaines et mesures, sans texte de source ni manifeste complet. La coupure réseau
est une déclaration de l’opérateur ; voir le [guide](../utilisation/verifier-usage-hors-ligne.md).

## Diagnostic commun des performances — 0.22.0

`pilot/performance.py` orchestre une campagne administrative explicite et bornée,
sans dépendre de l’onglet navigateur. Recherche commune puis vrai moteur assistant,
avec une réponse supplémentaire sur les documents déjà sélectionnés. Les réponses
temporaires sont nettoyées ; seuls les compteurs autorisés sont exportés.
L’API `/api/admin/performance` fournit le suivi compact, `/report` les échantillons ;
`/start` et `/stop` sont des actions explicites. Le module reste optionnel.

Le pont authentifié `operations.performance` lit `/performance` du contrôleur
natif. `scripts/host_performance.py` collecte CPU/disques/pagination Linux ou PDH
Windows, sans processus auxiliaire sur Windows. RAM/GPU réutilisent les mesures
du contrôleur avec âge indiqué. Absence, première mesure et correspondance de
volume inconnue restent explicites. Ni ports publics supplémentaires ni changement
de protocole de données : schéma produit 1. Voir le [guide de mesure](../exploitation/diagnostic-complet-performances.md).

Vue de référence documentaire actualisée le 15 novembre 2026. Elle décrit les rôles
des composants ; les [bilans](../essais/README.md) indiquent les validations réalisées.

## Refus avant lancement et diagnostic — 0.30.0

`startup_diagnostic.observe()` entoure les quatre créations de test et conserve
les refus 409/429/503 d’un mode connu, sans modifier le code HTTP/message originel.
Le fichier privé `startup-diagnostic.json` garde vingt observations au maximum.
Les objets libres sont filtrés par champs/types/enums avant écriture ; aucune
URL locale, liste de noms de modèles supplémentaires ou trace d’exception n’est
exportée. Les probes utilisent seulement GET version/ps/tags en parallèle,
avec délais courts ; pas de show/pull/chat/generate.

Le contrôleur écrit `last-engine-diagnostic.json` même après une commande en
échec, avec étape et durée, et expose uniquement ce résumé autorisé dans status.
L’export admin `/api/admin/assistant/startup-report` combine historique et nouvel
instantané ; les deux dates restent explicites. Il n’est pas interrogé au
chargement de l’interface et ne change aucun état du moteur.

## Ressources et lecture progressive — 0.39.0

`resource-status.js` reprend l’événement `survie:inference` du portail ; dans les
cartes, il effectue une observation GET périodique seulement sur ordinateur
visible. Aucune commande de démarrage n’est associée à la navigation. Le
contrôleur distingue une liste de modèles vide d’une observation impossible.
`model_session.KEEP_ALIVE` centralise la conservation sans expiration après
inactivité ; les arrêts explicites restent prioritaires.

`translation-text.js` partage un rendu Markdown local assaini entre le lecteur
Bibliothèque et la fenêtre de lecture. Les passages déjà affichés conservent
leurs nœuds pendant les mises à jour ; le changement de groupe reste volontaire.
Voir les guides [mémoire](../utilisation/mesurer-assistant-et-memoire.md) et
[traduction](../utilisation/documents-et-traduction.md) pour les comportements et
les limites, notamment l’absence de recomposition des illustrations du PDF.
