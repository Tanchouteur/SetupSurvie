# Faire une synthèse des documents

**Guide 0.18.0 — 15 novembre 2026.** Les essais simulés et les essais avec un
modèle réel sont distincts. Le [bilan](../essais/2026-11-15-synthese-multi-sources-et-essais-reels.md)
précise leurs résultats ; le corpus fictif ne valide pas celui de Marc.

Depuis 0.17.0, on peut aussi choisir les documents à comparer dans la Bibliothèque
avec **Choisir pour l’assistant**. Leur sélection est enregistrée avant l’envoi ;
le [guide documentaire](documents-et-traduction.md#choisir-les-documents-dune-conversation--0170)
explique la reprise et la traduction séparée de chaque source.

Dans **Assistant**, décrire le sujet, puis le résultat attendu, par exemple :
« Fais une synthèse des documents sur la production de feu. Compare les méthodes
et cite les sources. » Sans sélection explicite, le logiciel prépare une recherche
documentaire avant le premier appel du modèle. Avec une sélection, il commence
par les passages des documents choisis et peut chercher un complément utile. La question complète reste transmise au modèle ; une
consigne secondaire ne devient plus obligatoirement un mot à trouver dans le texte.

La préparation peut examiner jusqu’à douze résultats. Elle privilégie des documents
distincts et plusieurs collections, puis sélectionne des passages liés au sujet,
y compris loin du début. Un livre et plusieurs de ses pages ne sont pas présentés
comme autant de livres différents. Les textes identiques sont écartés du dossier.
Une source illisible ne bloque pas les autres. Pour un PDF entier sélectionné,
une page indexée correspondant au sujet peut remplacer le simple aperçu de début ;
son numéro et son lien restent conservés. Le nombre réellement transmis
dépend des documents disponibles, du contexte, de l’historique et de la longueur
des références : cinq est possible, pas une limite fixe ni une garantie par question.

Le modèle peut compléter le dossier avec **read_sources**, ou lire une suite avec
**read_source**. Les positions renvoient au texte extrait d’origine ; les PDF gardent
leurs liens de page. Un aperçu ou une extraction tronquée reste signalé. Charger
un fichier, fournir un passage et comprendre tout le livre sont trois choses
différentes. Les images du document ne sont pas encore interprétées par ce parcours.

Le premier tour documentaire propose les outils de recherche, lecture et calcul ;
les outils géographiques restent proposés pour une question spatiale et aux tours
suivants. Deux tours documentaires sans source ni passage nouveau conduisent à la
rédaction avec les éléments disponibles. Le plafond reste trois tours d’outils en
réponse rapide et six ailleurs ; une étape de liaison des références peut s’y ajouter.

Pour une demande explicite de synthèse, les numéros cités doivent correspondre à
des sources consultées. Si ce contrôle de format échoue, une étape séparée peut
relier les fragments de la réponse aux numéros des sources lues. Elle ajoute
uniquement des références, sans réécrire les faits. Les identifiants de fragments
et de sources sont contrôlés par le serveur. Cela ne vérifie pas que chaque
affirmation est vraie ou bien soutenue par la source : relire les documents et
leurs désaccords reste nécessaire.

Cette petite étape conserve le modèle choisi et réduit sa réflexion : désactivée
si le modèle accepte ce réglage, ou niveau `low` pour les profils à niveaux.
La rédaction de la réponse garde le réglage du mode demandé. Le but est d’éviter
que la seule mise en références épuise toute sa sortie avant de fournir le JSON.

Si cette étape échoue, le texte utile reste affiché avec « Références à vérifier »
et un état incomplet. Une réponse citant une source inconnue est remplacée par
les extraits consultés. Les traductions IA gardent leur avertissement et leur original.

Une panne du modèle ou un dépassement de temps conserve les extraits disponibles
et le texte déjà reçu dans la conversation, avec l’état d’échec. Une annulation
conserve seulement le texte déjà reçu, marqué comme interrompu ; sans texte,
elle n’invente pas de nouveau message. **Voir les durées** distingue sources
trouvées/lues, documents préparés, liaisons ajoutées aux sources et temps de liaison.
L’export numérique conserve aussi l’arrêt des répétitions.
Les textes de propositions refusées restent dans les traces privées, jamais dans
l’export numérique des mesures ; aucun raisonnement privé n’est enregistré.

La préparation et les outils de recherche disposent du budget documentaire long
de 60 secondes, comme le flux du portail. Le nombre de lectures simultanées est
limité à trois. Les fichiers déjà chargés sont réutilisés pour la demande ; une
demande différente conserve les contrôles de disponibilité du moteur documentaire.
Ce budget n’est pas une promesse de durée globale : le chargement et la génération
du modèle s’y ajoutent, dans le plafond de quinze minutes de la conversation.

**Restent à développer ou qualifier :** illustrations, fidélité des longues
synthèses et choix des modèles sur des essais représentatifs. La sélection
manuelle multiple est maintenant disponible. Voir le [programme retenu](../decisions/assistant-recherche-et-synthese.md).

## Lire un livre entier par étapes — 0.18.0

Dans la Bibliothèque, choisissez vos documents pour l’assistant. Dans **Assistant**,
écrivez ce que vous voulez en retenir, ouvrez **Lire les documents et préparer une
synthèse**, puis cliquez sur **Préparer une synthèse longue**. Sans question saisie,
le logiciel prépare une synthèse des informations utiles. Le mode choisi dans
le champ habituel détermine le modèle utilisé.

Une nouvelle conversation conserve ce travail et une copie de la sélection.
Un PDF entier est lu sur toutes ses pages contenant du texte extractible ;
une référence à une page précise reste limitée à cette page. Le parcours rapide
habituel conserve sa lecture par passages liés au sujet. Les aperçus d’articles
tronqués sont refusés pour la lecture complète, plutôt que présentés comme des
livres entièrement lus.

Le suivi indique la préparation des textes, les passages examinés, l’attente du
moteur puis le regroupement et la rédaction. **Mettre en pause** conserve les
étapes terminées ; **Reprendre avec le modèle choisi** poursuit les étapes restantes.
Fermer le navigateur laisse le travail continuer. Après un redémarrage du service
ou une mise en pause du moteur, la reprise est explicite. Aucun modèle n’est
redémarré de force. On peut ouvrir une autre conversation pendant ce travail ;
les étapes longues partagent la file du moteur avec les réponses ordinaires.

Les notes intermédiaires conservent leur extrait d’origine, page et position.
Les regroupements désignent les notes précises dont ils proviennent. Le bouton
**Télécharger la synthèse et les notes** permet aussi de récupérer le travail
inachevé. La rédaction conserve les sources et les éditions connues ; une
liaison séparée peut ajouter des numéros de référence sans réécrire la réponse.
Si elle échoue, le brouillon reste exportable avec l’état **Références à vérifier**.

Les textes préparés ne sont pas relus depuis une version modifiée lors de la
reprise. Un document initialement indisponible peut être réessayé. Les documents
indisponibles et pages sans texte extractible restent signalés, y compris dans
la réponse finale ; aucune analyse d’image ni OCR n’est effectuée. Les instantanés,
notes et exports restent rangés dans le profil, sans publication dans la bibliothèque
partagée. Les profils locaux ne sont pas des comptes protégés par mot de passe.
Supprimer cette conversation après sa pause supprime aussi ses travaux de synthèse,
sans supprimer les documents originaux.

La préparation accepte douze références au maximum, jusqu’à 1 200 pages par PDF,
300 Mo par PDF, cinq millions de caractères par document et vingt millions pour
le dossier. Chaque étape reçoit un volume borné par le contexte du modèle ;
elle peut échouer et être reprise sans perdre les étapes précédentes. Un livre
textuel de 500 pages entre généralement dans ces plafonds, mais sa fidélité,
son temps de traitement et ses tableaux ne sont pas validés par cette seule taille.

**Passage examiné ne signifie pas fait compris ou conservé.** Le modèle sélectionne
et compresse les informations ; il peut encore omettre un fait ou produire une
conclusion injustifiée. Les contrôles portent sur l’existence des extraits et des
références, pas sur la vérité de chaque phrase. Le [bilan 0.18.0](../essais/2026-11-15-syntheses-longues-et-reprise.md)
distingue les petites fixtures des essais sur modèle réel ; le fonds de Marc et
un vrai livre de 500 pages restent à éprouver.
