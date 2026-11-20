# Suivre les travaux de SetupSurvie

**Guide actuel — actualisé pour la 0.67.3.**

Dans **Mon appareil**, l’onglet **File d’attente** ouvre cette même page.
**À suivre** affiche les tâches actives, en attente et celles qui demandent une
intervention. **Historique récent** rassemble les derniers travaux terminés ou
annulés, y compris les traductions et synthèses du profil sélectionné. Les
boutons **?** expliquent le fonctionnement de la file et de chaque groupe.
Ils s’ouvrent au toucher, à la souris et au clavier.

Pour une préparation de l’appareil, ouvrez **Détails techniques** sur
sa carte. Les volets ouverts et le focus sur leur titre restent en place
quand les chiffres de la carte s’actualisent. Selon le travail, vous y verrez les fichiers actifs, les volumes
vérifiés, la dernière observation ou le nombre de documents indexés. Le
titre de la carte renvoie à la page d’origine, qui conserve les commandes
propres à cette préparation. Le profil Famille peut aussi mettre en pause
ou reprendre une préparation depuis sa carte quand le bouton est proposé. Une
indexation d’archives en attente affiche le motif du délai. Les transferts Windows indépendants restent
consultables en lecture seule. L’ancienne adresse de suivi ouvre la file.

Dans la barre de navigation du portail, l’icône de la file indique le nombre
de tâches visibles en cours ou en attente. Sur ordinateur, survolez l’icône
ou atteignez-la avec la touche Tab pour afficher l’aperçu des tâches. Cliquez
sur l’icône ou sur **Ouvrir la file** pour passer à la page dédiée. Sur
téléphone, l’icône ouvre directement cette page.

La page indique le contenu, l’étape, le modèle sélectionné et l’avancement
quand le traitement sait le mesurer. Dans l’aperçu du portail et sur la page,
maintenez la poignée à trois barres à droite d’une tâche en attente pour la
glisser avant ou après une autre. Au clavier, sélectionnez la poignée puis
utilisez les flèches haut et bas. Dans l’aperçu, la carte suit la poignée,
les cartes voisines lui font de la place et un contour souligne la section
dans laquelle elle peut être déposée. Sur téléphone, faites glisser la poignée
avec le doigt sur la page dédiée. Les réponses et les traductions de documents
s’affichent dans leur propre profil. Les travaux de la bibliothèque sont
communs et le profil **Famille** peut modifier leur ordre.

L’aperçu et la page montrent trois créneaux indépendants.

- **Assistant et traductions** utilise le moteur IA, une tâche à la fois.
  Les questions passent au prochain créneau libre. Après trois questions
  prioritaires, une tâche de fond qui attend reçoit un tour. Un passage déjà
  commencé se termine avant de libérer le moteur.
- **Téléchargements** suit les lots YouTube et la récupération des sous-titres.
  Ils peuvent avancer pendant une réponse.
- **Préparation locale** suit la transcription audio sur le processeur et
  l’inventaire des vidéos et sous-titres ainsi que l’examen des vidéos dans
  les collections. Les deux inventaires restent visibles pendant un autre
  traitement local. Whisper utilise jusqu’à quatre fils de calcul pour
  laisser de la capacité au reste du portail. Une traduction des sous-titres rejoint le créneau IA
  lorsque la piste source est disponible.

**Ensuite** désigne le prochain travail prévu dans chaque créneau. Une nouvelle
question peut changer ce choix pour l’IA. Les poignées règlent l’ordre au sein
d’un même créneau et d’un même niveau de priorité.

Avec **Famille**, utilisez le bouton pause ou lecture en haut de l’aperçu,
à côté d’**Ouvrir la file**. Sur la page dédiée, retrouvez **Mettre en pause**
et **Reprendre la file**. La pause empêche le démarrage des étapes suivantes
pour les tâches pilotées par la file. Elle demande aussi l’arrêt de l’inventaire
des vidéos et la pause des préparations documentaires suivies par le PC serveur,
dont le classement du fonds principal. Les cartes affichent encore ces travaux
pendant l’enregistrement de leur progression ou la publication d’un index.
Les autres préparations indépendantes gardent les commandes de leur carte ou de
leur page d’origine.
Une question finit sa réponse en cours, et les travaux découpés s’arrêtent
entre deux unités enregistrées. Le téléchargement YouTube en cours reçoit
une demande d’arrêt et conserve son fichier partiel. **Reprendre la file**
libère le prochain créneau. Les traitements interrompus par le mode jeu
gardent leurs propres commandes de reprise, après redémarrage volontaire
du moteur.

Une tâche en erreur libère le créneau. Le signe **!** apparaît sur l’icône,
et l’aperçu en indique le titre et le motif lorsque le service les fournit.
Les erreurs sont placées en tête de la page, avec **Réessayer** ou un accès
au travail d’origine. Les travaux en pause, interrompus ou incomplets sont
dans **À reprendre**. La pause générale laisse les erreurs visibles.

Si la connexion au suivi est coupée, l’aperçu et la page signalent le dernier
état connu. Les commandes de la file redeviennent disponibles après
actualisation. L’assistant continue à suivre la réponse en cours dès que la
connexion revient. Un envoi qui reste sans confirmation conserve le texte
dans la zone de saisie. Les lecteurs de documents, les synthèses et les préparations
de pistes indiquent aussi si un travail attend son tour ou la reprise de la file.

Quand le créneau IA est occupé, **Ajouter à la file d’attente** lance ou remet
dans la file une traduction depuis son document ou sa conversation. La reprise
conserve les passages terminés et utilise le modèle choisi pour la suite.
Un profil peut suivre plusieurs traductions dans des conversations distinctes.

Une reprise vidéo conserve les fichiers et
pistes déjà publiés. La pause globale et les étapes de la chaîne YouTube
sont conservées sur le disque. Après un redémarrage, les questions et les
traductions ordinaires suivent les règles de reprise de leur page.

Voir [les préparations de la bibliothèque et leur suivi](preparations-bibliotheque.md)
pour savoir où suivre chaque travail et ce que la file reçoit du PC serveur.

La priorité s’applique aux traitements du portail. Une réponse envoyée
depuis l’interface avancée Open WebUI a son propre traitement.

Pour les outils utilisés et les cas où YouTube refuse un fichier ou une
piste, voir [Télécharger une liste de vidéos YouTube](telecharger-videos-youtube.md).
