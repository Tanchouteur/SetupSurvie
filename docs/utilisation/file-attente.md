# Suivre les travaux de SetupSurvie

**Guide actuel — 0.52.1.**

Dans la barre de navigation du portail, l’icône de la file indique le nombre
de tâches visibles en cours ou en attente. Sur ordinateur, survolez l’icône
ou atteignez-la avec la touche Tab pour voir les prochaines tâches. Ouvrez
la page de la file en cliquant dessus ou en appuyant sur Entrée. Sur
téléphone, l’icône ouvre directement la page.

La page indique le contenu, l’étape, le modèle sélectionné et l’avancement
quand le traitement sait le mesurer. Les flèches changent l’ordre des travaux
qui attendent un créneau. Les réponses et les traductions de documents
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
  l’indexation des vidéos. Whisper utilise jusqu’à quatre fils de calcul pour
  laisser de la capacité au reste du portail. Une traduction des sous-titres rejoint le créneau IA
  lorsque la piste source est disponible.

**Ensuite** désigne le prochain travail prévu dans chaque créneau. Une nouvelle
question peut changer ce choix pour l’IA. Les flèches règlent l’ordre au sein
d’un même créneau et d’un même niveau de priorité.

Avec **Famille**, **Mettre en pause** empêche le démarrage des étapes suivantes de la file. L’indexation des fichiers déjà publiés peut se terminer en arrière-plan.
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

Une reprise vidéo conserve les fichiers et
pistes déjà publiés. La pause globale et les étapes de la chaîne YouTube
sont conservées sur le disque. Après un redémarrage, les questions et les
traductions ordinaires suivent les règles de reprise de leur page.

La priorité s’applique aux traitements du portail. Une réponse envoyée
depuis l’interface avancée Open WebUI a son propre traitement.

Pour les outils utilisés et les cas où YouTube refuse un fichier ou une
piste, voir [Télécharger une liste de vidéos YouTube](telecharger-videos-youtube.md).
