# Refonte UX évolutive

**Référence de conception — 0.34.0, 16 novembre 2026.** Louis autorise les changements de parcours,
la conception visuelle et une livraison autonome. Il demande une attention égale
au PC et au téléphone, des titres concrets, une aide courte et contextuelle,
la traduction dans le lecteur et un retour à la version précédente. Une seule
interface doit être active ; aucune double interface n’est nécessaire au retour.

## Direction et limites

Conserver nom et logo feu/livre ; choisir les changements visuels selon l’utilité.
Les cinq destinations restent Accueil, Bibliothèque, Assistant, Cartes, Appareil.
Sur PC, privilégier le travail côte à côte et les claviers à 1024, 1366, 1440 et
1920 px ; sur téléphone, une seule zone à la fois à 320/390 px. Une largeur de
lecture bornée reste nécessaire sur grand écran. Safari physique reste distinct.

La traduction se prépare et se lit dans le lecteur, avec original, pages,
comparaison et travaux persistants. Les synthèses, illustrations et sous-titres
s’intègrent aux contenus concernés. Toutes les capacités actuelles sont conservées,
notamment exports, pauses, reprises explicites, limites, publication et avertissements.
L’assistant comporte conversations à gauche, discussion au centre et documents à
droite sur PC ; les volets se replient. Les modes et les tâches restent distincts.

Pas de nouvelle inférence ni téléchargement lourd pour la recette du runner.
Pas de réécriture du moteur pour obtenir une disposition. Le catalogue de modèles
et la restauration complète sur PC vierge restent des travaux distincts.

## Lots et état réel

| Lot | État et critères de sortie |
| --- | --- |
| Référence et retour | Référence finale 0.33.1 avec vidéos et correctif de recherche et référence initiale 0.32.1 archivées ; retour avec sauvegarde des données récentes testé sur fixtures et base SQLite réelle, pas sur les PC physiques |
| Fondations | Implémentées : aides facultatives, variables CSS, titres concrets, lecture prioritaire, navigation au clavier |
| Lecteurs | Implémentés : traduction dans le lecteur portail et PDF dédié, travaux retrouvés par original, comparaison, pages, commandes et exports préservés |
| Assistant | Implémenté : trois zones repliables, dossiers personnels, déplacement, recherche et renommage ; tâches distinctes du temps de réponse |
| Cohérence complète | Implémentée : reprise à l’accueil, travaux personnels, destinations et composants communs ; fonctions vidéo, cartes et paramètres conservées |
| Livraison générale | Recette et inventaire dans le [bilan final](../essais/2026-11-16-refonte-ux.md) ; suivi de l’intégration et limites physiques explicites |

Ces états ne certifient pas la simplicité réelle pour Marc. Une recette humaine
reste préparée séparément, sans conditionner la livraison technique autonome.

## Extension des fonctions

**Consigne durable de Louis — 16 novembre 2026 :** conserver cette rigueur dans
les prochains choix de design. Chaque ajout garde des commandes compréhensibles,
une lecture confortable, une destination cohérente et des états visibles. Le
suivi doit distinguer travail en cours, résultat provisoire, fin et erreur. Une
nouvelle capacité ne justifie pas à elle seule un nouvel écran ou une nouvelle
commande permanente ; partir de l’usage et des composants déjà présents.

`portal/nouveau/ui.js` fournit les primitives communes ;
`ux-system.css` et les styles de composants portent leurs règles.
`ux-system.js` gère les adaptations et repères personnels. `SurvieUI.help(libellé, texte)` produit une aide
facultative, accessible au survol, au clic, au clavier et à Échap. Les conséquences
importantes d’une action restent écrites directement dans son parcours.
Les composants n’appellent pas les moteurs et ne lancent aucune opération.

Toute nouvelle fonction précise sa destination, ses commandes, ses états,
son aide et sa recette. Utiliser les composants existants avant d’en ajouter.
Les modules partagent l’identifiant et l’état serveur d’un même travail.
Les sélecteurs ne doivent pas dépendre du texte visible. Les pages générées restent
produites par `scripts/build_next_portal.py`, jamais modifiées isolément.

## Coordination du chantier parallèle

Branche interface : `codex/refonte-ux`, worktree séparé. L’autre chantier porte sur
le moteur et les vidéos/sous-titres. Ne pas modifier son worktree.
Les fichiers communs comprennent le générateur HTML, `pilot/app.py`, les lecteurs
et les clés de cache. Réconcilier leurs modifications puis intégrer successivement
sur main, avec tests après chaque intégration. Le lot vidéo 0.33.0 (`3dd2409`)
a été intégré avant l’UX. La refonte porte donc la version **0.34.0** : une
évolution fonctionnelle significative, avec API et données existantes compatibles.
Aucune version ni empreinte d’image tierce n’a changé.

Le correctif de recherche 0.33.1 (`fafc21e`) a ensuite été repris. Le paquet de
retour recommandé est donc la **0.33.1**, qui conserve aussi les ajouts vidéo.
La 0.32.1 reste la référence historique précédant les deux chantiers. Consulter
la [procédure de retour](../exploitation/retour-version-avant-refonte.md).

## Méthode et références

- [Divulgation progressive, NN/G](https://www.nngroup.com/articles/progressive-disclosure/) : fréquence, regroupement et découverte des options ; ne pas tout enfermer dans des accordéons.
- [Accessibilité cognitive, W3C](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o1-understandable/) : titres, commandes et relations explicites.
- [Human–AI Interaction, CHI 2019](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf) : compréhension, contrôle et correction.
- [GOV.UK, composants](https://design-system.service.gov.uk/community/contribution-criteria/) : composants cohérents, réutilisables et éprouvés.
- [GOV.UK, essais utilisateurs](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) : tâches sans indice, réussite, erreurs et hésitations.
- Skills consultés : [Frontend Design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) et [Web Design Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines), adaptés au français et au hors ligne.

Comparer les mêmes tâches et contenus avant/après. Séparer interaction, recherche
et inférence. Aucun score de clics ou audit automatique ne certifie à lui seul la
facilité d’usage. Les preuves datées indiquent version, environnement et limites.


## Retours visuels et reprise de la base — 0.36.0

Les captures de Louis après la 0.34.0 montrent des aides disproportionnées,
une case mal alignée, une navigation des volets redondante et une finition
insuffisante des autres pages. Le retour invalide l’idée que les tests techniques
suffisaient à déclarer le résultat visuel terminé. La reprise nettoie la couche
maquette, unifie les cartes et clarifie les responsabilités CSS/JS ; voir la
[référence des composants](../architecture/composants-interface.md).
La revue visuelle sur pages remplies fait désormais partie de la recette.
