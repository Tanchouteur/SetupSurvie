# Recherche, assistant et travaux sur Bazzite

**Bilan du 17 novembre 2026 — livraison corrective compatible 0.37.1.**
Les essais ont été préparés sous le numéro candidat 0.36.2 avant la fusion de
la navigation 0.37.0. Ce candidat n’a pas été livré sur main. La 0.37.1 conserve
la navigation et ses versions de ressources, puis ajoute seulement le correctif
du moteur. Les rapports et empreintes ci-dessous gardent leurs numéros mesurés. Louis recadre les
essais sur l’objectif actif : recherche et assistant utiles, puis traduction et
sous-titres. Installation neuve et transfert restent distincts. La préparation
initiale de cet autre scénario est arrêtée et supprimée sans remplacer son
installation. Aucun résultat d’installation neuve n’est revendiqué.

## Conditions

Base `5f314c354a8f3fee1f2d554bd5b480416e64b7a9`, 0.36.1. PC de Louis : Ryzen 9,
RTX 2060 6 Go, 32 Go RAM, SSD du laboratoire monté et vérifié. Images existantes,
Ollama 0.40.13 ; aucun modèle téléchargé, aucune pause utilisateur active.
API séparée, code et fonds originaux en lecture seule, profils et travaux
jetables, aucun compte réel monté. La publication de recette utilise des guides
jetables. Pas de contrôleur hôte dans cette API : repli réel vers Ollama, sans
qualification des commandes ni des réserves du contrôleur Windows.

## Recherche et comparaison avant/après

Six recherches : « faire du feux », « faire du feu », « techniques pour allumer
un feu », « couteaux », « tuyaux cuivre », « antenne radio ». Les trois premières
placent les articles pertinents de Wikilivres/Wikipédia en tête. **18 ouvertures
par l’API reçoivent du texte** ; cela ne vérifie pas tous les liens et images
dans un navigateur. Les demandes larges gardent des ambiguïtés : lieu homonyme
pour « couteaux », antenne automobile pour « antenne radio ».
Durées initiales : **408–3 198 ms**, cache système non vidé. Le diagnostic initial
de la racine Kiwix dépasse trois secondes alors que catalogue et recherches
répondent. Aucune comparaison HDD/NVMe ni performance Windows n’en est déduite.

« Fais une synthèse des documents expliquant comment faire du feu. Présente les
différentes techniques et cite les sources locales consultées. » retourne zéro
source en 0.36.1 : **expliquant** devient une contrainte de recherche. Ce défaut
est aussi reproduit dans un minuscule index SQLite. Le correctif reconnaît les
sources « expliquant », « qui expliquent », « décrivant » et leurs équivalents
anglais après une demande explicite de résumé ; sujet, contraintes techniques
et collection restent conservés.

Dans « quelle longueur… ? Distingue le calcul… », la consigne secondaire annulait
aussi la lecture préalable. Le sujet principal guide désormais la décision ; un
calcul avec des documents garde sa recherche, un calcul nu reste direct.

Même demande sur le feu et même bibliothèque, contexte **16 384**, candidat corrigé :
**19 résultats, 7 sources lues et citées, 41 017 ms**, premier texte **27 797 ms**.
La première demande GPT-OSS 20B après Gemma4 aboutit sans relance manuelle :
**55 982 ms**, préparation du modèle **5 310 ms**, une source lue et citée.
Cette dernière réponse ajoute des exemples de fabrication non certifiés par le
bilan : bascule réussie et références valides ne prouvent pas le sens de chaque
phrase. La relecture reste nécessaire.

À **8 192 tokens**, le budget est refusé avant génération : consignes, outils et
réponse réservée ne tiennent pas. Le message indique désormais le contexte et
son réglage, sans accuser seulement la question. Aucune hausse automatique de
mémoire ni réduction des réserves.

## Traduction et sous-titres

Texte technique réel existant sur la loi d’Ohm : **4 passages terminés**,
**83 677 ms**, aucun contrôle numérique bloquant ni avertissement. Pause, arrêt,
reprise, passages conservés, publication, lecteur identique aux passages et
conservation du document publié après suppression du travail vérifiés.
L’original reste inchangé. Cet essai ne certifie pas un livre de 500 pages.

La relecture ciblée par l’agent des quatre passages constate un vocabulaire
globalement suivi, mais « head to tail » devient « tête-bêche », expression
ambiguë pour le montage décrit. Le texte anglais extrait comporte déjà des
trous à la place d’équations ; le modèle ne les reconstitue pas dans la traduction.
Le contrôle numérique sans anomalie n’est donc pas une preuve d’extraction
complète ni de fidélité technique. La suite ciblée doit examiner les formules
et leurs originaux illustrés, ainsi que la terminologie spatiale, sans inventer
les éléments manquants. Ce constat reste distinct d’une relecture humaine.

