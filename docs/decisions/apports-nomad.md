# Apports utiles de NOMAD pour SetupSurvie

**Décision et étude du 16 novembre 2026.** Louis conserve SetupSurvie comme base
et demande d'identifier les apports utiles de NOMAD. Le classement ci-dessous
est une recommandation technique, sans engagement de réalisation ni de délai.
Il complète les objectifs de simplification et de fiabilité des
[choix actuels](choix-actuels.md), sans les remplacer.

## Périmètre et preuves

Comparaison avec SetupSurvie 0.35.0, code et documentation au commit
`5c74170`, incluant la refonte UX. NOMAD a été relu via l'API GitHub au commit
[`c903da48c97bc02f5cdfeff2ebcde00a82dfec8e`](https://github.com/Crosstalk-Solutions/project-nomad/tree/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e),
daté du 9 novembre 2026. Sa documentation officielle et celle de Kolibri ont
également été consultées le 16 novembre. Aucun service NOMAD ou Kolibri n'a été
installé ou exécuté ; aucun corpus, modèle ou cours n'a été téléchargé.
La présence d'un parcours dans le code ne prouve pas sa qualité sur nos PC.

L'[étude d'octobre](../historique/comparaison-nomad-assemblage.md) reste une archive :
elle décrit un assemblage proposé avant les développements actuels. Elle ne
constitue plus la comparaison fonctionnelle de notre version présente.

## Classement proposé

| Piste | Apport observé chez NOMAD | Existant SetupSurvie | Recommandation et effort relatif |
| --- | --- | --- | --- |
| Préparation guidée et stockage | Assistant de première préparation, choix de services/contenus et projection du disque | Installation Windows, sélection par thèmes/langues, volumes, reprise, suivi et garde-fous déjà présents | **P1 : simplifier le parcours existant**, effort moyen ; nouveau catalogue de modèles à cadrer séparément |
| Contrôle des liens du catalogue | Vérification CI périodique des URL de collections | Intégrité des téléchargements, audits du fonds local et métadonnées ; aucun contrôle CI périodique des URL distantes identifié dans `tests.yml` | **P1 : préparer un contrôle de maintenance ciblé**, effort faible à moyen ; sans téléchargement lourd |
| Cours avec exercices et progression | Kolibri proposé comme service de la plateforme | Parcours de savoir-faire, documents éducatifs et aide IA ; pas de suivi scolaire structuré dans ces parcours | **P2 : qualifier un petit module Kolibri optionnel**, effort moyen pour l'essai, plus élevé pour intégrer les profils et le secours |
| Nouvelles éditions et mises à jour | Réglages séparés pour cœur, applications et contenus, fenêtres horaires et contrôles avant lancement | Mise à jour logicielle avec sauvegarde/retour, téléchargements reprenables et indexation planifiée | **P2 : étudier la visibilité des nouvelles éditions**, effort moyen ; conserver une application explicite |
| Applications et utilitaires complémentaires | Catalogue d'applications, notes, outils PDF, bibliothèque de livres et CyberChef | Lecteur PDF, favoris, dossiers pratiques, Open WebUI, calcul et conversion | **P3 : ajouter seulement sur besoin concret**, effort variable ; éviter les parcours et stockages en double |
| Documentation des API | Description OpenAPI produite à partir des routes et validateurs | FastAPI et API interne existants, interfaces de documentation désactivées dans `pilot/app.py` | **P3 : améliorer les contrats pour le développement**, effort faible à moyen ; aucun nouvel écran technique nécessaire pour la famille |

L'effort est une appréciation d'intégration, sans estimation de durée ni mesure
de performance. P1 signifie première piste recommandée après ou dans les
objectifs actuels ; aucun de ces lots n'est lancé par cette note.

## 1. Préparer sans se perdre

