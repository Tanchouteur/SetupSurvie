# Diagnostic des lenteurs en un clic

**Demande de Louis, 16 novembre 2026 — proposition retenue, non livrée.**
Le traitement de la lecture française est en cours ; ce chantier de mesure
complète ensuite l’objectif de fiabilité de la recherche et de l’assistant.

Louis souhaite lancer depuis le site une seule campagne, puis exporter son
rapport pour déterminer ce qui ralentit la recherche documentaire et l’IA :
CPU, disque, RAM/VRAM, recherche et lecture des passages, chargement du modèle,
traitement de l’entrée ou génération. Ne pas confondre capacité occupée et
activité réelle, ni annoncer un composant coupable sans mesure suffisante.

## Existant à réutiliser

- Recherche commune et flux progressif : premiers documents, fin, couverture,
  appels, cache et CPU de traitement du pilote ; script `diagnose_kiwix.py` distinct.
- Mesures de l’assistant : phases, tokens, durées déclarées par Ollama, contexte,
  modèles chargés et reprises ; calibration mémoire distincte et volontaire.
- Contrôleur natif : RAM disponible, GPU utilisé et activité NVIDIA lorsqu’elle
  est disponible, espace disque. Il ne mesure pas encore les compteurs d’activité
  CPU/disque nécessaires au diagnostic demandé.

## Résultat attendu

Un bouton dans Entretien lance une campagne bornée, explicite, annulable et
exportable : état initial, quelques recherches répétées sans IA puis génération
seule et réponse documentaire avec le modèle choisi. Le moteur doit déjà être
démarré volontairement ; une pause n’est jamais levée par le test. Les autres
applications ne sont pas arrêtées et leurs activités peuvent influencer le rapport.
Ne pas vider les caches ni imposer un déchargement de modèle. Le premier passage
reste « état initial inconnu », suivi d’une répétition réchauffée.

Échantillonner les ressources du **serveur cible**, avec origine des compteurs,
horodatages et portée. Distinguer machine Windows/Linux, pilote et Kiwix ; ne pas
présenter les ressources du navigateur ou de la VM de développement comme celles
du PC de Marc. Ajouter des compteurs natifs CPU et disque quand disponibles,
puis les rapprocher des phases mesurées. Un contrôleur ancien ou une sonde absente
reste signalé comme non mesuré ; le logiciel ne fabrique pas de zéros.

L’explication doit distinguer fait observé, cause possible à confirmer et cause
non déterminée. Montrer le temps dominant, les indicateurs réellement recueillis
et les limites : plusieurs charges, mesures agrégées, cache déjà chaud, manque de
compteur ou pression mémoire. Une VRAM pleine ou un disque occupé ne prouve pas
à soi seul la cause de la lenteur. Les conseils matériels viennent après ces faits.

Le rapport exportable garde version, protocole, mesures, provenance, erreurs et
étapes non faites. Éviter les textes de documents, conversations et raisonnement
privé. Un changement du contrôleur doit rester compatible avec les installations
Windows/Linux et leur mise à jour ; documenter ce qui nécessite son redémarrage.

## Validation à fournir

Tests CPU et HTTP simulés sur compteurs Windows/Linux, rapports partiels,
annulation, pause moteur, moteur absent, autres activités et compteurs manquants ;
essais navigateur du bouton et de l’export. Puis campagne réelle sur R7 sans
forcer de charge tierce, et rapport Windows de Marc lorsque disponible. Aucune
mesure R7 ne certifie les performances de son PC ni la pertinence des réponses.