MP4 parlé synthétique de 132 s, 267 806 octets, déjà utilisé sur R7 : reconnaissance
CPU depuis le cache Whisper existant, **3 unités, 7 segments, 8 248 ms**. Pause
après une unité et reprise la conservent exactement ; original inchangé.
La première traduction Gemma4 échoue proprement : `refused` avec sept segments
pourtant renvoyés. Aucune piste française invalide n’est publiée.

Le correctif demande **une seule clarification** de ce statut contradictoire,
conserve la proposition rejetée et ses mesures, puis applique les mêmes contrôles
d’identifiants, d’ordre, de nombres et de temps. Un refus avec liste vide n’est
pas relancé. Un second échec reste une erreur ; la pause reste prioritaire.
La reprise réelle termine les sept segments avec une clarification et conserve
les deux propositions rejetées (échec initial et première proposition de reprise).
Un nouveau parcours complet, sans reprise manuelle après création, réussit en
**20 923 ms** : reconnaissance des trois unités/sept segments, sept traductions,
deux pistes et piste française indexée. Une clarification automatique est
enregistrée ; les temps de chaque segment sont identiques à ceux de la source.

Ollama et Kiwix ensuite arrêtés : lecteur du document français, source vidéo,
fichier WebVTT français et recherche du sous-titre français parmi les favoris
restent utilisables. Le réseau externe du PC n’a pas été coupé ; cet essai prouve
l’indépendance de ces lectures par rapport aux deux moteurs arrêtés, sans simuler
une coupure physique d’Internet.

## Vérification et limites

Avant le correctif des sous-titres : **975 tests, 6 ignorés, 201,964 s**.
Sous-titres ciblés : **17 tests, 6,730 s**, dont véritable protocole HTTP simulé,
clarification unique, refus explicite, deuxième échec et pause entre tentatives.
Ce sont des modèles simulés ; les générations Bazzite sont distinctes.
Suite finale avant fusion : **979 tests, 6 ignorés, 216,124 s**, sans échec.
Après fusion normale de la navigation 0.37.0, les **huit jobs CI** du code
`bb082577893893082a9584dcb65ccd2bdc93cdf5` réussissent :
[exécution 44039337612](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44039337612).
Linux : **979 tests, 6 ignorés, 80,042 s**. Windows, lecteurs isolés Python
3.11/3.13/3.14, Kiwix réel miniature, itinéraires hors ligne et campagne navigateur
complète passent. Les deux tests du générateur HTML repassent aussi localement.
Les exécutions précédentes et le doublon de PR sont annulés comme remplacés,
sans être comptés comme huit validations terminées. Aucun fichier du portail ou
de son générateur ne diffère de la base 0.37.0. La livraison est un correctif
compatible, sans changement du schéma de données ni des composants tiers.
Rapports avec textes privés, modèles, caches et corpus restent hors Git.
Linux ne valide ni les démarrages Windows, ni un livre entier, ni chaque vidéo
de Marc, ni Safari sur iPhone. Les limites du modèle restent explicites.

## Nettoyage et preuves privées

Le code Python testé pour la traduction, la reconnaissance et la clarification
correspond aux fichiers du candidat 0.36.2 : SHA-256 des modules `pilot/*.py`
concaténés dans l’ordre des noms,
`c4d478ac42a8e74a62706a4bc10994af907dde5f55f764771926ad4b3db62400`.
La seule différence de ces modules après fusion est la version de l’API portée
à 0.37.1 ; leur empreinte réunie devient
`6c0677c63a5b35f40d2f922b606a29edc64a5c7c5f460b740fcaafb6f1d3a62e`.
Les réponses, sources extraites et recettes HTTP sont conservées uniquement
dans une archive privée du runner : 114 089 octets,
SHA-256 `b16f1e4fccdbd30324dc823fc3f7e728d4fc4057510d95f49f1967383ef89925`.
Les premières comparaisons de recherche précèdent le changement du texte
d’erreur et du numéro de version ; leur noyau de recherche est celui du correctif.

Tous les dossiers, documents publiés de test, médias copiés et conteneurs créés
pour cette recette sont supprimés du PC. Les huit conteneurs historiques sont
arrêtés comme au départ, le runtime historique reste en 0.1.34 et Docker général
reste inactif. Le volume laboratoire est démonté et ses périphériques temporaires
détachés ; son image existante et ses données sont conservées. Le clone de
développement reste propre après sa synchronisation à 0.36.1. Aucun déploiement
client de 0.36.2, arrêt d’application utilisateur ou redémarrage du PC effectué.
