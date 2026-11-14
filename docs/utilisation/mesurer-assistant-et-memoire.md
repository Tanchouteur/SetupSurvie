# Comprendre les délais et mesurer la mémoire de l’assistant

**Guide actuel — 0.7.0, 14 novembre 2026.** Les mesures des réponses n’ajoutent
aucun modèle et ne changent pas le contexte. L’essai mémoire est distinct : il
charge le modèle déjà installé après une action explicite depuis Famille.

## Comprendre une réponse lente

Après une réponse, ou pendant sa préparation, **Voir les durées** apparaît sous
la zone de conversation lorsqu’un rapport est disponible. Choisir la demande à
examiner puis **Télécharger le rapport** pour le transmettre à Louis ou à l’agent.
Les vingt dernières demandes mesurées de la conversation restent accessibles
après rechargement. Les anciennes réponses peuvent ne pas avoir de mesures.

Le rapport distingue préparation de la demande, file d’attente, métadonnées du
modèle, recherche documentaire, lecture, préparation par le modèle et rédaction.
Le premier texte est le premier texte généré reçu par le serveur, pas une mesure
exacte de son affichage sur le téléphone. La préparation du modèle comprend
l’attente de son premier texte ou de ses appels d’outils, dont sa réflexion éventuelle.

Les temps de chargement, traitement de l’entrée et génération annoncés par le
moteur sont des sous-mesures : ne pas les ajouter aux phases pour recalculer le
total. Un champ absent reste non mesuré. Le rapport indique aussi modèle/digest,
version du moteur, contexte demandé et observé, nombres de tokens renvoyés par
le moteur, estimation du budget et sources trouvées/lues en nombres seulement.

Le rapport ne contient ni question, ni réponse, ni extrait documentaire, ni
raisonnement privé. Il est réservé au profil qui possède la conversation, selon
le fonctionnement actuel des [profils locaux](profils-locaux.md). Les anciennes
traces privées d’outils restent séparées de cet export. Les mesures se conservent
également après une erreur ou une annulation commencée. Un redémarrage brutal peut
laisser une mesure incomplète ; aucun résultat physique sur coupure n’est revendiqué.

Le document associé, déjà lu par le portail pour préparer la question, est réutilisé
en mémoire par la demande. Il ne fait plus une seconde lecture identique avant
le premier appel au modèle. Cette lecture préparatoire figure dans les durées.

## Essai mémoire volontaire sur le PC serveur

1. Choisir **Famille → Mon appareil → Réglages → Mémoire de l’assistant → Mesurer
   un contexte adapté à ce PC**.
2. Réserver une période disponible, y compris dans Open WebUI. Le moteur doit
   déjà être démarré volontairement, sans mode jeu ni question/traduction en cours.
   Les mesures de mémoire du contrôleur doivent être disponibles.
3. Choisir le mode et le plafond à comparer : 16k, 32k ou 64k si le modèle le permet.
   **Lancer l’essai avec l’IA locale** peut occuper le PC jusqu’à une heure.
4. Le test mesure un petit texte synthétique pour adapter le volume, puis compare
   des entrées importantes à froid et à chaud. Il ne lit pas les documents de la
   famille. Le contexte réellement alloué et les tokens effectivement traités
   doivent être confirmés ; un petit « OK » seul ne valide pas un grand contexte.
5. **Arrêter l’essai** annule les requêtes du test. Une nouvelle question ou
   traduction est prioritaire, et une pause moteur arrête aussi les mesures.
   Après redémarrage, un nouvel essai doit être demandé explicitement.
6. Télécharger le **rapport mémoire**. Si une proposition est disponible, choisir
   volontairement **Utiliser le contexte mesuré**. Aucun réglage n’est changé par
   la seule exécution du test. **Revenir au réglage précédent** restaure la valeur
   conservée avant application, sans charger de modèle.

La proposition est le plus grand des paliers testés qui a terminé les deux essais,
respecté les marges et le délai de premier texte à chaud. Elle vaut pour ce modèle
et le scénario synthétique mesuré ; elle ne certifie pas la qualité des réponses,
une conversation quelconque remplie au maximum ni les performances d’un autre PC.
L’essai à chaud peut bénéficier du cache d’un texte identique. La proportion réelle
de texte traité figure dans le rapport. Une limite native inconnue, une allocation
non confirmée ou un texte trop court empêche la proposition correspondante.

Par défaut, le test garde **4 Gio de RAM** et **512 Mio de mémoire vidéo** disponibles,
et arrête les paliers supérieurs en cas de pression. Les sondages sont ponctuels,
pas une garantie contre toute saturation. Une autre application n’est jamais
arrêtée pour libérer sa mémoire. Le modèle du test est déchargé lorsque cela peut
être confirmé sans gêner une nouvelle demande ; le rapport signale le contraire.
Le modèle n’est jamais téléchargé ni démarré de force en levant une pause.

## Budget de contexte et maintenance

Le contexte inclut la question, l’historique utile, le système, les outils et les
extraits. Le moteur réserve la sortie et une marge pour le format des messages.
Le nombre d’octets est une estimation prudente de tokens, pas un tokenizer exact ;
le comptage réel est conservé lorsqu’Ollama le renvoie. L’historique abrégé reste
intact dans la conversation enregistrée, et appels/réponses d’outils restent groupés.
Une limite native inférieure au réglage demandé est appliquée et signalée.

Les fichiers privés sont dans `state/pilot/assistant-metrics/` et
`state/pilot/calibration/`. La sauvegarde habituelle de l’état les couvre.
Supprimer une conversation supprime ses rapports de réponse ; les essais mémoire
ne contiennent pas de conversation et conservent leur propre historique.
Les réglages et le dernier contexte mesuré restent dans `settings` de `pilot.db`.

En maintenance, les paramètres de départ admettent une réserve RAM de 2 à 16 Gio,
une réserve vidéo de 256 à 4096 Mio, un délai à chaud de 10 à 600 secondes et un
délai par essai de 30 à 900 secondes. Le défaut est respectivement 4 Gio, 512 Mio,
90 secondes et 600 secondes. Le plafond global reste une heure. Ces ajustements
se font dans le corps validé de l’API, pas par une action forcée du moteur.

Les [champs de durée d’Ollama](https://docs.ollama.com/api/chat), les
[informations du modèle](https://docs.ollama.com/api-reference/show-model-details.md)
et le [contexte des modèles chargés](https://docs.ollama.com/api/ps) définissent
les données lues. Les tests du runner sont simulés ; le rapport **R4 réel** sur
Windows reste nécessaire avant de recommander un grand contexte chez Marc.