Reprendre le principe d'un parcours guidé, dans **Mon appareil → Bibliothèque
et préparations**, avec les composants de la
[refonte UX](inventaire-parcours-ux.md). Les [thèmes et langues](../bibliotheque/selection-kiwix-par-theme.md)
et le [fonds complet de Marc](../bibliotheque/bibliotheque-complete-marc.md)
existent déjà : ne pas créer un deuxième moteur de sélection.

La progression proposée est : choisir ses usages et langues, examiner la
sélection et son volume supplémentaire, vérifier le disque et les prérequis,
puis déclencher explicitement la préparation. Présenter les états distincts :
repéré, téléchargé et vérifié, ouvrable, indexé, essayé. Un téléchargement
terminé ne doit pas annoncer que tout fonctionne hors ligne.

La [demande de modèles à stocker](boite-a-idees.md) (IDEE-009) peut rejoindre ce
parcours : stock disque, modèle chargé et modes de réponse restent distincts.
Les estimations doivent compter fichiers déjà présents, marge de travail et
espace temporaire ; la seule barre de projection NOMAD ne prouve pas ces contrôles.
Conserver les limites physiques du laboratoire et l'absence de plafond
documentaire logiciel chez Marc.

**Critères avant livraison :** un novice sait ce qui sera ajouté et pourquoi ;
le retour dans la page ne démarre rien ; choix, interruptions et erreurs restent
compréhensibles ; pas de copie inutile ; navigation PC/téléphone et reprise
testées. Distinguer essais simulés, Windows réel et usage humain avec Marc.

Sources NOMAD : [assistant de préparation](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/app/controllers/easy_setup_controller.ts),
[projection disque](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/inertia/components/StorageProjectionBar.tsx),
[manifestes et cache](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/app/services/collection_manifest_service.ts).

## 2. Repérer les liens devenus indisponibles

NOMAD contrôle les URL de ses collections en CI, lors des changements et sur
un calendrier hebdomadaire, avec HEAD puis un repli GET borné pour certains
refus. Le principe peut compléter nos contrôles d'intégrité, qui interviennent
au téléchargement, et `scripts/audit_library.py`, consacré au fonds local.

Préparer un inventaire des URL publiques de nos catalogues figés, sans explorer
les données privées ni parcourir tout Internet. Limiter durée, concurrence,
volume reçu et redirections ; respecter une borne de lecture même si le serveur
ignore Range. Distinguer lien supprimé, refus de HEAD, limitation temporaire,
erreur réseau et vérification inconnue. Un HTTP 200 ne valide ni le bon document,
ni son édition, ni ses droits, ni son intégrité. Un échec temporaire ne doit
pas bloquer la consultation locale ni supprimer une référence.

**Critères avant livraison :** cas simulés 404, 405, 429, délai, redirection et
serveur ignorant Range ; aucun gros fichier reçu ; rapport daté avec taille et
édition inconnues conservées comme telles ; calendrier réseau séparé des tests
unitaires reproductibles. La vérification en ligne ne devient pas un prérequis
du portail hors ligne.

Source : [contrôle CI des URL](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/.github/workflows/validate-collection-urls.yml).

## 3. Essayer Kolibri pour l'enseignement

Kolibri est une brique indépendante que NOMAD distribue aussi. Il propose
leçons, exercices et suivi de progression, ce qui complète nos
[besoins de transmission](../bibliotheque/savoirs-durables.md). Un premier essai
devrait porter sur une petite sélection réellement disponible en français,
adaptée à un âge et un niveau définis, avec vérification humaine des exercices.
Ne pas annoncer un programme scolaire français complet.

Les contenus Kolibri doivent être préparés sous forme de chaînes compatibles.
Sa documentation décrit l'import depuis Studio, un appareil du réseau ou un
support préalablement exporté ; déposer nos PDF/ZIM ne les transforme pas en
cours Kolibri. La création d'une chaîne personnelle via Studio est une
préparation en ligne distincte de l'utilisation hors ligne des cours acquis.

