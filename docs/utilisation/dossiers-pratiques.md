# Organiser les documents autour d’un objectif pratique

**Guide actuel — 0.9.0, 14 novembre 2026.** Dans **Bibliothèque → Apprendre par
thème**, six dossiers organisent la lecture : allumage du feu, traitement de l’eau,
projet d’abri, générateur à pédales, crevaison de vélo et conservation des graines.
Les autres thèmes et niveaux pédagogiques restent disponibles sous ces dossiers.

## Chercher puis examiner

Choisir un objectif affiche les points à documenter : prérequis et limites,
matériel, plans ou schémas si nécessaires, étapes, contrôles, entretien ou
conservation. Le dossier commence avec ces questions et ses lacunes explicites.
La présence d’un livre ou d’une encyclopédie n’est pas présumée.
Sur téléphone, un sélecteur compact permet de choisir l’objectif ; les six cartes
restent visibles sur ordinateur.

**Chercher des sources pour ce dossier** lance deux demandes complémentaires dans
Autonomie et résilience, avec le moteur documentaire habituel et ses limites.
Les douze résultats au maximum sont à ouvrir et examiner. Le type corrigé d’une
source est affiché lorsqu’il existe ; un titre prometteur ne devient pas une
procédure vérifiée. Une recherche partielle garde les autres résultats et son
avertissement. Ouvrir simplement le dossier ne lance pas ces recherches.

**Rechercher avec mes mots** ouvre la recherche ordinaire. Pour élargir au fonds
non classé, choisir **Toute la bibliothèque**. L’accès direct par Collections,
les filtres et les documents d’origine restent disponibles.

Le dossier est inscrit dans l’adresse, par exemple
`/#/bibliotheque/parcours?dossier=generateur-pedales`. Actualiser, revenir en arrière
ou avancer avec le navigateur conserve cet objectif. Le lien d’un document garde
aussi le dossier dont il provient.

## Conserver un repère après lecture

Depuis **Famille**, ouvrir un document dans le lecteur du portail, puis déplier
**Relier ce document à un dossier pratique**.

1. Choisir le dossier et cocher les points effectivement présents dans le passage
   examiné. Une présentation générale peut éclairer un principe sans documenter
   le matériel ou les étapes de fabrication.
2. Indiquer la page ou section précise, puis un bref repère sur son contenu et ses
   limites. Ce texte est une note humaine, pas une réponse générée par l’assistant.
   Conserver les images et la mise en page en consultant l’original lorsque nécessaire.
3. Confirmer la lecture du passage dans l’original, puis **Enregistrer le repère**.
   Le serveur vérifie à nouveau l’accès à cette source et la révision de son fichier.
   Si le dossier a été modifié dans un autre onglet, recharger avant d’enregistrer.
4. **Ouvrir le dossier** montre la référence dans les points cochés. Chaque point
   sans référence examinée conserve sa prochaine action : chercher une source,
   l’ouvrir et relever où se trouve l’information. Un plan peut ne pas s’appliquer
   au projet : le préciser avec la source qui justifie ce choix.

Les repères sont communs à tous les profils du réseau. Éviter les données
personnelles dans les notes. Leur présence et le compteur ne valident pas la
sécurité, l’actualité, le sens ni l’exhaustivité d’une méthode. La référence date
le document lorsque cette information existe ; collecte et date d’archive ne sont
pas assimilées à sa date de publication. Les traductions IA sont signalées.

Si le fichier change, les anciens repères sont rangés sous **Source modifiée :
ancien repère à revoir** et cessent de couvrir les points du dossier. S’il manque,
la source est signalée indisponible. Les notes sont conservées pour permettre la
reprise de la lecture. La détection utilise taille et date de modification, comme
le [classement documentaire](classement-et-collections.md) ; elle ne calcule pas
une nouvelle empreinte de centaines de Go à chaque ouverture. Une archive présente
sur disque peut encore rencontrer une panne du lecteur : le compteur ne garantit
pas son accès HTTP permanent.

**Retirer ce repère du dossier** retire cette seule association, sans supprimer
le document ou ses autres repères. La même source et la même localisation se
mettent à jour ; plusieurs pages ou sections peuvent avoir des notes distinctes.
La limite est de 24 repères par dossier, six points par repère, 700 caractères de
note et 200 pour la localisation. Elle ne plafonne pas la bibliothèque.

## Étudier avec l’assistant

**Préparer une question à l’assistant** remplit une demande liée à l’objectif et
aux références examinées. Elle demande de chercher et lire les sources, leurs
dates, les prérequis et limites, et d’adapter les explications et un exercice de
compréhension à l’âge et au niveau. La question reste à envoyer volontairement ;
aucune inférence n’est lancée en ouvrant le dossier ou en préparant ce texte.
Une réponse en cours doit être terminée ou annulée avant ce changement.

Le dossier reste consultable sans modèle chargé et sans Internet. Une préparation
à la réalisation doit encore tenir compte du matériel, des compétences et des
conditions réellement disponibles. Les besoins du [guide des savoirs durables](../bibliotheque/savoirs-durables.md)
et les [règles de fiabilité](sources-et-fiabilite.md) restent applicables.

## Export, sauvegarde et relecture du fonds

Famille → Mon appareil → Paramètres → Entretien et données → Conserver les classements et les dossiers pratiques → **Repères des dossiers pratiques → Exporter
les dossiers** conserve les objectifs, références, notes, dates et lacunes, sans
texte complet des originaux ni conversation. Le fichier peut contenir les notes
saisies par la famille. L’import n’est pas encore proposé.

Les repères sont dans `settings` de `state/pilot/pilot.db`, préfixe `dossier:v1:`.
La sauvegarde habituelle les conserve sans migration de schéma. Un dossier dont
les données sont illisibles signale le problème ; les autres dossiers, la recherche
et les collections restent accessibles. Préserver une sauvegarde avant réparation.

La structure et les commandes sont livrées ; les six dossiers ne contiennent pas
de procédures inventées ni de références supposées présentes chez Marc. La relecture
R3 doit remplir les points à partir de son fonds, qualifier les lacunes et permettre
ensuite une acquisition ciblée avec provenance et droits examinés. Les tests sur
documents fictifs ne réalisent pas cette relecture à sa place.
