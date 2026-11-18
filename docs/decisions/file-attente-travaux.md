# File d’attente des travaux SetupSurvie

Décision de Louis, 18 novembre 2026. Le portail doit donner un point de suivi
commun aux questions, traductions, transcriptions, sous-titres et téléchargements
YouTube. Le réglage de l’ordre porte sur les travaux qui attendent. Une erreur
doit rester visible tout en libérant la place pour la suite.

## Suivi du chantier

- [x] Identifier les refus de yt-dlp par vidéo, isoler les erreurs et rendre la reprise possible.
- [x] Enchaîner automatiquement le téléchargement, l’indexation du titre, la
  préparation des sous-titres et leur indexation après transcription ou traduction.
- [x] Piloter les travaux depuis une file réordonnable avec une pause et une reprise globales.
- [x] Afficher la file dans la navigation, avec un aperçu au survol et au clavier,
  une page accessible au toucher et des erreurs visibles séparément.
- [x] Raccorder les reprises et contrôles du chantier de fiabilité des traductions.
- [ ] Vérifier priorités, erreurs, reprise, recherche par titre et par sous-titres
  ainsi que les parcours de navigation sur ordinateur et téléphone.

La capture de Marc montre le départ d’une liste de sept vidéos. Le compte rendu
communiqué ensuite indique six téléchargements sans sous-titres et un échec
yt-dlp à la ligne 2. Le détail du refus yt-dlp de cette ligne reste inconnu.


La version **0.50.0** ajoute une fonctionnalité compatible au portail. Le
planificateur reprend les points d’acquisition du moteur existants et fait
passer les étapes de la chaîne vidéo par les mêmes travailleurs que les
actions manuelles. Les essais automatisés peuvent vérifier ces enchaînements
avec un contrôleur et des modèles simulés. La recette sur le PC Windows de
Marc, le détail exact de sa ligne 2 et la reconnaissance sur ses propres
vidéos restent à valider sur place.
