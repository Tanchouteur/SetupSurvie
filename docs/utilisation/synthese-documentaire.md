# Faire une synthèse des documents

**Guide — préparation de la 0.16.0, 15 novembre 2026.** Les essais simulés et les
premiers essais avec un modèle réel sont distincts. La livraison et les résultats
finaux sont consignés dans le bilan ; le corpus fictif ne valide pas celui de Marc.

Dans **Assistant**, décrire le sujet, puis le résultat attendu, par exemple :
« Fais une synthèse des documents sur la production de feu. Compare les méthodes
et cite les sources. » Le logiciel prépare une recherche documentaire avant le
premier appel du modèle. La question complète reste transmise au modèle ; une
consigne secondaire ne devient plus obligatoirement un mot à trouver dans le texte.

La préparation peut examiner jusqu’à douze résultats. Elle privilégie des documents
distincts et plusieurs collections, puis sélectionne des passages liés au sujet,
y compris loin du début. Un livre et plusieurs de ses pages ne sont pas présentés
comme autant de livres différents. Les textes identiques sont écartés du dossier.
Une source illisible ne bloque pas les autres. Le nombre réellement transmis
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
réponse rapide et six ailleurs ; une reprise finale de références peut s’y ajouter.

Pour une demande explicite de synthèse, les numéros cités doivent correspondre à
des sources consultées. Si ce contrôle de format échoue, une seule reprise finale
est demandée au modèle. Un second échec affiche les extraits consultés avec un
avertissement, plutôt qu’une synthèse présentée comme aboutie. Ce contrôle ne
vérifie pas le sens des affirmations : relire les sources et leurs désaccords
reste nécessaire. Les traductions IA conservent leur avertissement et leur original.

Une panne du modèle ou un dépassement de temps conserve les extraits disponibles
et le texte déjà reçu dans la conversation, avec l’état d’échec. Une annulation
volontaire n’invente pas de nouveau message. **Voir les durées** distingue sources
trouvées/lues, dossier préparé, reprise de citations et arrêt des répétitions.
Les textes de propositions refusées restent dans les traces privées, jamais dans
l’export numérique des mesures ; aucun raisonnement privé n’est enregistré.

La préparation et les outils de recherche disposent du budget documentaire long
de 60 secondes, comme le flux du portail. Le nombre de lectures simultanées est
limité à trois. Les fichiers déjà chargés sont réutilisés pour la demande ; une
demande différente conserve les contrôles de disponibilité du moteur documentaire.
Ce budget n’est pas une promesse de durée globale : le chargement et la génération
du modèle s’y ajoutent, dans le plafond de quinze minutes de la conversation.

**Restent à développer :** sélection manuelle de plusieurs documents associés,
synthèses intermédiaires pour de longs livres, illustrations et choix des modèles
sur des essais représentatifs. Le bandeau d’association manuelle conserve pour
l’instant un document. Voir le [programme retenu](../decisions/assistant-recherche-et-synthese.md).
