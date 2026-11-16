# Traduction : modèle, contexte, reprise et texte incomplet

**Bilan daté — candidat 0.20.1, 16 novembre 2026.** Le
[guide documentaire](../utilisation/documents-et-traduction.md) donne la procédure
courante ; ce bilan conserve les essais et leurs limites.

## Défauts et corrections

La traduction utilisait une requête directe avec contexte fixé à 8k, distincte de
la préparation/reprise du modèle des conversations. Chaque passage reprend
maintenant le contexte configuré, limité par les métadonnées du modèle local,
avec budget d’entrée/sortie vérifié. La session prépare un changement de modèle
ou de contexte et peut reprendre une fois un accusé de chargement vide, en gardant
le passage identique. Une pause observée pendant la préparation laisse le travail
en pause. Le traitement ne télécharge aucun modèle et ne lève pas une pause.

L’essai réel sur la notice anglaise UV‑5R révèle une autre limite : des noms de
touches dessinés dans le PDF deviennent des blancs dans le texte extrait. La
traduction conserve les nombres mais cela ne suffit pas à rendre la commande
utilisable. La version 2 des contrôles ajoute un avertissement pour certains
trous de commandes et caractères manquants. Le modèle doit conserver les blancs,
sans reconstituer une touche ou une valeur. Les nombres/unités restent contrôlés
avec les règles précédentes ; les rapports historiques ne sont pas recalculés.

## Essai de 500 pages, sans modèle

`test_translation_long_book.py` fabrique un PDF minuscule de 500 pages fictives,
sans guide pratique. La traduction simulée s’interrompt après sept passages,
puis reprend après réinitialisation de l’état et remplacement du fichier source.
Le test vérifie l’instantané d’origine, les premiers passages inchangés, les
modèles distincts avant/après reprise, la page 500, l’export et la publication.
Il ne teste ni le temps d’un modèle réel ni la fidélité d’un vrai livre de 500 pages.

## Essais réels sur le R7

Les fichiers et rapports restent privés. Notice constructeur Baofeng/Radioddity
V1.0, date inconnue, empreinte et taille du catalogue 0.19.1. Modèle préexistant
`gemma4:e4b`, Ollama natif 0.40.14, contexte 16k, sortie au plus 4 096 tokens,
32 couches GPU, six threads, réserve 1 536 Mio, maintien quinze secondes.
Aucun téléchargement de poids, compte client, émission radio ou essai Windows.

- `report-gemma4-translation-initial.json` : page PDF 14, un passage traduit,
  contrôle version 1 sans anomalie. La lecture humaine relève pourtant les noms
  de touches absents de l’extraction et les marqueurs ajoutés par le modèle.
  Ce résultat n’est donc pas une traduction technique validée.
- `report-gemma4-translation-resume.json` : pages 13–14, deux passages,
  pause après le premier puis reprise explicite. Les deux terminent en 63 416 ms,
  le passage déjà enregistré est conservé. Le second porte l’avertissement
  `source_gaps` version 2 ; la traduction terminée compte un passage à relire.
  Publication et export portent les limites, sans fabriquer les noms manquants.
- La recette `tests/real_translation_check.py` conserve texte source, traduction,
  contrôles et mesures du cycle du modèle dans un rapport privé. `--pause-after 1`
  vérifie la reprise et la conservation ; `--preload-model` prépare seulement un
  modèle déjà présent, depuis un moteur sans modèle chargé. Elle refuse toute
  charge tierce inconnue et n’arrête aucun modèle de force.

Le changement de modèle réel a aussi terminé :
`report-gemma4-translation-switch.json`, Llama 3.1 8B préchargé par la recette
sur moteur initialement vide, puis Gemma demandé une seule fois pour la page 14.
La préparation est `ready`, 3 901 ms ; la traduction termine en 37 357 ms,
avec l’avertissement `source_gaps`. Le rapport ne relève aucune reprise HTTP.
Empreinte Python du code :
`bc88a62874301c317d7d7fb2e41d7fb461eeb1e87475b1dbe146ef62daa65c8b`.
Le modèle de départ n’a pas été arrêté de force ; aucun poids n’a été téléchargé.
Le commit fonctionnel `b6f29f22cf58ef9ee0e37662ceb535dbb9191cdd` réussit
les [huit jobs CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43810078753).
La suite finale confirme 750 tests locaux, trois ignorés spécifiques à Windows.
Aucun gain de vitesse Windows
n’est déduit de ces mesures Linux.

## Vérifications et limites

Les 750 tests locaux réussissent (trois ignorés propres à Windows). Tests HTTP
simulés : contexte réglé et limite native, changement de modèle préparé, reprise
sans texte changé, pause, contexte insuffisant sans troncature. Les recettes
Chromium/WebKit vérifient aussi l’avertissement dans le panneau, la comparaison,
le candidat refusé, les exports, pause/reprise et quatre tailles d’écran. Le MCP
Chromium confirme le rendu de l’avertissement ; capture examinée. Aucun essai
physique iPhone ni validation de traduction d’un livre réel entier.

Le nouvel avertissement est une heuristique : tous les dessins, tableaux, blancs,
caractères perdus ou problèmes de sens ne sont pas détectés. Aucun OCR ni vision
n’est ajouté. La lecture française intégrée dans les lecteurs, le glossaire,
la déduplication de traductions et les sous-titres restent des travaux distincts.
Le numéro **0.20.1** est une correction compatible du traitement existant ; aucune
migration du schéma 1 ni modification d’image tierce ou des profils conseillés.


## Reçu du paquet

Paquet extrait et comparé au commit `2786b0699bb4909f3cb7fa284a3e7f54177fe083` :
**809 fichiers**, 6880761 octets compressés, 15415878 octets
décompressés. SHA-256 :
`37c47ade1876d676201a9ea815a0da103afe2157e1dae2d3c66fbdeb6a3546ea`.
Chaque fichier correspond aux octets du commit après filtres Git. Ce reçu est
ajouté ensuite sans modifier le code validé ; aucun déploiement chez Marc.
