# Where There Is No Doctor — téléchargement et recette

Téléchargement et essais du 11 novembre 2026, documentation finalisée le 12 novembre 2026. **Édition anglaise 2025 complète**, obtenue depuis la [page de téléchargement officielle Hesperian](https://languages.hesperian.org/pages/en/pdf.html). Il s’agit du manuel classique, distinct de *New Where There Is No Doctor* et de *Where There Is No Dentist*.

Les **32 PDF** comprennent les 23 chapitres, les pages préliminaires, les pages de médicaments, le glossaire, l’index et les annexes. Taille cumulée : **14.03 Mo**. Chaque original illustré est conservé, avec taille et SHA-256 figés dans deploy/content-catalog.json, lot **no-doctor**.

## Téléchargement reproductible

~~~bash
python3 scripts/content.py download --lab --no-refresh --pack no-doctor
~~~

Sur une installation portable, remplacer --lab par --work-dir CHEMIN_DU_DOSSIER_PRIVE. Le catalogue conserve la source officielle, l’édition et les réserves sur la redistribution numérique/commerciale. Le téléchargement personnel ne constitue pas une autorisation de diffusion commerciale.

## Indexation et recherche

Les 32 fichiers sont indexés : **503 pages avec texte sur 503 pages**, sans erreur d’extraction ni besoin d’OCR signalé. Les PDF restent ouvrables à la page citée, avec leurs figures et tableaux. Les fichiers sont dans data/library/guides/HES-no-doctor-2025-*.en.pdf sur le volume dédié.

La recherche du titre anglais et la requête française **« examiner personne malade »** retrouvent le livre et le chapitre 3. Le vocabulaire bilingue de recherche a été complété pour ce cas. Les **18 recherches** de la recette générale ont réussi, avec lecture des passages et ouverture des originaux. Le contrôle d’intégrité n’a signalé aucun PDF modifié ni guide absent de l’index.

Un essai réel du mode « réponse rapide » a effectué search_library, puis read_source, et a répondu en français avec le titre, l’édition 2025 et le titre du chapitre demandé, en citant une page du chapitre 3. Le compte temporaire et ses conversations ont été supprimés. Rapport local : data/state/pilot/acceptance-no-doctor.json. Aucun marqueur de pause n’était présent ; aucun démarrage forcé n’a été effectué.

Pour rejouer uniquement cet essai dans le service pilote, lorsque les calculs sont autorisés :

~~~bash
python -m pilot.acceptance_library --case no-doctor
~~~

Les tests de catalogue vérifient aussi la présence des 23 chapitres et de toutes les annexes, pour éviter de présenter un extrait incomplet comme le livre entier. La suite de tests exécutée dans l’image du service a réussi (92 tests, dont les travaux parallèles présents au moment du contrôle). Aucune dépendance n’a été installée globalement sur le PC.

Cette recette valide l’accès par la recherche et les outils de l’assistant du portail ; elle ne représente ni une validation médicale du contenu, ni une importation complète dans les collections avancées d’Open WebUI.

## Fichiers inclus

| Partie de l’éditeur | Pages indexées | Taille en Mo |
| --- | ---: | ---: |
| Front Matter: Cover, Copyright | 4 | 0.36 |
| Table of Contents, Introduction, Note about this New Edition, Thanks | 12 | 0.17 |
| Words to the village health worker (Brown Pages) | 32 | 0.74 |
| 1 Home cures and popular beliefs | 16 | 0.45 |
| 2 Sicknesses that are often confused | 11 | 0.29 |
| 3 How to examine a sick person | 10 | 0.35 |
| 4 How to take care of a sick person | 6 | 0.21 |
| 5 Healing without medicines | 4 | 0.19 |
| 6 Right and wrong uses of modern medicines | 6 | 0.21 |
| 7 Antibiotics: what they are and how to use them | 4 | 0.19 |
| 8 How to measure and give medicine | 6 | 0.26 |
| 9 Instructions and precautions for injections | 10 | 0.63 |
| 10 First aid | 32 | 0.89 |
| 11 Nutrition: what to eat to be healthy | 24 | 1.02 |
| 12 Prevention: how to avoid many sicknesses | 20 | 0.52 |
| 13 Some very common sicknesses | 28 | 0.62 |
| 14 Serious illnesses that need special medical attention | 14 | 0.37 |
| 15 Skin problems | 24 | 1.00 |
| 16 The eyes | 12 | 0.42 |
| 17 The teeth, gums, and mouth | 4 | 0.21 |
| 18 The urinary system and the genitals | 12 | 0.35 |
| 19 Information for mothers and midwives | 38 | 0.71 |
| 20 Family planning - having the number of children you want | 12 | 0.45 |
| 21 Health and sicknesses of children | 28 | 1.10 |
| 22 Health and sicknesses of older people | 8 | 0.25 |
| 23 The medicine kit | 8 | 0.19 |
| The green pages: The uses, dosage, and precautions for medicines | 62 | 0.52 |
| Additional Information | 19 | 0.43 |
| Vocabulary | 10 | 0.13 |
| Addresses for teaching materials | 4 | 0.10 |
| Index | 14 | 0.17 |
| Dosage Blanks, Patient Reports, Other Books from Hesperian | 9 | 0.51 |

Bibliothèque après ajout : **environ 200,62 Go**, toujours sous les 500 Go documentaires. Les modèles et caches d’essai restent exclus de ce budget.
