# Retour d’expérience de Marc : trouver un savoir utilisable

**Compte rendu du 14 novembre 2026 — appel rapporté par Louis.** Notes utilisateur,
analyse du code et propositions ; aucune nouvelle recette sur le PC de Marc.
Les cinq captures sont consultées sans les recopier dans Git. L’une affiche
explicitement 0.1.34 ; les autres gardent l’ancienne présentation. Elles ne
prouvent pas que la 0.1.35 a été installée. Aucun changement fonctionnel livré ici.

**Suite :** Louis a demandé la mise en œuvre de ce chantier. La première
consolidation est décrite dans le [bilan 0.1.36](2026-11-14-moteur-recherche-utile.md),
avec un [suivi des points encore ouverts](../decisions/fiabilisation-recherche-et-contenus.md).
Les observations et propositions ci-dessous conservent leur contexte initial.

## Retour à conserver

| Sujet | Observation rapportée ou visible | Besoin |
| --- | --- | --- |
| Utilité pratique | Dans Appropedia, « générateur à pédales » mène à de l’histoire et des informations générales, pas au guide de fabrication attendu | Distinguer présentation, explication et véritable procédure de construction ; montrer matériel, étapes, schémas et limites lorsqu’ils existent |
| Profondeur | Les sujets ne permettent pas assez souvent de passer à l’action | Qualifier les documents utiles au lieu de confondre volume téléchargé et savoir-faire accessible |
| Collections | Plusieurs cartes Canadian Prepper portent le même nom, et le problème se retrouve ailleurs | Regrouper par source avec sous-collections explicites et conserver l’ouverture directe |
| Vidéo | Des vidéos intéressantes sont en anglais ; Marc ne parle pas anglais | Sous-titres français disponibles hors ligne, avec provenance et état de traduction |
| Traduction de lecture | Demande d’une commande en haut, comparable à Firefox | Traduire la page consultée et revenir à l’original sans dépendre d’Internet |
| Recherche documentaire | « faire du feu » retourne notamment risques d’incendie dans le Var, métallurgie et botanique ; « allumer un feu » affiche zéro résultat | Retrouver l’intention et classer les passages réellement utiles avant les mentions incidentes |
| Faux positif observé | PDF botanique, page 229/325 : proposition de quiz « utiliser sa sève comme allume feu » | Une option de quiz n’est ni un conseil validé ni une procédure ; son contexte doit apparaître |
| Parcours | L’appellation et ce qu’elle apporte ne sont pas compris | Une entrée par besoin concret avec résultat attendu et ressources réellement présentes |
| Assistant rapide | Environ quatre minutes rapportées pour conclure à l’absence de document et répondre en principes généraux | Délai visible, recherche fiable et explication des manques |
| Relance Wikipédia | L’assistant affirme n’avoir rien trouvé en français ni en anglais et va jusqu’à nier une page dédiée | Une recherche vide ne doit pas devenir une affirmation d’absence ; cibler réellement la collection demandée |
| Contexte | La relance en approfondi s’arrête avec « Cette recherche dépasse le contexte prévu » | Conserver la question utile et des extraits bornés, sans transformer une question simple en impasse |
| Lecteur | Le modèle de dossier familial affiche des marqueurs Markdown bruts (#, tableau avec barres) | Rendre le document lisible et annoncer clairement qu’il s’agit d’un modèle vierge |

La capture de dossier familial est une vue de recherche/lecture ; aucune des
captures ne montre clairement l’écran Parcours. L’incompréhension de Parcours
est rapportée par Louis, sans attribuer à cet écran les captures des autres vues.

## Ce que le code actuel explique et ne prouve pas

La recherche documentaire n’appelle pas de LLM. Elle combine SQLite FTS pour les
guides et la recherche Kiwix pour les archives. Depuis 0.1.35, les échecs Kiwix
sont isolés et signalés ; cela corrige l’accès mais ne garantit pas la pertinence.
Le classement commun privilégie surtout le titre exactement égal à la requête,
puis alterne guides et articles. Les mots de la question sont simplifiés ; les
recherches peuvent rester trop restrictives à plusieurs mots et trop larges sur
un seul. Ce n’est pas encore un classement par intention pratique.

Dans l’assistant, tous les profils disposent des mêmes outils. Le modèle décide
quand appeler `search_library`, avec quels mots et quelle langue, puis quels
résultats lire avec `read_source`. La stratégie peut donc varier entre modèles
et entre réponses. Le serveur exécute toujours le même moteur documentaire.
Ajouter « Wikipédia » aux mots de la requête n’équivaut pas à sélectionner la
collection Wikipédia ; le ciblage explicite doit être prévu dans l’outil.
Les modes rapide et approfondi recommandés utilisent tous deux GPT-OSS 20B,
avec une réflexion respectivement faible et élevée ; « rapide » n’est pas une
promesse de délai ni nécessairement un modèle plus petit.

Les appels et métriques du moteur sont conservés dans les traces privées quand
leur écriture réussit. Aucun de ces diagnostics de Marc n’a été lu ici. Les
quatre minutes peuvent inclure file d’attente, chargement, inférence, appels
successifs et lectures : leur répartition n’est pas déductible d’une capture.
La boucle actuelle peut faire sept appels au modèle, dont six avec outils ;
l’historique retenu est borné à 7 000 caractères et un garde-fou sur les messages
sérialisés à 24 000 octets peut interrompre la réponse. Ce n’est pas une preuve
que le modèle a lu la bibliothèque ou qu’un livre est trop long pour la traduction.

La page publique [Techniques de production de feu](https://fr.wikipedia.org/wiki/Techniques_de_production_de_feu)
existe et comporte notamment friction et percussion (consultation Web du 14 novembre).
Cela contredit une absence affirmée de page sur le Wikipédia actuel ; la présence
et le chemin exacts dans l’édition ZIM locale restent à vérifier par ouverture.
Même une archive dite complète peut différer du site actuel et de son édition.

## Priorité proposée : un moteur commun, mesuré sur des besoins réels

**Proposition technique, à réaliser et à mesurer ; aucune nouvelle garantie de
résultat, vitesse ou couverture documentaire.**

1. Constituer une recette de questions de Marc et repérer manuellement les sources
   pertinentes dans son fonds. Inclure feu, eau, abri, générateur à pédales,
   réparation et alimentation, avec variantes naturelles, fautes usuelles et relances.
   Séparer document absent, non indexé, recherche en panne et résultat mal classé.
2. Combiner titres et redirections, plein texte, vocabulaire technique FR/EN et
   reformulations bornées. Conserver les verbes utiles : allumer, fabriquer et
   éteindre ne désignent pas le même besoin. Rechercher plusieurs formulations
   sans imposer tous leurs mots à chaque document. Interroger les titres Kiwix
   en complément : l’API [suggest](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html#suggest)
   existe, mais est privée et doit être vérifiée avec la version épinglée.
3. Fusionner et classer les candidats en privilégiant titre pertinent, expression,
   proximité des mots et contenu du passage. Ne pas comparer directement des
   scores bruts de moteurs différents ; tester une fusion par rangs. Regrouper
   les pages d’un même ouvrage et montrer le meilleur passage avec sa page.
   Une mention de quiz ou un règlement incendie ne doit pas devancer une
   procédure disponible pour la requête « faire du feu ». Ne pas masquer ces
   sources lorsqu’on cherche précisément botanique ou prévention.
4. Exposer langue, collection, type de contenu et extrait qui explique la correspondance.
   Les étiquettes « tutoriel » ou « guide pratique » ne doivent pas être déduites
   du seul mot survie ou du nom d’une chaîne. Signaler les manques de procédure.
5. Fournir la même recherche à la bibliothèque et à l’assistant, avec filtre de
   collection explicite. Pour les demandes documentaires simples, préparer les
   candidats avant une longue boucle de décision du LLM ; conserver la liberté
   d’affiner ensuite. Ne pas imposer une recherche aux calculs ou échanges qui
   n’en demandent pas. Une relance « dans Wikipédia ? » doit reprendre le sujet
   précédent et cibler la collection, sans rechercher ces seuls mots.
6. Évaluer une recherche sémantique multilingue en complément seulement après
   cette référence mesurée. Elle demande un index des passages préparé à l’avance ;
   charger le modèle conversationnel en RAM ne lui donne pas accès à 755 Go.
   L’IA générative peut proposer des variantes ou reclasser un petit lot, mais
   le socle doit fonctionner moteur arrêté. Évaluer coût d’indexation, espace,
   reprise, qualité et délai sur un fonds représentatif avant généralisation.
7. Mesurer séparément attente, chargement, recherche, lecture et rédaction, à froid
   et à chaud, sur Windows chez Marc. Réduire les boucles inutiles et sélectionner
   les extraits pertinents plutôt que remplir le contexte puis demander au lecteur
   de reformuler. La mémoire GPU/RAM et les processus réels doivent être observés,
   sans benchmark ni démarrage forcé pendant une pause du moteur.

Critères proposés : une source pertinente réellement présente apparaît parmi
les cinq premiers résultats ; aucun quiz accessoire n’occupe la tête du cas feu
si un article pertinent est disponible ; les variantes proches retrouvent les
mêmes sources ; l’assistant reçoit ces sources et ne nie pas leur existence.
Mesurer aussi les cas négatifs, le temps et les sources utiles manquantes, pour
éviter une amélioration limitée à une liste de mots sur le feu. Les seuils de
latence seront fixés après une mesure de référence, pas annoncés comme atteints.

## Organisation, profondeur et langue

Regrouper les collections par éditeur/chaîne, puis sujet, langue et édition.
Par exemple « Canadian Prepper » donne accès à plusieurs sous-collections,
avec titres compréhensibles tirés des métadonnées vérifiées, compte de vidéos
si disponible et ouverture directe de chaque ensemble. Ne pas renommer ou
fusionner physiquement les fichiers, perdre leurs liens, ou déclarer des doublons
sur leur titre seul. Appliquer cette logique à toutes les sources concernées.

Étudier le remplacement de « Parcours » par « Apprendre par thème » ou « Savoir-faire ».
Le contenu doit guider vers un objectif (« construire un générateur à pédales »),
avec prérequis, documents, étapes et lacunes constatées. Un article historique
reste une ressource de contexte, sans être présenté comme un plan de fabrication.
Sélectionner et relire les procédures, les schémas et les nomenclatures réellement
présents avant de compléter le fonds. La première priorité reste de retrouver
les contenus existants, puis de combler les lacunes confirmées.

Pour les vidéos, inventorier d’abord les pistes locales VTT/SRT et les langues,
ainsi que les possibilités du lecteur ZIM. Si nécessaire, préparer séparément
transcription puis traduction synchronisée et les conserver localement, avec
statut humain/automatique et langue. Un bouton de traduction de page ne sous-titre
pas la voix d’une vidéo. Ni la présence des pistes dans les archives de Marc ni
la fidélité d’une transcription ne sont établies par ces captures.

Pour les pages, prévoir une commande visible « Lire en français / Voir l’original »,
avec traduction locale conservée et traitement explicite des erreurs. L’intégration
aux lecteurs Kiwix/PDF doit être étudiée, sans présumer qu’un bouton du portail
peut modifier chaque lecteur. Distinguer lecture traduite et traduction longue
publiée ; préserver l’original et indiquer les passages non traduits.

[Mozilla](https://support.mozilla.org/en-US/kb/website-translation) indique que
Firefox peut traduire le texte pris en charge hors ligne après installation
complète des fichiers linguistiques. C’est une possibilité immédiate à préparer
et tester sur l’appareil utilisé, pas une fonction garantie du portail, ni une
traduction de vidéo, d’image ou de PDF scanné. Une recette Internet coupé reste
nécessaire. Le portail doit rester utilisable avec les autres navigateurs.

## Réponse sur les livres longs

Voir les [limites actuelles de traduction](../utilisation/documents-et-traduction.md#taille-des-documents-et-livres-longs).
La traduction dédiée découpe les pages en passages d’environ 2 200 caractères,
enregistre leur progression et permet une reprise explicite. Un PDF de 500 pages
peut être accepté s’il respecte les limites et possède du texte extractible ;
aucune traduction réelle de 500 pages n’est validée ici. La durée peut être longue,
les images ne sont pas traduites et la cohérence technique entre passages reste
à contrôler. Ce n’est pas le traitement d’un livre entier dans un seul contexte IA.

## Idée reportée

Louis demande explicitement de garder pour plus tard un espace **Maison de
Solliès-Ville** : équipements, notices associées, entretien et éventuellement
stocks. L’idée est enregistrée dans la [boîte à idées](../decisions/boite-a-idees.md),
sans inventer un inventaire ni ajouter dès maintenant un onglet vide.