**Critères avant intégration :** cours et exercices utilisables sans Internet
ni IA ; progression retrouvée après redémarrage ; export et restauration sur
une cible isolée ; accès PC/téléphone ; droits et taille de chaque sélection
examinés. Les profils libres de SetupSurvie ne deviennent pas automatiquement
des comptes Kolibri. Qualifier le parcours et la séparation des élèves sans
réintroduire implicitement de mot de passe dans SetupSurvie ; signaler toute
limite de suivi ou de confidentialité. Une indisponibilité de Kolibri doit
laisser recherche, lecteurs, assistant et secours accessibles.

Sources : [présentation officielle Kolibri](https://learningequality.org/kolibri/about-kolibri/),
[import et export des chaînes](https://kolibri.readthedocs.io/en/latest/manage/resources.html),
[intégration dans le catalogue NOMAD](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/database/seeders/service_seeder.ts).

## 4. Montrer les nouvelles éditions sans remplacement implicite

NOMAD sépare les réglages de mise à jour du logiciel, des applications et des
contenus. L'intérêt pour nous est d'afficher : ce qui est installé, ce qui a une
nouvelle édition, le volume à ajouter, les reprises/indexations nécessaires et
les raisons d'un report. Nos [mises à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md)
restent le mécanisme de référence ; ne pas les remplacer par des images `latest`
ou une mise à jour automatique générale.

Avant développement, vérifier le lien entre document et édition : conserver les
sources des anciennes conversations et traductions, la dernière copie saine et
les usages en cours. Un catalogue indisponible ne doit pas faire disparaître
une ressource locale. La réservation d'espace, la bascule et le retour arrière
des gros contenus exigent une procédure propre ; le calendrier ne les garantit pas.

Sources : [mise à jour des contenus](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/app/services/content_auto_update_service.ts),
[mise à jour des applications](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/app/services/app_auto_update_service.ts).

## Ce qui n'est pas prioritaire

Ajouter d'emblée FlatNotes, Calibre Web, Stirling PDF ou CyberChef multiplierait
les interfaces et les données à sauvegarder. Examiner d'abord une tâche précise
non couverte : note personnelle durable, gestion EPUB, opération PDF ou outil
technique. Réutiliser le logiciel tiers seulement si le bénéfice justifie son
intégration et son maintien dans le secours. Aucun nouveau service n'est retenu
par cette étude, hormis Kolibri comme candidat à essayer.

Les cartes, Kiwix, Ollama, le chat documentaire et les diagnostics existent déjà
chez nous. Le moteur NOMAD comporte lui aussi recherche, reformulation,
contrôles de pertinence et références : sa présence ne prouve pas un gain sur
notre moteur. Ne pas doubler les index ou remplacer les parcours actuels sans
comparaison sur mêmes documents, questions et matériel. Les classements publics
de benchmarks ne remplacent pas nos mesures utiles à Marc.

Sources : [catalogue des services](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/database/seeders/service_seeder.ts),
[recherche documentaire](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/app/services/rag_pipeline_service.ts),
[génération OpenAPI](https://github.com/Crosstalk-Solutions/project-nomad/blob/c903da48c97bc02f5cdfeff2ebcde00a82dfec8e/admin/start/openapi/generator.ts).

## Suite et limites

La prochaine action recommandée est de cadrer le contrôle des liens et les
améliorations de préparation à partir des écrans existants. L'essai Kolibri
vient ensuite, selon les besoins éducatifs concrets. Les objectifs de fiabilité,
de restauration complète et de recette humaine restent prioritaires.

Cette livraison est documentaire : aucune nouvelle fonction, migration,
installation, reprise d'inférence ou modification des versions tierces. La
version logicielle reste 0.35.0. Avant toute reprise de code ou distribution,
examiner les conditions du composant et des contenus concernés ; les références
NOMAD ne constituent pas une autorisation de redistribuer leurs collections.
