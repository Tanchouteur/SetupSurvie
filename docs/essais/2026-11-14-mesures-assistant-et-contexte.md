# Mesures de l’assistant et calibration explicite du contexte

**Bilan daté — 0.7.0, 14 novembre 2026.** Lot L4 du
[plan retenu](../decisions/plan-ameliorations-marc.md). Objectif : expliquer les
délais réels et préparer R4, sans prétendre les avoir mesurés sur le PC de Marc.

## Changements

- Mesures numériques durables par demande : préparation initiale, file, catalogue
  de modèle, recherche, lecture, préparation du modèle, premier texte et rédaction.
  Les échecs et annulations commencées gardent aussi leur rapport.
- Métadonnées locales lues sans inférence : modèle installé, digest, limite native,
  version moteur et contexte/placement observés. Une limite native inférieure est
  appliquée au contexte demandé, avec état explicite.
- Budget d’entrée incluant les outils, la sortie et la marge de format. Estimation
  UTF-8 conservatrice, nombres réels du moteur lorsqu’ils existent ; paires d’outils
  et question actuelle conservées. Aucun comptage exact universel n’est revendiqué.
- Suppression d’une lecture en double du document associé : l’instantané déjà lu
  pendant la préparation de la requête est transmis en mémoire au travail accepté.
- Rapport accessible depuis la conversation, après rechargement et exportable sans
  texte de question/réponse/source ni raisonnement privé. Les traces existantes restent
  privées et séparées ; le nouveau rapport ne les expose pas.
- Calibration volontaire sur modèle local présent, texte synthétique adapté au
  nombre réel de tokens, essais à froid et à chaud, contexte alloué vérifié. Paliers
  16/32/64k selon limite et choix. Pas de téléchargement, de reprise forcée ni de
  réglage automatique de la valeur courante.
- Réserves RAM/vidéo, arrêt sur nouvelle demande, pause, erreur, lenteur ou volume
  insuffisant. Application explicite liée au digest et au matériel observé, retour
  au réglage précédent, rapports conservés et absence de reprise après redémarrage.

## Choix retenus et limites

Retenu : plus grand palier terminé avec les marges du scénario, puis application
volontaire. Écartés : imposer le maximum natif, remplir toute la RAM, déduire la
stabilité d’une toute petite entrée ou déclarer une calibration réelle depuis le
runner CPU. Le test à chaud réutilise le même texte : le cache peut aider sa vitesse.
Les marges et la charge sont observées ponctuellement, sans garantie de pire cas.
Open WebUI ne partage pas le verrou des travaux du portail ; réserver la période
aux mesures reste une condition d’essai. Les autres applications ne sont pas arrêtées.

Les API primaires Ollama ont été relues pour les durées en nanosecondes, les
métadonnées et le contexte chargé : liens dans le [guide actuel](../utilisation/mesurer-assistant-et-memoire.md).
Les détails de modèle, licence, gabarit et vocabulaire ne sont pas recopiés dans
le rapport ; seuls les champs nécessaires y figurent.

## Vérifications

Orchestration HTTP simulée : froid/chaud, volume mesuré, limite native, pression RAM,
pause avant contact, pause pendant appel, priorité à une nouvelle question,
annulation, absence de reprise, modèle distant refusé et digest modifié refusé.
Application répétée sans perte du réglage précédent et retour vérifiés. Aucun
modèle, corpus, ZIM volumineux ou carte n’a été téléchargé.

Tests assistant : métadonnées lues distinctes des résultats cherchés, citations
réellement consultées, réutilisation du document préchargé, rapports sans contenu
privé, mesures conservées sur erreur, réduction au contexte natif et budget outils.

Chromium MCP : 19 contrôles nouveaux de durées/calibration simulées ; recherche
(45), classement (19) et confort de conversation (37) également vérifiés. Pas de
débordement observé à 1366/390/320 pixels pour les nouvelles commandes.

La [CI finale sur le code b10c7ec](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43611740909)
est réussie : **435 tests Python, dont trois ignorés**, contrôles Windows,
29 vérifications Kiwix sur cinq petites archives générées, routage synthétique,
Chromium et WebKit. Les deux navigateurs passent notamment les 19 nouveaux
contrôles de durées/calibration, les 19 de classement et les 14 d’outils de recherche.
Les essais mémoire sont simulés, y compris le refus d’une application devenue
périmée pendant la vérification du modèle ; aucun essai matériel n’en est déduit.

**Version mineure 0.7.0** : nouveaux rapports et essai explicite compatibles avec
le schéma 1 et les états existants ; images tierces inchangées. Aucun gain de vitesse,
grand contexte stable ou qualité de modèle n’est validé sur le matériel de Marc.
R1/R2/R3/R4 réels et les suites restantes du plan restent ouverts.
